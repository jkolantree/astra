import ast
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import sympy as sp

from scripts import wki_check_algebra as candidate


class WkiRegressions(unittest.TestCase):
    def test_six_groups_eight_residuals(self):
        r = candidate.run_checks()
        self.assertEqual((r["status"], r["passed_checks"], r["total_checks"]), ("PASS", 6, 6))
        self.assertEqual(sum(len(c["residuals"]) for c in r["checks"].values()), 8)
        self.assertTrue(all(x == "0" for c in r["checks"].values() for x in c["residuals"]))

    def test_normalized_value_computed(self):
        self.assertEqual(
            candidate.run_checks()["checks"]["normalized_maximum_growth"]["computed_value"], "1/8"
        )

    def test_each_group_detects_nonzero_residual(self):
        for name in candidate.EXPECTED_RESIDUAL_COUNTS:
            with self.subTest(name=name):
                raw = candidate.build_checks()
                raw[name]["residuals"][0] += 1
                with patch.object(candidate, "build_checks", return_value=raw):
                    r = candidate.run_checks()
                self.assertEqual(r["status"], "FAIL")
                self.assertEqual(r["passed_checks"], 5)
                self.assertFalse(r["checks"][name]["passed"])

    def test_missing_extra_and_empty_groups_rejected(self):
        raw = candidate.build_checks()
        raw.pop(next(iter(raw)))
        with self.assertRaises(ValueError):
            candidate.evaluate_checks(raw)
        with self.assertRaises(ValueError):
            candidate.evaluate_checks({})
        raw = candidate.build_checks()
        raw["unreviewed"] = raw[next(iter(raw))]
        with self.assertRaises(ValueError):
            candidate.evaluate_checks(raw)

    def test_missing_component_rejected(self):
        raw = candidate.build_checks()
        raw["graph_gauge_equals_displayed_PDE"]["residuals"].pop()
        with self.assertRaises(ValueError):
            candidate.evaluate_checks(raw)

    def test_bad_expression_types_rejected(self):
        for bad in [True, "0", None]:
            raw = candidate.build_checks()
            raw["normalized_maximum_growth"]["residuals"][0] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                candidate.evaluate_checks(raw)

    def test_unresolved_equality_not_pass(self):
        raw = candidate.build_checks()
        raw["normalized_maximum_growth"]["residuals"][0] = sp.Symbol("unresolved")
        self.assertFalse(candidate.evaluate_checks(raw)["normalized_maximum_growth"]["passed"])

    def test_output_path_required(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as cm:
            candidate.main([])
        self.assertEqual(cm.exception.code, 2)

    def test_explicit_output_and_no_sibling_write(self):
        sibling = Path(candidate.__file__).with_name("algebra_checks.json")
        self.assertFalse(sibling.exists())
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            dest = Path(directory) / "report.json"
            with redirect_stdout(io.StringIO()):
                code = candidate.main(["--output", str(dest)])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(dest.read_text())["status"], "PASS")
        self.assertFalse(sibling.exists())

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            dest = Path(directory) / "report.json"
            dest.write_text("existing owner data")
            with redirect_stderr(io.StringIO()):
                code = candidate.main(["--output", str(dest)])
            self.assertEqual(code, 2)
            self.assertEqual(dest.read_text(), "existing owner data")

    def test_check_exception_has_error_report_and_nonzero_exit(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            dest = Path(directory) / "error.json"
            with (
                patch.object(
                    candidate, "build_checks", side_effect=RuntimeError("intentional control")
                ),
                redirect_stdout(io.StringIO()),
            ):
                code = candidate.main(["--output", str(dest)])
            self.assertEqual(code, 1)
            self.assertEqual(json.loads(dest.read_text())["status"], "ERROR")

    def test_wrong_identity_has_failure_report_and_nonzero_exit(self):
        raw = candidate.build_checks()
        raw["normalized_maximum_growth"]["residuals"][0] += 1
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            dest = Path(directory) / "failure.json"
            with (
                patch.object(candidate, "build_checks", return_value=raw),
                redirect_stdout(io.StringIO()),
            ):
                code = candidate.main(["--output", str(dest)])
            r = json.loads(dest.read_text())
            self.assertEqual(code, 1)
            self.assertEqual((r["status"], r["passed_checks"]), ("FAIL", 5))

    def test_no_assert_based_gate(self):
        tree = ast.parse(Path(candidate.__file__).read_text())
        self.assertFalse(any(isinstance(n, ast.Assert) for n in ast.walk(tree)))

    def test_existing_source_cannot_be_overwritten(self):
        p = Path(candidate.__file__)
        before = p.read_bytes()
        with redirect_stderr(io.StringIO()):
            code = candidate.main(["--output", str(p)])
        self.assertEqual(code, 2)
        self.assertEqual(p.read_bytes(), before)
