from __future__ import annotations

import copy
import hashlib
import json
import platform
import struct
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft7Validator, FormatChecker

from tools.build_claim_source_coverage import (
    AUTHORITATIVE_RUNTIME_IDENTITY,
    BASE_COMMIT,
    BASE_TREE,
    DEFAULT_OUTPUT,
    FROZEN_OUTPUT,
    IDENTITY_CLOSURE_PATHS,
    LOCK_PATH,
    MILESTONE_SOURCE_PATHS,
    RELEASE_COMMIT,
    RELEASE_TAG_OBJECT,
    RELEASE_TREE,
    ROOT,
    RUNTIME_CLASSIFICATION,
    RUNTIME_IDENTITY,
    RUNTIME_PATH,
    SCHEMA_PATH,
    SOURCE_PROJECTION_SCHEME,
    SOURCE_PROJECTION_SCOPE,
    SOURCE_PROJECTION_SERIALIZATION,
    build_record,
    build_source_projection,
    repository_snapshot,
    serialize_source_projection,
)
from tools.release_integrity import git, tag_identity

FROZEN_RECORD_RELATIVE = "evidence/claim_source_coverage_v1.0.7.json"
FROZEN_SCHEMA_RELATIVE = "schemas/claim-source-coverage-v1.schema.json"
OVERLAY_SCHEMA_RELATIVE = "schemas/claim-source-coverage-overlay-m1.schema.json"
UNSAFE_PROJECTION_PATHS = (
    "/x",
    "a//b",
    "./x",
    "../x",
    "a/./b",
    "a/../b",
    "a/",
    "a\\b",
    "a b",
    "a\n",
    "a\r",
    "a\x00b",
    "a\x7fb",
)


def test_frozen_v107_coverage_matches_release_tag_and_tagged_schema() -> None:
    identity = tag_identity("v1.0.7", require_head=False)
    frozen_bytes = FROZEN_OUTPUT.read_bytes()
    assert frozen_bytes == _tagged_bytes(identity["commit"], FROZEN_RECORD_RELATIVE)

    record = json.loads(frozen_bytes)
    tagged_schema_bytes = _tagged_bytes(identity["commit"], FROZEN_SCHEMA_RELATIVE)
    assert (ROOT / FROZEN_SCHEMA_RELATIVE).read_bytes() == tagged_schema_bytes
    tagged_schema = json.loads(tagged_schema_bytes)
    Draft7Validator(tagged_schema, format_checker=FormatChecker()).validate(record)

    published_schema = json.loads(
        (ROOT / FROZEN_SCHEMA_RELATIVE).read_text(encoding="utf-8")
    )
    Draft7Validator(published_schema, format_checker=FormatChecker()).validate(record)
    assert SCHEMA_PATH.relative_to(ROOT).as_posix() == OVERLAY_SCHEMA_RELATIVE


def test_frozen_v107_coverage_internal_hashes_match_tagged_files() -> None:
    identity = tag_identity("v1.0.7", require_head=False)
    record = _load_record(FROZEN_OUTPUT)
    observed: dict[str, str] = {}

    for item in record["input_files"]:
        assert item["sha256"] == _tagged_sha256(identity["commit"], item["path"], observed)

    for claim in record["claims"]:
        for locator in claim["claim_locators"]:
            assert locator["file_sha256"] == _tagged_sha256(
                identity["commit"], locator["path"], observed
            )
        for link in claim["source_links"]:
            path = link["admitted_path"]
            if path is not None:
                assert link["admitted_sha256"] == _tagged_sha256(
                    identity["commit"], path, observed
                )


def test_claim_source_coverage_overlay_matches_deterministic_generator() -> None:
    expected = _load_record(DEFAULT_OUTPUT)
    actual = build_record(ROOT)
    assert actual == expected


def test_claim_source_coverage_overlay_matches_schema_and_runtime() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    record = _load_record(DEFAULT_OUTPUT)
    Draft7Validator(schema, format_checker=FormatChecker()).validate(record)

    assert record["status"] == "candidate_only"
    assert record["generator"]["runtime"] == f"python=={platform.python_version()}"
    assert record["generator"]["runtime_implementation"] == platform.python_implementation()
    assert record["generator"]["runtime"] == RUNTIME_IDENTITY
    assert record["generator"]["required_runtime"] == AUTHORITATIVE_RUNTIME_IDENTITY
    assert record["generator"]["runtime_classification"] == RUNTIME_CLASSIFICATION
    assert record["generator"]["runtime_contract_path"] == RUNTIME_PATH
    assert record["generator"]["runtime_contract_sha256"] == _sha256(ROOT / RUNTIME_PATH)
    assert record["generator"]["dependency_lock_path"] == LOCK_PATH
    assert record["generator"]["dependency_lock_sha256"] == _sha256(ROOT / LOCK_PATH)
    if RUNTIME_CLASSIFICATION == "environment_limited":
        assert any("ENVIRONMENT_LIMITED" in gap for gap in record["known_gaps"])


def test_claim_source_coverage_overlay_identity_is_unpromoted_and_bound() -> None:
    record = _load_record(DEFAULT_OUTPUT)
    overlay = record["maintenance_overlay"]
    identity = tag_identity(overlay["release_tag"], require_head=False)

    assert overlay["promotion_status"] == "unpromoted_source_repair"
    assert overlay["identity_closure_paths"] == sorted(IDENTITY_CLOSURE_PATHS)
    assert overlay["baseline_commit"] == BASE_COMMIT
    assert overlay["baseline_tree"] == BASE_TREE
    assert overlay["milestone_changed_paths"] == sorted(MILESTONE_SOURCE_PATHS)
    changed_from_baseline = _independent_baseline_source_changes()
    assert MILESTONE_SOURCE_PATHS <= changed_from_baseline
    assert overlay["additional_baseline_changed_paths"] == sorted(
        changed_from_baseline - MILESTONE_SOURCE_PATHS
    )
    assert MILESTONE_SOURCE_PATHS == frozenset(
        {
            "AGENTS.md",
            "LICENSE_MAP.md",
            "README.md",
            "evidence/README.md",
            "manuscript/manuscript.md",
            "schemas/README.md",
            "schemas/claim-source-coverage-overlay-m1.schema.json",
            "tests/test_claim_source_coverage.py",
            "tests/test_document_contract.py",
            "tools/build_claim_source_coverage.py",
            "tools/check_repository.py",
        }
    )
    assert not {
        "source_state",
        "base_commit",
        "base_tree",
        "candidate_source_commit",
        "candidate_source_tree",
    } & set(overlay)
    projection = overlay["source_projection"]
    assert projection == build_source_projection(repository_snapshot(ROOT))
    assert projection["scheme"] == SOURCE_PROJECTION_SCHEME
    assert projection["scope"] == SOURCE_PROJECTION_SCOPE
    assert projection["serialization"] == SOURCE_PROJECTION_SERIALIZATION
    assert projection["excluded_paths"] == sorted(IDENTITY_CLOSURE_PATHS)
    paths = [entry["path"] for entry in projection["entries"]]
    assert paths == sorted(paths)
    assert len(paths) == len(set(paths)) == projection["entry_count"]
    assert not IDENTITY_CLOSURE_PATHS & set(paths)
    assert overlay["release_tag_object"] == identity["tag_object"]
    assert overlay["release_commit"] == identity["commit"]
    assert overlay["release_tree"] == identity["tree"]
    assert overlay["release_tag_object"] == RELEASE_TAG_OBJECT
    assert overlay["release_commit"] == RELEASE_COMMIT
    assert overlay["release_tree"] == RELEASE_TREE
    assert overlay["frozen_record_sha256"] == _sha256(FROZEN_OUTPUT)
    assert overlay["authoritative_source_sha256"] == _sha256(
        ROOT / overlay["authoritative_source_path"]
    )


def test_claim_source_coverage_overlay_preserves_structural_unknowns() -> None:
    record = _load_record(DEFAULT_OUTPUT)
    summary = record["summary"]

    assert record["reference_release"]["version"] == "1.0.7"
    assert summary["claim_count"] == 55
    assert summary["claims_with_support"] == 55
    assert summary["claims_with_current_path_support"] == 55
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


def test_claim_source_coverage_overlay_internal_hashes_match_files() -> None:
    record = _load_record(DEFAULT_OUTPUT)
    for item in record["input_files"]:
        assert item["sha256"] == _sha256(ROOT / item["path"])
    for claim in record["claims"]:
        for locator in claim["claim_locators"]:
            assert locator["file_sha256"] == _sha256(ROOT / locator["path"])
        for link in claim["source_links"]:
            path = link["admitted_path"]
            if path is not None:
                assert link["admitted_sha256"] == _sha256(ROOT / path)


def test_overlay_source_projection_matches_index_blobs_independently() -> None:
    record = _load_record(DEFAULT_OUTPUT)
    projection = record["maintenance_overlay"]["source_projection"]
    expected = _independent_index_projection_entries()
    assert projection["entries"] == expected
    assert projection["entry_count"] == len(expected)
    payload = _independent_source_projection_payload(
        expected, projection["excluded_paths"]
    )
    assert projection["canonical_bytes"] == len(payload)
    assert projection["sha256"] == hashlib.sha256(payload).hexdigest()
    manuscript = next(
        entry for entry in expected if entry["path"] == "manuscript/manuscript.md"
    )
    assert (
        record["maintenance_overlay"]["authoritative_source_sha256"]
        == manuscript["sha256"]
    )


def test_source_projection_serializer_has_stable_framing() -> None:
    entries = [
        {
            "path": "z/file.txt",
            "mode": "100644",
            "bytes": 3,
            "sha256": hashlib.sha256(b"abc").hexdigest(),
        },
        {
            "path": "a/run.py",
            "mode": "100755",
            "bytes": 0,
            "sha256": hashlib.sha256(b"").hexdigest(),
        },
    ]
    exclusions = sorted(IDENTITY_CLOSURE_PATHS)
    payload = serialize_source_projection(entries, exclusions)
    assert (
        hashlib.sha256(payload).hexdigest()
        == "b5b8e683ad9b24587a6f4aff72afeb0f6479200c234901bfbf610f0e3828e566"
    )
    assert payload == serialize_source_projection(list(reversed(entries)), exclusions)


@pytest.mark.parametrize("path", UNSAFE_PROJECTION_PATHS)
def test_source_projection_serializer_rejects_unsafe_paths(path: str) -> None:
    invalid = [
        {
            "path": path,
            "mode": "100644",
            "bytes": 3,
            "sha256": hashlib.sha256(b"abc").hexdigest(),
        }
    ]
    with pytest.raises(RuntimeError, match="Unsafe source-projection path"):
        serialize_source_projection(invalid, sorted(IDENTITY_CLOSURE_PATHS))


def test_overlay_never_treats_identity_closure_as_claim_support() -> None:
    record = _load_record(DEFAULT_OUTPUT)
    located = {
        locator["path"] for claim in record["claims"] for locator in claim["claim_locators"]
    }
    admitted = {
        link["admitted_path"]
        for claim in record["claims"]
        for link in claim["source_links"]
        if link["admitted_path"] is not None
    }
    assert not IDENTITY_CLOSURE_PATHS & located
    assert not IDENTITY_CLOSURE_PATHS & admitted


@pytest.mark.parametrize("path", UNSAFE_PROJECTION_PATHS)
def test_overlay_schema_rejects_unsafe_projection_paths(path: str) -> None:
    record = _load_record(DEFAULT_OUTPUT)
    record["maintenance_overlay"]["source_projection"]["entries"][0]["path"] = path
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = list(Draft7Validator(schema).iter_errors(record))
    assert errors


def test_frozen_and_overlay_claim_semantics_are_identical() -> None:
    frozen = _load_record(FROZEN_OUTPUT)
    overlay = _load_record(DEFAULT_OUTPUT)
    assert [_without_path_hashes(claim) for claim in overlay["claims"]] == [
        _without_path_hashes(claim) for claim in frozen["claims"]
    ]


def _load_record(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _without_path_hashes(claim: dict[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(claim)
    for locator in normalized["claim_locators"]:
        locator.pop("file_sha256")
    for link in normalized["source_links"]:
        link.pop("admitted_sha256")
    return normalized


def _tagged_bytes(commit: str, path: str) -> bytes:
    value = git(["show", f"{commit}:{path}"], binary=True)
    if not isinstance(value, bytes):
        raise TypeError("Expected binary Git output")
    return value


def _tagged_sha256(commit: str, path: str, observed: dict[str, str]) -> str:
    if path not in observed:
        observed[path] = hashlib.sha256(_tagged_bytes(commit, path)).hexdigest()
    return observed[path]


def _independent_index_projection_entries() -> list[dict[str, Any]]:
    value = git(["ls-files", "--stage", "-z"], binary=True)
    if not isinstance(value, bytes):
        raise TypeError("Expected binary Git output")
    entries: list[dict[str, Any]] = []
    for record in value.split(b"\0"):
        if not record:
            continue
        header, encoded_path = record.split(b"\t", 1)
        mode, object_id, stage = header.decode("ascii").split()
        assert stage == "0"
        path = encoded_path.decode("ascii")
        if path in IDENTITY_CLOSURE_PATHS:
            continue
        data = git(["cat-file", "blob", object_id], binary=True)
        if not isinstance(data, bytes):
            raise TypeError("Expected binary Git blob output")
        entries.append(
            {
                "path": path,
                "mode": mode,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    return sorted(entries, key=lambda entry: entry["path"])


def _independent_baseline_source_changes() -> set[str]:
    value = git(
        ["diff", "--cached", "--no-renames", "--name-only", "-z", BASE_COMMIT, "--"],
        binary=True,
    )
    if not isinstance(value, bytes):
        raise TypeError("Expected binary Git output")
    return {
        path
        for path in value.decode("ascii").split("\0")
        if path and path not in IDENTITY_CLOSURE_PATHS
    }


def _independent_source_projection_payload(
    entries: list[dict[str, Any]], excluded_paths: list[str]
) -> bytes:
    def lp32(value: bytes) -> bytes:
        return struct.pack(">I", len(value)) + value

    payload = bytearray(b"ASTRA\0SOURCE-PROJECTION\0V1\0")
    payload.extend(lp32(SOURCE_PROJECTION_SCOPE.encode("ascii")))
    exclusions = sorted(excluded_paths)
    payload.extend(struct.pack(">I", len(exclusions)))
    for path in exclusions:
        payload.extend(lp32(path.encode("ascii")))
    ordered = sorted(entries, key=lambda entry: entry["path"])
    payload.extend(struct.pack(">I", len(ordered)))
    for entry in ordered:
        payload.extend(lp32(entry["path"].encode("ascii")))
        payload.extend(lp32(entry["mode"].encode("ascii")))
        payload.extend(struct.pack(">Q", entry["bytes"]))
        payload.extend(bytes.fromhex(entry["sha256"]))
    return bytes(payload)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
