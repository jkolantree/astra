"""Independent controls for the migration's numerical diagnosis, not a new baseline."""

from __future__ import annotations

import numpy as np
import pytest

from scripts import synthetic_topology_benchmark as model
from tools.diagnose_linux_portability import compare, oracle, segmented


def test_segmented_reference_integrates_a_known_step_exactly() -> None:
    time = np.array([0.0, 9.9999, 10.0, 10.0001, 12.0])
    solution = segmented(lambda t, y: np.array([float(t > 10.0)]), (0.0, 12.0), [0.0], t_eval=time)
    assert solution.y[0] == pytest.approx(np.maximum(time - 10.0, 0.0), abs=1e-12)


@pytest.mark.parametrize(
    "protocol,end,forcing",
    [
        ("train", 36.0, model.train_forcing),
        ("heldout", 26.0, model.heldout_forcing),
    ],
)
def test_independent_references_agree_across_all_declared_discontinuities(
    protocol: str, end: float, forcing, monkeypatch: pytest.MonkeyPatch
) -> None:
    time = np.linspace(0, end, int(end * 10) + 1)
    edges = model.GRAPHS["chain"]
    conductance = np.array([0.22, 1.4])
    exact = oracle(model, edges, conductance, time, protocol)
    monkeypatch.setattr(model, "solve_ivp", segmented)
    state = model.simulate(edges, conductance, time, forcing)
    augmented, _ = model.simulate_with_log_conductance_sensitivities(
        edges, conductance, time, forcing
    )
    np.testing.assert_allclose(state, exact, rtol=0, atol=1e-10)
    np.testing.assert_allclose(augmented, exact, rtol=0, atol=1e-10)


def test_reference_rejects_an_undeclared_forcing_protocol() -> None:
    with pytest.raises(ValueError, match="Unknown forcing"):
        oracle(model, [], [], [], "unregistered")


def test_diagnosis_preserves_discrete_and_strict_numeric_failures() -> None:
    result = compare({"winner": "chain", "score": 1.0}, {"winner": "triangle", "score": 1.000001})
    assert result["/winner"]["discrete_changes"] == 1
    assert result["/score"]["strict_failures"] == 1
    assert result["/score"]["max_strict_tolerance_multiple"] > 900000
