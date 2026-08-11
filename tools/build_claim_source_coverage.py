"""Build the deterministic core-integrity-m1 claim-to-source coverage overlay."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_URL = "https://jkolantree.github.io/astra/schemas/claim-source-coverage-v1.schema.json"
SCHEMA_PATH = ROOT / "schemas" / "claim-source-coverage-v1.schema.json"
FROZEN_OUTPUT = ROOT / "evidence" / "claim_source_coverage_v1.0.7.json"
OVERLAY_RELATIVE_PATH = "evidence/claim_source_coverage_v1.0.7_maintenance_overlay_m1.json"
DEFAULT_OUTPUT = ROOT / OVERLAY_RELATIVE_PATH
GENERATOR_VERSION = "0.3.0"
AUTHORITATIVE_RUNTIME_IDENTITY = "python==3.12.10"
RUNTIME_IDENTITY = f"python=={platform.python_version()}"
RUNTIME_CLASSIFICATION = (
    "release_authoritative"
    if RUNTIME_IDENTITY == AUTHORITATIVE_RUNTIME_IDENTITY
    else "environment_limited"
)
SOURCE_CANDIDATE_PATHS = frozenset(
    {
        "AGENTS.md",
        "LICENSE_MAP.md",
        "manuscript/manuscript.md",
        "schemas/claim-source-coverage-v1.schema.json",
        "tests/test_claim_source_coverage.py",
        "tests/test_document_contract.py",
        "tools/build_claim_source_coverage.py",
        "tools/check_repository.py",
    }
)
IDENTITY_CLOSURE_PATHS = frozenset({"MANIFEST.sha256", OVERLAY_RELATIVE_PATH})
BASE_COMMIT = "f66027da807a35a1682033ba41348e81f9ceb7e7"
BASE_TREE = "2854b9c0ea13cf08d1f6c559cb471acee7e2b74e"
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def tracked_paths(root: Path = ROOT, *, revision: str | None = None) -> set[str]:
    arguments = (
        ["ls-files", "-z"]
        if revision is None
        else ["ls-tree", "-r", "--name-only", "-z", revision]
    )
    return git_path_set(arguments, root=root)


def worktree_changed_paths(root: Path = ROOT) -> set[str]:
    return (
        git_path_set(["diff", "--no-renames", "--name-only", "-z"], root=root)
        | git_path_set(
            ["diff", "--cached", "--no-renames", "--name-only", "-z"], root=root
        )
        | git_path_set(["ls-files", "--others", "--exclude-standard", "-z"], root=root)
    )


def commit_changed_paths(base: str, tip: str, *, root: Path = ROOT) -> set[str]:
    return git_path_set(
        ["diff", "--no-renames", "--name-only", "-z", base, tip, "--"], root=root
    )


def single_parent(commit: str, *, root: Path = ROOT) -> str:
    parts = str(git_command(["rev-list", "--parents", "-n", "1", commit], cwd=root)).split()
    if len(parts) != 2 or parts[0] != commit:
        raise RuntimeError(f"Candidate source commit must have exactly one parent: {commit}")
    return parts[1]


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


def source_candidate_identity(
    root: Path, *, candidate_source_commit: str | None
) -> dict[str, Any]:
    assert_no_hidden_index_flags(root)
    head = str(git_command(["rev-parse", "HEAD"], cwd=root)).strip()
    changed = worktree_changed_paths(root)
    if candidate_source_commit is None:
        expected = SOURCE_CANDIDATE_PATHS | IDENTITY_CLOSURE_PATHS
        head_tree = commit_tree(head, root=root)
        if head != BASE_COMMIT or head_tree != BASE_TREE:
            raise RuntimeError(
                "Uncommitted maintenance draft must remain on the frozen baseline: "
                f"expected={BASE_COMMIT}/{BASE_TREE}, observed={head}/{head_tree}"
            )
        if changed != expected:
            raise RuntimeError(
                "Uncommitted maintenance scope differs from the declared milestone: "
                f"expected={sorted(expected)}, observed={sorted(changed)}"
            )
        return {
            "source_state": "uncommitted_worktree",
            "base_commit": head,
            "base_tree": head_tree,
            "candidate_source_commit": None,
            "candidate_source_tree": None,
        }

    if not re.fullmatch(r"[0-9a-f]{40}", candidate_source_commit):
        raise RuntimeError("Candidate source commit must be a full lowercase 40-hex Git ID")
    resolved = str(
        git_command(["rev-parse", "--verify", f"{candidate_source_commit}^{{commit}}"], cwd=root)
    ).strip()
    if resolved != candidate_source_commit:
        raise RuntimeError("Candidate source commit did not resolve to itself")
    base_commit = single_parent(resolved, root=root)
    base_tree = commit_tree(base_commit, root=root)
    if base_commit != BASE_COMMIT or base_tree != BASE_TREE:
        raise RuntimeError(
            "Candidate source parent differs from the frozen baseline: "
            f"expected={BASE_COMMIT}/{BASE_TREE}, observed={base_commit}/{base_tree}"
        )
    source_paths = commit_changed_paths(base_commit, resolved, root=root)
    if source_paths != SOURCE_CANDIDATE_PATHS:
        raise RuntimeError(
            "Candidate source commit scope differs from the declared milestone: "
            f"expected={sorted(SOURCE_CANDIDATE_PATHS)}, observed={sorted(source_paths)}"
        )

    if head == resolved:
        if changed != IDENTITY_CLOSURE_PATHS:
            raise RuntimeError(
                "Before identity closure, only overlay and manifest may differ: "
                f"expected={sorted(IDENTITY_CLOSURE_PATHS)}, observed={sorted(changed)}"
            )
    else:
        if changed:
            raise RuntimeError(
                "Committed identity closure requires a clean worktree; "
                f"observed={sorted(changed)}"
            )
        closure_parent = single_parent(head, root=root)
        if closure_parent != resolved:
            raise RuntimeError(
                f"Identity-closure parent {closure_parent} differs from {resolved}"
            )
        closure_paths = commit_changed_paths(resolved, head, root=root)
        if closure_paths != IDENTITY_CLOSURE_PATHS:
            raise RuntimeError(
                "Identity-closure commit scope differs from overlay and manifest: "
                f"expected={sorted(IDENTITY_CLOSURE_PATHS)}, observed={sorted(closure_paths)}"
            )

    return {
        "source_state": "committed_source_candidate",
        "base_commit": base_commit,
        "base_tree": base_tree,
        "candidate_source_commit": resolved,
        "candidate_source_tree": commit_tree(resolved, root=root),
    }


def maintenance_overlay_identity(
    root: Path, *, candidate_source_commit: str | None = None
) -> dict[str, Any]:
    release_spec = load_json(root / "RELEASE_SPEC.json")
    release_tag = str(release_spec["tag"])
    release_identity = tag_identity(release_tag, root=root, require_head=False)
    source_identity = source_candidate_identity(
        root, candidate_source_commit=candidate_source_commit
    )
    frozen_relative = FROZEN_OUTPUT.relative_to(ROOT).as_posix()
    frozen_path = root / frozen_relative
    frozen_digest = sha256_file(frozen_path)
    tagged_frozen_bytes = git_command(
        ["show", f"{release_identity['commit']}:{frozen_relative}"],
        cwd=root,
        binary=True,
    )
    if not isinstance(tagged_frozen_bytes, bytes):
        raise TypeError("Expected binary Git output")
    if sha256_bytes(tagged_frozen_bytes) != frozen_digest:
        raise RuntimeError("Frozen v1.0.7 coverage bytes differ from the release tag")
    source_path = "manuscript/manuscript.md"
    return {
        "overlay_id": "astra-core-integrity-m1",
        "promotion_status": "unpromoted_source_repair",
        **source_identity,
        "identity_closure_paths": sorted(IDENTITY_CLOSURE_PATHS),
        "authoritative_source_path": source_path,
        "authoritative_source_sha256": sha256_file(root / source_path),
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


def build_record(
    root: Path = ROOT, *, candidate_source_commit: str | None = None
) -> dict[str, Any]:
    claim_matrix = load_json(root / "CLAIM_MATRIX.json")
    source_inventory = load_json(root / "SOURCE_INVENTORY.json")
    tracked = tracked_paths(root, revision=candidate_source_commit)
    tracked_hashes = {
        path: sha256_file(root / path)
        for path in tracked
        if (root / path).is_file()
    }
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
            "claim_matrix_sha256": sha256_file(root / "CLAIM_MATRIX.json"),
            "source_inventory_path": "SOURCE_INVENTORY.json",
            "source_inventory_sha256": sha256_file(root / "SOURCE_INVENTORY.json"),
            "bibliography_path": "manuscript/references.bib",
            "bibliography_sha256": sha256_file(root / "manuscript" / "references.bib"),
        },
        "generator": {
            "path": "tools/build_claim_source_coverage.py",
            "version": GENERATOR_VERSION,
            "runtime": RUNTIME_IDENTITY,
            "required_runtime": AUTHORITATIVE_RUNTIME_IDENTITY,
            "runtime_classification": RUNTIME_CLASSIFICATION,
            "output_path": OVERLAY_RELATIVE_PATH,
        },
        "input_files": [
            {
                "path": path,
                "sha256": sha256_file(root / path),
                "bytes": (root / path).stat().st_size,
            }
            for path in (
                "CLAIM_MATRIX.json",
                "SOURCE_INVENTORY.json",
                "manuscript/references.bib",
                "manuscript/manuscript.md",
                "tools/build_claim_source_coverage.py",
                "schemas/claim-source-coverage-v1.schema.json",
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
        "maintenance_overlay": maintenance_overlay_identity(
            root, candidate_source_commit=candidate_source_commit
        ),
        "known_gaps": [
            "Legacy CLAIM_MATRIX.json stores support as free text rather than source IDs and machine-addressable locators.",
            "Legacy claim records do not bind claims to admitted release-byte hashes.",
            "Legacy SOURCE_INVENTORY.json records supplied inputs but does not encode admitted replacement paths or hashes.",
            "External citation identity and claim-local entailment were not reverified by this structural generator.",
            "Exact execution commands, runtimes, and run identifiers are not present in the legacy claim records.",
            "This unpromoted core-integrity-m1 maintenance overlay does not alter or supersede the immutable v1.0.7 coverage record and is not a publication decision.",
            "The candidate_source_commit and candidate_source_tree identify the source-phase commit before the overlay and manifest identity-closure commit; the closure commit is bound externally by its Git tree, tracked manifest, and archive verification to avoid self-reference.",
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
    parser.add_argument(
        "--candidate-source-commit",
        help="full source-phase commit ID used by the two-commit identity closure",
    )
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    if output.resolve() != DEFAULT_OUTPUT.resolve():
        parser.error(
            f"output must be {OVERLAY_RELATIVE_PATH}; "
            f"the frozen {FROZEN_OUTPUT.relative_to(ROOT).as_posix()} record is immutable"
        )
    record = build_record(candidate_source_commit=args.candidate_source_commit)
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
