"""Reduced-order phase-reservoir network tools for SPPT-ASTRA.

The linear thermal core is

    C dT/dt = P(t) - (L_K + Lambda) T,

where C is a positive diagonal capacity matrix, L_K is a weighted graph
Laplacian, and Lambda is a non-negative local-loss matrix.

The module intentionally implements only the small, auditable model used in
the accompanying theory paper. It is not a general planetary simulator.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.linalg import expm

FloatArray = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]


@dataclass(frozen=True, slots=True)
class Edge:
    """Undirected linear transport edge between two reservoirs."""

    i: int
    j: int
    conductance: float

    def __post_init__(self) -> None:
        if self.i == self.j:
            raise ValueError("An edge must connect distinct nodes.")
        if self.conductance < 0:
            raise ValueError("Conductance must be non-negative.")


def weighted_laplacian(n_nodes: int, edges: Iterable[Edge]) -> FloatArray:
    """Return a symmetric weighted graph Laplacian."""
    if n_nodes < 1:
        raise ValueError("n_nodes must be positive.")
    lap = np.zeros((n_nodes, n_nodes), dtype=float)
    for edge in edges:
        if not (0 <= edge.i < n_nodes and 0 <= edge.j < n_nodes):
            raise IndexError("Edge index lies outside the network.")
        k = float(edge.conductance)
        lap[edge.i, edge.i] += k
        lap[edge.j, edge.j] += k
        lap[edge.i, edge.j] -= k
        lap[edge.j, edge.i] -= k
    return lap


def system_matrices(
    capacities: ArrayLike,
    edges: Sequence[Edge],
    loss: ArrayLike,
) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray]:
    """Build C, L_K, Lambda, and A for dT/dt = A T + C^{-1} P."""
    c = np.asarray(capacities, dtype=float)
    if c.ndim != 1 or c.size == 0 or np.any(c <= 0):
        raise ValueError("capacities must be a non-empty positive vector.")
    n = c.size

    loss_arr = np.asarray(loss, dtype=float)
    if loss_arr.ndim == 1:
        if loss_arr.shape != (n,) or np.any(loss_arr < 0):
            raise ValueError("loss vector must be non-negative and match capacities.")
        lam = np.diag(loss_arr)
    elif loss_arr.shape == (n, n):
        if not np.allclose(loss_arr, loss_arr.T, atol=1e-12):
            raise ValueError("loss matrix must be symmetric in this model.")
        if np.min(np.linalg.eigvalsh(loss_arr)) < -1e-12:
            raise ValueError("loss matrix must be positive semidefinite.")
        lam = loss_arr.copy()
    else:
        raise ValueError("loss must be an n-vector or n-by-n matrix.")

    cap = np.diag(c)
    lap = weighted_laplacian(n, edges)
    a = -np.diag(1.0 / c) @ (lap + lam)
    return cap, lap, lam, a


def steady_state(
    capacities: ArrayLike,
    edges: Sequence[Edge],
    loss: ArrayLike,
    power: ArrayLike,
) -> FloatArray:
    """Solve the unique linear steady state when every component has a sink."""
    _, lap, lam, _ = system_matrices(capacities, edges, loss)
    p = np.asarray(power, dtype=float)
    if p.shape != (lap.shape[0],):
        raise ValueError("power must match the number of reservoirs.")
    operator = lap + lam
    try:
        return np.linalg.solve(operator, p)
    except np.linalg.LinAlgError as exc:
        raise ValueError(
            "Steady-state operator is singular; each connected component needs an effective sink."
        ) from exc


def step_response(
    capacities: ArrayLike,
    edges: Sequence[Edge],
    loss: ArrayLike,
    power: ArrayLike,
    times: ArrayLike,
    initial: ArrayLike | None = None,
) -> FloatArray:
    """Exact response to a constant forcing vector using matrix exponentials."""
    cap, _, _, a = system_matrices(capacities, edges, loss)
    p = np.asarray(power, dtype=float)
    t = np.asarray(times, dtype=float)
    n = cap.shape[0]
    if p.shape != (n,):
        raise ValueError("power must match the number of reservoirs.")
    if t.ndim != 1 or np.any(np.diff(t) < 0):
        raise ValueError("times must be a non-decreasing vector.")
    x0 = np.zeros(n, dtype=float) if initial is None else np.asarray(initial, dtype=float)
    if x0.shape != (n,):
        raise ValueError("initial must match the number of reservoirs.")

    forcing = np.diag(1.0 / np.diag(cap)) @ p
    try:
        equilibrium = -np.linalg.solve(a, forcing)
    except np.linalg.LinAlgError as exc:
        raise ValueError("The system has an unclosed zero mode.") from exc

    out = np.empty((t.size, n), dtype=float)
    for idx, time in enumerate(t):
        out[idx] = equilibrium + expm(a * float(time)) @ (x0 - equilibrium)
    return out


def frequency_response(
    capacities: ArrayLike,
    edges: Sequence[Edge],
    loss: ArrayLike,
    input_vector: ArrayLike,
    output_vector: ArrayLike,
    angular_frequencies: ArrayLike,
) -> ComplexArray:
    """Return scalar harmonic transfer response y/u at each angular frequency."""
    cap, lap, lam, _ = system_matrices(capacities, edges, loss)
    b = np.asarray(input_vector, dtype=float)
    c_out = np.asarray(output_vector, dtype=float)
    omega = np.asarray(angular_frequencies, dtype=float)
    n = cap.shape[0]
    if b.shape != (n,) or c_out.shape != (n,):
        raise ValueError("input/output vectors must match the network size.")
    if omega.ndim != 1 or np.any(omega < 0):
        raise ValueError("angular_frequencies must be non-negative.")

    m = lap + lam
    response = np.empty(omega.size, dtype=np.complex128)
    for idx, w in enumerate(omega):
        state = np.linalg.solve(1j * float(w) * cap + m, b)
        response[idx] = c_out @ state
    return response


def relaxation_spectrum(
    capacities: ArrayLike,
    edges: Sequence[Edge],
    loss: ArrayLike,
) -> tuple[FloatArray, FloatArray]:
    """Return positive decay rates and their reciprocal relaxation times."""
    cap, lap, lam, _ = system_matrices(capacities, edges, loss)
    inv_sqrt_c = np.diag(1.0 / np.sqrt(np.diag(cap)))
    q = inv_sqrt_c @ (lap + lam) @ inv_sqrt_c
    rates = np.asarray(np.linalg.eigvalsh(q), dtype=np.float64)
    if np.min(rates) <= 0:
        raise ValueError("Network has an unclosed zero mode.")
    return rates, np.asarray(1.0 / rates, dtype=np.float64)


def two_reservoir_poles(
    c_surface: float,
    c_deep: float,
    coupling: float,
    loss: float,
) -> FloatArray:
    """Analytic poles of the two-reservoir model."""
    vals = (c_surface, c_deep, coupling, loss)
    if any(v <= 0 for v in vals):
        raise ValueError("All two-reservoir parameters must be positive.")
    b = c_surface * coupling + c_deep * (loss + coupling)
    discr = b * b - 4.0 * c_surface * c_deep * loss * coupling
    discr = max(discr, 0.0)
    denom = 2.0 * c_surface * c_deep
    return np.array(
        [(-b + np.sqrt(discr)) / denom, (-b - np.sqrt(discr)) / denom],
        dtype=float,
    )


def fisher_information(
    jacobians: ArrayLike,
    covariance: ArrayLike,
) -> FloatArray:
    """Compute summed Fisher information J^T Sigma^{-1} J.

    Parameters
    ----------
    jacobians:
        Array shaped (n_measurements, n_parameters).
    covariance:
        Positive-definite measurement covariance matrix.
    """
    j = np.asarray(jacobians, dtype=float)
    sigma = np.asarray(covariance, dtype=float)
    if j.ndim != 2:
        raise ValueError("jacobians must be two-dimensional.")
    if sigma.shape != (j.shape[0], j.shape[0]):
        raise ValueError("covariance shape must match measurement count.")
    if not np.all(np.isfinite(j)) or not np.all(np.isfinite(sigma)):
        raise ValueError("jacobians and covariance must be finite.")
    if not np.allclose(sigma, sigma.T, rtol=0.0, atol=1e-12):
        raise ValueError("covariance must be symmetric.")
    try:
        np.linalg.cholesky(sigma)
    except np.linalg.LinAlgError as exc:
        raise ValueError("covariance must be positive definite.") from exc
    return j.T @ np.linalg.solve(sigma, j)
