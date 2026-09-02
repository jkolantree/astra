from __future__ import annotations

import hashlib
import json
import os
import struct
import subprocess
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft7Validator, FormatChecker

from tools.build_dark_medium_response_atlas_successor_overlay import (
    AUTHORITATIVE_RUNTIME_IDENTITY,
    BASE_COMMIT,
    BASE_TREE,
    DEFAULT_OUTPUT,
    FULL_CHANGE_ROSTER,
    IDENTITY_CLOSURE_PATHS,
    PACKAGE_PATHS,
    PREDECESSOR_RELATIVE_PATH,
    PREDECESSOR_SHA256,
    ROOT,
    RUNTIME_CLASSIFICATION,
    RUNTIME_IDENTITY,
    RUNTIME_IMPLEMENTATION,
    SCHEMA_PATH,
    SOURCE_CHANGE_ROSTER,
    SOURCE_PROJECTION_SCOPE,
    build_record,
    repository_snapshot,
)


def test_successor_overlay_matches_deterministic_generator_and_schema() -> None:
    expected = _load_json(DEFAULT_OUTPUT)
    actual = build_record(ROOT)
    assert actual == expected
    schema = _load_json(SCHEMA_PATH)
    Draft7Validator(schema, format_checker=FormatChecker()).validate(expected)


def test_successor_overlay_preserves_identity_and_non_authority_boundary() -> None:
    record = _load_json(DEFAULT_OUTPUT)
    assert record["schema"].endswith(
        "/dark-medium-response-atlas-successor-overlay-s1.schema.json"
    )
    assert record["overlay_kind"] == "supplemental_resource_admission"
    assert record["base_identity"] == {
        "commit": BASE_COMMIT,
        "tree": BASE_TREE,
        "relationship": "audited_repository_base",
    }
    predecessor = record["predecessor_overlay"]
    assert predecessor["path"] == PREDECESSOR_RELATIVE_PATH
    assert predecessor["sha256"] == PREDECESSOR_SHA256
    assert predecessor["inherited_authority"] is False
    assert record["authority"] == {
        "scope": "repository_admission_and_byte_identity_only",
        "core_claim_authority": "none",
        "scientific_validation_authority": "none",
        "release_authority": "none",
        "publication_authority": "none",
        "supersedes_predecessor": False,
    }


def test_successor_overlay_binds_exact_rosters_and_package_hashes() -> None:
    record = _load_json(DEFAULT_OUTPUT)
    roster = record["change_roster"]
    assert roster["expected_paths"] == sorted(FULL_CHANGE_ROSTER)
    assert roster["source_paths"] == sorted(SOURCE_CHANGE_ROSTER)
    assert roster["identity_closure_paths"] == sorted(IDENTITY_CLOSURE_PATHS)
    package = record["package"]
    assert package["roster"] == list(PACKAGE_PATHS)
    assert package["file_count"] == len(PACKAGE_PATHS) == 8
    assert [entry["path"] for entry in package["files"]] == list(PACKAGE_PATHS)
    for entry in package["files"]:
        assert entry["sha256"] == hashlib.sha256((ROOT / entry["path"]).read_bytes()).hexdigest()
        assert entry["bytes"] == (ROOT / entry["path"]).stat().st_size


def test_successor_projection_matches_git_index_independently() -> None:
    record = _load_json(DEFAULT_OUTPUT)
    projection = record["source_projection"]
    expected = _independent_index_entries(set(IDENTITY_CLOSURE_PATHS))
    assert projection["entries"] == expected
    assert projection["entry_count"] == len(expected)
    payload = _independent_projection_payload(
        expected, sorted(IDENTITY_CLOSURE_PATHS)
    )
    assert projection["canonical_bytes"] == len(payload)
    assert projection["sha256"] == hashlib.sha256(payload).hexdigest()
    paths = [entry["path"] for entry in expected]
    assert paths == sorted(paths)
    assert not set(paths) & IDENTITY_CLOSURE_PATHS
    assert PREDECESSOR_RELATIVE_PATH in paths


def test_successor_runtime_is_explicitly_classified() -> None:
    assert RUNTIME_IMPLEMENTATION == "CPython"
    assert RUNTIME_IDENTITY in {"python==3.12.10", "python==3.12.13"}
    expected = (
        "release_authoritative"
        if RUNTIME_IDENTITY == AUTHORITATIVE_RUNTIME_IDENTITY
        else "environment_limited"
    )
    assert RUNTIME_CLASSIFICATION == expected
    record = _load_json(DEFAULT_OUTPUT)
    assert record["generator"]["runtime_classification"] == expected
    if expected == "environment_limited":
        assert record["generator"]["environment_note"].startswith(
            "ENVIRONMENT_LIMITED:"
        )


def test_snapshot_fails_on_untracked_source(tmp_path: Path) -> None:
    root, base_commit, base_tree = _minimal_candidate(tmp_path)
    (root / "rogue.txt").write_text("untracked\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="Untracked source paths"):
        _minimal_snapshot(root, base_commit, base_tree)


def test_snapshot_fails_on_unstaged_source(tmp_path: Path) -> None:
    root, base_commit, base_tree = _minimal_candidate(tmp_path)
    (root / "source.txt").write_text("staged then modified\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="must be staged"):
        _minimal_snapshot(root, base_commit, base_tree)


def test_snapshot_fails_on_unexpected_staged_change(tmp_path: Path) -> None:
    root, base_commit, base_tree = _minimal_candidate(tmp_path)
    (root / "rogue.txt").write_text("rogue\n", encoding="utf-8")
    _git(root, "add", "rogue.txt")
    with pytest.raises(RuntimeError, match="Unexpected candidate change paths"):
        _minimal_snapshot(root, base_commit, base_tree)


def _minimal_snapshot(
    root: Path, base_commit: str, base_tree: str
) -> dict[str, Any]:
    return repository_snapshot(
        root,
        base_commit=base_commit,
        base_tree=base_tree,
        source_change_roster={"source.txt"},
        full_change_roster={"source.txt", "MANIFEST.sha256", "overlay.json"},
        identity_closure_paths={"MANIFEST.sha256", "overlay.json"},
    )


def _minimal_candidate(tmp_path: Path) -> tuple[Path, str, str]:
    root = tmp_path / "candidate"
    root.mkdir()
    _git(root, "init", "--quiet")
    _git(root, "config", "user.name", "ASTRA Test")
    _git(root, "config", "user.email", "astra-test.invalid")
    (root / "baseline.txt").write_text("baseline\n", encoding="utf-8")
    _git(root, "add", "baseline.txt")
    _git(root, "commit", "--quiet", "-m", "baseline")
    base_commit = _git(root, "rev-parse", "HEAD").strip()
    base_tree = _git(root, "rev-parse", "HEAD^{tree}").strip()
    (root / "source.txt").write_text("candidate\n", encoding="utf-8")
    _git(root, "add", "source.txt")
    return root, base_commit, base_tree


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _git(root: Path, *arguments: str, binary: bool = False) -> str | bytes:
    environment = os.environ.copy()
    environment.update(
        {
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "safe.directory",
            "GIT_CONFIG_VALUE_0": str(root.resolve()),
        }
    )
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        env=environment,
        check=True,
        capture_output=True,
        text=not binary,
    )
    return completed.stdout


def _independent_index_entries(exclusions: set[str]) -> list[dict[str, Any]]:
    value = _git(ROOT, "ls-files", "--stage", "-z", binary=True)
    assert isinstance(value, bytes)
    entries: list[dict[str, Any]] = []
    for record in value.split(b"\0"):
        if not record:
            continue
        header, encoded_path = record.split(b"\t", 1)
        mode, object_id, stage = header.decode("ascii").split()
        assert stage == "0"
        path = encoded_path.decode("ascii")
        if path in exclusions:
            continue
        data = _git(ROOT, "cat-file", "blob", object_id, binary=True)
        assert isinstance(data, bytes)
        entries.append(
            {
                "path": path,
                "mode": mode,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    return sorted(entries, key=lambda entry: entry["path"])


def _independent_projection_payload(
    entries: list[dict[str, Any]], exclusions: list[str]
) -> bytes:
    def lp32(value: bytes) -> bytes:
        return struct.pack(">I", len(value)) + value

    payload = bytearray(b"ASTRA\0SOURCE-PROJECTION\0V1\0")
    payload.extend(lp32(SOURCE_PROJECTION_SCOPE.encode("ascii")))
    ordered_exclusions = sorted(exclusions)
    payload.extend(struct.pack(">I", len(ordered_exclusions)))
    for path in ordered_exclusions:
        payload.extend(lp32(path.encode("ascii")))
    ordered_entries = sorted(entries, key=lambda entry: entry["path"])
    payload.extend(struct.pack(">I", len(ordered_entries)))
    for entry in ordered_entries:
        payload.extend(lp32(entry["path"].encode("ascii")))
        payload.extend(lp32(entry["mode"].encode("ascii")))
        payload.extend(struct.pack(">Q", entry["bytes"]))
        payload.extend(bytes.fromhex(entry["sha256"]))
    return bytes(payload)
