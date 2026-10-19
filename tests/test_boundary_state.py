from __future__ import annotations

import unittest

import numpy as np

import boundary_state as bs


class TestBoundaryState(unittest.TestCase):
    def test_bulk_surface_exchange_closes(self) -> None:
        b = np.array([[1.0, 0.2], [0.4, -0.1]])
        s = np.array([0.3, 0.5])
        j = np.array([[0.2, 0.7], [0.1, 0.1]])
        result = bs.bulk_surface_exchange_balance(b, s, j)
        np.testing.assert_allclose(result.total, np.sum(b, axis=0) + s)

    def test_passive_dissipation_nonpositive(self) -> None:
        rate = bs.passive_free_energy_rate(
            [1.0, -2.0], [1.0, 2.0], [0.5], [3.0], [1.2], [0.4], [0.2], [2.0], [0.3], [1.5]
        )
        self.assertLessEqual(rate, 0.0)

    def test_boundary_dominance_scaling(self) -> None:
        self.assertAlmostEqual(bs.film_boundary_dominance(2.0, 4.0, 0.5), 2.0)
        self.assertAlmostEqual(bs.sphere_boundary_dominance(2.0, 4.0, 0.75), 2.0)

    def test_soft_mode_bound(self) -> None:
        result = bs.soft_mode_response([[2.0, 0.0], [0.0, 0.5]], [[1.0], [2.0]], [0.1])
        self.assertLessEqual(result.response_norm, result.upper_bound + 1e-14)

    def test_schur_elimination_softens(self) -> None:
        kb = np.diag([2.0, 3.0])
        c = np.array([[0.4], [0.6]])
        kg = np.array([[1.5]])
        keff = bs.effective_bulk_stiffness(kb, c, kg)
        reduction = kb - keff
        self.assertGreaterEqual(float(np.min(np.linalg.eigvalsh(reduction))), -1e-12)
        self.assertLess(
            float(np.min(np.linalg.eigvalsh(keff))), float(np.min(np.linalg.eigvalsh(kb)))
        )

    def test_dynamic_operator_recovers_static_limit(self) -> None:
        static = bs.effective_bulk_stiffness([[2.0]], [[0.4]], [[1.2]])
        dynamic = bs.dynamic_effective_stiffness([0.0], [[2.0]], [[0.7]], [[0.4]], [[1.2]], [[0.5]])
        np.testing.assert_allclose(dynamic[0].real, static)
        np.testing.assert_allclose(dynamic[0].imag, 0.0)

    def test_dynamic_boundary_step_matches_numerical(self) -> None:
        p = bs.LinearBoundaryParameters(0.7, 0.8, 0.4, 1.1, 2.0)
        t = np.linspace(0.0, 8.0, 501)
        exact = bs.exact_linear_step(t, p)
        numeric = bs.simulate_dynamic_boundary(t, lambda _t: 1.0, p)
        self.assertLess(float(np.max(np.abs(exact - numeric))), 2e-7)

    def test_kramers_survival(self) -> None:
        t = np.linspace(0.0, 2.0, 1001)
        k = np.repeat(0.7, t.size)
        h = bs.time_dependent_hazard(t, k)
        self.assertAlmostEqual(float(h.survival[-1]), float(np.exp(-1.4)), places=5)

    def test_closure_reset_conserves_inventory(self) -> None:
        r = bs.compartment_closure_reset(10.0, 2.0, 1.5)
        self.assertAlmostEqual(r.total_before, r.total_after)
        self.assertAlmostEqual(r.captured_after, 3.0)

    def test_reservoir_emergence_requires_retention(self) -> None:
        transient = bs.reservoir_emergence(1, 2, 0.5, 1.0)
        persistent = bs.reservoir_emergence(1, 2, 20.0, 1.0)
        self.assertFalse(transient.is_reservoir)
        self.assertTrue(persistent.is_reservoir)

    def test_gauss_bonnet(self) -> None:
        self.assertAlmostEqual(bs.gauss_bonnet_integral(0, 1), 4.0 * np.pi)
        self.assertAlmostEqual(bs.gauss_bonnet_integral(1, 1), 0.0)
        self.assertAlmostEqual(bs.gauss_bonnet_integral(0, 2), 8.0 * np.pi)

    def test_size_design_rank(self) -> None:
        one = bs.size_decomposition_design([2.0])
        many = bs.size_decomposition_design([1.0, 2.0, 4.0])
        self.assertEqual(np.linalg.matrix_rank(one), 1)
        self.assertEqual(np.linalg.matrix_rank(many), 2)

    def test_critical_thickness(self) -> None:
        self.assertAlmostEqual(bs.critical_film_thickness(1.0, -0.2, 0.0, -0.4), 0.5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
