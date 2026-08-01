from __future__ import annotations

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


def test_frequency_response_has_expected_static_gain() -> None:
    response = astra.frequency_response(
        [20.0, 1.0], EDGES, [0.0, 1.0], [1.0, 0.0], [0.0, 1.0], [0.0]
    )
    assert response[0] == pytest.approx(1.0 + 0.0j)


def test_relaxation_spectrum_is_positive() -> None:
    rates, times = astra.relaxation_spectrum([20.0, 1.0], EDGES, [0.0, 1.0])
    assert rates == pytest.approx([0.0083216947, 1.2016783053])
    assert times == pytest.approx(1.0 / rates)


def test_fisher_information_is_symmetric_psd() -> None:
    jacobian = np.array([[1.0, 0.0], [1.0, 2.0], [0.0, 1.0]])
    information = astra.fisher_information(jacobian, np.diag([1.0, 2.0, 3.0]))
    assert np.allclose(information, information.T)
    assert np.min(np.linalg.eigvalsh(information)) >= -1.0e-12


@pytest.mark.parametrize(
    "covariance",
    [np.array([[1.0, 2.0], [0.0, 1.0]]), np.array([[1.0, 0.0], [0.0, 0.0]])],
)
def test_fisher_information_rejects_invalid_covariance(covariance: np.ndarray) -> None:
    with pytest.raises(ValueError, match="covariance"):
        astra.fisher_information(np.eye(2), covariance)
