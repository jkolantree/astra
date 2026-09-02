from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

import tools.verify as core_verify
from tools.dark_medium_response_atlas_release import (
    ARCHIVE_SOURCE_PATHS,
    IDENTITY_NAME,
    PACKAGE_ROOT,
    RELEASE_SPEC_PATH,
    S2_PATH,
    SUMS_NAME,
    TagIdentity,
    _extract_archive,
    _validate_identity,
    _validate_spec,
    build_detached_identity,
    canonical_json,
    source_archive_bytes,
    sums_bytes,
)

ROOT = Path(__file__).resolve().parents[1]


def _spec() -> dict[str, object]:
    value = json.loads(
        (ROOT / "resources" / "dark-medium-response-atlas" / "v0.1.0" / "RELEASE_SPEC.json").read_text(
            encoding="utf-8"
        )
    )
    assert isinstance(value, dict)
    return value


def _blobs(spec: dict[str, object]) -> dict[str, bytes]:
    blobs = {path: f"synthetic source for {path}\n".encode("ascii") for path in ARCHIVE_SOURCE_PATHS}
    blobs[RELEASE_SPEC_PATH] = canonical_json(spec)
    return blobs


def _payloads(spec: dict[str, object], blobs: dict[str, bytes]) -> dict[str, bytes]:
    assets, checksums = _validate_spec(spec)
    payloads = {
        assets[0]: b"<!doctype html><title>Atlas fixture</title>\n",
        assets[1]: b"%PDF-fixture\n",
        assets[2]: source_archive_bytes(spec, blobs),
    }
    payloads[SUMS_NAME] = sums_bytes(checksums, payloads)
    return payloads


def test_source_archive_is_deterministic_and_has_an_exact_safe_roster(tmp_path: Path) -> None:
    spec = _spec()
    blobs = _blobs(spec)
    first = source_archive_bytes(spec, blobs)
    second = source_archive_bytes(spec, blobs)
    assert first == second

    archive = tmp_path / "source.tar.gz"
    archive.write_bytes(first)
    extracted = _extract_archive(archive, tmp_path / "extracted", spec)
    assert extracted == blobs
    assert (tmp_path / "extracted" / "dark-medium-response-atlas-v0.1.0-source").is_dir()


def test_detached_identity_binds_the_exact_nonself_asset_contract() -> None:
    spec = _spec()
    blobs = _blobs(spec)
    payloads = _payloads(spec, blobs)
    identity = TagIdentity(tag_object="a" * 40, commit="b" * 40, tree="c" * 40)
    value = json.loads(build_detached_identity(spec, identity, blobs, payloads))

    assert value["tag"] == "dark-medium-response-atlas-v0.1.0"
    assert [record["name"] for record in value["assets"]] == [
        "dark-medium-response-atlas-v0.1.0.html",
        "dark-medium-response-atlas-v0.1.0.pdf",
        "dark-medium-response-atlas-v0.1.0-source.tar.gz",
        SUMS_NAME,
    ]
    assert value["identity_excludes_self"] is True
    assert IDENTITY_NAME not in {record["name"] for record in value["assets"]}
    assert all(record["path"].startswith(PACKAGE_ROOT + "/") for record in value["pages_source_files"])

    value["assets"][0]["sha256"] = "0" * 64
    with pytest.raises(RuntimeError, match="asset roster mismatch"):
        _validate_identity(value, spec, identity, payloads, blobs)


def test_release_spec_rejects_a_renamed_payload_even_with_matching_checksums() -> None:
    spec = _spec()
    spec["release_asset_allowlist"] = [
        "alternate.html",
        "alternate.pdf",
        "alternate-source.tar.gz",
        SUMS_NAME,
        IDENTITY_NAME,
    ]
    spec["checksum_asset_names"] = spec["release_asset_allowlist"][:3]
    with pytest.raises(RuntimeError, match="exact v0.1.0 contract"):
        _validate_spec(spec)


def test_extracted_source_archive_imports_the_self_contained_atlas_builder(
    tmp_path: Path,
) -> None:
    spec = _spec()
    blobs = {
        path: (b"{}\n" if path == S2_PATH else (ROOT / path).read_bytes())
        for path in ARCHIVE_SOURCE_PATHS
    }
    archive = tmp_path / "source.tar.gz"
    archive.write_bytes(source_archive_bytes(spec, blobs))
    extracted = tmp_path / "extracted"
    _extract_archive(archive, extracted, spec)
    source_root = extracted / "dark-medium-response-atlas-v0.1.0-source"
    commands = (
        "tools/build_dark_medium_response_atlas_documents.py",
        "tools/inspect_dark_medium_response_atlas_pdf.py",
    )
    for command in commands:
        completed = subprocess.run(
            [sys.executable, "-I", "-B", command, "--help"],
            cwd=source_root,
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0, completed.stderr


def test_core_m1_boundary_only_allows_the_exact_atlas_tag_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        core_verify,
        "capture_git",
        lambda *_args, **_kwargs: "dark-medium-response-atlas-v0.1.0\n",
    )
    core_verify.verify_candidate_not_at_tag({}, allow_atlas_tag=True)

    monkeypatch.setattr(core_verify, "capture_git", lambda *_args, **_kwargs: "v1.0.7\n")
    with pytest.raises(RuntimeError, match="cannot authorize verification at a tag"):
        core_verify.verify_candidate_not_at_tag({}, allow_atlas_tag=True)


def test_two_field_s2_marker_cannot_bypass_the_committed_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "dark_medium_response_atlas_publication_successor_overlay_s2.json").write_text(
        json.dumps(
            {
                "overlay_id": "dark-medium-response-atlas-publication-successor-s2",
                "status": "publication_candidate",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(core_verify, "ROOT", tmp_path)
    monkeypatch.setattr(
        core_verify,
        "capture_git",
        lambda arguments, **_kwargs: "" if arguments[:1] in (["status"], ["rev-list"]) else b"",
    )
    with pytest.raises(RuntimeError, match="not byte-verified from a committed candidate"):
        core_verify.atlas_publication_overlay_present({})
