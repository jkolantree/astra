from __future__ import annotations

import copy
import hashlib
import json
import platform
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, FormatChecker

from tools.build_claim_source_coverage import (
    AUTHORITATIVE_RUNTIME_IDENTITY,
    BASE_COMMIT,
    BASE_TREE,
    DEFAULT_OUTPUT,
    FROZEN_OUTPUT,
    IDENTITY_CLOSURE_PATHS,
    ROOT,
    RUNTIME_CLASSIFICATION,
    RUNTIME_IDENTITY,
    SCHEMA_PATH,
    SOURCE_CANDIDATE_PATHS,
    build_record,
    worktree_changed_paths,
)
from tools.release_integrity import git, tag_identity

FROZEN_RECORD_RELATIVE = "evidence/claim_source_coverage_v1.0.7.json"
FROZEN_SCHEMA_RELATIVE = "schemas/claim-source-coverage-v1.schema.json"


def test_frozen_v107_coverage_matches_release_tag_and_tagged_schema() -> None:
    identity = tag_identity("v1.0.7", require_head=False)
    frozen_bytes = FROZEN_OUTPUT.read_bytes()
    assert frozen_bytes == _tagged_bytes(identity["commit"], FROZEN_RECORD_RELATIVE)

    record = json.loads(frozen_bytes)
    tagged_schema = json.loads(_tagged_bytes(identity["commit"], FROZEN_SCHEMA_RELATIVE))
    Draft7Validator(tagged_schema, format_checker=FormatChecker()).validate(record)

    current_schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft7Validator(current_schema, format_checker=FormatChecker()).validate(record)


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
    candidate_source_commit = expected["maintenance_overlay"]["candidate_source_commit"]
    actual = build_record(ROOT, candidate_source_commit=candidate_source_commit)
    assert actual == expected


def test_claim_source_coverage_overlay_matches_schema_and_runtime() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    record = _load_record(DEFAULT_OUTPUT)
    Draft7Validator(schema, format_checker=FormatChecker()).validate(record)

    assert record["status"] == "candidate_only"
    assert record["generator"]["runtime"] == f"python=={platform.python_version()}"
    assert record["generator"]["runtime"] == RUNTIME_IDENTITY
    assert record["generator"]["required_runtime"] == AUTHORITATIVE_RUNTIME_IDENTITY
    assert record["generator"]["runtime_classification"] == RUNTIME_CLASSIFICATION
    if RUNTIME_CLASSIFICATION == "environment_limited":
        assert any("ENVIRONMENT_LIMITED" in gap for gap in record["known_gaps"])


def test_claim_source_coverage_overlay_identity_is_unpromoted_and_bound() -> None:
    record = _load_record(DEFAULT_OUTPUT)
    overlay = record["maintenance_overlay"]
    identity = tag_identity(overlay["release_tag"], require_head=False)

    assert overlay["promotion_status"] == "unpromoted_source_repair"
    assert overlay["identity_closure_paths"] == sorted(IDENTITY_CLOSURE_PATHS)
    assert overlay["base_commit"] == BASE_COMMIT
    assert overlay["base_tree"] == BASE_TREE
    assert SOURCE_CANDIDATE_PATHS == frozenset(
        {
            "AGENTS.md",
            "LICENSE_MAP.md",
            "manuscript/manuscript.md",
            "schemas/claim-source-coverage-v1.schema.json",
            "tests/test_claim_source_coverage.py",
            "tests/test_document_contract.py",
            "tools/build_claim_source_coverage.py",
            "tools/check_repository.py",
        }
    )
    if overlay["source_state"] == "uncommitted_worktree":
        assert overlay["candidate_source_commit"] is None
        assert overlay["candidate_source_tree"] is None
        assert git(["rev-parse", "HEAD"]).strip() == BASE_COMMIT
        assert worktree_changed_paths(ROOT) == (
            SOURCE_CANDIDATE_PATHS | IDENTITY_CLOSURE_PATHS
        )
    else:
        assert overlay["source_state"] == "committed_source_candidate"
        candidate = overlay["candidate_source_commit"]
        candidate_tree = overlay["candidate_source_tree"]
        assert isinstance(candidate, str)
        assert isinstance(candidate_tree, str)
        assert candidate_tree == git(["rev-parse", f"{candidate}^{{tree}}"]).strip()
        assert git(["rev-parse", f"{candidate}^"]).strip() == BASE_COMMIT
        assert _changed_paths_between(BASE_COMMIT, candidate) == SOURCE_CANDIDATE_PATHS
        head = git(["rev-parse", "HEAD"]).strip()
        changed = worktree_changed_paths(ROOT)
        if head == candidate:
            assert changed == IDENTITY_CLOSURE_PATHS
        else:
            assert not changed
            assert git(["rev-parse", "HEAD^"]).strip() == candidate
            assert _changed_paths_between(candidate, head) == IDENTITY_CLOSURE_PATHS
    assert overlay["release_tag_object"] == identity["tag_object"]
    assert overlay["release_commit"] == identity["commit"]
    assert overlay["release_tree"] == identity["tree"]
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


def test_committed_overlay_hashes_match_candidate_source_blobs() -> None:
    record = _load_record(DEFAULT_OUTPUT)
    candidate = record["maintenance_overlay"]["candidate_source_commit"]
    if candidate is None:
        return
    observed: dict[str, str] = {}
    for item in record["input_files"]:
        assert item["sha256"] == _tagged_sha256(candidate, item["path"], observed)
    for claim in record["claims"]:
        for locator in claim["claim_locators"]:
            assert locator["file_sha256"] == _tagged_sha256(
                candidate, locator["path"], observed
            )
        for link in claim["source_links"]:
            path = link["admitted_path"]
            if path is not None:
                assert link["admitted_sha256"] == _tagged_sha256(
                    candidate, path, observed
                )


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


def _changed_paths_between(base: str, tip: str) -> set[str]:
    value = git(
        ["diff", "--no-renames", "--name-only", "-z", base, tip, "--"], binary=True
    )
    if not isinstance(value, bytes):
        raise TypeError("Expected binary Git output")
    return {
        path.replace("\\", "/")
        for path in value.decode("utf-8", errors="surrogateescape").split("\0")
        if path
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
