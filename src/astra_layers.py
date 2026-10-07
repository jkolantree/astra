"""Reference calculations for ASTRA-Layers hidden-state tasks.

Transparent reduced-order calculations used in the foundational preprint.
This is not a domain-general inference engine.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum, StrEnum

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.stats import norm


class EdgeType(StrEnum):
    # Preserve the earlier public str/format behavior while using the modern base.
    __str__ = Enum.__str__
    __format__ = Enum.__format__

    PHYSICAL = "physical"
    CONTROL = "control"
    OBSERVATION = "observation"
    ARCHIVE = "archive"
    CERTIFICATE = "certificate"


@dataclass(frozen=True)
class TypedEdge:
    tail: str
    head: str
    edge_type: EdgeType
    mechanism: str
    units: str | None = None
    failure_scope: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        # Normalize the JSON string representation before Enum identity checks.
        object.__setattr__(self, "edge_type", EdgeType(self.edge_type))
        if not isinstance(self.failure_scope, (tuple, list)) or any(
            not isinstance(x, str) or not x.strip() for x in self.failure_scope
        ):
            raise ValueError("failure_scope must contain nonempty strings")
        object.__setattr__(self, "failure_scope", tuple(self.failure_scope))


@dataclass
class LayeredGraph:
    nodes: set[str] = field(default_factory=set)
    edges: list[TypedEdge] = field(default_factory=list)

    def validate(self) -> None:
        for edge in self.edges:
            if edge.tail not in self.nodes or edge.head not in self.nodes:
                raise ValueError(f"Unknown endpoint in edge {edge}")
            if not edge.mechanism.strip():
                raise ValueError("Every edge needs a declared mechanism.")
            if edge.edge_type is EdgeType.PHYSICAL and (
                not isinstance(edge.units, str) or not edge.units.strip()
            ):
                raise ValueError("Physical edges require declared transported units.")
            if edge.edge_type is EdgeType.CERTIFICATE and not edge.failure_scope:
                raise ValueError("Certificate edges require a nonempty failure scope.")

    def by_type(self, edge_type: EdgeType) -> list[TypedEdge]:
        normalized = EdgeType(edge_type)
        return [edge for edge in self.edges if edge.edge_type is normalized]


def _array(value: ArrayLike) -> NDArray[np.float64]:
    arr = np.asarray(value, dtype=float)
    if not np.all(np.isfinite(arr)):
        raise ValueError("All numerical inputs must be finite.")
    return arr


def incidence_matrix(nodes: int, edges: Sequence[tuple[int, int]]) -> NDArray[np.float64]:
    if nodes < 1:
        raise ValueError("nodes must be positive")
    B = np.zeros((nodes, len(edges)), dtype=float)
    for j, (tail, head) in enumerate(edges):
        if tail == head:
            raise ValueError("self loops are excluded")
        if tail < 0 or tail >= nodes or head < 0 or head >= nodes:
            raise IndexError("edge endpoint outside node range")
        B[tail, j] = -1.0
        B[head, j] = 1.0
    return B


def physical_inventory_tendency(
    B: ArrayLike, flux: ArrayLike, source: ArrayLike, sink: ArrayLike
) -> NDArray[np.float64]:
    Bm, J, S, E = _array(B), _array(flux), _array(source), _array(sink)
    if Bm.ndim != 2 or J.ndim != 1 or S.ndim != 1 or E.ndim != 1:
        raise ValueError("unexpected dimensions")
    if Bm.shape[1] != J.size or Bm.shape[0] != S.size or S.shape != E.shape:
        raise ValueError("shape mismatch")
    return Bm @ J + S - E


def gaussian_kl_same_variance(mu_p: ArrayLike, mu_q: ArrayLike, sigma: float) -> float:
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    p, q = _array(mu_p), _array(mu_q)
    if p.shape != q.shape:
        raise ValueError("means must have equal shape")
    return float(np.sum((p - q) ** 2) / (2.0 * sigma**2))


def posterior_odds(prior_odds: float, likelihood_ratio: float) -> float:
    if prior_odds < 0 or likelihood_ratio < 0:
        raise ValueError("odds and likelihood ratio must be nonnegative")
    return float(prior_odds * likelihood_ratio)


def closed_loop_coefficient(a: float, b: float, k: float) -> float:
    return float(a - b * k)


def simulate_closed_loop(
    a: float, b: float, k: float, probe: ArrayLike, *, x0: float = 1.0
) -> NDArray[np.float64]:
    r = _array(probe)
    if r.ndim != 1:
        raise ValueError("probe must be one-dimensional")
    x = np.empty(r.size + 1, dtype=float)
    x[0] = x0
    for t, value in enumerate(r):
        u = -k * x[t] + value
        x[t + 1] = a * x[t] + b * u
    return x


def archive_state(
    time: ArrayLike, source: ArrayLike, leak: ArrayLike, *, initial: float = 0.0
) -> NDArray[np.float64]:
    t, s, ell = _array(time), _array(source), _array(leak)
    if t.ndim != 1 or s.shape != t.shape or ell.shape != t.shape:
        raise ValueError("time, source, and leak must be one-dimensional and equal length")
    if t.size == 0 or not np.isfinite(initial) or np.any(np.diff(t) <= 0) or np.any(ell < 0):
        raise ValueError("invalid time or leak")
    h = np.empty_like(t)
    h[0] = initial
    for j in range(t.size - 1):
        dt = t[j + 1] - t[j]
        decay = np.exp(-ell[j] * dt)
        local = dt if ell[j] == 0 or ell[j] * dt == 0 else -np.expm1(-ell[j] * dt) / ell[j]
        h[j + 1] = h[j] * decay + s[j] * local
    return h


def archive_kernel_weights(time: ArrayLike, leak: ArrayLike) -> NDArray[np.float64]:
    t, ell = _array(time), _array(leak)
    if t.ndim != 1 or ell.shape != t.shape:
        raise ValueError("time and leak shape mismatch")
    if t.size == 0 or np.any(np.diff(t) <= 0) or np.any(ell < 0):
        raise ValueError("nonempty increasing time and nonnegative leak required")
    n = t.size
    weights = np.zeros(n, dtype=float)
    cumulative_after = 0.0
    for j in range(n - 2, -1, -1):
        dt = t[j + 1] - t[j]
        local = dt if ell[j] == 0 or ell[j] * dt == 0 else -np.expm1(-ell[j] * dt) / ell[j]
        weights[j] = local * np.exp(-cumulative_after)
        cumulative_after += ell[j] * dt
    return weights


def certificate_posterior_failure(
    prior_failure: float, p_z_given_failure: float, p_z_given_ok: float
) -> float:
    for value in (prior_failure, p_z_given_failure, p_z_given_ok):
        if not 0 <= value <= 1:
            raise ValueError("probabilities must lie in [0,1]")
    num = prior_failure * p_z_given_failure
    den = num + (1.0 - prior_failure) * p_z_given_ok
    if den == 0:
        raise ValueError("certificate event has zero probability")
    return float(num / den)


def selectivity_curve(
    thresholds: ArrayLike, *, good_prior: float, good_mean: float, bad_mean: float, sigma: float
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    tau = _array(thresholds)
    if not 0 < good_prior < 1 or sigma <= 0:
        raise ValueError("invalid prior or sigma")
    good_tail = norm.sf((tau - good_mean) / sigma)
    bad_tail = norm.sf((tau - bad_mean) / sigma)
    yield_rate = good_prior * good_tail + (1.0 - good_prior) * bad_tail
    precision = np.divide(
        good_prior * good_tail, yield_rate, out=np.ones_like(yield_rate), where=yield_rate > 0
    )
    return yield_rate, precision


def best_intervention_by_kl(
    predictions_a: Mapping[str, ArrayLike], predictions_b: Mapping[str, ArrayLike], sigma: float
) -> tuple[str, dict[str, float]]:
    if predictions_a.keys() != predictions_b.keys():
        raise ValueError("candidate keys must match")
    scores = {
        key: gaussian_kl_same_variance(predictions_a[key], predictions_b[key], sigma)
        for key in predictions_a
    }
    return max(scores, key=scores.__getitem__), scores
