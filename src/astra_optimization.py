"""Deterministic multistart helpers for the synthetic ASTRA benchmarks.

The helpers reject solver terminations that do not meet an explicit first-order
optimality threshold.  The start design is fixed independently of the hidden
generating parameters and spans the declared log-conductance box.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass

import numpy as np
from scipy.optimize import OptimizeResult, least_squares

LOG_LOWER = -8.0
LOG_UPPER = 5.0
N_STARTS = 12
FINITE_DIFFERENCE_STEP = 5.0e-3
SCALED_OPTIMALITY_LIMIT = 1.0e-4


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

    One conventional start at conductance 0.6 is followed by eleven Halton-like
    points over the interior log box ``[-7.5, 4.5]``.  The design is generic: it
    does not use the generating graph, generating conductances, noise, or data.
    """
    if n_parameters < 1 or n_parameters > 3:
        raise ValueError("n_parameters must lie in [1, 3].")
    primes = (2, 3, 5)
    starts = [np.full(n_parameters, np.log(0.6), dtype=float)]
    for index in range(1, N_STARTS):
        unit = np.array(
            [_radical_inverse(index, primes[column]) for column in range(n_parameters)],
            dtype=float,
        )
        starts.append(-7.5 + 12.0 * unit)
    return np.vstack(starts)


@dataclass(frozen=True)
class SolverDiagnostic:
    start_index: int
    accepted: bool
    status: int
    nfev: int
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
            accepted=is_accepted,
            status=int(result.status),
            nfev=int(result.nfev),
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
    _, best_start, best_result = min(accepted, key=lambda item: (item[0], item[1]))
    return best_result, best_start, tuple(diagnostics)
