from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tools import assemble_research_companion_pages as companion
from tools import build_pages_admission as builder
from tools.check_pages_admission import check_pages_admission, copy_admitted_shell
from tools.check_pages_links import check_pages_links
from tools.check_repository_links import check_repository_links

ROOT = Path(__file__).resolve().parents[1]


def artifact(tmp_path: Path) -> Path:
    site = tmp_path / "site"
    copy_admitted_shell(site)
    return site


def test_companion_assembly_preserves_existing_routes_and_exact_payload(tmp_path: Path) -> None:
    site = artifact(tmp_path)
    historical = site / "v1.0.1/preprint/index.html"
    historical.parent.mkdir(parents=True)
    historical.write_text("<!doctype html><title>Frozen edition fixture</title>")
    existing = companion.snapshot(site)
    result = companion.assemble(site)
    after = companion.snapshot(site)
    assert result == {"new_files": 44, "preserved_files": len(existing), "status": "draft-unpromoted"}
    assert all(after[name] == value for name, value in existing.items())
    record = check_pages_admission()["research_companion"]
    for item in record["files"]:
        path = site / record["root"] / item["path"]
        assert path.stat().st_size == item["bytes"]
        assert companion.digest(path) == item["sha256"]
    # Audit the complete companion hierarchy and its alias without pretending
    # this local fixture contains the separately release-built reading room.
    isolated = tmp_path / "companion-only"
    isolated.mkdir()
    import shutil

    shutil.copytree(site / "resources/sppt-scm-research-companion", isolated / "resources/sppt-scm-research-companion")
    shutil.copytree(site / "explore", isolated / "explore")
    shutil.copytree(site / "licenses", isolated / "licenses")
    shutil.copyfile(site / "LICENSE", isolated / "LICENSE")
    audited = check_pages_links(isolated)
    assert audited["html_files"] == 2
    assert audited["redirects"] == 1
    assert audited["internal_references"] >= 40
    markdown = check_repository_links(isolated)
    assert markdown["markdown_files"] == 7
    assert markdown["local_links"] >= 10


@pytest.mark.parametrize("collision", ["explore", builder.COMPANION_ROOT, "LICENSE", "licenses"])
def test_companion_rejects_collisions_before_writing(tmp_path: Path, collision: str) -> None:
    site = artifact(tmp_path)
    target = site / collision
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("existing artifact bytes")
    before = companion.snapshot(site)
    with pytest.raises(RuntimeError, match="collision|parent is not a directory"):
        companion.assemble(site)
    assert companion.snapshot(site) == before


def test_companion_reuses_identical_notice_without_overwriting(tmp_path: Path) -> None:
    site = artifact(tmp_path)
    target = site / "LICENSE"
    target.write_bytes((ROOT / "LICENSE").read_bytes())
    before = target.stat().st_mtime_ns
    assert companion.assemble(site)["new_files"] == 43
    assert target.stat().st_mtime_ns == before


def test_companion_rejects_missing_shell_and_destination_link(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(RuntimeError, match="exact admitted Pages shell"):
        companion.assemble(empty)
    site = artifact(tmp_path)
    link = tmp_path / "alias"
    link.symlink_to(site, target_is_directory=True)
    with pytest.raises(RuntimeError, match="links or junctions"):
        companion.assemble(link)
    (site / "licenses").symlink_to(empty, target_is_directory=True)
    with pytest.raises(RuntimeError, match="links or junctions"):
        companion.assemble(site)
    assert not (site / "explore").exists()


def test_companion_source_roster_and_bytes_are_bound(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "source"
    source = root / builder.COMPANION_ROOT
    source.mkdir(parents=True)
    (source / "only.txt").write_text("admitted")
    monkeypatch.setattr(builder, "ROOT", root)
    monkeypatch.setattr(builder, "COMPANION_PATHS", ("only.txt",))
    monkeypatch.setattr(builder, "SUPPORT_PATHS", ())
    original = builder.companion_record()
    (source / "only.txt").write_text("changed")
    assert builder.companion_record() != original
    (source / "extra.txt").write_text("not admitted")
    with pytest.raises(RuntimeError, match="not explicitly admitted"):
        builder.companion_record()
    (source / "extra.txt").unlink()
    (source / "only.txt").unlink()
    (source / "only.txt").symlink_to(ROOT / "LICENSE")
    with pytest.raises(RuntimeError, match="not explicitly admitted"):
        builder.companion_record()


def test_changed_manifest_companion_hash_is_rejected(tmp_path: Path) -> None:
    record = builder.build_record()
    record["research_companion"]["files"][0]["sha256"] = "0" * 64
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(record))
    with pytest.raises(RuntimeError, match="differs from exact source bytes"):
        check_pages_admission(path)


def review_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, dict]:
    # Synthetic review records test enforcement only; they are never publication
    # evidence and are not saved to the repository's pending real review.
    monkeypatch.setattr(companion, "CANDIDATE_INPUTS", ("source.txt",))
    (tmp_path / "source.txt").write_text("fixture candidate")
    record = {
        "schema": companion.REVIEW_SCHEMA,
        "status": "approved",
        "candidate_sha256": companion.candidate_digest(tmp_path),
        "surface": "synthetic test fixture, not a browser review",
        "checks": dict.fromkeys(companion.CHECKS, True),
        "evidence": [],
    }
    directory = tmp_path / "evidence/research-companion-browser-review"
    directory.mkdir(parents=True)
    for name, content in (("desktop.png", b"\x89PNG\r\n\x1a\nfixture"), ("review.md", b"Synthetic test only")):
        target = directory / name
        target.write_bytes(content)
        record["evidence"].append({"path": target.relative_to(tmp_path).as_posix(), "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()})
    path = tmp_path / "review.json"
    path.write_text(json.dumps(record))
    return path, record


def test_visual_gate_rejects_pending_stale_and_incomplete_review(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path, record = review_fixture(tmp_path, monkeypatch)
    companion.require_visual_review(path, root=tmp_path)
    record["status"] = "pending"
    path.write_text(json.dumps(record))
    with pytest.raises(RuntimeError, match="are pending"):
        companion.require_visual_review(path, root=tmp_path)
    record["status"] = "approved"
    record["checks"]["keyboard_and_focus"] = False
    path.write_text(json.dumps(record))
    with pytest.raises(RuntimeError, match="checklist is incomplete"):
        companion.require_visual_review(path, root=tmp_path)
    record["checks"]["keyboard_and_focus"] = True
    path.write_text(json.dumps(record))
    (tmp_path / "source.txt").write_text("changed candidate")
    with pytest.raises(RuntimeError, match="stale"):
        companion.require_visual_review(path, root=tmp_path)


@pytest.mark.parametrize("fault", ["bytes", "traversal", "missing_report", "link", "surface"])
def test_visual_gate_requires_bounded_exact_evidence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str) -> None:
    path, record = review_fixture(tmp_path, monkeypatch)
    if fault == "bytes":
        record["evidence"][0]["sha256"] = "0" * 64
    elif fault == "traversal":
        record["evidence"][0]["path"] = "evidence/research-companion-browser-review/../desktop.png"
    elif fault == "missing_report":
        record["evidence"] = record["evidence"][:1]
    elif fault == "link":
        image = tmp_path / record["evidence"][0]["path"]
        image.unlink()
        image.symlink_to(tmp_path / "source.txt")
    else:
        record["surface"] = None
    path.write_text(json.dumps(record))
    with pytest.raises(RuntimeError):
        companion.require_visual_review(path, root=tmp_path)


def test_current_pending_gate_blocks_production_before_any_write(tmp_path: Path) -> None:
    record = json.loads(companion.REVIEW.read_text())
    if record["status"] == "approved":
        pytest.skip("An actual reviewed candidate must be checked by the deployment gate")
    assert record["candidate_sha256"] == companion.candidate_digest()
    site = artifact(tmp_path)
    before = companion.snapshot(site)
    with pytest.raises(RuntimeError, match="are pending"):
        companion.assemble(site, require_reviewed=True)
    assert companion.snapshot(site) == before


def test_frozen_release_routes_still_match_v1_and_workflow_requires_review() -> None:
    historical = json.loads((ROOT / "evidence/pages_admission_v1.json").read_text())
    assert builder.RELEASE_ROUTES == historical["release_routes"]
    workflow = (ROOT / ".github/workflows/pages.yml").read_text()
    assert 'tools/assemble_research_companion_pages.py --site "$site" --require-reviewed' in workflow
    assert workflow.index('tools/assemble_research_companion_pages.py --site "$site" --require-reviewed') < workflow.index('tools/check_pages_links.py "$site"')
