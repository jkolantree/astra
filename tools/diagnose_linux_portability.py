"""Diagnose Linux portability without changing frozen producers or accepting a baseline.

The independent sine/step convolution and segmented high-accuracy integration are
reference calculations only. Their agreement is not a tolerance waiver.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
TOL = 1e-12


def compare(a, b):
    summary = {}

    def walk(x, y, path=""):
        if type(x) is not type(y):
            summary.setdefault(path, {"type_changes": 0})["type_changes"] += 1
            return
        if isinstance(x, dict):
            if x.keys() != y.keys():
                raise RuntimeError("Schema drift")
            for k in x:
                walk(x[k], y[k], path + "/" + k)
        elif isinstance(x, list):
            if len(x) != len(y):
                raise RuntimeError("Length drift")
            for v, w in zip(x, y, strict=True):
                walk(v, w, path + "/*")
        elif isinstance(x, float):
            assert math.isfinite(x) and math.isfinite(y)
            if x == y:
                return
            delta = abs(x - y)
            limit = max(TOL, TOL * max(abs(x), abs(y)))
            s = summary.setdefault(
                path,
                {
                    "changed": 0,
                    "strict_failures": 0,
                    "max_absolute_delta": 0,
                    "max_strict_tolerance_multiple": 0,
                },
            )
            s["changed"] += 1
            s["strict_failures"] += delta > limit
            s["max_absolute_delta"] = max(s["max_absolute_delta"], delta)
            if delta / limit > s["max_strict_tolerance_multiple"]:
                s["max_strict_tolerance_multiple"] = delta / limit
                s["worst_pair"] = [x, y]
        elif x != y:
            s = summary.setdefault(path, {"discrete_changes": 0, "examples": []})
            s["discrete_changes"] += 1
            if len(s["examples"]) < 3 and [x, y] not in s["examples"]:
                s["examples"].append([x, y])

    walk(a, b)
    return summary


def oracle(model, edges, k, time, protocol):
    import numpy as np
    from scipy.linalg import expm

    if protocol not in {"train", "heldout"}:
        raise ValueError("Unknown forcing protocol")
    L = model.laplacian(edges, k)
    A = np.diag(1 / model.CAPACITY) @ (-L - np.diag([0.0, 0.0, model.SURFACE_SINK]))
    initial = model.equilibrium(edges, k, 0.0)
    E = expm(time[:, None, None] * A[None, :, :])
    output = np.repeat(initial[:, None], len(time), axis=1)
    drive = np.array([0.0, 0.0, 1 / model.CAPACITY[2]])
    sines = [(0.35, 0.55)] if protocol == "train" else [(0.28, 1.05), (0.22, 0.19)]
    steps = [(0.18, 10.0), (-0.12, 23.0)] if protocol == "train" else [(0.20, 6.0), (-0.20, 14.0)]
    for amplitude, omega in sines:
        q = np.linalg.solve(1j * omega * np.eye(3) - A, amplitude * drive)
        output += (np.exp(1j * omega * time)[:, None] * q[None, :] - E @ q).imag.T
    for amplitude, start in steps:
        mask = time > start
        elapsed = time[mask] - start
        transitions = expm(elapsed[:, None, None] * A[None, :, :]) - np.eye(3)
        contribution = np.linalg.solve(A, (transitions @ (amplitude * drive)).T)
        output[:, mask] += contribution
    return output


def segmented(rhs, span, y0, *, t_eval, **kwargs):
    import numpy as np
    from scipy.integrate import solve_ivp

    time = np.asarray(t_eval)
    out = np.empty((len(y0), len(time)))
    out[:, time == span[0]] = np.asarray(y0)[:, None]
    points = [span[0]] + [t for t in [6.0, 10.0, 14.0, 23.0] if span[0] < t < span[1]] + [span[1]]
    state = np.array(y0)
    nfev = 0
    for a, b in zip(points[:-1], points[1:], strict=True):
        mask = (time > a) & (time <= b)
        wanted = time[mask]
        nodes = np.unique(np.r_[wanted, b])

        def one_sided(t, y, a=a, b=b):
            return rhs(np.nextafter(a, b) if t == a else np.nextafter(b, a) if t == b else t, y)

        sol = solve_ivp(
            one_sided,
            (a, b),
            state,
            t_eval=nodes,
            method="DOP853",
            rtol=2.5e-14,
            atol=1e-15,
            max_step=0.025,
        )
        if not sol.success:
            raise RuntimeError(sol.message)
        out[:, mask] = sol.y[:, : len(wanted)]
        state = sol.y[:, -1]
        nfev += sol.nfev
    return SimpleNamespace(success=True, message="", y=out, t=time, nfev=nfev)


def main() -> None:
    if not sys.flags.isolated or not sys.dont_write_bytecode:
        raise RuntimeError("Run with -I -B")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay-root", type=Path, required=True)
    args = parser.parse_args()
    RUN = args.replay_root.resolve()
    sys.path.insert(0, str(ROOT))
    from tools.verify_linux import configure

    configure()
    import numpy as np

    from scripts import synthetic_topology_benchmark as model

    report = {
        "scope": "diagnostic only; no published outputs or scientific generators changed",
        "strict_comparison": {"rtol": TOL, "atol": TOL, "discrete": "exact"},
        "original_solver": {
            "single_ode_rtol": 1e-9,
            "single_ode_atol": 1e-11,
            "single_max_step": 0.05,
            "single_least_squares_xtol_ftol_gtol": 1e-11,
            "ensemble_least_squares_xtol_ftol_gtol": 2e-9,
            "accepted_scaled_optimality_limit": 1e-4,
            "observation_noise_sd": 0.0025,
        },
        "differences": {},
    }
    for name in ["synthetic_topology_benchmark.json", "synthetic_topology_ensemble.json"]:
        a = json.loads((ROOT / "data" / name).read_text())
        b = json.loads((RUN / "data" / name).read_text())
        report["differences"][name] = compare(a, b)
        if name.startswith("synthetic_topology_ensemble"):
            report["ensemble_conclusions"] = {
                key: {"historical": a[key], "linux": b[key], "exact": a[key] == b[key]}
                for key in [
                    "winner_counts",
                    "chain_selection_fraction",
                    "triangle_lower_heldout_rmse_count",
                    "triangle_shortcut_lower_bound_count",
                    "optimizer_all_graphs_converged",
                ]
            }
            report["ensemble_per_seed"] = {
                "same_winner": sum(
                    x["winner"] == y["winner"]
                    for x, y in zip(a["results"], b["results"], strict=True)
                ),
                "same_heldout_ordering": sum(
                    (x["triangle_heldout_rmse"] < x["chain_heldout_rmse"])
                    == (y["triangle_heldout_rmse"] < y["chain_heldout_rmse"])
                    for x, y in zip(a["results"], b["results"], strict=True)
                ),
                "same_shortcut_boundary_flag": sum(
                    x["triangle_shortcut_at_lower_bound"] == y["triangle_shortcut_at_lower_bound"]
                    for x, y in zip(a["results"], b["results"], strict=True)
                ),
            }

    old = json.loads((ROOT / "data/synthetic_topology_benchmark.json").read_text())[
        "fits_ranked_by_bic"
    ]
    new = json.loads((RUN / "data/synthetic_topology_benchmark.json").read_text())[
        "fits_ranked_by_bic"
    ]
    report["single_fit_diagnosis"] = []
    original_integrator = model.solve_ivp
    for before, after in zip(old, new, strict=True):
        name = before["graph"]
        assert name == after["graph"]
        edges = model.GRAPHS[name]
        record = {
            "graph": name,
            "metric_deltas": {
                key: after[key] - before[key]
                for key in ["train_rss", "train_rmse", "bic", "heldout_rmse"]
            },
            "accepted_starts": [before["optimizer_accepted"], after["optimizer_accepted"]],
            "selected_start": [before["optimizer_best_start"], after["optimizer_best_start"]],
            "conductance_pairs": list(
                zip(before["conductance"], after["conductance"], strict=True)
            ),
            "protocols": {},
        }
        for protocol, end, forcing in [
            ("train", 36.0, model.train_forcing),
            ("heldout", 26.0, model.heldout_forcing),
        ]:
            time = np.linspace(0, end, int(end * 10) + 1)
            k = np.array(after["conductance"])
            truth = oracle(model, edges, k, time, protocol)
            ordinary = model.simulate(edges, k, time, forcing)
            augmented, jac = model.simulate_with_log_conductance_sensitivities(
                edges, k, time, forcing
            )
            model.solve_ivp = segmented
            try:
                precise = model.simulate(edges, k, time, forcing)
                precise_augmented, precise_jac = model.simulate_with_log_conductance_sensitivities(
                    edges, k, time, forcing
                )
            finally:
                model.solve_ivp = original_integrator
            errors = {
                "default_state_vs_oracle_max_abs": float(np.max(abs(ordinary - truth))),
                "default_augmented_state_vs_oracle_max_abs": float(np.max(abs(augmented - truth))),
                "segmented_state_vs_oracle_max_abs": float(np.max(abs(precise - truth))),
                "segmented_augmented_state_vs_oracle_max_abs": float(
                    np.max(abs(precise_augmented - truth))
                ),
                "default_vs_segmented_sensitivity_max_abs": float(np.max(abs(jac - precise_jac))),
            }
            if (
                errors["segmented_state_vs_oracle_max_abs"] > 1e-10
                or errors["segmented_augmented_state_vs_oracle_max_abs"] > 1e-10
            ):
                raise RuntimeError("Independent forward references disagree")
            old_prediction = oracle(model, edges, np.array(before["conductance"]), time, protocol)
            delta = truth[2] - old_prediction[2]
            errors["old_vs_linux_fitted_surface_max_abs"] = float(np.max(abs(delta)))
            errors["old_vs_linux_fitted_surface_rms"] = float(np.sqrt(np.mean(delta**2)))
            errors["max_surface_shift_as_fraction_of_noise_sd"] = (
                errors["old_vs_linux_fitted_surface_max_abs"] / 0.0025
            )
            record["protocols"][protocol] = errors
        report["single_fit_diagnosis"].append(record)
        print("Diagnosed", name, flush=True)
    report["reference_method"] = (
        "Closed-form matrix-exponential convolution for declared sine/step forcing, cross-checked against discontinuity-segmented DOP853 at rtol=2.5e-14, atol=1e-15 and max_step=.025. The reference calculation does not refit or overwrite historical results."
    )
    output = ROOT / "tmp/linux-portability-diagnosis.json"
    report["input_sha256"] = {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in [
            "scripts/synthetic_topology_benchmark.py",
            "scripts/benchmark_ensemble.py",
            "src/astra_optimization.py",
            "RUNTIME.json",
            "RUNTIME-linux.json",
            "requirements-lock.txt",
        ]
    }
    report["replay_input_sha256"] = {
        name: hashlib.sha256((RUN / "data" / name).read_bytes()).hexdigest()
        for name in ["synthetic_topology_benchmark.json", "synthetic_topology_ensemble.json"]
    }
    output.write_text(json.dumps(report, indent=2) + "\n")
    print("Wrote tmp/linux-portability-diagnosis.json")


if __name__ == "__main__":
    main()
