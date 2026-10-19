"""Transparent reduced-order calculations for *The Coupling Is a State*.

The module implements only the analytic and synthetic examples used in the
preprint. It is not a universal simulator for sensing, catalysis, biology, or
astronomy. Numerical arrays are dimensionless unless a function documents
physical units explicitly.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.linalg import expm

FloatArray = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]


def _array(value: ArrayLike, *, ndim: int | None = None) -> FloatArray:
    arr = np.asarray(value, dtype=float)
    if ndim is not None and arr.ndim != ndim:
        raise ValueError(f"Expected ndim={ndim}, got shape {arr.shape}.")
    if not np.all(np.isfinite(arr)):
        raise ValueError("All numerical inputs must be finite.")
    return arr


def schur_effective_stiffness(
    focal_stiffness: ArrayLike,
    coupling: ArrayLike,
    context_stiffness: ArrayLike,
) -> FloatArray:
    """Return K_eff = K_xx - K_xq K_qq^{-1} K_qx.

    The context stiffness must be symmetric positive definite. The result is
    the quasistatic focal Hessian obtained by minimizing a quadratic free
    energy over the contextual coordinates.
    """

    kxx = _array(focal_stiffness, ndim=2)
    kxq = _array(coupling, ndim=2)
    kqq = _array(context_stiffness, ndim=2)
    if kxx.shape[0] != kxx.shape[1] or kqq.shape[0] != kqq.shape[1]:
        raise ValueError("Both stiffness matrices must be square.")
    if kxq.shape != (kxx.shape[0], kqq.shape[0]):
        raise ValueError("Coupling shape is inconsistent with the block sizes.")
    kxx = 0.5 * (kxx + kxx.T)
    kqq = 0.5 * (kqq + kqq.T)
    if np.min(np.linalg.eigvalsh(kqq)) <= 0.0:
        raise ValueError("Context stiffness must be positive definite.")
    return kxx - kxq @ np.linalg.solve(kqq, kxq.T)


def context_influence_number(
    focal_stiffness: ArrayLike,
    coupling: ArrayLike,
    context_stiffness: ArrayLike,
) -> float:
    """Return ||K_xq K_qq^{-1} K_qx||_2 / ||K_xx||_2."""

    kxx = _array(focal_stiffness, ndim=2)
    kxq = _array(coupling, ndim=2)
    kqq = _array(context_stiffness, ndim=2)
    reduction = kxq @ np.linalg.solve(kqq, kxq.T)
    denom = float(np.linalg.norm(kxx, 2))
    if denom <= 0.0:
        raise ValueError("Focal stiffness must have nonzero norm.")
    return float(np.linalg.norm(reduction, 2) / denom)


def similarity_transform(
    a: ArrayLike,
    b: ArrayLike,
    c: ArrayLike,
    transform: ArrayLike,
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Apply the state-coordinate transform z' = S z to an LTI realization."""

    A = _array(a, ndim=2)
    B = _array(b, ndim=2)
    C = _array(c, ndim=2)
    S = _array(transform, ndim=2)
    n = A.shape[0]
    if A.shape != (n, n) or S.shape != (n, n) or B.shape[0] != n or C.shape[1] != n:
        raise ValueError("State-space dimensions are inconsistent.")
    if abs(float(np.linalg.det(S))) < 1e-12:
        raise ValueError("Similarity transform must be invertible.")
    Sinv = np.linalg.inv(S)
    return S @ A @ Sinv, S @ B, C @ Sinv


def simulate_lti_piecewise_constant(
    a: ArrayLike,
    b: ArrayLike,
    c: ArrayLike,
    d: ArrayLike,
    inputs: ArrayLike,
    dt: float,
    initial: ArrayLike | None = None,
) -> tuple[FloatArray, FloatArray]:
    """Exact zero-order-hold simulation of a continuous-time LTI system.

    dx/dt = A x + B u, y = C x + D u.
    ``inputs`` has shape (n_steps, n_inputs). Returned states and outputs are
    sampled before each step update.
    """

    if dt <= 0.0:
        raise ValueError("dt must be positive.")
    A = _array(a, ndim=2)
    B = _array(b, ndim=2)
    C = _array(c, ndim=2)
    D = _array(d, ndim=2)
    U = _array(inputs, ndim=2)
    n = A.shape[0]
    m = B.shape[1]
    if A.shape != (n, n) or B.shape[0] != n or C.shape[1] != n or D.shape != (C.shape[0], m):
        raise ValueError("State-space dimensions are inconsistent.")
    if U.shape[1] != m:
        raise ValueError("Input width does not match B.")
    x = np.zeros(n, dtype=float) if initial is None else _array(initial, ndim=1).copy()
    if x.size != n:
        raise ValueError("Initial state has wrong dimension.")

    aug = np.zeros((n + m, n + m), dtype=float)
    aug[:n, :n] = A
    aug[:n, n:] = B
    transition = expm(aug * dt)
    Ad = transition[:n, :n]
    Bd = transition[:n, n:]

    states = np.zeros((U.shape[0], n), dtype=float)
    outputs = np.zeros((U.shape[0], C.shape[0]), dtype=float)
    for k, u in enumerate(U):
        states[k] = x
        outputs[k] = C @ x + D @ u
        x = Ad @ x + Bd @ u
    return states, outputs


@dataclass(frozen=True)
class StatefulChannelParameters:
    persistence: float
    drive: float
    direct_gain: float
    memory_gain: float
    interaction_gain: float
    offset: float = 0.0

    def validate(self) -> None:
        if not (0.0 <= self.persistence < 1.0):
            raise ValueError("persistence must lie in [0, 1).")


def simulate_stateful_channel(
    source: ArrayLike,
    parameters: StatefulChannelParameters,
    *,
    initial_memory: float = 0.0,
) -> tuple[FloatArray, FloatArray]:
    """Simulate a discrete-time source coupled to a memory-bearing channel.

    m[k+1] = a m[k] + b x[k]
    y[k]   = beta0 + beta1 x[k] + beta2 m[k] + beta3 x[k] m[k]
    """

    parameters.validate()
    x = _array(source, ndim=1)
    m = np.zeros_like(x)
    y = np.zeros_like(x)
    state = float(initial_memory)
    for k, value in enumerate(x):
        m[k] = state
        y[k] = (
            parameters.offset
            + parameters.direct_gain * value
            + parameters.memory_gain * state
            + parameters.interaction_gain * value * state
        )
        state = parameters.persistence * state + parameters.drive * value
    return m, y


def exponential_memory_kernel(lags: ArrayLike, persistence: float, drive: float) -> FloatArray:
    """Return the discrete impulse-response kernel b a^lag for lag >= 0."""

    if not (0.0 <= persistence < 1.0):
        raise ValueError("persistence must lie in [0, 1).")
    lag = _array(lags, ndim=1)
    if np.any(lag < 0) or np.any(np.floor(lag) != lag):
        raise ValueError("lags must be nonnegative integers.")
    return drive * persistence ** lag.astype(int)


def effective_sample_size_from_autocorrelation(
    autocorrelation: ArrayLike,
    sample_count: int,
) -> float:
    """Approximate effective sample size for a stationary scalar mean.

    Uses N_eff = N / (1 + 2 sum rho_k). The caller should truncate the
    autocorrelation sequence where estimation noise or sign oscillations make
    the asymptotic approximation unreliable.
    """

    if sample_count <= 0:
        raise ValueError("sample_count must be positive.")
    rho = _array(autocorrelation, ndim=1)
    denominator = 1.0 + 2.0 * float(np.sum(rho))
    if denominator <= 0.0:
        raise ValueError("Autocorrelation sum gives a nonpositive variance inflation factor.")
    return float(sample_count / denominator)


def ar1_effective_sample_size(sample_count: int, rho: float) -> float:
    """Large-N effective sample size for an AR(1) scalar mean."""

    if sample_count <= 0 or not (-1.0 < rho < 1.0):
        raise ValueError("Require positive sample count and |rho| < 1.")
    return float(sample_count * (1.0 - rho) / (1.0 + rho))


def precision_floor(
    single_event_sd: float,
    effective_sample_count: float,
    systematic_sd: float = 0.0,
) -> float:
    """Quadrature combination of repeat-limited precision and a systematic floor."""

    if single_event_sd < 0.0 or effective_sample_count <= 0.0 or systematic_sd < 0.0:
        raise ValueError("Standard deviations must be nonnegative and sample count positive.")
    return float(np.sqrt(single_event_sd**2 / effective_sample_count + systematic_sd**2))


def chiral_reference_completion_energy(
    handedness: float,
    axis_one: ArrayLike,
    axis_two: ArrayLike,
    reference: ArrayLike,
    coupling: float,
) -> float:
    r"""Return ``-lambda chi (n1 x n2) . r`` for unit vectors.

    The scalar triple product is a pseudoscalar. Multiplication by the
    handedness pseudoscalar gives a parity-even schematic energy. This is a
    reduced symmetry model for reference completion, not a detailed model of
    floral development.
    """

    n1 = _array(axis_one, ndim=1)
    n2 = _array(axis_two, ndim=1)
    r = _array(reference, ndim=1)
    if n1.size != 3 or n2.size != 3 or r.size != 3:
        raise ValueError("axis_one, axis_two, and reference must be three-dimensional.")
    norms = [np.linalg.norm(n1), np.linalg.norm(n2), np.linalg.norm(r)]
    if any(value == 0.0 for value in norms):
        raise ValueError("All vectors must be nonzero.")
    n1 = n1 / norms[0]
    n2 = n2 / norms[1]
    r = r / norms[2]
    return float(-coupling * handedness * np.dot(np.cross(n1, n2), r))


def two_element_diffusion_snapshot(
    parent_flux: ArrayLike,
    sinking_times: ArrayLike,
    duration: float,
    time_since_stop: float = 0.0,
) -> FloatArray:
    """Two-or-more element accretion/diffusion toy forward model.

    During constant accretion from an initially pristine convection zone,
    M_i(t) = F_i tau_i (1 - exp(-t/tau_i)). After accretion stops, each
    inventory decays as exp(-t_stop/tau_i).
    """

    flux = _array(parent_flux, ndim=1)
    tau = _array(sinking_times, ndim=1)
    if flux.size != tau.size or np.any(flux < 0.0) or np.any(tau <= 0.0):
        raise ValueError("Flux and sinking-time vectors must match and be physically valid.")
    if duration < 0.0 or time_since_stop < 0.0:
        raise ValueError("Times must be nonnegative.")
    inventory = flux * tau * (1.0 - np.exp(-duration / tau))
    if time_since_stop > 0.0:
        inventory = inventory * np.exp(-time_since_stop / tau)
    return inventory


def local_sensitivity_rank(jacobian_blocks: Sequence[ArrayLike], tolerance: float = 1e-10) -> int:
    """Return first-order numerical rank at the supplied point and tolerance.

    Rank deficiency is not a general certificate of nonlinear nonidentifiability
    (theta**3 at zero is injective despite zero derivative). This function does
    not establish global uniqueness, predictive sufficiency or Markov closure.
    """

    blocks = [_array(block, ndim=2) for block in jacobian_blocks]
    if not blocks:
        raise ValueError("At least one sensitivity block is required.")
    rows = {block.shape[0] for block in blocks}
    if len(rows) != 1:
        raise ValueError("All sensitivity blocks must have the same number of observations.")
    return int(np.linalg.matrix_rank(np.concatenate(blocks, axis=1), tol=tolerance))


def operational_edge_present(
    coupling_values: ArrayLike,
    *,
    tolerance: float = 1e-12,
) -> bool:
    """Whether an edge becomes non-negligibly active under the declared protocol set."""

    values = _array(coupling_values)
    return bool(np.any(np.abs(values) > tolerance))


def normalized_disclosure_severity(
    before: ArrayLike, after: ArrayLike, epsilon: float = 1e-12
) -> float:
    """Return ||after-before|| / (||before|| + epsilon)."""

    x0 = _array(before, ndim=1)
    x1 = _array(after, ndim=1)
    if x0.size != x1.size or epsilon <= 0.0:
        raise ValueError("States must match and epsilon must be positive.")
    return float(np.linalg.norm(x1 - x0) / (np.linalg.norm(x0) + epsilon))
