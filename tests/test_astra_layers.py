from __future__ import annotations

import json
import unittest

import numpy as np

import astra_layers as astra
from core_contracts import ObservationStatus


class TestAstraLayers(unittest.TestCase):
    def test_string_enum_compatibility(self):
        for enum_type in (astra.EdgeType, ObservationStatus):
            for member in enum_type:
                with self.subTest(member=member):
                    label = f"{enum_type.__name__}.{member.name}"
                    self.assertEqual(str(member), label)
                    self.assertEqual(f"{member}", label)
                    self.assertEqual(format(member, ">45"), format(label, ">45"))
                    self.assertEqual(repr(member), f"<{label}: {member.value!r}>")
                    self.assertIs(enum_type(member.value), member)
                    self.assertIs(enum_type(member), member)
                    self.assertIsInstance(member, str)
                    self.assertEqual(member, member.value)
                    self.assertEqual(
                        json.dumps({"kind": member}), json.dumps({"kind": member.value})
                    )

    def test_intervention_choice_preserves_scores_and_ties(self):
        selected, scores = astra.best_intervention_by_kl(
            {"first": [0.0], "second": [1.0], "third": [1.0]},
            {"first": [0.0], "second": [0.0], "third": [0.0]},
            1.0,
        )
        self.assertEqual(selected, "second")
        self.assertEqual(scores, {"first": 0.0, "second": 0.5, "third": 0.5})
        with self.assertRaises(ValueError):
            astra.best_intervention_by_kl({}, {}, 1.0)

    def test_typed_graph_requires_physical_units(self):
        g = astra.LayeredGraph(
            nodes={"a", "b"},
            edges=[astra.TypedEdge("a", "b", astra.EdgeType.PHYSICAL, "diffusion")],
        )
        with self.assertRaises(ValueError):
            g.validate()

    def test_certificate_requires_scope(self):
        g = astra.LayeredGraph(
            nodes={"m", "c"}, edges=[astra.TypedEdge("m", "c", astra.EdgeType.CERTIFICATE, "audit")]
        )
        with self.assertRaises(ValueError):
            g.validate()

    def test_internal_flux_conserves_inventory(self):
        B = astra.incidence_matrix(3, [(0, 1), (1, 2)])
        d = astra.physical_inventory_tendency(B, [1.2, -0.7], [0, 0, 0], [0, 0, 0])
        self.assertAlmostEqual(float(np.sum(d)), 0.0, places=14)

    def test_equal_likelihood_preserves_odds(self):
        self.assertEqual(astra.posterior_odds(2.5, 1.0), 2.5)

    def test_closed_loop_confounding(self):
        self.assertAlmostEqual(
            astra.closed_loop_coefficient(0.8, 0.5, 0.6),
            astra.closed_loop_coefficient(0.65, 0.25, 0.6),
            places=14,
        )
        z = np.zeros(20)
        self.assertTrue(
            np.allclose(
                astra.simulate_closed_loop(0.8, 0.5, 0.6, z),
                astra.simulate_closed_loop(0.65, 0.25, 0.6, z),
            )
        )
        p = z.copy()
        p[2] = 1
        self.assertGreater(
            float(
                np.max(
                    np.abs(
                        astra.simulate_closed_loop(0.8, 0.5, 0.6, p)
                        - astra.simulate_closed_loop(0.65, 0.25, 0.6, p)
                    )
                )
            ),
            0.2,
        )

    def test_archive_kernel(self):
        t = np.linspace(0, 10, 1001)
        leak = np.where(t < 5, 0.5, 0.02)
        src = np.sin(t) ** 2
        self.assertAlmostEqual(
            float(astra.archive_kernel_weights(t, leak) @ src),
            float(astra.archive_state(t, src, leak)[-1]),
            places=10,
        )

    def test_uninformative_certificate(self):
        self.assertAlmostEqual(astra.certificate_posterior_failure(0.2, 0.7, 0.7), 0.2, places=14)

    def test_selectivity_tradeoff(self):
        tau = np.linspace(-3, 4, 200)
        y, q = astra.selectivity_curve(tau, good_prior=0.3, good_mean=1.2, bad_mean=0, sigma=1)
        self.assertTrue(np.all(np.diff(y) <= 1e-12))
        self.assertTrue(np.all(np.diff(q) >= -1e-12))

    def test_best_intervention(self):
        best, s = astra.best_intervention_by_kl(
            {"u0": [0], "u1": [0, 1]}, {"u0": [0], "u1": [0, 1.5]}, 0.1
        )
        self.assertEqual(best, "u1")
        self.assertEqual(s["u0"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
