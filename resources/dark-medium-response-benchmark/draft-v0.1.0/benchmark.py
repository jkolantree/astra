"""Canonical producer for the separate Draft response/null experiment (stdlib only)."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import random
import statistics
from fractions import Fraction as F
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CONFIG = HERE / "evaluation.json"
FREEZE = HERE / "frozen-evaluation.json"
RESULTS = HERE / "results.json"
SOURCE = ROOT / "resources/dark-medium-response-atlas/v0.1.0/dark-medium-response-atlas-v0.1.0.md"


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_config() -> dict[str, Any]:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if (
        platform.python_implementation() != "CPython"
        or platform.python_version() != config["python"]
    ):
        raise RuntimeError("Required CPython runtime unavailable")
    if config["python"] != json.loads((ROOT / "RUNTIME.json").read_text())["python"]:
        raise RuntimeError("Benchmark and repository runtime contracts differ")
    sampling = config["sampling"]
    for dimension in ("wave_numbers", "frequencies"):
        if set(sampling["training"][dimension]) & set(sampling["held_out"][dimension]):
            raise RuntimeError("Training and held-out split points overlap")
    if sampling["development_seed"] == sampling["evaluation_seed"]:
        raise RuntimeError("Development and evaluation seeds overlap")
    if sampling["repetitions"] != 64 or sampling["noise_component_sigma"] <= 0:
        raise RuntimeError("Unsupported repetition/noise contract")
    model = config["model"]
    if (model["mass_plus"], model["mass_minus"], model["number_density"]) != (1, 1, 1):
        raise RuntimeError("Evaluation supports the declared dimensionless equal masses only")
    if model["damping"] <= 0:
        raise RuntimeError("Evaluation requires positive symmetric damping")
    if len(library(config)) != config["inference"]["candidate_budget_per_fit"]:
        raise RuntimeError("Candidate budget mismatch")
    return config


def freeze_record(config: dict[str, Any]) -> dict[str, Any]:
    paths = [
        Path(__file__),
        CONFIG,
        ROOT / "tests/test_dark_medium_response_benchmark.py",
        ROOT / "RUNTIME.json",
        ROOT / "requirements-lock.txt",
        SOURCE,
    ]
    return {
        "candidate": config["candidate"],
        "status": "contract frozen before held-out scoring",
        "inputs": {p.relative_to(ROOT).as_posix(): digest(p) for p in paths},
        "runtime": {
            "implementation": platform.python_implementation(),
            "python": platform.python_version(),
        },
        "data_provenance": "synthetic primitive species response plus independently seeded Gaussian component noise",
        "identity_boundary": "input hashes exclude this record, results, root manifest and Git commit; outer manifest/commit bind outputs",
    }


def verify_freeze(config: dict[str, Any]) -> dict[str, Any]:
    if not FREEZE.is_file() or FREEZE.read_bytes() != canonical(freeze_record(config)):
        raise RuntimeError("Frozen evaluation input identity mismatch; new candidate/run required")
    return json.loads(FREEZE.read_text())


def library(config: dict[str, Any]) -> list[dict[str, Any]]:
    m = config["model"]
    return [
        {
            "id": f"p{pi}-d{di}",
            "c": m["mean_sound_squared"],
            "j": m["jeans_squared"],
            "p": p,
            "d": d,
            "gamma": m["damping"],
        }
        for pi, p in enumerate(m["charge_squared_frequency_grid"])
        for di, d in enumerate(m["half_sound_squared_difference_grid"])
    ]


def solve(matrix: list[list[complex]], rhs: list[complex]) -> list[complex]:
    """Pivoted elimination; used only by the primitive-species formulation."""
    a = [list(row) + [value] for row, value in zip(matrix, rhs, strict=True)]
    n = len(a)
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(a[row][col]))
        a[col], a[pivot] = a[pivot], a[col]
        divisor = a[col][col]
        if abs(divisor) < 1e-14:
            raise RuntimeError("Singular primitive response solve")
        a[col] = [value / divisor for value in a[col]]
        for row in range(n):
            if row != col:
                factor = a[row][col]
                a[row] = [x - factor * y for x, y in zip(a[row], a[col], strict=True)]
    return [row[-1] for row in a]


def response(
    theta: dict[str, Any], k: float, w: float, formulation: str, drive_amplitude: float = 1.0
) -> list[complex]:
    """Return mass/charge rows and mass/charge drive columns, row-major."""
    c, j, p, d, gamma = (theta[key] for key in ("c", "j", "p", "d", "gamma"))
    z = w * w + 1j * gamma * w
    if formulation == "response":
        a, b, e = c * k * k - j - z, d * k * k, c * k * k + p - z
        det = a * e - b * b
        if abs(det) < 1e-14:
            raise RuntimeError("Singular modal response")
        return [drive_amplitude * value / det for value in (e, -b, -b, a)]
    if formulation != "species":
        raise ValueError("Unknown formulation")
    # Direct Fourier continuity + momentum equations for densities n+/- and
    # velocities v+/-. Poisson/Gauss fields are eliminated in these coordinates.
    # For m=n0=1, 4*pi*G=j/2 and q^2=p/2. T maps densities to [R,Q].
    gravity, electric = j / 2, p / 2
    matrix = [
        [-1j * w, 0j, 1j * k, 0j],
        [0j, -1j * w, 0j, 1j * k],
        [
            1j * ((c + d) * k - gravity / k + electric / k),
            1j * (-gravity / k - electric / k),
            gamma - 1j * w,
            0j,
        ],
        [
            1j * (-gravity / k - electric / k),
            1j * ((c - d) * k - gravity / k + electric / k),
            0j,
            gamma - 1j * w,
        ],
    ]
    columns = []
    for fplus, fminus in ((0.5, 0.5), (0.5, -0.5)):
        solution = solve(
            matrix, [0j, 0j, 1j * drive_amplitude * fplus / k, 1j * drive_amplitude * fminus / k]
        )
        columns.append([solution[0] + solution[1], solution[0] - solution[1]])
    return [columns[0][0], columns[1][0], columns[0][1], columns[1][1]]


def observe(
    theta: dict[str, Any],
    design: dict[str, Any],
    operator: str,
    formulation: str,
    *,
    drive_amplitude: float = 1.0,
    sensor_gain: float = 1.0,
) -> list[complex]:
    values = []
    for k in design["wave_numbers"]:
        for w in design["frequencies"]:
            matrix = [
                sensor_gain * value for value in response(theta, k, w, formulation, drive_amplitude)
            ]
            values.extend(matrix if operator == "full_response" else matrix[:1])
    if operator not in ("mass_only", "full_response"):
        raise ValueError("Unknown observation operator")
    return values


def distance(left: list[complex], right: list[complex]) -> float:
    return max(abs(a - b) for a, b in zip(left, right, strict=True))


def fit(
    data: list[complex], candidates: list[list[complex]], sigma: float, tolerance: float
) -> list[int]:
    """No truth or held-out argument: fixed-budget Gaussian WLS enumeration."""
    costs = [
        sum(abs(y - mu) ** 2 for y, mu in zip(data, means, strict=True)) / sigma**2
        for means in candidates
    ]
    best = min(costs)
    if not all(math.isfinite(value) for value in costs):
        raise RuntimeError("Nonfinite fit cost")
    return [index for index, cost in enumerate(costs) if cost - best <= tolerance]


def score(data: list[complex], means: list[complex], sigma: float) -> float:
    return sum(abs(y - mu) ** 2 for y, mu in zip(data, means, strict=True)) / (
        2 * len(data) * sigma**2
    )


def derived_seed(base: int, repetition: int, truth: str, operator: str, split: str) -> int:
    return int(
        hashlib.sha256(f"{base}:{repetition}:{truth}:{operator}:{split}".encode()).hexdigest(), 16
    )


def noisy(means: list[complex], sigma: float, seed: int) -> list[complex]:
    rng = random.Random(seed)
    return [mu + complex(rng.gauss(0, sigma), rng.gauss(0, sigma)) for mu in means]


def interval(values: list[float]) -> dict[str, Any]:
    mean = statistics.mean(values)
    half_width = 1.99834 * statistics.stdev(values) / math.sqrt(len(values))
    return {
        "mean": mean,
        "approximate_95_percent_interval": [mean - half_width, mean + half_width],
        "independent_repetition_aggregates": len(values),
    }


def wilson(successes: int, n: int) -> dict[str, Any]:
    z = 1.959963984540054
    p = successes / n
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return {
        "successes": successes,
        "trials": n,
        "rate": p,
        "wilson_95_percent_interval": [max(0.0, center - half), min(1.0, center + half)],
    }


def rational_algebra() -> int:
    """Independent exact primitive density operator transformed by physical T."""
    cases = 0
    for mp, mm, cp, cm in ((1, 1, 1, 1), (2, 3, 1, 1), (2, 3, 2, 1), (1, 1, 0, 0), (2, 3, 0, 0)):
        mp, mm, cp, cm = map(F, (mp, mm, cp, cm))
        for gravity, charge in ((F(5, 7), F(3)), (F(0), F(3)), (F(5, 7), F(0))):
            n, k = F(2), F(7, 3)
            total, reduced, delta = mp + mm, mp * mm / (mp + mm), cp - cm
            primitive = [
                [
                    k * k * cp - gravity * n * mp + n * charge / mp,
                    -gravity * n * mm - n * charge / mp,
                ],
                [
                    -gravity * n * mp - n * charge / mm,
                    k * k * cm - gravity * n * mm + n * charge / mm,
                ],
            ]
            transform, inverse = (
                [[mp, mm], [F(1), F(-1)]],
                [[1 / total, mm / total], [1 / total, -mp / total]],
            )
            transformed = [
                [
                    sum(
                        transform[i][a] * primitive[a][b] * inverse[b][j]
                        for a in range(2)
                        for b in range(2)
                    )
                    for j in range(2)
                ]
                for i in range(2)
            ]
            expected = [
                [
                    k * k * (mp * cp + mm * cm) / total - gravity * n * total,
                    k * k * reduced * delta,
                ],
                [
                    k * k * delta / total,
                    k * k * (mm * cp + mp * cm) / total + charge * n * (1 / mp + 1 / mm),
                ],
            ]
            if transformed != expected:
                raise RuntimeError("Exact rational Atlas mode algebra failed")
            # The displayed eigenvalue discriminant equals trace^2 - 4 det.
            a, b, c, d = (
                transformed[0][0],
                transformed[0][1],
                transformed[1][0],
                transformed[1][1],
            )
            displayed = (a - d) ** 2 + 4 * k**4 * mp * mm * delta**2 / total**2
            if (a + d) ** 2 - 4 * (a * d - b * c) != displayed:
                raise RuntimeError("Exact eigenvalue discriminant failed")
            cases += 1
    return cases


def controls(config: dict[str, Any]) -> dict[str, Any]:
    tol = config["controls"]["algebra_tolerance"]
    candidates = library(config)
    design = config["sampling"]["training"]
    comparison_error = max(
        distance(
            observe(t, config["sampling"][split], "full_response", "species"),
            observe(t, config["sampling"][split], "full_response", "response"),
        )
        for t in candidates
        for split in ("training", "held_out")
    )
    stable = min(
        t["c"] * k * k
        + (t["p"] - t["j"]) / 2
        - math.sqrt(((t["p"] + t["j"]) / 2) ** 2 + (t["d"] * k * k) ** 2)
        for t in candidates
        for k in design["wave_numbers"]
    )
    symmetric = dict(candidates[1])
    changed_charge = dict(symmetric, p=symmetric["p"] * 3)
    plus, minus = dict(symmetric, d=0.2), dict(symmetric, d=-0.2)
    single_k = {"wave_numbers": [1.0], "frequencies": design["frequencies"]}
    second_k = {"wave_numbers": [1.4], "frequencies": design["frequencies"]}
    compensated = dict(plus, c=plus["c"] + 0.1, j=plus["j"] + 0.1, p=plus["p"] - 0.1)
    full = [observe(t, design, "full_response", "species") for t in candidates]
    noiseless = [
        fit(values, full, 0.04, config["inference"]["tie_cost_absolute_tolerance"])
        for values in full
    ]
    projected = [observe(t, design, "mass_only", "species") for t in candidates]
    classes = [
        [
            candidates[j]["id"]
            for j, other in enumerate(projected)
            if distance(values, other) < config["controls"]["observable_equivalence_tolerance"]
        ]
        for values in projected
    ]
    a = observe(plus, design, "full_response", "species")
    gain_compensation = distance(
        observe(plus, design, "full_response", "species", drive_amplitude=2, sensor_gain=1),
        observe(plus, design, "full_response", "species", drive_amplitude=4, sensor_gain=0.5),
    )
    # A separate known unit-amplitude calibration fixes gain; the unknown-drive
    # measurement alone fixes only their product. This is additional information.
    calibration = observe(
        plus, design, "full_response", "species", drive_amplitude=1, sensor_gain=2
    )
    calibrated_gain = sum(
        (value.conjugate() * measured).real for value, measured in zip(a, calibration, strict=True)
    ) / sum(abs(value) ** 2 for value in a)
    zero_predictions = [
        observe(t, design, "full_response", "species", drive_amplitude=0) for t in candidates
    ]
    zero_null = fit(zero_predictions[0], zero_predictions, 0.04, 1e-9)
    ratios = [F(3) * n * (F(1, 2) + F(1, 2)) / (F(5, 7) * n * F(4)) for n in (F(1), F(2), F(7))]
    result = {
        "exact_rational_algebra_cases": rational_algebra(),
        "max_independent_formulation_absolute_error": comparison_error,
        "minimum_undamped_squared_frequency": stable,
        "symmetric_cross_response_max": max(
            abs(response(symmetric, 1.0, w, "species")[1]) for w in design["frequencies"]
        ),
        "broken_pressure_cross_response_max": max(
            abs(response(plus, 1.0, w, "species")[1]) for w in design["frequencies"]
        ),
        "mass_only_charge_scale_difference_at_symmetry": distance(
            observe(symmetric, design, "mass_only", "species"),
            observe(changed_charge, design, "mass_only", "species"),
        ),
        "mass_only_mixing_sign_difference": distance(
            observe(plus, design, "mass_only", "species"),
            observe(minus, design, "mass_only", "species"),
        ),
        "full_response_mixing_sign_difference": distance(
            observe(plus, design, "full_response", "species"),
            observe(minus, design, "full_response", "species"),
        ),
        "single_k_compensation_difference": distance(
            observe(plus, single_k, "full_response", "species"),
            observe(compensated, single_k, "full_response", "species"),
        ),
        "second_k_compensation_difference": distance(
            observe(plus, second_k, "full_response", "species"),
            observe(compensated, second_k, "full_response", "species"),
        ),
        "gain_drive_compensation_difference": gain_compensation,
        "known_unit_drive_calibrated_gain": calibrated_gain,
        "zero_drive_equivalent_candidates": len(zero_null),
        "zero_drive_max_response": max(
            abs(value) for values in zero_predictions for value in values
        ),
        "density_independent_frequency_ratio_exact": len(set(ratios)) == 1,
        "noise_free_full_response_unique_recoveries": sum(
            match == [i] for i, match in enumerate(noiseless)
        ),
        "mass_only_exact_observational_classes": dict(
            zip((t["id"] for t in candidates), classes, strict=True)
        ),
    }
    near_zero = (
        "symmetric_cross_response_max",
        "mass_only_charge_scale_difference_at_symmetry",
        "mass_only_mixing_sign_difference",
        "single_k_compensation_difference",
        "gain_drive_compensation_difference",
        "zero_drive_max_response",
    )
    nonzero = (
        "broken_pressure_cross_response_max",
        "full_response_mixing_sign_difference",
        "second_k_compensation_difference",
    )
    if (
        comparison_error > tol
        or stable <= 0
        or any(result[key] > tol for key in near_zero)
        or any(result[key] < 1e-3 for key in nonzero)
        or len(zero_null) != len(candidates)
        or result["noise_free_full_response_unique_recoveries"] != len(candidates)
        or abs(calibrated_gain - 2.0) > tol
        or not result["density_independent_frequency_ratio_exact"]
    ):
        raise RuntimeError("Algebra/control harness failure")
    result["status"] = "PASS: declared algebra and controls only"
    return result


def run(config: dict[str, Any]) -> dict[str, Any]:
    frozen = verify_freeze(config)
    control_results = controls(config)
    candidates = library(config)
    sampling, inference = config["sampling"], config["inference"]
    sigma, repetitions = sampling["noise_component_sigma"], sampling["repetitions"]
    output = {}
    for operator in config["operators"]:
        predictions = {
            form: {
                split: [observe(t, sampling[split], operator, form) for t in candidates]
                for split in ("training", "held_out")
            }
            for form in ("species", "response")
        }
        stats = {
            t["id"]: {
                "truth_in_fitted_class": 0,
                "unique_true_recovery": 0,
                "retained_class_sizes": [],
            }
            for t in candidates
        }
        base_scores, response_scores, advantages = [], [], []
        score_difference_max = 0.0
        same_classes = 0
        for rep in range(repetitions):
            repetition_scores: dict[str, list[float]] = {"species": [], "response": []}
            for truth_index, truth in enumerate(candidates):
                data = {
                    split: noisy(
                        predictions["species"][split][truth_index],
                        sigma,
                        derived_seed(
                            sampling["evaluation_seed"], rep, truth["id"], operator, split
                        ),
                    )
                    for split in ("training", "held_out")
                }
                fits = {}
                for form in ("species", "response"):
                    fits[form] = fit(
                        data["training"],
                        predictions[form]["training"],
                        sigma,
                        inference["tie_cost_absolute_tolerance"],
                    )
                    repetition_scores[form].append(
                        score(data["held_out"], predictions[form]["held_out"][fits[form][0]], sigma)
                    )
                same_classes += fits["species"] == fits["response"]
                stat = stats[truth["id"]]
                stat["truth_in_fitted_class"] += truth_index in fits["response"]
                stat["unique_true_recovery"] += fits["response"] == [truth_index]
                stat["retained_class_sizes"].append(len(fits["response"]))
                score_difference_max = max(
                    score_difference_max,
                    abs(repetition_scores["species"][-1] - repetition_scores["response"][-1]),
                )
            baseline = statistics.mean(repetition_scores["species"])
            proposed = statistics.mean(repetition_scores["response"])
            base_scores.append(baseline)
            response_scores.append(proposed)
            advantages.append((baseline - proposed) / baseline)
        for stat in stats.values():
            for key in ("truth_in_fitted_class", "unique_true_recovery"):
                stat[key] = wilson(stat[key], repetitions)
            sizes = stat.pop("retained_class_sizes")
            stat["retained_class_size_range"] = [min(sizes), max(sizes)]
        advantage = interval(advantages)
        if (
            same_classes != repetitions * len(candidates)
            or score_difference_max > config["scoring"]["method_equivalence_tolerance"]
        ):
            raise RuntimeError(
                "Equivalent formulations disagree: harness failure, not comparative utility"
            )
        output[operator] = {
            "baseline_score": interval(base_scores),
            "response_score": interval(response_scores),
            "paired_relative_advantage": advantage,
            "practical_criterion_met": advantage["approximate_95_percent_interval"][0]
            > config["scoring"]["practical_relative_improvement"],
            "max_paired_absolute_score_difference": score_difference_max,
            "same_fitted_classes": same_classes,
            "paired_trials": repetitions * len(candidates),
            "recovery_by_fixed_truth": stats,
        }
    return {
        "candidate": config["candidate"],
        "status": "COMPLETED_SYNTHETIC_EXPERIMENT",
        "frozen_evaluation_sha256": digest(FREEZE),
        "input_identity": frozen,
        "numeric_engine": "CPython standard-library complex arithmetic, random.Random.gauss, and exact Fraction controls; no external numeric kernel",
        "controls": control_results,
        "evaluation": output,
        "comparative_utility": config["scoring"]["utility_claim"],
        "interpretation": "Additional drives/readouts resolve only the declared finite-library observational classes. Coordinate re-expression supplies no distinct method or general superiority result.",
        "scientific_ceiling": "Synthetic conditional fluid response only; no empirical validation, dark-matter detection, ontology, novelty, peer review, CRS superiority, core integration or publication authority.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--controls", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if sum((args.freeze, args.controls, args.check)) > 1:
        parser.error("Choose only one mode")
    config = read_config()
    if args.freeze:
        payload = canonical(freeze_record(config))
        if FREEZE.exists() and FREEZE.read_bytes() != payload:
            raise RuntimeError("Refusing to replace an existing frozen contract")
        FREEZE.write_bytes(payload)
        print(f"Frozen {config['candidate']}: {digest(FREEZE)}")
    elif args.controls:
        print(canonical(controls(config)).decode(), end="")
    else:
        payload = canonical(run(config))
        if args.check:
            if not RESULTS.is_file() or RESULTS.read_bytes() != payload:
                raise RuntimeError("Retained results do not reproduce")
            print(f"Reproduced {config['candidate']}: {digest(RESULTS)}")
        else:
            if RESULTS.exists() and RESULTS.read_bytes() != payload:
                raise RuntimeError("Refusing to replace different retained evaluation results")
            RESULTS.write_bytes(payload)
            print(f"Scored {config['candidate']}: {digest(RESULTS)}")


if __name__ == "__main__":
    main()
