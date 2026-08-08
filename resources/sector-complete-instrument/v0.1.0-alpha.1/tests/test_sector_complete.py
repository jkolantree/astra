from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
from jsonschema.validators import validator_for

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import astra_sector_complete as sci  # noqa: E402


def test_trace_of_commutator_is_zero() -> None:
    rng = np.random.default_rng(7)
    a = rng.normal(size=(5, 5)) + 1j * rng.normal(size=(5, 5))
    b = rng.normal(size=(5, 5)) + 1j * rng.normal(size=(5, 5))
    assert abs(sci.trace_commutator(a, b)) < 1e-10


@pytest.mark.parametrize("povm_factory", [sci.local_povm, sci.sector_complete_povm])
def test_povm_completeness(povm_factory) -> None:
    sci.validate_povm(povm_factory())


@pytest.mark.parametrize("generator", sci.GENERATOR_ORDER)
def test_generator_unitaries_are_unitary(generator: str) -> None:
    u = sci.generator_unitary(generator)
    assert np.allclose(u.conj().T @ u, np.eye(sci.DIM), atol=1e-12)


@pytest.mark.parametrize("generator", sci.GENERATOR_ORDER)
def test_output_states_are_valid(generator: str) -> None:
    sci.validate_density_matrix(sci.output_state(generator))


def test_local_observation_declares_absorb_string_equivalence() -> None:
    _, generators, response = sci.response_matrix(sci.local_povm())
    classes = sci.exact_equivalence_classes(response, generators)
    assert ["absorb", "string_transmit"] in classes


def test_sector_complete_observation_resolves_all_generators() -> None:
    _, generators, response = sci.response_matrix(sci.sector_complete_povm())
    classes = sci.exact_equivalence_classes(response, generators)
    assert all(len(cls) == 1 for cls in classes)


def test_local_fisher_has_null_direction() -> None:
    labels, _, response = sci.response_matrix(sci.local_povm())
    response = sci.apply_detector_confusion(
        response, sci.symmetric_confusion_matrix(len(labels), 0.02)
    )
    fisher = sci.mixture_fisher_information(response)
    values = np.linalg.eigvalsh(fisher)
    assert sci.matrix_rank_with_tolerance(fisher) == 2
    assert values.min() < 1e-8


def test_sector_complete_fisher_is_full_rank_on_simplex() -> None:
    labels, _, response = sci.response_matrix(sci.sector_complete_povm())
    response = sci.apply_detector_confusion(
        response, sci.symmetric_confusion_matrix(len(labels), 0.02)
    )
    fisher = sci.mixture_fisher_information(response)
    assert sci.matrix_rank_with_tolerance(fisher) == 3
    assert np.linalg.eigvalsh(fisher).min() > 0


def test_sector_complete_mutual_information_exceeds_local() -> None:
    l_labels, _, local = sci.response_matrix(sci.local_povm())
    c_labels, _, complete = sci.response_matrix(sci.sector_complete_povm())
    local = sci.apply_detector_confusion(local, sci.symmetric_confusion_matrix(len(l_labels), 0.05))
    complete = sci.apply_detector_confusion(complete, sci.symmetric_confusion_matrix(len(c_labels), 0.05))
    assert sci.mutual_information_uniform(complete) > sci.mutual_information_uniform(local)


@pytest.mark.parametrize("generator", sci.GENERATOR_ORDER)
def test_global_excitation_is_conserved(generator: str) -> None:
    value = sci.expectation(sci.output_state(generator), sci.global_excitation_observable())
    assert np.isclose(value, 1.0, atol=1e-12)


def test_defect_changes_only_for_string_generator() -> None:
    values = {
        g: sci.expectation(sci.output_state(g), sci.defect_observable())
        for g in sci.GENERATOR_ORDER
    }
    assert values["string_transmit"] == pytest.approx(1.0)
    assert values["reflect"] == pytest.approx(0.0)
    assert values["absorb"] == pytest.approx(0.0)
    assert values["local_transmit"] == pytest.approx(0.0)


def test_detector_confusion_is_column_stochastic() -> None:
    matrix = sci.symmetric_confusion_matrix(5, 0.08)
    assert np.all(matrix >= 0)
    assert np.allclose(matrix.sum(axis=0), 1.0)


def test_broken_duality_restores_reflection_monotonically() -> None:
    values = []
    for delta in (0.0, 0.1, 0.2, 0.4):
        labels, p = sci.measurement_probabilities(sci.broken_duality_state(delta), sci.sector_complete_povm())
        values.append(p[labels.index("left_local")])
    assert np.all(np.diff(values) > 0)


def test_finite_boundary_converges_to_string_transmission() -> None:
    labels, p_small = sci.measurement_probabilities(sci.finite_boundary_state(0.0), sci.sector_complete_povm())
    _, p_large = sci.measurement_probabilities(sci.finite_boundary_state(20.0), sci.sector_complete_povm())
    assert p_small[labels.index("environment_sector")] == pytest.approx(1.0)
    assert p_large[labels.index("string_sector")] > 0.999999


def test_model_mismatch_deviance_is_positive() -> None:
    labels, generators, response = sci.response_matrix(sci.sector_complete_povm())
    response = sci.apply_detector_confusion(response, sci.symmetric_confusion_matrix(len(labels), 0.02))
    hybrid = response @ np.array([0.1, 0.2, 0.25, 0.45])
    rng = np.random.default_rng(11)
    counts = sci.sample_counts(hybrid, 5000, rng)
    best, _ = sci.classify_pure_generator(counts, response, generators)
    deviance = sci.multinomial_deviance(counts, response[:, generators.index(best)])
    assert deviance > 100.0


def test_typed_record_keeps_dark_matter_out_of_empirical_status() -> None:
    record = sci.default_transduction_record()
    assert record.interpretation_status == "synthetic_methods_only"
    schema_path = ROOT / "schema" / "sector_complete_instrument.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator_type = validator_for(schema)
    validator_type.check_schema(schema)
    errors = sorted(validator_type(schema).iter_errors(record.to_dict()), key=str)
    assert not errors, "default typed record must satisfy its declared schema"
    assert isinstance(record.conservation_exchange_ledger, dict)
    assert isinstance(record.identifiability, dict)


def test_frozen_benchmark_file_is_methods_only() -> None:
    path = ROOT / "data" / "sector_complete_benchmark.json"
    if not path.exists():
        pytest.skip("Run benchmark before frozen-output test")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert "not evidence" in payload["status"]
    assert payload["dark_matter_interpretation_status"] == "proposed_only"


def test_model_mismatch_preserves_selection_caveat() -> None:
    path = ROOT / "data" / "sector_complete_benchmark.json"
    if not path.exists():
        pytest.skip("Run benchmark before frozen-output test")
    payload = json.loads(path.read_text(encoding="utf-8"))
    control = payload["model_mismatch_control"]
    assert "best-of-four" in control["selection_note"]
    assert control["selection_adjusted_pvalue_upper_bound"] < 0.001


def test_generated_text_outputs_are_utf8_lf() -> None:
    for path in (ROOT / "data").glob("*.json"):
        raw = path.read_bytes()
        assert b"\r" not in raw, path.name
    for path in (ROOT / "data").glob("*.csv"):
        raw = path.read_bytes()
        assert b"\r" not in raw, path.name
