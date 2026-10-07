"""Candidate-specific integration invariants and fail-closed scope controls."""

import dataclasses
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

import astra_reservoir
import boundary_state
import research_candidate
from core_contracts import (
    CalibrationDeclaration,
    Quantity,
    QuantityType,
    StageContract,
    compose,
    exclusion_from_null,
    finite_reduction_diagnostics,
    first_order_rank,
    observation_likelihood,
    observe_mass,
)
from integrated_case import build_contracts, run_case

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    return json.loads((ROOT / "data/integrated-core/integrated_case.json").read_text())


class IntegratedCaseTests(unittest.TestCase):
    def test_closed_two_reservoir_analytic_solution(self):
        case = fixture()
        result = run_case(case)
        times = np.array(case["times_s"])
        # Independent closed-form two-compartment solution, not the implementation's expm.
        difference = (case["initial_mass_kg"][0] - case["initial_mass_kg"][1]) * np.exp(
            -2 * case["conductance_per_s"] * times
        )
        total = sum(case["initial_mass_kg"])
        expected = np.column_stack(((total + difference) / 2, (total - difference) / 2))
        np.testing.assert_allclose(result["transport"]["mass_kg"], expected, rtol=1e-13, atol=1e-13)
        np.testing.assert_allclose(
            np.sum(result["transport"]["mass_kg"], axis=1), total, atol=1e-13
        )
        self.assertAlmostEqual(result["transport"]["mass_closure_residual_kg"], 0, places=13)
        self.assertEqual(result["transport"]["inventory_tendency_kg_s"], [0.0] * len(times))

    def test_capture_reallocates_existing_mass(self):
        case = fixture()
        result = run_case(case)
        sample = result["transport"]["mass_kg"][-1][1]
        self.assertAlmostEqual(
            result["capture"]["captured_after"], sample * case["capture_fraction"]
        )
        self.assertAlmostEqual(
            result["capture"]["external_after"] + result["capture"]["captured_after"], sample
        )

    def test_record_reset_matches_independent_weighted_sum(self):
        case = fixture()
        result = run_case(case)
        counts = [x["expected_counts"][0] for x in result["observations"]]
        k = case["reset_after_intervals"]
        r = case["archive_retention"]
        self.assertAlmostEqual(
            result["archive"]["stock"], sum(counts[:k]) * r + sum(counts[k:]), places=11
        )
        self.assertAlmostEqual(result["archive"]["erased"], sum(counts[:k]) * (1 - r), places=11)
        self.assertIsNone(result["archive"]["physical_mass_kg"])

    def test_observation_change_cannot_change_physical_mass(self):
        case = fixture()
        a = run_case(case)
        case["efficiency"] = 0.1
        b = run_case(case)
        self.assertEqual(a["transport"], b["transport"])
        self.assertEqual(a["capture"], b["capture"])
        self.assertNotEqual(a["observations"], b["observations"])

    def test_zero_and_unknown_response_are_distinct(self):
        case = fixture()
        case["efficiency"] = 0
        zero = run_case(case)
        case["efficiency"] = None
        unknown = run_case(case)
        self.assertEqual(zero["status"], "COMPLETED_SYNTHETIC")
        self.assertEqual(zero["archive"]["stock"], 0)
        self.assertEqual(unknown["status"], "INCOMPLETE_OBSERVATION")
        self.assertIsNone(unknown["archive"]["stock"])
        for row in zero["observations"]:
            self.assertEqual(row["expected_counts"], [0.0])
            self.assertIsNone(row["normalized_count_response"])
            self.assertIsNone(row["no_record_probability"])
        self.assertTrue(all(row["expected_counts"] is None for row in unknown["observations"]))

    def test_zero_capture_is_valid_empty_observation(self):
        case = fixture()
        case["capture_fraction"] = 0.0
        result = run_case(case)
        self.assertEqual(result["capture"]["captured_after"], 0)
        self.assertEqual(result["archive"]["stock"], 0)

    def test_context_memory_changes_observation_and_keeps_mass_fixed(self):
        case = fixture()
        a = run_case(case)
        case["channel"]["memory_gain"] = 0
        case["channel"]["interaction_gain"] = 0
        b = run_case(case)
        self.assertEqual(a["transport"], b["transport"])
        self.assertNotEqual(a["observations"], b["observations"])

    def test_boundary_exact_matches_independent_numerical_path(self):
        case = fixture()
        result = run_case(case)
        p = boundary_state.LinearBoundaryParameters(**case["boundary"])
        drive = result["capture"]["captured_after"] / case["reference_mass_kg"]
        numeric = boundary_state.simulate_dynamic_boundary(case["times_s"], lambda t: drive, p)
        np.testing.assert_allclose(result["boundary_context"], numeric, rtol=1e-7, atol=1e-9)

    def test_corrupt_conservation_path_fails(self):
        import sppt_core

        original = sppt_core.species_tendency

        def wrong(*args, **kwargs):
            return original(*args, **kwargs) + 0.1

        with (
            patch.object(sppt_core, "species_tendency", side_effect=wrong),
            self.assertRaises(ValueError),
        ):
            run_case(fixture())

    def test_corrupt_archive_path_fails(self):
        import astra_layers

        original = astra_layers.archive_state
        with (
            patch.object(
                astra_layers, "archive_state", side_effect=lambda *a, **k: original(*a, **k) + 1
            ),
            self.assertRaises(ValueError),
        ):
            run_case(fixture())

    def test_wrong_detector_output_type_is_not_silently_relabelled(self):
        import integrated_case

        original = integrated_case.observe_mass
        for field, value in [
            ("unit", "kg"),
            ("quantity", "energy"),
            ("basis", ["different"]),
            ("space", "other"),
        ]:

            def wrong(*a, field=field, value=value, **k):
                result = original(*a, **k)
                result["output_type"][field] = value
                return result

            with (
                self.subTest(field=field),
                patch.object(integrated_case, "observe_mass", side_effect=wrong),
                self.assertRaises(ValueError),
            ):
                run_case(fixture())

    def test_wrong_channel_context_type_is_rejected(self):
        import integrated_case

        contracts = build_contracts()
        contracts[1] = dataclasses.replace(
            contracts[1], output_type=dataclasses.replace(contracts[1].output_type, unit="kg")
        )
        with (
            patch.object(integrated_case, "build_contracts", return_value=contracts),
            self.assertRaises(ValueError),
        ):
            run_case(fixture())

    def test_nonfinite_or_negative_parameters_fail(self):
        for key, value in [
            ("conductance_per_s", -1),
            ("reference_mass_kg", 0),
            ("efficiency", True),
            ("archive_retention", float("nan")),
            ("detector_count_per_kg", float("inf")),
        ]:
            case = fixture()
            case[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                run_case(case)
        case = fixture()
        case["channel"]["drive"] = float("inf")
        with self.assertRaises(ValueError):
            run_case(case)

    def test_bad_time_or_reset_policy_fails(self):
        for times in [[0, 1, 1], [0, 0.5, 2], [1, 2, 3]]:
            case = fixture()
            case["times_s"] = times
            with self.subTest(times=times), self.assertRaises(ValueError):
                run_case(case)
        for reset in [0, True, 1.5, 99]:
            case = fixture()
            case["reset_after_intervals"] = reset
            with self.subTest(reset=reset), self.assertRaises(ValueError):
                run_case(case)

    def test_synthetic_case_does_not_confer_release_or_empirical_status(self):
        result = run_case(fixture())
        self.assertFalse(result["empirical_admission"])
        self.assertFalse(result["core_release_promoted"])
        self.assertFalse(result["calibration"]["calibration_ready"])
        self.assertEqual(result["physical_edge_count"], 1)


class CommonContractTests(unittest.TestCase):
    def test_json_edge_roundtrip_keeps_type(self):
        contracts = build_contracts()
        payload = json.loads(json.dumps(dataclasses.asdict(contracts[0])))
        rebuilt = StageContract(
            payload["stage_id"],
            payload["edge_type"],
            contracts[0].input_type,
            contracts[0].output_type,
            payload["mechanism"],
            payload["model_id"],
            tuple(payload["source_claim_keys"]),
        )
        self.assertEqual(rebuilt, contracts[0])
        self.assertEqual(compose(contracts[0], contracts[1])[0], contracts[0].input_type)

    def test_wrong_units_quantity_basis_and_space_rejected(self):
        contract = build_contracts()[2]
        good = contract.input_type
        for bad in [
            dataclasses.replace(good, unit="J"),
            dataclasses.replace(good, quantity="energy"),
            dataclasses.replace(good, space="different"),
            dataclasses.replace(good, basis=("other",)),
        ]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                contract.accept(Quantity(bad, (1.0,)))
        a = QuantityType("m", "tracer-mass", "kg", ("a", "b"))
        b = dataclasses.replace(a, basis=("b", "a"))
        first = StageContract("a", "physical", a, a, "exchange", "m", ("Layers:C-01",))
        second = StageContract("b", "physical", b, b, "exchange", "m", ("Layers:C-01",))
        with self.assertRaises(ValueError):
            compose(first, second)

    def test_physical_cast_and_unscoped_certificate_rejected(self):
        contract = build_contracts()[2]
        with self.assertRaises(ValueError):
            dataclasses.replace(contract, edge_type="physical")
        with self.assertRaises(ValueError):
            dataclasses.replace(contract, edge_type="certificate")

    def test_values_require_finite_immutable_coordinates(self):
        q = build_contracts()[2].input_type
        for values in [[1.0], (True,), (float("nan"),), (-1.0,), (1.0, 2.0)]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                Quantity(q, values)

    def test_digest_declaration_never_confers_readiness(self):
        record = fixture()["calibration"]
        assessment = CalibrationDeclaration.from_mapping(record).assessment()
        self.assertTrue(assessment["calibration_declared"])
        self.assertFalse(assessment["artifact_bytes_resolved"])
        self.assertFalse(assessment["calibration_ready"])
        self.assertFalse(assessment["empirical_admission"])

    def test_malformed_or_reused_calibration_roots_rejected(self):
        for hashes in ["a" * 64, ["not-hash"], [None], []]:
            record = fixture()["calibration"]
            record["artifact_sha256s"] = hashes
            with self.subTest(hashes=hashes), self.assertRaises(ValueError):
                CalibrationDeclaration.from_mapping(record)
        record = fixture()["calibration"]
        record["holdout_root"] = record["calibration_root"]
        with self.assertRaises(ValueError):
            CalibrationDeclaration.from_mapping(record)
        record = fixture()["calibration"]
        record["calibration_ready"] = True
        with self.assertRaises(ValueError):
            CalibrationDeclaration.from_mapping(record)

    def test_first_moments_do_not_supply_a_likelihood_or_exclusion(self):
        q = Quantity(QuantityType("sample", "tracer-mass", "kg", ("t",)), (1.0,))
        observation = observe_mass(q, 10, efficiency=0.5)
        self.assertEqual(observation["expected_counts"], [5.0])
        self.assertIsNone(observation["no_record_probability"])
        with self.assertRaises(NotImplementedError):
            observation_likelihood(observation, 0)
        with self.assertRaises(NotImplementedError):
            exclusion_from_null(observation)
        # Two distributions with equal first moments but different null probabilities.
        self.assertEqual(0.5 * 0 + 0.5 * 2, 1.0)
        self.assertNotEqual(0.5, 0.0)  # versus the deterministic count-one law

    def test_constant_markov_reduction_can_lose_declared_output(self):
        report = finite_reduction_diagnostics([[1, 0], [0, 1]], [0, 0], [0, 1])
        self.assertTrue(report["strong_lumpability_at_tolerance"])
        self.assertFalse(report["instantaneous_declared_output_constant_on_fibers"])

    def test_nonlumpable_partition_and_invalid_probability_rejected(self):
        result = finite_reduction_diagnostics(
            [[0, 0, 1], [0, 1, 0], [0, 0, 1]], [0, 0, 1], [0, 0, 1]
        )
        self.assertFalse(result["strong_lumpability_at_tolerance"])
        with self.assertRaises(ValueError):
            finite_reduction_diagnostics([[1.1, -0.1], [0, 1]], [0, 0], [0, 1])

    def test_first_order_rank_does_not_decide_nonlinear_identifiability(self):
        report = first_order_rank([[[0.0]]])
        self.assertEqual(report["first_order_numerical_rank"], 0)
        self.assertEqual(report["nonlinear_local_identifiability"], "not-assessed")
        self.assertEqual(report["global_identifiability"], "not-assessed")
        values = [x**3 for x in [-0.1, 0, 0.1]]
        self.assertEqual(len(set(values)), 3)
        self.assertEqual(len(set([0 for _ in values])), 1)

    def test_frozen_transfer_ignores_holdout_labels(self):
        args = dict(
            source_time=[0.0, 1.0, 2.0, 3.0],
            source_response=[0.0, 0.5, 0.8, 0.9],
            source_tau=1.0,
            source_amplitude=1.0,
            calibration_tau=[1.0, 1.1],
            calibration_amplitude=[2.0, 2.1],
            target_time=[0.0, 1.0, 2.0],
            training_root="synthetic:a",
            calibration_root="synthetic:b",
            holdout_root="synthetic:c",
        )
        a = research_candidate.frozen_transfer_pipeline(**args, target_response=[0.0, 1.0, 2.0])
        b = research_candidate.frozen_transfer_pipeline(**args, target_response=[9.0, 8.0, 7.0])
        self.assertEqual(a["frozen_map_sha256"], b["frozen_map_sha256"])
        self.assertEqual(a["prediction"], b["prediction"])
        self.assertNotEqual(a["rmse_K"], b["rmse_K"])

    def test_base_positive_semidefinite_and_finite_guards_retained(self):
        with self.assertRaises(ValueError):
            astra_reservoir.system_matrices([1, 1], [], [[-1, 0], [0, 1]])
        with self.assertRaises(ValueError):
            astra_reservoir.system_matrices([1, float("nan")], [], [1, 1])


if __name__ == "__main__":
    unittest.main()
