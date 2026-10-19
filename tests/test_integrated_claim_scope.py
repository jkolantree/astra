"""Public scoped claims retain limitations without private intake metadata."""

import ast
import json
import unittest
from pathlib import Path

from integrated_case import build_contracts

ROOT = Path(__file__).resolve().parents[1]


class PublicClaimScopeTests(unittest.TestCase):
    def setUp(self):
        self.rows = json.loads((ROOT / "docs/integrated-core/claims.json").read_text())["claims"]
        self.keyed = {row["claim_id"]: row for row in self.rows}

    def test_exact_claim_coverage_and_no_empirical_promotion(self):
        self.assertEqual(len(self.rows), 93)
        self.assertEqual(len(self.keyed), 93)
        for row in self.rows:
            for key in (
                "empirical_admission",
                "novelty_priority_established",
                "whole_source_claim_validated",
            ):
                self.assertIs(row[key], False)
            self.assertEqual(
                row["comparative_publication_status"],
                "NO_EMPIRICAL_SUPERIORITY_ADMITTED",
            )
            self.assertNotIn("source_member", row)
            self.assertNotIn("source_sha256", row)

    def test_crosswalk_statements_support_and_tests_match(self):
        mapping = json.loads((ROOT / "docs/integrated-core/claim-test-map.json").read_text())[
            "mapping"
        ]
        self.assertEqual(set(mapping), set(self.keyed))
        for key, row in self.keyed.items():
            self.assertEqual(mapping[key]["scope"], row["statement"])
            self.assertEqual(mapping[key]["tests"], row["tests"])
            self.assertEqual(mapping[key]["candidate_support"], row["candidate_support"])

    def test_every_public_check_locator_resolves(self):
        locators = {locator for row in self.rows for locator in row["tests"]}
        self.assertTrue(locators)
        for locator in sorted(locators):
            with self.subTest(locator=locator):
                if "::" in locator:
                    filename, name = locator.split("::", 1)
                    path = ROOT / filename
                    self.assertTrue(path.is_file())
                    self.assertTrue(path.resolve().is_relative_to(ROOT))
                    tree = ast.parse(path.read_text())
                    if filename == "scripts/wki_check_algebra.py":
                        declarations = [
                            node.value
                            for node in tree.body
                            if isinstance(node, ast.Assign)
                            and any(
                                isinstance(target, ast.Name)
                                and target.id == "EXPECTED_RESIDUAL_COUNTS"
                                for target in node.targets
                            )
                        ]
                        self.assertEqual(len(declarations), 1)
                        self.assertIn(name, ast.literal_eval(declarations[0]))
                        build = next(
                            node
                            for node in tree.body
                            if isinstance(node, ast.FunctionDef) and node.name == "build_checks"
                        )
                        returned_groups = [
                            key.value
                            for node in ast.walk(build)
                            if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict)
                            for key in node.value.keys
                            if isinstance(key, ast.Constant) and isinstance(key.value, str)
                        ]
                        self.assertIn(name, returned_groups)
                    else:
                        self.assertEqual(filename, "scripts/scm_replay_checks.py")
                        self.assertIn(
                            name,
                            {node.name for node in tree.body if isinstance(node, ast.FunctionDef)},
                        )
                else:
                    module, class_name, method = locator.split(".")
                    path = ROOT / "tests" / (module + ".py")
                    self.assertTrue(path.is_file())
                    tree = ast.parse(path.read_text())
                    classes = {
                        node.name: node for node in tree.body if isinstance(node, ast.ClassDef)
                    }
                    self.assertIn(class_name, classes)
                    self.assertIn(
                        method,
                        {
                            node.name
                            for node in classes[class_name].body
                            if isinstance(node, ast.FunctionDef)
                        },
                    )
                    self.assertTrue(method.startswith("test_"))

    def test_contract_references_resolve(self):
        for contract in build_contracts():
            for key in contract.source_claim_keys:
                self.assertIn(key, self.keyed)

    def test_uncovered_wave_results_stay_uncovered(self):
        for key in (
            "wki_correction:CVG-06",
            "wki_correction:CVG-07",
            "wki_correction:CVG-08–12",
        ):
            self.assertEqual(self.keyed[key]["tests"], [])
        self.assertIn("1/8", self.keyed["wki_correction:CVG-04"]["statement"])
        self.assertTrue(self.keyed["wki_correction:CVG-03"]["prior_art_demotion_retained"])

    def test_six_scoped_limitations_retained(self):
        rows = json.loads((ROOT / "docs/integrated-core/limitations.json").read_text())["findings"]
        self.assertEqual(
            {row["id"] for row in rows},
            {"CORE-01", "CORE-03", "CORE-09", "CORE-11", "ILG-04", "ILG-C01"},
        )


if __name__ == "__main__":
    unittest.main()
