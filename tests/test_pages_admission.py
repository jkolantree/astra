from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator, FormatChecker

from tools import assemble_research_companion_pages as companion
from tools import build_pages_admission as builder
from tools import check_pages_admission as checker
from tools.assemble_pages import (
    EXPECTED_PAGE_SOURCE_NAMES,
    IDENTITY_NAME,
    PACKAGE_ROOT,
    SUMS_NAME,
    sha256,
    verify_atlas_release_assets,
)
from tools.build_pages_admission import (
    COMPANION_PATHS,
    COMPANION_ROOT,
    RELEASE_ROUTES,
    SHELL_PATHS,
    SUPPORT_PATHS,
    build_record,
    companion_record,
)
from tools.check_pages_admission import SCHEMA


@pytest.fixture
def admitted_source(tmp_path: Path) -> Path:
    """Complete synthetic source bytes for the historical roster, not an admission."""
    root = tmp_path / "source"
    relatives = (
        *(f"docs/{name}" for name in SHELL_PATHS),
        *(f"{COMPANION_ROOT}/{name}" for name in COMPANION_PATHS),
        *SUPPORT_PATHS,
    )
    for relative in relatives:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"Synthetic fixture: {relative}\n", encoding="utf-8")
    return root


@pytest.fixture
def admitted_manifest(
    tmp_path: Path, admitted_source: Path, monkeypatch: pytest.MonkeyPatch,
) -> Path:
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(build_record(admitted_source)), encoding="utf-8")
    monkeypatch.setattr(checker, "DOCS", admitted_source / "docs")
    monkeypatch.setattr(checker, "companion_record", lambda: companion_record(admitted_source))
    return path


def test_pages_admission_builder_matches_schema_and_exact_route_contract(
    admitted_source: Path,
) -> None:
    record = build_record(admitted_source)
    Draft7Validator(
        json.loads(SCHEMA.read_text(encoding="utf-8")), format_checker=FormatChecker()
    ).validate(record)
    assert record["release_routes"] == RELEASE_ROUTES
    paths = [item["path"] for item in record["head_shell"]["files"]]
    assert paths == sorted(paths)
    assert "resources/index.html" in paths
    assert "sppt-astra-cover.svg" in paths
    companion_paths = [item["path"] for item in record["research_companion"]["files"]]
    assert companion_paths == sorted(companion_paths) == list(COMPANION_PATHS)


def test_pages_admission_rejects_an_extra_shell_file(
    admitted_source: Path, admitted_manifest: Path,
) -> None:
    docs = admitted_source / "docs"
    assert checker.check_pages_admission(admitted_manifest) == build_record(admitted_source)
    (docs / "unadmitted.html").write_text("no\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="not explicitly admitted|unexpected"):
        checker.check_pages_admission(admitted_manifest)


def test_default_builder_still_rejects_unadmitted_current_docs() -> None:
    with pytest.raises(RuntimeError, match="Pages shell roster is not explicitly admitted"):
        build_record()


def test_default_companion_has_the_exact_portable_roster() -> None:
    assert [item["path"] for item in companion_record()["files"]] == list(COMPANION_PATHS)


def test_historical_admission_still_rejects_the_current_tree() -> None:
    with pytest.raises(
        RuntimeError,
        match="Research companion Pages admission differs|Pages shell roster is not explicitly admitted|Pages shell admission mismatch",
    ):
        checker.check_pages_admission()


@pytest.mark.parametrize("fault", ["extra", "case"])
def test_companion_roster_rejects_extra_or_case_changed_paths(
    tmp_path: Path, admitted_source: Path, fault: str,
) -> None:
    companion = admitted_source / COMPANION_ROOT
    assert [item["path"] for item in companion_record(admitted_source)["files"]] == list(COMPANION_PATHS)
    if fault == "extra":
        (companion / "extra.txt").write_text("unadmitted\n", encoding="utf-8")
    else:
        original = companion / "FONT_NOTICES.txt"
        # An intermediate path makes a case-only rename explicit on Windows too.
        intermediate = tmp_path / "renamed-notice.txt"
        original.rename(intermediate)
        intermediate.rename(companion / "font_notices.txt")
    with pytest.raises(RuntimeError, match="Research companion Pages roster is not explicitly admitted"):
        companion_record(admitted_source)


def test_pages_admission_rejects_changed_companion_bytes(
    admitted_source: Path, admitted_manifest: Path,
) -> None:
    checker.check_pages_admission(admitted_manifest)
    (admitted_source / COMPANION_ROOT / "README.md").write_text("changed\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="differs from exact source bytes"):
        checker.check_pages_admission(admitted_manifest)


def _path_record(root: Path, relative: str) -> dict[str, object]:
    path = root / relative
    return {"path": relative, "bytes": path.stat().st_size, "sha256": sha256(path)}


def _atlas_fixture(tmp_path: Path) -> tuple[Path, Path]:
    source_root = tmp_path / "source"
    package = source_root / PACKAGE_ROOT
    package.mkdir(parents=True)
    source_spec = Path("resources/dark-medium-response-atlas/v0.1.0/RELEASE_SPEC.json")
    spec = json.loads(source_spec.read_text(encoding="utf-8"))
    (package / "RELEASE_SPEC.json").write_text(
        json.dumps(spec, indent=2) + "\n", encoding="utf-8"
    )
    for name in EXPECTED_PAGE_SOURCE_NAMES:
        path = package / name
        if name != "RELEASE_SPEC.json":
            path.write_text(f"fixture {name}\n", encoding="utf-8")
    (source_root / "evidence").mkdir()
    (source_root / "evidence" / "dark_medium_response_atlas_publication_successor_overlay_s2.json").write_text(
        "{}\n", encoding="utf-8"
    )
    (source_root / "MANIFEST.sha256").write_text("fixture manifest\n", encoding="utf-8")

    assets = tmp_path / "assets"
    assets.mkdir()
    asset_names = spec["release_asset_allowlist"]
    checksum_names = spec["checksum_asset_names"]
    for name in checksum_names:
        (assets / name).write_bytes(("asset:" + name).encode("ascii"))
    (assets / SUMS_NAME).write_text(
        "".join(f"{sha256(assets / name)}  {name}\n" for name in checksum_names),
        encoding="ascii",
    )
    identity = {
        "schema": spec["identity_schema"],
        "contract_version": spec["contract_version"],
        "repository": spec["repository"],
        "repository_id": spec["repository_id"],
        "publication_line_id": spec["publication_line_id"],
        "version": spec["version"],
        "tag": spec["tag"],
        "annotated_tag_object": "a" * 40,
        "commit": "b" * 40,
        "tree": "c" * 40,
        "tracked_manifest": _path_record(source_root, "MANIFEST.sha256"),
        "release_spec": _path_record(source_root, f"{PACKAGE_ROOT}/RELEASE_SPEC.json"),
        "successor_overlay": _path_record(
            source_root, "evidence/dark_medium_response_atlas_publication_successor_overlay_s2.json"
        ),
        "release_date": spec["release_date"],
        "build_epoch": spec["build_epoch"],
        "assets": [
            {"name": name, "bytes": (assets / name).stat().st_size, "sha256": sha256(assets / name)}
            for name in asset_names[:4]
        ],
        "checksum_covered_assets": [
            {"name": name, "bytes": (assets / name).stat().st_size, "sha256": sha256(assets / name)}
            for name in checksum_names
        ],
        "sha256sums_sha256": sha256(assets / SUMS_NAME),
        "pages_source_files": [
            _path_record(source_root, f"{PACKAGE_ROOT}/{name}")
            for name in EXPECTED_PAGE_SOURCE_NAMES
        ],
        "github_release": spec["github_release"],
        "pages": {
            key: spec["pages"][key]
            for key in ("versioned_route", "latest_route", "citation_route")
        },
        "identity_excludes_self": True,
    }
    (assets / IDENTITY_NAME).write_text(
        json.dumps(identity, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return assets, source_root


def test_atlas_asset_verifier_requires_tag_derived_source_identity(tmp_path: Path) -> None:
    assets, source_root = _atlas_fixture(tmp_path)
    spec, names, page_records = verify_atlas_release_assets(assets, source_root)
    assert spec["tag"] == "dark-medium-response-atlas-v0.1.0"
    assert names[-2:] == (SUMS_NAME, IDENTITY_NAME)
    assert [record["path"] for record in page_records] == [
        f"{PACKAGE_ROOT}/{name}" for name in EXPECTED_PAGE_SOURCE_NAMES
    ]

    (assets / "unadmitted.txt").write_text("no\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="roster mismatch"):
        verify_atlas_release_assets(assets, source_root)
    (assets / "unadmitted.txt").unlink()
    (source_root / PACKAGE_ROOT / "CITATION.cff").write_text("changed\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="Pages-source bytes differ"):
        verify_atlas_release_assets(assets, source_root)


def test_pages_assembler_rejects_a_renamed_source_asset_contract(tmp_path: Path) -> None:
    assets, source_root = _atlas_fixture(tmp_path)
    spec_path = source_root / PACKAGE_ROOT / "RELEASE_SPEC.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    spec["release_asset_allowlist"] = [
        "alternate.html",
        "alternate.pdf",
        "alternate-source.tar.gz",
        SUMS_NAME,
        IDENTITY_NAME,
    ]
    spec["checksum_asset_names"] = spec["release_asset_allowlist"][:3]
    spec_path.write_text(json.dumps(spec) + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="exact v0.1.0 contract"):
        verify_atlas_release_assets(assets, source_root)


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def current_source(tmp_path: Path) -> Path:
    root = tmp_path / "source"
    paths = (
        *(f"docs/{name}" for name in builder.CURRENT_SHELL_PATHS),
        *(f"{builder.COMPANION_ROOT}/{name}" for name in builder.COMPANION_PATHS),
        *builder.SUPPORT_PATHS,
    )
    for name in paths:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"Synthetic fixture: {name}\n", encoding="utf-8")
    manifest = root / "evidence/pages_admission_current.json"
    manifest.parent.mkdir()
    manifest.write_text(json.dumps(builder.build_record(root, current=True)), encoding="utf-8")
    return root


def test_current_manifest_is_separate_and_matches_schema(current_source: Path) -> None:
    record = checker.check_pages_admission(current=True, root=current_source)
    schema = json.loads((ROOT / "schemas/pages-admission-current-v1.schema.json").read_bytes())
    Draft7Validator(schema).validate(record)
    assert len(record["head_shell"]["files"]) == 44
    assert len(record["research_companion"]["files"]) == 40
    assert record["release_routes"] == builder.RELEASE_ROUTES
    with pytest.raises(RuntimeError, match="not explicitly admitted"):
        builder.build_record(current_source)


@pytest.mark.parametrize("fault", ["changed", "extra", "missing", "manifest", "route", "companion", "support"])
def test_current_admission_rejects_unreviewed_change(current_source: Path, fault: str) -> None:
    manifest = current_source / "evidence/pages_admission_current.json"
    if fault == "changed":
        (current_source / "docs/index.html").write_text("changed", encoding="utf-8")
    elif fault == "extra":
        (current_source / "docs/extra.html").write_text("extra", encoding="utf-8")
    elif fault == "missing":
        (current_source / "docs/index.html").unlink()
    elif fault in {"manifest", "route"}:
        record = json.loads(manifest.read_bytes())
        if fault == "manifest":
            record["unexpected_authority"] = True
        else:
            record["release_routes"][0]["tag"] = "unreleased"
        manifest.write_text(json.dumps(record), encoding="utf-8")
    elif fault == "companion":
        (current_source / builder.COMPANION_ROOT / "README.md").write_text("changed", encoding="utf-8")
    else:
        (current_source / "LICENSE").write_text("changed", encoding="utf-8")
    with pytest.raises(RuntimeError, match="not explicitly admitted|differs from the exact reviewed"):
        checker.check_pages_admission(current=True, root=current_source)


@pytest.fixture
def current_review(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, dict]:
    monkeypatch.setattr(companion, "CURRENT_CANDIDATE_INPUTS", ("gate.py",))
    monkeypatch.setattr(companion, "CURRENT_VISUAL_SOURCE_PATHS", (("page.html", "index.html"),))
    (tmp_path / "gate.py").write_text("# fixture only\n", encoding="utf-8")
    (tmp_path / "page.html").write_text("<title>Fixture</title>", encoding="utf-8")
    record = {
        "kind": companion.CURRENT_REVIEW_KIND,
        "candidate_sha256": companion.candidate_digest(tmp_path, current=True),
        "visual_review": {
            "status": "accepted",
            "reviewer": "Codex agent",
            "owner_visual_review_claimed": False,
            "basis": "Synthetic enforcement fixture only",
            "surface": "Synthetic fixture",
            "scope": "Synthetic fixture",
            "content_sha256": companion.visual_content_digest(tmp_path, current=True),
        },
        "coverage": dict.fromkeys(companion.COVERAGE_CHECKS, "not-tested"),
        "publication_authorization": {
            "status": "authorized",
            "actor": "repository owner",
            "basis": "Synthetic fixture; no real publication authority",
            "scope": "current GitHub code and existing ASTRA website",
            "scientific_release_authorized": False,
        },
    }
    path = tmp_path / "current-review.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    return path, record


def test_current_review_keeps_owner_authority_and_agent_observation_separate(
    current_review: tuple[Path, dict],
) -> None:
    path, record = current_review
    assert companion.require_current_review(path, root=path.parent) == record["coverage"]


@pytest.mark.parametrize("fault", [
    "owner_visual", "owner_pending", "visual_pending", "reviewer", "candidate",
    "visual_bytes", "failed", "coverage_boolean", "release", "scope", "extra",
])
def test_current_review_fails_closed(current_review: tuple[Path, dict], fault: str) -> None:
    path, record = current_review
    if fault == "owner_visual":
        record["visual_review"]["owner_visual_review_claimed"] = True
    elif fault == "owner_pending":
        record["publication_authorization"]["status"] = "pending"
    elif fault == "visual_pending":
        record["visual_review"]["status"] = "pending"
    elif fault == "reviewer":
        record["visual_review"]["reviewer"] = "repository owner"
    elif fault == "candidate":
        (path.parent / "gate.py").write_text("# changed", encoding="utf-8")
    elif fault == "visual_bytes":
        (path.parent / "page.html").write_text("changed", encoding="utf-8")
    elif fault == "failed":
        record["coverage"]["desktop_and_mobile_layout"] = "failed"
    elif fault == "coverage_boolean":
        record["coverage"]["desktop_and_mobile_layout"] = True
    elif fault == "release":
        record["publication_authorization"]["scientific_release_authorized"] = True
    elif fault == "scope":
        record["publication_authorization"]["scope"] = "all future releases"
    else:
        record["undocumented"] = True
    path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(RuntimeError):
        companion.require_current_review(path, root=path.parent)


def test_current_workflow_requires_review_before_upload() -> None:
    workflow = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
    gate = 'tools/assemble_research_companion_pages.py --current --site "$site" --require-reviewed'
    assert gate in workflow
    assert workflow.index(gate) < workflow.index("tools/check_pages_links.py")
    assert workflow.index(gate) < workflow.index("actions/upload-pages-artifact")
