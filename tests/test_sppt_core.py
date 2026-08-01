from __future__ import annotations

import numpy as np
import pytest

import sppt_core as sppt


def test_species_balance_conserves_weighted_internal_inventory() -> None:
    incidence = sppt.incidence_matrix(3, [(0, 1), (1, 2)])
    flux = np.array([[2.0, -1.0], [0.25, 3.0]])
    reaction = np.array([[1.0], [-2.0], [0.5]])
    stoichiometry = np.array([[-2.0], [1.0]])
    tendency = sppt.species_tendency(
        incidence,
        flux,
        reaction,
        stoichiometry,
        np.zeros((3, 2)),
        np.zeros((3, 2)),
    )
    assert sppt.weighted_inventory_tendency(tendency, [1.0, 2.0]) == pytest.approx(0.0)


def test_species_balance_rejects_dimension_mismatch() -> None:
    with pytest.raises(ValueError, match="wrong number of edges"):
        sppt.species_tendency(
            np.zeros((2, 2)),
            np.zeros((1, 1)),
            np.zeros((2, 1)),
            np.zeros((1, 1)),
            np.zeros((2, 1)),
            np.zeros((2, 1)),
        )


def test_periodic_solution_satisfies_ode() -> None:
    t = np.linspace(0.0, 2.0 * np.pi / 1.3, 20001, endpoint=False)
    c0, c1, omega, tau = 0.8, 0.75, 1.3, 1.0 / 1.3
    mass = sppt.trap_periodic_solution(t, c0, c1, omega, tau)
    dt = t[1] - t[0]
    derivative = (np.roll(mass, -1) - np.roll(mass, 1)) / (2.0 * dt)
    forcing = c0 + c1 * np.cos(omega * t)
    assert np.max(np.abs(derivative - (forcing - mass / tau))) < 2.0e-7


def test_periodic_loop_area_matches_quadrature() -> None:
    c0, c1, omega, tau = 0.8, 0.75, 1.3, 0.9
    period = 2.0 * np.pi / omega
    t = np.linspace(0.0, period, 200001)
    mass = sppt.trap_periodic_solution(t, c0, c1, omega, tau)
    dc_dt = -c1 * omega * np.sin(omega * t)
    numerical = np.trapezoid(mass * dc_dt, t)
    assert numerical == pytest.approx(sppt.trap_loop_area(c1, omega, tau), abs=3.0e-10)


def test_raw_loop_magnitude_is_monotone_in_release_time() -> None:
    taus = np.geomspace(1.0e-3, 1.0e3, 1000)
    areas = np.abs([sppt.trap_loop_area(0.75, 1.3, tau) for tau in taus])
    assert np.all(np.diff(areas) > 0.0)


def test_release_normalized_loop_peaks_at_omega_tau_one() -> None:
    omega = 1.3
    taus = np.geomspace(1.0e-3, 1.0e3, 20001)
    normalized = np.abs([sppt.trap_loop_area(0.75, omega, tau) / tau for tau in taus])
    peak_tau = taus[int(np.argmax(normalized))]
    assert peak_tau == pytest.approx(1.0 / omega, rel=5.0e-4)


def test_weak_cut_bound_with_positive_capacities_and_connected_weights() -> None:
    incidence = sppt.incidence_matrix(4, [(0, 1), (1, 2), (2, 3)])
    capacity = np.array([2.0, 3.0, 5.0, 7.0])
    conductance = np.array([4.0, 0.1, 6.0])
    eigenvalues = sppt.generalized_relaxation_eigenvalues(incidence, conductance, capacity)
    bound = sppt.weak_cut_upper_bound(0.1, 5.0, 12.0)
    assert eigenvalues[1] <= bound + 1.0e-12
    assert eigenvalues[1] > 0.0


def test_weak_cut_rejects_nonpositive_capacity() -> None:
    with pytest.raises(ValueError, match="capacities positive"):
        sppt.weak_cut_upper_bound(0.1, 0.0, 1.0)


def test_electroreduction_scale_is_supplied_free_energy_not_latent_heat() -> None:
    scale = sppt.electroreduction_scale(1.0e6)
    assert scale.co2_kg_per_year_ideal == pytest.approx(3.598563e6, rel=2.0e-7)
    assert sppt.current_for_co2_rate(1.0e12) == pytest.approx(2.778887e11, rel=2.0e-7)
    assert scale.minimum_energy_j_per_kg_co2 == pytest.approx(8.9594e6, rel=2.0e-5)


def test_static_boundary_independence_requires_positive_conductance() -> None:
    equilibria = [sppt.static_two_reservoir_equilibrium(1.0, 2.0, k) for k in (0.1, 1.0, 10.0)]
    assert np.ptp([upper for _, upper in equilibria]) == pytest.approx(0.0)
    assert len({deep for deep, _ in equilibria}) == 3
    with pytest.raises(ValueError, match="conductance"):
        sppt.static_two_reservoir_equilibrium(1.0, 2.0, 0.0)


def test_complete_state_dependent_flux_derivative_matches_finite_difference() -> None:
    td = 8.0
    upper_slope = 0.35
    psi0 = 0.4
    psi_slope = -0.08
    k_min, k_span = 0.2, 1.7
    tu0 = 3.0

    def flux(deep_temperature: float) -> float:
        psi = psi0 + psi_slope * (deep_temperature - td)
        upper = tu0 + upper_slope * (deep_temperature - td)
        return (k_min + k_span * psi) * (deep_temperature - upper)

    eps = 1.0e-6
    numerical = (flux(td + eps) - flux(td - eps)) / (2.0 * eps)
    analytic = sppt.effective_flux_slope(
        td - tu0,
        psi0,
        psi_slope,
        k_min,
        k_span,
        upper_slope,
    )
    assert analytic == pytest.approx(numerical, rel=1.0e-9, abs=1.0e-9)
