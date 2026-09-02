from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator, FormatChecker

from tools.assemble_pages import (
    EXPECTED_PAGE_SOURCE_NAMES,
    IDENTITY_NAME,
    PACKAGE_ROOT,
    SUMS_NAME,
    sha256,
    verify_atlas_release_assets,
)
from tools.build_pages_admission import RELEASE_ROUTES, build_record
from tools.check_pages_admission import SCHEMA


def test_pages_admission_builder_matches_schema_and_exact_route_contract() -> None:
    record = build_record()
    Draft7Validator(
        json.loads(SCHEMA.read_text(encoding="utf-8")), format_checker=FormatChecker()
    ).validate(record)
    assert record["release_routes"] == RELEASE_ROUTES
    paths = [item["path"] for item in record["head_shell"]["files"]]
    assert paths == sorted(paths)
    assert "resources/index.html" in paths
    assert "sppt-astra-cover.svg" in paths


def test_pages_admission_rejects_an_extra_shell_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import tools.build_pages_admission as builder
    import tools.check_pages_admission as checker

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.html").write_text("home\n", encoding="utf-8")
    digest = hashlib.sha256((docs / "index.html").read_bytes()).hexdigest()
    manifest = {
        "schema": "https://jkolantree.github.io/astra/schemas/pages-admission-v1.schema.json",
        "manifest_version": "1.0.0",
        "base": {
            "commit": "3c1a1325b6b365ba457a03b87cc73139d0c6a629",
            "tree": "ff03d152c98deb65c7246fdd2283cebee71b5857",
            "relationship": "fresh_current_main_pages_admission_base",
        },
        "head_shell": {
            "root": "docs",
            "files": [
                {
                    "path": "index.html",
                    "bytes": (docs / "index.html").stat().st_size,
                    "sha256": digest,
                }
            ],
        },
        "release_routes": RELEASE_ROUTES,
        "policy": {
            "copy_exact_head_shell_only": True,
            "release_bytes_required_for_publication_routes": True,
            "reject_unadmitted_docs": True,
            "reject_draft_and_candidate_content": True,
        },
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(builder, "SHELL_PATHS", ("index.html",))
    monkeypatch.setattr(checker, "DOCS", docs)
    assert checker.check_pages_admission(path)["head_shell"]["files"] == manifest["head_shell"]["files"]
    (docs / "unadmitted.html").write_text("no\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="not explicitly admitted|unexpected"):
        checker.check_pages_admission(path)


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
