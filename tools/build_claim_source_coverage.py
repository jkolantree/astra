"""Build the local structured claim-to-source coverage draft."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_URL = "https://jkolantree.github.io/astra/schemas/claim-source-coverage-v1.schema.json"
SCHEMA_PATH = ROOT / "schemas" / "claim-source-coverage-v1.schema.json"
DEFAULT_OUTPUT = ROOT / "evidence" / "claim_source_coverage_v1.0.6_draft.json"
GENERATOR_VERSION = "0.1.0"
RUNTIME_IDENTITY = "python==3.12.10"
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


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected an object in {path}")
    return value


def tracked_paths() -> set[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return {
        item.replace("\\", "/")
        for item in result.stdout.decode("utf-8", errors="surrogateescape").split("\0")
        if item
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
    claim_matrix = load_json(root / "CLAIM_MATRIX.json")
    source_inventory = load_json(root / "SOURCE_INVENTORY.json")
    tracked = tracked_paths()
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
        "title": "SPPT/ASTRA structured claim-to-source coverage audit (maintenance draft)",
        "status": "maintenance_draft",
        "reference_release": {
            "line": "core",
            "version": "1.0.6",
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
            "output_path": "evidence/claim_source_coverage_v1.0.6_draft.json",
        },
        "input_files": [
            {
                "path": path,
                "sha256": sha256_file(root / path),
                "bytes": (root / path).stat().st_size,
            }
            for path in ("CLAIM_MATRIX.json", "SOURCE_INVENTORY.json", "manuscript/references.bib")
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
        "known_gaps": [
            "Legacy CLAIM_MATRIX.json stores support as free text rather than source IDs and machine-addressable locators.",
            "Legacy claim records do not bind claims to admitted release-byte hashes.",
            "Legacy SOURCE_INVENTORY.json records supplied inputs but does not encode admitted replacement paths or hashes.",
            "External citation identity and claim-local entailment were not reverified by this structural generator.",
            "Exact execution commands, runtimes, and run identifiers are not present in the legacy claim records.",
            "This is a maintenance draft tied to the v1.0.6 core line; it is not a new release identity or publication decision.",
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
