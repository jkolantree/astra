"""Deterministic multistart helpers for the synthetic ASTRA benchmarks.

The helpers reject solver terminations that do not meet an explicit first-order
optimality threshold. The release-frozen start coordinates are generic, do not
use hidden generating parameters, and span the declared log-conductance box;
the public documentation discloses that their coverage was strengthened during
release audit after an earlier design missed an endpoint on the same benchmark.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass

import numpy as np
from scipy.optimize import OptimizeResult, least_squares

LOG_LOWER = -8.0
LOG_UPPER = 5.0
N_STARTS = 20
FINITE_DIFFERENCE_STEP = 5.0e-3
SCALED_OPTIMALITY_LIMIT = 1.0e-4
MATERIAL_COST_GAP_LIMIT = 1.0e-4


def _radical_inverse(index: int, base: int) -> float:
    """Return a deterministic radical-inverse coordinate in ``[0, 1)``."""
    value = 0.0
    factor = 1.0 / base
    while index:
        index, digit = divmod(index, base)
        value += digit * factor
        factor /= base
    return value


def deterministic_log_starts(n_parameters: int) -> np.ndarray:
    """Construct a fixed low-discrepancy multistart design.

    The design combines a conventional start, the original eleven Halton-like
    points, a unit-conductance center, coordinate-wise decade anchors at 0.1
    and 10, and enough additional Halton-like points to reach ``N_STARTS``.
    It is generic: it does not use the generating graph, generating
    conductances, noise, or data.
    """
    if n_parameters < 1 or n_parameters > 3:
        raise ValueError("n_parameters must lie in [1, 3].")
    primes = (2, 3, 5)
    starts: list[np.ndarray] = []

    def append_unique(candidate: np.ndarray) -> None:
        if not any(np.array_equal(candidate, existing) for existing in starts):
            starts.append(candidate)

    append_unique(np.full(n_parameters, np.log(0.6), dtype=float))
    for index in range(1, 12):
        unit = np.array(
            [_radical_inverse(index, primes[column]) for column in range(n_parameters)],
            dtype=float,
        )
        append_unique(-7.5 + 12.0 * unit)
    append_unique(np.zeros(n_parameters, dtype=float))
    for column in range(n_parameters):
        low = np.zeros(n_parameters, dtype=float)
        high = np.zeros(n_parameters, dtype=float)
        low[column] = np.log(0.1)
        high[column] = np.log(10.0)
        append_unique(low)
        append_unique(high)
    index = 12
    while len(starts) < N_STARTS:
        unit = np.array(
            [_radical_inverse(index, primes[column]) for column in range(n_parameters)],
            dtype=float,
        )
        append_unique(-7.5 + 12.0 * unit)
        index += 1
    return np.vstack(starts)


@dataclass(frozen=True)
class SolverDiagnostic:
    start_index: int
    start_log_conductance: list[float]
    solver_success: bool
    accepted: bool
    status: int
    nfev: int
    endpoint_log_conductance: list[float]
    cost: float
    optimality: float
    scaled_optimality: float
    active_mask: list[int]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def solve_multistart(
    residual: Callable[[np.ndarray], np.ndarray],
    n_parameters: int,
    *,
    jacobian: Callable[[np.ndarray], np.ndarray] | None = None,
    xtol: float,
    ftol: float,
    gtol: float,
    max_nfev: int,
) -> tuple[OptimizeResult, int, tuple[SolverDiagnostic, ...]]:
    """Run and validate every fixed start, returning the best accepted fit.

    A successful solver flag alone is insufficient.  An accepted run must have
    finite parameters, cost, and optimality; positive termination status; and
    cost-scaled first-order optimality no larger than
    ``SCALED_OPTIMALITY_LIMIT``.
    """
    diagnostics: list[SolverDiagnostic] = []
    accepted: list[tuple[float, int, OptimizeResult]] = []
    for start_index, start in enumerate(deterministic_log_starts(n_parameters)):
        options: dict[str, object] = {}
        if jacobian is None:
            options["diff_step"] = FINITE_DIFFERENCE_STEP
        else:
            options["jac"] = jacobian
        result = least_squares(
            residual,
            start,
            bounds=(LOG_LOWER, LOG_UPPER),
            xtol=xtol,
            ftol=ftol,
            gtol=gtol,
            max_nfev=max_nfev,
            **options,
        )
        scaled_optimality = float(result.optimality) / max(1.0, float(result.cost))
        is_accepted = bool(
            result.success
            and int(result.status) > 0
            and np.all(np.isfinite(result.x))
            and np.isfinite(result.cost)
            and np.isfinite(result.optimality)
            and np.isfinite(scaled_optimality)
            and scaled_optimality <= SCALED_OPTIMALITY_LIMIT
        )
        diagnostic = SolverDiagnostic(
            start_index=start_index,
            start_log_conductance=[float(value) for value in start],
            solver_success=bool(result.success),
            accepted=is_accepted,
            status=int(result.status),
            nfev=int(result.nfev),
            endpoint_log_conductance=[float(value) for value in np.asarray(result.x, dtype=float)],
            cost=float(result.cost),
            optimality=float(result.optimality),
            scaled_optimality=scaled_optimality,
            active_mask=[int(value) for value in np.asarray(result.active_mask, dtype=int)],
        )
        diagnostics.append(diagnostic)
        if is_accepted:
            accepted.append((float(result.cost), start_index, result))

    if not accepted:
        finite_optimality = [
            item.scaled_optimality for item in diagnostics if np.isfinite(item.scaled_optimality)
        ]
        best_observed = min(finite_optimality, default=float("inf"))
        positive_status = sum(item.status > 0 for item in diagnostics)
        raise RuntimeError(
            "No multistart fit satisfied the declared convergence criterion "
            f"(optimality/max(1,cost) <= {SCALED_OPTIMALITY_LIMIT:g}); "
            "best observed scaled optimality="
            f"{best_observed:.6g}, positive-status runs={positive_status}/{len(diagnostics)}."
        )
    best_cost, best_start, best_result = min(accepted, key=lambda item: (item[0], item[1]))
    finite_diagnostics = [item for item in diagnostics if np.isfinite(item.cost)]
    lowest_observed = min(finite_diagnostics, key=lambda item: (item.cost, item.start_index))
    material_gap = (best_cost - lowest_observed.cost) / max(1.0, abs(best_cost))
    if not lowest_observed.accepted and material_gap > MATERIAL_COST_GAP_LIMIT:
        raise RuntimeError(
            "A non-admitted multistart endpoint has a materially lower cost than "
            "the best accepted fit; optimizer coverage is insufficient "
            f"(accepted cost={best_cost:.9g}, observed cost={lowest_observed.cost:.9g}, "
            f"relative gap={material_gap:.6g}, limit={MATERIAL_COST_GAP_LIMIT:g})."
        )
    return best_result, best_start, tuple(diagnostics)
