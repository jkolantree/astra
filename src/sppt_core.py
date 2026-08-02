"""Core calculations for the Solar-Planetary Phase-Partition Theory (SPPT).

The module contains only reduced-order, transparent calculations used in the
preprint. It is not a general planetary evolution code. All inputs are SI
unless a function explicitly states otherwise.
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.linalg import null_space

FARADAY_C_PER_MOL = 96485.33212
SECONDS_PER_JULIAN_YEAR = 365.25 * 24.0 * 3600.0
MOLAR_MASS_CO2_KG_PER_MOL = 44.0095e-3
DG_CO2_TO_C_O2_J_PER_MOL = 394.3e3


def _as_float_array(value: ArrayLike, *, ndim: int | None = None) -> NDArray[np.float64]:
    arr = np.asarray(value, dtype=float)
    if ndim is not None and arr.ndim != ndim:
        raise ValueError(f"Expected an array with ndim={ndim}; received shape {arr.shape}.")
    if not np.all(np.isfinite(arr)):
        raise ValueError("All numerical inputs must be finite.")
    return arr


def _require_finite_scalars(*values: float) -> None:
    if not all(np.isfinite(value) for value in values):
        raise ValueError("All numerical inputs must be finite.")


def _scaled_product(*values: float) -> float:
    """Multiply finite scalars with binary exponent bookkeeping."""
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
    except OverflowError as error:
        raise ValueError("Numerical result exceeds the finite range.") from error
    if not math.isfinite(result):
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
    return math.copysign(result, numerator)


def incidence_matrix(n_nodes: int, edges: Sequence[tuple[int, int]]) -> NDArray[np.float64]:
    """Return a directed node-edge incidence matrix.

    Each edge is ``(tail, head)``. The tail receives -1 and the head +1.
    """
    if n_nodes < 1:
        raise ValueError("n_nodes must be positive.")
    matrix = np.zeros((n_nodes, len(edges)), dtype=float)
    for column, (tail, head) in enumerate(edges):
        if tail == head:
            raise ValueError("Self-loops are excluded from the transport incidence matrix.")
        if not (0 <= tail < n_nodes and 0 <= head < n_nodes):
            raise IndexError(f"Edge {(tail, head)} is outside 0..{n_nodes - 1}.")
        matrix[tail, column] = -1.0
        matrix[head, column] = 1.0
    return matrix


def species_tendency(
    B: ArrayLike,
    edge_flux: ArrayLike,
    reaction_rate: ArrayLike,
    stoichiometry: ArrayLike,
    source: ArrayLike,
    escape: ArrayLike,
) -> NDArray[np.float64]:
    """Evaluate dM/dt = B J + R N^T + S - E.

    Shapes:
      B: (n_reservoirs, n_edges)
      edge_flux: (n_edges, n_species)
      reaction_rate: (n_reservoirs, n_reactions)
      stoichiometry: (n_species, n_reactions)
      source, escape: (n_reservoirs, n_species)
    """
    Bm = _as_float_array(B, ndim=2)
    J = _as_float_array(edge_flux, ndim=2)
    R = _as_float_array(reaction_rate, ndim=2)
    N = _as_float_array(stoichiometry, ndim=2)
    S = _as_float_array(source, ndim=2)
    E = _as_float_array(escape, ndim=2)
    n, m = Bm.shape
    if J.shape[0] != m:
        raise ValueError("edge_flux has the wrong number of edges.")
    species = J.shape[1]
    if R.shape[0] != n or N.shape[0] != species or R.shape[1] != N.shape[1]:
        raise ValueError("reaction_rate and stoichiometry shapes are inconsistent.")
    if S.shape != (n, species) or E.shape != (n, species):
        raise ValueError("source and escape must have shape (n_reservoirs, n_species).")
    return Bm @ J + R @ N.T + S - E


def weighted_inventory_tendency(
    dMdt: ArrayLike,
    conserved_weights: ArrayLike,
) -> float:
    """Return the whole-network tendency of a weighted species inventory."""
    tendency = _as_float_array(dMdt, ndim=2)
    weights = _as_float_array(conserved_weights, ndim=1)
    if tendency.shape[1] != weights.size:
        raise ValueError("Weight vector length must equal the number of species.")
    return float(np.ones(tendency.shape[0]) @ tendency @ weights)


def trap_periodic_solution(
    t: ArrayLike,
    capture_mean: float,
    capture_amplitude: float,
    omega: float,
    release_time: float,
) -> NDArray[np.float64]:
    """Steady periodic solution of dM/dt = c0 + c1 cos(omega t) - M/tau."""
    _require_finite_scalars(capture_mean, capture_amplitude, omega, release_time)
    if omega <= 0.0 or release_time <= 0.0:
        raise ValueError("omega and release_time must be positive.")
    times = _as_float_array(t)
    if release_time < 1.0:
        scaled_frequency = omega * release_time
        denominator = np.hypot(1.0, scaled_frequency)
        response_inside_release = capture_amplitude / denominator
        phase = np.arctan(scaled_frequency)
    else:
        inverse_release_time = 1.0 / release_time
        denominator = np.hypot(inverse_release_time, omega)
        response_inside_release = capture_amplitude * (inverse_release_time / denominator)
        phase = np.arctan2(omega, inverse_release_time)
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        result = release_time * (
            capture_mean + response_inside_release * np.cos(omega * times - phase)
        )
    if not np.all(np.isfinite(result)):
        raise ValueError("Periodic trap solution exceeds the finite numerical range.")
    return np.asarray(result, dtype=np.float64)


def trap_loop_area(capture_amplitude: float, omega: float, release_time: float) -> float:
    r"""Signed area integral \oint M dc for the steady periodic trap model."""
    _require_finite_scalars(capture_amplitude, omega, release_time)
    if omega <= 0.0 or release_time <= 0.0:
        raise ValueError("omega and release_time must be positive.")
    if release_time < 1.0:
        scaled_frequency = omega * release_time
        denominator = np.hypot(1.0, scaled_frequency)
        response_multiplier = release_time / denominator
        area_factors = [
            float(response_multiplier),
            float(omega / denominator),
            release_time,
        ]
    else:
        inverse_release_time = 1.0 / release_time
        denominator = np.hypot(inverse_release_time, omega)
        response_multiplier = 1.0 / denominator
        area_factors = [float(response_multiplier), float(omega / denominator)]
    return -_scaled_product(
        float(np.pi),
        capture_amplitude,
        capture_amplitude,
        *area_factors,
    )


def weighted_laplacian(
    B: ArrayLike,
    conductance: ArrayLike,
) -> NDArray[np.float64]:
    """Return L = B diag(k) B^T for positive edge conductances."""
    Bm = _as_float_array(B, ndim=2)
    k = _as_float_array(conductance, ndim=1)
    if Bm.shape[1] != k.size:
        raise ValueError("One conductance is required per edge.")
    if np.any(k < 0.0):
        raise ValueError("Conductances cannot be negative.")
    diagonal_contributions: list[list[float]] = []
    for row in Bm:
        contributions: list[float] = []
        for coefficient, conductance_value in zip(row, k, strict=True):
            if coefficient == 0.0 or conductance_value == 0.0:
                contributions.append(0.0)
                continue
            contribution = _scaled_product(
                float(coefficient), float(coefficient), float(conductance_value)
            )
            if contribution == 0.0:
                raise ValueError(
                    "Incident conductance dynamic range exceeds reliable Laplacian assembly."
                )
            contributions.append(contribution)
        diagonal_contributions.append(contributions)
        positive = [value for value in contributions if value > 0.0]
        if len(positive) >= 2:
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
                if (
                    retained <= 0.0
                    or abs(retained - contribution) > tolerance * contribution
                ):
                    raise ValueError(
                        "Incident conductance dynamic range exceeds reliable Laplacian assembly."
                    )
    laplacian = np.empty((Bm.shape[0], Bm.shape[0]), dtype=float)
    try:
        for row in range(Bm.shape[0]):
            laplacian[row, row] = math.fsum(diagonal_contributions[row])
            for column in range(row + 1, Bm.shape[0]):
                terms = (
                    _scaled_product(
                        float(Bm[row, edge]),
                        float(k[edge]),
                        float(Bm[column, edge]),
                    )
                    for edge in range(k.size)
                    if Bm[row, edge] != 0.0
                    and k[edge] != 0.0
                    and Bm[column, edge] != 0.0
                )
                value = math.fsum(terms)
                laplacian[row, column] = value
                laplacian[column, row] = value
    except OverflowError as exc:
        raise ValueError("Weighted Laplacian exceeds the finite numerical range.") from exc
    if not np.all(np.isfinite(laplacian)):
        raise ValueError("Weighted Laplacian exceeds the finite numerical range.")
    return np.asarray(laplacian, dtype=np.float64)


def generalized_relaxation_eigenvalues(
    B: ArrayLike,
    conductance: ArrayLike,
    capacity: ArrayLike,
) -> NDArray[np.float64]:
    """Return sorted eigenvalues of L v = lambda C v."""
    Bm = _as_float_array(B, ndim=2)
    k = _as_float_array(conductance, ndim=1)
    C = _as_float_array(capacity, ndim=1)
    if np.any(C <= 0.0):
        raise ValueError("Capacities must be strictly positive.")
    weighted_laplacian(Bm, k)
    if Bm.shape[0] != C.size:
        raise ValueError("One capacity is required per node.")
    edge_nodes: list[tuple[int, int]] = []
    for column in range(Bm.shape[1]):
        nonzero = np.flatnonzero(Bm[:, column])
        if (
            nonzero.size != 2
            or Bm[nonzero[0], column] not in {-1.0, 1.0}
            or Bm[nonzero[1], column] != -Bm[nonzero[0], column]
        ):
            raise ValueError(
                "Generalized relaxation requires a standard signed node-edge incidence matrix."
            )
        edge_nodes.append((int(nonzero[0]), int(nonzero[1])))

    parent = list(range(Bm.shape[0]))

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for column, (left, right) in enumerate(edge_nodes):
        if k[column] <= 0.0:
            continue
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root
    components: dict[int, list[int]] = {}
    for node in range(Bm.shape[0]):
        components.setdefault(find(node), []).append(node)

    rates: list[float] = []
    for nodes in components.values():
        if len(nodes) == 1:
            continue
        node_set = set(nodes)
        columns = [
            column
            for column, (left, right) in enumerate(edge_nodes)
            if k[column] > 0.0 and left in node_set and right in node_set
        ]
        normalized = np.empty((len(nodes), len(columns)), dtype=np.float64)
        try:
            for local_row, node in enumerate(nodes):
                for local_column, column in enumerate(columns):
                    normalized[local_row, local_column] = _scaled_product_over(
                        float(Bm[node, column]),
                        math.sqrt(float(k[column])),
                        math.sqrt(float(C[node])),
                    )
        except ValueError as exc:
            raise ValueError("Relaxation eigenvalues exceed the finite numerical range.") from exc
        zero_mode = np.sqrt(C[nodes])
        zero_mode_scaled = zero_mode / float(np.max(zero_mode))
        if np.any((zero_mode != 0.0) & (zero_mode_scaled == 0.0)):
            raise ValueError("Relaxation eigenvalues exceed the finite numerical range.")
        complement = null_space(zero_mode_scaled.reshape(1, -1))
        if complement.shape != (len(nodes), len(nodes) - 1):
            raise ValueError("Unable to resolve the structural conservation mode.")
        reduced = complement.T @ normalized
        singular_values = np.linalg.svd(reduced, compute_uv=False)
        if singular_values.size != len(nodes) - 1 or not np.all(
            np.isfinite(singular_values)
        ):
            raise ValueError("Relaxation eigenvalues exceed the finite numerical range.")
        try:
            component_rates = [
                _scaled_product(float(value), float(value)) for value in singular_values
            ]
        except ValueError as exc:
            raise ValueError("Relaxation eigenvalues exceed the finite numerical range.") from exc
        if any(rate <= 0.0 or not math.isfinite(rate) for rate in component_rates):
            raise ValueError("Relaxation eigenvalues exceed the finite numerical range.")
        rates.extend(component_rates)
    return np.sort(
        np.array([0.0] * len(components) + rates, dtype=np.float64)
    )


def weak_cut_upper_bound(
    cut_conductance: float,
    capacity_left: float,
    capacity_right: float,
) -> float:
    """Rayleigh-quotient upper bound on the first nonzero relaxation rate."""
    _require_finite_scalars(cut_conductance, capacity_left, capacity_right)
    if cut_conductance < 0.0 or capacity_left <= 0.0 or capacity_right <= 0.0:
        raise ValueError("Cut conductance must be nonnegative and capacities positive.")
    return cut_conductance / capacity_left + cut_conductance / capacity_right


@dataclass(frozen=True)
class ElectroreductionScale:
    current_a: float
    co2_kg_per_year_ideal: float
    electrical_charge_c_per_year: float
    minimum_energy_j_per_kg_co2: float
    minimum_power_w: float


def electroreduction_scale(
    current_a: float,
    *,
    faradaic_efficiency: float = 1.0,
    delta_g_j_per_mol: float = DG_CO2_TO_C_O2_J_PER_MOL,
) -> ElectroreductionScale:
    """Ideal four-electron CO2-to-C throughput and reversible power."""
    _require_finite_scalars(current_a, faradaic_efficiency, delta_g_j_per_mol)
    if current_a < 0.0:
        raise ValueError("current_a must be nonnegative.")
    if not (0.0 < faradaic_efficiency <= 1.0):
        raise ValueError("faradaic_efficiency must lie in (0, 1].")
    charge = current_a * SECONDS_PER_JULIAN_YEAR
    mol = charge * faradaic_efficiency / (4.0 * FARADAY_C_PER_MOL)
    kg = mol * MOLAR_MASS_CO2_KG_PER_MOL
    e_per_kg = delta_g_j_per_mol / MOLAR_MASS_CO2_KG_PER_MOL
    min_power = current_a * faradaic_efficiency * delta_g_j_per_mol / (4.0 * FARADAY_C_PER_MOL)
    return ElectroreductionScale(
        current_a=float(current_a),
        co2_kg_per_year_ideal=float(kg),
        electrical_charge_c_per_year=float(charge),
        minimum_energy_j_per_kg_co2=float(e_per_kg),
        minimum_power_w=float(min_power),
    )


def current_for_co2_rate(co2_kg_per_year: float, *, faradaic_efficiency: float = 1.0) -> float:
    """Current required for a target ideal CO2 conversion rate."""
    _require_finite_scalars(co2_kg_per_year, faradaic_efficiency)
    if co2_kg_per_year < 0.0:
        raise ValueError("co2_kg_per_year must be nonnegative.")
    if not (0.0 < faradaic_efficiency <= 1.0):
        raise ValueError("faradaic_efficiency must lie in (0, 1].")
    mol_per_year = co2_kg_per_year / MOLAR_MASS_CO2_KG_PER_MOL
    return float(4.0 * FARADAY_C_PER_MOL * mol_per_year / (SECONDS_PER_JULIAN_YEAR * faradaic_efficiency))


def static_two_reservoir_equilibrium(
    internal_power: float,
    absorbed_external_power: float,
    conductance: float,
    radiative_coefficient: float = 1.0,
) -> tuple[float, float]:
    """Equilibrium of a dimensionless two-reservoir radiative model.

    The upper reservoir radiates L(T_u)=a*T_u^4. The returned tuple is
    (T_deep, T_upper). The upper temperature is independent of conductance.
    """
    _require_finite_scalars(
        internal_power, absorbed_external_power, conductance, radiative_coefficient
    )
    if internal_power < 0.0 or absorbed_external_power < 0.0:
        raise ValueError("Power terms must be nonnegative.")
    if conductance <= 0.0 or radiative_coefficient <= 0.0:
        raise ValueError("conductance and radiative_coefficient must be positive.")
    power_scale = max(internal_power, absorbed_external_power)
    if power_scale == 0.0:
        upper = 0.0
    else:
        normalized_power = (
            internal_power / power_scale + absorbed_external_power / power_scale
        )
        upper = (
            power_scale**0.25
            / radiative_coefficient**0.25
            * normalized_power**0.25
        )
    deep = upper + internal_power / conductance
    return float(deep), float(upper)


def effective_flux_slope(
    temperature_contrast: float,
    connectivity: float,
    d_connectivity_d_temperature: float,
    k_min: float,
    k_span: float,
    upper_temperature_slope: float = 0.0,
) -> float:
    """Return ``d[K(psi)(T_d-T_u)]/dT_d``.

    ``upper_temperature_slope`` is ``dT_u/dT_d``.  The default zero is the
    explicitly fixed-upper-state toy closure used in the manuscript.  The full
    derivative is ``K*(1-dT_u/dT_d) + DeltaT*k_span*dpsi/dT_d``.

    A negative value is a local negative-differential-transport condition. It
    is a fold precursor in a reduced constitutive model, not by itself proof of
    a global bifurcation.
    """
    _require_finite_scalars(
        temperature_contrast,
        connectivity,
        d_connectivity_d_temperature,
        k_min,
        k_span,
        upper_temperature_slope,
    )
    if not (0.0 <= connectivity <= 1.0):
        raise ValueError("connectivity must lie in [0, 1].")
    if k_min <= 0.0 or k_span < 0.0:
        raise ValueError("k_min must be positive and k_span nonnegative.")
    K = k_min + k_span * connectivity
    return float(
        K * (1.0 - upper_temperature_slope)
        + temperature_contrast * k_span * d_connectivity_d_temperature
    )
