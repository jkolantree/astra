"""Finite report validation; no scientific imports and no inferred empirical status."""

WKI_COUNTS = {
    "graph_gauge_equals_displayed_PDE": 3,
    "graph_growth_equals_Hasimoto_NLS_growth": 1,
    "maximum_growth_equals_beta_curvature_squared_over_two": 1,
    "normalized_maximum_growth": 1,
    "shared_nuisance_fisher_complement": 1,
    "time_varying_storage_chain_rule": 1,
}


def validate_wki(
    report: object, source_sha256: str, optimization_level: int, failed_group: str | None = None
) -> bool:
    if failed_group is not None and failed_group not in WKI_COUNTS:
        raise ValueError("Unknown fault group")
    if not isinstance(report, dict) or report.get("status") != (
        "PASS" if failed_group is None else "FAIL"
    ):
        raise ValueError("Wrong WKI status")
    if (
        type(report.get("total_checks")) is not int
        or report["total_checks"] != 6
        or type(report.get("passed_checks")) is not int
        or report["passed_checks"] != (6 if failed_group is None else 5)
    ):
        raise ValueError("Wrong WKI counts")
    if (
        report.get("script_sha256") != source_sha256
        or type(report.get("optimization_level")) is not int
        or report["optimization_level"] != optimization_level
    ):
        raise ValueError("WKI source or optimization identity mismatch")
    if any(
        report.get(k) != v
        for k, v in {"python": "3.12.14", "sympy": "1.14.0", "mpmath": "1.3.0"}.items()
    ):
        raise ValueError("WKI runtime mismatch")
    checks = report.get("checks")
    if not isinstance(checks, dict) or set(checks) != set(WKI_COUNTS):
        raise ValueError("Exactly the six named WKI groups are required")
    for name, count in WKI_COUNTS.items():
        entry = checks[name]
        expected = ["0"] * count
        if name == failed_group:
            expected[0] = "1"
        if (
            not isinstance(entry, dict)
            or entry.get("residuals") != expected
            or entry.get("passed") is not (name != failed_group)
        ):
            raise ValueError("Unexpected residuals or pass flag: " + name)
        if not isinstance(entry.get("scope"), str) or not entry["scope"].strip():
            raise ValueError("Missing WKI scope")
    if (
        checks["normalized_maximum_growth"].get("computed_value") != "1/8"
        or checks["shared_nuisance_fisher_complement"].get("computed_value") != "1/(sigma2 + tau2)"
    ):
        raise ValueError("Unexpected computed value")
    return True
