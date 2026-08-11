"""Build the deterministic core-integrity-m1 claim-to-source coverage overlay."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import struct
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_URL = (
    "https://jkolantree.github.io/astra/schemas/"
    "claim-source-coverage-overlay-m1.schema.json"
)
SCHEMA_PATH = ROOT / "schemas" / "claim-source-coverage-overlay-m1.schema.json"
FROZEN_OUTPUT = ROOT / "evidence" / "claim_source_coverage_v1.0.7.json"
OVERLAY_RELATIVE_PATH = "evidence/claim_source_coverage_v1.0.7_maintenance_overlay_m1.json"
DEFAULT_OUTPUT = ROOT / OVERLAY_RELATIVE_PATH
GENERATOR_VERSION = "0.4.0"
AUTHORITATIVE_RUNTIME_IDENTITY = "python==3.12.10"
RUNTIME_IDENTITY = f"python=={platform.python_version()}"
RUNTIME_CLASSIFICATION = (
    "release_authoritative"
    if (
        platform.python_implementation() == "CPython"
        and RUNTIME_IDENTITY == AUTHORITATIVE_RUNTIME_IDENTITY
    )
    else "environment_limited"
)
MILESTONE_SOURCE_PATHS = frozenset(
    {
        "AGENTS.md",
        "LICENSE_MAP.md",
        "README.md",
        "evidence/README.md",
        "manuscript/manuscript.md",
        "schemas/README.md",
        "schemas/claim-source-coverage-overlay-m1.schema.json",
        "tests/test_claim_source_coverage.py",
        "tests/test_document_contract.py",
        "tools/build_claim_source_coverage.py",
        "tools/check_repository.py",
    }
)
IDENTITY_CLOSURE_PATHS = frozenset({"MANIFEST.sha256", OVERLAY_RELATIVE_PATH})
BASE_COMMIT = "f66027da807a35a1682033ba41348e81f9ceb7e7"
BASE_TREE = "2854b9c0ea13cf08d1f6c559cb471acee7e2b74e"
RELEASE_TAG = "v1.0.7"
RELEASE_TAG_OBJECT = "b5dc469dc05e07d62d736a4c3ddc749a54e8ebbd"
RELEASE_COMMIT = "7454b8134cf28c233fe54a11ae4b65e256844821"
RELEASE_TREE = "3aaa2ec8c62d7c5c925e557cd79b3b43446aaf1d"
SOURCE_PROJECTION_SCHEME = "astra-source-projection-v1"
SOURCE_PROJECTION_SCOPE = "astra-core-integrity-m1-repository-source-v1"
SOURCE_PROJECTION_SERIALIZATION = "astra-binary-length-prefixed-v1"
RUNTIME_PATH = "RUNTIME.json"
LOCK_PATH = "requirements-lock.txt"
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
SHA256_RE = re.compile(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", re.IGNORECASE)
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")
ARXIV_RE = re.compile(r"arXiv:[ \t]*([0-9]{4}[.][0-9]{4,5}(?:v[0-9]+)?)", re.IGNORECASE)
LOCATOR_RE = re.compile(
    r"(?:equation|proposition|appendix|section\s+\d|function|figure|test|"
    r"inline proof|no-go|carbon phase relay|algebraic-statistical)",
    re.IGNORECASE,
)


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
    arguments: list[str], *, cwd: Path = ROOT, binary: bool = False
) -> str | bytes:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        env=git_environment(cwd),
        check=True,
        capture_output=True,
        text=not binary,
    )
    return completed.stdout


def tag_identity(tag: str, *, root: Path = ROOT, require_head: bool = True) -> dict[str, str]:
    object_type = str(git_command(["cat-file", "-t", f"refs/tags/{tag}"], cwd=root)).strip()
    if object_type != "tag":
        raise RuntimeError(f"Release tag must be annotated; observed {object_type!r}")
    tag_object = str(git_command(["rev-parse", f"refs/tags/{tag}"], cwd=root)).strip()
    commit = str(git_command(["rev-parse", f"refs/tags/{tag}^{{commit}}"], cwd=root)).strip()
    tree = str(git_command(["rev-parse", f"{commit}^{{tree}}"], cwd=root)).strip()
    payload = str(git_command(["cat-file", "-p", f"refs/tags/{tag}"], cwd=root))
    headers = dict(
        line.split(" ", 1) for line in payload.partition("\n\n")[0].splitlines()
    )
    if headers.get("object") != commit or headers.get("type") != "commit":
        raise RuntimeError(f"Release tag {tag} does not directly target its peeled commit")
    if headers.get("tag") != tag:
        raise RuntimeError(f"Annotated tag's internal name differs from {tag}")
    head = str(git_command(["rev-parse", "HEAD"], cwd=root)).strip()
    if require_head and commit != head:
        raise RuntimeError(f"Tag {tag} targets {commit}, not current HEAD {head}")
    return {"tag_object": tag_object, "commit": commit, "tree": tree}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected an object in {path}")
    return value


def git_path_set(arguments: list[str], *, root: Path = ROOT) -> set[str]:
    result = git_command(arguments, cwd=root, binary=True)
    if not isinstance(result, bytes):
        raise TypeError("Expected binary Git output")
    return {
        item.replace("\\", "/")
        for item in result.decode("utf-8", errors="surrogateescape").split("\0")
        if item
    }


def commit_tree(commit: str, *, root: Path = ROOT) -> str:
    return str(git_command(["rev-parse", f"{commit}^{{tree}}"], cwd=root)).strip()


def assert_no_hidden_index_flags(root: Path = ROOT) -> None:
    result = git_command(["ls-files", "-v", "-z"], cwd=root, binary=True)
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


def baseline_source_changes(root: Path = ROOT) -> set[str]:
    return git_path_set(
        ["diff", "--cached", "--no-renames", "--name-only", "-z", BASE_COMMIT, "--"],
        root=root,
    ) - IDENTITY_CLOSURE_PATHS


def _validate_snapshot_path(path: str) -> None:
    try:
        path.encode("ascii")
    except UnicodeEncodeError as error:
        raise RuntimeError(f"Source-projection path is not ASCII: {path!r}") from error
    parts = path.split("/")
    if (
        not path
        or "\\" in path
        or path.startswith("/")
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise RuntimeError(f"Unsafe source-projection path: {path!r}")


def _index_metadata(root: Path) -> tuple[bytes, dict[str, tuple[str, str]]]:
    raw = git_command(["ls-files", "--stage", "-z"], cwd=root, binary=True)
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
            raise RuntimeError(f"Unsupported source-projection Git mode: {mode}")
        if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", object_id) or set(object_id) == {"0"}:
            raise RuntimeError("Invalid or intent-to-add Git index object")
        path = encoded_path.decode("ascii")
        _validate_snapshot_path(path)
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


def repository_snapshot(root: Path = ROOT) -> dict[str, SnapshotEntry]:
    assert_no_hidden_index_flags(root)
    if commit_tree(BASE_COMMIT, root=root) != BASE_TREE:
        raise RuntimeError("Frozen maintenance baseline tree identity drift")
    untracked = git_path_set(["ls-files", "--others", "--exclude-standard", "-z"], root=root)
    if untracked:
        raise RuntimeError(
            "Untracked nonignored paths block source projection: " + ", ".join(sorted(untracked))
        )
    unstaged = git_path_set(["diff", "--no-renames", "--name-only", "-z"], root=root)
    unexpected_unstaged = unstaged - IDENTITY_CLOSURE_PATHS
    if unexpected_unstaged:
        raise RuntimeError(
            "Source files must be staged before projection: "
            + ", ".join(sorted(unexpected_unstaged))
        )
    index_before, metadata = _index_metadata(root)
    source_changes = baseline_source_changes(root)
    missing_milestone_paths = MILESTONE_SOURCE_PATHS - source_changes
    if missing_milestone_paths:
        raise RuntimeError(
            "Indexed source no longer contains every declared milestone change: "
            + ", ".join(sorted(missing_milestone_paths))
        )
    snapshot: dict[str, SnapshotEntry] = {}
    for path, (mode, object_id) in metadata.items():
        data = git_command(["cat-file", "blob", object_id], cwd=root, binary=True)
        if not isinstance(data, bytes):
            raise TypeError("Expected binary Git blob output")
        if path not in IDENTITY_CLOSURE_PATHS:
            worktree_path = root / path
            if worktree_path.is_symlink() or not worktree_path.is_file():
                raise RuntimeError(f"Projected source path is not a regular file: {path}")
            if worktree_path.read_bytes() != data:
                raise RuntimeError(f"Working-tree bytes differ from staged source blob: {path}")
        snapshot[path] = SnapshotEntry(path, mode, object_id, data)
    index_after, _ = _index_metadata(root)
    if index_after != index_before:
        raise RuntimeError("Git index changed while source projection was being read")
    missing_projected_paths = MILESTONE_SOURCE_PATHS - set(snapshot)
    if missing_projected_paths:
        raise RuntimeError(
            "Declared milestone paths are absent from the source projection: "
            + ", ".join(sorted(missing_projected_paths))
        )
    return snapshot


def snapshot_bytes(snapshot: dict[str, SnapshotEntry], path: str) -> bytes:
    try:
        return snapshot[path].data
    except KeyError as error:
        raise RuntimeError(f"Required source path is absent from the Git snapshot: {path}") from error


def snapshot_json(snapshot: dict[str, SnapshotEntry], path: str) -> dict[str, Any]:
    value = json.loads(snapshot_bytes(snapshot, path).decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object at {path}")
    return value


def _length_prefixed(value: bytes) -> bytes:
    if len(value) > 0xFFFFFFFF:
        raise RuntimeError("Source-projection field exceeds the uint32 framing limit")
    return struct.pack(">I", len(value)) + value


def serialize_source_projection(
    entries: list[dict[str, Any]], excluded_paths: list[str]
) -> bytes:
    normalized_exclusions = sorted(excluded_paths)
    if len(set(normalized_exclusions)) != len(normalized_exclusions):
        raise RuntimeError("Duplicate source-projection exclusion")
    payload = bytearray(b"ASTRA\0SOURCE-PROJECTION\0V1\0")
    payload.extend(_length_prefixed(SOURCE_PROJECTION_SCOPE.encode("ascii")))
    payload.extend(struct.pack(">I", len(normalized_exclusions)))
    for path in normalized_exclusions:
        _validate_snapshot_path(path)
        payload.extend(_length_prefixed(path.encode("ascii")))
    normalized_entries = sorted(entries, key=lambda entry: str(entry["path"]))
    paths = [str(entry["path"]) for entry in normalized_entries]
    if len(set(paths)) != len(paths):
        raise RuntimeError("Duplicate source-projection entry")
    if len({path.casefold() for path in paths}) != len(paths):
        raise RuntimeError("Case-fold-colliding source-projection entries")
    payload.extend(struct.pack(">I", len(normalized_entries)))
    for entry in normalized_entries:
        if set(entry) != {"path", "mode", "bytes", "sha256"}:
            raise RuntimeError("Malformed source-projection entry")
        path = str(entry["path"])
        mode = str(entry["mode"])
        byte_count = entry["bytes"]
        digest = str(entry["sha256"])
        _validate_snapshot_path(path)
        if mode not in {"100644", "100755"}:
            raise RuntimeError(f"Unsupported source-projection mode: {mode}")
        if not isinstance(byte_count, int) or isinstance(byte_count, bool) or byte_count < 0:
            raise RuntimeError("Invalid source-projection byte count")
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise RuntimeError("Invalid source-projection SHA-256")
        payload.extend(_length_prefixed(path.encode("ascii")))
        payload.extend(_length_prefixed(mode.encode("ascii")))
        payload.extend(struct.pack(">Q", byte_count))
        payload.extend(bytes.fromhex(digest))
    return bytes(payload)


def build_source_projection(snapshot: dict[str, SnapshotEntry]) -> dict[str, Any]:
    entries = [
        {
            "path": path,
            "mode": entry.mode,
            "bytes": len(entry.data),
            "sha256": entry.sha256,
        }
        for path, entry in sorted(snapshot.items())
        if path not in IDENTITY_CLOSURE_PATHS
    ]
    exclusions = sorted(IDENTITY_CLOSURE_PATHS)
    payload = serialize_source_projection(entries, exclusions)
    return {
        "scheme": SOURCE_PROJECTION_SCHEME,
        "scope": SOURCE_PROJECTION_SCOPE,
        "digest_algorithm": "sha256",
        "canonical_byte_domain": "git-index-blob",
        "serialization": SOURCE_PROJECTION_SERIALIZATION,
        "path_encoding": "ascii-posix",
        "entry_count": len(entries),
        "canonical_bytes": len(payload),
        "excluded_paths": exclusions,
        "entries": entries,
        "sha256": sha256_bytes(payload),
    }


def verify_release_identity(root: Path, release_tag: str) -> dict[str, str]:
    if release_tag != RELEASE_TAG:
        raise RuntimeError(f"Unexpected release tag in RELEASE_SPEC.json: {release_tag}")
    identity = tag_identity(release_tag, root=root, require_head=False)
    expected = {
        "tag_object": RELEASE_TAG_OBJECT,
        "commit": RELEASE_COMMIT,
        "tree": RELEASE_TREE,
    }
    if identity != expected:
        raise RuntimeError(f"Immutable v1.0.7 tag identity drift: {identity}")
    return identity


def maintenance_overlay_identity(
    root: Path, snapshot: dict[str, SnapshotEntry]
) -> dict[str, Any]:
    release_spec = snapshot_json(snapshot, "RELEASE_SPEC.json")
    release_tag = str(release_spec["tag"])
    release_identity = verify_release_identity(root, release_tag)
    frozen_relative = FROZEN_OUTPUT.relative_to(ROOT).as_posix()
    frozen_bytes = snapshot_bytes(snapshot, frozen_relative)
    frozen_digest = sha256_bytes(frozen_bytes)
    tagged_frozen_bytes = git_command(
        ["show", f"{release_identity['commit']}:{frozen_relative}"],
        cwd=root,
        binary=True,
    )
    if not isinstance(tagged_frozen_bytes, bytes):
        raise TypeError("Expected binary Git output")
    if tagged_frozen_bytes != frozen_bytes:
        raise RuntimeError("Frozen v1.0.7 coverage bytes differ from the release tag")
    for contract_path in (RUNTIME_PATH, LOCK_PATH):
        tagged_contract = git_command(
            ["show", f"{release_identity['commit']}:{contract_path}"],
            cwd=root,
            binary=True,
        )
        if not isinstance(tagged_contract, bytes):
            raise TypeError("Expected binary Git output")
        if tagged_contract != snapshot_bytes(snapshot, contract_path):
            raise RuntimeError(
                f"Runtime contract differs from immutable v1.0.7 bytes: {contract_path}"
            )
    source_path = "manuscript/manuscript.md"
    return {
        "overlay_id": "astra-core-integrity-m1",
        "promotion_status": "unpromoted_source_repair",
        "baseline_commit": BASE_COMMIT,
        "baseline_tree": BASE_TREE,
        "milestone_changed_paths": sorted(MILESTONE_SOURCE_PATHS),
        "additional_baseline_changed_paths": sorted(
            baseline_source_changes(root) - MILESTONE_SOURCE_PATHS
        ),
        "source_projection": build_source_projection(snapshot),
        "identity_closure_paths": sorted(IDENTITY_CLOSURE_PATHS),
        "authoritative_source_path": source_path,
        "authoritative_source_sha256": snapshot[source_path].sha256,
        "frozen_record_path": frozen_relative,
        "frozen_record_sha256": frozen_digest,
        "release_tag": release_tag,
        "release_tag_object": release_identity["tag_object"],
        "release_commit": release_identity["commit"],
        "release_tree": release_identity["tree"],
    }


def path_matches(raw_support: str, tracked: set[str]) -> list[str]:
    normalized = raw_support.replace("\\", "/")
    return sorted(
        (path for path in tracked if len(path) >= 5 and path in normalized),
        key=lambda path: (-len(path), path),
    )


def supplied_hash_matches(raw_support: str, artifact_hashes: set[str]) -> list[str]:
    return sorted(
        digest.lower()
        for digest in SHA256_RE.findall(raw_support)
        if digest.lower() in artifact_hashes
    )


def external_references(raw_support: str) -> list[str]:
    references = [f"doi:{value.rstrip('.,')}" for value in DOI_RE.findall(raw_support)]
    references.extend(f"arxiv:{value}" for value in ARXIV_RE.findall(raw_support))
    return sorted(set(references))


def locator_precision(text: str) -> str:
    return "named_locator" if LOCATOR_RE.search(text) else "file_level"


def locator_for(path: str, raw_support: str, digest: str) -> dict[str, Any]:
    normalized = raw_support.replace("\\", "/")
    tail = normalized.replace(path, "", 1).strip(" ,:;-\t") or None
    return {
        "path": path,
        "file_sha256": digest,
        "locator": tail,
        "precision": locator_precision(raw_support),
    }


def link(
    *,
    kind: str,
    reference: str,
    raw_support: str,
    admitted_path: str | None = None,
    admitted_sha256: str | None = None,
    supplied_input_sha256: str | None = None,
    entailment_status: str,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "reference": reference,
        "raw_support": raw_support,
        "admitted_path": admitted_path,
        "admitted_sha256": admitted_sha256,
        "supplied_input_sha256": supplied_input_sha256,
        "source_record_version": None,
        "retrieval_date": None,
        "entailment_status": entailment_status,
    }


def source_links(
    raw_support: str,
    *,
    tracked: set[str],
    tracked_hashes: dict[str, str],
    artifact_hashes: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    links: list[dict[str, Any]] = []
    locators: list[dict[str, Any]] = []
    paths = path_matches(raw_support, tracked)
    for path in paths:
        digest = tracked_hashes[path]
        locators.append(locator_for(path, raw_support, digest))
        links.append(
            link(
                kind="tracked_file",
                reference=path,
                raw_support=raw_support,
                admitted_path=path,
                admitted_sha256=digest,
                entailment_status="structural_link_only",
            )
        )

    for digest in supplied_hash_matches(raw_support, artifact_hashes):
        links.append(
            link(
                kind="supplied_input",
                reference=f"source-input-sha256:{digest}",
                raw_support=raw_support,
                supplied_input_sha256=digest,
                entailment_status="historical_provenance_only",
            )
        )

    for reference in external_references(raw_support):
        links.append(
            link(
                kind="external_record",
                reference=reference,
                raw_support=raw_support,
                entailment_status="not_reverified",
            )
        )

    if not links:
        lower = raw_support.lower()
        kind = "provenance_record" if any(
            marker in lower
            for marker in ("author", "publication instruction", "acknowledgment", "chatgpt")
        ) else "framework_statement"
        links.append(
            link(
                kind=kind,
                reference="legacy-support-text",
                raw_support=raw_support,
                entailment_status="structural_link_only",
            )
        )
    return links, locators


def claim_coverage(
    claim: dict[str, Any],
    *,
    tracked: set[str],
    tracked_hashes: dict[str, str],
    artifact_hashes: set[str],
) -> dict[str, Any]:
    links: list[dict[str, Any]] = []
    locators: list[dict[str, Any]] = []
    for raw_support in claim["support"]:
        support_links, support_locators = source_links(
            raw_support,
            tracked=tracked,
            tracked_hashes=tracked_hashes,
            artifact_hashes=artifact_hashes,
        )
        links.extend(support_links)
        locators.extend(support_locators)

    kinds = {item["kind"] for item in links}
    if claim["disposition"] in {"proposed_only", "deferred"}:
        coverage_status = "proposed_or_deferred"
    elif "tracked_file" in kinds and "external_record" in kinds:
        coverage_status = "mixed_tracked_external"
    elif "tracked_file" in kinds:
        coverage_status = "tracked_structural"
    elif "external_record" in kinds:
        coverage_status = "external_record_only"
    elif "supplied_input" in kinds:
        coverage_status = "historical_input_only"
    else:
        coverage_status = "framework_or_provenance"

    notes: list[str] = []
    if not locators:
        notes.append("No tracked-file locator is present in the legacy support strings.")
    if "external_record" in kinds:
        notes.append("External record identity and entailment were not reverified in this generation.")
    if claim["evidence_class"] in {"independently_reproduced", "mechanically_replayed"}:
        notes.append("The exact reproduction command, runtime, and run identifier are not encoded in the legacy claim matrix.")
    if not claim["limitations_or_counterexamples"]:
        notes.append("The legacy claim record has no limitations_or_counterexamples entry.")

    execution_status = (
        "not_recorded_in_claim_matrix"
        if claim["evidence_class"] in {"independently_reproduced", "mechanically_replayed"}
        else "not_applicable_to_legacy_record"
    )
    return {
        "id": claim["id"],
        "statement": claim["statement"],
        "claim_type": claim["claim_type"],
        "hypotheses": claim["hypotheses"],
        "domain_units_signs_boundary_quantifiers": claim[
            "domain_units_signs_boundary_quantifiers"
        ],
        "evidence_class": claim["evidence_class"],
        "disposition": claim["disposition"],
        "limitations_or_counterexamples": claim["limitations_or_counterexamples"],
        "coverage_status": coverage_status,
        "claim_locators": locators,
        "source_links": links,
        "execution": {
            "status": execution_status,
            "command": None,
            "runtime": None,
            "run_id": None,
        },
        "coverage_notes": notes,
    }


def build_record(root: Path = ROOT) -> dict[str, Any]:
    snapshot = repository_snapshot(root)
    claim_matrix = snapshot_json(snapshot, "CLAIM_MATRIX.json")
    source_inventory = snapshot_json(snapshot, "SOURCE_INVENTORY.json")
    runtime_contract = snapshot_json(snapshot, RUNTIME_PATH)
    required_runtime = f"python=={runtime_contract['python']}"
    if required_runtime != AUTHORITATIVE_RUNTIME_IDENTITY:
        raise RuntimeError(
            "RUNTIME.json Python identity differs from the generator's audited contract"
        )
    tracked = set(snapshot) - IDENTITY_CLOSURE_PATHS
    tracked_hashes = {path: snapshot[path].sha256 for path in tracked}
    artifact_hashes = {item["sha256"].lower() for item in source_inventory["artifacts"]}

    claims = [
        claim_coverage(
            claim,
            tracked=tracked,
            tracked_hashes=tracked_hashes,
            artifact_hashes=artifact_hashes,
        )
        for claim in claim_matrix["claims"]
    ]
    path_references = sum(len(claim["claim_locators"]) for claim in claims)
    unique_paths = {
        locator["path"] for claim in claims for locator in claim["claim_locators"]
    }
    claims_with_input_hash = sum(
        any(link_item["kind"] == "supplied_input" for link_item in claim["source_links"])
        for claim in claims
    )
    claims_with_external = sum(
        any(link_item["kind"] == "external_record" for link_item in claim["source_links"])
        for claim in claims
    )
    claims_with_exact_locators = sum(
        any(locator["precision"] == "named_locator" for locator in claim["claim_locators"])
        for claim in claims
    )

    source_records = [
        {
            "artifact_id": f"SUP-{index:03d}",
            "canonical_relative_path": item["canonical_relative_path"],
            "bytes": item["bytes"],
            "supplied_sha256": item["sha256"],
            "media_type": item["media_type"],
            "displayed_attribution": item["displayed_attribution"],
            "embedded_attribution": item["embedded_attribution"],
            "license": item["license"],
            "rights_status": item["rights_status"],
            "relationship": item["relationship"],
            "admitted_path": None,
            "admitted_sha256": None,
            "source_record_version": None,
            "retrieval_date": None,
            "status": "historical_supplied_input",
        }
        for index, item in enumerate(source_inventory["artifacts"], start=1)
    ]
    aliases = [
        {
            "alias_id": f"ALIAS-{index:03d}",
            "canonical_relative_path": item["canonical_relative_path"],
            "bytes": item["bytes"],
            "sha256": item["sha256"],
            "relationship": item["relationship"],
        }
        for index, item in enumerate(source_inventory["discovered_aliases"], start=1)
    ]

    return {
        "schema": SCHEMA_URL,
        "title": "SPPT/ASTRA v1.0.7 claim-source maintenance overlay M1 (unpromoted)",
        "status": "candidate_only",
        "reference_release": {
            "line": "core",
            "version": "1.0.7",
            "identity_status": "immutable_release_with_local_overlay",
            "claim_matrix_path": "CLAIM_MATRIX.json",
            "claim_matrix_sha256": snapshot["CLAIM_MATRIX.json"].sha256,
            "source_inventory_path": "SOURCE_INVENTORY.json",
            "source_inventory_sha256": snapshot["SOURCE_INVENTORY.json"].sha256,
            "bibliography_path": "manuscript/references.bib",
            "bibliography_sha256": snapshot["manuscript/references.bib"].sha256,
        },
        "generator": {
            "path": "tools/build_claim_source_coverage.py",
            "version": GENERATOR_VERSION,
            "runtime": RUNTIME_IDENTITY,
            "runtime_implementation": platform.python_implementation(),
            "required_runtime": AUTHORITATIVE_RUNTIME_IDENTITY,
            "runtime_classification": RUNTIME_CLASSIFICATION,
            "runtime_classification_scope": (
                "cpython-version-and-tagged-runtime-lock-contracts"
            ),
            "runtime_contract_path": RUNTIME_PATH,
            "runtime_contract_sha256": snapshot[RUNTIME_PATH].sha256,
            "dependency_lock_path": LOCK_PATH,
            "dependency_lock_sha256": snapshot[LOCK_PATH].sha256,
            "output_path": OVERLAY_RELATIVE_PATH,
        },
        "input_files": [
            {
                "path": path,
                "sha256": snapshot[path].sha256,
                "bytes": len(snapshot[path].data),
            }
            for path in (
                "CLAIM_MATRIX.json",
                "SOURCE_INVENTORY.json",
                "manuscript/references.bib",
                "manuscript/manuscript.md",
                "tools/build_claim_source_coverage.py",
                "schemas/claim-source-coverage-overlay-m1.schema.json",
            )
        ],
        "summary": {
            "claim_count": len(claims),
            "claims_with_support": sum(bool(claim["source_links"]) for claim in claims),
            "claims_with_current_path_support": sum(bool(claim["claim_locators"]) for claim in claims),
            "path_support_references": path_references,
            "unique_tracked_support_paths": len(unique_paths),
            "claims_with_supplied_input_hash_support": claims_with_input_hash,
            "claims_with_external_record_support": claims_with_external,
            "claims_with_exact_locators": claims_with_exact_locators,
            "claims_without_limitations": [
                claim["id"] for claim in claims if not claim["limitations_or_counterexamples"]
            ],
            "source_record_count": len(source_records),
            "source_records_with_admitted_hash": sum(
                record["admitted_sha256"] is not None for record in source_records
            ),
            "source_records_with_retrieval_date": sum(
                record["retrieval_date"] is not None for record in source_records
            ),
            "legacy_claim_fields_missing": [
                "claim_locator",
                "source_record_id",
                "admitted_hash",
                "input_hash",
                "source_record_version",
                "retrieval_date",
                "entailment_status",
                "independent_reproduction",
                "reproduction_command",
                "runtime",
            ],
        },
        "claims": claims,
        "source_records": source_records,
        "discovered_aliases": aliases,
        "duplicate_evidence_rules": source_inventory["duplicate_evidence_rules"],
        "maintenance_overlay": maintenance_overlay_identity(root, snapshot),
        "known_gaps": [
            "Legacy CLAIM_MATRIX.json stores support as free text rather than source IDs and machine-addressable locators.",
            "Legacy claim records do not bind claims to admitted release-byte hashes.",
            "Legacy SOURCE_INVENTORY.json records supplied inputs but does not encode admitted replacement paths or hashes.",
            "External citation identity and claim-local entailment were not reverified by this structural generator.",
            "Exact execution commands, runtimes, and run identifiers are not present in the legacy claim records.",
            "This unpromoted core-integrity-m1 maintenance overlay does not alter or supersede the immutable v1.0.7 coverage record and is not a publication decision.",
            "The source projection binds every staged repository source blob, path, mode, and byte length except the explicitly self-excluded overlay and manifest; tracked-manifest and archive verification bind those closure files after commit.",
            "Runtime classification here binds the CPython version plus the immutable tagged RUNTIME.json and dependency-lock contracts. Exact executable/distribution and installed-environment provenance require the separate runtime verifier and hash-locked replay.",
            *(
                [
                    f"ENVIRONMENT_LIMITED: generated with {RUNTIME_IDENTITY} rather than the release-authoritative {AUTHORITATIVE_RUNTIME_IDENTITY}."
                ]
                if RUNTIME_IDENTITY != AUTHORITATIVE_RUNTIME_IDENTITY
                else []
            ),
        ],
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
        parser.error(
            f"output must be {OVERLAY_RELATIVE_PATH}; "
            f"the frozen {FROZEN_OUTPUT.relative_to(ROOT).as_posix()} record is immutable"
        )
    record = build_record()
    validate_record(record)
    if not args.validate_only:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(f"Wrote {output.relative_to(ROOT).as_posix()}.")
    else:
        print("Structured claim-source coverage draft is valid.")


if __name__ == "__main__":
    main()
