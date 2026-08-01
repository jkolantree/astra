from __future__ import annotations

import numpy as np
import pytest

from scripts import benchmark_ensemble as ensemble
from scripts import synthetic_topology_benchmark as single


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
