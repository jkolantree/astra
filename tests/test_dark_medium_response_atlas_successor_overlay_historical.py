from __future__ import annotations

import hashlib
import json
from pathlib import Path

from jsonschema import Draft7Validator, FormatChecker

from tools.build_dark_medium_response_atlas_successor_overlay import (
    PACKAGE_ROSTER_SCOPE,
    serialize_file_entries,
)

ROOT = Path(__file__).resolve().parents[1]
S1_RECORD = ROOT / "evidence" / "dark_medium_response_atlas_successor_overlay_s1.json"
S1_SCHEMA = ROOT / "schemas" / "dark-medium-response-atlas-successor-overlay-s1.schema.json"
S1_GENERATOR = ROOT / "tools" / "build_dark_medium_response_atlas_successor_overlay.py"
S1_TEST = ROOT / "tests" / "test_dark_medium_response_atlas_successor_overlay.py"

EXPECTED_FIXED_HASHES = {
    S1_RECORD: "9d879d9a638dd5882aa546914204ab4b1ea40221adcdfa11f3820dd583628291",
    S1_SCHEMA: "4a4433b83a62dfd18ea65b761372888a1ab67e5dac1ec8b5386edcb7d9e4e76d",
    S1_GENERATOR: "e4f4255750fa72a25b4353564c4ecaec68a56408aaa761219b339c8bab546efa",
    S1_TEST: "10a775fe4b928a45255a59de2ead69dd01e690db6325d546c86f2c4c5554d8d6",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _record() -> dict[str, object]:
    value = json.loads(S1_RECORD.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_historical_s1_program_and_record_bytes_are_fixed() -> None:
    assert {path: _sha256(path) for path in EXPECTED_FIXED_HASHES} == EXPECTED_FIXED_HASHES


def test_historical_s1_record_still_satisfies_its_fixed_schema() -> None:
    schema = json.loads(S1_SCHEMA.read_text(encoding="utf-8"))
    Draft7Validator(schema, format_checker=FormatChecker()).validate(_record())


def test_historical_s1_package_bytes_and_aggregate_are_self_consistent() -> None:
    record = _record()
    package = record["package"]
    assert isinstance(package, dict)
    entries = package["files"]
    assert isinstance(entries, list)
    for entry in entries:
        assert isinstance(entry, dict)
        path = ROOT / str(entry["path"])
        assert path.is_file()
        assert path.stat().st_size == entry["bytes"]
        assert _sha256(path) == entry["sha256"]
    payload = serialize_file_entries(
        domain=b"PACKAGE-ROSTER",
        scope=PACKAGE_ROSTER_SCOPE,
        entries=entries,
    )
    aggregate = package["aggregate"]
    assert isinstance(aggregate, dict)
    assert len(payload) == aggregate["canonical_bytes"]
    assert hashlib.sha256(payload).hexdigest() == aggregate["sha256"]


def test_historical_s1_projection_is_recorded_not_replayed_on_current_main() -> None:
    record = _record()
    assert record["base_identity"] == {
        "commit": "f8b32ef0af9cb6804f256490b4daafbdba43740e",
        "relationship": "audited_repository_base",
        "tree": "251895700cdfc80addf180d46178b5aa8c43528c",
    }
    projection = record["source_projection"]
    assert isinstance(projection, dict)
    assert projection["sha256"] == (
        "e59d518f7892d94b0f7a035879b3bb16c1b0bc9cb95c83bc4f038ab36052bdba"
    )
    assert record["package"]["aggregate"]["sha256"] == (
        "5993bcf52c786a1b48f05e303228b99ae5e7f22fd879058efd2af12b754abaf5"
    )
    assert record["predecessor_overlay"]["sha256"] == (
        "a655277bb9f241d8aa28a3ab11eacd03ae097befa5650c02dc50a66385555fd9"
    )
