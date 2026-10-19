from __future__ import annotations

import json
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from tools import assemble_research_companion_pages as companion
from tools import build_pages_admission as builder
from tools import check_pages_admission as admission_checker
from tools.check_pages_admission import check_pages_admission, copy_admitted_shell
from tools.check_pages_links import check_pages_links
from tools.check_repository_links import check_repository_links

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def artifact_root() -> Iterator[Path]:
    # Canonical verification puts pytest's tmp_path inside the source tree.
    # Assembly artifacts must instead be external, including under that runner.
    with tempfile.TemporaryDirectory(prefix="astra-companion-test-", dir=ROOT.parent) as directory:
        yield Path(directory)


def artifact(tmp_path: Path) -> Path:
    site = tmp_path / "site"
    copy_admitted_shell(site, current=True)
    return site


def test_companion_assembly_preserves_existing_routes_and_exact_payload(artifact_root: Path) -> None:
    site = artifact(artifact_root)
    historical = site / "v1.0.1/preprint/index.html"
    historical.parent.mkdir(parents=True)
    historical.write_text("<!doctype html><title>Frozen edition fixture</title>")
    existing = companion.snapshot(site)
    result = companion.assemble(site, current=True)
    after = companion.snapshot(site)
    assert result == {"new_files": 44, "preserved_files": len(existing), "status": "draft-unpromoted"}
    assert all(after[name] == value for name, value in existing.items())
    record = check_pages_admission(current=True)["research_companion"]
    for item in record["files"]:
        path = site / record["root"] / item["path"]
        assert path.stat().st_size == item["bytes"]
        assert companion.digest(path) == item["sha256"]
    # Audit the complete companion hierarchy and its alias without pretending
    # this local fixture contains the separately release-built reading room.
    isolated = artifact_root / "companion-only"
    isolated.mkdir()
    import shutil

    shutil.copytree(site / "resources/sppt-scm-research-companion", isolated / "resources/sppt-scm-research-companion")
    shutil.copytree(site / "explore", isolated / "explore")
    shutil.copytree(site / "licenses", isolated / "licenses")
    shutil.copyfile(site / "LICENSE", isolated / "LICENSE")
    (isolated / "index.html").write_text("<!doctype html><title>Explorer destination fixture</title>")
    audited = check_pages_links(isolated)
    assert audited["html_files"] == 3
    assert audited["redirects"] == 1
    assert audited["internal_references"] >= 40
    markdown = check_repository_links(isolated)
    assert markdown["markdown_files"] == 7
    assert markdown["local_links"] >= 10


@pytest.mark.parametrize("collision", ["explore", builder.COMPANION_ROOT, "LICENSE", "licenses"])
def test_companion_rejects_collisions_before_writing(artifact_root: Path, collision: str) -> None:
    site = artifact(artifact_root)
    target = site / collision
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("existing artifact bytes")
    before = companion.snapshot(site)
    with pytest.raises(RuntimeError, match="collision|parent is not a directory"):
        companion.assemble(site, current=True)
    assert companion.snapshot(site) == before


def test_companion_reuses_identical_notice_without_overwriting(artifact_root: Path) -> None:
    site = artifact(artifact_root)
    target = site / "LICENSE"
    target.write_bytes((ROOT / "LICENSE").read_bytes())
    before = target.stat().st_mtime_ns
    assert companion.assemble(site, current=True)["new_files"] == 43
    assert target.stat().st_mtime_ns == before


def test_companion_rejects_missing_shell_and_destination_link(artifact_root: Path) -> None:
    empty = artifact_root / "empty"
    empty.mkdir()
    with pytest.raises(RuntimeError, match="exact admitted Pages shell"):
        companion.assemble(empty, current=True)
    site = artifact(artifact_root)
    link = artifact_root / "alias"
    link.symlink_to(site, target_is_directory=True)
    with pytest.raises(RuntimeError, match="links or junctions"):
        companion.assemble(link, current=True)
    (site / "licenses").symlink_to(empty, target_is_directory=True)
    with pytest.raises(RuntimeError, match="links or junctions"):
        companion.assemble(site, current=True)
    assert not (site / "explore").exists()


def test_artifact_fixture_ignores_source_nested_temp_environment(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest,
) -> None:
    temporary = ROOT / "tmp"
    temporary.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="nested-companion-test-", dir=temporary) as directory:
        nested = Path(directory)
        for name in ("TEMP", "TMP", "TMPDIR"):
            monkeypatch.setenv(name, directory)
        monkeypatch.setattr(tempfile, "tempdir", directory)
        assert Path(tempfile.gettempdir()) == nested
        assert ROOT in nested.parents
        inside = artifact(nested)
        before = companion.snapshot(inside)
        with pytest.raises(RuntimeError, match="outside the source tree"):
            companion.assemble(inside, current=True)
        assert companion.snapshot(inside) == before
        external = request.getfixturevalue("artifact_root")
        assert ROOT not in external.resolve().parents and external.resolve() != ROOT
        result = companion.assemble(artifact(external), current=True)
        assert result == {"new_files": 44, "preserved_files": 36, "status": "draft-unpromoted"}


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
    with pytest.raises(RuntimeError, match="not explicitly admitted|links or junctions"):
        builder.companion_record()
    (source / "extra.txt").unlink()
    (source / "only.txt").unlink()
    (source / "only.txt").symlink_to(ROOT / "LICENSE")
    with pytest.raises(RuntimeError, match="not explicitly admitted|links or junctions"):
        builder.companion_record()


def test_changed_manifest_companion_hash_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    relatives = (
        *(f"docs/{name}" for name in builder.SHELL_PATHS),
        *(f"{builder.COMPANION_ROOT}/{name}" for name in builder.COMPANION_PATHS),
        *builder.SUPPORT_PATHS,
    )
    for relative in relatives:
        fixture = source / relative
        fixture.parent.mkdir(parents=True, exist_ok=True)
        fixture.write_text(f"Synthetic fixture: {relative}\n", encoding="utf-8")
    record = builder.build_record(source)
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    monkeypatch.setattr(admission_checker, "DOCS", source / "docs")
    monkeypatch.setattr(admission_checker, "companion_record", lambda: builder.companion_record(source))
    assert check_pages_admission(path) == record

    record["research_companion"]["files"][0]["sha256"] = "0" * 64
    path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(RuntimeError, match="differs from exact source bytes"):
        check_pages_admission(path)


def review_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, dict]:
    # These synthetic records test enforcement only and are never saved as
    # owner review or publication evidence.
    monkeypatch.setattr(companion, "CANDIDATE_INPUTS", ("source.txt",))
    monkeypatch.setattr(companion, "VISUAL_SOURCE_PATHS", (("render.html", "index.html"),))
    (tmp_path / "source.txt").write_text("fixture candidate")
    (tmp_path / "render.html").write_text("<title>Fixture appearance</title>")
    record = {
        "schema": companion.REVIEW_SCHEMA,
        "candidate_sha256": companion.candidate_digest(tmp_path),
        "visual_review": {
            "status": "accepted",
            "basis": "Synthetic fixture only",
            "surface": "Synthetic fixture only",
            "scope": "Synthetic fixture only",
            "content_sha256": companion.visual_content_digest(tmp_path),
            "preview_candidate_sha256": companion.candidate_digest(tmp_path),
        },
        "coverage": dict.fromkeys(companion.COVERAGE_CHECKS, "not-tested"),
        "publication_approval": {"status": "approved", "basis": "Synthetic fixture only"},
    }
    path = tmp_path / "review.json"
    path.write_text(json.dumps(record))
    return path, record


def test_manual_acceptance_and_final_approval_do_not_require_specialist_passes_or_screenshots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path, record = review_fixture(tmp_path, monkeypatch)
    assert companion.require_visual_review(path, root=tmp_path) == record["coverage"]
    assert set(record["coverage"].values()) == {"not-tested"}
    assert not (tmp_path / "evidence").exists()
    record["coverage"]["keyboard_and_focus"] = "passed"
    path.write_text(json.dumps(record))
    assert companion.require_visual_review(path, root=tmp_path)["keyboard_and_focus"] == "passed"


@pytest.mark.parametrize("missing", ["visual", "publication"])
def test_visual_gate_requires_both_explicit_acceptance_and_publication_approval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, missing: str,
) -> None:
    path, record = review_fixture(tmp_path, monkeypatch)
    field = "visual_review" if missing == "visual" else "publication_approval"
    record[field]["status"] = "pending"
    path.write_text(json.dumps(record))
    with pytest.raises(RuntimeError, match="is pending"):
        companion.require_visual_review(path, root=tmp_path)


def test_changed_candidate_requires_new_final_approval_but_unchanged_visual_acceptance_survives(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path, record = review_fixture(tmp_path, monkeypatch)
    visual = record["visual_review"].copy()
    (tmp_path / "source.txt").write_text("refined gate, same rendered content")
    with pytest.raises(RuntimeError, match="stale for the current candidate"):
        companion.require_visual_review(path, root=tmp_path)
    record["candidate_sha256"] = companion.candidate_digest(tmp_path)
    record["publication_approval"] = {"status": "pending", "basis": None}
    path.write_text(json.dumps(record))
    with pytest.raises(RuntimeError, match="final publication approval is pending"):
        companion.require_visual_review(path, root=tmp_path)
    assert record["visual_review"] == visual
    record["publication_approval"] = {"status": "approved", "basis": "New synthetic approval"}
    path.write_text(json.dumps(record))
    companion.require_visual_review(path, root=tmp_path)


@pytest.mark.parametrize("change", ["page", "alias"])
def test_changed_rendered_content_invalidates_visual_acceptance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str,
) -> None:
    path, record = review_fixture(tmp_path, monkeypatch)
    if change == "page":
        (tmp_path / "render.html").write_text("<title>Changed appearance</title>")
    else:
        monkeypatch.setattr(companion, "ALIAS", b"changed alias")
    record["candidate_sha256"] = companion.candidate_digest(tmp_path)
    path.write_text(json.dumps(record))
    with pytest.raises(RuntimeError, match="stale for the rendered content"):
        companion.require_visual_review(path, root=tmp_path)


@pytest.mark.parametrize("fault", ["failed", "boolean", "missing", "unknown", "private_evidence", "approval_basis", "surface"])
def test_review_rejects_false_passes_incomplete_records_and_declared_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str,
) -> None:
    path, record = review_fixture(tmp_path, monkeypatch)
    if fault == "failed":
        record["coverage"]["keyboard_and_focus"] = "failed"
    elif fault == "boolean":
        record["coverage"]["keyboard_and_focus"] = True
    elif fault == "missing":
        del record["coverage"]["keyboard_and_focus"]
    elif fault == "unknown":
        record["coverage"]["keyboard_and_focus"] = "unknown"
    elif fault == "private_evidence":
        record["evidence"] = ["unrequested-private-screenshot.png"]
    elif fault == "approval_basis":
        record["publication_approval"]["basis"] = None
    else:
        record["visual_review"]["surface"] = None
    path.write_text(json.dumps(record))
    with pytest.raises(RuntimeError):
        companion.require_visual_review(path, root=tmp_path)


def test_historical_review_is_retained_but_does_not_admit_current_candidate() -> None:
    with pytest.raises(RuntimeError, match="stale for the current candidate"):
        companion.require_visual_review()


def test_current_review_obeys_separate_owner_and_agent_roles(artifact_root: Path) -> None:
    record = json.loads(companion.CURRENT_REVIEW.read_text())
    assert record["candidate_sha256"] == companion.candidate_digest(current=True)
    assert record["visual_review"]["owner_visual_review_claimed"] is False
    site = artifact(artifact_root)
    before = companion.snapshot(site)
    if record["visual_review"]["status"] == "accepted":
        result = companion.assemble(site, current=True, require_reviewed=True)
        assert result["new_files"] == 44
        assert result["review_coverage"] == record["coverage"]
        assert all(companion.snapshot(site)[name] == value for name, value in before.items())
    else:
        with pytest.raises(RuntimeError, match="visual review is pending"):
            companion.assemble(site, current=True, require_reviewed=True)
        assert companion.snapshot(site) == before


def test_frozen_release_routes_still_match_v1_and_workflow_requires_review() -> None:
    historical = json.loads((ROOT / "evidence/pages_admission_v1.json").read_text())
    assert builder.RELEASE_ROUTES == historical["release_routes"]
    workflow = (ROOT / ".github/workflows/pages.yml").read_text()
    assert 'tools/assemble_research_companion_pages.py --current --site "$site" --require-reviewed' in workflow
    assert workflow.index('tools/assemble_research_companion_pages.py --current --site "$site" --require-reviewed') < workflow.index('tools/check_pages_links.py "$site"')
