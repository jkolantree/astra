"""Core calculations for the Solar-Planetary Phase-Partition Theory (SPPT).

The module contains only reduced-order, transparent calculations used in the
preprint. It is not a general planetary evolution code. All inputs are SI
unless a function explicitly states otherwise.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.linalg import eigh

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
    if omega <= 0.0 or release_time <= 0.0:
        raise ValueError("omega and release_time must be positive.")
    times = _as_float_array(t)
    z = omega * release_time
    amplitude = capture_amplitude * release_time / np.sqrt(1.0 + z * z)
    phase = np.arctan(z)
    return np.asarray(
        capture_mean * release_time + amplitude * np.cos(omega * times - phase),
        dtype=np.float64,
    )


def trap_loop_area(capture_amplitude: float, omega: float, release_time: float) -> float:
    r"""Signed area integral \oint M dc for the steady periodic trap model."""
    if omega <= 0.0 or release_time <= 0.0:
        raise ValueError("omega and release_time must be positive.")
    return float(
        -np.pi
        * capture_amplitude**2
        * omega
        * release_time**2
        / (1.0 + (omega * release_time) ** 2)
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
    return Bm @ np.diag(k) @ Bm.T


def generalized_relaxation_eigenvalues(
    B: ArrayLike,
    conductance: ArrayLike,
    capacity: ArrayLike,
) -> NDArray[np.float64]:
    """Return sorted eigenvalues of L v = lambda C v."""
    C = _as_float_array(capacity, ndim=1)
    if np.any(C <= 0.0):
        raise ValueError("Capacities must be strictly positive.")
    L = weighted_laplacian(B, conductance)
    if L.shape[0] != C.size:
        raise ValueError("One capacity is required per node.")
    values = eigh(L, np.diag(C), eigvals_only=True)
    values[np.abs(values) < 1e-12] = 0.0
    return np.sort(values)


def weak_cut_upper_bound(
    cut_conductance: float,
    capacity_left: float,
    capacity_right: float,
) -> float:
    """Rayleigh-quotient upper bound on the first nonzero relaxation rate."""
    if cut_conductance < 0.0 or capacity_left <= 0.0 or capacity_right <= 0.0:
        raise ValueError("Cut conductance must be nonnegative and capacities positive.")
    return cut_conductance * (1.0 / capacity_left + 1.0 / capacity_right)


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
    if internal_power < 0.0 or absorbed_external_power < 0.0:
        raise ValueError("Power terms must be nonnegative.")
    if conductance <= 0.0 or radiative_coefficient <= 0.0:
        raise ValueError("conductance and radiative_coefficient must be positive.")
    upper = ((internal_power + absorbed_external_power) / radiative_coefficient) ** 0.25
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
    if not (0.0 <= connectivity <= 1.0):
        raise ValueError("connectivity must lie in [0, 1].")
    if k_min <= 0.0 or k_span < 0.0:
        raise ValueError("k_min must be positive and k_span nonnegative.")
    if not np.isfinite(upper_temperature_slope):
        raise ValueError("upper_temperature_slope must be finite.")
    K = k_min + k_span * connectivity
    return float(
        K * (1.0 - upper_temperature_slope)
        + temperature_contrast * k_span * d_connectivity_d_temperature
    )
