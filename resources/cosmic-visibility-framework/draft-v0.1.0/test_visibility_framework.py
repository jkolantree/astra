"""Contract tests for the unpromoted cosmic visibility framework draft."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_framework import (
    EXAMPLE,
    validate_example,
    validate_manifest,
    validate_pdf_identity,
    validate_record,
)


def test_example_is_utf8_canonical_json() -> None:
    raw = EXAMPLE.read_text(encoding="utf-8")
    parsed = json.loads(raw)
    assert raw == json.dumps(parsed, ensure_ascii=False, indent=2) + "\n"


def test_example_passes_fail_closed_contract() -> None:
    record = validate_example()
    assert record["status"] == "unpromoted_research_draft"
    assert record["certificate"]["result"] == "defer"
    assert {stage["chain_id"] for stage in record["visibility_chain"]} == {
        "filament-conversion",
        "martian-archive",
    }
    assert len(record["visibility_kernel"]["factors"]) >= 9


def test_manifest_binds_every_payload_file() -> None:
    validate_manifest()


def test_pdf_identity_binds_source_builder_and_artifacts() -> None:
    validate_pdf_identity()


def test_invalid_interval_is_rejected() -> None:
    record = copy.deepcopy(validate_example())
    interval_factor = next(
        factor for factor in record["visibility_kernel"]["factors"] if factor["value_kind"] == "interval"
    )
    interval_factor["interval"]["lower"] = 2.0
    interval_factor["interval"]["upper"] = 1.0
    with pytest.raises(ValueError, match="invalid interval"):
        validate_record(record)


def test_unknown_source_and_untyped_promotion_are_rejected() -> None:
    record = copy.deepcopy(validate_example())
    record["provenance"]["source_ids"].append("S999")
    with pytest.raises(ValueError, match="unknown source_ids"):
        validate_record(record)

    promoted = copy.deepcopy(validate_example())
    promoted["certificate"]["result"] = "pass_with_qualification"
    with pytest.raises(ValueError, match="method-only"):
        validate_record(promoted)


def test_no_nonstandard_schema_data_keyword_is_present() -> None:
    schema = (EXAMPLE.parent / "visibility_framework.schema.json").read_text(encoding="utf-8")
    assert "$data" not in schema
