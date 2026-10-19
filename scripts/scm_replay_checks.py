"""Independent synthetic checks of the proposed SCM graph-volume dynamics.

SCM mathematical replay implementation; no empirical data are used.
Run with ordinary Python 3.12 and NumPy; no SymPy, SciPy, or data download needed.
Usage: python scripts/scm_replay_checks.py --output replay_results.json

The numerical experiments are mathematical replay checks, not measurements.
Exact mathematical statements and model assumptions appear in the JSON output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np

SEED = 1042026


def scalar(x):
    return float(x)


def record(name, passed, **details):
    return {"name": name, "passed": bool(passed), **details}


def l2(f, dx):
    return scalar(np.sqrt(dx * np.sum(np.abs(f) ** 2)))


def derivative(f, length=2 * np.pi, order=1):
    """Fourier derivative on a periodic synthetic one-dimensional grid."""
    k = 2 * np.pi * np.fft.fftfreq(f.size, d=length / f.size)
    return np.fft.ifft((1j * k) ** order * np.fft.fft(f))


def graph_hamiltonian_rhs(phi, a_squared, beta=0.5):
    """Return F in i phi_t = F, in hbar=1 units."""
    slope = derivative(phi)
    return -beta * derivative(slope / np.sqrt(1 + a_squared * np.abs(slope) ** 2))


def graph_flow_check(rng):
    # F_x=(1,p1,p2), F_xx=(0,q1,q2), B=beta F_x cross F_xx / |F_x|^3.
    # Fixed-x graph gauge uses V=B-B_x F_x; V-B must be tangential.
    beta = 0.73
    slopes = []
    hessians = []
    for scale in (0.001, 0.1, 1.0, 10.0):
        slopes.append(scale * rng.normal(size=(1000, 2)))
        hessians.append(rng.normal(size=(1000, 2)))
    p = np.vstack(slopes)
    q = np.vstack(hessians)
    g = 1 + np.sum(p * p, axis=1)
    fx = np.column_stack((np.ones(p.shape[0]), p))
    fxx = np.column_stack((np.zeros(q.shape[0]), q))
    binormal = beta * np.cross(fx, fxx) / g[:, None] ** 1.5
    vertical = binormal - binormal[:, :1] * fx
    divergence = q / np.sqrt(g[:, None]) - p * np.sum(p * q, axis=1)[:, None] / g[:, None] ** 1.5
    graph = beta * np.column_stack((-divergence[:, 1], divergence[:, 0]))
    error = np.linalg.norm(vertical[:, 1:] - graph, axis=1)
    relative = error / np.maximum(1.0, np.linalg.norm(graph, axis=1))
    # Project graph velocity normally and verify the geometric velocity B.
    graph3 = np.column_stack((np.zeros(graph.shape[0]), graph))
    projection = graph3 - fx * (np.sum(graph3 * fx, axis=1) / g)[:, None]
    normal_error = np.max(np.linalg.norm(projection - binormal, axis=1))
    bad_no_gauge = np.max(np.linalg.norm(binormal[:, 1:] - graph, axis=1))
    bad_sign = np.max(np.linalg.norm(vertical[:, 1:] + graph, axis=1))
    tol = 2e-12
    return record(
        "d1_exact_graph_flow_equals_binormal_flow_up_to_tangential_gauge",
        np.max(relative) < tol and normal_error < tol and bad_no_gauge > 1e-3 and bad_sign > 1e-3,
        synthetic_samples=4000,
        dimensions={"base": 1, "ambient": 3, "normal": 2},
        dimensionless_coordinates=True,
        orientation="J(p1,p2)=(-p2,p1); B=beta F_x cross F_xx / |F_x|^3",
        equations={
            "graph": "U_t=beta J d_x(U_x/sqrt(1+|U_x|^2))",
            "gauge": "V=B-B_x F_x; P_normal(V)=B",
        },
        tolerance=tol,
        maximum_scaled_error=scalar(np.max(relative)),
        maximum_normal_projection_error=scalar(normal_error),
        negative_controls={
            "omit_tangential_gauge_maximum_error": scalar(bad_no_gauge),
            "reverse_orientation_without_reversing_B_maximum_error": scalar(bad_sign),
            "required_minimum_detected_error": 1e-3,
        },
        mathematical_scope="Pointwise identity for smooth curves remaining graphs, independent of a time integrator.",
    )


def plane_wave_check(rng):
    beta = 0.5
    rows = []
    errors = []
    for d in (1, 2, 3, 6):
        for _unused in range(24):
            k = rng.normal(size=d)
            amplitude = scalar(rng.uniform(0.1, 1.5))
            a_squared = scalar(rng.uniform(0.0, 1.2))
            xi = a_squared * amplitude**2 * np.dot(k, k)
            g = np.eye(d) + a_squared * amplitude**2 * np.outer(k, k)
            flux_matrix = np.sqrt(np.linalg.det(g)) * np.linalg.inv(g)
            measured_flux = flux_matrix @ k
            predicted_flux = k / np.sqrt(1 + xi)
            matrix_omega = beta * np.dot(k, measured_flux)
            formula_omega = beta * np.dot(k, k) / np.sqrt(1 + xi)
            error = np.linalg.norm(measured_flux - predicted_flux) / max(
                1.0, np.linalg.norm(predicted_flux)
            )
            errors.append(error)
            rows.append(
                {
                    "d": d,
                    "xi": scalar(xi),
                    "omega_matrix": scalar(matrix_omega),
                    "omega_formula": scalar(formula_omega),
                }
            )
    xi_values = np.array([0.04, 0.02, 0.01, 0.005])
    exact = 1 / np.sqrt(1 + xi_values)
    quadratic = 1 - xi_values / 2 + 3 * xi_values**2 / 8
    expansion_errors = np.abs(exact - quadratic)
    ratios = expansion_errors[:-1] / expansion_errors[1:]
    negative_control = abs(1 / np.sqrt(1.5) - 1)
    passed = (
        max(errors) < 2e-12 and np.all((ratios > 7.5) & (ratios < 8.1)) and negative_control > 0.1
    )
    return record(
        "exact_plane_wave_and_small_xi_dispersion_expansion",
        passed,
        synthetic_cases=len(rows),
        dimensions={"base_dimensions_tested": [1, 2, 3, 6], "normal": 2},
        units={
            "hbar": 1.0,
            "mass": 1.0,
            "beta": beta,
            "amplitude_dimension": "L^(-d/2)",
            "a_squared_dimension": "L^(d+2)",
            "xi_dimension": "1",
        },
        formula="omega=(hbar/(2m)) |k|^2 / sqrt(1+a^2 |A|^2 |k|^2)",
        tolerance=2e-12,
        maximum_scaled_flux_error=scalar(max(errors)),
        expansion={
            "formula": "(1+xi)^(-1/2)=1-xi/2+3xi^2/8+O(xi^3)",
            "xi": xi_values.tolist(),
            "absolute_errors": expansion_errors.tolist(),
            "error_ratios_on_halving_xi": ratios.tolist(),
            "accepted_ratio_interval": [7.5, 8.1],
        },
        negative_control={
            "replace_finite_scale_dispersion_by_linear_at_xi_0_5_error": negative_control,
            "required_minimum_detected_error": 0.1,
        },
        cases=rows,
    )


def matrix_expansion_check(rng):
    # Re(dpsi* tensor dpsi) has rank at most two, exactly as graph geometry requires.
    p = rng.normal(size=(3, 2))
    M = p @ p.T
    a_values = np.array([0.08, 0.04, 0.02, 0.01])
    errors = []
    for a in a_values:
        g = np.eye(3) + a**2 * M
        exact = np.sqrt(np.linalg.det(g)) * np.linalg.inv(g)
        quadratic = np.eye(3) + a**2 * (0.5 * np.trace(M) * np.eye(3) - M)
        errors.append(np.linalg.norm(exact - quadratic))
    ratios = np.array(errors[:-1]) / errors[1:]
    # In d=1 scaling both slope and Hessian by eps gives cubic correction to flow.
    p1, q1 = np.array([0.7, -0.4]), np.array([0.2, 0.9])
    eps_values = np.array([0.08, 0.04, 0.02, 0.01])
    cubic_errors = []
    for eps in eps_values:
        p_eps, q_eps = eps * p1, eps * q1
        g = 1 + np.dot(p_eps, p_eps)
        exact = q_eps / np.sqrt(g) - p_eps * np.dot(p_eps, q_eps) / g**1.5
        cubic_errors.append(np.linalg.norm(exact - q_eps))
    cubic_ratios = np.array(cubic_errors[:-1]) / cubic_errors[1:]
    return record(
        "graph_flux_and_linearization_remainder_orders",
        np.all((ratios > 15.0) & (ratios < 16.1))
        and np.all((cubic_ratios > 7.8) & (cubic_ratios < 8.1)),
        synthetic=True,
        dimensions={"matrix_base": 3, "normal": 2, "linearization_base": 1},
        formula="sqrt(det g) g^-1=I+a^2((tr M)/2 I-M)+O(a^4)",
        a=a_values.tolist(),
        matrix_errors=errors,
        matrix_error_ratios_on_halving_a=ratios.tolist(),
        expected_matrix_ratio=16,
        accepted_matrix_ratio_interval=[15.0, 16.1],
        linearization_formula="R=O(|U_x|^2 |U_xx|); common scaling U_x,U_xx by eps gives O(eps^3)",
        epsilon=eps_values.tolist(),
        linearization_errors=cubic_errors,
        linearization_error_ratios_on_halving_epsilon=cubic_ratios.tolist(),
        expected_linearization_ratio=8,
        accepted_linearization_ratio_interval=[7.8, 8.1],
    )


def galilean_check():
    amplitude = 0.8
    velocity = 1.3
    mass = hbar = 1.0
    k = mass * velocity / hbar
    a_squared = 0.6
    xi = a_squared * amplitude**2 * k**2
    omega_boost = mass * velocity**2 / (2 * hbar)
    omega_actual = omega_boost / np.sqrt(1 + xi)
    relative = 1 - 1 / np.sqrt(1 + xi)
    residual = abs(amplitude * (omega_boost - omega_actual))
    linear_control = abs(
        amplitude * (omega_boost - omega_boost / np.sqrt(1 + 0 * amplitude**2 * k**2))
    )
    return record(
        "finite_scale_standard_Galilean_boost_counterexample",
        residual > 1e-2 and linear_control < 1e-14,
        synthetic=True,
        dimensions={"base": 1, "ambient": 3},
        assumptions=[
            "Free field V=0",
            "Standard Galilean boost law with fixed mass m",
            "Positive fixed geometric scale a",
            "Nonzero amplitude and boost velocity",
        ],
        exact_counterexample="A constant rest solution boosted to A exp(i(mvx-mv^2t/2)/hbar) fails the finite-scale PDE because omega_required=mv^2/(2hbar)/sqrt(1+xi) while omega_boost=mv^2/(2hbar).",
        proof_scope="Failure for every a>0, A!=0, v!=0 under these assumptions; a different boost law or preferred frame is a different physical proposal.",
        units={"hbar": hbar, "mass": mass, "dimensionless_test_values": True},
        parameters={"amplitude": amplitude, "velocity": velocity, "a_squared": a_squared, "xi": xi},
        omega_standard_boost=omega_boost,
        omega_geometric_equation=scalar(omega_actual),
        normalized_dispersion_defect=scalar(relative),
        PDE_residual_amplitude=scalar(residual),
        required_minimum_detected_residual=1e-2,
        linear_scale_control_residual=scalar(linear_control),
        linear_control_tolerance=1e-14,
        inference="An exact symmetry obstruction in the finite-scale model, not an experimental exclusion by itself.",
    )


def spectator_check():
    ell = 0.7
    d, D = 1, 2
    a_d_squared = ell ** (d + 2)
    a_D_squared = ell ** (D + 2)
    Lx = 2 * np.pi
    lengths = [0.8, 2.4]
    k = 2.0
    amplitude = 1 / np.sqrt(Lx)
    rows = []
    for Ly in lengths:
        a_eff_squared = a_D_squared / Ly
        omega = 0.5 * k**2 / np.sqrt(1 + a_eff_squared * amplitude**2 * k**2)
        rows.append(
            {
                "Ly": Ly,
                "a_eff_squared": a_eff_squared,
                "ratio_to_standalone_a_d_squared": a_eff_squared / a_d_squared,
                "normalized_active_plane_wave_amplitude": scalar(amplitude),
                "omega": scalar(omega),
            }
        )
    N = 512
    x = np.arange(N) * Lx / N
    dx = Lx / N
    raw = (1 + 0.35 * np.cos(x) + 0.15 * np.sin(2 * x)) * np.exp(
        1j * (x + 0.4 * np.sin(x) + 0.15 * np.cos(2 * x))
    )
    phi = raw / np.sqrt(dx * np.sum(np.abs(raw) ** 2))
    derivatives = []
    formula_errors = []
    density_rates = []
    for Ly in lengths:
        eff = a_D_squared / Ly
        active_F = graph_hamiltonian_rhs(phi, eff)
        # Direct two-dimensional product construction: y gradient is exactly zero.
        psi = phi / np.sqrt(Ly)
        direct_F = graph_hamiltonian_rhs(psi, a_D_squared)
        formula_errors.append(l2(np.sqrt(Ly) * direct_F - active_F, dx))
        dotphi = -1j * active_F
        derivatives.append(dotphi)
        density_rates.append(2 * np.real(np.conj(phi) * dotphi))
    delta = derivatives[0] - derivatives[1]
    best_global_phase_rate = scalar(np.real(dx * np.vdot(1j * phi, delta)))
    projective_delta = delta - 1j * best_global_phase_rate * phi
    density_delta = density_rates[0] - density_rates[1]
    zero_scale_delta = -1j * graph_hamiltonian_rhs(phi, 0.0) - (
        -1j * graph_hamiltonian_rhs(phi, 0.0)
    )
    projective_norm = l2(projective_delta, dx)
    density_norm = l2(density_delta, dx)
    conservation_error = max(abs(dx * np.sum(rate)) for rate in density_rates)
    return record(
        "uniform_spectator_volume_changes_active_product_state_evolution",
        max(formula_errors) < 1e-11
        and projective_norm > 1e-4
        and density_norm > 1e-4
        and conservation_error < 1e-11
        and l2(zero_scale_delta, dx) < 1e-14,
        synthetic=True,
        dimensions={"active_base": d, "spectator_base": D - d, "composite_base": D, "normal": 2},
        units={
            "ell_dimension": "L",
            "a_d_squared_dimension": "L^(d+2)",
            "a_D_squared_dimension": "L^(D+2)",
            "spectator_volume_dimension": "L^(D-d)",
            "a_eff_squared_dimension": "L^(d+2)",
            "dimensionless_numeric_length_unit": True,
        },
        assumptions=[
            "Product state psi(x,y)=phi(x)/sqrt(Ly)",
            "Uniform periodic spectator",
            "Same mass and Euclidean base metric",
            "Dimension-dependent prescription a_n^2=ell^(n+2)",
            "No interaction potential",
        ],
        exact_formula="a_eff^2=a_D^2/Ly; in D=d+s, a_eff^2=ell^(D+2)/V_s, so a_eff^2/a_d^2=ell^s/V_s",
        ell=ell,
        standalone_a_d_squared=a_d_squared,
        composite_a_D_squared=a_D_squared,
        plane_wave_cases=rows,
        plane_wave_frequency_difference=abs(rows[0]["omega"] - rows[1]["omega"]),
        plane_wave_caveat="For a single plane wave the frequency difference is a global phase; the non-plane-wave check below removes this ambiguity.",
        non_plane_wave={
            "grid_points": N,
            "active_interval_length": Lx,
            "normalization_error": scalar(abs(dx * np.sum(np.abs(phi) ** 2) - 1)),
            "direct_product_vs_effective_equation_L2_errors": formula_errors,
            "equation_tolerance": 1e-11,
            "best_global_phase_rate_removed": best_global_phase_rate,
            "projective_tangent_difference_L2": projective_norm,
            "position_density_time_derivative_difference_L2": density_norm,
            "required_minimum_detected_difference": 1e-4,
            "integrated_density_time_derivative_maximum_absolute_error": scalar(conservation_error),
            "conservation_tolerance": 1e-11,
        },
        zero_scale_control_projective_difference_L2=l2(zero_scale_delta, dx),
        inference="Failure of spectator independence and the naive tensor-product composition prescription. This does not, by itself, prove an operational faster-than-light signalling protocol.",
    )


def variational_check():
    N = 512
    length = 2 * np.pi
    dx = length / N
    x = np.arange(N) * dx
    phi = (0.4 + 0.2 * np.cos(x)) * np.exp(1j * (x + 0.3 * np.sin(2 * x)))
    direction = 0.15 * np.cos(3 * x) + 0.1j * np.sin(2 * x)
    a_squared = 0.3

    def energy(f):
        return scalar(
            dx * np.sum((np.sqrt(1 + a_squared * np.abs(derivative(f)) ** 2) - 1) / a_squared)
        )

    rhs = graph_hamiltonian_rhs(phi, a_squared)
    predicted = scalar(2 * np.real(dx * np.vdot(direction, rhs)))
    eps = 1e-5
    finite_difference = (energy(phi + eps * direction) - energy(phi - eps * direction)) / (2 * eps)
    error = abs(predicted - finite_difference)
    norm_rate = scalar(2 * np.real(dx * np.vdot(phi, -1j * rhs)))
    # Missing Wirtinger factor 1/2 is a useful independent negative control.
    wrong_factor_error = abs(2 * predicted - finite_difference)
    return record(
        "finite_scale_action_directional_variation_and_instantaneous_norm",
        error < 1e-8 and abs(norm_rate) < 1e-11 and wrong_factor_error > 1e-4,
        synthetic=True,
        dimensions={"base": 1, "normal": 2},
        units={"hbar": 1.0, "mass": 1.0},
        energy="H=(hbar^2/(m a^2)) integral (sqrt(1+a^2|phi_x|^2)-1) dx",
        directional_derivative_identity="dH[direction]=2 Re integral conjugate(direction) F dx, where i hbar phi_t=F",
        periodic_grid_points=N,
        finite_difference_step=eps,
        predicted_directional_derivative=predicted,
        direct_energy_directional_derivative=finite_difference,
        derivative_absolute_error=error,
        derivative_tolerance=1e-8,
        instantaneous_norm_time_derivative=norm_rate,
        norm_tolerance=1e-11,
        negative_control_wrong_factor_error=wrong_factor_error,
        negative_control_required_minimum_error=1e-4,
        scope="One smooth synthetic periodic state and direction; no claim of global existence or long-time numerical conservation.",
    )


def scalar_mirror_check(rng):
    n = 64
    profile = np.cumsum(rng.normal(size=(n, 3)), axis=0) / np.sqrt(n)
    weights = rng.uniform(0.05, 1.0, n)
    weights /= weights.sum()
    Q = np.diag([-1.0, 1.0, 1.0])
    mirror = profile @ Q.T
    shifted = profile.copy()
    shifted[5] += [0.7, -0.3, 0.2]
    qs = np.array([0.0, 0.2, 0.7, 1.4, 3.0, 7.0])

    def intensity(points):
        distance = np.linalg.norm(points[:, None, :] - points[None, :, :], axis=2)
        return [
            scalar(np.sum(weights[:, None] * weights[None, :] * np.sinc(q * distance / np.pi)))
            for q in qs
        ]

    original_I = np.array(intensity(profile))
    mirror_I = np.array(intensity(mirror))
    perturbed_I = np.array(intensity(shifted))
    parity_error = scalar(np.max(np.abs(original_I - mirror_I)))
    deformation_error = scalar(np.max(np.abs(original_I - perturbed_I)))
    return record(
        "isotropic_scalar_intensity_is_exactly_mirror_parity_blind",
        parity_error < 1e-13 and deformation_error > 1e-5 and abs(original_I[0] - 1) < 1e-13,
        synthetic=True,
        dimensions={"profile_ambient": 3},
        points=n,
        positive_normalized_weights=True,
        formula="I_iso(q)=sum_ij w_i w_j sinc(q|r_i-r_j|)",
        proof="For any orthogonal Q, including det(Q)=-1, |Qr_i-Qr_j|=|r_i-r_j|. Therefore I_iso is identical at every q, exactly, not only to leading order.",
        q=qs.tolist(),
        original_intensity=original_I.tolist(),
        mirror_intensity=mirror_I.tolist(),
        tolerance=1e-13,
        maximum_mirror_error=parity_error,
        negative_control_geometric_deformation_intensity_error=deformation_error,
        negative_control_required_minimum_detected_error=1e-5,
        inference="This observable cannot identify chirality or torsion sign of mirror-related profiles; a parity-sensitive measurement requires additional response structure.",
    )


def ensemble_check():
    # Exact two-mode solutions: only the k mode contributes to the graph slope.
    length = 2 * np.pi
    N = 256
    dx = length / N
    x = np.arange(N) * dx
    k = 3
    p = 0.2
    a_squared = 0.8
    beta = 0.5
    time = 1.2
    f0 = np.ones(N, dtype=complex) / np.sqrt(length)
    fk = np.exp(1j * k * x) / np.sqrt(length)

    def omega(r, a2=a_squared):
        return beta * k**2 / np.sqrt(1 + a2 * r * k**2 / length)

    w1, w2 = omega(1 - p), omega(p)
    chi1 = np.sqrt(p) * f0 + np.sqrt(1 - p) * np.exp(-1j * w1 * time) * fk
    chi2 = np.sqrt(1 - p) * f0 - np.sqrt(p) * np.exp(-1j * w2 * time) * fk
    lhs1 = w1 * np.sqrt(1 - p) * np.exp(-1j * w1 * time) * fk
    lhs2 = -w2 * np.sqrt(p) * np.exp(-1j * w2 * time) * fk
    residual1 = l2(lhs1 - graph_hamiltonian_rhs(chi1, a_squared), dx)
    residual2 = l2(lhs2 - graph_hamiltonian_rhs(chi2, a_squared), dx)
    overlap = dx * np.vdot(chi1, chi2)
    predicted_overlap = np.sqrt(p * (1 - p)) * (1 - np.exp(1j * (w1 - w2) * time))
    rho0k = np.sqrt(p * (1 - p)) / 2 * (np.exp(1j * w1 * time) - np.exp(1j * w2 * time))
    c1 = np.array([np.sqrt(p), np.sqrt(1 - p) * np.exp(-1j * w1 * time)])
    c2 = np.array([np.sqrt(1 - p), -np.sqrt(p) * np.exp(-1j * w2 * time)])
    density_matrix = (np.outer(c1, c1.conj()) + np.outer(c2, c2.conj())) / 2
    initial_c1 = np.array([np.sqrt(p), np.sqrt(1 - p)])
    initial_c2 = np.array([np.sqrt(1 - p), -np.sqrt(p)])
    initial_matrix = (np.outer(initial_c1, initial_c1) + np.outer(initial_c2, initial_c2)) / 2
    initial_error = np.max(np.abs(initial_matrix - np.eye(2) / 2))
    position_density = (np.abs(chi1) ** 2 + np.abs(chi2) ** 2) / 2
    spectral_position_density = np.ones(N) / length
    position_difference = scalar(np.max(np.abs(position_density - spectral_position_density)))
    predicted_difference = scalar(2 * abs(rho0k) / length)
    linear_overlap = np.sqrt(p * (1 - p)) * (
        1 - np.exp(1j * (omega(1 - p, 0) - omega(p, 0)) * time)
    )
    equal_weight_overlap = 0.5 * (1 - np.exp(1j * (omega(0.5) - omega(0.5)) * time))
    eigenvalues = np.linalg.eigvalsh(density_matrix)
    return record(
        "exact_two_mode_branchwise_ensemble_decomposition_counterexample",
        max(residual1, residual2) < 2e-10
        and abs(overlap - predicted_overlap) < 1e-12
        and abs(density_matrix[0, 1] - rho0k) < 1e-12
        and initial_error < 1e-14
        and abs(rho0k) > 1e-3
        and position_difference > 1e-3
        and abs(linear_overlap) < 1e-14
        and abs(equal_weight_overlap) < 1e-14,
        synthetic=True,
        dimensions={"base": 1, "normal": 2, "exact_mode_subspace": 2},
        assumptions=[
            "Deterministic pure-state graph flow",
            "Statistical mixtures evolved branch by branch",
            "Born expectation rule for the resulting ensemble",
            "No alternative nonlinear density-operator dynamics supplied",
        ],
        normalization="f0=1/sqrt(L), fk=exp(ikx)/sqrt(L) on a periodic circle, k an allowed mode",
        exact_solutions={
            "chi1": "sqrt(p) f0 + sqrt(1-p) exp(-i Omega(1-p)t) fk",
            "chi2": "sqrt(1-p) f0 - sqrt(p) exp(-i Omega(p)t) fk",
            "Omega(r)": "beta k^2/sqrt(1+a^2 r k^2/L)",
            "overlap": "sqrt(p(1-p)) [1-exp(i(Omega(1-p)-Omega(p))t)]",
            "rho_0k": "sqrt(p(1-p))/2 [exp(i Omega(1-p)t)-exp(i Omega(p)t)]",
        },
        parameters={
            "L": length,
            "k": k,
            "p": p,
            "a_squared": a_squared,
            "beta": beta,
            "time": time,
        },
        initial_ensemble_matrix_error_from_identity_over_2=scalar(initial_error),
        exact_PDE_residual_L2=[residual1, residual2],
        PDE_tolerance=2e-10,
        overlap={
            "real": scalar(overlap.real),
            "imaginary": scalar(overlap.imag),
            "magnitude": scalar(abs(overlap)),
            "formula_error": scalar(abs(overlap - predicted_overlap)),
        },
        rho0k={
            "real": scalar(rho0k.real),
            "imaginary": scalar(rho0k.imag),
            "magnitude": scalar(abs(rho0k)),
            "matrix_formula_error": scalar(abs(density_matrix[0, 1] - rho0k)),
        },
        density_matrix_eigenvalues=eigenvalues.tolist(),
        trace_distance_from_spectral_mixture=scalar(abs(rho0k)),
        position_density_maximum_difference_on_grid=position_difference,
        position_density_continuous_supremum_prediction=predicted_difference,
        required_minimum_detected_coherence=1e-3,
        negative_controls={
            "a_zero_overlap": scalar(abs(linear_overlap)),
            "p_half_overlap": scalar(abs(equal_weight_overlap)),
            "tolerance": 1e-14,
        },
        inference="The same initial density matrix has distinct evolved position densities under the specified branchwise extension. This is an ensemble-consistency counterexample; an operational signalling conclusion requires explicit remote-preparation assumptions and a complete composite theory.",
    )


def rank_two_energy_check(rng):
    a_squared = 0.4
    lam1 = rng.uniform(0.0, 3.0, 500)
    lam2 = rng.uniform(0.0, 3.0, 500)
    trace = lam1 + lam2
    trace_squared_matrix = lam1**2 + lam2**2
    quartic_invariant = trace**2 / 8 - trace_squared_matrix / 4
    quartic_formula = -((lam1 - lam2) ** 2) / 8
    exact_energy = (np.sqrt((1 + a_squared * lam1) * (1 + a_squared * lam2)) - 1) / a_squared
    linear_energy = trace / 2
    gap = linear_energy - exact_energy
    gap_formula = (
        a_squared
        * (lam1 - lam2) ** 2
        / (
            4
            * (1 + a_squared * trace / 2 + np.sqrt((1 + a_squared * lam1) * (1 + a_squared * lam2)))
        )
    )
    balanced_errors = []
    unequal_errors = []
    for d in (2, 3, 6):
        for _unused in range(20):
            basis, unused_r = np.linalg.qr(rng.normal(size=(d, 2)))
            lam = scalar(rng.uniform(0.05, 2.0))
            slopes = np.sqrt(lam) * basis
            g = np.eye(d) + a_squared * slopes @ slopes.T
            flux = np.sqrt(np.linalg.det(g)) * np.linalg.inv(g) @ slopes
            balanced_errors.append(np.linalg.norm(flux - slopes))
            unequal = slopes @ np.diag([1.0, 1.4])
            gu = np.eye(d) + a_squared * unequal @ unequal.T
            unequal_flux = np.sqrt(np.linalg.det(gu)) * np.linalg.inv(gu) @ unequal
            unequal_errors.append(np.linalg.norm(unequal_flux - unequal))
    tolerance = 1e-12
    return record(
        "rank_two_quartic_energy_sign_exact_inequality_and_balanced_flux_cancellation",
        np.max(np.abs(quartic_invariant - quartic_formula)) < tolerance
        and np.max(np.abs(gap - gap_formula)) < tolerance
        and np.min(gap) > -tolerance
        and max(balanced_errors) < tolerance
        and min(unequal_errors) > 1e-5,
        synthetic=True,
        dimensions={"matrix_rank_maximum": 2, "base_dimensions_tested": [2, 3, 6], "normal": 2},
        units={"hbar": 1.0, "mass": 1.0},
        formulas={
            "rank_two_determinant": "det(I+a^2 M)=(1+a^2 lambda1)(1+a^2 lambda2)",
            "quartic_energy_density": "-hbar^2 a^2/(8m) (lambda1-lambda2)^2",
            "exact_inequality": "0 <= H_graph_density <= hbar^2/(2m) (lambda1+lambda2)",
            "gap": "H_linear-H_graph=hbar^2 a^2(lambda1-lambda2)^2/[4m(1+a^2(lambda1+lambda2)/2+sqrt((1+a^2lambda1)(1+a^2lambda2)))]",
            "balanced_flux": "If grad(u) dot grad(v)=0 and |grad(u)|=|grad(v)|, sqrt(det g) g^-1 grad(u or v)=grad(u or v)",
        },
        inequality_equality_condition="lambda1=lambda2, including zero; positivity follows from lambda_i>=0",
        random_eigenvalue_cases=500,
        quartic_identity_maximum_error=scalar(np.max(np.abs(quartic_invariant - quartic_formula))),
        exact_gap_formula_maximum_error=scalar(np.max(np.abs(gap - gap_formula))),
        smallest_energy_gap=scalar(np.min(gap)),
        balanced_gradient_cases=len(balanced_errors),
        balanced_flux_maximum_error=scalar(max(balanced_errors)),
        tolerance=tolerance,
        negative_control_unequal_gradient_smallest_flux_difference=scalar(min(unequal_errors)),
        negative_control_required_minimum_detected_difference=1e-5,
        inference="A finite scale need not produce a residue in every state. Balanced rank-two gradients cancel the exact flux correction; global dynamical persistence of that constraint is a separate question.",
    )


def run_checks(seed=SEED):
    """Independent per-run generator; no shared mutable replay state."""
    rng = np.random.default_rng(seed)
    checks = [
        graph_flow_check(rng),
        plane_wave_check(rng),
        matrix_expansion_check(rng),
        galilean_check(),
        spectator_check(),
        variational_check(),
        scalar_mirror_check(rng),
        ensemble_check(),
        rank_two_energy_check(rng),
    ]
    result = {
        "schema_version": "1.0",
        "artifact": "Independent SCM/ASTRA synthetic mathematical replay",
        "status": "PASS" if all(c["passed"] for c in checks) else "FAIL",
        "synthetic": True,
        "empirical_data": False,
        "replay_source_executed": True,
        "seed": seed,
        "runtime": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "numpy": np.__version__,
            "platform": platform.system(),
        },
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "passed_checks": sum(c["passed"] for c in checks),
        "total_checks": len(checks),
        "checks": checks,
        "scope_limits": [
            "Replay checks establish identities and counterexamples for the specified model; they do not confirm that the model describes electrons.",
            "The chosen dimensionless synthetic values are demonstration parameters, not fitted physical constants or experimental bounds.",
            "Only the listed numerical replay checks are executed; no manuscript experiments are run.",
            "No PDE time integration, global existence theorem, no-signalling completion, or empirical data reanalysis is claimed.",
            "Mirror identity is exact under orthogonal transformations for isotropic scalar elastic intensity; it does not cover polarization-dependent or parity-violating response operators.",
        ],
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="replay_results.json")
    args = parser.parse_args()
    result = run_checks()
    checks = result["checks"]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": result["status"],
                "passed_checks": result["passed_checks"],
                "total_checks": result["total_checks"],
                "output": str(output.resolve()),
            }
        )
    )
    if result["status"] != "PASS":
        for check in checks:
            if not check["passed"]:
                print("FAILED: " + check["name"], file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
