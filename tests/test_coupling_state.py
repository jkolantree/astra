from __future__ import annotations

import unittest

import numpy as np

import coupling_state as cs


class TestCouplingState(unittest.TestCase):
    def test_schur_context_softens(self) -> None:
        kxx = np.diag([2.0, 3.0])
        kxq = np.array([[0.5], [0.8]])
        kqq = np.array([[1.5]])
        keff = cs.schur_effective_stiffness(kxx, kxq, kqq)
        reduction = kxx - keff
        self.assertGreaterEqual(float(np.min(np.linalg.eigvalsh(reduction))), -1e-12)
        self.assertLess(
            float(np.min(np.linalg.eigvalsh(keff))), float(np.min(np.linalg.eigvalsh(kxx)))
        )

    def test_similarity_transform_preserves_output(self) -> None:
        A = np.array([[-0.7, 0.2], [-0.1, -0.3]])
        B = np.array([[1.0], [0.4]])
        C = np.array([[0.6, -0.2]])
        D = np.zeros((1, 1))
        S = np.array([[1.0, 0.5], [-0.3, 1.2]])
        At, Bt, Ct = cs.similarity_transform(A, B, C, S)
        u = np.sin(np.linspace(0, 8, 500))[:, None]
        x0 = np.array([0.2, -0.4])
        _, y = cs.simulate_lti_piecewise_constant(A, B, C, D, u, 0.02, x0)
        _, yt = cs.simulate_lti_piecewise_constant(At, Bt, Ct, D, u, 0.02, S @ x0)
        self.assertLess(float(np.max(np.abs(y - yt))), 1e-10)

    def test_stateful_channel_is_sequence_dependent(self) -> None:
        p = cs.StatefulChannelParameters(0.8, 0.4, 1.0, 0.7, -0.3)
        x1 = np.array([1.0, 0.0, -1.0, 0.0])
        x2 = x1[::-1]
        _, y1 = cs.simulate_stateful_channel(x1, p)
        _, y2 = cs.simulate_stateful_channel(x2, p)
        self.assertFalse(np.allclose(y1[::-1], y2))

    def test_ar1_effective_sample_size(self) -> None:
        self.assertAlmostEqual(cs.ar1_effective_sample_size(1000, 0.5), 1000 / 3)

    def test_precision_floor(self) -> None:
        self.assertAlmostEqual(cs.precision_floor(2.0, 100.0, 0.3), np.sqrt(0.04 + 0.09))

    def test_chiral_reference_energy_reverses(self) -> None:
        e1 = cs.chiral_reference_completion_energy(1.0, [1, 0, 0], [0, 1, 0], [0, 0, 1], 2.0)
        e2 = cs.chiral_reference_completion_energy(1.0, [1, 0, 0], [0, 1, 0], [0, 0, -1], 2.0)
        self.assertAlmostEqual(e1, -e2)

    def test_negative_correlation_can_raise_effective_count(self) -> None:
        self.assertGreater(cs.effective_sample_size_from_autocorrelation([-0.1], 1000), 1000)

    def test_diffusion_steady_limit(self) -> None:
        flux = np.array([2.0, 3.0])
        tau = np.array([1.0, 4.0])
        result = cs.two_element_diffusion_snapshot(flux, tau, duration=100.0)
        np.testing.assert_allclose(result, flux * tau, rtol=1e-10)

    def test_diffusion_decreasing_phase(self) -> None:
        start = cs.two_element_diffusion_snapshot([1.0, 1.0], [1.0, 3.0], duration=10.0)
        later = cs.two_element_diffusion_snapshot(
            [1.0, 1.0], [1.0, 3.0], duration=10.0, time_since_stop=2.0
        )
        self.assertTrue(np.all(later < start))
        self.assertNotAlmostEqual(later[0] / start[0], later[1] / start[1])

    def test_sensitivity_rank(self) -> None:
        rank1 = cs.local_sensitivity_rank([[[1.0]], [[2.0]]])
        rank2 = cs.local_sensitivity_rank([[[1.0], [0.0]], [[0.0], [1.0]]])
        self.assertEqual(rank1, 1)
        self.assertEqual(rank2, 2)

    def test_operational_edge(self) -> None:
        self.assertFalse(cs.operational_edge_present([0.0, 1e-14]))
        self.assertTrue(cs.operational_edge_present([0.0, 1e-3]))

    def test_disclosure_severity_zero(self) -> None:
        self.assertAlmostEqual(cs.normalized_disclosure_severity([1, 2], [1, 2]), 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
