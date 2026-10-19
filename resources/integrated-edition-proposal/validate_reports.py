"""Bounded payload checks using the unchanged WKI validator and exact SCM cases."""

import hashlib
import json
import math
from pathlib import Path

from evidence_contracts import validate_wki

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(integrated, scm, wki):
    def finite_tree(value):
        if isinstance(value, float):
            require(math.isfinite(value), "Non-finite numeric report value")
        elif isinstance(value, dict):
            for item in value.values(): finite_tree(item)
        elif isinstance(value, list):
            for item in value: finite_tree(item)

    for payload in (integrated, scm, wki): finite_tree(payload)
    require(integrated["status"] == "COMPLETED_SYNTHETIC"
            and integrated["synthetic"] is True
            and integrated["empirical_admission"] is False
            and integrated["core_release_promoted"] is False, "Wrong integration status")
    require(integrated["case_sha256"] == hashlib.sha256(
        (ROOT/"data/integrated-core/integrated_case.json").read_bytes()).hexdigest(), "Fixture identity")
    require(abs(integrated["transport"]["mass_closure_residual_kg"]) <= 1e-12,
            "Mass ledger residual")
    require(abs(integrated["transport"]["sppt_generator_max_residual"]) <= 1e-12,
            "SPPT generator residual")
    a = integrated["archive"]
    fixture = json.loads((ROOT/"data/integrated-core/integrated_case.json").read_text())
    observations = integrated["observations"]
    require(isinstance(observations, list) and len(observations) == len(fixture["times_s"])-1,
            "Exact nonempty exposure-bin inventory required")
    require(all(isinstance(o.get("expected_counts"), list) and len(o["expected_counts"]) == 1
                and type(o["expected_counts"][0]) in (int, float) and o["expected_counts"][0] >= 0
                for o in observations), "Finite scalar expected count required per bin")
    total = sum(o["expected_counts"][0] for o in observations)
    require(math.isfinite(total), "Expected-count sum overflow")
    require(all(type(a[k]) in (int, float) and a[k] >= 0 for k in
                ["stock", "erased", "expected_input_records"]), "Nonnegative numeric record ledger")
    require(abs(total-a["expected_input_records"]) <= 1e-12 * max(1.0,total),
            "Observation / archive first-moment mismatch")
    require(abs(total-a["stock"]-a["erased"]) <= 1e-10 * max(1.0,total),
            "Independent record ledger closure")
    require(abs(a["balance_residual"]) <= 1e-10 * max(1.0, a["expected_input_records"])
            and a["physical_mass_kg"] is None, "Expected record ledger")
    require(all(o["empirical_admission"] is False and o["no_record_probability"] is None
                and o["status"] == "first-moment-only" for o in observations),
            "Observation scope changed")
    require(scm["status"] == "PASS" and scm["total_checks"] == scm["passed_checks"] == 9
            and len(scm["checks"]) == 9 and all(c["passed"] is True for c in scm["checks"]),
            "SCM family failure")
    require(scm["synthetic"] is True and scm["empirical_data"] is False
            and scm["replay_source_executed"] is True, "SCM evidence class")
    require(scm["script_sha256"] == hashlib.sha256(
        (ROOT/"scripts/scm_replay_checks.py").read_bytes()).hexdigest(), "SCM source hash")
    require(scm["runtime"]["python"] == "3.12.10" and scm["runtime"]["numpy"] == "2.3.5",
            "SCM runtime route")
    expected = json.loads((PACKAGE/"SCM_CASE_IDENTITIES.json").read_text())
    require([c["name"] for c in scm["checks"]] == expected, "SCM case inventory mismatch")
    validate_wki(wki, hashlib.sha256((ROOT/"scripts/wki_check_algebra.py").read_bytes()).hexdigest(), 0)


def main():
    outputs = PACKAGE/"generated"
    validate(*(json.loads((outputs/name).read_text()) for name in
               ["integrated-case.json", "scm-checks.json", "wki-checks.json"]))
    print("Synthetic status, ledger residuals, nine named SCM families and unchanged WKI validator: PASS")


if __name__ == "__main__":
    main()
