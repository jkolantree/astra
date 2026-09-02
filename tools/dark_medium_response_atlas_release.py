"""Build and verify the five-asset Dark-Medium Response Atlas prerelease.

This controller deliberately reads release payloads from an annotated tag's
Git blobs.  It never packages the caller's ambient working tree, so an
untracked file or a later checkout change cannot enter the source archive.
"""

from __future__ import annotations

if __name__ == "__main__":
    import sys as _bootstrap_sys

    if not _bootstrap_sys.flags.isolated or not _bootstrap_sys.dont_write_bytecode:
        raise SystemExit(
            "Unsafe startup: run Python with -I -B before "
            "tools/dark_medium_response_atlas_release.py"
        )

import argparse
import gzip
import hashlib
import io
import json
import os
import platform
import re
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = "resources/dark-medium-response-atlas/v0.1.0"
RELEASE_SPEC_PATH = f"{PACKAGE_ROOT}/RELEASE_SPEC.json"
S2_PATH = "evidence/dark_medium_response_atlas_publication_successor_overlay_s2.json"
MANIFEST_PATH = "MANIFEST.sha256"
IDENTITY_SCHEMA_PATH = "schemas/supplemental-release-identity-v2.schema.json"
SOURCE_ARCHIVE_ROOT = "dark-medium-response-atlas-v0.1.0-source"
IDENTITY_NAME = "dark-medium-response-atlas-v0.1.0-release-identity.json"
SUMS_NAME = "SHA256SUMS"
EXPECTED_RUNTIME = "3.12.10"
RELEASE_ASSET_NAMES = (
    "dark-medium-response-atlas-v0.1.0.html",
    "dark-medium-response-atlas-v0.1.0.pdf",
    "dark-medium-response-atlas-v0.1.0-source.tar.gz",
    SUMS_NAME,
    IDENTITY_NAME,
)
CHECKSUM_ASSET_NAMES = RELEASE_ASSET_NAMES[:3]
SOURCE_REPLAY_PATHS = (
    f"{PACKAGE_ROOT}/dark-medium-response-atlas-v0.1.0.html",
    f"{PACKAGE_ROOT}/dark-medium-response-atlas-v0.1.0.pdf",
    f"{PACKAGE_ROOT}/html-accessibility.json",
    f"{PACKAGE_ROOT}/pdf-inspection.json",
    f"{PACKAGE_ROOT}/publication-identity.json",
)

PACKAGE_FILES = (
    f"{PACKAGE_ROOT}/CHANGELOG.md",
    f"{PACKAGE_ROOT}/CITATION.cff",
    f"{PACKAGE_ROOT}/LICENSE_MAP.md",
    f"{PACKAGE_ROOT}/README.md",
    f"{PACKAGE_ROOT}/RELEASE_NOTES.md",
    RELEASE_SPEC_PATH,
    f"{PACKAGE_ROOT}/claim-ledger.csv",
    f"{PACKAGE_ROOT}/dark-medium-response-atlas-v0.1.0.css",
    f"{PACKAGE_ROOT}/dark-medium-response-atlas-v0.1.0.html",
    f"{PACKAGE_ROOT}/dark-medium-response-atlas-v0.1.0.md",
    f"{PACKAGE_ROOT}/dark-medium-response-atlas-v0.1.0.pdf",
    f"{PACKAGE_ROOT}/external-link-observations.json",
    f"{PACKAGE_ROOT}/html-accessibility.json",
    f"{PACKAGE_ROOT}/novelty-ledger.csv",
    f"{PACKAGE_ROOT}/pdf-inspection.json",
    f"{PACKAGE_ROOT}/publication-identity.json",
    f"{PACKAGE_ROOT}/source-ledger.csv",
    f"{PACKAGE_ROOT}/visual-review.json",
)

# This is a source archive, not a repository snapshot.  It contains the exact
# paper package plus the small, named set of runtime, schema, evidence, font,
# and controller inputs needed to inspect its identity and reproduce its build.
ARCHIVE_SOURCE_PATHS = (
    ".python-version",
    "LICENSE",
    "MANIFEST.sha256",
    "RUNTIME.json",
    "requirements-lock.txt",
    "evidence/dark_medium_response_atlas_successor_overlay_s1.json",
    S2_PATH,
    "licenses/DEJAVU-FONTS.txt",
    "licenses/STIX-FONTS.txt",
    *PACKAGE_FILES,
    "schemas/dark-medium-response-atlas-html-accessibility-v1.schema.json",
    "schemas/dark-medium-response-atlas-pdf-inspection-v1.schema.json",
    "schemas/dark-medium-response-atlas-publication-identity-v1.schema.json",
    "schemas/dark-medium-response-atlas-publication-successor-overlay-s2.schema.json",
    "schemas/dark-medium-response-atlas-successor-overlay-s1.schema.json",
    "schemas/dark-medium-response-atlas-visual-review-v1.schema.json",
    "schemas/external-link-observations-v1.schema.json",
    IDENTITY_SCHEMA_PATH,
    "schemas/supplemental-release-spec-v2.schema.json",
    "tools/build_dark_medium_response_atlas_documents.py",
    "tools/dark_medium_response_atlas_document_helpers.py",
    "tools/dark_medium_response_atlas_pdf_helpers.py",
    "tools/build_dark_medium_response_atlas_publication_successor_overlay.py",
    "tools/build_dark_medium_response_atlas_successor_overlay.py",
    "tools/check_dark_medium_response_atlas_html.py",
    "tools/check_external_links.py",
    "tools/check_repository_links.py",
    "tools/dark_medium_response_atlas_release.py",
    "tools/inspect_dark_medium_response_atlas_pdf.py",
    "tools/link_audit_common.py",
    "tools/render_dark_medium_response_atlas_pdf.py",
)

PAGES_SOURCE_FILES = (
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

GIT_CONTROL_VARIABLES = {
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_CEILING_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_CONFIG_COUNT",
    "GIT_CONFIG_PARAMETERS",
    "GIT_CONFIG_SYSTEM",
    "GIT_DIR",
    "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    "GIT_INDEX_FILE",
    "GIT_NAMESPACE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_QUARANTINE_PATH",
    "GIT_REPLACE_REF_BASE",
    "GIT_WORK_TREE",
}


@dataclass(frozen=True)
class TagIdentity:
    tag_object: str
    commit: str
    tree: str


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def git_environment(root: Path = ROOT) -> dict[str, str]:
    environment = os.environ.copy()
    for name in tuple(environment):
        if name in GIT_CONTROL_VARIABLES or name.startswith("GIT_"):
            environment.pop(name)
    environment.update(
        {
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "safe.directory",
            "GIT_CONFIG_VALUE_0": str(root.resolve()),
            "GIT_NO_REPLACE_OBJECTS": "1",
        }
    )
    return environment


def git(
    arguments: list[str], *, root: Path = ROOT, binary: bool = False
) -> str | bytes:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        env=git_environment(root),
        check=True,
        capture_output=True,
        text=not binary,
    )
    return completed.stdout


def _require_runtime() -> None:
    if platform.python_implementation() != "CPython" or platform.python_version() != EXPECTED_RUNTIME:
        raise RuntimeError(
            "Dark-Medium Response Atlas release control requires release-authoritative "
            f"CPython {EXPECTED_RUNTIME}; observed "
            f"{platform.python_implementation()} {platform.python_version()}"
        )


def _safe_relative_path(path: str) -> None:
    try:
        path.encode("ascii")
    except UnicodeEncodeError as error:
        raise RuntimeError(f"Archive path is not ASCII: {path!r}") from error
    if re.fullmatch(r"[A-Za-z0-9._/-]*[A-Za-z0-9._-]", path) is None:
        raise RuntimeError(f"Archive path is malformed: {path!r}")
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts or not pure.parts:
        raise RuntimeError(f"Archive path is unsafe: {path!r}")


for _archive_path in ARCHIVE_SOURCE_PATHS:
    _safe_relative_path(_archive_path)
if len(ARCHIVE_SOURCE_PATHS) != len(set(ARCHIVE_SOURCE_PATHS)):
    raise RuntimeError("Source archive roster contains a duplicate path")
if tuple(sorted(PAGES_SOURCE_FILES)) != PAGES_SOURCE_FILES:
    raise RuntimeError("Public Pages source roster must be sorted")


def _require_clean_worktree(root: Path = ROOT) -> None:
    raw = git(["status", "--porcelain=v1", "--untracked-files=all"], root=root)
    if not isinstance(raw, str):  # pragma: no cover - type guard
        raise TypeError("Expected text Git status")
    if raw.strip():
        raise RuntimeError("A dirty worktree cannot build or verify a release asset bundle")


def tag_identity(tag: str, *, root: Path = ROOT, require_head: bool = True) -> TagIdentity:
    if re.fullmatch(r"dark-medium-response-atlas-v0\.1\.0", tag) is None:
        raise RuntimeError("Unexpected Dark-Medium Response Atlas release tag")
    kind = str(git(["cat-file", "-t", f"refs/tags/{tag}"], root=root)).strip()
    if kind != "tag":
        raise RuntimeError("Atlas release tag must be annotated")
    tag_object = str(git(["rev-parse", f"refs/tags/{tag}"], root=root)).strip()
    commit = str(git(["rev-parse", f"refs/tags/{tag}^{{commit}}"], root=root)).strip()
    tree = str(git(["rev-parse", f"{commit}^{{tree}}"], root=root)).strip()
    if any(re.fullmatch(r"[0-9a-f]{40}", value) is None for value in (tag_object, commit, tree)):
        raise RuntimeError("Atlas annotated tag identity is malformed")
    payload = str(git(["cat-file", "-p", f"refs/tags/{tag}"], root=root))
    headers = payload.partition("\n\n")[0].splitlines()
    expected_headers = ["object", "type", "tag", "tagger"]
    if [line.split(" ", 1)[0] for line in headers] != expected_headers:
        raise RuntimeError("Atlas annotated tag header is not canonical")
    header_map = dict(line.split(" ", 1) for line in headers)
    if (
        header_map.get("object") != commit
        or header_map.get("type") != "commit"
        or header_map.get("tag") != tag
    ):
        raise RuntimeError("Atlas annotated tag does not directly bind its commit")
    if require_head:
        head = str(git(["rev-parse", "HEAD"], root=root)).strip()
        if head != commit:
            raise RuntimeError("Atlas tag must point to the checked-out release commit")
    return TagIdentity(tag_object=tag_object, commit=commit, tree=tree)


def tag_blob(tag: str, path: str, *, root: Path = ROOT) -> bytes:
    _safe_relative_path(path)
    value = git(["show", f"{tag}^{{commit}}:{path}"], root=root, binary=True)
    if not isinstance(value, bytes):  # pragma: no cover - type guard
        raise TypeError("Expected binary Git blob")
    return value


def _json_object(data: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError(f"{label} is not valid UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} must be a JSON object")
    return value


def _require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise RuntimeError(
            f"{label} keys mismatch: missing={sorted(expected - set(value))}; "
            f"unexpected={sorted(set(value) - expected)}"
        )


def _validate_spec(spec: dict[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
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
        "external_identifiers": {"doi": False, "zenodo": False},
    }
    for key, required in expected.items():
        if spec.get(key) != required:
            raise RuntimeError(f"Atlas release specification mismatch for {key}")
    if spec.get("schema") != "https://jkolantree.github.io/astra/schemas/supplemental-release-spec-v2.schema.json":
        raise RuntimeError("Atlas release specification schema mismatch")
    if spec.get("identity_schema") != (
        "https://jkolantree.github.io/astra/schemas/supplemental-release-identity-v2.schema.json"
    ):
        raise RuntimeError("Atlas detached identity schema mismatch")
    assets = spec.get("release_asset_allowlist")
    checksums = spec.get("checksum_asset_names")
    if (
        not isinstance(assets, list)
        or not isinstance(checksums, list)
        or tuple(assets) != RELEASE_ASSET_NAMES
        or tuple(checksums) != CHECKSUM_ASSET_NAMES
    ):
        raise RuntimeError("Atlas release asset/checksum roster is not the exact v0.1.0 contract")
    for name in assets:
        if not isinstance(name, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name) is None:
            raise RuntimeError("Atlas release asset is not a portable basename")
    return RELEASE_ASSET_NAMES, CHECKSUM_ASSET_NAMES


def tag_snapshot(tag: str, *, root: Path = ROOT) -> tuple[dict[str, Any], dict[str, bytes]]:
    spec_bytes = tag_blob(tag, RELEASE_SPEC_PATH, root=root)
    spec = _json_object(spec_bytes, RELEASE_SPEC_PATH)
    _validate_spec(spec)
    blobs = {path: tag_blob(tag, path, root=root) for path in ARCHIVE_SOURCE_PATHS}
    if blobs[RELEASE_SPEC_PATH] != spec_bytes:
        raise RuntimeError("Atlas tag source archive does not bind its release specification")
    for path in PACKAGE_FILES:
        if path not in blobs:
            raise RuntimeError(f"Atlas package path is absent from the source archive roster: {path}")
    return spec, blobs


def source_archive_bytes(spec: dict[str, Any], blobs: dict[str, bytes]) -> bytes:
    if set(blobs) != set(ARCHIVE_SOURCE_PATHS):
        raise RuntimeError("Source archive blob roster is incomplete or unexpected")
    epoch = spec.get("build_epoch_unix")
    if not isinstance(epoch, int) or epoch < 0:
        raise RuntimeError("Atlas release build epoch is invalid")
    payload = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=payload, mtime=epoch, compresslevel=9) as gzip_file:
        with tarfile.open(fileobj=gzip_file, mode="w", format=tarfile.PAX_FORMAT) as archive:
            for path in ARCHIVE_SOURCE_PATHS:
                data = blobs[path]
                info = tarfile.TarInfo(f"{SOURCE_ARCHIVE_ROOT}/{path}")
                info.size = len(data)
                info.mode = 0o644
                info.mtime = epoch
                info.uid = 0
                info.gid = 0
                info.uname = ""
                info.gname = ""
                archive.addfile(info, io.BytesIO(data))
    return payload.getvalue()


def _asset_record(name: str, data: bytes) -> dict[str, Any]:
    return {"name": name, "bytes": len(data), "sha256": sha256_bytes(data)}


def sums_bytes(checksums: tuple[str, ...], payloads: dict[str, bytes]) -> bytes:
    return "".join(
        f"{sha256_bytes(payloads[name])}  {name}\n" for name in checksums
    ).encode("ascii")


def _path_record(path: str, data: bytes) -> dict[str, Any]:
    _safe_relative_path(path)
    return {"path": path, "bytes": len(data), "sha256": sha256_bytes(data)}


def build_detached_identity(
    spec: dict[str, Any],
    identity: TagIdentity,
    blobs: dict[str, bytes],
    payloads: dict[str, bytes],
) -> bytes:
    assets, checksums = _validate_spec(spec)
    if tuple(payloads) != assets[:4]:
        raise RuntimeError("Detached identity input does not contain the four non-self assets")
    record = {
        "schema": spec["identity_schema"],
        "contract_version": spec["contract_version"],
        "repository": spec["repository"],
        "repository_id": spec["repository_id"],
        "publication_line_id": spec["publication_line_id"],
        "version": spec["version"],
        "tag": spec["tag"],
        "annotated_tag_object": identity.tag_object,
        "commit": identity.commit,
        "tree": identity.tree,
        "tracked_manifest": _path_record(MANIFEST_PATH, blobs[MANIFEST_PATH]),
        "release_spec": _path_record(RELEASE_SPEC_PATH, blobs[RELEASE_SPEC_PATH]),
        "successor_overlay": _path_record(S2_PATH, blobs[S2_PATH]),
        "release_date": spec["release_date"],
        "build_epoch": spec["build_epoch"],
        "assets": [_asset_record(name, payloads[name]) for name in assets[:4]],
        "checksum_covered_assets": [_asset_record(name, payloads[name]) for name in checksums],
        "sha256sums_sha256": sha256_bytes(payloads[SUMS_NAME]),
        "pages_source_files": [
            _path_record(f"{PACKAGE_ROOT}/{name}", blobs[f"{PACKAGE_ROOT}/{name}"])
            for name in PAGES_SOURCE_FILES
        ],
        "github_release": spec["github_release"],
        "pages": {
            key: spec["pages"][key]
            for key in ("versioned_route", "latest_route", "citation_route")
        },
        "identity_excludes_self": True,
    }
    _validate_identity(record, spec, identity, payloads, blobs)
    return canonical_json(record)


def _identity_file_records(value: object, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise RuntimeError(f"Atlas identity {label} must be an array")
    output: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise RuntimeError(f"Atlas identity {label}[{index}] must be an object")
        _require_exact_keys(item, {"name", "bytes", "sha256"}, f"Atlas identity {label}[{index}]")
        if (
            not isinstance(item["name"], str)
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", item["name"]) is None
            or not isinstance(item["bytes"], int)
            or item["bytes"] < 1
            or not isinstance(item["sha256"], str)
            or re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is None
        ):
            raise RuntimeError(f"Atlas identity {label}[{index}] is malformed")
        output.append(item)
    return output


def _validate_identity(
    record: dict[str, Any],
    spec: dict[str, Any],
    identity: TagIdentity,
    payloads: dict[str, bytes],
    blobs: dict[str, bytes],
) -> None:
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
    _require_exact_keys(record, expected_keys, "Atlas detached identity")
    expected_values = {
        "schema": spec["identity_schema"],
        "contract_version": spec["contract_version"],
        "repository": spec["repository"],
        "repository_id": spec["repository_id"],
        "publication_line_id": spec["publication_line_id"],
        "version": spec["version"],
        "tag": spec["tag"],
        "annotated_tag_object": identity.tag_object,
        "commit": identity.commit,
        "tree": identity.tree,
        "release_date": spec["release_date"],
        "build_epoch": spec["build_epoch"],
        "github_release": spec["github_release"],
        "pages": {
            key: spec["pages"][key]
            for key in ("versioned_route", "latest_route", "citation_route")
        },
        "identity_excludes_self": True,
    }
    for key, expected in expected_values.items():
        if record.get(key) != expected:
            raise RuntimeError(f"Atlas detached identity mismatch for {key}")
    for key, path in (
        ("tracked_manifest", MANIFEST_PATH),
        ("release_spec", RELEASE_SPEC_PATH),
        ("successor_overlay", S2_PATH),
    ):
        if record.get(key) != _path_record(path, blobs[path]):
            raise RuntimeError(f"Atlas detached identity mismatch for {key}")
    assets, checksums = _validate_spec(spec)
    expected_assets = [_asset_record(name, payloads[name]) for name in assets[:4]]
    if _identity_file_records(record.get("assets"), "assets") != expected_assets:
        raise RuntimeError("Atlas detached identity asset roster mismatch")
    expected_covered = [_asset_record(name, payloads[name]) for name in checksums]
    if _identity_file_records(record.get("checksum_covered_assets"), "checksum_covered_assets") != expected_covered:
        raise RuntimeError("Atlas detached identity checksum coverage mismatch")
    if record.get("sha256sums_sha256") != sha256_bytes(payloads[SUMS_NAME]):
        raise RuntimeError("Atlas detached identity checksum-file digest mismatch")
    expected_pages_files = [
        _path_record(f"{PACKAGE_ROOT}/{name}", blobs[f"{PACKAGE_ROOT}/{name}"])
        for name in PAGES_SOURCE_FILES
    ]
    pages_files = record.get("pages_source_files")
    if not isinstance(pages_files, list) or pages_files != expected_pages_files:
        raise RuntimeError("Atlas detached identity Pages-source roster mismatch")


def _safe_output_dir(path: Path) -> Path:
    resolved = path.resolve()
    if resolved in {ROOT.resolve(), (ROOT / PACKAGE_ROOT).resolve()}:
        raise RuntimeError("Release output directory must not be a source directory")
    if path.is_symlink() or (path.exists() and not path.is_dir()):
        raise RuntimeError("Release output directory must be a regular directory")
    if path.exists() and any(path.iterdir()):
        raise RuntimeError("Release output directory must be empty")
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def build_assets(tag: str, output: Path, *, root: Path = ROOT) -> dict[str, dict[str, Any]]:
    _require_runtime()
    _require_clean_worktree(root)
    identity = tag_identity(tag, root=root, require_head=True)
    spec, blobs = tag_snapshot(tag, root=root)
    assets, checksums = _validate_spec(spec)
    destination = _safe_output_dir(output)
    payloads = {
        assets[0]: blobs[f"{PACKAGE_ROOT}/{assets[0]}"],
        assets[1]: blobs[f"{PACKAGE_ROOT}/{assets[1]}"],
        assets[2]: source_archive_bytes(spec, blobs),
    }
    payloads[SUMS_NAME] = sums_bytes(checksums, payloads)
    payloads[IDENTITY_NAME] = build_detached_identity(spec, identity, blobs, payloads)
    if tuple(payloads) != assets:
        raise RuntimeError("Atlas release payload construction did not produce the exact asset roster")
    for name in assets:
        (destination / name).write_bytes(payloads[name])
    verify_assets(tag, destination, root=root)
    return {name: _asset_record(name, payloads[name]) for name in assets}


def _parse_sums(path: Path) -> dict[str, str]:
    output: dict[str, str] = {}
    for line in path.read_text(encoding="ascii").splitlines():
        digest, separator, name = line.partition("  ")
        if (
            separator != "  "
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name) is None
            or name in output
        ):
            raise RuntimeError(f"Malformed Atlas SHA256SUMS record: {line!r}")
        output[name] = digest
    return output


def _extract_archive(archive: Path, destination: Path, spec: dict[str, Any]) -> dict[str, bytes]:
    expected_epoch = spec["build_epoch_unix"]
    expected_names = [f"{SOURCE_ARCHIVE_ROOT}/{path}" for path in ARCHIVE_SOURCE_PATHS]
    extracted: dict[str, bytes] = {}
    with tarfile.open(archive, mode="r:gz") as reader:
        members = reader.getmembers()
        names = [member.name for member in members]
        if names != expected_names:
            raise RuntimeError("Atlas source archive roster differs from the tag-bound source roster")
        for member, name in zip(members, expected_names, strict=True):
            if (
                member.name != name
                or not member.isfile()
                or member.issym()
                or member.islnk()
                or member.uid != 0
                or member.gid != 0
                or member.mtime != expected_epoch
                or member.mode != 0o644
            ):
                raise RuntimeError(f"Atlas source archive member is unsafe or non-deterministic: {name}")
            relative = name.removeprefix(SOURCE_ARCHIVE_ROOT + "/")
            _safe_relative_path(relative)
            stream = reader.extractfile(member)
            if stream is None:
                raise RuntimeError(f"Atlas source archive member is unreadable: {name}")
            data = stream.read()
            if len(data) != member.size:
                raise RuntimeError(f"Atlas source archive member is truncated: {name}")
            extracted[relative] = data
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    return extracted


def _replay_extracted_source(source_root: Path, blobs: dict[str, bytes]) -> None:
    """Rebuild the archive in a disposable copy and bind every producer output."""
    environment = os.environ.copy()
    for name in tuple(environment):
        if name in {"PYTHONHOME", "PYTHONPATH", "PYTEST_ADDOPTS", "PYTEST_PLUGINS"}:
            environment.pop(name)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "tools/build_dark_medium_response_atlas_documents.py",
        ],
        cwd=source_root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "Extracted Atlas source archive failed its document replay.\n"
            + completed.stdout
            + completed.stderr
        )
    for relative in SOURCE_REPLAY_PATHS:
        rebuilt = source_root / relative
        if rebuilt.is_symlink() or not rebuilt.is_file():
            raise RuntimeError(f"Extracted Atlas source replay did not produce {relative}")
        if rebuilt.read_bytes() != blobs[relative]:
            raise RuntimeError(
                "Extracted Atlas source replay differs from the tag-bound producer output: "
                + relative
            )


def verify_assets(
    tag: str,
    assets_directory: Path,
    *,
    root: Path = ROOT,
    extract_to: Path | None = None,
    allow_tag_ancestor: bool = False,
    replay_source: bool = False,
) -> dict[str, dict[str, Any]]:
    _require_runtime()
    _require_clean_worktree(root)
    identity = tag_identity(tag, root=root, require_head=not allow_tag_ancestor)
    if allow_tag_ancestor:
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", identity.commit, "HEAD"],
            cwd=root,
            env=git_environment(root),
            check=False,
        )
        if ancestor.returncode != 0:
            raise RuntimeError("Atlas release tag is not an ancestor of the Pages checkout")
    spec, blobs = tag_snapshot(tag, root=root)
    assets, checksums = _validate_spec(spec)
    directory = assets_directory.resolve()
    if directory.is_symlink() or not directory.is_dir():
        raise RuntimeError("Atlas release asset directory must be a regular directory")
    children = sorted(directory.iterdir(), key=lambda path: path.name)
    if any(path.is_symlink() or not path.is_file() for path in children):
        raise RuntimeError("Atlas release asset directory contains a non-regular entry")
    if [path.name for path in children] != sorted(assets):
        raise RuntimeError("Atlas release asset directory roster differs from the specification")
    payloads = {name: (directory / name).read_bytes() for name in assets}
    sums = _parse_sums(directory / SUMS_NAME)
    if tuple(sums) != checksums:
        raise RuntimeError("Atlas SHA256SUMS coverage differs from the specification")
    for name in checksums:
        if sums[name] != sha256_bytes(payloads[name]):
            raise RuntimeError(f"Atlas checksum mismatch: {name}")
    expected_sums = sums_bytes(checksums, payloads)
    if payloads[SUMS_NAME] != expected_sums:
        raise RuntimeError("Atlas SHA256SUMS bytes are not canonical")
    record = _json_object(payloads[IDENTITY_NAME], IDENTITY_NAME)
    _validate_identity(record, spec, identity, payloads, blobs)
    if payloads[assets[0]] != blobs[f"{PACKAGE_ROOT}/{assets[0]}"]:
        raise RuntimeError("Atlas HTML release asset differs from the annotated tag blob")
    if payloads[assets[1]] != blobs[f"{PACKAGE_ROOT}/{assets[1]}"]:
        raise RuntimeError("Atlas PDF release asset differs from the annotated tag blob")
    expected_archive = source_archive_bytes(spec, blobs)
    if payloads[assets[2]] != expected_archive:
        raise RuntimeError("Atlas source archive is stale or non-deterministic")

    if replay_source:
        with tempfile.TemporaryDirectory(prefix="astra-atlas-source-replay-") as replay_directory:
            replay_destination = Path(replay_directory)
            replayed = _extract_archive(directory / assets[2], replay_destination, spec)
            if replayed != blobs:
                raise RuntimeError("Atlas source-replay extraction differs from annotated-tag blobs")
            _replay_extracted_source(replay_destination / SOURCE_ARCHIVE_ROOT, blobs)

    if extract_to is None:
        temporary = tempfile.TemporaryDirectory(prefix="astra-atlas-release-")
        destination = Path(temporary.name)
    else:
        temporary = None
        destination = _safe_output_dir(extract_to)
    try:
        extracted = _extract_archive(directory / assets[2], destination, spec)
        if extracted != blobs:
            raise RuntimeError("Atlas source archive extraction differs from annotated-tag blobs")
    finally:
        if temporary is not None:
            temporary.cleanup()
    return {name: _asset_record(name, payloads[name]) for name in assets}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    build = subcommands.add_parser("build", help="build an exact five-asset bundle from an annotated tag")
    build.add_argument("--tag", required=True)
    build.add_argument("--output-dir", type=Path, required=True)
    verify = subcommands.add_parser("verify", help="verify an exact five-asset bundle against an annotated tag")
    verify.add_argument("--tag", required=True)
    verify.add_argument("--assets", type=Path, required=True)
    verify.add_argument(
        "--extract-to",
        type=Path,
        help="safely extract the verified source archive for a release-derived consumer",
    )
    verify.add_argument(
        "--allow-tag-ancestor",
        action="store_true",
        help="permit a clean main checkout that is a descendant of the verified release tag",
    )
    verify.add_argument(
        "--replay-source",
        action="store_true",
        help="rebuild the safely extracted source archive and compare its producer outputs",
    )
    args = parser.parse_args()
    if args.command == "build":
        records = build_assets(args.tag, args.output_dir)
        print(json.dumps(records, indent=2, sort_keys=True))
    else:
        records = verify_assets(
            args.tag,
            args.assets,
            extract_to=args.extract_to,
            allow_tag_ancestor=args.allow_tag_ancestor,
            replay_source=args.replay_source,
        )
        print(json.dumps(records, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
