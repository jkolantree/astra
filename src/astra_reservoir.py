"""Reduced-order phase-reservoir network tools for SPPT-ASTRA.

The linear thermal core is

    C dT/dt = P(t) - (L_K + Lambda) T,

where C is a positive diagonal capacity matrix, L_K is a weighted graph
Laplacian, and Lambda is a non-negative local-loss matrix.

The module intentionally implements only the small, auditable model used in
the accompanying theory paper. It is not a general planetary simulator.
"""
from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.linalg import expm, solve_triangular

FloatArray = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]


def _as_finite_array(value: ArrayLike, *, name: str) -> FloatArray:
    array = np.asarray(value, dtype=float)
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values.")
    return array


def _scaled_product(*values: float) -> float:
    if any(value == 0.0 for value in values):
        return 0.0
    sign = -1.0 if sum(value < 0.0 for value in values) % 2 else 1.0
    mantissa = 1.0
    exponent = 0
    for value in values:
        value_mantissa, value_exponent = math.frexp(abs(value))
        mantissa *= value_mantissa
        mantissa, normalization_exponent = math.frexp(mantissa)
        exponent += value_exponent + normalization_exponent
    try:
        result = math.ldexp(mantissa, exponent)
    except OverflowError as exc:
        raise ValueError("Numerical result exceeds the finite range.") from exc
    if result == 0.0 or not math.isfinite(result):
        raise ValueError("Numerical result exceeds the finite range.")
    return sign * result


def _scaled_product_over(numerator: float, multiplier: float, denominator: float) -> float:
    if numerator == 0.0 or multiplier == 0.0:
        return 0.0
    numerator_mantissa, numerator_exponent = math.frexp(abs(numerator))
    multiplier_mantissa, multiplier_exponent = math.frexp(abs(multiplier))
    denominator_mantissa, denominator_exponent = math.frexp(denominator)
    mantissa, normalization_exponent = math.frexp(
        numerator_mantissa * multiplier_mantissa / denominator_mantissa
    )
    try:
        result = math.ldexp(
            mantissa,
            numerator_exponent
            + multiplier_exponent
            - denominator_exponent
            + normalization_exponent,
        )
    except OverflowError as exc:
        raise ValueError("Numerical result exceeds the finite range.") from exc
    if result == 0.0 or not math.isfinite(result):
        raise ValueError("Numerical result exceeds the finite range.")
    sign = -1.0 if (numerator < 0.0) != (multiplier < 0.0) else 1.0
    return sign * result


def _symmetrized(array: FloatArray, *, name: str) -> FloatArray:
    transpose = array.T
    pair_scale = np.maximum(np.abs(array), np.abs(transpose))
    normalized = np.divide(
        array,
        pair_scale,
        out=np.zeros_like(array),
        where=pair_scale != 0.0,
    )
    normalized_transpose = np.divide(
        transpose,
        pair_scale,
        out=np.zeros_like(array),
        where=pair_scale != 0.0,
    )
    if float(np.max(np.abs(normalized - normalized_transpose))) > 8.0 * np.finfo(
        float
    ).eps:
        raise ValueError(f"{name} must be symmetric.")
    # The accepted pairwise differences are small relative to their own
    # entries, so this midpoint correction cannot incur the opposite-sign
    # overflow hidden by a matrix-global scale.
    result = array + 0.5 * (transpose - array)
    if not np.all(np.isfinite(result)):
        raise ValueError(f"{name} exceeds the finite numerical range.")
    return np.asarray(result, dtype=np.float64)


def _positive_semidefinite(array: FloatArray, *, name: str) -> FloatArray:
    """Validate PSD after diagonal congruence scaling and clip only roundoff."""
    diagonal = np.diag(array)
    if np.any(diagonal < 0.0):
        raise ValueError(f"{name} must be positive semidefinite.")
    positive = diagonal > 0.0
    zero = ~positive
    if np.any(array[zero, :] != 0.0) or np.any(array[:, zero] != 0.0):
        raise ValueError(f"{name} must be positive semidefinite.")
    if not np.any(positive):
        return array.copy()

    submatrix = array[np.ix_(positive, positive)]
    root_diagonal = np.sqrt(diagonal[positive])
    scale = root_diagonal[:, None] * root_diagonal[None, :]
    correlation = submatrix / scale
    if not np.all(np.isfinite(correlation)):
        raise ValueError(f"{name} must be positive semidefinite.")
    eigenvalues, eigenvectors = np.linalg.eigh(correlation)
    tolerance = 8.0 * np.finfo(float).eps * max(1, correlation.shape[0])
    if float(np.min(eigenvalues)) < -tolerance:
        raise ValueError(f"{name} must be positive semidefinite.")
    if np.min(eigenvalues) < 0.0:
        correlation = (
            eigenvectors * np.maximum(eigenvalues, 0.0)
        ) @ eigenvectors.T
        result = array.copy()
        result[np.ix_(positive, positive)] = correlation * scale
        if not np.all(np.isfinite(result)):
            raise ValueError(f"{name} exceeds the finite numerical range.")
        return np.asarray(result, dtype=np.float64)
    return array.copy()


@dataclass(frozen=True, slots=True)
class Edge:
    """Undirected linear transport edge between two reservoirs."""

    i: int
    j: int
    conductance: float

    def __post_init__(self) -> None:
        if self.i == self.j:
            raise ValueError("An edge must connect distinct nodes.")
        if not np.isfinite(self.conductance) or self.conductance < 0:
            raise ValueError("Conductance must be finite and non-negative.")


def _validate_resolvable_positive_sum(values: Sequence[float]) -> None:
    positive = [float(value) for value in values if value > 0.0]
    if len(positive) < 2:
        return
    largest = max(positive)
    normalized = [value / largest for value in positive]
    if any(value == 0.0 for value in normalized):
        raise ValueError(
            "Incident conductance dynamic range exceeds reliable Laplacian assembly."
        )
    total = math.fsum(normalized)
    tolerance = math.sqrt(np.finfo(float).eps) * len(normalized)
    for index, contribution in enumerate(normalized):
        without = math.fsum(
            value for offset, value in enumerate(normalized) if offset != index
        )
        retained = total - without
        if retained <= 0.0 or abs(retained - contribution) > tolerance * contribution:
            raise ValueError(
                "Incident conductance dynamic range exceeds reliable Laplacian assembly."
            )


def _validate_pairwise_sum(
    left: FloatArray, right: FloatArray, combined: FloatArray, *, name: str
) -> None:
    tolerance = math.sqrt(np.finfo(float).eps)
    for original, other in ((left, right), (right, left)):
        nonzero = original != 0.0
        retained = combined[nonzero] - other[nonzero]
        relative_error = np.abs((retained - original[nonzero]) / original[nonzero])
        if np.any(~np.isfinite(relative_error)) or np.any(relative_error > tolerance):
            raise ValueError(f"{name} cannot retain its separated terms accurately.")


def weighted_laplacian(n_nodes: int, edges: Iterable[Edge]) -> FloatArray:
    """Return a symmetric weighted graph Laplacian."""
    if n_nodes < 1:
        raise ValueError("n_nodes must be positive.")
    edge_list = tuple(edges)
    incident: list[list[float]] = [[] for _ in range(n_nodes)]
    for edge in edge_list:
        if not (0 <= edge.i < n_nodes and 0 <= edge.j < n_nodes):
            raise IndexError("Edge index lies outside the network.")
        if edge.conductance > 0.0:
            incident[edge.i].append(float(edge.conductance))
            incident[edge.j].append(float(edge.conductance))
    for conductances in incident:
        _validate_resolvable_positive_sum(conductances)
    lap = np.zeros((n_nodes, n_nodes), dtype=float)
    grouped: dict[tuple[int, int], list[float]] = {}
    for edge in edge_list:
        pair = (min(edge.i, edge.j), max(edge.i, edge.j))
        grouped.setdefault(pair, []).append(float(edge.conductance))
    try:
        grouped_incident: list[list[float]] = [[] for _ in range(n_nodes)]
        for (left, right), conductances in grouped.items():
            _validate_resolvable_positive_sum(conductances)
            total = math.fsum(conductances)
            lap[left, right] = -total
            lap[right, left] = -total
            grouped_incident[left].append(total)
            grouped_incident[right].append(total)
        for node, conductances in enumerate(grouped_incident):
            _validate_resolvable_positive_sum(conductances)
            lap[node, node] = math.fsum(conductances)
    except OverflowError as exc:
        raise ValueError("Weighted Laplacian exceeds the finite numerical range.") from exc
    if not np.all(np.isfinite(lap)):
        raise ValueError("Weighted Laplacian exceeds the finite numerical range.")
    return lap


def system_matrices(
    capacities: ArrayLike,
    edges: Sequence[Edge],
    loss: ArrayLike,
) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray]:
    """Build C, L_K, Lambda, and A for dT/dt = A T + C^{-1} P."""
    c = _as_finite_array(capacities, name="capacities")
    if c.ndim != 1 or c.size == 0 or np.any(c <= 0):
        raise ValueError("capacities must be a non-empty positive vector.")
    n = c.size

    loss_arr = _as_finite_array(loss, name="loss")
    if loss_arr.ndim == 1:
        if loss_arr.shape != (n,) or np.any(loss_arr < 0):
            raise ValueError("loss vector must be non-negative and match capacities.")
        lam = np.diag(loss_arr)
    elif loss_arr.shape == (n, n):
        lam = _symmetrized(loss_arr, name="loss matrix")
        lam = _positive_semidefinite(lam, name="loss matrix")
    else:
        raise ValueError("loss must be an n-vector or n-by-n matrix.")

    cap = np.diag(c)
    lap = weighted_laplacian(n, edges)
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        a = -(lap / c[:, None] + lam / c[:, None])
    if not np.all(np.isfinite(a)):
        raise ValueError("System operator exceeds the finite numerical range.")
    return cap, lap, lam, a


def _solve_steady_operator(lap: FloatArray, lam: FloatArray, power: FloatArray) -> FloatArray:
    row_scale = np.maximum(np.max(np.abs(lap), axis=1), np.max(np.abs(lam), axis=1))
    if not np.all(np.isfinite(row_scale)) or np.any(row_scale == 0.0):
        raise ValueError(
            "Steady-state operator is singular; each connected component needs an effective sink."
        )
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        scaled_lap = lap / row_scale[:, None]
        scaled_lam = lam / row_scale[:, None]
        operator = scaled_lap + scaled_lam
        scaled_power = power / row_scale
    if not np.all(np.isfinite(operator)) or not np.all(np.isfinite(scaled_power)):
        raise ValueError("Steady-state solve exceeded the finite numerical range.")
    if np.any((power != 0.0) & (scaled_power == 0.0)):
        raise ValueError("Steady-state scaling erased a nonzero power component.")
    if np.any((lap != 0.0) & (scaled_lap == 0.0)) or np.any(
        (lam != 0.0) & (scaled_lam == 0.0)
    ):
        raise ValueError("Steady-state scaling erased a nonzero operator component.")
    scaling_tolerance = 64.0 * np.finfo(float).eps
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        reconstructed_lap = scaled_lap * row_scale[:, None]
        reconstructed_lam = scaled_lam * row_scale[:, None]
        reconstructed_power = scaled_power * row_scale
    for original, reconstructed, name in (
        (lap, reconstructed_lap, "transport operator"),
        (lam, reconstructed_lam, "loss operator"),
        (power, reconstructed_power, "power"),
    ):
        nonzero = original != 0.0
        if np.any(~np.isfinite(reconstructed[nonzero])) or np.any(
            np.abs((reconstructed[nonzero] - original[nonzero]) / original[nonzero])
            > scaling_tolerance
        ):
            raise ValueError(f"Steady-state scaling cannot retain {name} accurately.")
    try:
        result = np.linalg.solve(operator, scaled_power)
    except np.linalg.LinAlgError as exc:
        raise ValueError(
            "Steady-state operator is singular; each connected component needs an effective sink."
        ) from exc
    if not np.all(np.isfinite(result)):
        raise ValueError("Steady-state solve exceeded the finite numerical range.")
    # Check backward error with L and Lambda kept separate. Forming their sum
    # can round away a physically decisive sink while still yielding a finite
    # answer from the linear solver. A few refinement steps repair ordinary
    # rounding error; failure to satisfy the separated balance is fail-closed.
    tolerance = 64.0 * np.finfo(float).eps * max(1, result.size)
    for attempt in range(4):
        residual = np.empty(result.size, dtype=float)
        maximum_error = 0.0
        for row in range(result.size):
            try:
                lap_terms = [
                    float(scaled_lap[row, column]) * float(result[column])
                    for column in range(result.size)
                ]
                loss_terms = [
                    float(scaled_lam[row, column]) * float(result[column])
                    for column in range(result.size)
                ]
                lap_action = math.fsum(lap_terms)
                loss_action = math.fsum(loss_terms)
                residual[row] = math.fsum(
                    [float(scaled_power[row]), -lap_action, -loss_action]
                )
            except OverflowError as exc:
                raise ValueError(
                    "Steady-state residual exceeded the finite numerical range."
                ) from exc
            if scaled_power[row] == 0.0 and loss_action == 0.0:
                row_magnitude = math.fsum(
                    abs(value) for value in [*lap_terms, *loss_terms]
                )
            else:
                row_magnitude = max(
                    abs(float(scaled_power[row])), abs(lap_action), abs(loss_action)
                )
            if row_magnitude == 0.0:
                row_error = 0.0 if residual[row] == 0.0 else math.inf
            else:
                row_error = abs(float(residual[row])) / row_magnitude
            maximum_error = max(maximum_error, row_error)
        if maximum_error <= tolerance:
            return np.asarray(result, dtype=np.float64)
        if attempt == 3:
            break
        try:
            correction = np.linalg.solve(operator, residual)
        except np.linalg.LinAlgError:
            break
        candidate = result + correction
        if not np.all(np.isfinite(candidate)) or np.array_equal(candidate, result):
            break
        result = candidate
    raise ValueError("Steady-state balance is numerically unresolved.")


def steady_state(
    capacities: ArrayLike,
    edges: Sequence[Edge],
    loss: ArrayLike,
    power: ArrayLike,
) -> FloatArray:
    """Solve the unique linear steady state when every component has a sink."""
    _, lap, lam, _ = system_matrices(capacities, edges, loss)
    p = _as_finite_array(power, name="power")
    if p.shape != (lap.shape[0],):
        raise ValueError("power must match the number of reservoirs.")
    return _solve_steady_operator(lap, lam, p)


def step_response(
    capacities: ArrayLike,
    edges: Sequence[Edge],
    loss: ArrayLike,
    power: ArrayLike,
    times: ArrayLike,
    initial: ArrayLike | None = None,
) -> FloatArray:
    """Exact response to a constant forcing vector using matrix exponentials."""
    cap, lap, lam, a = system_matrices(capacities, edges, loss)
    p = _as_finite_array(power, name="power")
    t = _as_finite_array(times, name="times")
    n = cap.shape[0]
    if p.shape != (n,):
        raise ValueError("power must match the number of reservoirs.")
    if t.ndim != 1 or np.any(t < 0.0) or np.any(np.diff(t) < 0):
        raise ValueError("times must be a non-negative, non-decreasing vector.")
    x0 = (
        np.zeros(n, dtype=float)
        if initial is None
        else _as_finite_array(initial, name="initial")
    )
    if x0.shape != (n,):
        raise ValueError("initial must match the number of reservoirs.")

    _solve_steady_operator(lap, lam, p)
    capacities_diagonal = np.diag(cap)

    out = np.empty((t.size, n), dtype=float)
    for idx, time in enumerate(t):
        elapsed = float(time)
        with np.errstate(over="ignore", under="ignore", invalid="ignore"):
            exponent = np.zeros((n + 1, n + 1), dtype=float)
            exponent[:n, :n] = a * elapsed
        if not np.all(np.isfinite(exponent)):
            raise ValueError("Step-response propagation exceeds the finite numerical range.")
        try:
            exponent[:n, n] = [
                _scaled_product_over(float(p[node]), elapsed, float(capacities_diagonal[node]))
                for node in range(n)
            ]
        except ValueError as exc:
            raise ValueError("Step-response forcing exceeds the finite numerical range.") from exc
        propagator = expm(exponent)
        if not np.all(np.isfinite(propagator)):
            raise ValueError("Step-response propagation exceeds the finite numerical range.")
        out[idx] = propagator[:n, :n] @ x0 + propagator[:n, n]
        if not np.all(np.isfinite(out[idx])):
            raise ValueError("Step-response propagation exceeds the finite numerical range.")
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
    cap, lap, lam, a = system_matrices(capacities, edges, loss)
    b = _as_finite_array(input_vector, name="input_vector")
    c_out = _as_finite_array(output_vector, name="output_vector")
    omega = _as_finite_array(angular_frequencies, name="angular_frequencies")
    n = cap.shape[0]
    if b.shape != (n,) or c_out.shape != (n,):
        raise ValueError("input/output vectors must match the network size.")
    if omega.ndim != 1 or np.any(omega < 0):
        raise ValueError("angular_frequencies must be non-negative.")

    capacities_diagonal = np.diag(cap)
    with np.errstate(over="ignore", invalid="ignore"):
        m = lap + lam
    if np.all(np.isfinite(m)):
        _validate_pairwise_sum(lap, lam, m, name="Frequency-response operator")
    response = np.empty(omega.size, dtype=np.complex128)
    for idx, w in enumerate(omega):
        frequency = float(w)
        if frequency == 0.0:
            static_state = _solve_steady_operator(lap, lam, b)
            response[idx] = c_out @ static_state
            continue
        with np.errstate(over="ignore", under="ignore", invalid="ignore"):
            dynamic_diagonal = frequency * capacities_diagonal
            direct_matrix = 1j * frequency * cap + m
        direct_safe = np.all(np.isfinite(m)) and np.all(np.isfinite(direct_matrix)) and not (
            frequency > 0.0 and np.any(dynamic_diagonal == 0.0)
        )
        state: ComplexArray | None = None
        if direct_safe:
            try:
                direct_state = np.linalg.solve(direct_matrix, b)
            except np.linalg.LinAlgError:
                direct_state = None
            if direct_state is not None and np.all(np.isfinite(direct_state)):
                state = np.asarray(direct_state, dtype=np.complex128)
        if state is None:
            with np.errstate(over="ignore", under="ignore", invalid="ignore"):
                normalized_matrix = 1j * frequency * np.eye(n) - a
                normalized_input = b / capacities_diagonal
            if not (
                np.all(np.isfinite(normalized_matrix))
                and np.all(np.isfinite(normalized_input))
            ):
                raise ValueError("Frequency-response solve exceeded the finite numerical range.")
            try:
                normalized_state = np.linalg.solve(normalized_matrix, normalized_input)
            except np.linalg.LinAlgError as exc:
                raise ValueError("Frequency-response operator is numerically singular.") from exc
            if not np.all(np.isfinite(normalized_state)):
                raise ValueError("Frequency-response solve exceeded the finite numerical range.")
            state = np.asarray(normalized_state, dtype=np.complex128)
        response[idx] = c_out @ state
        if not np.isfinite(response[idx]):
            raise ValueError("Frequency-response result exceeds the finite numerical range.")
    return response


def relaxation_spectrum(
    capacities: ArrayLike,
    edges: Sequence[Edge],
    loss: ArrayLike,
) -> tuple[FloatArray, FloatArray]:
    """Return positive decay rates and their reciprocal relaxation times."""
    cap, lap, lam, _ = system_matrices(capacities, edges, loss)
    inverse_roots = 1.0 / np.sqrt(np.diag(cap))
    q = np.empty_like(lap)
    try:
        for row in range(q.shape[0]):
            for column in range(row, q.shape[1]):
                value = math.fsum(
                    [
                        0.0
                        if lap[row, column] == 0.0
                        else _scaled_product(
                            float(lap[row, column]),
                            float(inverse_roots[row]),
                            float(inverse_roots[column]),
                        ),
                        0.0
                        if lam[row, column] == 0.0
                        else _scaled_product(
                            float(lam[row, column]),
                            float(inverse_roots[row]),
                            float(inverse_roots[column]),
                        ),
                    ]
                )
                q[row, column] = value
                q[column, row] = value
    except (OverflowError, ValueError) as exc:
        raise ValueError("Relaxation spectrum exceeds the finite numerical range.") from exc
    rates = np.asarray(np.linalg.eigvalsh(q), dtype=np.float64)
    if not np.all(np.isfinite(rates)):
        raise ValueError("Relaxation spectrum exceeds the finite numerical range.")
    if np.min(rates) <= 0:
        raise ValueError("Network has an unclosed zero mode.")
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        times = np.asarray(1.0 / rates, dtype=np.float64)
    if not np.all(np.isfinite(times)):
        raise ValueError("Relaxation times exceed the finite numerical range.")
    return rates, times


def two_reservoir_poles(
    c_surface: float,
    c_deep: float,
    coupling: float,
    loss: float,
) -> FloatArray:
    """Analytic poles of the two-reservoir model."""
    vals = (c_surface, c_deep, coupling, loss)
    if any(not np.isfinite(v) or v <= 0 for v in vals):
        raise ValueError("All two-reservoir parameters must be finite and positive.")

    def ratio_components(numerator: float, denominator: float) -> tuple[float, int]:
        numerator_mantissa, numerator_exponent = math.frexp(numerator)
        denominator_mantissa, denominator_exponent = math.frexp(denominator)
        mantissa, normalization_exponent = math.frexp(
            numerator_mantissa / denominator_mantissa
        )
        return mantissa, numerator_exponent - denominator_exponent + normalization_exponent

    deep_mantissa, deep_exponent = ratio_components(coupling, c_deep)
    surface_mantissa, surface_exponent = ratio_components(coupling, c_surface)
    loss_mantissa, loss_exponent = ratio_components(loss, c_surface)
    scale_exponent = max(deep_exponent, surface_exponent, loss_exponent)
    deep_scaled = math.ldexp(deep_mantissa, deep_exponent - scale_exponent)
    surface_scaled = math.ldexp(surface_mantissa, surface_exponent - scale_exponent)
    loss_scaled = math.ldexp(loss_mantissa, loss_exponent - scale_exponent)
    surface_rate_scaled = math.fsum([surface_scaled, loss_scaled])
    root_gap_scaled = math.hypot(
        deep_scaled - surface_rate_scaled,
        2.0 * math.sqrt(deep_scaled) * math.sqrt(surface_scaled),
    )
    fast_scaled = math.fsum(
        [0.5 * deep_scaled, 0.5 * surface_rate_scaled, 0.5 * root_gap_scaled]
    )
    fast_mantissa, fast_normalization_exponent = math.frexp(fast_scaled)
    fast_exponent = scale_exponent + fast_normalization_exponent
    try:
        fast_magnitude = math.ldexp(fast_mantissa, fast_exponent)
    except OverflowError as exc:
        raise ValueError("Two-reservoir poles exceed the finite numerical range.") from exc
    if not np.isfinite(fast_magnitude) or fast_magnitude <= 0.0:
        raise ValueError("Two-reservoir poles exceed the finite numerical range.")
    # Rationalize the slow root and normalize before forming products.  This
    # avoids both subtractive cancellation and overflow in the raw quadratic
    # coefficients when reservoir timescales are widely separated.
    slow_mantissa, slow_normalization_exponent = math.frexp(
        deep_mantissa * loss_mantissa / fast_mantissa
    )
    try:
        slow_magnitude = math.ldexp(
            slow_mantissa,
            deep_exponent
            + loss_exponent
            - fast_exponent
            + slow_normalization_exponent,
        )
    except OverflowError as exc:
        raise ValueError("Two-reservoir poles exceed the finite numerical range.") from exc
    slow_pole = -slow_magnitude
    fast_pole = -fast_magnitude
    if slow_pole == 0.0 or not np.isfinite(slow_pole):
        raise ValueError("Two-reservoir poles exceed the finite numerical range.")
    return np.array(
        [slow_pole, fast_pole],
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
    j = _as_finite_array(jacobians, name="jacobians")
    sigma = _as_finite_array(covariance, name="covariance")
    if j.ndim != 2:
        raise ValueError("jacobians must be two-dimensional.")
    if sigma.shape != (j.shape[0], j.shape[0]):
        raise ValueError("covariance shape must match measurement count.")
    sigma = _symmetrized(sigma, name="covariance")
    try:
        cholesky = np.linalg.cholesky(sigma)
    except np.linalg.LinAlgError as exc:
        raise ValueError("covariance must be positive definite.") from exc
    whitened = solve_triangular(cholesky, j, lower=True)
    return np.asarray(whitened.T @ whitened, dtype=np.float64)
