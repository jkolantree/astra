"""Independent scientific, leakage and identity checks for the separate Draft."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "resources/dark-medium-response-benchmark/draft-v0.1.0"
SPEC = importlib.util.spec_from_file_location(
    "dark_medium_response_benchmark", PACKAGE / "benchmark.py"
)
assert SPEC is not None and SPEC.loader is not None
benchmark = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(benchmark)


def configuration() -> dict:
    return benchmark.read_config()


def test_generic_unequal_mass_algebra_and_declared_controls() -> None:
    result = benchmark.controls(configuration())
    assert result["exact_rational_algebra_cases"] == 15
    assert result["noise_free_full_response_unique_recoveries"] == 6
    assert result["minimum_undamped_squared_frequency"] > 0.4
    assert result["known_unit_drive_calibrated_gain"] == pytest.approx(2)
    assert all(
        len(group) == 2 for group in result["mass_only_exact_observational_classes"].values()
    )


@pytest.mark.parametrize("k", [0.7, 1.0, 1.9])
@pytest.mark.parametrize("w", [0.1, 0.8, 2.2])
def test_independent_primitive_four_state_response(k: float, w: float) -> None:
    for theta in benchmark.library(configuration()):
        primitive = benchmark.response(theta, k, w, "species")
        modal = benchmark.response(theta, k, w, "response")
        assert primitive == pytest.approx(modal, rel=1e-11, abs=1e-11)


def test_independent_equal_pair_limits_and_symmetry_breaking() -> None:
    theta = dict(c=1.0, j=0.2, p=1.6, d=0.0, gamma=0.15)
    k, w = 1.2, 0.65
    response = benchmark.response(theta, k, w, "species")
    assert response[0] == pytest.approx(1 / (k * k - 0.2 - w * w - 0.15j * w))
    assert response[3] == pytest.approx(1 / (k * k + 1.6 - w * w - 0.15j * w))
    assert response[1:3] == pytest.approx([0, 0], abs=1e-12)
    theta["d"] = 0.2
    assert abs(benchmark.response(theta, k, w, "species")[1]) > 0.01


def test_fixed_noise_does_not_resolve_exact_projected_classes() -> None:
    config = configuration()
    truths = benchmark.library(config)
    design = config["sampling"]["training"]
    candidates = [benchmark.observe(t, design, "mass_only", "response") for t in truths]
    for index in range(len(truths)):
        # Development-only seed; evaluation generator/run is not invoked here.
        data = benchmark.noisy(
            candidates[index], 0.04, config["sampling"]["development_seed"] + index
        )
        matches = benchmark.fit(data, candidates, 0.04, 1e-9)
        assert len(matches) >= 2
        values = [truths[item] for item in matches]
        if values[0]["d"] == 0:
            assert {value["p"] for value in values} == {0.8, 1.6}
        else:
            assert {value["d"] for value in values} == {-0.2, 0.2}


def test_holdout_cannot_enter_fit_and_split_seeds_are_distinct() -> None:
    config = configuration()
    sampling = config["sampling"]
    seed_arguments = (sampling["evaluation_seed"], 0, "p0-d0", "mass_only")
    assert benchmark.derived_seed(*seed_arguments, "training") != benchmark.derived_seed(
        *seed_arguments, "held_out"
    )
    candidates = [[1 + 1j, 2 + 0j], [3 + 1j, 4 + 0j]]
    training = [1 + 1j, 2 + 0j]
    before = benchmark.fit(training, candidates, 0.04, 1e-9)
    benchmark.score([1000j, -2000j], candidates[before[0]], 0.04)
    assert benchmark.fit(training, candidates, 0.04, 1e-9) == before == [0]
    for dimension in ("wave_numbers", "frequencies"):
        assert set(sampling["training"][dimension]).isdisjoint(sampling["held_out"][dimension])


def test_score_normalization_and_uncertainty_are_independently_checkable() -> None:
    assert benchmark.score([1 + 1j], [0j], 1.0) == pytest.approx(1.0)
    assert benchmark.interval([0.0] * 64)["approximate_95_percent_interval"] == [0.0, 0.0]
    assert benchmark.wilson(64, 64)["wilson_95_percent_interval"][0] == pytest.approx(0.9433759402)
    assert benchmark.wilson(0, 64)["wilson_95_percent_interval"][1] == pytest.approx(0.05662405979)


def test_runtime_and_configuration_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(benchmark.platform, "python_version", lambda: "3.12.99")
    with pytest.raises(RuntimeError, match="Required CPython"):
        benchmark.read_config()


def test_frozen_identity_detects_configuration_mutation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config = configuration()
    record = benchmark.freeze_record(config)
    frozen = tmp_path / "frozen.json"
    frozen.write_bytes(benchmark.canonical(record))
    monkeypatch.setattr(benchmark, "FREEZE", frozen)
    benchmark.verify_freeze(config)
    changed = dict(config, candidate="unapproved-candidate")
    with pytest.raises(RuntimeError, match="Frozen evaluation input identity mismatch"):
        benchmark.verify_freeze(changed)


def test_unknown_operator_and_singular_model_are_harness_errors() -> None:
    theta = dict(c=1.0, j=1.0, p=1.0, d=0.0, gamma=0.0)
    with pytest.raises(RuntimeError, match="Singular"):
        benchmark.response(theta, 1.0, 0.0, "response")
    with pytest.raises(ValueError, match="Unknown observation"):
        benchmark.observe(theta, {"wave_numbers": [1.0], "frequencies": [0.1]}, "hidden", "species")


def test_retained_evaluation_reproduces_with_frozen_sources() -> None:
    config = configuration()
    expected = json.loads((PACKAGE / "results.json").read_text())
    produced = benchmark.run(config)
    assert benchmark.canonical(produced) == benchmark.canonical(expected)
    assert expected["comparative_utility"].startswith("UNESTABLISHED")
    for result in produced["evaluation"].values():
        assert result["same_fitted_classes"] == result["paired_trials"] == 384
        assert result["practical_criterion_met"] is False


def test_package_is_separate_and_exactly_admitted() -> None:
    from tools import check_repository

    expected = {
        "README.md",
        "evaluation.json",
        "frozen-evaluation.json",
        "benchmark.py",
        "results.json",
    }
    assert {path.name for path in PACKAGE.iterdir() if path.is_file()} == expected
    assert {
        path.relative_to(ROOT).as_posix() for path in PACKAGE.iterdir() if path.is_file()
    } <= check_repository.RESOURCE_PATH_ALLOWLIST
    text = (PACKAGE / "README.md").read_text()
    assert "Draft" in text and "unpromoted" in text
    assert "UNESTABLISHED" in text
    assert "no Pages route" in text
