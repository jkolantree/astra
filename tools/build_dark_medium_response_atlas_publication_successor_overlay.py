"""Build the deterministic Dark-Medium Response Atlas S2 publication overlay.

This controller reads the staged Git index, not an ambient directory walk.  The
two self-referential closure files are deliberately excluded; every other path
must be staged, byte-identical in the worktree, and part of the exact delta from
the audited current-main base.
"""

from __future__ import annotations

import sys

if __name__ == "__main__" and not sys.flags.isolated:
    raise SystemExit("Unsafe startup: invoke this controller with Python -I -B.")

import argparse
import hashlib
import json
import os
import platform
import re
import struct
import subprocess
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_URL = (
    "https://jkolantree.github.io/astra/schemas/"
    "dark-medium-response-atlas-publication-successor-overlay-s2.schema.json"
)
SCHEMA_RELATIVE_PATH = (
    "schemas/dark-medium-response-atlas-publication-successor-overlay-s2.schema.json"
)
SCHEMA_PATH = ROOT / SCHEMA_RELATIVE_PATH
OUTPUT_RELATIVE_PATH = (
    "evidence/dark_medium_response_atlas_publication_successor_overlay_s2.json"
)
DEFAULT_OUTPUT = ROOT / OUTPUT_RELATIVE_PATH
GENERATOR_RELATIVE_PATH = (
    "tools/build_dark_medium_response_atlas_publication_successor_overlay.py"
)
GENERATOR_VERSION = "2.0.0"

BASE_COMMIT = "3c1a1325b6b365ba457a03b87cc73139d0c6a629"
BASE_TREE = "ff03d152c98deb65c7246fdd2283cebee71b5857"

S1_PATH = "evidence/dark_medium_response_atlas_successor_overlay_s1.json"
S1_SHA256 = "9d879d9a638dd5882aa546914204ab4b1ea40221adcdfa11f3820dd583628291"
S1_SCHEMA_PATH = "schemas/dark-medium-response-atlas-successor-overlay-s1.schema.json"
S1_SCHEMA_SHA256 = "4a4433b83a62dfd18ea65b761372888a1ab67e5dac1ec8b5386edcb7d9e4e76d"
S1_GENERATOR_PATH = "tools/build_dark_medium_response_atlas_successor_overlay.py"
S1_GENERATOR_SHA256 = "e4f4255750fa72a25b4353564c4ecaec68a56408aaa761219b339c8bab546efa"
S1_TEST_PATH = "tests/test_dark_medium_response_atlas_successor_overlay.py"
S1_TEST_SHA256 = "10a775fe4b928a45255a59de2ead69dd01e690db6325d546c86f2c4c5554d8d6"
S1_BASE_COMMIT = "f8b32ef0af9cb6804f256490b4daafbdba43740e"
S1_BASE_TREE = "251895700cdfc80addf180d46178b5aa8c43528c"
S1_SOURCE_PROJECTION_SHA256 = (
    "e59d518f7892d94b0f7a035879b3bb16c1b0bc9cb95c83bc4f038ab36052bdba"
)
S1_PACKAGE_AGGREGATE_SHA256 = (
    "5993bcf52c786a1b48f05e303228b99ae5e7f22fd879058efd2af12b754abaf5"
)
S1_M1_SHA256 = "a655277bb9f241d8aa28a3ab11eacd03ae097befa5650c02dc50a66385555fd9"

LIVE_M1_PATH = "evidence/claim_source_coverage_v1.0.7_maintenance_overlay_m1.json"
LIVE_M1_SHA256 = "4287e047fabe501db944791fce0423f93ca556e67922bb50386f566a2e9466ad"
LIVE_M1_SOURCE_PROJECTION_SHA256 = (
    "ba4277bf11cb5a2b4d5d247f33433361636b93d5ec71d7ce29939be40f3ca52f"
)
V108_MANIFEST_PATH = (
    "resources/sppt-astra-v1.0.8-candidate/package/candidate_package_manifest.json"
)
V108_MANIFEST_SHA256 = (
    "c0bcbcbd6ccc4d39746d7218e9398f8efc991c6b7f4981ecb1a8a4b5935b6e6d"
)
V108_SOURCE_PACKAGE_SHA256 = (
    "55b8962176680859064fa2ebc009bb45ddc0cce987bce0bc16206faa4c7c387a"
)

PACKAGE_ROOT = "resources/dark-medium-response-atlas/v0.1.0"
PACKAGE_PATHS = (
    f"{PACKAGE_ROOT}/CHANGELOG.md",
    f"{PACKAGE_ROOT}/CITATION.cff",
    f"{PACKAGE_ROOT}/LICENSE_MAP.md",
    f"{PACKAGE_ROOT}/README.md",
    f"{PACKAGE_ROOT}/RELEASE_NOTES.md",
    f"{PACKAGE_ROOT}/RELEASE_SPEC.json",
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
RELEASE_SPEC_PATH = f"{PACKAGE_ROOT}/RELEASE_SPEC.json"
RELEASE_SPEC_SCHEMA_PATH = "schemas/supplemental-release-spec-v2.schema.json"
PUBLICATION_IDENTITY_PATH = f"{PACKAGE_ROOT}/publication-identity.json"
PUBLICATION_IDENTITY_SCHEMA_PATH = (
    "schemas/dark-medium-response-atlas-publication-identity-v1.schema.json"
)
PAGES_ORIGIN = "https://jkolantree.github.io/astra"
RELEASE_ASSETS = (
    "dark-medium-response-atlas-v0.1.0.html",
    "dark-medium-response-atlas-v0.1.0.pdf",
    "dark-medium-response-atlas-v0.1.0-source.tar.gz",
    "SHA256SUMS",
    "dark-medium-response-atlas-v0.1.0-release-identity.json",
)
CHECKSUM_ASSETS = RELEASE_ASSETS[:3]

IDENTITY_CLOSURE_PATHS = frozenset({"MANIFEST.sha256", OUTPUT_RELATIVE_PATH})
EXPECTED_DELETED_PATHS = frozenset({"AGENTS.md"})

# This is deliberately an exact, reviewable set rather than a prefix allowlist.
# The finalizer must reconcile it with the staged delta before serializing S2.
SOURCE_CHANGE_ROSTER = frozenset(
    {
        ".github/ISSUE_TEMPLATE/config.yml",
        ".github/workflows/pages.yml",
        ".github/workflows/release-dark-medium-response-atlas.yml",
        ".github/workflows/verify.yml",
        ".gitignore",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "LICENSE_MAP.md",
        "PROVENANCE.md",
        "PUBLICATIONS.md",
        "README.md",
        "RELEASE_NOTES_earth-instrument-wp-0.1.md",
        "REPRODUCING.md",
        "docs/404.html",
        "docs/index.html",
        "docs/resources/index.html",
        "docs/style.css",
        "evidence/README.md",
        "evidence/pages_admission_v1.json",
        S1_PATH,
        "resources/README.md",
        *PACKAGE_PATHS,
        "resources/dark-medium-response-atlas/draft-v0.1.0/CHANGE_LOG.md",
        "resources/dark-medium-response-atlas/draft-v0.1.0/DARK_MEDIUM_RESPONSE_ATLAS.md",
        "resources/dark-medium-response-atlas/draft-v0.1.0/LICENSE_MAP.md",
        "resources/dark-medium-response-atlas/draft-v0.1.0/README.md",
        "resources/dark-medium-response-atlas/draft-v0.1.0/claim_ledger.csv",
        "resources/dark-medium-response-atlas/draft-v0.1.0/draft_metadata.json",
        "resources/dark-medium-response-atlas/draft-v0.1.0/novelty_ledger.csv",
        "resources/dark-medium-response-atlas/draft-v0.1.0/source_ledger.csv",
        "schemas/README.md",
        "schemas/dark-medium-response-atlas-html-accessibility-v1.schema.json",
        "schemas/dark-medium-response-atlas-pdf-inspection-v1.schema.json",
        "schemas/dark-medium-response-atlas-publication-identity-v1.schema.json",
        SCHEMA_RELATIVE_PATH,
        "schemas/dark-medium-response-atlas-visual-review-v1.schema.json",
        S1_SCHEMA_PATH,
        "schemas/external-link-observations-v1.schema.json",
        "schemas/pages-admission-v1.schema.json",
        "schemas/supplemental-release-identity-v2.schema.json",
        RELEASE_SPEC_SCHEMA_PATH,
        "tests/conftest.py",
        "tests/test_dark_medium_response_atlas_documents.py",
        "tests/test_dark_medium_response_atlas_publication_successor_overlay_s2.py",
        "tests/test_dark_medium_response_atlas_release.py",
        "tests/test_dark_medium_response_atlas_successor_overlay.py",
        "tests/test_dark_medium_response_atlas_successor_overlay_historical.py",
        "tests/test_link_audits.py",
        "tests/test_pages_admission.py",
        "tests/test_pages_contract.py",
        "tools/assemble_pages.py",
        GENERATOR_RELATIVE_PATH,
        "tools/build_dark_medium_response_atlas_documents.py",
        "tools/dark_medium_response_atlas_document_helpers.py",
        "tools/dark_medium_response_atlas_pdf_helpers.py",
        S1_GENERATOR_PATH,
        "tools/build_pages_admission.py",
        "tools/check_dark_medium_response_atlas_html.py",
        "tools/check_external_links.py",
        "tools/check_pages_admission.py",
        "tools/check_pages_links.py",
        "tools/check_repository.py",
        "tools/check_repository_links.py",
        "tools/dark_medium_response_atlas_release.py",
        "tools/inspect_dark_medium_response_atlas_pdf.py",
        "tools/link_audit_common.py",
        "tools/render_dark_medium_response_atlas_pdf.py",
        "tools/verify.py",
    }
)
FULL_CHANGE_ROSTER = (
    SOURCE_CHANGE_ROSTER | EXPECTED_DELETED_PATHS | IDENTITY_CLOSURE_PATHS
)

RUNTIME_IDENTITY = f"python=={platform.python_version()}"
RUNTIME_IMPLEMENTATION = platform.python_implementation()
AUTHORITATIVE_RUNTIME_IDENTITY = "python==3.12.10"
RUNTIME_PATH = "RUNTIME.json"
LOCK_PATH = "requirements-lock.txt"
SOURCE_PROJECTION_SCHEME = "astra-source-projection-v1"
SOURCE_PROJECTION_SCOPE = (
    "astra-dark-medium-response-atlas-publication-successor-s2-repository-source-v1"
)
PACKAGE_ROSTER_SCHEME = "astra-package-roster-v1"
PACKAGE_ROSTER_SCOPE = (
    "astra-dark-medium-response-atlas-v0.1.0-publication-package-v1"
)
CANONICAL_SERIALIZATION = "astra-binary-length-prefixed-v1"
SAFE_PATH_PATTERN = re.compile(
    r"(?!/)(?!.*//)(?!.*(?:^|/)\.{1,2}(?:/|$))[A-Za-z0-9._/-]*[A-Za-z0-9._-]"
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
class SnapshotEntry:
    path: str
    mode: str
    object_id: str
    data: bytes

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.data).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def load_json_bytes(value: bytes, *, source: str) -> dict[str, Any]:
    document = json.loads(value.decode("utf-8"))
    if not isinstance(document, dict):
        raise RuntimeError(f"Expected a JSON object at {source}")
    return document


def git_environment(root: Path) -> dict[str, str]:
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


def git_command(
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


def git_path_set(arguments: list[str], *, root: Path = ROOT) -> set[str]:
    raw = git_command(arguments, root=root, binary=True)
    if not isinstance(raw, bytes):
        raise TypeError("Expected binary Git output")
    try:
        return {item for item in raw.decode("ascii").split("\0") if item}
    except UnicodeDecodeError as error:
        raise RuntimeError("Candidate paths must be ASCII") from error


def resolve_commit(revision: str, *, root: Path = ROOT) -> str:
    """Resolve a caller-selected revision to one immutable commit object."""

    try:
        value = git_command(
            ["rev-parse", "--verify", f"{revision}^{{commit}}"], root=root
        )
    except subprocess.CalledProcessError as error:
        raise RuntimeError(f"Cannot resolve committed S2 revision: {revision!r}") from error
    if not isinstance(value, str):
        raise TypeError("Expected textual Git commit identity")
    commit = value.strip()
    if re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit) is None:
        raise RuntimeError("Resolved S2 revision is not a Git commit identity")
    return commit


def assert_base_is_ancestor(
    base_commit: str, revision: str, *, root: Path = ROOT
) -> None:
    """Require the audited base to be in the verified revision's history."""

    try:
        git_command(
            ["merge-base", "--is-ancestor", base_commit, revision], root=root
        )
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            "Audited current-main S2 base is not an ancestor of "
            f"the candidate revision: {revision}"
        ) from error


def _validate_path(path: str) -> None:
    try:
        path.encode("ascii")
    except UnicodeEncodeError as error:
        raise RuntimeError(f"Projection path is not ASCII: {path!r}") from error
    if SAFE_PATH_PATTERN.fullmatch(path) is None:
        raise RuntimeError(f"Unsafe projection path: {path!r}")


def _index_metadata(root: Path) -> tuple[bytes, dict[str, tuple[str, str]]]:
    raw = git_command(["ls-files", "--stage", "-z"], root=root, binary=True)
    if not isinstance(raw, bytes):
        raise TypeError("Expected binary Git output")
    entries: dict[str, tuple[str, str]] = {}
    casefolded: dict[str, str] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        header, separator, encoded_path = record.partition(b"\t")
        fields = header.split()
        if not separator or len(fields) != 3:
            raise RuntimeError("Malformed Git index record")
        mode, object_id, stage = (field.decode("ascii") for field in fields)
        if stage != "0":
            raise RuntimeError("Unmerged Git index stage blocks source projection")
        if mode not in {"100644", "100755"}:
            raise RuntimeError(f"Unsupported projection Git mode: {mode}")
        if re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", object_id) is None:
            raise RuntimeError("Invalid or intent-to-add Git index object")
        path = encoded_path.decode("ascii")
        _validate_path(path)
        if path in entries or path.casefold() in casefolded:
            raise RuntimeError(f"Duplicate or case-fold-colliding index path: {path}")
        casefolded[path.casefold()] = path
        entries[path] = (mode, object_id)
    return raw, entries


def assert_supported_runtime() -> None:
    if (
        RUNTIME_IMPLEMENTATION != "CPython"
        or RUNTIME_IDENTITY != AUTHORITATIVE_RUNTIME_IDENTITY
    ):
        raise RuntimeError(
            "S2 generation requires release-authoritative CPython 3.12.10; observed "
            f"{RUNTIME_IMPLEMENTATION} {platform.python_version()}"
        )


def assert_no_hidden_index_flags(root: Path = ROOT) -> None:
    raw = git_command(["ls-files", "-v", "-z"], root=root, binary=True)
    if not isinstance(raw, bytes):
        raise TypeError("Expected binary Git output")
    hidden = [
        record[2:].decode("utf-8", errors="replace")
        for record in raw.split(b"\0")
        if record and (record[:1] == b"S" or record[:1].islower())
    ]
    if hidden:
        raise RuntimeError("Index flags hide candidate changes: " + ", ".join(hidden))
    if git_path_set(["ls-files", "--unmerged", "-z"], root=root):
        raise RuntimeError("Unmerged index entries block candidate identity")


def assert_exact_change_roster(
    root: Path = ROOT,
    *,
    base_commit: str = BASE_COMMIT,
    source_paths: Collection[str] = SOURCE_CHANGE_ROSTER,
    deleted_paths: Collection[str] = EXPECTED_DELETED_PATHS,
    closure_paths: Collection[str] = IDENTITY_CLOSURE_PATHS,
) -> set[str]:
    changed = git_path_set(
        ["diff", "--cached", "--no-renames", "--name-only", "-z", base_commit, "--"],
        root=root,
    )
    expected = set(source_paths) | set(deleted_paths) | set(closure_paths)
    # Closure paths may be absent before their final deterministic serialization.
    if changed - expected or expected - set(closure_paths) - changed:
        missing = sorted((expected - set(closure_paths)) - changed)
        unexpected = sorted(changed - expected)
        raise RuntimeError(
            "Staged S2 change roster mismatch: "
            f"missing={','.join(missing) or '-'}; "
            f"unexpected={','.join(unexpected) or '-'}"
        )
    deleted = git_path_set(
        [
            "diff",
            "--cached",
            "--no-renames",
            "--diff-filter=D",
            "--name-only",
            "-z",
            base_commit,
            "--",
        ],
        root=root,
    )
    if deleted != set(deleted_paths):
        raise RuntimeError(
            "S2 deletion roster mismatch: "
            f"expected={','.join(sorted(deleted_paths))}; "
            f"observed={','.join(sorted(deleted)) or '-'}"
        )
    return changed


def assert_exact_committed_change_roster(
    root: Path,
    *,
    commit: str,
    base_commit: str = BASE_COMMIT,
    source_paths: Collection[str] = SOURCE_CHANGE_ROSTER,
    deleted_paths: Collection[str] = EXPECTED_DELETED_PATHS,
    closure_paths: Collection[str] = IDENTITY_CLOSURE_PATHS,
) -> set[str]:
    """Require a final commit, not an index, to carry the exact S2 delta."""

    changed = git_path_set(
        [
            "diff",
            "--no-renames",
            "--name-only",
            "-z",
            base_commit,
            commit,
            "--",
        ],
        root=root,
    )
    expected = set(source_paths) | set(deleted_paths) | set(closure_paths)
    if changed != expected:
        missing = sorted(expected - changed)
        unexpected = sorted(changed - expected)
        raise RuntimeError(
            "Committed S2 change roster mismatch: "
            f"missing={','.join(missing) or '-'}; "
            f"unexpected={','.join(unexpected) or '-'}"
        )
    deleted = git_path_set(
        [
            "diff",
            "--no-renames",
            "--diff-filter=D",
            "--name-only",
            "-z",
            base_commit,
            commit,
            "--",
        ],
        root=root,
    )
    if deleted != set(deleted_paths):
        raise RuntimeError(
            "Committed S2 deletion roster mismatch: "
            f"expected={','.join(sorted(deleted_paths))}; "
            f"observed={','.join(sorted(deleted)) or '-'}"
        )
    return changed


def committed_revision_snapshot(
    revision: str, *, root: Path = ROOT
) -> tuple[str, str, dict[str, SnapshotEntry]]:
    """Read only regular-file blobs from a resolved committed tree."""

    commit = resolve_commit(revision, root=root)
    tree_value = git_command(["rev-parse", f"{commit}^{{tree}}"], root=root)
    if not isinstance(tree_value, str):
        raise TypeError("Expected textual Git tree identity")
    tree = tree_value.strip()
    if re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", tree) is None:
        raise RuntimeError("Resolved S2 revision has an invalid Git tree identity")
    raw = git_command(["ls-tree", "-r", "-z", commit], root=root, binary=True)
    if not isinstance(raw, bytes):
        raise TypeError("Expected binary Git tree output")
    snapshot: dict[str, SnapshotEntry] = {}
    casefolded: dict[str, str] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        header, separator, encoded_path = record.partition(b"\t")
        fields = header.split()
        if not separator or len(fields) != 3:
            raise RuntimeError("Malformed committed Git tree record")
        mode, object_type, object_id = (field.decode("ascii") for field in fields)
        if object_type != "blob" or mode not in {"100644", "100755"}:
            raise RuntimeError("Committed S2 tree contains unsupported non-regular file")
        if re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", object_id) is None:
            raise RuntimeError("Committed S2 tree contains an invalid blob identity")
        try:
            path = encoded_path.decode("ascii")
        except UnicodeDecodeError as error:
            raise RuntimeError("Committed S2 paths must be ASCII") from error
        _validate_path(path)
        if path in snapshot or path.casefold() in casefolded:
            raise RuntimeError(f"Duplicate or case-fold-colliding committed path: {path}")
        data = git_command(["cat-file", "blob", object_id], root=root, binary=True)
        if not isinstance(data, bytes):
            raise TypeError("Expected binary committed Git blob")
        casefolded[path.casefold()] = path
        snapshot[path] = SnapshotEntry(path, mode, object_id, data)
    return commit, tree, snapshot


def assert_committed_snapshot_membership(
    snapshot: Mapping[str, SnapshotEntry],
    *,
    source_paths: Collection[str] = SOURCE_CHANGE_ROSTER,
    deleted_paths: Collection[str] = EXPECTED_DELETED_PATHS,
    closure_paths: Collection[str] = IDENTITY_CLOSURE_PATHS,
) -> None:
    required = set(source_paths) | set(closure_paths)
    missing = required - set(snapshot)
    if missing:
        raise RuntimeError(
            "Committed S2 tree is missing required paths: " + ", ".join(sorted(missing))
        )
    present_deleted = set(deleted_paths) & set(snapshot)
    if present_deleted:
        raise RuntimeError(
            "Committed S2 tree retains intended deletions: "
            + ", ".join(sorted(present_deleted))
        )


def repository_snapshot(
    root: Path = ROOT,
    *,
    base_commit: str = BASE_COMMIT,
    base_tree: str = BASE_TREE,
    source_paths: Collection[str] = SOURCE_CHANGE_ROSTER,
    deleted_paths: Collection[str] = EXPECTED_DELETED_PATHS,
    closure_paths: Collection[str] = IDENTITY_CLOSURE_PATHS,
) -> dict[str, SnapshotEntry]:
    assert_no_hidden_index_flags(root)
    observed_tree = str(
        git_command(["rev-parse", f"{base_commit}^{{tree}}"], root=root)
    ).strip()
    if observed_tree != base_tree:
        raise RuntimeError("Audited current-main S2 base tree identity drift")
    assert_base_is_ancestor(base_commit, "HEAD", root=root)
    closure = set(closure_paths)
    untracked = git_path_set(
        ["ls-files", "--others", "--exclude-standard", "-z"], root=root
    )
    if untracked - closure:
        raise RuntimeError(
            "Untracked source paths block S2 projection: "
            + ", ".join(sorted(untracked - closure))
        )
    unstaged = git_path_set(
        ["diff", "--no-renames", "--name-only", "-z", "--"], root=root
    )
    if unstaged - closure:
        raise RuntimeError(
            "Source files must be staged before S2 projection: "
            + ", ".join(sorted(unstaged - closure))
        )
    assert_exact_change_roster(
        root,
        base_commit=base_commit,
        source_paths=source_paths,
        deleted_paths=deleted_paths,
        closure_paths=closure,
    )
    before, metadata = _index_metadata(root)
    snapshot: dict[str, SnapshotEntry] = {}
    for path, (mode, object_id) in metadata.items():
        data = git_command(["cat-file", "blob", object_id], root=root, binary=True)
        if not isinstance(data, bytes):
            raise TypeError("Expected binary Git blob output")
        if path not in closure:
            worktree_path = root / path
            if worktree_path.is_symlink() or not worktree_path.is_file():
                raise RuntimeError(f"Projected path is not a regular file: {path}")
            if worktree_path.read_bytes() != data:
                raise RuntimeError(f"Working-tree bytes differ from staged blob: {path}")
        snapshot[path] = SnapshotEntry(path, mode, object_id, data)
    after, _ = _index_metadata(root)
    if after != before:
        raise RuntimeError("Git index changed while S2 projection was read")
    if set(deleted_paths) & set(snapshot):
        raise RuntimeError("Authorized private-policy deletion remains in candidate index")
    missing = set(source_paths) - set(snapshot)
    if missing:
        raise RuntimeError("Declared S2 source paths absent from index: " + ", ".join(sorted(missing)))
    return snapshot


def _length_prefixed(value: bytes) -> bytes:
    if len(value) > 0xFFFFFFFF:
        raise RuntimeError("Canonical field exceeds uint32 framing limit")
    return struct.pack(">I", len(value)) + value


def serialize_file_entries(
    *, domain: bytes, scope: str, entries: list[dict[str, Any]], excluded_paths: Collection[str] = ()
) -> bytes:
    exclusions = sorted(excluded_paths)
    payload = bytearray(b"ASTRA\0" + domain + b"\0V1\0")
    payload.extend(_length_prefixed(scope.encode("ascii")))
    payload.extend(struct.pack(">I", len(exclusions)))
    for path in exclusions:
        _validate_path(path)
        payload.extend(_length_prefixed(path.encode("ascii")))
    normalized = sorted(entries, key=lambda item: str(item["path"]))
    paths = [str(item["path"]) for item in normalized]
    if len(paths) != len(set(paths)) or len(paths) != len({p.casefold() for p in paths}):
        raise RuntimeError("Duplicate or case-fold-colliding canonical entry")
    payload.extend(struct.pack(">I", len(normalized)))
    for entry in normalized:
        if set(entry) != {"path", "mode", "bytes", "sha256"}:
            raise RuntimeError("Malformed canonical entry")
        path = str(entry["path"])
        mode = str(entry["mode"])
        byte_count = entry["bytes"]
        digest = str(entry["sha256"])
        _validate_path(path)
        if mode not in {"100644", "100755"}:
            raise RuntimeError("Unsupported canonical mode")
        if not isinstance(byte_count, int) or isinstance(byte_count, bool) or byte_count < 0:
            raise RuntimeError("Invalid canonical byte count")
        if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise RuntimeError("Invalid canonical SHA-256")
        payload.extend(_length_prefixed(path.encode("ascii")))
        payload.extend(_length_prefixed(mode.encode("ascii")))
        payload.extend(struct.pack(">Q", byte_count))
        payload.extend(bytes.fromhex(digest))
    return bytes(payload)


def file_entries(
    snapshot: Mapping[str, SnapshotEntry], paths: Collection[str]
) -> list[dict[str, Any]]:
    return [
        {
            "path": path,
            "mode": snapshot[path].mode,
            "bytes": len(snapshot[path].data),
            "sha256": snapshot[path].sha256,
        }
        for path in sorted(paths)
    ]


def build_source_projection(snapshot: Mapping[str, SnapshotEntry]) -> dict[str, Any]:
    exclusions = sorted(IDENTITY_CLOSURE_PATHS)
    entries = file_entries(snapshot, set(snapshot) - set(exclusions))
    serialized = serialize_file_entries(
        domain=b"SOURCE-PROJECTION",
        scope=SOURCE_PROJECTION_SCOPE,
        entries=entries,
        excluded_paths=exclusions,
    )
    return {
        "scheme": SOURCE_PROJECTION_SCHEME,
        "scope": SOURCE_PROJECTION_SCOPE,
        "digest_algorithm": "sha256",
        "canonical_byte_domain": "git-index-blob",
        "serialization": CANONICAL_SERIALIZATION,
        "path_encoding": "ascii-posix",
        "entry_count": len(entries),
        "canonical_bytes": len(serialized),
        "excluded_paths": exclusions,
        "entries": entries,
        "sha256": sha256_bytes(serialized),
    }


def build_package_identity(snapshot: Mapping[str, SnapshotEntry]) -> dict[str, Any]:
    observed = {path for path in snapshot if path.startswith(PACKAGE_ROOT + "/")}
    if observed != set(PACKAGE_PATHS):
        raise RuntimeError(
            "Publication package roster mismatch: "
            f"missing={','.join(sorted(set(PACKAGE_PATHS) - observed)) or '-'}; "
            f"unexpected={','.join(sorted(observed - set(PACKAGE_PATHS))) or '-'}"
        )
    entries = file_entries(snapshot, PACKAGE_PATHS)
    serialized = serialize_file_entries(
        domain=b"PACKAGE-ROSTER", scope=PACKAGE_ROSTER_SCOPE, entries=entries
    )
    return {
        "root": PACKAGE_ROOT,
        "status": "supplemental_working_paper_v0.1.0",
        "roster": list(PACKAGE_PATHS),
        "file_count": len(entries),
        "files": entries,
        "aggregate": {
            "scheme": PACKAGE_ROSTER_SCHEME,
            "scope": PACKAGE_ROSTER_SCOPE,
            "digest_algorithm": "sha256",
            "canonical_byte_domain": "git-index-blob",
            "serialization": CANONICAL_SERIALIZATION,
            "canonical_bytes": len(serialized),
            "sha256": sha256_bytes(serialized),
        },
    }


def verify_historical_s1(snapshot: Mapping[str, SnapshotEntry]) -> dict[str, Any]:
    fixed = {
        S1_PATH: S1_SHA256,
        S1_SCHEMA_PATH: S1_SCHEMA_SHA256,
        S1_GENERATOR_PATH: S1_GENERATOR_SHA256,
        S1_TEST_PATH: S1_TEST_SHA256,
    }
    for path, digest in fixed.items():
        if path not in snapshot or snapshot[path].sha256 != digest:
            raise RuntimeError(f"Historical S1 byte identity drifted: {path}")
    record = load_json_bytes(snapshot[S1_PATH].data, source=S1_PATH)
    expected = {
        "overlay_id": "dark-medium-response-atlas-successor-s1",
        "status": "unpromoted_supplemental_resource_admission",
    }
    if {key: record.get(key) for key in expected} != expected:
        raise RuntimeError("Historical S1 semantic identity drifted")
    if record.get("base_identity") != {
        "commit": S1_BASE_COMMIT,
        "relationship": "audited_repository_base",
        "tree": S1_BASE_TREE,
    }:
        raise RuntimeError("Historical S1 base identity drifted")
    projection = record.get("source_projection")
    package = record.get("package")
    predecessor = record.get("predecessor_overlay")
    if not isinstance(projection, dict) or projection.get("sha256") != S1_SOURCE_PROJECTION_SHA256:
        raise RuntimeError("Historical S1 projection identity drifted")
    if not isinstance(package, dict) or not isinstance(package.get("aggregate"), dict):
        raise RuntimeError("Historical S1 package identity is malformed")
    if package["aggregate"].get("sha256") != S1_PACKAGE_AGGREGATE_SHA256:
        raise RuntimeError("Historical S1 package aggregate drifted")
    if not isinstance(predecessor, dict) or predecessor.get("sha256") != S1_M1_SHA256:
        raise RuntimeError("Historical S1-era M1 identity drifted")
    package_files = package.get("files")
    if not isinstance(package_files, list):
        raise RuntimeError("Historical S1 package file records are malformed")
    for item in package_files:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise RuntimeError("Historical S1 package file record is malformed")
        path = item["path"]
        if path not in snapshot:
            raise RuntimeError(f"Historical S1 package path is absent: {path}")
        if item.get("bytes") != len(snapshot[path].data) or item.get("sha256") != snapshot[path].sha256:
            raise RuntimeError(f"Historical S1 package bytes drifted: {path}")
    return {
        "path": S1_PATH,
        "sha256": S1_SHA256,
        "overlay_id": "dark-medium-response-atlas-successor-s1",
        "status": "unpromoted_supplemental_resource_admission",
        "base_commit": S1_BASE_COMMIT,
        "base_tree": S1_BASE_TREE,
        "source_projection_sha256": S1_SOURCE_PROJECTION_SHA256,
        "package_aggregate_sha256": S1_PACKAGE_AGGREGATE_SHA256,
        "s1_era_m1": {
            "path": LIVE_M1_PATH,
            "sha256": S1_M1_SHA256,
            "relationship": "historical_s1_predecessor_bytes_not_live_current_main",
        },
        "relationship": "historical_unpromoted_source_admission_preserved_byte_for_byte",
        "inherited_authority": False,
    }


def verify_live_predecessor(snapshot: Mapping[str, SnapshotEntry]) -> dict[str, Any]:
    expected = {
        LIVE_M1_PATH: LIVE_M1_SHA256,
        V108_MANIFEST_PATH: V108_MANIFEST_SHA256,
    }
    for path, digest in expected.items():
        if path not in snapshot or snapshot[path].sha256 != digest:
            raise RuntimeError(f"Live current-main predecessor drifted: {path}")
    m1 = load_json_bytes(snapshot[LIVE_M1_PATH].data, source=LIVE_M1_PATH)
    maintenance = m1.get("maintenance_overlay")
    if not isinstance(maintenance, dict):
        raise RuntimeError("Live M1 maintenance-overlay identity is malformed")
    projection = maintenance.get("source_projection")
    if not isinstance(projection, dict) or projection.get("sha256") != LIVE_M1_SOURCE_PROJECTION_SHA256:
        raise RuntimeError("Live M1 source projection identity drifted")
    candidate = load_json_bytes(snapshot[V108_MANIFEST_PATH].data, source=V108_MANIFEST_PATH)
    if candidate.get("status") != "reviewed_unpromoted_candidate":
        raise RuntimeError("v1.0.8 candidate status was promoted or rewritten")
    source_digest = candidate.get("source_package_sha256")
    if source_digest is None:
        source_digest = candidate.get("source_intake_sha256")
    if source_digest != V108_SOURCE_PACKAGE_SHA256:
        raise RuntimeError("v1.0.8 source-package identity drifted")
    return {
        "m1": {
            "path": LIVE_M1_PATH,
            "sha256": LIVE_M1_SHA256,
            "source_projection_sha256": LIVE_M1_SOURCE_PROJECTION_SHA256,
            "status": "candidate_only",
        },
        "v1_0_8_candidate": {
            "manifest_path": V108_MANIFEST_PATH,
            "manifest_sha256": V108_MANIFEST_SHA256,
            "source_package_sha256": V108_SOURCE_PACKAGE_SHA256,
            "status": "reviewed_unpromoted_candidate",
        },
        "relationship": "live_current_main_m1_and_v1_0_8_era_boundary_not_promoted",
        "inherited_authority": False,
    }


def verify_release_contract(snapshot: Mapping[str, SnapshotEntry]) -> dict[str, Any]:
    spec = load_json_bytes(snapshot[RELEASE_SPEC_PATH].data, source=RELEASE_SPEC_PATH)
    schema = load_json_bytes(
        snapshot[RELEASE_SPEC_SCHEMA_PATH].data, source=RELEASE_SPEC_SCHEMA_PATH
    )
    Draft7Validator(schema, format_checker=FormatChecker()).validate(spec)
    expected = {
        "publication_line_id": "dark-medium-response-atlas",
        "version": "0.1.0",
        "tag": "dark-medium-response-atlas-v0.1.0",
        "namespace": PACKAGE_ROOT,
        "release_asset_allowlist": list(RELEASE_ASSETS),
        "checksum_asset_names": list(CHECKSUM_ASSETS),
        "identity_excludes_self": True,
        "github_release": {
            "draft": False,
            "prerelease": True,
            "make_latest": False,
            "immutable_required": True,
        },
    }
    for key, value in expected.items():
        if spec.get(key) != value:
            raise RuntimeError(f"Atlas release contract mismatch for {key}")
    pages = spec.get("pages")
    expected_pages = {
        "versioned_route": "/resources/dark-medium-response-atlas/v0.1.0/",
        "latest_route": "/resources/dark-medium-response-atlas/latest/",
        "citation_route": "/resources/dark-medium-response-atlas/v0.1.0/",
    }
    if not isinstance(pages, dict) or any(
        pages.get(key) != value for key, value in expected_pages.items()
    ):
        raise RuntimeError("Atlas Pages release contract mismatch")
    if pages["citation_route"] != pages["versioned_route"]:
        raise RuntimeError("Atlas citation route must be the immutable versioned route")
    publication_identity = load_json_bytes(
        snapshot[PUBLICATION_IDENTITY_PATH].data, source=PUBLICATION_IDENTITY_PATH
    )
    publication_identity_schema = load_json_bytes(
        snapshot[PUBLICATION_IDENTITY_SCHEMA_PATH].data,
        source=PUBLICATION_IDENTITY_SCHEMA_PATH,
    )
    Draft7Validator(publication_identity_schema, format_checker=FormatChecker()).validate(
        publication_identity
    )
    if publication_identity.get("canonical_url") != (
        f"{PAGES_ORIGIN}{pages['citation_route']}"
    ):
        raise RuntimeError(
            "Atlas publication identity canonical URL does not bind the citation route"
        )
    return {
        "spec_path": RELEASE_SPEC_PATH,
        "spec_sha256": snapshot[RELEASE_SPEC_PATH].sha256,
        "version": "0.1.0",
        "tag": "dark-medium-response-atlas-v0.1.0",
        "asset_allowlist": list(RELEASE_ASSETS),
        "checksum_asset_names": list(CHECKSUM_ASSETS),
        "github_release": expected["github_release"],
        "versioned_pages_route": pages["versioned_route"],
        "latest_pages_route": pages["latest_route"],
        "citation_pages_route": pages["citation_route"],
    }


def build_record_from_snapshot(
    snapshot: Mapping[str, SnapshotEntry],
) -> dict[str, Any]:
    historical = verify_historical_s1(snapshot)
    live = verify_live_predecessor(snapshot)
    package = build_package_identity(snapshot)
    release = verify_release_contract(snapshot)
    return {
        "schema": SCHEMA_URL,
        "schema_version": "2.0.0",
        "overlay_id": "dark-medium-response-atlas-publication-successor-s2",
        "overlay_kind": "supplemental_publication_admission",
        "status": "publication_candidate",
        "prepared_date": "2026-09-01",
        "current_main_base": {
            "commit": BASE_COMMIT,
            "tree": BASE_TREE,
            "relationship": "fresh_current_main_publication_base",
        },
        "historical_s1": historical,
        "live_predecessor": live,
        "change_roster": {
            "expected_paths": sorted(FULL_CHANGE_ROSTER),
            "source_paths": sorted(SOURCE_CHANGE_ROSTER),
            "identity_closure_paths": sorted(IDENTITY_CLOSURE_PATHS),
        },
        "package": package,
        "release_contract": release,
        "source_projection": build_source_projection(snapshot),
        "authority": {
            "grants": [
                "exact_dark_medium_response_atlas_v0.1.0_repository_admission",
                "exact_five_asset_namespaced_github_prerelease_admission",
                "exact_versioned_and_namespace_latest_pages_admission",
            ],
            "does_not_grant": [
                "astra_core_authority",
                "m1_promotion",
                "v1.0.8_promotion",
                "empirical_validation",
                "peer_review",
                "dark_matter_detection",
                "doi_or_zenodo_authority",
                "scientific_priority",
            ],
            "supersedes_s1": False,
            "supersedes_m1": False,
            "promotes_v1_0_8": False,
        },
        "generator": {
            "path": GENERATOR_RELATIVE_PATH,
            "version": GENERATOR_VERSION,
            "runtime": RUNTIME_IDENTITY,
            "runtime_implementation": RUNTIME_IMPLEMENTATION,
            "runtime_contract_path": RUNTIME_PATH,
            "runtime_contract_sha256": snapshot[RUNTIME_PATH].sha256,
            "dependency_lock_path": LOCK_PATH,
            "dependency_lock_sha256": snapshot[LOCK_PATH].sha256,
            "schema_path": SCHEMA_RELATIVE_PATH,
            "schema_sha256": snapshot[SCHEMA_RELATIVE_PATH].sha256,
            "output_path": OUTPUT_RELATIVE_PATH,
        },
        "verification_scope": {
            "binds": [
                "historical_s1_exact_bytes_and_its_s1_era_m1_hash",
                "live_current_main_m1_and_v1.0.8_candidate_boundary",
                "exact_current_main_base_delta",
                "full_staged_git_index_except_identity_closure",
                "exact_final_commit_tree_reconstruction_and_s2_byte_identity",
                "exact_v0.1.0_package_roster_modes_and_bytes",
                "exact_stable_resource_version_and_prerelease_publication_contract",
            ],
            "rejects": [
                "unexpected_or_missing_changed_paths",
                "hidden_or_unmerged_index_state",
                "unstaged_or_untracked_source_content",
                "schema_valid_but_nonreconstructed_s2_record",
                "package_roster_or_byte_drift",
                "s1_or_live_m1_byte_drift",
                "v1.0.8_candidate_promotion",
                "core_release_or_latest_authority_transfer",
            ],
            "closure_note": (
                "MANIFEST.sha256 and this S2 JSON are excluded from the "
                "self-referential source projection; the final clean commit, tracked "
                "manifest, annotated tag, and detached release identity close those two identities."
            ),
        },
    }


def build_record(root: Path = ROOT) -> dict[str, Any]:
    assert_supported_runtime()
    return build_record_from_snapshot(repository_snapshot(root))


def validate_record(
    record: Mapping[str, Any],
    schema_path: Path = SCHEMA_PATH,
    *,
    schema_bytes: bytes | None = None,
) -> None:
    if schema_bytes is None:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    else:
        schema = load_json_bytes(schema_bytes, source=SCHEMA_RELATIVE_PATH)
    Draft7Validator(schema, format_checker=FormatChecker()).validate(record)


def verify_committed_revision(
    revision: str, *, root: Path = ROOT
) -> tuple[str, str, dict[str, Any]]:
    """Reconstruct and byte-verify the final S2 record from committed blobs."""

    assert_supported_runtime()
    commit, tree, snapshot = committed_revision_snapshot(revision, root=root)
    assert_base_is_ancestor(BASE_COMMIT, commit, root=root)
    assert_exact_committed_change_roster(root, commit=commit)
    assert_committed_snapshot_membership(snapshot)
    try:
        committed_record_bytes = snapshot[OUTPUT_RELATIVE_PATH].data
        schema_bytes = snapshot[SCHEMA_RELATIVE_PATH].data
    except KeyError as error:
        raise RuntimeError(f"Committed S2 tree lacks required identity input: {error.args[0]}") from error
    committed_record = load_json_bytes(
        committed_record_bytes, source=OUTPUT_RELATIVE_PATH
    )
    validate_record(committed_record, schema_bytes=schema_bytes)
    reconstructed = build_record_from_snapshot(snapshot)
    validate_record(reconstructed, schema_bytes=schema_bytes)
    expected_bytes = canonical_json_bytes(reconstructed)
    if committed_record_bytes != expected_bytes:
        raise RuntimeError(
            "Committed S2 JSON bytes do not exactly match the deterministic "
            "reconstruction from the committed tree"
        )
    return commit, tree, reconstructed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument(
        "--verify-commit",
        metavar="REVISION",
        help="reconstruct and byte-verify the final S2 record from a commit or annotated tag",
    )
    args = parser.parse_args()
    if args.verify_commit is not None:
        if args.validate_only:
            parser.error("--validate-only cannot be combined with --verify-commit")
        if args.output != DEFAULT_OUTPUT:
            parser.error("--output cannot be combined with --verify-commit")
        commit, tree, _record = verify_committed_revision(args.verify_commit)
        print(f"Verified committed S2 overlay at {commit} ({tree}).")
        return
    output = args.output if args.output.is_absolute() else ROOT / args.output
    if output.resolve() != DEFAULT_OUTPUT.resolve():
        parser.error(f"output must be {OUTPUT_RELATIVE_PATH}")
    record = build_record()
    validate_record(record)
    if args.validate_only:
        print("Dark-Medium Response Atlas S2 publication overlay is structurally valid.")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(record))
    print(f"Wrote {OUTPUT_RELATIVE_PATH}.")


if __name__ == "__main__":
    main()
