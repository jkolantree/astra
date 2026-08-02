from __future__ import annotations

from fractions import Fraction

import numpy as np
import pytest

from astra_reservoir import Edge, frequency_response, system_matrices
from scripts import benchmark_ensemble as ensemble
from scripts import generate_astra_figures as figures
from scripts import synthetic_topology_benchmark as single

ConductanceTriple = tuple[Fraction, Fraction, Fraction]


def _surface_transfer_coefficients(
    conductance: ConductanceTriple,
) -> tuple[tuple[Fraction, ...], tuple[Fraction, ...]]:
    """Exact surface-port polynomials for C=(8, 3, 1) and lambda=6/5.

    Conductances are ordered as (k01, k12, k02), regardless of a benchmark
    family's array order. Coefficients are returned in descending powers of s.
    """
    k01, k12, k02 = conductance
    alpha = 11 * k01 + 8 * k12 + 3 * k02
    tau = k01 * k12 + k01 * k02 + k12 * k02
    surface_degree = k12 + k02
    numerator = (Fraction(24), alpha, tau)
    denominator = (
        Fraction(24),
        alpha + 24 * (surface_degree + Fraction(6, 5)),
        12 * tau + Fraction(6, 5) * alpha,
        Fraction(6, 5) * tau,
    )
    return numerator, denominator


def _positive_edges(conductance: ConductanceTriple) -> list[Edge]:
    k01, k12, k02 = conductance
    candidates = ((0, 1, k01), (1, 2, k12), (0, 2, k02))
    return [Edge(i, j, float(value)) for i, j, value in candidates if value > 0]


def _surface_frequency_response(conductance: ConductanceTriple) -> np.ndarray:
    omega = np.concatenate(([0.0], np.geomspace(1.0e-8, 1.0e8, 65)))
    return frequency_response(
        single.CAPACITY,
        _positive_edges(conductance),
        [0.0, 0.0, single.SURFACE_SINK],
        [0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0],
        omega,
    )


def _surface_realization_ranks(conductance: ConductanceTriple) -> tuple[int, int]:
    capacity, _, _, state_matrix = system_matrices(
        single.CAPACITY,
        _positive_edges(conductance),
        [0.0, 0.0, single.SURFACE_SINK],
    )
    input_state = np.linalg.solve(capacity, np.array([0.0, 0.0, 1.0]))
    output_state = np.array([0.0, 0.0, 1.0])
    controllability = np.column_stack(
        (input_state, state_matrix @ input_state, state_matrix @ state_matrix @ input_state)
    )
    observability = np.vstack(
        (output_state, output_state @ state_matrix, output_state @ state_matrix @ state_matrix)
    )
    return int(np.linalg.matrix_rank(controllability)), int(np.linalg.matrix_rank(observability))


def test_distinct_two_edge_supports_have_the_same_exact_surface_transfer() -> None:
    surface_star = (Fraction(0), Fraction(6), Fraction(5))
    deep_star = (Fraction(30, 11), Fraction(0), Fraction(11))

    expected = (
        (Fraction(24), Fraction(63), Fraction(30)),
        (Fraction(24), Fraction(1779, 5), Fraction(2178, 5), Fraction(36)),
    )
    assert _surface_transfer_coefficients(surface_star) == expected
    assert _surface_transfer_coefficients(deep_star) == expected
    assert _surface_realization_ranks(surface_star) == (3, 3)
    assert _surface_realization_ranks(deep_star) == (3, 3)
    np.testing.assert_allclose(
        _surface_frequency_response(surface_star),
        _surface_frequency_response(deep_star),
        rtol=2.0e-13,
        atol=2.0e-14,
    )


@pytest.mark.parametrize(
    ("time", "forcing"),
    [
        (np.linspace(0.0, 36.0, 361), ensemble.train_forcing),
        (np.linspace(0.0, 26.0, 261), ensemble.heldout_forcing),
    ],
)
def test_benchmark_surface_protocol_cannot_break_exact_support_equivalence(
    time: np.ndarray,
    forcing,
) -> None:
    surface_star = ensemble.simulate(
        ensemble.GRAPHS["surface_star"], np.array([5.0, 6.0]), time, forcing
    )
    deep_star = ensemble.simulate(
        ensemble.GRAPHS["deep_star"], np.array([30.0 / 11.0, 11.0]), time, forcing
    )

    assert not np.allclose(surface_star[:2], deep_star[:2], rtol=1.0e-8, atol=1.0e-10)
    np.testing.assert_allclose(surface_star[2], deep_star[2], rtol=5.0e-13, atol=5.0e-14)


def test_distinct_locally_full_rank_triangles_share_the_surface_transfer() -> None:
    first = (Fraction(1), Fraction(1), Fraction(1))
    second = (Fraction(171, 121), Fraction(1, 11), Fraction(21, 11))

    assert first != second
    assert all(value > 0 for value in second)
    assert 2 * (8 * first[1] - 3 * first[2]) == 10
    assert 2 * (8 * second[1] - 3 * second[2]) == -10
    assert _surface_transfer_coefficients(first) == _surface_transfer_coefficients(second)
    np.testing.assert_allclose(
        _surface_frequency_response(first),
        _surface_frequency_response(second),
        rtol=2.0e-13,
        atol=2.0e-14,
    )


def test_balanced_hidden_mode_and_edge_are_invisible_at_the_surface() -> None:
    surface_star = (Fraction(0), Fraction(3), Fraction(8))
    triangle = (Fraction(1), Fraction(3), Fraction(8))
    hidden_mode = np.array([3.0, -8.0, 0.0])

    for conductance in (surface_star, triangle):
        capacity, laplacian, loss, _ = system_matrices(
            single.CAPACITY,
            _positive_edges(conductance),
            [0.0, 0.0, single.SURFACE_SINK],
        )
        rate = (11.0 * float(conductance[0]) + 24.0) / 24.0
        np.testing.assert_allclose(
            (laplacian + loss) @ hidden_mode,
            rate * capacity @ hidden_mode,
            rtol=2.0e-15,
            atol=2.0e-15,
        )
        assert hidden_mode[2] == 0.0

    np.testing.assert_allclose(
        _surface_frequency_response(surface_star),
        _surface_frequency_response(triangle),
        rtol=2.0e-13,
        atol=2.0e-14,
    )


def test_released_chain_algebraic_dual_leaves_the_positive_domain() -> None:
    assert single.TRUE_GRAPH == "chain"
    k01, k12 = (Fraction(str(float(value))) for value in single.TRUE_CONDUCTANCE)
    k02 = Fraction(0)
    surface_degree = k12 + k02
    dual_k12 = Fraction(6, 11) * surface_degree - k12

    assert (k01, k12, k02) == (Fraction(11, 50), Fraction(7, 5), Fraction(0))
    assert _surface_realization_ranks((k01, k12, k02)) == (3, 3)
    assert dual_k12 == Fraction(-7, 11)


def test_high_accuracy_forward_sensitivities_match_centered_difference() -> None:
    time = np.linspace(0.0, 1.0, 21)
    conductance = np.array([0.22, 1.40])
    _, sensitivity = single.simulate_with_log_conductance_sensitivities(
        single.GRAPHS["chain"], conductance, time, single.train_forcing
    )
    epsilon = 1.0e-5
    plus = single.simulate(
        single.GRAPHS["chain"], conductance * np.exp([epsilon, 0.0]), time, single.train_forcing
    )
    minus = single.simulate(
        single.GRAPHS["chain"], conductance * np.exp([-epsilon, 0.0]), time, single.train_forcing
    )
    assert sensitivity[:, 0, :] == pytest.approx((plus - minus) / (2.0 * epsilon), abs=2.0e-9)


def test_zoh_forward_sensitivities_match_centered_difference() -> None:
    time = np.linspace(0.0, 1.0, 11)
    conductance = np.array([0.22, 1.40])
    _, sensitivity = ensemble.simulate_with_log_conductance_sensitivities(
        ensemble.GRAPHS["chain"], conductance, time, ensemble.train_forcing
    )
    epsilon = 1.0e-5
    plus = ensemble.simulate(
        ensemble.GRAPHS["chain"], conductance * np.exp([epsilon, 0.0]), time, ensemble.train_forcing
    )
    minus = ensemble.simulate(
        ensemble.GRAPHS["chain"], conductance * np.exp([-epsilon, 0.0]), time, ensemble.train_forcing
    )
    assert sensitivity[:, 0, :] == pytest.approx((plus - minus) / (2.0 * epsilon), abs=2.0e-9)


def test_static_degeneracy_figure_forces_the_deep_reservoir() -> None:
    equilibrium = figures.static_degeneracy_equilibrium(0.2)
    assert equilibrium == pytest.approx([1.0, 6.0])


@pytest.mark.parametrize(
    "simulate",
    [single.simulate, single.simulate_with_log_conductance_sensitivities],
)
@pytest.mark.parametrize("time", [np.array([0.0]), np.array([0.0, 0.0])])
def test_high_accuracy_simulation_rejects_zero_span_time_grids(simulate, time: np.ndarray) -> None:
    with pytest.raises(ValueError, match="strictly monotonic"):
        simulate(single.GRAPHS["chain"], single.TRUE_CONDUCTANCE, time, single.train_forcing)


@pytest.mark.parametrize(
    "simulate",
    [ensemble.simulate, ensemble.simulate_with_log_conductance_sensitivities],
)
@pytest.mark.parametrize(
    "time",
    [
        np.array([0.0, 0.0]),
        np.array([0.0, 1.0, 1.0]),
        np.array([0.0, np.nan]),
    ],
)
def test_fast_simulation_rejects_nonfinite_or_repeated_time_grids(
    simulate, time: np.ndarray
) -> None:
    with pytest.raises(ValueError, match="finite|strictly monotonic"):
        simulate(
            ensemble.GRAPHS["chain"],
            ensemble.TRUE_CONDUCTANCE,
            time,
            ensemble.train_forcing,
        )


def test_graph_fit_rejects_broadcastable_observation_shape() -> None:
    with pytest.raises(ValueError, match="observed_surface"):
        single.fit_graph("chain", np.linspace(0.0, 1.0, 11), np.array([0.8]))


@pytest.mark.parametrize(
    ("time", "forcing", "maximum_limit", "rmse_limit"),
    [
        (np.linspace(0.0, 36.0, 361), single.train_forcing, 1.0e-5, 7.0e-6),
        (np.linspace(0.0, 26.0, 261), single.heldout_forcing, 1.7e-5, 1.0e-5),
    ],
)
def test_fast_propagator_agrees_with_high_accuracy_solver(
    time: np.ndarray,
    forcing,
    maximum_limit: float,
    rmse_limit: float,
) -> None:
    accurate = single.simulate(single.GRAPHS["chain"], single.TRUE_CONDUCTANCE, time, forcing)[2]
    fast = ensemble.simulate(ensemble.GRAPHS["chain"], ensemble.TRUE_CONDUCTANCE, time, forcing)[2]
    error = fast - accurate
    assert np.max(np.abs(error)) < maximum_limit
    assert np.sqrt(np.mean(error**2)) < rmse_limit
