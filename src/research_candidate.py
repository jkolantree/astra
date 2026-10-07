"""ASTRA research integration candidate v0.2.0.

Synthetic audit instruments, not plume physics or empirical framework validation.
NumPy/SciPy are used for declared numerical calculations. No network or file
mutation occurs on import. See the protocol and verification records for scope.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypedDict

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.stats import norm


class FrozenTransferMap(TypedDict):
    tau_s: float
    amplitude_K: float
    source_shape: float
    training_root: str
    calibration_root: str
    uses_target_holdout_labels: bool


class MonteCarloReplicate(TypedDict):
    replicate: int
    joint_logscore_A_minus_B: float
    joint_logscore_A_minus_B_when_B_true: float
    main_channel_gap: float
    preferred: str


VERSION = "0.2.0"
LAYERS = {"physical", "control", "observation", "archive", "provenance", "verification"}


@dataclass(frozen=True)
class QuantityType:
    space: str
    quantity: str
    unit: str
    basis: tuple[str, ...]

    def validate(self) -> None:
        if not all(
            isinstance(x, str) and x.strip() for x in (self.space, self.quantity, self.unit)
        ):
            raise ValueError("space, quantity and unit must be explicit")
        if not self.basis or not all(isinstance(x, str) and x for x in self.basis):
            raise ValueError("basis must be nonempty named coordinates")
        if len(set(self.basis)) != len(self.basis):
            raise ValueError("basis coordinates must be unique")


@dataclass(frozen=True)
class Operator:
    operator_id: str
    input_type: QuantityType
    output_type: QuantityType
    layer: str
    kind: str
    matrix: tuple[tuple[float, ...], ...]
    calibration_root: str
    version: str = "synthetic-0.2.0"

    def validate(self) -> np.ndarray:
        self.input_type.validate()
        self.output_type.validate()
        if (
            self.layer not in LAYERS
            or not self.operator_id
            or not self.calibration_root
            or not self.version
        ):
            raise ValueError("operator identity, layer, version and calibration root required")
        m = np.asarray(self.matrix, dtype=float)
        if m.shape != (len(self.output_type.basis), len(self.input_type.basis)):
            raise ValueError("matrix shape does not match declared bases")
        if not np.all(np.isfinite(m)) or np.any(m < 0):
            raise ValueError("operator must be finite and nonnegative")
        a, b = self.input_type, self.output_type
        if self.kind in {"mass-transfer", "selection"}:
            if (
                a.unit != "kg"
                or b.unit != "kg"
                or a.quantity != "tracer-mass"
                or b.quantity != a.quantity
            ):
                raise ValueError("mass/selection maps require compatible tracer mass in kg")
            required_layer = "physical" if self.kind == "mass-transfer" else "observation"
            if self.layer != required_layer:
                raise ValueError("a selection map is not a physical flux edge")
            if np.any(m.sum(axis=0) > 1 + 1e-12):
                raise ValueError("substochastic tracer map cannot create tracer mass")
        elif self.kind == "detector-response":
            if self.layer != "observation" or a.unit != "kg" or b.unit != "count":
                raise ValueError("detector response maps kg to expected counts")
            if a.quantity != "tracer-mass" or b.quantity != "expected-count":
                raise ValueError("same endpoint names cannot override quantity semantics")
        else:
            raise ValueError("unsupported operator kind; no analogy or generic cast is admitted")
        return m


def validate_chain(operators: list[Operator]) -> None:
    if not operators:
        raise ValueError("empty operator chain")
    ids = [x.operator_id for x in operators]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate operator identity")
    for i, op in enumerate(operators):
        op.validate()
        if i and operators[i - 1].output_type != op.input_type:
            raise ValueError("composition must match space, quantity, unit and ordered basis")
    if operators[0].input_type.unit != "kg" or operators[-1].kind != "detector-response":
        raise ValueError("audited chain must start in tracer mass and end in detector counts")
    if any(op.kind == "detector-response" for op in operators[:-1]):
        raise ValueError("detector response is terminal for this bounded chain")


def forward_chain(source_mass: Any, operators: list[Operator]) -> dict[str, Any]:
    validate_chain(operators)
    x = np.asarray(source_mass, dtype=float)
    if (
        x.shape != (len(operators[0].input_type.basis),)
        or not np.all(np.isfinite(x))
        or np.any(x < 0)
    ):
        raise ValueError("source must be finite nonnegative mass on the declared basis")
    initial_mass = float(x.sum())
    if initial_mass <= 0:
        raise ValueError("positive total tracer mass required")
    stages, outside, unobserved = [], 0.0, 0.0
    selected_mass = initial_mass
    for op in operators:
        before = float(x.sum())
        x = op.validate() @ x
        record = {"operator_id": op.operator_id, "output": x.tolist(), "unit": op.output_type.unit}
        if op.kind != "detector-response":
            omitted = before - float(x.sum())
            record["unmodeled_or_unobserved_mass_kg"] = omitted
            if op.kind == "selection":
                unobserved += omitted
            else:
                outside += omitted
            selected_mass = float(x.sum())
        stages.append(record)
    counts = float(x.sum())
    if not math.isfinite(counts):
        raise ValueError("expected counts overflowed")
    return {
        "stages": stages,
        "expected_counts": x.tolist(),
        "normalized_count_response": (x / counts).tolist() if counts > 0 else None,
        "observation_model_status": "first-moment-only",
        "no_record_probability": None,
        "normalization_status": "defined" if counts > 0 else "undefined-zero-expected-counts",
        "initial_mass_kg": initial_mass,
        "selected_mass_kg": selected_mass,
        "outside_tracked_mass_kg": outside,
        "unobserved_mass_kg": unobserved,
        "mass_closure_residual_kg": initial_mass - float(selected_mass) - outside - unobserved,
    }


def synthetic_operators() -> list[Operator]:
    """Six maps; conversion redistributes tracer labels, not chemical species.

    A single synthetic tracer is allocated among three categories. Only total
    tracer mass is conserved; categories can change. A/B/C are not salt species.
    This is a mass-ledger scaffold and does not supply salt kinetics, size bins,
    fragmentation multiplicities, latent heat or Cassini response calibration.
    """
    basis = ("A", "B", "C")
    names = ["ocean", "droplets", "phase-partition", "fragments", "transported", "selected"]
    types = [QuantityType(n, "tracer-mass", "kg", basis) for n in names]
    mats = [
        np.diag([0.85, 0.75, 0.95]),
        np.array([[0.85, 0.08, 0.02], [0.10, 0.87, 0.13], [0.05, 0.05, 0.85]]),
        np.diag([0.95, 0.90, 0.85]),
        np.diag([0.90, 0.70, 0.80]),
        np.diag([0.30, 0.85, 0.55]),
    ]
    ids = [
        "droplet-formation",
        "phase-partition-placeholder",
        "fragmentation-placeholder",
        "transport",
        "grain-selection",
    ]
    ops = [
        Operator(
            ids[i],
            types[i],
            types[i + 1],
            "observation" if i == 4 else "physical",
            "selection" if i == 4 else "mass-transfer",
            tuple(map(tuple, mats[i])),
            "synthetic:declared-matrices",
        )
        for i in range(5)
    ]
    response = np.array([[800, 30, 0], [50, 1000, 40], [0, 20, 650]], dtype=float)
    ops.append(
        Operator(
            "detector-response",
            types[-1],
            QuantityType("detector", "expected-count", "count", basis),
            "observation",
            "detector-response",
            tuple(map(tuple, response)),
            "synthetic:detector-response",
        )
    )
    return ops


def hybrid_archive(
    times: Any,
    *,
    production: float = 1.0,
    decay: float = 0.2,
    events: tuple[tuple[float, float], ...] = ((2.0, 0.25),),
) -> dict[str, Any]:
    """Clock guards t=t_e reset record stock a+ = r*a-.

    a'=production-decay*a between events. Finite ordered distinct clock guards
    are required. All stock units are synthetic record-equivalents, not energy
    or physical entropy. Erasure and background attrition are separate ledgers.
    """
    t = np.asarray(times, dtype=float)
    if (
        t.ndim != 1
        or len(t) < 2
        or t[0] != 0
        or np.any(np.diff(t) <= 0)
        or not np.all(np.isfinite(t))
    ):
        raise ValueError("finite strictly increasing grid starting at zero required")
    if not all(math.isfinite(v) and v >= 0 for v in (production, decay)):
        raise ValueError("finite nonnegative production/decay required")
    prev_event = -1.0
    for et, r in events:
        if (
            not math.isfinite(et)
            or et <= prev_event
            or not 0 < et <= t[-1]
            or not math.isfinite(r)
            or not 0 <= r <= 1
        ):
            raise ValueError("finite distinct ordered guards and retention in [0,1] required")
        prev_event = et
    a, last, attrition, erased, ei = 0.0, 0.0, 0.0, 0.0, 0
    trace, resets = [], []

    def advance(dt: float) -> None:
        nonlocal a, attrition
        before = a
        a = (
            a + production * dt
            if decay == 0
            else a * math.exp(-decay * dt) + production * (-math.expm1(-decay * dt)) / decay
        )
        attrition += production * dt - (a - before)

    for target in t:
        while ei < len(events) and events[ei][0] <= target:
            et, r = events[ei]
            advance(et - last)
            last = et
            before = a
            a *= r
            loss = before - a
            erased += loss
            resets.append(
                {"guard_time": et, "pre": before, "post": a, "erased": loss, "retention": r}
            )
            ei += 1
        advance(float(target) - last)
        last = float(target)
        trace.append(
            {
                "time": last,
                "stock": a,
                "erased_cumulative": erased,
                "attrition_cumulative": attrition,
            }
        )
    return {
        "trace": trace,
        "resets": resets,
        "unit": "synthetic record-equivalent",
        "balance_residual": production * float(t[-1]) - a - erased - attrition,
    }


def fit_shape(time: Any, response: Any, tau: float, amplitude: float) -> float:
    t, y = np.asarray(time, float), np.asarray(response, float)
    if (
        t.shape != y.shape
        or t.ndim != 1
        or len(t) < 3
        or not np.all(np.isfinite(t))
        or not np.all(np.isfinite(y))
    ):
        raise ValueError("finite matched source-training arrays required")
    if tau <= 0 or amplitude <= 0 or not math.isfinite(tau + amplitude):
        raise ValueError("positive finite independently supplied scales required")

    def f(k: float) -> float:
        return float(np.sum((y - amplitude * (-np.expm1(-k * t / tau))) ** 2))

    r = minimize_scalar(f, bounds=(0.2, 3.0), method="bounded")
    if not r.success:
        raise ValueError("shape fit failed")
    return float(r.x)


def transfer_prediction(
    target_time: Any, shape: float, frozen_tau: float, frozen_amplitude: float
) -> np.ndarray:
    t = np.asarray(target_time, float)
    if (
        not np.all(np.isfinite(t))
        or np.any(t < 0)
        or not all(math.isfinite(x) and x > 0 for x in (shape, frozen_tau, frozen_amplitude))
    ):
        raise ValueError("finite nonnegative time and positive frozen scales required")
    return frozen_amplitude * (-np.expm1(-shape * t / frozen_tau))


def common_unit_rmse(
    truth: Any, prediction: Any, *, truth_unit: str, prediction_unit: str
) -> float:
    if not truth_unit or truth_unit != prediction_unit:
        raise ValueError("both arrays must be explicitly expressed in the same target unit")
    a, b = np.asarray(truth, float), np.asarray(prediction, float)
    if (
        a.shape != b.shape
        or a.size == 0
        or not np.all(np.isfinite(a))
        or not np.all(np.isfinite(b))
    ):
        raise ValueError("finite matched nonempty arrays required")
    return float(np.sqrt(np.mean((a - b) ** 2)))


def frozen_transfer_pipeline(
    *,
    source_time: Any,
    source_response: Any,
    source_tau: float,
    source_amplitude: float,
    calibration_tau: Any,
    calibration_amplitude: Any,
    target_time: Any,
    target_response: Any,
    training_root: str,
    calibration_root: str,
    holdout_root: str,
) -> dict[str, Any]:
    """Fit/freeze using source and calibration only; holdout labels score last.

    Distinct root labels are a structural guard, not authenticated provenance.
    This bounded synthetic adapter does not establish empirical independence.
    """
    roots = [training_root, calibration_root, holdout_root]
    if any(not isinstance(x, str) or not x.strip() for x in roots) or len(set(roots)) != 3:
        raise ValueError("distinct explicit training/calibration/holdout roots required")
    tau = np.asarray(calibration_tau, float)
    amp = np.asarray(calibration_amplitude, float)
    if any(
        x.ndim != 1 or x.size == 0 or not np.all(np.isfinite(x)) or np.any(x <= 0)
        for x in [tau, amp]
    ):
        raise ValueError("positive finite calibration sample vectors required")
    k = fit_shape(source_time, source_response, source_tau, source_amplitude)
    frozen: FrozenTransferMap = {
        "tau_s": float(tau.mean()),
        "amplitude_K": float(amp.mean()),
        "source_shape": k,
        "training_root": training_root,
        "calibration_root": calibration_root,
        "uses_target_holdout_labels": False,
    }
    digest = hashlib.sha256(json.dumps(frozen, sort_keys=True).encode()).hexdigest()
    prediction = transfer_prediction(target_time, k, frozen["tau_s"], frozen["amplitude_K"])
    score = common_unit_rmse(target_response, prediction, truth_unit="K", prediction_unit="K")
    return {
        "frozen_map": frozen,
        "frozen_map_sha256": digest,
        "prediction": prediction.tolist(),
        "rmse_K": score,
        "holdout_root": holdout_root,
        "provenance_status": "declared-synthetic",
    }


def scale_transfer(seed: int) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    source_t = np.linspace(0.1, 6.0, 100)
    source_y = transfer_prediction(source_t, 1.0, 2.0, 4.0) + rng.normal(0, 0.03, len(source_t))
    # Independent metrology replicates, not the target-response holdout.
    tau_samples = rng.normal(17.0, 0.20, 12)
    amp_samples = rng.normal(0.60, 0.008, 12)
    target_t = np.linspace(0.4, 25.5, 250)
    true = transfer_prediction(target_t, 1.0, 17.0, 0.60)
    target_y = true + rng.normal(0, 0.008, len(target_t))
    result = frozen_transfer_pipeline(
        source_time=source_t,
        source_response=source_y,
        source_tau=2.0,
        source_amplitude=4.0,
        calibration_tau=tau_samples,
        calibration_amplitude=amp_samples,
        target_time=target_t,
        target_response=target_y,
        training_root="synthetic:source-training",
        calibration_root="synthetic:independent-metrology-12",
        holdout_root="synthetic:target-holdout",
    )
    frozen, freeze_hash = result["frozen_map"], result["frozen_map_sha256"]
    k = frozen["source_shape"]
    pred = np.asarray(result["prediction"])
    raw = transfer_prediction(target_t, k, 2.0, 4.0)
    misspecified = transfer_prediction(target_t, 1.35, 17.0, 0.60)
    return {
        "frozen_map": frozen,
        "frozen_map_sha256": freeze_hash,
        "score_unit": "K",
        "transfer_rmse_K": common_unit_rmse(target_y, pred, truth_unit="K", prediction_unit="K"),
        "raw_control_rmse_K": common_unit_rmse(target_y, raw, truth_unit="K", prediction_unit="K"),
        "changed_shape_truth_rmse_K": common_unit_rmse(
            misspecified, pred, truth_unit="K", prediction_unit="K"
        ),
        "negative_control": "raw source scales are deliberately mismatched; not a best empirical competitor",
        "trace": {
            "target_time_s": target_t.tolist(),
            "response_K": target_y.tolist(),
            "transferred_K": pred.tolist(),
            "raw_control_K": raw.tolist(),
        },
    }


def joint_logscore_gap(observed: Any, model_a: Any, model_b: Any, covariance: Any) -> float:
    y, a, b, c = map(lambda x: np.asarray(x, float), (observed, model_a, model_b, covariance))
    if (
        y.ndim != 2
        or y.shape != a.shape
        or y.shape != b.shape
        or c.shape != (y.shape[1], y.shape[1])
    ):
        raise ValueError("channel/time dimensions inconsistent")
    if not all(np.all(np.isfinite(x)) for x in (y, a, b, c)) or not np.allclose(
        c, c.T, atol=1e-14, rtol=0
    ):
        raise ValueError("finite symmetric covariance required")
    np.linalg.cholesky(c)
    ra, rb = y - a, y - b
    return float(
        0.5 * (np.sum(rb * np.linalg.solve(c, rb.T).T) - np.sum(ra * np.linalg.solve(c, ra.T).T))
    )


def monte_carlo(n_mc: int = 256, seed: int = 20261004) -> dict[str, Any]:
    if (
        isinstance(n_mc, bool)
        or not isinstance(n_mc, int)
        or n_mc < 2
        or isinstance(seed, bool)
        or not isinstance(seed, int)
    ):
        raise ValueError("n_mc must be an integer >=2 and seed an integer")
    rng = np.random.default_rng(seed)
    sigma, rho, n_time = 0.08, 0.65, 40
    covariance = sigma**2 * np.array([[1.0, rho], [rho, 1.0]])
    a = np.tile([0.6, 1.0], (n_time, 1))  # visibility change; unchanged source anchor
    b = np.tile([0.6, 0.6], (n_time, 1))  # source change; anchor also changes
    rows: list[MonteCarloReplicate] = []
    for i in range(n_mc):
        y = a + rng.multivariate_normal([0.0, 0.0], covariance, size=n_time)
        y_b = b + rng.multivariate_normal([0.0, 0.0], covariance, size=n_time)
        gap = joint_logscore_gap(y, a, b, covariance)
        rows.append(
            {
                "replicate": i,
                "joint_logscore_A_minus_B": gap,
                "joint_logscore_A_minus_B_when_B_true": joint_logscore_gap(y_b, a, b, covariance),
                "main_channel_gap": 0.0,
                "preferred": "A" if gap > 0 else "B" if gap < 0 else "equivalent",
            }
        )
    gaps = np.array([x["joint_logscore_A_minus_B"] for x in rows])
    return {
        "n_mc_requested": n_mc,
        "n_mc_executed": len(rows),
        "seed": seed,
        "covariance": covariance.tolist(),
        "rho": rho,
        "n_time": n_time,
        "mean_joint_logscore_gap": float(gaps.mean()),
        "sd_joint_logscore_gap": float(gaps.std(ddof=1)),
        "fraction_A_preferred": float(np.mean(gaps > 0)),
        "main_channel_exact_equivalence": True,
        "fraction_B_preferred_when_B_true": float(
            np.mean([x["joint_logscore_A_minus_B_when_B_true"] < 0 for x in rows])
        ),
        "miscalibrated_anchor_control_gap": joint_logscore_gap(
            a - np.array([0.0, 0.4]), a, b, covariance
        ),
        "known_generator_constants": True,
        "external_or_blinded_validation": False,
        "replicates": rows,
    }


def equivalence_decision(
    estimate: float, standard_error: float, tolerance: float, alpha: float = 0.05
) -> dict[str, Any]:
    if (
        not all(math.isfinite(x) for x in (estimate, standard_error, tolerance, alpha))
        or standard_error < 0
        or tolerance <= 0
        or not 0 < alpha < 0.5
    ):
        raise ValueError(
            "finite estimate, nonnegative SE, positive tolerance and valid alpha required"
        )
    z = float(norm.ppf(1 - alpha))
    lo, hi = estimate - z * standard_error, estimate + z * standard_error
    return {
        "interval_level": 1 - 2 * alpha,
        "interval": [lo, hi],
        "tolerance": tolerance,
        "equivalent": lo > -tolerance and hi < tolerance,
        "unit": "dimensionless fractional effect",
    }


def prospective_equivalence(n_mc: int, seed: int) -> dict[str, Any]:
    """Planning sensitivity only: independent session means, known SD.

    A five-percent margin and SD values are illustrative inputs. They are not
    the registered experimental tolerance or estimates from water experiments.
    The normal known-SD approximation omits pilot uncertainty and interlab effects.
    """
    rng = np.random.default_rng(seed)
    delta = 0.05
    out = []
    z_alpha, z_power = norm.ppf(0.95), norm.ppf(0.95)
    for sigma in (0.03, 0.06, 0.10):
        n = max(2, math.ceil(((z_alpha + z_power) * sigma / delta) ** 2))
        se = sigma / math.sqrt(n)
        for theta in (0.0, delta, 2 * delta):
            estimates = rng.normal(theta, se, n_mc)
            fraction = np.mean(
                [equivalence_decision(float(x), se, delta)["equivalent"] for x in estimates]
            )
            out.append(
                {
                    "session_sd": sigma,
                    "sessions": n,
                    "true_effect": theta,
                    "equivalence_fraction": float(fraction),
                }
            )
    return {
        "status": "illustrative prospective simulation; no experiment performed",
        "illustrative_margin": delta,
        "n_mc_per_scenario": n_mc,
        "scenarios": out,
        "systematic_floor_rule": "if defensible systematic uncertainty reaches the tolerance, redesign rather than add sessions",
    }


def run_all(n_mc: int = 256, seed: int = 20261004) -> dict[str, Any]:
    chain = forward_chain([0.70, 0.20, 0.10], synthetic_operators())
    archive = hybrid_archive(np.linspace(0, 6, 121))
    mc = monte_carlo(n_mc, seed)
    return {
        "version": VERSION,
        "release_status": "unpromoted-research-candidate",
        "empirical_framework_validation": False,
        "factorized_chain": chain,
        "hybrid_archive": archive,
        "scale_transfer": scale_transfer(seed + 1),
        "monte_carlo": mc,
        "evaporation_planning": prospective_equivalence(n_mc, seed + 2),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--n-mc", type=int, default=256)
    p.add_argument("--seed", type=int, default=20261004)
    args = p.parse_args()
    r = run_all(args.n_mc, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(r, indent=2, allow_nan=False) + "\n")
    print(
        json.dumps(
            {
                "output": str(args.out),
                "version": VERSION,
                "n_mc_executed": r["monte_carlo"]["n_mc_executed"],
            }
        )
    )


if __name__ == "__main__":
    main()
