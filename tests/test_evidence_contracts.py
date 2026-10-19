"""Malformed receipts must not count as detected scientific faults."""

import unittest

from evidence_contracts import WKI_COUNTS, validate_wki


def receipt(fault=None):
    groups = {
        k: {"residuals": ["0"] * n, "passed": k != fault, "scope": "deliberate validator fixture"}
        for k, n in WKI_COUNTS.items()
    }
    if fault:
        groups[fault]["residuals"][0] = "1"
    groups["normalized_maximum_growth"]["computed_value"] = "1/8"
    groups["shared_nuisance_fisher_complement"]["computed_value"] = "1/(sigma2 + tau2)"
    return {
        "status": "FAIL" if fault else "PASS",
        "total_checks": 6,
        "passed_checks": 5 if fault else 6,
        "script_sha256": "a" * 64,
        "optimization_level": 0,
        "python": "3.12.14",
        "sympy": "1.14.0",
        "mpmath": "1.3.0",
        "checks": groups,
    }


class EvidenceContractTests(unittest.TestCase):
    def test_empty_fault_report_cannot_pass(self):
        fault = next(iter(WKI_COUNTS))
        r = receipt(fault)
        r["checks"] = {}
        with self.assertRaises(ValueError):
            validate_wki(r, "a" * 64, 0, fault)

    def test_missing_or_extra_group_and_component_fail(self):
        for mutate in [
            lambda r: r["checks"].pop("normalized_maximum_growth"),
            lambda r: r["checks"].update(extra={}),
            lambda r: r["checks"]["graph_gauge_equals_displayed_PDE"]["residuals"].pop(),
        ]:
            r = receipt()
            mutate(r)
            with self.assertRaises(ValueError):
                validate_wki(r, "a" * 64, 0)

    def test_wrong_source_runtime_and_optimization_fail(self):
        for key, value in [
            ("script_sha256", "b" * 64),
            ("sympy", "other"),
            ("optimization_level", 1),
            ("passed_checks", True),
        ]:
            r = receipt()
            r[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_wki(r, "a" * 64, 0)

    def test_wrong_group_or_error_is_not_detected_fault(self):
        first, second = list(WKI_COUNTS)[:2]
        r = receipt(first)
        with self.assertRaises(ValueError):
            validate_wki(r, "a" * 64, 0, second)
        r["status"] = "ERROR"
        with self.assertRaises(ValueError):
            validate_wki(r, "a" * 64, 0, first)

    def test_complete_control_reports_are_accepted(self):
        for fault in [None, *WKI_COUNTS]:
            self.assertTrue(validate_wki(receipt(fault), "a" * 64, 0, fault))
