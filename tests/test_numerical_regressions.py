"""Independent edge cases for integrated-core diagnostics, not empirical validation."""

import copy
import dataclasses
import json
import math
import unittest
from pathlib import Path

import numpy as np

import admission
import astra_layers as layers
import boundary_state as gamma
import coupling_state as xi
import research_candidate as october
from scripts import scm_replay_checks as scm


class LayersRegressions(unittest.TestCase):
    def test_ILG01_small_rate_long_horizon(self):
        expected = -math.expm1(-10) / 1e-15
        self.assertAlmostEqual(
            layers.archive_state([0, 1e16], [1, 1], [1e-15, 1e-15])[-1] / expected, 1, places=12
        )
        self.assertAlmostEqual(
            layers.archive_kernel_weights([0, 1e16], [1e-15, 1e-15])[0] / expected, 1, places=12
        )
        # Same physical problem in a time coordinate scaled by 1e15.
        scaled = layers.archive_state([0, 10], [1e15, 1e15], [1, 1])[-1]
        self.assertAlmostEqual(scaled / expected, 1, places=12)

    def test_ILG01_small_accumulated_decay(self):
        expected = -math.expm1(-1e-16)
        self.assertAlmostEqual(
            layers.archive_state([0, 1e-16], [1, 1], [1, 1])[-1] / expected, 1, places=12
        )

    def test_archive_invalid_grids(self):
        for t, ell in [([], []), ([1, 0], [0, 0]), ([0, 1], [-1, 0])]:
            with self.subTest(t=t, ell=ell), self.assertRaises(ValueError):
                layers.archive_kernel_weights(t, ell)

    def test_ILG02_json_requirements(self):
        for kind in ["physical", "certificate"]:
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                e = layers.TypedEdge(
                    **json.loads(
                        json.dumps({"tail": "a", "head": "b", "edge_type": kind, "mechanism": "m"})
                    )
                )
                layers.LayeredGraph({"a", "b"}, [e]).validate()

    def test_ILG02_json_roundtrip_selection(self):
        e = layers.TypedEdge("a", "b", "physical", "transport", units="kg")
        g = layers.LayeredGraph({"a", "b"}, [e])
        g.validate()
        self.assertEqual(g.by_type(layers.EdgeType.PHYSICAL), [e])
        self.assertEqual(g.by_type("physical"), [e])

    def test_ILG02_unknown_type(self):
        with self.assertRaises(ValueError):
            layers.TypedEdge("a", "b", "unknown", "m")


class GammaRegressions(unittest.TestCase):
    def rate(self, f, m):
        return gamma.passive_free_energy_rate(f, m, [0], [0], [0], [0], [0], [0], [0], [0])

    def test_ILG03_material_negative_mobility(self):
        for scale in [1e-6, 1, 1e6]:
            with self.subTest(scale=scale), self.assertRaises(ValueError):
                self.rate([1e8], [[-1e-13 * scale]])

    def test_ILG03_roundoff_cannot_generate_energy(self):
        with self.assertRaises(ValueError):
            self.rate([1e10, 0], np.diag([-1e-17, 1]))
        # Correlation eigenvalue roundoff can be clipped, but cannot add energy.
        self.assertLessEqual(self.rate([1e10, -1e10], [[1, 1 + 2e-16], [1 + 2e-16, 1]]), 0)

    def test_review_Gamma_large_force_small_mobility(self):
        for m in [1e-300, [1e-300], [[1e-300]]]:
            with self.subTest(m=m):
                self.assertAlmostEqual(self.rate([1e200], m) / -1e100, 1, places=12)
        self.assertEqual(self.rate([1e200], [[0.0]]), 0)
        with self.assertRaises(ValueError):
            self.rate([1e200], [[1.0]])

    def test_review_Gamma_diagonal_scaling(self):
        with self.assertRaises(ValueError):
            self.rate([1, 1], np.diag([-1, 1e20]))
        with self.assertRaises(ValueError):
            self.rate([1, 1], [[0, 1e-100], [1e-100, 1]])
        m = np.array([[2.0, 0.3], [0.3, 1.0]])
        f = np.array([0.5, -2.0])
        scale = np.diag([1e-100, 1e100])
        self.assertAlmostEqual(
            self.rate(f, m), self.rate(np.linalg.solve(scale, f), scale @ m @ scale), places=12
        )

    def test_mobility_must_be_finite(self):
        for m in [float("nan"), [float("nan")], [[float("nan")]]]:
            with self.subTest(m=m), self.assertRaises(ValueError):
                self.rate([1], m)

    def test_ILG05_no_negative_inventory(self):
        for inventory, captured in [(0, 5e-13), (1, 1 + 5e-13)]:
            with self.subTest(inventory=inventory), self.assertRaises(ValueError):
                gamma.compartment_closure_reset(inventory, 1, captured)

    def test_inventory_must_be_finite(self):
        with self.assertRaises(ValueError):
            gamma.compartment_closure_reset(float("nan"), 1, 0)

    def test_ILGC02_shifted_time_origin(self):
        p = gamma.LinearBoundaryParameters(0.7, 0.8, 0.4, 1.1, 2)
        t = np.linspace(5, 7, 31)
        initial = [0.3, -0.2]
        exact = gamma.exact_linear_step(t, p, initial=initial)
        numeric = gamma.simulate_dynamic_boundary(t, lambda _: 1, p, initial=initial)
        np.testing.assert_allclose(exact[:, 0], initial, atol=1e-14)
        np.testing.assert_allclose(exact, numeric, rtol=1e-7, atol=2e-8)


class OctoberRegressions(unittest.TestCase):
    def test_CORE01_declared_hash_cannot_confer_readiness(self):
        records = json.loads(
            (
                Path(admission.__file__).resolve().parents[1]
                / "data/integrated-core/bridge_contracts.json"
            ).read_text()
        )
        for hashes in ["not-a-hash", ["not-a-hash"], ["a" * 64]]:
            r = copy.deepcopy(records[0])
            r["calibration"].update(status="verified", artifact_hashes=hashes)
            result = admission.audit_bridges([r])
            self.assertEqual(result["calibration_ready_count"], 0)
            self.assertEqual(result["empirical_admission_count"], 0)

    def test_CORE02_detector_only_chain(self):
        r = october.forward_chain([0.7, 0.2, 0.1], [october.synthetic_operators()[-1]])
        self.assertAlmostEqual(r["selected_mass_kg"], 1, places=14)
        self.assertAlmostEqual(r["mass_closure_residual_kg"], 0)

    def test_CORE02_no_selection_chain(self):
        ops = october.synthetic_operators()
        ops[4] = dataclasses.replace(ops[4], layer="physical", kind="mass-transfer")
        r = october.forward_chain([0.7, 0.2, 0.1], ops)
        self.assertEqual(r["unobserved_mass_kg"], 0)
        self.assertAlmostEqual(r["mass_closure_residual_kg"], 0)

    def test_CORE03_zero_expected_counts(self):
        ops = october.synthetic_operators()
        ops[-1] = dataclasses.replace(ops[-1], matrix=tuple(map(tuple, np.zeros((3, 3)))))
        r = october.forward_chain([1, 0, 0], ops)
        self.assertEqual(r["expected_counts"], [0, 0, 0])
        self.assertIsNone(r["normalized_count_response"])
        self.assertEqual(r["observation_model_status"], "first-moment-only")
        self.assertIsNone(r["no_record_probability"])

    def test_CORE04_freeze_boundary(self):
        st = np.linspace(0, 3, 40)
        sy = october.transfer_prediction(st, 1.2, 2, 4)
        tt = np.linspace(0, 5, 40)
        args = dict(
            source_time=st,
            source_response=sy,
            source_tau=2,
            source_amplitude=4,
            calibration_tau=[17, 17.2, 16.8],
            calibration_amplitude=[0.6, 0.61, 0.59],
            target_time=tt,
            training_root="train",
            calibration_root="metrology",
            holdout_root="holdout",
        )
        a = october.frozen_transfer_pipeline(target_response=np.zeros(40), **args)
        b = october.frozen_transfer_pipeline(target_response=np.full(40, 999), **args)
        for key in ["frozen_map", "frozen_map_sha256", "prediction"]:
            self.assertEqual(a[key], b[key])
        self.assertNotEqual(a["rmse_K"], b["rmse_K"])
        args["holdout_root"] = "metrology"
        with self.assertRaises(ValueError):
            october.frozen_transfer_pipeline(target_response=np.zeros(40), **args)


class ScopedClaimControls(unittest.TestCase):
    def test_ILG04_markov_reduction_not_output_sufficiency(self):
        # A constant reduced state is Markov; hidden h still changes Y=h.
        hidden = [-1, 1]
        reduced_future = [0 for _ in hidden]
        self.assertEqual(reduced_future[0], reduced_future[1])
        self.assertNotEqual(hidden[0], hidden[1])

    def test_ILGC01_zero_rank_not_noninjectivity(self):
        self.assertEqual(xi.local_sensitivity_rank([[[0.0]]]), 0)
        self.assertLess((-1e-3) ** 3, 0)
        self.assertGreater((1e-3) ** 3, 0)
        # Constant forward map is a separate nonidentifiable example.
        self.assertEqual(0 * -1e-3, 0 * 1e-3)

    def test_CORE08_repeatable_explicit_run(self):
        a = scm.run_checks(seed=1042026)
        b = scm.run_checks(seed=1042026)
        self.assertEqual(a, b)
        self.assertEqual(a["total_checks"], 9)
        self.assertTrue(a["replay_source_executed"])
        self.assertFalse(a["empirical_data"])
