"""Six finite symbolic check groups with explicit outcomes.

This is not a proof-assistant certificate, PDE theorem, empirical validation or
novelty certificate. Run with --output pointing to a new report file.
Normal and optimized Python evaluate the same checks; no assert is a gate.
"""

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

import mpmath
import sympy as sp

EXPECTED_RESIDUAL_COUNTS = {
    "graph_gauge_equals_displayed_PDE": 3,
    "graph_growth_equals_Hasimoto_NLS_growth": 1,
    "maximum_growth_equals_beta_curvature_squared_over_two": 1,
    "normalized_maximum_growth": 1,
    "shared_nuisance_fisher_complement": 1,
    "time_varying_storage_chain_rule": 1,
}


def build_checks():
    """Construct the original eight equalities, grouped into six report entries."""
    beta, a, A, k, Q = sp.symbols("beta a A k Q", positive=True)
    s = a**2 * A**2 * k**2
    g = 1 + s
    curvature = a * A * k**2 / g
    p2 = Q**2 / g
    gamma2_graph = beta**2 * Q**2 * (k**2 * s - g * Q**2) / g**3
    gamma2_nls = beta**2 * p2 * (curvature**2 - p2)
    max_graph = beta * k**2 * s / (2 * g**2)
    max_nls = beta * curvature**2 / 2
    normalized = max_graph.subs({beta: 1, a: 1, A: 1, k: 1})

    ux, vx, uxx, vxx = sp.symbols("ux vx uxx vxx", real=True)
    gg = 1 + ux**2 + vx**2
    rx = sp.Matrix([1, ux, vx])
    rxx = sp.Matrix([0, uxx, vxx])
    raw = beta * rx.cross(rxx) / gg ** sp.Rational(3, 2)
    graph = raw - raw[0] * rx
    gx = 2 * (ux * uxx + vx * vxx)
    pde_u = -beta * (vxx / sp.sqrt(gg) - vx * gx / (2 * gg ** sp.Rational(3, 2)))
    pde_v = beta * (uxx / sp.sqrt(gg) - ux * gx / (2 * gg ** sp.Rational(3, 2)))

    sigma2, tau2 = sp.symbols("sigma2 tau2", positive=True)
    fisher = sp.Matrix([[1 / sigma2, 1 / sigma2], [1 / sigma2, 1 / sigma2 + 1 / tau2]])
    efficient = fisher[0, 0] - fisher[0, 1] ** 2 / fisher[1, 1]

    aa, b, damp, P, V, E, adot, bdot = sp.symbols(
        "aa b damp P V E adot bdot", real=True, nonzero=True
    )
    W = (V**2 + b * P**2) / (2 * aa)
    derivative = (
        sp.diff(W, P) * V
        + sp.diff(W, V) * (aa * E - damp * V - b * P)
        + sp.diff(W, aa) * adot
        + sp.diff(W, b) * bdot
    )
    pump = bdot * P**2 / (2 * aa) - adot * (V**2 + b * P**2) / (2 * aa**2)

    return {
        "graph_gauge_equals_displayed_PDE": {
            "residuals": [graph[0], graph[1] - pde_u, graph[2] - pde_v],
            "scope": "Local smooth graph chart; fixed orientation and tangential gauge.",
        },
        "graph_growth_equals_Hasimoto_NLS_growth": {
            "residuals": [gamma2_graph - gamma2_nls],
            "scope": "Equality of displayed real-growth expressions with p^2=Q^2/g; not a new dispersion derivation.",
        },
        "maximum_growth_equals_beta_curvature_squared_over_two": {
            "residuals": [max_graph - max_nls],
            "scope": "Equality of reported continuous-mode maximum formulas; no discrete-mode admissibility proof.",
        },
        "normalized_maximum_growth": {
            "residuals": [normalized - sp.Rational(1, 8)],
            "computed_value": str(normalized),
            "scope": "Substitution beta=a=A=k=1 in the reported maximum formula.",
        },
        "shared_nuisance_fisher_complement": {
            "residuals": [efficient - 1 / (sigma2 + tau2)],
            "computed_value": str(sp.simplify(efficient)),
            "scope": "Specified independent Gaussian noises and shared offset; no calibration or causal identification.",
        },
        "time_varying_storage_chain_rule": {
            "residuals": [derivative - (E * V - damp * V**2 / aa + pump)],
            "scope": "Finite scalar storage chain rule with signed coefficient work; no device or Maxwell PDE validation.",
        },
    }


def evaluate_checks(raw):
    """Fail on incomplete/malformed groups; unresolved equalities are not PASS."""
    if not isinstance(raw, dict) or set(raw) != set(EXPECTED_RESIDUAL_COUNTS):
        raise ValueError("Exactly the six declared check groups are required")
    checks = {}
    for name, count in EXPECTED_RESIDUAL_COUNTS.items():
        entry = raw[name]
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("residuals"), (list, tuple))
            or len(entry["residuals"]) != count
        ):
            raise ValueError("Incorrect residual count for " + name)
        if not isinstance(entry.get("scope"), str) or not entry["scope"].strip():
            raise ValueError("Explicit check scope required for " + name)
        if not all(isinstance(value, sp.Expr) for value in entry["residuals"]):
            raise ValueError("Symbolic expressions required for " + name)
        residuals = [sp.simplify(value) for value in entry["residuals"]]
        checks[name] = {
            "passed": all(value == sp.S.Zero for value in residuals),
            "residuals": [str(value) for value in residuals],
            "scope": entry["scope"],
        }
        if "computed_value" in entry:
            checks[name]["computed_value"] = entry["computed_value"]
    return checks


def run_checks():
    checks = evaluate_checks(build_checks())
    passed = sum(entry["passed"] for entry in checks.values())
    return {
        "schema_version": "1.1",
        "status": "PASS" if passed == len(EXPECTED_RESIDUAL_COUNTS) else "FAIL",
        "scope": "Six finite symbolic identity groups only; not novelty, empirical validation or external review.",
        "python": platform.python_version(),
        "sympy": sp.__version__,
        "mpmath": mpmath.__version__,
        "optimization_level": sys.flags.optimize,
        "total_checks": len(checks),
        "passed_checks": passed,
        "checks": checks,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "not_performed": [
            "Independent PDE integration",
            "Discrete-mode/boundary spectral analysis",
            "Proof-assistant verification",
            "External specialist review",
            "Fresh prior-art search",
            "Empirical calibration or validation",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="New report file in an existing directory; existing files are refused",
    )
    args = parser.parse_args(argv)
    try:
        # Exclusive creation prevents source overwrite or reuse of an old PASS.
        # A killed run leaves RUNNING/invalid JSON, never an old PASS.
        with args.output.open("x", encoding="utf-8") as report:
            json.dump({"schema_version": "1.1", "status": "RUNNING"}, report)
            report.flush()
            try:
                result = run_checks()
            except Exception as exc:
                result = {
                    "schema_version": "1.1",
                    "status": "ERROR",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            report.seek(0)
            report.truncate()
            json.dump(result, report, indent=2, allow_nan=False)
            report.write("\n")
            report.flush()
    except OSError as exc:
        print(
            json.dumps({"status": "ERROR", "error_type": type(exc).__name__, "error": str(exc)}),
            file=sys.stderr,
        )
        return 2
    print(
        json.dumps(
            {
                "status": result["status"],
                "passed_checks": result.get("passed_checks"),
                "total_checks": result.get("total_checks"),
            }
        )
    )
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
