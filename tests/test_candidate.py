"""Meaningful negative controls and mathematical invariants for the candidate."""

import dataclasses
import unittest

import numpy as np

from research_candidate import (
    QuantityType,
    common_unit_rmse,
    equivalence_decision,
    fit_shape,
    forward_chain,
    hybrid_archive,
    joint_logscore_gap,
    monte_carlo,
    synthetic_operators,
    transfer_prediction,
    validate_chain,
)


class TypedChainTests(unittest.TestCase):
    def test_conserved_tracer_accounting_across_random_inputs(self):
        rng = np.random.default_rng(903)
        for _ in range(100):
            x = rng.dirichlet(np.ones(3)) * rng.uniform(0.01, 10)
            y = forward_chain(x, synthetic_operators())
            self.assertAlmostEqual(y["mass_closure_residual_kg"], 0, places=12)
            self.assertAlmostEqual(sum(y["normalized_count_response"]), 1, places=12)
            self.assertGreaterEqual(y["outside_tracked_mass_kg"], 0)
            self.assertGreaterEqual(y["unobserved_mass_kg"], 0)

    def test_same_space_wrong_unit_fails(self):
        ops = synthetic_operators()
        i = 2
        wrong = dataclasses.replace(ops[i].input_type, unit="g")
        ops[i] = dataclasses.replace(ops[i], input_type=wrong)
        with self.assertRaises(ValueError):
            validate_chain(ops)

    def test_same_endpoint_wrong_semantics_fails(self):
        ops = synthetic_operators()
        ops[-1] = dataclasses.replace(
            ops[-1], output_type=QuantityType("detector", "energy", "count", ("A", "B", "C"))
        )
        with self.assertRaises(ValueError):
            validate_chain(ops)

    def test_permuted_basis_cannot_silently_compose(self):
        ops = synthetic_operators()
        ops[2] = dataclasses.replace(
            ops[2], input_type=dataclasses.replace(ops[2].input_type, basis=("B", "A", "C"))
        )
        with self.assertRaises(ValueError):
            validate_chain(ops)

    def test_selection_cannot_be_relabeled_physical(self):
        ops = synthetic_operators()
        ops[4] = dataclasses.replace(ops[4], layer="physical")
        with self.assertRaises(ValueError):
            validate_chain(ops)

    def test_mass_creation_rejected_and_empty_observation_retained(self):
        ops = synthetic_operators()
        ops[0] = dataclasses.replace(ops[0], matrix=tuple(map(tuple, np.eye(3) * 1.01)))
        with self.assertRaises(ValueError):
            forward_chain([1, 0, 0], ops)
        ops = synthetic_operators()
        ops[4] = dataclasses.replace(ops[4], matrix=tuple(map(tuple, np.zeros((3, 3)))))
        result = forward_chain([1, 0, 0], ops)
        self.assertEqual(result["expected_counts"], [0, 0, 0])
        self.assertIsNone(result["normalized_count_response"])
        self.assertAlmostEqual(result["mass_closure_residual_kg"], 0)

    def test_noncommuting_operator_order_has_declared_difference(self):
        a = np.diag([0.2, 0.8])
        b = np.array([[0.9, 0.3], [0.1, 0.7]])
        x = np.array([0.8, 0.2])
        self.assertGreater(float(np.linalg.norm(a @ b @ x - b @ a @ x)), 0.01)
        ops = synthetic_operators()
        ops[0], ops[1] = ops[1], ops[0]
        with self.assertRaises(ValueError):
            validate_chain(ops)


class HybridTests(unittest.TestCase):
    def test_exact_guard_jump_and_record_balance(self):
        r = hybrid_archive([0, 1, 2, 3], production=2, decay=0, events=((2, 0.25),))
        self.assertEqual(r["resets"][0]["pre"], 4)
        self.assertEqual(r["resets"][0]["post"], 1)
        self.assertEqual(r["trace"][-1]["stock"], 3)
        self.assertEqual(r["balance_residual"], 0)

    def test_decay_grid_refinement_does_not_change_closed_solution(self):
        a = hybrid_archive(np.linspace(0, 6, 13))
        b = hybrid_archive(np.linspace(0, 6, 121))
        self.assertAlmostEqual(a["trace"][-1]["stock"], b["trace"][-1]["stock"], places=12)
        self.assertAlmostEqual(b["balance_residual"], 0, places=12)

    def test_ambiguous_or_unspecified_event_order_rejected(self):
        for events in [
            ((2, 0.5), (2, 0.4)),
            ((3, 0.5), (1, 0.4)),
            ((2, 1.1),),
            ((float("nan"), 0.5),),
        ]:
            with self.assertRaises(ValueError):
                hybrid_archive([0, 1, 2, 3], events=events)


class ScaleAndScoreTests(unittest.TestCase):
    def test_target_holdout_cannot_change_frozen_prediction(self):
        t = np.linspace(0, 3, 40)
        ys = transfer_prediction(t, 1.2, 2, 4)
        k = fit_shape(t, ys, 2, 4)
        self.assertAlmostEqual(k, 1.2, places=5)
        prediction = transfer_prediction(t, k, 17, 0.6)
        target_holdout = np.zeros(40)
        target_holdout[:] = 999
        np.testing.assert_array_equal(prediction, transfer_prediction(t, k, 17, 0.6))

    def test_mismatched_unit_ratio_is_prohibited(self):
        with self.assertRaises(ValueError):
            common_unit_rmse([1, 2], [1, 2], truth_unit="K", prediction_unit="1")
        self.assertEqual(common_unit_rmse([0, 2], [1, 1], truth_unit="K", prediction_unit="K"), 1)

    def test_scale_map_cannot_prove_equal_shape(self):
        t = np.linspace(0, 25, 100)
        a = transfer_prediction(t, 1, 17, 0.6)
        b = transfer_prediction(t, 1.35, 17, 0.6)
        self.assertGreater(common_unit_rmse(a, b, truth_unit="K", prediction_unit="K"), 0.03)

    def test_covariance_aware_scoring_rejects_singular_noise(self):
        y = np.ones((4, 2))
        with self.assertRaises(np.linalg.LinAlgError):
            joint_logscore_gap(y, y, y, [[1, 1], [1, 1]])
        self.assertEqual(joint_logscore_gap(y, y, y, [[1, 0.5], [0.5, 1]]), 0)


class MonteCarloAndDecisionTests(unittest.TestCase):
    def test_requested_count_controls_actual_execution(self):
        a = monte_carlo(8, 7)
        b = monte_carlo(16, 7)
        self.assertEqual(a["n_mc_executed"], 8)
        self.assertEqual(b["n_mc_executed"], 16)
        self.assertEqual(a["replicates"], b["replicates"][:8])
        self.assertEqual(a, monte_carlo(8, 7))

    def test_invalid_replication_count_is_rejected(self):
        for n in [0, 1, True, 2.5]:
            with self.assertRaises(ValueError):
                monte_carlo(n)

    def test_null_is_not_equivalence_without_precision(self):
        self.assertFalse(equivalence_decision(0, 0.1, 0.05)["equivalent"])
        self.assertTrue(equivalence_decision(0, 0.01, 0.05)["equivalent"])
        self.assertFalse(equivalence_decision(0.1, 0.01, 0.05)["equivalent"])

    def test_margin_boundary_and_nonfinite_values_fail_closed(self):
        self.assertFalse(equivalence_decision(0.05, 0, 0.05)["equivalent"])
        for args in [(float("nan"), 0.01, 0.05), (0, -1, 0.05), (0, 0.1, 0)]:
            with self.assertRaises(ValueError):
                equivalence_decision(*args)


if __name__ == "__main__":
    unittest.main()
