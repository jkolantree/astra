"""Build the deterministic Dark-Medium Response Atlas successor overlay S1."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import struct
import subprocess
from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_URL = (
    "https://jkolantree.github.io/astra/schemas/"
    "dark-medium-response-atlas-successor-overlay-s1.schema.json"
)
SCHEMA_RELATIVE_PATH = (
    "schemas/dark-medium-response-atlas-successor-overlay-s1.schema.json"
)
SCHEMA_PATH = ROOT / SCHEMA_RELATIVE_PATH
OUTPUT_RELATIVE_PATH = "evidence/dark_medium_response_atlas_successor_overlay_s1.json"
DEFAULT_OUTPUT = ROOT / OUTPUT_RELATIVE_PATH
GENERATOR_RELATIVE_PATH = "tools/build_dark_medium_response_atlas_successor_overlay.py"
GENERATOR_VERSION = "1.0.0"

BASE_COMMIT = "f8b32ef0af9cb6804f256490b4daafbdba43740e"
BASE_TREE = "251895700cdfc80addf180d46178b5aa8c43528c"
PREDECESSOR_RELATIVE_PATH = (
    "evidence/claim_source_coverage_v1.0.7_maintenance_overlay_m1.json"
)
PREDECESSOR_SHA256 = (
    "a655277bb9f241d8aa28a3ab11eacd03ae097befa5650c02dc50a66385555fd9"
)
PREDECESSOR_AUTHORITATIVE_SOURCE_PATH = "manuscript/manuscript.md"
PREDECESSOR_AUTHORITATIVE_SOURCE_SHA256 = (
    "ce55ea375ae5fbc28d06a52e3a2ea6e118294fc2b5925aef99365c39a637c292"
)

PACKAGE_ROOT = "resources/dark-medium-response-atlas/draft-v0.1.0"
PACKAGE_PATHS = (
    f"{PACKAGE_ROOT}/CHANGE_LOG.md",
    f"{PACKAGE_ROOT}/DARK_MEDIUM_RESPONSE_ATLAS.md",
    f"{PACKAGE_ROOT}/LICENSE_MAP.md",
    f"{PACKAGE_ROOT}/README.md",
    f"{PACKAGE_ROOT}/claim_ledger.csv",
    f"{PACKAGE_ROOT}/draft_metadata.json",
    f"{PACKAGE_ROOT}/novelty_ledger.csv",
    f"{PACKAGE_ROOT}/source_ledger.csv",
)

IDENTITY_CLOSURE_PATHS = frozenset({"MANIFEST.sha256", OUTPUT_RELATIVE_PATH})
SOURCE_CHANGE_ROSTER = frozenset(
    {
        "LICENSE_MAP.md",
        "README.md",
        "evidence/README.md",
        "resources/README.md",
        *PACKAGE_PATHS,
        "schemas/README.md",
        SCHEMA_RELATIVE_PATH,
        "tests/test_claim_source_coverage.py",
        "tests/test_dark_medium_response_atlas_successor_overlay.py",
        GENERATOR_RELATIVE_PATH,
        "tools/check_repository.py",
        "tools/verify.py",
    }
)
FULL_CHANGE_ROSTER = SOURCE_CHANGE_ROSTER | IDENTITY_CLOSURE_PATHS

AUTHORITATIVE_RUNTIME_IDENTITY = "python==3.12.10"
PERMITTED_ENVIRONMENT_LIMITED_RUNTIME_IDENTITY = "python==3.12.13"
RUNTIME_IDENTITY = f"python=={platform.python_version()}"
RUNTIME_IMPLEMENTATION = platform.python_implementation()
RUNTIME_CLASSIFICATION = (
    "release_authoritative"
    if (
        RUNTIME_IMPLEMENTATION == "CPython"
        and RUNTIME_IDENTITY == AUTHORITATIVE_RUNTIME_IDENTITY
    )
    else "environment_limited"
)
RUNTIME_PATH = "RUNTIME.json"
LOCK_PATH = "requirements-lock.txt"

SOURCE_PROJECTION_SCHEME = "astra-source-projection-v1"
SOURCE_PROJECTION_SCOPE = (
    "astra-dark-medium-response-atlas-successor-s1-repository-source-v1"
)
PACKAGE_ROSTER_SCHEME = "astra-package-roster-v1"
PACKAGE_ROSTER_SCOPE = "astra-dark-medium-response-atlas-draft-v0.1.0-package-v1"
CANONICAL_SERIALIZATION = "astra-binary-length-prefixed-v1"
SAFE_PATH_PATTERN = re.compile(
    r"(?!/)(?!.*//)(?!.*(?:^|/)\.{1,2}(?:/|$))"
    r"[A-Za-z0-9._/-]*[A-Za-z0-9._-]"
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
        return sha256_bytes(self.data)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json_bytes(value: bytes, *, source: str) -> dict[str, Any]:
    document = json.loads(value.decode("utf-8"))
    if not isinstance(document, dict):
        raise ValueError(f"Expected a JSON object at {source}")
    return document


def load_json(path: Path) -> dict[str, Any]:
    return load_json_bytes(path.read_bytes(), source=str(path))


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
    result = git_command(arguments, root=root, binary=True)
    if not isinstance(result, bytes):
        raise TypeError("Expected binary Git output")
    try:
        return {
            item.replace("\\", "/")
            for item in result.decode("ascii").split("\0")
            if item
        }
    except UnicodeDecodeError as error:
        raise RuntimeError("Candidate paths must be ASCII") from error


def commit_tree(commit: str, *, root: Path = ROOT) -> str:
    return str(git_command(["rev-parse", f"{commit}^{{tree}}"], root=root)).strip()


def assert_supported_runtime() -> None:
    permitted = {
        AUTHORITATIVE_RUNTIME_IDENTITY,
        PERMITTED_ENVIRONMENT_LIMITED_RUNTIME_IDENTITY,
    }
    if RUNTIME_IMPLEMENTATION != "CPython" or RUNTIME_IDENTITY not in permitted:
        raise RuntimeError(
            "S1 generation requires CPython 3.12.10 or the explicitly "
            "ENVIRONMENT_LIMITED CPython 3.12.13 lane; observed "
            f"{RUNTIME_IMPLEMENTATION} {platform.python_version()}"
        )


def assert_no_hidden_index_flags(root: Path = ROOT) -> None:
    result = git_command(["ls-files", "-v", "-z"], root=root, binary=True)
    if not isinstance(result, bytes):
        raise TypeError("Expected binary Git output")
    hidden = [
        record[2:].decode("utf-8", errors="replace")
        for record in result.split(b"\0")
        if record and (record[:1] == b"S" or record[:1].islower())
    ]
    if hidden:
        raise RuntimeError("Index flags hide candidate changes: " + ", ".join(hidden))
    if git_path_set(["ls-files", "--unmerged", "-z"], root=root):
        raise RuntimeError("Unmerged index entries block candidate identity")


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
        raise TypeError("Expected binary Git index output")
    entries: dict[str, tuple[str, str]] = {}
    casefolded: dict[str, str] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        header, separator, encoded_path = record.partition(b"\t")
        if not separator:
            raise RuntimeError("Malformed Git index record")
        fields = header.split()
        if len(fields) != 3:
            raise RuntimeError("Malformed Git index metadata")
        mode, object_id, stage = (field.decode("ascii") for field in fields)
        if stage != "0":
            raise RuntimeError("Unmerged Git index stage blocks source projection")
        if mode not in {"100644", "100755"}:
            raise RuntimeError(f"Unsupported projection Git mode: {mode}")
        if (
            re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", object_id) is None
            or set(object_id) == {"0"}
        ):
            raise RuntimeError("Invalid or intent-to-add Git index object")
        try:
            path = encoded_path.decode("ascii")
        except UnicodeDecodeError as error:
            raise RuntimeError("Candidate paths must be ASCII") from error
        _validate_path(path)
        if path in entries:
            raise RuntimeError(f"Duplicate Git index path: {path}")
        folded = path.casefold()
        if folded in casefolded:
            raise RuntimeError(
                f"Case-fold-colliding Git index paths: {casefolded[folded]} and {path}"
            )
        casefolded[folded] = path
        entries[path] = (mode, object_id)
    return raw, entries


def assert_exact_change_roster(
    root: Path = ROOT,
    *,
    base_commit: str = BASE_COMMIT,
    source_change_roster: Collection[str] = SOURCE_CHANGE_ROSTER,
    full_change_roster: Collection[str] = FULL_CHANGE_ROSTER,
    identity_closure_paths: Collection[str] = IDENTITY_CLOSURE_PATHS,
) -> set[str]:
    changed = git_path_set(
        ["diff", "--cached", "--no-renames", "--name-only", "-z", base_commit, "--"],
        root=root,
    )
    expected_source = set(source_change_roster)
    expected_full = set(full_change_roster)
    closure = set(identity_closure_paths)
    if changed - expected_full:
        raise RuntimeError(
            "Unexpected candidate change paths: " + ", ".join(sorted(changed - expected_full))
        )
    observed_source = changed - closure
    if observed_source != expected_source:
        missing = sorted(expected_source - observed_source)
        unexpected = sorted(observed_source - expected_source)
        details = []
        if missing:
            details.append("missing=" + ",".join(missing))
        if unexpected:
            details.append("unexpected=" + ",".join(unexpected))
        raise RuntimeError("Staged source change roster mismatch: " + "; ".join(details))
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
    if deleted:
        raise RuntimeError("Candidate roster may not delete paths: " + ", ".join(sorted(deleted)))
    return changed


def repository_snapshot(
    root: Path = ROOT,
    *,
    base_commit: str = BASE_COMMIT,
    base_tree: str = BASE_TREE,
    source_change_roster: Collection[str] = SOURCE_CHANGE_ROSTER,
    full_change_roster: Collection[str] = FULL_CHANGE_ROSTER,
    identity_closure_paths: Collection[str] = IDENTITY_CLOSURE_PATHS,
) -> dict[str, SnapshotEntry]:
    assert_no_hidden_index_flags(root)
    if commit_tree(base_commit, root=root) != base_tree:
        raise RuntimeError("Audited S1 base tree identity drift")
    closure = set(identity_closure_paths)
    untracked = git_path_set(
        ["ls-files", "--others", "--exclude-standard", "-z"], root=root
    )
    unexpected_untracked = untracked - closure
    if unexpected_untracked:
        raise RuntimeError(
            "Untracked source paths block S1 projection: "
            + ", ".join(sorted(unexpected_untracked))
        )
    unstaged = git_path_set(
        ["diff", "--no-renames", "--name-only", "-z", "--"], root=root
    )
    unexpected_unstaged = unstaged - closure
    if unexpected_unstaged:
        raise RuntimeError(
            "Source files must be staged before S1 projection: "
            + ", ".join(sorted(unexpected_unstaged))
        )
    assert_exact_change_roster(
        root,
        base_commit=base_commit,
        source_change_roster=source_change_roster,
        full_change_roster=full_change_roster,
        identity_closure_paths=closure,
    )

    index_before, metadata = _index_metadata(root)
    snapshot: dict[str, SnapshotEntry] = {}
    for path, (mode, object_id) in metadata.items():
        data = git_command(["cat-file", "blob", object_id], root=root, binary=True)
        if not isinstance(data, bytes):
            raise TypeError("Expected binary Git blob output")
        if path not in closure:
            worktree_path = root / path
            if worktree_path.is_symlink() or not worktree_path.is_file():
                raise RuntimeError(f"Projected source path is not a regular file: {path}")
            if worktree_path.read_bytes() != data:
                raise RuntimeError(f"Working-tree bytes differ from staged source blob: {path}")
        snapshot[path] = SnapshotEntry(path, mode, object_id, data)
    index_after, _ = _index_metadata(root)
    if index_after != index_before:
        raise RuntimeError("Git index changed while S1 projection was being read")
    missing_source = set(source_change_roster) - set(snapshot)
    if missing_source:
        raise RuntimeError(
            "Declared S1 source paths are absent from the index: "
            + ", ".join(sorted(missing_source))
        )
    return snapshot


def _length_prefixed(value: bytes) -> bytes:
    if len(value) > 0xFFFFFFFF:
        raise RuntimeError("Canonical field exceeds the uint32 framing limit")
    return struct.pack(">I", len(value)) + value


def serialize_file_entries(
    *,
    domain: bytes,
    scope: str,
    entries: list[dict[str, Any]],
    excluded_paths: Collection[str] = (),
) -> bytes:
    try:
        encoded_scope = scope.encode("ascii")
    except UnicodeEncodeError as error:
        raise RuntimeError("Canonical scope must be ASCII") from error
    normalized_exclusions = sorted(excluded_paths)
    if len(set(normalized_exclusions)) != len(normalized_exclusions):
        raise RuntimeError("Duplicate canonical exclusion")
    payload = bytearray(b"ASTRA\0" + domain + b"\0V1\0")
    payload.extend(_length_prefixed(encoded_scope))
    payload.extend(struct.pack(">I", len(normalized_exclusions)))
    for path in normalized_exclusions:
        _validate_path(path)
        payload.extend(_length_prefixed(path.encode("ascii")))
    normalized_entries = sorted(entries, key=lambda entry: str(entry["path"]))
    paths = [str(entry["path"]) for entry in normalized_entries]
    if len(set(paths)) != len(paths):
        raise RuntimeError("Duplicate canonical entry")
    if len({path.casefold() for path in paths}) != len(paths):
        raise RuntimeError("Case-fold-colliding canonical entries")
    payload.extend(struct.pack(">I", len(normalized_entries)))
    for entry in normalized_entries:
        if set(entry) != {"path", "mode", "bytes", "sha256"}:
            raise RuntimeError("Malformed canonical entry")
        path = str(entry["path"])
        mode = str(entry["mode"])
        byte_count = entry["bytes"]
        digest = str(entry["sha256"])
        _validate_path(path)
        if mode not in {"100644", "100755"}:
            raise RuntimeError(f"Unsupported canonical mode: {mode}")
        if not isinstance(byte_count, int) or isinstance(byte_count, bool) or byte_count < 0:
            raise RuntimeError("Invalid canonical byte count")
        if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise RuntimeError("Invalid canonical SHA-256")
        payload.extend(_length_prefixed(path.encode("ascii")))
        payload.extend(_length_prefixed(mode.encode("ascii")))
        payload.extend(struct.pack(">Q", byte_count))
        payload.extend(bytes.fromhex(digest))
    return bytes(payload)


def projection_entries(
    snapshot: dict[str, SnapshotEntry], *, exclusions: Collection[str]
) -> list[dict[str, Any]]:
    excluded = set(exclusions)
    return [
        {
            "path": path,
            "mode": entry.mode,
            "bytes": len(entry.data),
            "sha256": entry.sha256,
        }
        for path, entry in sorted(snapshot.items())
        if path not in excluded
    ]


def build_source_projection(snapshot: dict[str, SnapshotEntry]) -> dict[str, Any]:
    exclusions = sorted(IDENTITY_CLOSURE_PATHS)
    entries = projection_entries(snapshot, exclusions=exclusions)
    payload = serialize_file_entries(
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
        "canonical_bytes": len(payload),
        "excluded_paths": exclusions,
        "entries": entries,
        "sha256": sha256_bytes(payload),
    }


def build_package_identity(snapshot: dict[str, SnapshotEntry]) -> dict[str, Any]:
    observed_package_paths = {
        path for path in snapshot if path.startswith(f"{PACKAGE_ROOT}/")
    }
    if observed_package_paths != set(PACKAGE_PATHS):
        missing = sorted(set(PACKAGE_PATHS) - observed_package_paths)
        unexpected = sorted(observed_package_paths - set(PACKAGE_PATHS))
        details = []
        if missing:
            details.append("missing=" + ",".join(missing))
        if unexpected:
            details.append("unexpected=" + ",".join(unexpected))
        raise RuntimeError("Package roster mismatch: " + "; ".join(details))
    entries = [
        {
            "path": path,
            "mode": snapshot[path].mode,
            "bytes": len(snapshot[path].data),
            "sha256": snapshot[path].sha256,
        }
        for path in PACKAGE_PATHS
    ]
    payload = serialize_file_entries(
        domain=b"PACKAGE-ROSTER",
        scope=PACKAGE_ROSTER_SCOPE,
        entries=entries,
    )
    metadata = load_json_bytes(
        snapshot[f"{PACKAGE_ROOT}/draft_metadata.json"].data,
        source=f"{PACKAGE_ROOT}/draft_metadata.json",
    )
    expected_metadata = {
        "status": "unpromoted_supplemental_research_draft",
        "audited_base_commit": BASE_COMMIT,
        "audited_base_tree": BASE_TREE,
        "successor_overlay_id": "dark-medium-response-atlas-successor-s1",
        "predecessor_overlay": PREDECESSOR_RELATIVE_PATH,
        "release_identity": None,
    }
    observed_metadata = {key: metadata.get(key) for key in expected_metadata}
    if observed_metadata != expected_metadata:
        raise RuntimeError(
            "Package metadata identity mismatch: "
            + json.dumps(observed_metadata, sort_keys=True)
        )
    expected_publication = {
        "github_release": False,
        "pages": False,
        "zenodo": False,
        "doi": False,
    }
    if metadata.get("publication") != expected_publication:
        raise RuntimeError("Package metadata must preserve the no-publication boundary")
    return {
        "root": PACKAGE_ROOT,
        "status": "unpromoted_supplemental_research_draft",
        "roster": list(PACKAGE_PATHS),
        "file_count": len(entries),
        "files": entries,
        "aggregate": {
            "scheme": PACKAGE_ROSTER_SCHEME,
            "scope": PACKAGE_ROSTER_SCOPE,
            "digest_algorithm": "sha256",
            "canonical_byte_domain": "git-index-blob",
            "serialization": CANONICAL_SERIALIZATION,
            "canonical_bytes": len(payload),
            "sha256": sha256_bytes(payload),
        },
    }


def verify_predecessor(
    root: Path, snapshot: dict[str, SnapshotEntry]
) -> dict[str, Any]:
    try:
        predecessor = snapshot[PREDECESSOR_RELATIVE_PATH]
    except KeyError as error:
        raise RuntimeError("Immutable M1 predecessor is absent from the S1 projection") from error
    if predecessor.sha256 != PREDECESSOR_SHA256:
        raise RuntimeError("Immutable M1 predecessor bytes drifted")
    base_bytes = git_command(
        ["show", f"{BASE_COMMIT}:{PREDECESSOR_RELATIVE_PATH}"],
        root=root,
        binary=True,
    )
    if not isinstance(base_bytes, bytes):
        raise TypeError("Expected binary Git output")
    if base_bytes != predecessor.data:
        raise RuntimeError("M1 predecessor differs from the audited S1 base")
    record = load_json_bytes(predecessor.data, source=PREDECESSOR_RELATIVE_PATH)
    maintenance = record.get("maintenance_overlay")
    if not isinstance(maintenance, dict):
        raise RuntimeError("M1 predecessor lacks its maintenance-overlay identity")
    if (
        maintenance.get("authoritative_source_path")
        != PREDECESSOR_AUTHORITATIVE_SOURCE_PATH
        or maintenance.get("authoritative_source_sha256")
        != PREDECESSOR_AUTHORITATIVE_SOURCE_SHA256
    ):
        raise RuntimeError("M1 authoritative-source boundary drifted")
    return {
        "path": PREDECESSOR_RELATIVE_PATH,
        "sha256": PREDECESSOR_SHA256,
        "relationship": "immutable_predecessor_not_regenerated_or_superseded",
        "authoritative_source_path": PREDECESSOR_AUTHORITATIVE_SOURCE_PATH,
        "authoritative_source_sha256": PREDECESSOR_AUTHORITATIVE_SOURCE_SHA256,
        "inherited_authority": False,
    }


def build_record(root: Path = ROOT) -> dict[str, Any]:
    assert_supported_runtime()
    snapshot = repository_snapshot(root)
    package = build_package_identity(snapshot)
    predecessor = verify_predecessor(root, snapshot)
    return {
        "schema": SCHEMA_URL,
        "schema_version": "1.0.0",
        "overlay_id": "dark-medium-response-atlas-successor-s1",
        "overlay_kind": "supplemental_resource_admission",
        "status": "unpromoted_supplemental_resource_admission",
        "prepared_date": "2026-09-01",
        "base_identity": {
            "commit": BASE_COMMIT,
            "tree": BASE_TREE,
            "relationship": "audited_repository_base",
        },
        "predecessor_overlay": predecessor,
        "change_roster": {
            "expected_paths": sorted(FULL_CHANGE_ROSTER),
            "source_paths": sorted(SOURCE_CHANGE_ROSTER),
            "identity_closure_paths": sorted(IDENTITY_CLOSURE_PATHS),
        },
        "package": package,
        "source_projection": build_source_projection(snapshot),
        "authority": {
            "scope": "repository_admission_and_byte_identity_only",
            "core_claim_authority": "none",
            "scientific_validation_authority": "none",
            "release_authority": "none",
            "publication_authority": "none",
            "supersedes_predecessor": False,
        },
        "generator": {
            "path": GENERATOR_RELATIVE_PATH,
            "version": GENERATOR_VERSION,
            "runtime": RUNTIME_IDENTITY,
            "runtime_implementation": RUNTIME_IMPLEMENTATION,
            "required_runtime": AUTHORITATIVE_RUNTIME_IDENTITY,
            "permitted_environment_limited_runtime": (
                PERMITTED_ENVIRONMENT_LIMITED_RUNTIME_IDENTITY
            ),
            "runtime_classification": RUNTIME_CLASSIFICATION,
            "runtime_classification_scope": (
                "cpython-version-and-repository-runtime-contract-bytes"
            ),
            "runtime_contract_path": RUNTIME_PATH,
            "runtime_contract_sha256": snapshot[RUNTIME_PATH].sha256,
            "dependency_lock_path": LOCK_PATH,
            "dependency_lock_sha256": snapshot[LOCK_PATH].sha256,
            "schema_path": SCHEMA_RELATIVE_PATH,
            "schema_sha256": snapshot[SCHEMA_RELATIVE_PATH].sha256,
            "output_path": OUTPUT_RELATIVE_PATH,
            "environment_note": (
                None
                if RUNTIME_CLASSIFICATION == "release_authoritative"
                else (
                    "ENVIRONMENT_LIMITED: generated with python==3.12.13; "
                    "release-authoritative regeneration requires python==3.12.10."
                )
            ),
        },
        "verification_scope": {
            "binds": [
                "immutable_m1_predecessor_bytes",
                "exact_declared_base_delta",
                "full_staged_git_index_except_identity_closure",
                "exact_eight_file_package_roster_and_bytes",
            ],
            "does_not_establish": [
                "core_claim_authority",
                "scientific_validation",
                "peer_review",
                "release_authority",
                "publication_authority",
            ],
            "closure_note": (
                "MANIFEST.sha256 and this S1 JSON are intentionally excluded from the "
                "self-referential source projection; tracked-manifest and archive checks "
                "must bind them after candidate serialization."
            ),
        },
    }


def validate_record(record: dict[str, Any], schema_path: Path = SCHEMA_PATH) -> None:
    schema = load_json(schema_path)
    Draft7Validator(schema, format_checker=FormatChecker()).validate(record)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    if output.resolve() != DEFAULT_OUTPUT.resolve():
        parser.error(f"output must be {OUTPUT_RELATIVE_PATH}")
    record = build_record()
    validate_record(record)
    if args.validate_only:
        print("Dark-Medium Response Atlas successor overlay S1 is structurally valid.")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Wrote {OUTPUT_RELATIVE_PATH}.")


if __name__ == "__main__":
    main()
