"""Small local contract tests for the unpromoted bridge prototype."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bridge_contract import (
    CalibratedPredictionAudit,
    ConservationContract,
    InterventionDesign,
    InterventionOption,
    ObservationalEquivalenceClass,
    ThermodynamicLedger,
    ThermodynamicTerm,
    gaussian_crps,
    apply_data_split,
    canonical_protocol_json,
    canonical_graph_label,
    compare_linear_models,
    controllability_matrix,
    example_protocol,
    fisher_information_from_jacobian,
    fisher_pairwise_separation,
    intervention_option_from_signatures,
    matrix_rank_condition,
    observability_matrix,
    posterior_predictive_check,
    partition_equivalence_classes,
    run_calibrated_prediction_audit,
    select_intervention,
    seeded_three_way_split,
    simulation_based_calibration,
    StrictSPPTAdapter,
    ThermalEdgeContract,
    read_protocol_json,
    write_protocol_json,
    transfer_signature,
    protocol_from_dict,
)
from validate_schema import DRAFT_2020_12_SCHEMA, validate_protocol_schema


class BridgeContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = ConservationContract(
            incidence=np.array([[-1.0], [1.0]]),
            stoichiometry=np.zeros((1, 0)),
            conserved_weights=np.array([1.0]),
            state_units=("mol",),
        )

    def test_valid_conservation_contract_and_dynamic_residual(self) -> None:
        report = self.contract.audit(
            dMdt=np.array([[-2.0], [2.0]]),
            edge_flux=np.array([[2.0]]),
            reaction_rate=np.zeros((2, 0)),
            source=np.zeros((2, 1)),
            escape=np.zeros((2, 1)),
        )
        self.assertTrue(report.passed)
        self.assertEqual(report.dynamic_residual, 0.0)
        self.assertEqual(report.weighted_residual, 0.0)

    def test_malformed_incidence_fails_closed(self) -> None:
        malformed = ConservationContract(
            incidence=np.array([[1.0], [1.0], [0.0]]),
            stoichiometry=np.zeros((1, 0)),
            conserved_weights=np.array([1.0]),
            state_units=("mol",),
        )
        with self.assertRaises(ValueError):
            malformed.validate_structure()

    def test_thermodynamic_ledger_balances_and_requires_nonnegative_production(self) -> None:
        ledger = ThermodynamicLedger(
            terms=(
                ThermodynamicTerm(
                    term_id="heat-in",
                    source="bath",
                    destination="reservoir",
                    process="heat",
                    quantity="energy",
                    units="J",
                    internal_or_external="external",
                    energy_delta=4.0,
                    entropy_flow=1.0,
                    entropy_production=0.0,
                ),
                ThermodynamicTerm(
                    term_id="dissipation",
                    source="reservoir",
                    destination="bath",
                    process="dissipation",
                    quantity="energy",
                    units="J",
                    internal_or_external="internal",
                    energy_delta=-1.0,
                    entropy_flow=0.0,
                    entropy_production=0.2,
                ),
            )
        )
        report = ledger.audit(observed_energy_delta=3.0, observed_entropy_delta=1.2)
        self.assertTrue(report.passed)
        self.assertEqual(report.energy_residual, 0.0)
        self.assertAlmostEqual(report.entropy_residual, 0.0, places=14)

        bad_term = ThermodynamicTerm(
            term_id="bad",
            source="a",
            destination="b",
            process="invalid",
            quantity="energy",
            units="J",
            internal_or_external="internal",
            energy_delta=0.0,
            entropy_flow=0.0,
            entropy_production=-1.0,
        )
        with self.assertRaises(ValueError):
            bad_term.validate()

    def test_typed_downstream_records_require_separate_datasets_and_gates(self) -> None:
        equivalence = ObservationalEquivalenceClass(
            class_id="class-1",
            candidate_ids=("chain", "star"),
            signature_kind="exact",
            maximum_residual=0.0,
            tolerance=1e-12,
            design_id="design-1",
            status="equivalent",
        )
        equivalence.validate()

        design = InterventionDesign(
            design_id="design-1",
            control_ports=("surface-input",),
            observation_ports=("surface-output", "deep-sensor"),
            objective="maximize minimum class separation",
            budget=1.0,
            safety_constraints=("conservation", "entropy", "amplitude-limit"),
            expected_minimum_separation=0.1,
        )
        design.validate()

        audit = CalibratedPredictionAudit(
            audit_id="audit-1",
            fit_data_id="fit-1",
            calibration_data_id="cal-1",
            test_data_id="test-1",
            candidate_id="topology-aware",
            baseline_id="fixed-topology",
            heldout_log_score=-1.0,
            baseline_heldout_log_score=-1.2,
            coverage=0.9,
            target_coverage=0.9,
            calibration_status="pass",
            result="promote",
        )
        audit.validate()

        with self.assertRaises(ValueError):
            CalibratedPredictionAudit(
                audit_id="bad",
                fit_data_id="same",
                calibration_data_id="same",
                test_data_id="test",
                candidate_id="candidate",
                baseline_id="baseline",
                heldout_log_score=0.0,
                baseline_heldout_log_score=0.0,
                coverage=0.9,
                target_coverage=0.9,
                calibration_status="unknown",
                result="promote",
            ).validate()

    def test_transfer_signatures_partition_observational_classes(self) -> None:
        signature_a = transfer_signature(
            np.array([[0.5]]),
            np.array([[1.0]]),
            np.array([[2.0]]),
            np.array([[0.0]]),
        )
        signature_b = transfer_signature(
            np.array([[0.5]]),
            np.array([[1.0]]),
            np.array([[2.0 + 1e-10]]),
            np.array([[0.0]]),
        )
        signature_c = transfer_signature(
            np.array([[0.2]]),
            np.array([[1.0]]),
            np.array([[2.0]]),
            np.array([[0.0]]),
        )
        classes = partition_equivalence_classes(
            {"candidate-a": signature_a, "candidate-b": signature_b, "candidate-c": signature_c},
            "design-2",
            absolute_tolerance=1e-8,
            relative_tolerance=1e-8,
        )
        self.assertEqual(len(classes), 2)
        self.assertEqual(classes[0].candidate_ids, ("candidate-a", "candidate-b"))
        self.assertEqual(classes[0].status, "equivalent")
        self.assertEqual(classes[1].candidate_ids, ("candidate-c",))
        self.assertEqual(classes[1].status, "identified")

    def test_identifiability_reports_poles_zeros_ranks_and_label_quotient(self) -> None:
        visible = {
            "A": np.diag([0.5, 0.2]),
            "B": np.array([[1.0], [0.0]]),
            "C": np.array([[1.0, 0.0]]),
            "D": np.array([[0.0]]),
        }
        hidden_mode_changed = {
            "A": np.diag([0.5, 0.9]),
            "B": np.array([[1.0], [0.0]]),
            "C": np.array([[1.0, 0.0]]),
            "D": np.array([[0.0]]),
        }
        report = compare_linear_models(visible, hidden_mode_changed)
        self.assertTrue(report.practical_equivalent)
        self.assertTrue(report.exact_equivalent)
        near = {
            "A": np.diag([0.500000001, 0.2]),
            "B": np.array([[1.0], [0.0]]),
            "C": np.array([[1.0, 0.0]]),
            "D": np.array([[0.0]]),
        }
        near_report = compare_linear_models(visible, near)
        self.assertTrue(near_report.practical_equivalent)
        self.assertFalse(near_report.exact_equivalent)
        self.assertEqual(matrix_rank_condition(controllability_matrix(visible["A"], visible["B"])).rank, 1)
        self.assertEqual(matrix_rank_condition(observability_matrix(visible["A"], visible["C"])).rank, 1)

        adjacency = np.array([[0.0, 1.0], [2.0, 0.0]])
        relabeled = adjacency[[1, 0]][:, [1, 0]]
        self.assertEqual(canonical_graph_label(adjacency), canonical_graph_label(relabeled))

    def test_intervention_selection_enforces_budget_and_safety(self) -> None:
        cheap = intervention_option_from_signatures(
            option_id="cheap",
            control_ports=("u1",),
            observation_ports=("y1",),
            cost=1.0,
            candidate_signatures={"a": [1.0, 0.0], "b": [1.2, 0.0]},
            safety_ok=True,
        )
        options = (
            cheap,
            InterventionOption(
                option_id="best",
                control_ports=("u2",),
                observation_ports=("y2",),
                cost=2.0,
                expected_minimum_separation=0.8,
                safety_ok=True,
            ),
            InterventionOption(
                option_id="unsafe",
                control_ports=("u3",),
                observation_ports=("y3",),
                cost=0.1,
                expected_minimum_separation=1.0,
                safety_ok=False,
                safety_reason="exceeds amplitude limit",
            ),
        )
        selection = select_intervention(options, budget=2.0)
        self.assertTrue(selection.feasible)
        self.assertEqual(selection.selected_option_id, "best")
        self.assertEqual(selection.total_cost, 2.0)
        self.assertIn("unsafe", selection.rejected_option_ids)
        no_selection = select_intervention(options, budget=0.05)
        self.assertFalse(no_selection.feasible)

        fisher_option = intervention_option_from_signatures(
            option_id="fisher",
            control_ports=("u4",),
            observation_ports=("y4", "y5"),
            cost=1.0,
            candidate_signatures={"a": [0.0, 0.0], "b": [1.0, 0.0]},
            safety_ok=True,
            noise_covariance=np.eye(2),
        )
        self.assertEqual(fisher_option.utility_kind, "fisher")
        self.assertAlmostEqual(fisher_option.expected_minimum_separation, 1.0)
        self.assertAlmostEqual(fisher_pairwise_separation({"a": [0.0, 0.0], "b": [1.0, 0.0]}, np.eye(2)), 1.0)
        information = fisher_information_from_jacobian(np.eye(2), np.eye(2))
        np.testing.assert_allclose(information, np.eye(2))

    def test_heldout_scoring_calibrates_on_one_split_and_compares_baseline(self) -> None:
        calibration_observed = np.array([0.10, -0.10, 0.05, -0.05])
        candidate_calibration_mean = np.zeros(4)
        baseline_calibration_mean = np.full(4, 0.25)
        test_observed = np.array([0.02, -0.04, 0.03, -0.01, 0.04, -0.02])
        audit = run_calibrated_prediction_audit(
            audit_id="audit-2",
            fit_data_id="fit-2",
            calibration_data_id="cal-2",
            test_data_id="test-2",
            candidate_id="candidate",
            baseline_id="baseline",
            calibration_observed=calibration_observed,
            candidate_calibration_mean=candidate_calibration_mean,
            baseline_calibration_mean=baseline_calibration_mean,
            test_observed=test_observed,
            candidate_test_mean=np.zeros(6),
            baseline_test_mean=np.full(6, 0.25),
            target_coverage=0.9,
            coverage_tolerance=0.1,
        )
        self.assertEqual(audit.result, "promote")
        self.assertEqual(audit.calibration_status, "pass")
        self.assertGreater(audit.heldout_log_score, audit.baseline_heldout_log_score)
        self.assertIsNotNone(audit.candidate_crps)
        self.assertIsNotNone(audit.baseline_crps)
        self.assertGreaterEqual(gaussian_crps(test_observed, np.zeros(6), 0.1), 0.0)

    def test_seeded_splits_ppc_sbc_and_miscalibration_gate(self) -> None:
        values = np.arange(30.0)
        split_a = seeded_three_way_split(30, seed=17)
        split_b = seeded_three_way_split(30, seed=17)
        self.assertEqual(split_a, split_b)
        fit, calibration, test = apply_data_split(values, split_a)
        self.assertEqual((fit.size, calibration.size, test.size), (18, 6, 6))

        predictive = np.vstack([np.linspace(-0.1, 0.1, 6) + offset for offset in np.linspace(-0.02, 0.02, 30)])
        ppc = posterior_predictive_check(np.zeros(6), predictive)
        self.assertEqual(ppc.draw_count, 30)
        self.assertTrue(0.0 <= ppc.coverage <= 1.0)
        self.assertTrue(0.0 <= ppc.discrepancy_p_value <= 1.0)

        offsets = np.linspace(-1.0, 1.0, 50)
        posterior = np.tile(offsets[:, None], (1, 20))
        truth = np.array([offsets[5 + (index % 5) * 10] for index in range(20)])
        sbc = simulation_based_calibration(truth, posterior, bins=5)
        self.assertEqual(len(sbc.ranks), 20)
        self.assertEqual(sum(sbc.bin_counts), 20)
        self.assertEqual(sbc.status, "pass")

        deferred = run_calibrated_prediction_audit(
            audit_id="audit-miscalibrated",
            fit_data_id="fit-miscalibrated",
            calibration_data_id="cal-miscalibrated",
            test_data_id="test-miscalibrated",
            candidate_id="candidate",
            baseline_id="baseline",
            calibration_observed=np.array([0.1, -0.1, 0.05, -0.05]),
            candidate_calibration_mean=np.zeros(4),
            baseline_calibration_mean=np.zeros(4),
            test_observed=np.full(6, 2.0),
            candidate_test_mean=np.zeros(6),
            baseline_test_mean=np.full(6, 1.0),
            target_coverage=0.9,
            coverage_tolerance=0.05,
        )
        self.assertEqual(deferred.result, "defer")
        self.assertEqual(deferred.calibration_status, "fail")

    def test_adversarial_replays_and_successor_sppt_adapter(self) -> None:
        adapter = StrictSPPTAdapter(
            conservation=self.contract,
            edges=(ThermalEdgeContract("edge-1", tail=0, head=1, conductance=2.0),),
        )
        audit = adapter.audit(np.array([3.0, 1.0]))
        self.assertTrue(audit.passed)
        self.assertGreater(audit.edge_entropy_production[0], 0.0)
        with self.assertRaises(ValueError):
            adapter.audit(np.array([0.0, 1.0]))

        bad_adapter = StrictSPPTAdapter(
            conservation=self.contract,
            edges=(ThermalEdgeContract("wrong-edge", tail=1, head=0, conductance=2.0),),
        )
        with self.assertRaises(ValueError):
            bad_adapter.validate()

        omitted_channel = intervention_option_from_signatures(
            option_id="omitted-channel",
            control_ports=("u",),
            observation_ports=("y",),
            cost=1.0,
            candidate_signatures={"anisotropic": [1.0, 0.1], "scalar": [1.0, 0.1]},
            safety_ok=True,
            noise_covariance=np.diag([0.01, 1.0]),
        )
        self.assertEqual(omitted_channel.utility_kind, "fisher")
        self.assertAlmostEqual(omitted_channel.expected_minimum_separation, 0.0)
        anisotropic = intervention_option_from_signatures(
            option_id="anisotropic-channel",
            control_ports=("u",),
            observation_ports=("y", "directional-y"),
            cost=1.0,
            candidate_signatures={"anisotropic": [1.0, 0.8], "scalar": [1.0, 0.2]},
            safety_ok=True,
            noise_covariance=np.diag([0.01, 0.04]),
        )
        self.assertGreater(anisotropic.expected_minimum_separation, omitted_channel.expected_minimum_separation)
        chosen = select_intervention((omitted_channel, anisotropic), budget=1.0)
        self.assertEqual(chosen.selected_option_id, "anisotropic-channel")

    def test_canonical_protocol_round_trip_is_byte_stable(self) -> None:
        protocol = example_protocol()
        canonical = canonical_protocol_json(protocol)
        restored = protocol_from_dict(json.loads(canonical))
        self.assertEqual(canonical_protocol_json(restored), canonical)
        self.assertEqual(restored.protocol_id, "sppt-bridge-demo-v0.1.0")
        dynamic = json.loads(canonical)
        dynamic["unexpected_runtime_field"] = "forbidden"
        with self.assertRaises(ValueError):
            protocol_from_dict(dynamic)
        with tempfile.TemporaryDirectory() as temporary_root:
            target = Path(temporary_root) / "protocol.json"
            write_protocol_json(target, protocol)
            self.assertEqual(read_protocol_json(target).protocol_id, protocol.protocol_id)
            self.assertEqual(target.read_text(encoding="utf-8"), canonical)

    def test_checked_in_example_is_canonical_and_round_trips(self) -> None:
        example_path = Path(__file__).with_name("example_protocol.json")
        raw = example_path.read_text(encoding="utf-8")
        parsed = protocol_from_dict(json.loads(raw))
        self.assertEqual(raw, canonical_protocol_json(parsed))

    def test_schema_validation_never_falls_back_from_draft_2020_12(self) -> None:
        result = validate_protocol_schema()
        self.assertEqual(result.declared_schema, DRAFT_2020_12_SCHEMA)
        self.assertIn(result.status, {"valid", "environment_limited"})
        if result.status == "environment_limited":
            self.assertIsNone(result.validator)
            self.assertIn("Draft202012Validator", result.reason or "")
        else:
            self.assertEqual(result.status, "valid")
            self.assertIn("Draft202012Validator", result.validator or "")

    def test_bridge_manifest_binds_all_local_payload_bytes(self) -> None:
        root = Path(__file__).parent
        manifest = root / "BRIDGE_MANIFEST.sha256"
        rows = [line.split("  ", 1) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
        observed = set()
        for digest, relative_name in rows:
            self.assertNotIn(relative_name, observed)
            observed.add(relative_name)
            target = root / relative_name
            self.assertTrue(target.is_file())
            actual = hashlib.sha256(target.read_bytes()).hexdigest()
            self.assertEqual(actual, digest)
        expected = {path.name for path in root.iterdir() if path.is_file() and path.name != manifest.name}
        self.assertEqual(observed, expected)


if __name__ == "__main__":
    unittest.main()
