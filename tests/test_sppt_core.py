from __future__ import annotations

import math

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


def test_trap_closed_forms_remain_finite_at_separated_scales() -> None:
    omega = 1.0e100
    tau = 1.0e100
    time = np.array([np.pi / (2.0 * omega)])
    solution = sppt.trap_periodic_solution(time, 0.0, 1.0, omega, tau)
    assert solution[0] == pytest.approx(1.0e-100, rel=1.0e-14, abs=0.0)
    assert sppt.trap_loop_area(1.0, omega, tau) == pytest.approx(
        -np.pi * 1.0e-100, rel=1.0e-15, abs=0.0
    )


def test_trap_closed_forms_preserve_tiny_positive_release_time() -> None:
    solution = sppt.trap_periodic_solution([0.0], 0.0, 1.0, 1.0, 1.0e-320)
    np.testing.assert_allclose(solution, [1.0e-320], rtol=0.0, atol=5.0e-324)
    area = sppt.trap_loop_area(1.0e160, 1.0, 1.0e-320)
    assert area == pytest.approx(-np.pi * 1.0e-320, rel=0.0, abs=5.0e-324)


def test_trap_periodic_solution_factors_cancelling_extreme_baseline() -> None:
    solution = sppt.trap_periodic_solution([0.0], 6.0e307, -6.0e307, 0.1, 3.0)
    assert solution[0] == pytest.approx(1.4862385321100917e307, rel=2.0e-15)


def test_trap_loop_area_avoids_finite_product_overflow() -> None:
    area = sppt.trap_loop_area(1.0e250, 1.0e-100, 1.0e-100)
    assert area == pytest.approx(-np.pi * 1.0e200, rel=2.0e-15)


def test_trap_loop_area_preserves_underflowed_phase_product() -> None:
    area = sppt.trap_loop_area(1.0e300, 1.0e-300, 1.0e-100)
    assert area == pytest.approx(-np.pi * 1.0e100, rel=2.0e-15)


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


def test_small_positive_relaxation_mode_is_not_erased() -> None:
    incidence = sppt.incidence_matrix(2, [(0, 1)])
    eigenvalues = sppt.generalized_relaxation_eigenvalues(
        incidence, [1.0e-13], [1.0, 1.0]
    )
    assert eigenvalues[0] == pytest.approx(0.0, abs=1.0e-30)
    assert eigenvalues[1] == pytest.approx(2.0e-13, rel=1.0e-15, abs=0.0)


def test_generalized_spectrum_sets_only_structural_null_modes_to_zero() -> None:
    incidence = sppt.incidence_matrix(2, [(0, 1)])
    values = sppt.generalized_relaxation_eigenvalues(
        incidence, [1.0e-300], [1.0e-308, 1.0e-308]
    )
    assert values[0] == 0.0
    assert values[1] == pytest.approx(2.0e8, rel=2.0e-15)


@pytest.mark.parametrize(
    "capacity",
    [[1.0e308, 5.0e-324], [1.0e-308, 1.0e-308]],
)
def test_generalized_spectrum_rejects_nonfinite_results(capacity) -> None:
    incidence = sppt.incidence_matrix(2, [(0, 1)])
    with pytest.raises(ValueError, match="finite numerical range"):
        sppt.generalized_relaxation_eigenvalues(incidence, [1.0], capacity)


@pytest.mark.parametrize(
    "incidence",
    [
        np.array([[1.0, 0.0, 1.0], [1.0, 1.0, 0.0], [0.0, 1.0, 1.0]]),
        np.diag([1.0, 1.0e-150]),
    ],
)
def test_generalized_spectrum_requires_standard_graph_incidence(incidence) -> None:
    with pytest.raises(ValueError, match="standard signed"):
        sppt.generalized_relaxation_eigenvalues(
            incidence, np.ones(incidence.shape[1]), np.ones(incidence.shape[0])
        )


def test_generalized_spectrum_preserves_each_components_slow_mode() -> None:
    incidence = sppt.incidence_matrix(4, [(0, 1), (2, 3)])
    values = sppt.generalized_relaxation_eigenvalues(
        incidence, [1.0e-300, 1.0e-320], [1.0e-308, 1.0e-308, 1.0, 1.0]
    )
    assert values[:2] == pytest.approx([0.0, 0.0], abs=0.0)
    assert values[2] == pytest.approx(2.0e-320, rel=2.0e-5, abs=5.0e-324)
    assert values[3] == pytest.approx(2.0e8, rel=2.0e-15)


def test_generalized_spectrum_does_not_confuse_cycle_roundoff_with_weak_component() -> None:
    incidence = sppt.incidence_matrix(
        5, [(0, 1), (1, 2), (2, 0), (3, 4)]
    )
    values = sppt.generalized_relaxation_eigenvalues(
        incidence,
        [1.0e200, 1.0e200, 1.0e200, 1.0e-200],
        [1.0, 1.0, 1.0, 1.0, 1.0],
    )
    assert values[:2] == pytest.approx([0.0, 0.0], abs=0.0)
    assert values[2] == pytest.approx(2.0e-200, rel=2.0e-15, abs=0.0)
    assert values[3:] == pytest.approx([3.0e200, 3.0e200], rel=2.0e-15)
def test_unresolvable_incident_conductance_ratio_fails_closed() -> None:
    incidence = sppt.incidence_matrix(3, [(0, 1), (0, 2)])
    with pytest.raises(ValueError, match="dynamic range"):
        sppt.generalized_relaxation_eigenvalues(
            incidence, [float(2**53), 1.0], [1.0, 1.0, 1.0]
        )


def test_core_laplacian_rejects_collective_rounding_distortion() -> None:
    edges = [(0, 1), (0, 2), (0, 3)]
    conductances = np.array([1.0, float(2**-53), float(2**-52)])
    incidence = sppt.incidence_matrix(4, edges)
    with pytest.raises(ValueError, match="dynamic range"):
        sppt.weighted_laplacian(incidence, conductances)
    with pytest.raises(ValueError, match="dynamic range"):
        sppt.weighted_laplacian(incidence[:, ::-1], conductances[::-1])


def test_core_laplacian_is_permutation_invariant_when_resolvable() -> None:
    edges = [(0, 1), (0, 2), (0, 3)]
    conductances = np.array([0.1, 0.2, 0.3])
    incidence = sppt.incidence_matrix(4, edges)
    forward = sppt.weighted_laplacian(incidence, conductances)
    reverse = sppt.weighted_laplacian(incidence[:, ::-1], conductances[::-1])
    assert forward[0, 0] == math.fsum(conductances)
    np.testing.assert_array_equal(forward, reverse)


def test_core_parallel_edges_match_their_resolvable_aggregate() -> None:
    parallel_incidence = sppt.incidence_matrix(2, [(0, 1), (0, 1)])
    aggregate_incidence = sppt.incidence_matrix(2, [(0, 1)])
    parallel = sppt.weighted_laplacian(parallel_incidence, [1.0, 0.001])
    aggregate = sppt.weighted_laplacian(aggregate_incidence, [1.001])
    np.testing.assert_array_equal(parallel, aggregate)


def test_core_laplacian_rejects_material_weak_edge_distortion() -> None:
    incidence = sppt.incidence_matrix(3, [(0, 1), (0, 2)])
    with pytest.raises(ValueError, match="dynamic range"):
        sppt.weighted_laplacian(incidence, [float(2**53), 1.5])


def test_weak_cut_rejects_nonpositive_capacity() -> None:
    with pytest.raises(ValueError, match="capacities positive"):
        sppt.weak_cut_upper_bound(0.1, 0.0, 1.0)


def test_weak_cut_bound_avoids_reciprocal_overflow() -> None:
    assert sppt.weak_cut_upper_bound(1.0e-308, 1.0e-308, 1.0e-308) == pytest.approx(2.0)


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


def test_static_equilibrium_avoids_power_sum_and_ratio_overflow() -> None:
    tiny = sppt.static_two_reservoir_equilibrium(1.0e-308, 0.0, 1.0, 1.0e308)
    huge = sppt.static_two_reservoir_equilibrium(1.0e308, 1.0e308, 1.0e308)
    assert tiny == pytest.approx([1.0e-154, 1.0e-154], rel=1.0e-15, abs=0.0)
    expected_upper = 2.0**0.25 * 1.0e77
    assert huge == pytest.approx([expected_upper, expected_upper], rel=1.0e-15)


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


@pytest.mark.parametrize(
    "operation",
    [
        lambda: sppt.trap_loop_area(1.0, np.nan, 1.0),
        lambda: sppt.weak_cut_upper_bound(np.nan, 1.0, 1.0),
        lambda: sppt.electroreduction_scale(np.nan),
        lambda: sppt.current_for_co2_rate(np.nan),
        lambda: sppt.static_two_reservoir_equilibrium(np.nan, 1.0, 1.0),
        lambda: sppt.effective_flux_slope(1.0, 0.5, np.nan, 1.0, 1.0),
    ],
)
def test_scalar_core_apis_reject_nonfinite_inputs(operation) -> None:
    with pytest.raises(ValueError, match="finite"):
        operation()
