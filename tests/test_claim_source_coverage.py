from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft7Validator, FormatChecker

from tools.build_claim_source_coverage import (
    DEFAULT_OUTPUT,
    ROOT,
    SCHEMA_PATH,
    build_record,
)


def test_claim_source_coverage_draft_matches_deterministic_generator() -> None:
    expected = json.loads(DEFAULT_OUTPUT.read_text(encoding="utf-8"))
    actual = build_record(ROOT)
    assert actual == expected


def test_claim_source_coverage_draft_matches_schema() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    record = json.loads(DEFAULT_OUTPUT.read_text(encoding="utf-8"))
    Draft7Validator(schema, format_checker=FormatChecker()).validate(record)


def test_claim_source_coverage_preserves_structural_unknowns() -> None:
    record = json.loads(DEFAULT_OUTPUT.read_text(encoding="utf-8"))
    summary = record["summary"]

    assert record["status"] == "maintenance_draft"
    assert record["reference_release"]["version"] == "1.0.6"
    assert summary["claim_count"] == 26
    assert summary["claims_with_support"] == 26
    assert summary["claims_with_current_path_support"] == 26
    assert summary["source_records_with_admitted_hash"] == 0
    assert summary["source_records_with_retrieval_date"] == 0
    assert "VERIFY-C019" in summary["claims_without_limitations"]
    external_links = [
        link
        for claim in record["claims"]
        for link in claim["source_links"]
        if link["kind"] == "external_record"
    ]
    assert external_links
    assert all(link["entailment_status"] == "not_reverified" for link in external_links)


def test_claim_source_coverage_internal_hashes_match_files() -> None:
    record = json.loads(DEFAULT_OUTPUT.read_text(encoding="utf-8"))
    for claim in record["claims"]:
        for link in claim["source_links"]:
            path = link["admitted_path"]
            if path is None:
                continue
            assert Path(ROOT / path).is_file()
            assert link["admitted_sha256"] == _sha256(ROOT / path)


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()
