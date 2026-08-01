"""Transparent synthetic benchmark for topology-aware planetary inference.

This is a deliberately small linear thermal-network experiment. It demonstrates
one narrow claim from SPPT: identical static boundary equilibria need not imply
identical internal connectivity, while transient forcing can identify the
minimum graph family. It is not a fit to any planet.
"""
from __future__ import annotations

import csv
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np
from scipy.integrate import solve_ivp

import sppt_core as sppt
from astra_optimization import N_STARTS, solve_multistart

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIGURES = ROOT / "figures"
DATA.mkdir(parents=True, exist_ok=True)
FIGURES.mkdir(parents=True, exist_ok=True)

CAPACITY = np.array([8.0, 3.0, 1.0], dtype=float)
SURFACE_SINK = 1.2
INTERNAL_POWER = 1.0
NOISE_SD = 2.5e-3
SEED = 20260801

GRAPHS: dict[str, list[tuple[int, int]]] = {
    "chain": [(0, 1), (1, 2)],
    "surface_star": [(0, 2), (1, 2)],
    "deep_star": [(0, 1), (0, 2)],
    "triangle": [(0, 1), (1, 2), (0, 2)],
}
TRUE_GRAPH = "chain"
TRUE_CONDUCTANCE = np.array([0.22, 1.40], dtype=float)


@dataclass(frozen=True)
class FitRecord:
    graph: str
    n_edges: int
    conductance: list[float]
    train_rss: float
    train_rmse: float
    bic: float
    heldout_rmse: float
    optimizer_starts: int
    optimizer_accepted: int
    optimizer_best_start: int
    optimizer_nfev: int
    optimizer_optimality: float
    optimizer_scaled_optimality: float
    optimizer_active_mask: list[int]


def train_forcing(t: float) -> float:
    return float(0.35 * np.sin(0.55 * t) + 0.18 * (t > 10.0) - 0.12 * (t > 23.0))


def heldout_forcing(t: float) -> float:
    pulse = 0.20 if 6.0 < t < 14.0 else 0.0
    return float(0.28 * np.sin(1.05 * t) + 0.22 * np.sin(0.19 * t) + pulse)


def laplacian(edges: list[tuple[int, int]], conductance: np.ndarray) -> np.ndarray:
    B = sppt.incidence_matrix(3, edges)
    return sppt.weighted_laplacian(B, conductance)


def equilibrium(edges: list[tuple[int, int]], conductance: np.ndarray, forcing: float) -> np.ndarray:
    """Return equilibrium temperatures for a connected three-node graph."""
    L = laplacian(edges, conductance)
    sink = np.diag([0.0, 0.0, SURFACE_SINK])
    source = np.array([INTERNAL_POWER, 0.0, forcing], dtype=float)
    return np.linalg.solve(L + sink, source)


def simulate(
    edges: list[tuple[int, int]],
    conductance: np.ndarray,
    time: np.ndarray,
    forcing: Callable[[float], float],
) -> np.ndarray:
    L = laplacian(edges, conductance)
    sink = np.diag([0.0, 0.0, SURFACE_SINK])
    A = np.diag(1.0 / CAPACITY) @ (-L - sink)
    base = np.array([INTERNAL_POWER / CAPACITY[0], 0.0, 0.0])

    def rhs(t: float, state: np.ndarray) -> np.ndarray:
        drive = base.copy()
        drive[2] = forcing(t) / CAPACITY[2]
        return A @ state + drive

    initial = equilibrium(edges, conductance, forcing(float(time[0])))
    solution = solve_ivp(
        rhs,
        (float(time[0]), float(time[-1])),
        initial,
        t_eval=time,
        max_step=0.05,
        rtol=1e-9,
        atol=1e-11,
    )
    if not solution.success:
        raise RuntimeError(solution.message)
    return solution.y


def simulate_with_log_conductance_sensitivities(
    edges: list[tuple[int, int]],
    conductance: np.ndarray,
    time: np.ndarray,
    forcing: Callable[[float], float],
) -> tuple[np.ndarray, np.ndarray]:
    """Integrate state and exact forward sensitivities to log conductances."""
    incidence = sppt.incidence_matrix(3, edges)
    laplacian_matrix = sppt.weighted_laplacian(incidence, conductance)
    sink = np.diag([0.0, 0.0, SURFACE_SINK])
    inverse_capacity = np.diag(1.0 / CAPACITY)
    operator = laplacian_matrix + sink
    system = -inverse_capacity @ operator
    base = np.array([INTERNAL_POWER / CAPACITY[0], 0.0, 0.0])
    source = np.array([INTERNAL_POWER, 0.0, forcing(float(time[0]))], dtype=float)
    initial = np.linalg.solve(operator, source)

    laplacian_derivatives = [
        conductance[index] * np.outer(incidence[:, index], incidence[:, index])
        for index in range(conductance.size)
    ]
    system_derivatives = [-inverse_capacity @ derivative for derivative in laplacian_derivatives]
    initial_sensitivity = np.column_stack(
        [-np.linalg.solve(operator, derivative @ initial) for derivative in laplacian_derivatives]
    )

    def augmented_rhs(t: float, augmented: np.ndarray) -> np.ndarray:
        state = augmented[:3]
        sensitivity = augmented[3:].reshape(3, conductance.size)
        drive = base.copy()
        drive[2] = forcing(t) / CAPACITY[2]
        state_tendency = system @ state + drive
        sensitivity_tendency = system @ sensitivity
        for index, derivative in enumerate(system_derivatives):
            sensitivity_tendency[:, index] += derivative @ state
        return np.concatenate((state_tendency, sensitivity_tendency.ravel()))

    solution = solve_ivp(
        augmented_rhs,
        (float(time[0]), float(time[-1])),
        np.concatenate((initial, initial_sensitivity.ravel())),
        t_eval=time,
        max_step=0.05,
        rtol=1e-9,
        atol=1e-11,
    )
    if not solution.success:
        raise RuntimeError(solution.message)
    states = solution.y[:3]
    sensitivity = solution.y[3:].T.reshape(time.size, 3, conductance.size).transpose(1, 2, 0)
    return states, sensitivity


def fit_graph(
    name: str,
    time: np.ndarray,
    observed_surface: np.ndarray,
) -> tuple[np.ndarray, float, float, dict[str, object]]:
    edges = GRAPHS[name]

    cached_log_conductance: np.ndarray | None = None
    cached_state: np.ndarray | None = None
    cached_sensitivity: np.ndarray | None = None

    def evaluate(log_conductance: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        nonlocal cached_log_conductance, cached_state, cached_sensitivity
        if cached_log_conductance is None or not np.array_equal(
            cached_log_conductance, log_conductance
        ):
            cached_log_conductance = log_conductance.copy()
            cached_state, cached_sensitivity = simulate_with_log_conductance_sensitivities(
                edges, np.exp(log_conductance), time, train_forcing
            )
        assert cached_state is not None and cached_sensitivity is not None
        return cached_state, cached_sensitivity

    def residual(log_conductance: np.ndarray) -> np.ndarray:
        predicted = evaluate(log_conductance)[0][2]
        return (predicted - observed_surface) / NOISE_SD

    def jacobian(log_conductance: np.ndarray) -> np.ndarray:
        sensitivity = evaluate(log_conductance)[1]
        return sensitivity[2].T / NOISE_SD

    try:
        result, best_start, diagnostics = solve_multistart(
            residual,
            len(edges),
            jacobian=jacobian,
            xtol=1e-11,
            ftol=1e-11,
            gtol=1e-11,
            max_nfev=1500,
        )
    except RuntimeError as exc:
        raise RuntimeError(f"{name} fit failed convergence: {exc}") from exc
    conductance = np.exp(result.x)
    residual_physical = residual(result.x) * NOISE_SD
    rss = float(np.sum(residual_physical**2))
    n = observed_surface.size
    p = conductance.size
    bic = float(n * np.log(rss / n) + p * np.log(n))
    optimizer = {
        "starts": N_STARTS,
        "accepted": sum(item.accepted for item in diagnostics),
        "best_start": best_start,
        "nfev": int(result.nfev),
        "optimality": float(result.optimality),
        "scaled_optimality": float(result.optimality) / max(1.0, float(result.cost)),
        "active_mask": [int(value) for value in np.asarray(result.active_mask, dtype=int)],
        "diagnostics": [item.to_dict() for item in diagnostics],
    }
    return conductance, rss, bic, optimizer


def main() -> None:
    rng = np.random.default_rng(SEED)
    t_train = np.linspace(0.0, 36.0, 361)
    truth_train = simulate(GRAPHS[TRUE_GRAPH], TRUE_CONDUCTANCE, t_train, train_forcing)
    observed = truth_train[2] + rng.normal(0.0, NOISE_SD, t_train.size)

    t_test = np.linspace(0.0, 26.0, 261)
    truth_test = simulate(GRAPHS[TRUE_GRAPH], TRUE_CONDUCTANCE, t_test, heldout_forcing)

    records: list[FitRecord] = []
    predictions: dict[str, np.ndarray] = {}
    for name in GRAPHS:
        fitted_k, rss, bic, optimizer = fit_graph(name, t_train, observed)
        pred_test = simulate(GRAPHS[name], fitted_k, t_test, heldout_forcing)[2]
        predictions[name] = pred_test
        records.append(
            FitRecord(
                graph=name,
                n_edges=len(GRAPHS[name]),
                conductance=[float(value) for value in fitted_k],
                train_rss=rss,
                train_rmse=float(np.sqrt(rss / t_train.size)),
                bic=bic,
                heldout_rmse=float(np.sqrt(np.mean((pred_test - truth_test[2]) ** 2))),
                optimizer_starts=int(optimizer["starts"]),
                optimizer_accepted=int(optimizer["accepted"]),
                optimizer_best_start=int(optimizer["best_start"]),
                optimizer_nfev=int(optimizer["nfev"]),
                optimizer_optimality=float(optimizer["optimality"]),
                optimizer_scaled_optimality=float(optimizer["scaled_optimality"]),
                optimizer_active_mask=list(optimizer["active_mask"]),
            )
        )

    records.sort(key=lambda record: record.bic)

    static_checks = {}
    for name, edges in GRAPHS.items():
        k = TRUE_CONDUCTANCE if name == TRUE_GRAPH else np.repeat(0.7, len(edges))
        state = equilibrium(edges, np.asarray(k, dtype=float), forcing=0.0)
        static_checks[name] = {
            "surface_temperature": float(state[2]),
            "deep_temperature": float(state[0]),
        }

    payload = {
        "status": "synthetic benchmark; not planetary data",
        "seed": SEED,
        "noise_sd": NOISE_SD,
        "true_graph": TRUE_GRAPH,
        "true_conductance": TRUE_CONDUCTANCE.tolist(),
        "capacities": CAPACITY.tolist(),
        "surface_sink": SURFACE_SINK,
        "internal_power": INTERNAL_POWER,
        "static_equilibrium": static_checks,
        "fits_ranked_by_bic": [asdict(record) for record in records],
    }
    (DATA / "synthetic_topology_benchmark.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    with (DATA / "synthetic_topology_benchmark.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(asdict(records[0]).keys()),
            lineterminator="\n",
        )
        writer.writeheader()
        for record in records:
            row = asdict(record)
            row["conductance"] = ";".join(f"{value:.8g}" for value in record.conductance)
            row["optimizer_active_mask"] = ";".join(
                str(value) for value in record.optimizer_active_mask
            )
            writer.writerow(row)

    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.6))
    ax = axes[0]
    ax.scatter(t_train[::6], observed[::6], s=9, label="noisy boundary observations", zorder=3)
    ax.plot(t_train, truth_train[2], linewidth=1.5, label="true chain response")
    ax.set_xlabel("training time")
    ax.set_ylabel("surface state")
    ax.set_title("Training protocol")
    ax.legend(frameon=False, fontsize=7.5)

    ax = axes[1]
    ax.plot(t_test, truth_test[2], linewidth=2.0, label="true chain")
    for record in records:
        if record.graph == TRUE_GRAPH:
            continue
        label = record.graph.replace("_", " ")
        ax.plot(t_test, predictions[record.graph], linewidth=1.0, label=label)
    ax.set_xlabel("held-out time")
    ax.set_ylabel("surface state")
    ax.set_title("Post-selection unseen-forcing comparison")
    ax.legend(frameon=False, fontsize=7.2)
    fig.suptitle("Synthetic topology-recovery benchmark", fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIGURES / "supplement_figure_S1_topology_benchmark.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIGURES / "supplement_figure_S1_topology_benchmark.pdf", bbox_inches="tight")
    plt.close(fig)

    best = records[0]
    if best.graph != TRUE_GRAPH:
        raise AssertionError(f"BIC selected {best.graph}, expected {TRUE_GRAPH}.")
    if not np.allclose([static_checks[name]["surface_temperature"] for name in GRAPHS], 1.0 / 1.2):
        raise AssertionError("Connected candidate graphs should share the same static surface equilibrium.")


if __name__ == "__main__":
    main()
