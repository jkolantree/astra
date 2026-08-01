"""Monte Carlo robustness check for the synthetic topology-recovery benchmark.

This script repeats the three-reservoir benchmark over independent noise seeds.
It is a synthetic model-selection test, not a fit to any planet.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import Counter
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np
from scipy.linalg import expm, expm_frechet

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import sppt_core as sppt  # noqa: E402
from astra_optimization import N_STARTS, solve_multistart  # noqa: E402

DATA = ROOT / "data"
FIGURES = ROOT / "figures"
DATA.mkdir(parents=True, exist_ok=True)
FIGURES.mkdir(parents=True, exist_ok=True)

CAPACITY = np.array([8.0, 3.0, 1.0], dtype=float)
SURFACE_SINK = 1.2
INTERNAL_POWER = 1.0
TRUE_GRAPH = "chain"
TRUE_CONDUCTANCE = np.array([0.22, 1.40], dtype=float)
FAST_SUBSTEPS = 4
GRAPHS: dict[str, list[tuple[int, int]]] = {
    "chain": [(0, 1), (1, 2)],
    "surface_star": [(0, 2), (1, 2)],
    "deep_star": [(0, 1), (0, 2)],
    "triangle": [(0, 1), (1, 2), (0, 2)],
}


def train_forcing(t: float) -> float:
    return float(0.35 * np.sin(0.55 * t) + 0.18 * (t > 10.0) - 0.12 * (t > 23.0))


def heldout_forcing(t: float) -> float:
    pulse = 0.20 if 6.0 < t < 14.0 else 0.0
    return float(0.28 * np.sin(1.05 * t) + 0.22 * np.sin(0.19 * t) + pulse)


def laplacian(edges: list[tuple[int, int]], conductance: np.ndarray) -> np.ndarray:
    return sppt.weighted_laplacian(sppt.incidence_matrix(3, edges), conductance)


def equilibrium(edges: list[tuple[int, int]], conductance: np.ndarray, forcing: float) -> np.ndarray:
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
    """Integrate the linear model with exact zero-order-hold propagation.

    Each sample interval is divided into ``FAST_SUBSTEPS`` equal zero-order-hold
    steps, with the forcing evaluated at each substep midpoint. Validation
    against the high-accuracy solve_ivp implementation is recorded in the
    technical supplement and unit tests.
    """
    if time.ndim != 1 or time.size < 2:
        raise ValueError("time must contain at least two samples.")
    steps = np.diff(time)
    if not np.allclose(steps, steps[0], rtol=0.0, atol=1e-12):
        raise ValueError("Fast ensemble simulation requires a uniform time grid.")

    L = laplacian(edges, conductance)
    sink = np.diag([0.0, 0.0, SURFACE_SINK])
    A = np.diag(1.0 / CAPACITY) @ (-L - sink)
    base = np.array([INTERNAL_POWER / CAPACITY[0], 0.0, 0.0], dtype=float)
    sample_dt = float(steps[0])
    sub_dt = sample_dt / FAST_SUBSTEPS
    transition = expm(A * sub_dt)
    input_map = np.linalg.solve(A, transition - np.eye(3))

    state = equilibrium(edges, conductance, forcing(float(time[0])))
    output = np.empty((3, time.size), dtype=float)
    output[:, 0] = state
    for index in range(time.size - 1):
        interval_start = float(time[index])
        for sub_index in range(FAST_SUBSTEPS):
            midpoint = interval_start + (sub_index + 0.5) * sub_dt
            drive = base.copy()
            drive[2] = forcing(midpoint) / CAPACITY[2]
            state = transition @ state + input_map @ drive
        output[:, index + 1] = state
    return output


def simulate_with_log_conductance_sensitivities(
    edges: list[tuple[int, int]],
    conductance: np.ndarray,
    time: np.ndarray,
    forcing: Callable[[float], float],
) -> tuple[np.ndarray, np.ndarray]:
    """Propagate the ZOH model and exact sensitivities to log conductances."""
    if time.ndim != 1 or time.size < 2:
        raise ValueError("time must contain at least two samples.")
    steps = np.diff(time)
    if not np.allclose(steps, steps[0], rtol=0.0, atol=1e-12):
        raise ValueError("Fast ensemble simulation requires a uniform time grid.")

    incidence = sppt.incidence_matrix(3, edges)
    laplacian_matrix = sppt.weighted_laplacian(incidence, conductance)
    sink = np.diag([0.0, 0.0, SURFACE_SINK])
    inverse_capacity = np.diag(1.0 / CAPACITY)
    operator = laplacian_matrix + sink
    system = -inverse_capacity @ operator
    base = np.array([INTERNAL_POWER / CAPACITY[0], 0.0, 0.0], dtype=float)
    sample_dt = float(steps[0])
    sub_dt = sample_dt / FAST_SUBSTEPS
    transition = expm(system * sub_dt)
    input_map = np.linalg.solve(system, transition - np.eye(3))

    laplacian_derivatives = [
        conductance[index] * np.outer(incidence[:, index], incidence[:, index])
        for index in range(conductance.size)
    ]
    system_derivatives = [-inverse_capacity @ derivative for derivative in laplacian_derivatives]
    transition_derivatives = [
        expm_frechet(system * sub_dt, derivative * sub_dt, compute_expm=False)
        for derivative in system_derivatives
    ]
    input_map_derivatives = [
        np.linalg.solve(system, transition_derivative - derivative @ input_map)
        for derivative, transition_derivative in zip(
            system_derivatives, transition_derivatives, strict=True
        )
    ]

    source = np.array([INTERNAL_POWER, 0.0, forcing(float(time[0]))], dtype=float)
    state = np.linalg.solve(operator, source)
    sensitivity = np.column_stack(
        [-np.linalg.solve(operator, derivative @ state) for derivative in laplacian_derivatives]
    )
    output = np.empty((3, time.size), dtype=float)
    sensitivity_output = np.empty((3, conductance.size, time.size), dtype=float)
    output[:, 0] = state
    sensitivity_output[:, :, 0] = sensitivity
    for index in range(time.size - 1):
        interval_start = float(time[index])
        for sub_index in range(FAST_SUBSTEPS):
            midpoint = interval_start + (sub_index + 0.5) * sub_dt
            drive = base.copy()
            drive[2] = forcing(midpoint) / CAPACITY[2]
            old_state = state
            old_sensitivity = sensitivity
            state = transition @ old_state + input_map @ drive
            sensitivity = transition @ old_sensitivity
            for parameter in range(conductance.size):
                sensitivity[:, parameter] += (
                    transition_derivatives[parameter] @ old_state
                    + input_map_derivatives[parameter] @ drive
                )
        output[:, index + 1] = state
        sensitivity_output[:, :, index + 1] = sensitivity
    return output, sensitivity_output


@dataclass(frozen=True)
class SeedResult:
    seed: int
    winner: str
    chain_bic: float
    triangle_bic: float
    delta_bic_triangle_minus_chain: float
    chain_heldout_rmse: float
    triangle_heldout_rmse: float
    surface_star_heldout_rmse: float
    deep_star_heldout_rmse: float
    triangle_shortcut_conductance: float
    optimizer_all_converged: bool
    optimizer_min_accepted_starts: int
    optimizer_max_optimality: float
    optimizer_max_scaled_optimality: float
    triangle_shortcut_at_lower_bound: bool
    optimizer_diagnostics: dict[str, dict[str, object]]


def run_seed(arguments: tuple[int, float]) -> SeedResult:
    seed, noise_sd = arguments
    rng = np.random.default_rng(seed)
    t_train = np.linspace(0.0, 36.0, 361)
    truth_train = simulate(GRAPHS[TRUE_GRAPH], TRUE_CONDUCTANCE, t_train, train_forcing)
    observed = truth_train[2] + rng.normal(0.0, noise_sd, t_train.size)

    t_test = np.linspace(0.0, 26.0, 261)
    truth_test = simulate(GRAPHS[TRUE_GRAPH], TRUE_CONDUCTANCE, t_test, heldout_forcing)[2]

    records: dict[str, dict[str, object]] = {}
    for name, edges in GRAPHS.items():

        cached_log_conductance: np.ndarray | None = None
        cached_state: np.ndarray | None = None
        cached_sensitivity: np.ndarray | None = None

        def evaluate(
            log_conductance: np.ndarray,
            graph_edges: list[tuple[int, int]] = edges,
        ) -> tuple[np.ndarray, np.ndarray]:
            nonlocal cached_log_conductance, cached_state, cached_sensitivity
            if cached_log_conductance is None or not np.array_equal(
                cached_log_conductance, log_conductance
            ):
                cached_log_conductance = log_conductance.copy()
                cached_state, cached_sensitivity = simulate_with_log_conductance_sensitivities(
                    graph_edges, np.exp(log_conductance), t_train, train_forcing
                )
            assert cached_state is not None and cached_sensitivity is not None
            return cached_state, cached_sensitivity

        def residual(log_conductance: np.ndarray) -> np.ndarray:
            predicted = evaluate(log_conductance)[0][2]
            return (predicted - observed) / noise_sd

        def jacobian(log_conductance: np.ndarray) -> np.ndarray:
            return evaluate(log_conductance)[1][2].T / noise_sd

        try:
            result, best_start, diagnostics = solve_multistart(
                residual,
                len(edges),
                jacobian=jacobian,
                xtol=2e-9,
                ftol=2e-9,
                gtol=2e-9,
                max_nfev=900,
            )
        except RuntimeError as exc:
            raise RuntimeError(f"seed {seed} graph {name} failed convergence: {exc}") from exc
        conductance = np.exp(result.x)
        residual_physical = residual(result.x) * noise_sd
        rss = float(np.sum(residual_physical**2))
        n = observed.size
        p = conductance.size
        bic = float(n * np.log(rss / n) + p * np.log(n))
        prediction = simulate(edges, conductance, t_test, heldout_forcing)[2]
        heldout = float(np.sqrt(np.mean((prediction - truth_test) ** 2)))
        records[name] = {
            "conductance": conductance,
            "bic": bic,
            "heldout_rmse": heldout,
            "best_start": best_start,
            "accepted_starts": sum(item.accepted for item in diagnostics),
            "optimality": float(result.optimality),
            "scaled_optimality": float(result.optimality) / max(1.0, float(result.cost)),
            "diagnostics": {
                "best_start": best_start,
                "accepted_starts": sum(item.accepted for item in diagnostics),
                "selected_nfev": int(result.nfev),
                "selected_cost": float(result.cost),
                "selected_optimality": float(result.optimality),
                "selected_scaled_optimality": float(result.optimality)
                / max(1.0, float(result.cost)),
                "selected_active_mask": [
                    int(value) for value in np.asarray(result.active_mask, dtype=int)
                ],
                "starts": [item.to_dict() for item in diagnostics],
            },
        }

    winner = min(records, key=lambda name: float(records[name]["bic"]))
    triangle_k = np.asarray(records["triangle"]["conductance"], dtype=float)
    return SeedResult(
        seed=seed,
        winner=winner,
        chain_bic=float(records["chain"]["bic"]),
        triangle_bic=float(records["triangle"]["bic"]),
        delta_bic_triangle_minus_chain=float(records["triangle"]["bic"] - records["chain"]["bic"]),
        chain_heldout_rmse=float(records["chain"]["heldout_rmse"]),
        triangle_heldout_rmse=float(records["triangle"]["heldout_rmse"]),
        surface_star_heldout_rmse=float(records["surface_star"]["heldout_rmse"]),
        deep_star_heldout_rmse=float(records["deep_star"]["heldout_rmse"]),
        triangle_shortcut_conductance=float(triangle_k[2]),
        optimizer_all_converged=all(int(record["accepted_starts"]) > 0 for record in records.values()),
        optimizer_min_accepted_starts=min(int(record["accepted_starts"]) for record in records.values()),
        optimizer_max_optimality=max(float(record["optimality"]) for record in records.values()),
        optimizer_max_scaled_optimality=max(
            float(record["scaled_optimality"]) for record in records.values()
        ),
        triangle_shortcut_at_lower_bound=bool(np.isclose(np.log(triangle_k[2]), -8.0, atol=1e-7)),
        optimizer_diagnostics={
            name: dict(record["diagnostics"]) for name, record in records.items()
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=64, help="Number of independent noise seeds.")
    parser.add_argument("--seed-start", type=int, default=20260801)
    parser.add_argument("--noise-sd", type=float, default=2.5e-3)
    parser.add_argument("--workers", type=int, default=max(1, min(4, os.cpu_count() or 1)))
    args = parser.parse_args()
    if args.seeds < 1 or args.noise_sd <= 0.0 or args.workers < 1:
        raise ValueError("seeds, noise-sd, and workers must be positive.")

    jobs = [(args.seed_start + i, args.noise_sd) for i in range(args.seeds)]
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        results = list(executor.map(run_seed, jobs))

    counts = Counter(result.winner for result in results)
    triangle_heldout_wins = sum(
        result.triangle_heldout_rmse < result.chain_heldout_rmse for result in results
    )
    shortcut_lower_bound_count = sum(result.triangle_shortcut_at_lower_bound for result in results)
    payload = {
        "status": "synthetic Monte Carlo robustness check; not planetary data",
        "noise_sd": args.noise_sd,
        "seed_start": args.seed_start,
        "n_seeds": args.seeds,
        "true_graph": TRUE_GRAPH,
        "fast_substeps_per_sample": FAST_SUBSTEPS,
        "winner_counts": dict(sorted(counts.items())),
        "chain_selection_fraction": counts.get(TRUE_GRAPH, 0) / args.seeds,
        "selection_basis": "training BIC only; held-out RMSE is reported post-selection",
        "optimizer_starts_per_graph": N_STARTS,
        "optimizer_all_graphs_converged": all(result.optimizer_all_converged for result in results),
        "triangle_lower_heldout_rmse_count": triangle_heldout_wins,
        "mean_chain_heldout_rmse": float(np.mean([r.chain_heldout_rmse for r in results])),
        "mean_triangle_heldout_rmse": float(np.mean([r.triangle_heldout_rmse for r in results])),
        "triangle_shortcut_lower_bound_count": shortcut_lower_bound_count,
        "triangle_shortcut_log_lower_bound": -8.0,
        "median_delta_bic_triangle_minus_chain": float(
            np.median([r.delta_bic_triangle_minus_chain for r in results])
        ),
        "minimum_delta_bic_triangle_minus_chain": float(
            np.min([r.delta_bic_triangle_minus_chain for r in results])
        ),
        "maximum_delta_bic_triangle_minus_chain": float(
            np.max([r.delta_bic_triangle_minus_chain for r in results])
        ),
        "median_triangle_shortcut_conductance": float(
            np.median([r.triangle_shortcut_conductance for r in results])
        ),
        "results": [asdict(result) for result in results],
    }
    (DATA / "synthetic_topology_ensemble.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n"
    )

    fieldnames = list(asdict(results[0]).keys())
    with (DATA / "synthetic_topology_ensemble.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for result in results:
            row = asdict(result)
            row["optimizer_diagnostics"] = json.dumps(
                result.optimizer_diagnostics,
                allow_nan=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            writer.writerow(row)

    delta_bic = np.array([r.delta_bic_triangle_minus_chain for r in results])
    shortcut = np.array([r.triangle_shortcut_conductance for r in results])
    rmse = {
        "chain": np.array([r.chain_heldout_rmse for r in results]),
        "triangle": np.array([r.triangle_heldout_rmse for r in results]),
        "surface star": np.array([r.surface_star_heldout_rmse for r in results]),
        "deep star": np.array([r.deep_star_heldout_rmse for r in results]),
    }

    fig, axes = plt.subplots(1, 3, figsize=(10.2, 3.5))
    ax = axes[0]
    ax.hist(delta_bic, bins=max(8, int(np.sqrt(args.seeds))))
    ax.axvline(0.0, linewidth=1.0, linestyle="--")
    ax.set_xlabel(r"$\Delta$BIC = BIC$_{triangle}$ - BIC$_{chain}$")
    ax.set_ylabel("noise realizations")
    ax.set_title("Minimum-family selection")
    ax.text(
        0.03,
        0.95,
        f"chain selected {counts.get(TRUE_GRAPH, 0)}/{args.seeds}",
        transform=ax.transAxes,
        va="top",
        fontsize=8,
    )

    ax = axes[1]
    labels = list(rmse)
    ax.boxplot([rmse[label] for label in labels], tick_labels=labels, showfliers=False)
    ax.set_ylabel("held-out RMSE")
    ax.set_title("Unseen-forcing prediction")
    ax.tick_params(axis="x", rotation=25)

    ax = axes[2]
    shortcut_bins = np.geomspace(np.exp(-8.0), TRUE_CONDUCTANCE[0] * 1.05, 18)
    ax.hist(shortcut, bins=shortcut_bins)
    ax.axvline(np.exp(-8.0), linewidth=1.0, linestyle=":", label="optimizer lower bound")
    ax.axvline(TRUE_CONDUCTANCE[0], linewidth=1.0, linestyle="--", label="weaker true edge")
    ax.set_xscale("log")
    ax.set_xlabel("fitted triangle shortcut conductance")
    ax.set_ylabel("noise realizations")
    ax.set_title("Overconnected edge shrinkage")
    ax.legend(frameon=False, fontsize=7.5)

    fig.suptitle("Synthetic topology-recovery robustness ensemble", fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIGURES / "supplement_figure_S6_topology_ensemble.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIGURES / "supplement_figure_S6_topology_ensemble.pdf", bbox_inches="tight")
    plt.close(fig)

    if counts.get(TRUE_GRAPH, 0) != args.seeds:
        raise AssertionError("Training BIC did not select the chain in every declared realization.")
    if not all(result.optimizer_all_converged for result in results):
        raise AssertionError("At least one graph fit lacked an accepted optimizer run.")


if __name__ == "__main__":
    main()
