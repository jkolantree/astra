import copy
import json
import unittest
from pathlib import Path

from admission import audit_bridges, validate_bridge


class AdmissionNegativeTests(unittest.TestCase):
    def setUp(self):
        self.records = json.loads(
            (
                Path(__file__).resolve().parents[1] / "data/integrated-core/bridge_contracts.json"
            ).read_text()
        )

    def test_schema_pass_never_confers_empirical_admission(self):
        a = audit_bridges(self.records)
        self.assertEqual(a["structural_pass_count"], 8)
        self.assertEqual(a["calibration_ready_count"], 0)
        self.assertEqual(a["empirical_admission_count"], 0)
        for key, value in [
            ("release_status", "stable"),
            ("framework_validation", "empirically-validated"),
        ]:
            r = copy.deepcopy(self.records[0])
            r[key] = value
            self.assertTrue(validate_bridge(r))

    def test_malformed_calibration_is_rejected_without_crashing(self):
        for bad in [None, [], 42, "verified"]:
            r = copy.deepcopy(self.records[0])
            r["calibration"] = bad
            self.assertTrue(validate_bridge(r))

    def test_query_does_not_replace_a_fog_coordinate(self):
        r = copy.deepcopy(self.records[0])
        r["fog"].pop("chronology")
        r["fog"]["query"] = r["query"]
        self.assertTrue(validate_bridge(r))

    def test_reused_contract_id_is_detected(self):
        a = audit_bridges([self.records[0], self.records[0]])
        self.assertEqual(a["structural_pass_count"], 1)
        self.assertIn("duplicate contract ID", a["results"][1]["errors"])


if __name__ == "__main__":
    unittest.main()
