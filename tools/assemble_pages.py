"""Assemble Atlas Pages routes from admitted shell and verified release bytes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = "resources/dark-medium-response-atlas/v0.1.0"
IDENTITY_NAME = "dark-medium-response-atlas-v0.1.0-release-identity.json"
SUMS_NAME = "SHA256SUMS"
EXPECTED_RELEASE_ASSET_NAMES = (
    "dark-medium-response-atlas-v0.1.0.html",
    "dark-medium-response-atlas-v0.1.0.pdf",
    "dark-medium-response-atlas-v0.1.0-source.tar.gz",
    SUMS_NAME,
    IDENTITY_NAME,
)
EXPECTED_CHECKSUM_ASSET_NAMES = EXPECTED_RELEASE_ASSET_NAMES[:3]
EXPECTED_PAGE_SOURCE_NAMES = (
    "CHANGELOG.md",
    "CITATION.cff",
    "LICENSE_MAP.md",
    "RELEASE_NOTES.md",
    "RELEASE_SPEC.json",
    "claim-ledger.csv",
    "external-link-observations.json",
    "html-accessibility.json",
    "novelty-ledger.csv",
    "pdf-inspection.json",
    "publication-identity.json",
    "source-ledger.csv",
    "visual-review.json",
)

sys.path.insert(0, str(ROOT))
from tools.check_pages_admission import (  # noqa: E402
    check_pages_admission,
    copy_admitted_shell,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _file_record(path: Path) -> dict[str, Any]:
    return {"name": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)}


def _path_record(path: str, value: bytes) -> dict[str, Any]:
    return {"path": path, "bytes": len(value), "sha256": hashlib.sha256(value).hexdigest()}


def _require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise RuntimeError(
            f"{label} keys mismatch: missing={sorted(expected - set(value))}; "
            f"unexpected={sorted(set(value) - expected)}"
        )


def _safe_relative_path(path: str) -> None:
    if (
        re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", path) is None
        or "/../" in f"/{path}/"
        or "//" in path
    ):
        raise RuntimeError(f"Unsafe source-archive path: {path!r}")


def _source_file(source_root: Path, relative: str) -> Path:
    _safe_relative_path(relative)
    root = source_root.resolve()
    candidate = root / relative
    try:
        candidate.resolve().relative_to(root)
    except ValueError as error:
        raise RuntimeError(f"Source-archive path escapes its root: {relative!r}") from error
    if candidate.is_symlink() or not candidate.is_file():
        raise RuntimeError(f"Verified source archive lacks a regular file: {relative}")
    return candidate


def parse_sums(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="ascii").splitlines():
        digest, separator, name = line.partition("  ")
        if (
            separator != "  "
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name) is None
            or name in values
        ):
            raise RuntimeError(f"Malformed Atlas checksum record: {line!r}")
        values[name] = digest
    return values


def _spec_from_source(source_root: Path) -> tuple[dict[str, Any], tuple[str, ...], tuple[str, ...]]:
    spec_path = _source_file(source_root, f"{PACKAGE_ROOT}/RELEASE_SPEC.json")
    value = json.loads(spec_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("Verified Atlas release specification is not an object")
    expected = {
        "publication_line_id": "dark-medium-response-atlas",
        "version": "0.1.0",
        "tag": "dark-medium-response-atlas-v0.1.0",
        "namespace": PACKAGE_ROOT,
        "identity_excludes_self": True,
        "github_release": {
            "draft": False,
            "prerelease": True,
            "make_latest": False,
            "immutable_required": True,
        },
        "pages": {
            "publish": True,
            "versioned_route": "/resources/dark-medium-response-atlas/v0.1.0/",
            "latest_route": "/resources/dark-medium-response-atlas/latest/",
            "citation_route": "/resources/dark-medium-response-atlas/v0.1.0/",
        },
    }
    for key, required in expected.items():
        if value.get(key) != required:
            raise RuntimeError(f"Verified Atlas release specification mismatch for {key}")
    assets = value.get("release_asset_allowlist")
    checksums = value.get("checksum_asset_names")
    if (
        not isinstance(assets, list)
        or not isinstance(checksums, list)
        or tuple(assets) != EXPECTED_RELEASE_ASSET_NAMES
        or tuple(checksums) != EXPECTED_CHECKSUM_ASSET_NAMES
    ):
        raise RuntimeError("Verified Atlas release asset contract is not the exact v0.1.0 contract")
    for name in assets:
        if not isinstance(name, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name) is None:
            raise RuntimeError("Verified Atlas release asset name is unsafe")
    return value, EXPECTED_RELEASE_ASSET_NAMES, EXPECTED_CHECKSUM_ASSET_NAMES


def _identity_file_records(value: object, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise RuntimeError(f"{label} must be an array")
    records: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise RuntimeError(f"{label}[{index}] must be an object")
        _require_exact_keys(item, {"name", "bytes", "sha256"}, f"{label}[{index}]")
        if (
            not isinstance(item["name"], str)
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", item["name"]) is None
            or not isinstance(item["bytes"], int)
            or item["bytes"] < 1
            or not isinstance(item["sha256"], str)
            or re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is None
        ):
            raise RuntimeError(f"{label}[{index}] is malformed")
        records.append(item)
    return records


def _identity_path_records(value: object, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise RuntimeError(f"{label} must be an array")
    records: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise RuntimeError(f"{label}[{index}] must be an object")
        _require_exact_keys(item, {"path", "bytes", "sha256"}, f"{label}[{index}]")
        if (
            not isinstance(item["path"], str)
            or not isinstance(item["bytes"], int)
            or item["bytes"] < 1
            or not isinstance(item["sha256"], str)
            or re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is None
        ):
            raise RuntimeError(f"{label}[{index}] is malformed")
        _safe_relative_path(item["path"])
        records.append(item)
    return records


def _verify_identity(
    directory: Path,
    source_root: Path,
    spec: dict[str, Any],
    assets: tuple[str, ...],
    checksums: tuple[str, ...],
    sums: dict[str, str],
) -> list[dict[str, Any]]:
    identity = json.loads((directory / IDENTITY_NAME).read_text(encoding="utf-8"))
    if not isinstance(identity, dict):
        raise RuntimeError("Atlas detached release identity must be an object")
    expected_keys = {
        "schema",
        "contract_version",
        "repository",
        "repository_id",
        "publication_line_id",
        "version",
        "tag",
        "annotated_tag_object",
        "commit",
        "tree",
        "tracked_manifest",
        "release_spec",
        "successor_overlay",
        "release_date",
        "build_epoch",
        "assets",
        "checksum_covered_assets",
        "sha256sums_sha256",
        "pages_source_files",
        "github_release",
        "pages",
        "identity_excludes_self",
    }
    _require_exact_keys(identity, expected_keys, "Atlas detached release identity")
    expected_scalars = {
        "schema": spec["identity_schema"],
        "contract_version": spec["contract_version"],
        "repository": spec["repository"],
        "repository_id": spec["repository_id"],
        "publication_line_id": spec["publication_line_id"],
        "version": spec["version"],
        "tag": spec["tag"],
        "release_date": spec["release_date"],
        "build_epoch": spec["build_epoch"],
        "github_release": spec["github_release"],
        "pages": {
            key: spec["pages"][key]
            for key in ("versioned_route", "latest_route", "citation_route")
        },
        "identity_excludes_self": True,
    }
    for key, expected in expected_scalars.items():
        if identity.get(key) != expected:
            raise RuntimeError(f"Atlas release identity mismatch for {key}")
    for key in ("annotated_tag_object", "commit", "tree"):
        if not isinstance(identity[key], str) or re.fullmatch(r"[0-9a-f]{40}", identity[key]) is None:
            raise RuntimeError(f"Atlas release identity has invalid {key}")

    for key, relative in (
        ("tracked_manifest", "MANIFEST.sha256"),
        ("release_spec", f"{PACKAGE_ROOT}/RELEASE_SPEC.json"),
        ("successor_overlay", "evidence/dark_medium_response_atlas_publication_successor_overlay_s2.json"),
    ):
        record = identity[key]
        if not isinstance(record, dict) or set(record) != {"path", "bytes", "sha256"}:
            raise RuntimeError(f"Atlas release identity {key} is malformed")
        actual = _source_file(source_root, relative).read_bytes()
        if record != _path_record(relative, actual):
            raise RuntimeError(f"Atlas release identity {key} differs from the verified source archive")

    expected_assets = [_file_record(directory / name) for name in assets[:4]]
    if _identity_file_records(identity["assets"], "assets") != expected_assets:
        raise RuntimeError("Atlas detached identity does not bind the downloaded asset bytes")
    expected_covered = [_file_record(directory / name) for name in checksums]
    covered = _identity_file_records(identity["checksum_covered_assets"], "checksum_covered_assets")
    if covered != expected_covered:
        raise RuntimeError("Atlas detached identity checksum coverage mismatch")
    if identity["sha256sums_sha256"] != sha256(directory / SUMS_NAME):
        raise RuntimeError("Atlas detached identity checksum-file digest mismatch")
    for name, record in zip(checksums, covered, strict=True):
        if sums[name] != record["sha256"]:
            raise RuntimeError(f"Atlas checksum and detached identity disagree for {name}")

    pages_records = _identity_path_records(identity["pages_source_files"], "pages_source_files")
    expected_paths = [f"{PACKAGE_ROOT}/{name}" for name in EXPECTED_PAGE_SOURCE_NAMES]
    if [record["path"] for record in pages_records] != expected_paths:
        raise RuntimeError("Atlas detached identity Pages-source path roster is not exact")
    for record in pages_records:
        actual = _source_file(source_root, record["path"]).read_bytes()
        if record != _path_record(record["path"], actual):
            raise RuntimeError(
                f"Atlas detached identity Pages-source bytes differ: {record['path']}"
            )
    return pages_records


def verify_atlas_release_assets(
    directory: Path, source_root: Path
) -> tuple[dict[str, Any], tuple[str, ...], list[dict[str, Any]]]:
    if directory.is_symlink() or not directory.is_dir():
        raise RuntimeError("Atlas release asset directory must be a regular directory")
    if source_root.is_symlink() or not source_root.is_dir():
        raise RuntimeError("Verified Atlas source root must be a regular directory")
    spec, assets, checksums = _spec_from_source(source_root)
    entries = sorted(directory.iterdir(), key=lambda path: path.name)
    if any(path.is_symlink() or not path.is_file() for path in entries):
        raise RuntimeError("Atlas release asset directory contains a non-regular entry")
    if [path.name for path in entries] != sorted(assets):
        raise RuntimeError(
            f"Atlas release asset roster mismatch: expected={sorted(assets)}, "
            f"observed={[path.name for path in entries]}"
        )
    sums = parse_sums(directory / SUMS_NAME)
    if tuple(sums) != checksums:
        raise RuntimeError("Atlas SHA256SUMS roster differs from the release specification")
    for name in checksums:
        if sha256(directory / name) != sums[name]:
            raise RuntimeError(f"Atlas release checksum mismatch: {name}")
    pages_records = _verify_identity(directory, source_root, spec, assets, checksums, sums)
    return spec, assets, pages_records


def write_redirect(path: Path, target: str, label: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "<!doctype html>\n"
        '<html lang="en-US"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<meta http-equiv="refresh" content="0; url={target}">'
        f"<title>{label} | ASTRA</title></head><body><main>"
        f"<h1>{label}</h1><p><a href=\"{target}\">Continue to the versioned edition</a>.</p>"
        "</main></body></html>\n",
        encoding="utf-8",
        newline="\n",
    )


def _verify_admitted_shell_in_site(site: Path) -> None:
    record = check_pages_admission()
    for item in record["head_shell"]["files"]:
        target = site / str(item["path"])
        if not target.is_file() or target.stat().st_size != item["bytes"] or sha256(target) != item["sha256"]:
            raise RuntimeError(f"Pages site no longer contains the admitted shell byte: {item['path']}")


def assemble_atlas_routes(site: Path, assets: Path, source_root: Path) -> None:
    site = site.resolve()
    if site.is_symlink() or not site.is_dir():
        raise RuntimeError("Pages assembly destination must be a regular directory")
    _verify_admitted_shell_in_site(site)
    spec, asset_names, pages_records = verify_atlas_release_assets(assets, source_root)
    versioned = site / spec["pages"]["versioned_route"].strip("/")
    latest = site / spec["pages"]["latest_route"].strip("/")
    if versioned.exists() or latest.exists():
        raise RuntimeError("Atlas Pages routes already exist in the assembly destination")
    versioned.mkdir(parents=True, exist_ok=False)
    for name in asset_names:
        shutil.copyfile(assets / name, versioned / name)
    for record in pages_records:
        source = _source_file(source_root, record["path"])
        target = versioned / Path(record["path"]).name
        shutil.copyfile(source, target)
        if target.stat().st_size != record["bytes"] or sha256(target) != record["sha256"]:
            raise RuntimeError(f"Atlas Pages copy mismatch: {record['path']}")
    shutil.copyfile(versioned / asset_names[0], versioned / "index.html")
    write_redirect(
        latest / "index.html",
        "../v0.1.0/",
        "Current Dark-Medium Response Atlas edition",
    )


def assemble(site: Path, assets: Path, source_root: Path) -> None:
    site = site.resolve()
    if site.exists() and any(site.iterdir()):
        raise RuntimeError("Pages assembly destination must be empty")
    copy_admitted_shell(site)
    assemble_atlas_routes(site, assets, source_root)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--atlas-assets", type=Path, required=True)
    parser.add_argument("--atlas-source", type=Path, required=True)
    parser.add_argument(
        "--preserve-existing",
        action="store_true",
        help="add only the Atlas routes after admitted shell and legacy routes exist",
    )
    args = parser.parse_args()
    if args.preserve_existing:
        assemble_atlas_routes(args.site, args.atlas_assets, args.atlas_source)
    else:
        assemble(args.site, args.atlas_assets, args.atlas_source)
    print(f"Assembled Atlas Pages routes in {args.site}.")


if __name__ == "__main__":
    main()
