from __future__ import annotations

import math

import numpy as np
import pytest

import astra_reservoir as astra

EDGES = [astra.Edge(0, 1, 0.2)]


def test_weighted_laplacian_is_conservative_and_psd() -> None:
    laplacian = astra.weighted_laplacian(3, [astra.Edge(0, 1, 0.2), astra.Edge(1, 2, 1.4)])
    assert np.allclose(laplacian @ np.ones(3), 0.0)
    assert np.min(np.linalg.eigvalsh(laplacian)) >= -1.0e-12


def test_two_reservoir_steady_state_and_step_response() -> None:
    capacities = [20.0, 1.0]
    loss = [0.0, 1.0]
    power = [1.0, 0.0]
    equilibrium = astra.steady_state(capacities, EDGES, loss, power)
    response = astra.step_response(capacities, EDGES, loss, power, [0.0, 2000.0])
    assert equilibrium == pytest.approx([6.0, 1.0])
    assert response[-1] == pytest.approx(equilibrium, rel=1.0e-4)


def test_two_reservoir_poles_match_matrix_rates() -> None:
    _, _, _, matrix = astra.system_matrices([20.0, 1.0], EDGES, [0.0, 1.0])
    assert np.sort(astra.two_reservoir_poles(1.0, 20.0, 0.2, 1.0)) == pytest.approx(
        np.sort(np.linalg.eigvals(matrix).real)
    )


def test_two_reservoir_poles_preserve_slow_mode_across_separated_scales() -> None:
    poles = astra.two_reservoir_poles(1.0, 1.0e16, 1.0, 1.0)
    assert poles[0] == pytest.approx(-5.0e-17, rel=1.0e-15, abs=0.0)
    assert poles[1] == pytest.approx(-2.0, rel=1.0e-15)


def test_two_reservoir_poles_avoid_coefficient_overflow() -> None:
    poles = astra.two_reservoir_poles(1.0, 1.0e200, 1.0, 1.0)
    assert poles[0] == pytest.approx(-5.0e-201, rel=1.0e-15, abs=0.0)
    assert poles[1] == pytest.approx(-2.0, rel=1.0e-15)


def test_two_reservoir_poles_preserve_representable_extreme_slow_mode() -> None:
    poles = astra.two_reservoir_poles(1.0e308, 1.0, 4.0e307, 1.0e208)
    assert poles[0] == pytest.approx(-1.0e-100, rel=2.0e-15, abs=0.0)
    assert poles[1] == pytest.approx(-4.0e307, rel=2.0e-15, abs=0.0)


def test_loss_matrix_rejects_material_relative_asymmetry() -> None:
    loss = np.array([[2.0e12, 1.0e12], [1.0e12 + 9.0e6, 2.0e12]])
    with pytest.raises(ValueError, match="symmetric"):
        astra.system_matrices([1.0, 1.0], [], loss)


def test_reservoir_laplacian_rejects_unresolvable_incident_edge_ratio() -> None:
    edges = [astra.Edge(0, 1, float(2**53)), astra.Edge(0, 2, 1.0)]
    with pytest.raises(ValueError, match="dynamic range"):
        astra.weighted_laplacian(3, edges)


def test_reservoir_laplacian_rejects_collective_rounding_distortion() -> None:
    conductances = [1.0, float(2**-53), float(2**-52)]
    edges = [astra.Edge(0, index + 1, value) for index, value in enumerate(conductances)]
    with pytest.raises(ValueError, match="dynamic range"):
        astra.weighted_laplacian(4, edges)
    with pytest.raises(ValueError, match="dynamic range"):
        astra.weighted_laplacian(4, reversed(edges))


def test_reservoir_laplacian_is_permutation_invariant_when_resolvable() -> None:
    conductances = [0.1, 0.2, 0.3]
    edges = [astra.Edge(0, index + 1, value) for index, value in enumerate(conductances)]
    forward = astra.weighted_laplacian(4, edges)
    reverse = astra.weighted_laplacian(4, reversed(edges))
    assert forward[0, 0] == math.fsum(conductances)
    np.testing.assert_array_equal(forward, reverse)


def test_reservoir_parallel_edges_match_their_resolvable_aggregate() -> None:
    parallel = astra.weighted_laplacian(
        2, [astra.Edge(0, 1, 1.0), astra.Edge(0, 1, 0.001)]
    )
    aggregate = astra.weighted_laplacian(2, [astra.Edge(0, 1, 1.001)])
    np.testing.assert_array_equal(parallel, aggregate)


def test_reservoir_laplacian_rejects_material_weak_edge_distortion() -> None:
    edges = [astra.Edge(0, 1, float(2**53)), astra.Edge(0, 2, 1.5)]
    with pytest.raises(ValueError, match="dynamic range"):
        astra.weighted_laplacian(3, edges)


def test_large_common_physical_scale_does_not_overflow_operator_or_steady_state() -> None:
    values = [1.0e308, 1.0e308]
    edge = [astra.Edge(0, 1, 1.0e308)]
    _, _, _, matrix = astra.system_matrices(values, edge, values)
    equilibrium = astra.steady_state(values, edge, values, values)
    np.testing.assert_allclose(matrix, [[-2.0, 1.0], [1.0, -2.0]])
    assert equilibrium == pytest.approx([1.0, 1.0])


def test_row_scaled_steady_state_preserves_smaller_independent_component() -> None:
    equilibrium = astra.steady_state(
        [1.0, 1.0], [], [1.0e308, 1.0], [0.0, 1.0e-100]
    )
    np.testing.assert_allclose(equilibrium, [0.0, 1.0e-100], rtol=0.0, atol=0.0)


def test_steady_state_fails_closed_when_sink_is_rounded_out_of_operator() -> None:
    tiny_sink = 1.111e-16
    with pytest.raises(ValueError, match="numerically unresolved"):
        astra.steady_state(
            [1.0, 1.0],
            [astra.Edge(0, 1, 1.0)],
            [0.0, tiny_sink],
            [0.0, tiny_sink],
        )


def test_steady_state_rejects_operator_entries_erased_by_row_scaling() -> None:
    loss = np.array([[1.0e308, 1.0e-100], [1.0e-100, 1.0]])
    with pytest.raises(ValueError, match="erased a nonzero operator"):
        astra.steady_state([1.0, 1.0], [], loss, [1.0e208, 1.0e308])


def test_steady_state_rejects_coarsely_rounded_operator_scaling() -> None:
    large = 1.0e308
    small = 7.0e-16
    loss = np.array([[large, small], [small, 1.0]])
    with pytest.raises(ValueError, match="cannot retain loss operator"):
        astra.steady_state([1.0, 1.0], [], loss, [small * large, large])


def test_steady_state_rejects_coarsely_rounded_power_scaling() -> None:
    with pytest.raises(ValueError, match="cannot retain power"):
        astra.steady_state([1.0], [], [1.0e308], [7.0e-16])


def test_symmetric_loss_near_float_max_does_not_overflow() -> None:
    _, _, loss, operator = astra.system_matrices([1.0e308], [], [[1.0e308]])
    np.testing.assert_allclose(loss, [[1.0e308]])
    np.testing.assert_allclose(operator, [[-1.0]])


def test_step_response_preserves_initial_state_without_equilibrium_cancellation() -> None:
    response = astra.step_response([1.0], [], [1.0], [1.0e20], [0.0], initial=[1.0])
    np.testing.assert_allclose(response, [[1.0]])


def test_step_response_preserves_time_integrated_subnormal_forcing_rate() -> None:
    response = astra.step_response([1.0e308], [], [1.0], [1.0e-100], [1.0e308])
    assert response[0, 0] == pytest.approx(6.321205588285577e-101, rel=2.0e-15)


def test_step_response_rejects_unresolved_stiff_exponential() -> None:
    with pytest.raises(ValueError, match="propagation"):
        astra.step_response([1.0], [], [1.0e308], [1.0e308], [1.0])


def test_step_response_rejects_negative_elapsed_times() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        astra.step_response([1.0], [], [1.0], [1.0], [-1.0])


def test_tiny_negative_loss_matrix_is_not_accepted_as_roundoff() -> None:
    with pytest.raises(ValueError, match="positive semidefinite"):
        astra.system_matrices([1.0], [], [[-5.0e-13]])


def test_negative_loss_block_is_not_hidden_by_unrelated_large_scale() -> None:
    with pytest.raises(ValueError, match="positive semidefinite"):
        astra.system_matrices([1.0, 1.0], [], [[1.0e16, 0.0], [0.0, -1.0]])


def test_frequency_response_has_expected_static_gain() -> None:
    response = astra.frequency_response(
        [20.0, 1.0], EDGES, [0.0, 1.0], [1.0, 0.0], [0.0, 1.0], [0.0]
    )
    assert response[0] == pytest.approx(1.0 + 0.0j)


@pytest.mark.parametrize("frequency", [0.0, 1.0e-20])
def test_frequency_response_fails_closed_on_rounded_sink(frequency: float) -> None:
    with pytest.raises(ValueError, match="cannot retain|numerically unresolved|singular"):
        astra.frequency_response(
            [1.0, 1.0],
            [astra.Edge(0, 1, 1.0)],
            [0.0, 1.2e-16],
            [1.0, 0.0],
            [1.0, 0.0],
            [frequency],
        )


def test_frequency_response_falls_back_when_dynamic_term_overflows() -> None:
    response = astra.frequency_response(
        [1.0e200], [], [1.0], [1.0e308], [1.0], [1.0e200]
    )
    assert response[0] == pytest.approx(-1.0e-92j, rel=2.0e-15, abs=0.0)


def test_frequency_response_falls_back_when_dynamic_term_underflows() -> None:
    response = astra.frequency_response(
        [1.0e-200], [], [0.0], [5.0e-324], [1.0], [1.0e-124]
    )
    expected = -1j * (5.0e-324 / 1.0e-200) / 1.0e-124
    assert response[0] == pytest.approx(expected, rel=2.0e-15, abs=0.0)


def test_two_reservoir_poles_avoid_root_sum_overflow() -> None:
    poles = astra.two_reservoir_poles(1.0, 1.0e308, 4.0e307, 5.0e307)
    assert poles[0] == pytest.approx(-2.0 / 9.0, rel=2.0e-15)
    assert poles[1] == pytest.approx(-9.0e307, rel=2.0e-15)


def test_two_reservoir_poles_preserve_representable_ratio_after_underflowing_order() -> None:
    poles = astra.two_reservoir_poles(1.0, 1.0e200, 1.0, 1.0e124)
    assert poles[0] == pytest.approx(-1.0e-200, rel=2.0e-15, abs=0.0)
    assert poles[1] == pytest.approx(-1.0e124, rel=2.0e-15)


def test_two_reservoir_poles_allow_negligible_surface_coupling_rate_underflow() -> None:
    poles = astra.two_reservoir_poles(1.0e200, 1.0, 1.0e-200, 1.0e200)
    assert poles[0] == pytest.approx(-1.0e-200, rel=2.0e-15, abs=0.0)
    assert poles[1] == pytest.approx(-1.0, rel=2.0e-15)


def test_two_reservoir_poles_normalize_subnormal_rates_before_root_calculation() -> None:
    poles = astra.two_reservoir_poles(4.0, 1.0, 5.0e-324, 2.0e-323)
    assert poles[0] == -5.0e-324
    assert poles[1] == -1.0e-323


def test_relaxation_spectrum_is_positive() -> None:
    rates, times = astra.relaxation_spectrum([20.0, 1.0], EDGES, [0.0, 1.0])
    assert rates == pytest.approx([0.0083216947, 1.2016783053])
    assert times == pytest.approx(1.0 / rates)


def test_relaxation_spectrum_scales_transport_and_loss_before_summing() -> None:
    maximum = np.finfo(float).max
    rates, times = astra.relaxation_spectrum(
        [maximum, maximum], [astra.Edge(0, 1, maximum)], [maximum, maximum]
    )
    assert rates == pytest.approx([1.0, 3.0], rel=2.0e-15)
    assert times == pytest.approx([1.0, 1.0 / 3.0], rel=2.0e-15)


def test_relaxation_spectrum_rejects_unrepresentable_reciprocal_time() -> None:
    with pytest.raises(ValueError, match="finite numerical range"):
        astra.relaxation_spectrum([1.0e308], [], [0.5])


def test_fisher_information_is_symmetric_psd() -> None:
    jacobian = np.array([[1.0, 0.0], [1.0, 2.0], [0.0, 1.0]])
    information = astra.fisher_information(jacobian, np.diag([1.0, 2.0, 3.0]))
    assert np.allclose(information, information.T)
    assert np.min(np.linalg.eigvalsh(information)) >= -1.0e-12


def test_fisher_information_handles_covariance_near_float_max() -> None:
    information = astra.fisher_information([[1.0]], [[1.0e308]])
    np.testing.assert_allclose(information, [[1.0e-308]], rtol=2.0e-15, atol=0.0)


@pytest.mark.parametrize(
    "covariance",
    [np.array([[1.0, 2.0], [0.0, 1.0]]), np.array([[1.0, 0.0], [0.0, 0.0]])],
)
def test_fisher_information_rejects_invalid_covariance(covariance: np.ndarray) -> None:
    with pytest.raises(ValueError, match="covariance"):
        astra.fisher_information(np.eye(2), covariance)


def test_fisher_information_rejects_scale_relative_covariance_skew() -> None:
    covariance = np.array([[1.0e-12, 5.0e-13], [0.0, 1.0e-12]])
    with pytest.raises(ValueError, match="symmetric"):
        astra.fisher_information(np.eye(2), covariance)


def test_covariance_skew_is_not_hidden_by_unrelated_large_scale() -> None:
    covariance = np.array(
        [[1.0e16, 0.0, 0.0], [0.0, 1.0, 1.0], [0.0, 0.0, 1.0]]
    )
    with pytest.raises(ValueError, match="symmetric"):
        astra.fisher_information(np.eye(3), covariance)


@pytest.mark.parametrize(
    "operation",
    [
        lambda: astra.Edge(0, 1, np.nan),
        lambda: astra.system_matrices([1.0, np.nan], [], [1.0, 1.0]),
        lambda: astra.steady_state([1.0], [], [1.0], [np.nan]),
        lambda: astra.step_response([1.0], [], [1.0], [1.0], [np.nan]),
        lambda: astra.frequency_response([1.0], [], [1.0], [1.0], [1.0], [np.nan]),
    ],
)
def test_public_reservoir_apis_reject_nonfinite_inputs(operation) -> None:
    with pytest.raises(ValueError, match="finite"):
        operation()
