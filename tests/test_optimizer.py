from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

import astra_optimization as optimization


def test_multistart_design_is_frozen_and_spans_log_box() -> None:
    first = optimization.deterministic_log_starts(3)
    second = optimization.deterministic_log_starts(3)
    assert first.shape == (optimization.N_STARTS, 3)
    assert np.array_equal(first, second)
    assert np.all(np.ptp(first, axis=0) > 8.0)


def test_multistart_solves_simple_problem() -> None:
    result, _, diagnostics = optimization.solve_multistart(
        lambda value: value - np.array([-2.0, 1.0]),
        2,
        xtol=1e-12,
        ftol=1e-12,
        gtol=1e-12,
        max_nfev=200,
    )
    assert result.x == pytest.approx([-2.0, 1.0])
    assert any(item.accepted for item in diagnostics)


def test_success_flag_without_adequate_optimality_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = SimpleNamespace(
        success=True,
        status=2,
        x=np.array([0.0]),
        cost=0.0,
        optimality=1.0,
        nfev=1,
        active_mask=np.array([0]),
    )
    monkeypatch.setattr(optimization, "least_squares", lambda *args, **kwargs: fake)
    with pytest.raises(RuntimeError, match="No multistart fit"):
        optimization.solve_multistart(
            lambda value: value,
            1,
            xtol=1e-12,
            ftol=1e-12,
            gtol=1e-12,
            max_nfev=10,
        )
