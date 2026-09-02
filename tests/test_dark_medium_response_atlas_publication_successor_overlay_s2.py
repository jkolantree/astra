from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

import tools.build_dark_medium_response_atlas_publication_successor_overlay as s2


def test_release_contract_binds_citation_to_immutable_versioned_route() -> None:
    snapshot = _release_contract_snapshot()
    contract = s2.verify_release_contract(snapshot)

    assert contract["citation_pages_route"] == contract["versioned_pages_route"]


def test_s2_schema_requires_the_bound_citation_route() -> None:
    schema = _load_json(s2.SCHEMA_PATH)
    release_contract = schema["properties"]["release_contract"]
    assert isinstance(release_contract, dict)
    assert "citation_pages_route" in release_contract["required"]
    assert release_contract["properties"]["citation_pages_route"] == {
        "const": "/resources/dark-medium-response-atlas/v0.1.0/"
    }


def test_release_contract_rejects_nonversioned_citation_route() -> None:
    snapshot = _release_contract_snapshot(
        citation_route="/resources/dark-medium-response-atlas/latest/"
    )

    with pytest.raises(RuntimeError, match="Pages release contract mismatch"):
        s2.verify_release_contract(snapshot)


def test_committed_snapshot_is_immune_to_ambient_worktree_mutation(
    tmp_path: Path,
) -> None:
    root, _base, commit = _minimal_committed_candidate(tmp_path)
    (root / "source.txt").write_bytes(b"ambient mutation\n")

    resolved, _tree, snapshot = s2.committed_revision_snapshot(commit, root=root)

    assert resolved == commit
    assert snapshot["source.txt"].data == b"candidate\n"


def test_committed_roster_and_base_ancestry_are_exact(tmp_path: Path) -> None:
    root, base, commit = _minimal_committed_candidate(tmp_path)
    s2.assert_base_is_ancestor(base, commit, root=root)
    assert s2.assert_exact_committed_change_roster(
        root,
        commit=commit,
        base_commit=base,
        source_paths={"source.txt"},
        deleted_paths={"obsolete.txt"},
        closure_paths={"MANIFEST.sha256", "overlay.json"},
    ) == {"MANIFEST.sha256", "obsolete.txt", "overlay.json", "source.txt"}

    orphan = _git(root, "commit-tree", f"{base}^{{tree}}", "-m", "orphan").strip()
    with pytest.raises(RuntimeError, match="not an ancestor"):
        s2.assert_base_is_ancestor(base, orphan, root=root)

    (root / "rogue.txt").write_text("unexpected\n", encoding="utf-8")
    _git(root, "add", "rogue.txt")
    rogue_commit = _git(root, "commit", "--quiet", "-m", "unexpected").strip()
    if not rogue_commit:
        rogue_commit = _git(root, "rev-parse", "HEAD").strip()
    with pytest.raises(RuntimeError, match="Committed S2 change roster mismatch"):
        s2.assert_exact_committed_change_roster(
            root,
            commit=rogue_commit,
            base_commit=base,
            source_paths={"source.txt"},
            deleted_paths={"obsolete.txt"},
            closure_paths={"MANIFEST.sha256", "overlay.json"},
        )


def test_verify_committed_revision_rejects_reformatted_s2_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = {"example": ["same", "semantic", "content"]}
    canonical = s2.canonical_json_bytes(record)
    reformatted = json.dumps(record, sort_keys=True).encode("utf-8")
    snapshot = {
        s2.OUTPUT_RELATIVE_PATH: _entry(s2.OUTPUT_RELATIVE_PATH, reformatted),
        s2.SCHEMA_RELATIVE_PATH: _entry(s2.SCHEMA_RELATIVE_PATH, b"{}"),
    }

    monkeypatch.setattr(s2, "assert_supported_runtime", lambda: None)
    monkeypatch.setattr(
        s2,
        "committed_revision_snapshot",
        lambda revision, *, root: ("a" * 40, "b" * 40, snapshot),
    )
    monkeypatch.setattr(s2, "assert_base_is_ancestor", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        s2, "assert_exact_committed_change_roster", lambda *args, **kwargs: set()
    )
    monkeypatch.setattr(
        s2, "assert_committed_snapshot_membership", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(s2, "validate_record", lambda *args, **kwargs: None)
    monkeypatch.setattr(s2, "build_record_from_snapshot", lambda value: record)

    with pytest.raises(RuntimeError, match="do not exactly match"):
        s2.verify_committed_revision("HEAD")

    assert reformatted != canonical


def _release_contract_snapshot(
    *, citation_route: str = "/resources/dark-medium-response-atlas/v0.1.0/"
) -> dict[str, s2.SnapshotEntry]:
    spec = _load_json(s2.ROOT / s2.RELEASE_SPEC_PATH)
    pages = spec["pages"]
    assert isinstance(pages, dict)
    pages["citation_route"] = citation_route
    publication_identity = _load_json(s2.ROOT / s2.PUBLICATION_IDENTITY_PATH)
    return {
        s2.RELEASE_SPEC_PATH: _entry(
            s2.RELEASE_SPEC_PATH, json.dumps(spec).encode("utf-8")
        ),
        s2.RELEASE_SPEC_SCHEMA_PATH: _entry(
            s2.RELEASE_SPEC_SCHEMA_PATH,
            (s2.ROOT / s2.RELEASE_SPEC_SCHEMA_PATH).read_bytes(),
        ),
        s2.PUBLICATION_IDENTITY_PATH: _entry(
            s2.PUBLICATION_IDENTITY_PATH,
            json.dumps(publication_identity).encode("utf-8"),
        ),
        s2.PUBLICATION_IDENTITY_SCHEMA_PATH: _entry(
            s2.PUBLICATION_IDENTITY_SCHEMA_PATH,
            (s2.ROOT / s2.PUBLICATION_IDENTITY_SCHEMA_PATH).read_bytes(),
        ),
    }


def _minimal_committed_candidate(tmp_path: Path) -> tuple[Path, str, str]:
    root = tmp_path / "candidate"
    root.mkdir()
    _git(root, "init", "--quiet")
    _git(root, "config", "user.name", "ASTRA Test")
    _git(root, "config", "user.email", "astra-test.invalid")
    _git(root, "config", "core.autocrlf", "false")
    (root / "baseline.txt").write_text("baseline\n", encoding="utf-8")
    (root / "obsolete.txt").write_text("obsolete\n", encoding="utf-8")
    _git(root, "add", "baseline.txt", "obsolete.txt")
    _git(root, "commit", "--quiet", "-m", "base")
    base = _git(root, "rev-parse", "HEAD").strip()

    (root / "obsolete.txt").unlink()
    (root / "source.txt").write_bytes(b"candidate\n")
    (root / "MANIFEST.sha256").write_text("manifest\n", encoding="utf-8")
    (root / "overlay.json").write_text("{}\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "--quiet", "-m", "candidate")
    commit = _git(root, "rev-parse", "HEAD").strip()
    return root, base, commit


def _entry(path: str, data: bytes) -> s2.SnapshotEntry:
    return s2.SnapshotEntry(path, "100644", "0" * 40, data)


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _git(root: Path, *arguments: str) -> str:
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
        text=True,
    )
    return completed.stdout
