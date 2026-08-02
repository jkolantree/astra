"""Generate every non-benchmark SPPT/ASTRA figure and its numeric data."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LogNorm  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RELEASE_SPEC = json.loads((ROOT / "RELEASE_SPEC.json").read_text(encoding="utf-8"))
VERSION = str(RELEASE_SPEC["version"])
sys.path.insert(0, str(ROOT / "src"))

import sppt_core as sppt  # noqa: E402
from astra_reservoir import (  # noqa: E402
    Edge,
    frequency_response,
    relaxation_spectrum,
    steady_state,
    step_response,
)

FIG = ROOT / "figures"
DATA = ROOT / "data"
FIG.mkdir(exist_ok=True)
DATA.mkdir(exist_ok=True)

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "figure.dpi": 120,
        "savefig.dpi": 300,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "svg.hashsalt": f"sppt-astra-v{VERSION}",
    }
)


def save_png(figure: plt.Figure, filename: str) -> None:
    figure.savefig(
        FIG / filename,
        bbox_inches="tight",
        metadata={"Software": f"SPPT-ASTRA reproducibility build v{VERSION}"},
    )
    plt.close(figure)


def diagram(
    filename: str,
    title: str,
    nodes: dict[str, tuple[float, float, str]],
    edges: list[tuple[str, str, str]],
    *,
    figsize: tuple[float, float] = (10.0, 6.0),
) -> None:
    figure, axis = plt.subplots(figsize=figsize)
    axis.set_xlim(0.0, 1.0)
    axis.set_ylim(0.0, 1.0)
    axis.axis("off")
    axis.set_title(title, fontsize=14, fontweight="bold", pad=14)
    for _, (x, y, label) in nodes.items():
        axis.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            fontsize=9.2,
            bbox={
                "boxstyle": "round,pad=0.45",
                "facecolor": "#F4F8FB",
                "edgecolor": "#1A4F7A",
                "linewidth": 1.2,
            },
            zorder=3,
        )
    for source, target, label in edges:
        x0, y0, _ = nodes[source]
        x1, y1, _ = nodes[target]
        axis.annotate(
            "",
            xy=(x1, y1),
            xytext=(x0, y0),
            arrowprops={
                "arrowstyle": "->",
                "color": "#4A4A4A",
                "linewidth": 1.1,
                "shrinkA": 24,
                "shrinkB": 24,
                "connectionstyle": "arc3,rad=0.0",
            },
            zorder=1,
        )
        if label:
            axis.text(
                (x0 + x1) / 2.0,
                (y0 + y1) / 2.0 + 0.022,
                label,
                ha="center",
                va="center",
                fontsize=7.3,
                color="#333333",
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.2, "alpha": 0.92},
                zorder=2,
            )
    save_png(figure, filename)


def figure_1_network() -> None:
    nodes = {
        "star": (0.50, 0.91, "Stellar forcing"),
        "surface": (0.50, 0.75, "Atmosphere / surface\nobservable boundary"),
        "ocean": (0.32, 0.54, "Ocean or magma\nreservoir"),
        "trap": (0.72, 0.54, "Condensate / phase trap"),
        "mantle": (0.32, 0.32, "Mantle reservoir"),
        "core": (0.32, 0.11, "Core reservoir"),
        "escape": (0.69, 0.30, "Escaping matter"),
        "space": (0.86, 0.15, "Radiative space"),
    }
    edges = [
        ("star", "surface", ""),
        ("surface", "ocean", ""),
        ("ocean", "mantle", ""),
        ("mantle", "core", ""),
        ("surface", "trap", ""),
        ("surface", "escape", ""),
        ("surface", "space", ""),
        ("ocean", "space", ""),
    ]
    diagram(
        "figure_1_phase_reservoir_network.png",
        "Illustrative phase-reservoir network",
        nodes,
        edges,
    )


def figure_2_trap_memory() -> None:
    c0, c1, omega = 1.0, 0.75, 1.0
    release_times = (0.25, 1.0, 4.0)
    time = np.linspace(0.0, 2.0 * np.pi / omega, 1200)
    capture = c0 + c1 * np.cos(omega * time)
    figure, axes = plt.subplots(1, 2, figsize=(10.2, 4.2))
    rows: list[dict[str, float]] = []
    for tau in release_times:
        inventory = sppt.trap_periodic_solution(time, c0, c1, omega, tau)
        axes[0].plot(time, inventory, label=rf"$\tau_r={tau:g}$")
        axes[1].plot(capture, inventory, label=rf"$\tau_r={tau:g}$")
        for t, c, m in zip(time, capture, inventory, strict=True):
            rows.append({"time": float(t), "release_time": tau, "capture": float(c), "inventory": float(m)})
    axes[0].set(xlabel="normalized time", ylabel="trapped inventory", title="Periodic inventory response")
    axes[1].set(xlabel="capture rate", ylabel="trapped inventory", title="Capture–inventory memory loops")
    for axis in axes:
        axis.legend(frameon=False)
    figure.suptitle("Periodic forcing creates phase lag and inventory memory", fontweight="bold")
    figure.tight_layout()
    save_png(figure, "figure_2_trap_memory_hysteresis.png")
    pd.DataFrame.from_records(rows).to_csv(
        DATA / "trap_memory_loops.csv", index=False, lineterminator="\n"
    )


def figure_3_bottleneck() -> None:
    cut_values = np.geomspace(1.0e-4, 1.0, 240)
    capacity = np.array([2.0, 3.0, 5.0, 7.0])
    incidence = sppt.incidence_matrix(4, [(0, 1), (1, 2), (2, 3)])
    eigenvalues = []
    bounds = []
    for cut in cut_values:
        spectrum = sppt.generalized_relaxation_eigenvalues(incidence, [4.0, cut, 6.0], capacity)
        eigenvalues.append(spectrum[1])
        bounds.append(sppt.weak_cut_upper_bound(cut, capacity[:2].sum(), capacity[2:].sum()))
    figure, axis = plt.subplots(figsize=(7.6, 4.8))
    axis.loglog(cut_values, eigenvalues, label=r"computed $\lambda_2$")
    axis.loglog(cut_values, bounds, "--", label="weak-cut upper bound")
    axis.set(
        xlabel="cut conductance",
        ylabel="slowest nonuniform decay rate",
        title="A weak conductance cut creates a long relaxation time",
    )
    axis.legend(frameon=False)
    figure.tight_layout()
    save_png(figure, "figure_3_spectral_bottleneck.png")
    pd.DataFrame(
        {"cut_conductance": cut_values, "lambda_2": eigenvalues, "upper_bound": bounds}
    ).to_csv(DATA / "spectral_bottleneck.csv", index=False, lineterminator="\n")


def figure_4_carbon_relay() -> None:
    nodes = {
        "carbonate": (0.50, 0.88, "CO₂ / carbonate\ngas, fluid, melt, mineral"),
        "reduced": (0.22, 0.63, "CO / CH₄ / organics"),
        "carbon": (0.58, 0.63, "Amorphous and sp² carbon"),
        "escape": (0.86, 0.63, "Atmospheric / plume escape"),
        "superionic": (0.20, 0.31, "C–H–O or C–H\nsuperionic phases"),
        "carbide": (0.50, 0.21, "Carbides and\nmetal–carbon phases"),
        "diamond": (0.80, 0.31, "Diamond / dense carbon"),
    }
    edges = [
        ("carbonate", "reduced", ""),
        ("carbonate", "carbon", ""),
        ("carbonate", "escape", ""),
        ("reduced", "superionic", ""),
        ("carbon", "carbide", ""),
        ("carbon", "diamond", ""),
        ("carbonate", "superionic", ""),
    ]
    diagram(
        "figure_4_carbon_phase_relay.png",
        "Carbon Phase Relay: candidate reservoirs and pathways",
        nodes,
        edges,
        figsize=(11.0, 6.5),
    )


STATIC_DEGENERACY_CAPACITIES = [1.0, 20.0]
STATIC_DEGENERACY_LOSS = [1.0, 0.0]
STATIC_DEGENERACY_POWER = [0.0, 1.0]


def static_degeneracy_equilibrium(coupling: float) -> np.ndarray:
    """Return the surface/deep equilibrium for unit deep internal power."""
    return steady_state(
        STATIC_DEGENERACY_CAPACITIES,
        [Edge(0, 1, coupling)],
        STATIC_DEGENERACY_LOSS,
        STATIC_DEGENERACY_POWER,
    )


def figure_5_static_degeneracy() -> None:
    times = np.linspace(0.0, 500.0, 900)
    couplings = [0.05, 0.20, 1.00]
    figure, axes = plt.subplots(1, 2, figsize=(10.2, 4.2))
    rows: list[dict[str, float]] = []
    equilibria = []
    for coupling in couplings:
        states = step_response(
            STATIC_DEGENERACY_CAPACITIES,
            [Edge(0, 1, coupling)],
            STATIC_DEGENERACY_LOSS,
            STATIC_DEGENERACY_POWER,
            times,
        )
        axes[0].plot(times, states[:, 0], label=rf"$K={coupling:g}$")
        equilibria.append(static_degeneracy_equilibrium(coupling))
        for time_value, surface, deep in zip(times, states[:, 0], states[:, 1], strict=True):
            rows.append(
                {
                    "time": float(time_value),
                    "conductance": coupling,
                    "surface_state": float(surface),
                    "deep_state": float(deep),
                }
            )
    axes[0].axhline(1.0, color="black", linestyle="--", linewidth=1.0, label="common surface equilibrium")
    axes[0].set(xlabel="normalized time", ylabel="surface state", title="Transients depend on conductance")
    axes[0].legend(frameon=False, fontsize=8)
    axes[1].semilogx(
        couplings, [state[0] for state in equilibria], "o-", label="surface equilibrium"
    )
    axes[1].semilogx(
        couplings, [state[1] for state in equilibria], "s-", label="deep equilibrium"
    )
    axes[1].set(xlabel="conductance $K$", ylabel="equilibrium state", title="One boundary value hides deep states")
    axes[1].legend(frameon=False)
    figure.suptitle("Static boundary degeneracy and transient resolution", fontweight="bold")
    figure.tight_layout()
    save_png(figure, "figure_5_static_degeneracy_transient_resolution.png")
    pd.DataFrame.from_records(rows).to_csv(
        DATA / "two_reservoir_step_response.csv", index=False, lineterminator="\n"
    )


def figure_6_inference() -> None:
    nodes = {
        "inputs": (0.10, 0.55, "Declared observables\nand uncertainties"),
        "candidates": (0.30, 0.55, "Physically admissible\ngraph candidates"),
        "fit": (0.50, 0.55, "Training-only fit\nand diagnostics"),
        "checks": (0.70, 0.55, "Closure, calibration,\nnegative controls"),
        "heldout": (0.90, 0.55, "Held-out prediction\nor demotion"),
    }
    edges = [
        ("inputs", "candidates", ""),
        ("candidates", "fit", ""),
        ("fit", "checks", ""),
        ("checks", "heldout", ""),
    ]
    diagram(
        "figure_6_topology_aware_inference.png",
        "ASTRA promotion workflow",
        nodes,
        edges,
        figsize=(12.0, 3.5),
    )


def figure_7_feedback() -> None:
    deep = np.linspace(2.1, 8.0, 1000)
    upper = 2.0
    midpoint, width = 5.0, 0.32
    connectivity = 1.0 / (1.0 + np.exp((deep - midpoint) / width))
    dconnectivity = -connectivity * (1.0 - connectivity) / width
    k_min, k_span = 0.05, 1.0
    conductance = k_min + k_span * connectivity
    flux = conductance * (deep - upper)
    slope = np.array(
        [
            sppt.effective_flux_slope(td - upper, psi, dpsi, k_min, k_span, 0.0)
            for td, psi, dpsi in zip(deep, connectivity, dconnectivity, strict=True)
        ]
    )
    figure, axes = plt.subplots(1, 2, figsize=(10.0, 4.2))
    axes[0].plot(deep, connectivity, label=r"connectivity $\psi$")
    axes[0].plot(deep, conductance, label=r"conductance $K(\psi)$")
    axes[0].set(xlabel="deep temperature", ylabel="normalized state", title="State-dependent edge")
    axes[0].legend(frameon=False)
    axes[1].plot(deep, flux, label="transported flux")
    axes[1].plot(deep, slope, label=r"$dq/dT_d$")
    axes[1].axhline(0.0, color="black", linewidth=0.8)
    axes[1].fill_between(deep, slope, 0.0, where=slope < 0.0, color="#D55E00", alpha=0.25, label="negative slope")
    axes[1].set(xlabel="deep temperature", ylabel="normalized flux / slope", title="Local negative differential transport")
    axes[1].legend(frameon=False, fontsize=8)
    figure.suptitle("Illustrative fixed-upper-state feedback closure", fontweight="bold")
    figure.tight_layout()
    save_png(figure, "figure_7_state_dependent_transport_feedback.png")
    pd.DataFrame(
        {
            "deep_temperature": deep,
            "upper_temperature": upper,
            "connectivity": connectivity,
            "conductance": conductance,
            "transported_flux": flux,
            "flux_slope": slope,
        }
    ).to_csv(DATA / "state_dependent_transport.csv", index=False, lineterminator="\n")


def figure_s4_s5_frequency_response() -> None:
    frequencies = np.logspace(-3.0, 1.5, 500)
    omega = 2.0 * np.pi * frequencies
    configurations = {
        "one effective reservoir": ([1.0], [], [1.0], [1.0], [1.0]),
        "weakly coupled deep reservoir": ([1.0, 20.0], [Edge(0, 1, 0.05)], [1.0, 0.0], [1.0, 0.0], [1.0, 0.0]),
        "strongly coupled deep reservoir": ([1.0, 20.0], [Edge(0, 1, 1.0)], [1.0, 0.0], [1.0, 0.0], [1.0, 0.0]),
    }
    rows: list[dict[str, float | str]] = []
    responses: dict[str, np.ndarray] = {}
    for name, (capacity, edges, loss, input_vector, output_vector) in configurations.items():
        response = frequency_response(capacity, edges, loss, input_vector, output_vector, omega)
        responses[name] = response
        for frequency, value in zip(frequencies, response, strict=True):
            rows.append(
                {
                    "frequency": float(frequency),
                    "model": name,
                    "amplitude": float(abs(value)),
                    "phase_radians": float(np.angle(value)),
                }
            )

    figure, axis = plt.subplots(figsize=(8.0, 5.2))
    for name, response in responses.items():
        axis.loglog(frequencies, np.abs(response), label=name)
    axis.set(xlabel="forcing frequency (cycles per unit time)", ylabel="response amplitude", title="Frequency response reveals hidden reservoir modes")
    axis.legend(frameon=False)
    figure.tight_layout()
    save_png(figure, "supplement_figure_S4_frequency_response_amplitude.png")

    figure, axis = plt.subplots(figsize=(8.0, 5.2))
    for name, response in responses.items():
        axis.semilogx(frequencies, np.degrees(np.angle(response)), label=name)
    axis.set(xlabel="forcing frequency (cycles per unit time)", ylabel="phase lag (degrees)", title="Phase lag separates transport-connectivity regimes")
    axis.legend(frameon=False)
    figure.tight_layout()
    save_png(figure, "supplement_figure_S5_frequency_response_phase.png")
    pd.DataFrame.from_records(rows).to_csv(
        DATA / "frequency_response.csv", index=False, lineterminator="\n"
    )


def inverse_response(c_deep: float, coupling: float, frequencies: np.ndarray) -> np.ndarray:
    return frequency_response(
        [1.0, c_deep],
        [Edge(0, 1, coupling)],
        [1.0, 0.0],
        [1.0, 0.0],
        [1.0, 0.0],
        2.0 * np.pi * frequencies,
    )


def figure_s2_s3_inverse() -> None:
    true_c, true_k = 20.0, 0.2
    single_f = np.array([0.003])
    multi_f = np.logspace(-3.0, 0.8, 24)
    single_true = inverse_response(true_c, true_k, single_f)
    multi_true = inverse_response(true_c, true_k, multi_f)
    c_grid = np.geomspace(2.0, 80.0, 180)
    k_grid = np.geomspace(0.015, 2.0, 180)
    single_objective = np.empty((k_grid.size, c_grid.size))
    multi_objective = np.empty_like(single_objective)
    sigma_amplitude = 0.01 * float(abs(single_true[0]))
    sigma_complex = 0.02 * np.maximum(np.abs(multi_true), 0.02)
    rows: list[dict[str, float]] = []
    for row_index, coupling in enumerate(k_grid):
        for column_index, capacity in enumerate(c_grid):
            single = inverse_response(float(capacity), float(coupling), single_f)
            multi = inverse_response(float(capacity), float(coupling), multi_f)
            single_objective[row_index, column_index] = (
                (abs(single[0]) - abs(single_true[0])) / sigma_amplitude
            ) ** 2
            multi_objective[row_index, column_index] = float(
                np.sum(np.abs((multi - multi_true) / sigma_complex) ** 2)
            )
            rows.append(
                {
                    "deep_capacity": float(capacity),
                    "coupling": float(coupling),
                    "single_frequency_objective": float(single_objective[row_index, column_index]),
                    "multi_frequency_objective": float(multi_objective[row_index, column_index]),
                }
            )

    def landscape(values: np.ndarray, title: str, filename: str) -> None:
        delta = values - float(np.nanmin(values)) + 1.0e-4
        vmax = max(float(np.nanpercentile(delta, 99.0)), 1.0)
        figure, axis = plt.subplots(figsize=(8.1, 5.6))
        mesh = axis.pcolormesh(
            c_grid,
            k_grid,
            delta,
            shading="auto",
            norm=LogNorm(vmin=1.0e-4, vmax=vmax),
        )
        contours = axis.contour(c_grid, k_grid, delta, levels=[2.30, 6.18, 11.83], linewidths=1.0)
        axis.clabel(contours, inline=True, fontsize=8)
        axis.set_xscale("log")
        axis.set_yscale("log")
        axis.set_xticks([2.0, 5.0, 10.0, 20.0, 50.0])
        axis.set_xticklabels(["2", "5", "10", "20", "50"])
        axis.tick_params(axis="x", which="minor", labelbottom=False)
        axis.scatter([true_c], [true_k], marker="x", s=90, linewidths=2.0, label="generating model")
        axis.set(xlabel="deep-reservoir capacity", ylabel="surface–deep coupling", title=title)
        figure.colorbar(mesh, ax=axis, label=r"$\Delta\chi^2$ (log scale)")
        axis.legend(frameon=False)
        figure.tight_layout()
        save_png(figure, filename)

    landscape(
        single_objective,
        "One low-frequency amplitude leaves a broad parameter degeneracy",
        "supplement_figure_S2_single_frequency_degeneracy.png",
    )
    landscape(
        multi_objective,
        "Multi-frequency amplitude and phase localize the hidden reservoir",
        "supplement_figure_S3_multifrequency_localization.png",
    )
    pd.DataFrame.from_records(rows).to_csv(
        DATA / "inverse_objective_landscapes.csv", index=False, lineterminator="\n"
    )
    single_best = np.unravel_index(np.argmin(single_objective), single_objective.shape)
    multi_best = np.unravel_index(np.argmin(multi_objective), multi_objective.shape)
    summary = {
        "note": "Synthetic normalized demonstration; no planetary data are used.",
        "true_parameters": {"deep_capacity": true_c, "coupling": true_k},
        "single_frequency": float(single_f[0]),
        "multi_frequency_count": int(multi_f.size),
        "single_best_grid_point": {
            "deep_capacity": float(c_grid[single_best[1]]),
            "coupling": float(k_grid[single_best[0]]),
        },
        "multi_best_grid_point": {
            "deep_capacity": float(c_grid[multi_best[1]]),
            "coupling": float(k_grid[multi_best[0]]),
        },
    }
    (DATA / "inverse_demo_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


def summary_json() -> None:
    rates, times = relaxation_spectrum([1.0, 20.0], [Edge(0, 1, 0.2)], [1.0, 0.0])
    summary = {
        "model": "two-reservoir normalized demonstration",
        "capacities": [1.0, 20.0],
        "surface_loss": 1.0,
        "coupling": 0.2,
        "decay_rates": rates.tolist(),
        "relaxation_times": times.tolist(),
        "note": "Synthetic demonstration only; parameters are dimensionless and are not fitted to a planet.",
    }
    (DATA / "demo_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


def main() -> None:
    figure_1_network()
    figure_2_trap_memory()
    figure_3_bottleneck()
    figure_4_carbon_relay()
    figure_5_static_degeneracy()
    figure_6_inference()
    figure_7_feedback()
    figure_s2_s3_inverse()
    figure_s4_s5_frequency_response()
    summary_json()
    print(f"Wrote figures to {FIG}")
    print(f"Wrote data to {DATA}")


if __name__ == "__main__":
    main()
