"""Fail-closed structural checks for the unpromoted visibility example.

This intentionally does not pretend to be a Draft 2020-12 validator.  The
root environment may only provide jsonschema 3.x.  It checks the invariants
that are specific to this draft (cross-field interval order, ledger references,
and the method-only promotion boundary) while the JSON schema remains the
normative shape contract.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
EXAMPLE = ROOT / "example_visibility_record.json"
MANIFEST = ROOT / "VISIBILITY_MANIFEST.sha256"
PDF_IDENTITY = ROOT / "pdf_build_identity.json"
_ID = re.compile(r"^[A-Z][A-Z0-9._-]+$")


def _ledger_ids(name: str, prefix: str) -> set[str]:
    with (ROOT / name).open(newline="", encoding="utf-8") as handle:
        rows = csv.DictReader(handle)
        result = {row[f"{prefix}_id"] for row in rows}
    if not result or any(not _ID.fullmatch(item) for item in result):
        raise ValueError(f"invalid or empty {prefix} ledger")
    return result


def _validate_ledger_references(source_ids: set[str], claim_ids: set[str], novelty_ids: set[str]) -> None:
    with (ROOT / "claim_ledger.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            supports = [item for item in row["support_ids"].split(";") if item]
            if any(item not in source_ids for item in supports):
                raise ValueError(f"claim {row['claim_id']} references an unknown source")
    with (ROOT / "novelty_ledger.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            supports = [item for item in row["prior_art_source_ids"].split(";") if item]
            if any(item not in source_ids for item in supports):
                raise ValueError(f"novelty {row['novelty_id']} references an unknown source")
    if not claim_ids or not novelty_ids:
        raise ValueError("claim and novelty ledgers must not be empty")


def validate_record(record: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "record_id",
        "status",
        "question",
        "domain",
        "hypotheses",
        "visibility_chain",
        "visibility_kernel",
        "observation_design",
        "predictions",
        "evidence_boundary",
        "provenance",
        "certificate",
    }
    if set(record) != required:
        raise ValueError("record keys do not match the declared protocol")
    if record["schema_version"] != "cosmic-visibility-record-v0.1.0":
        raise ValueError("unsupported record version")
    if record["status"] not in {"unpromoted_research_draft", "reproduction_candidate", "deferred"}:
        raise ValueError("invalid record status")

    source_ids = _ledger_ids("source_ledger.csv", "source")
    claim_ids = _ledger_ids("claim_ledger.csv", "claim")
    novelty_ids = _ledger_ids("novelty_ledger.csv", "novelty")
    _validate_ledger_references(source_ids, claim_ids, novelty_ids)
    provenance = record["provenance"]
    for field, known in (("source_ids", source_ids), ("claim_ids", claim_ids), ("novelty_ids", novelty_ids)):
        unknown = set(provenance[field]) - known
        if unknown:
            raise ValueError(f"unknown {field}: {sorted(unknown)}")
    base = provenance["base_reference"]
    if base != {
        "tag": "v1.0.6",
        "commit": "6982f700bdad2f8e19a3ab4121f1afb0aa323d92",
        "tree": "7aee19aa1bc31ac9d918ff797dc51dfb50d6afae",
    }:
        raise ValueError("base reference is not the immutable v1.0.6 identity")

    stages = record["visibility_chain"]
    stage_ids = [stage["stage_id"] for stage in stages]
    if len(stage_ids) != len(set(stage_ids)):
        raise ValueError("visibility stages must have unique IDs")
    chain_ids = {stage["chain_id"] for stage in stages}
    if len(chain_ids) < 2:
        raise ValueError("visibility example must retain separate physical chains")
    for chain_id in chain_ids:
        kinds = {stage["stage_kind"] for stage in stages if stage["chain_id"] == chain_id}
        if not {"source", "detector", "certificate"}.issubset(kinds):
            raise ValueError(f"chain {chain_id} is missing a source, detector, or certificate stage")
    factor_ids = {factor["factor_id"] for factor in record["visibility_kernel"]["factors"]}
    if len(factor_ids) != len(record["visibility_kernel"]["factors"]):
        raise ValueError("visibility factors must have unique IDs")
    stage_set = set(stage_ids)
    for factor in record["visibility_kernel"]["factors"]:
        if factor["stage_id"] not in stage_set:
            raise ValueError(f"factor references unknown stage: {factor['stage_id']}")
        if factor["value_kind"] == "interval":
            interval = factor.get("interval")
            if not isinstance(interval, dict) or interval["lower"] > interval["upper"]:
                raise ValueError(f"invalid interval for {factor['factor_id']}")
        if factor["value_kind"] == "unknown" and factor.get("value") is not None:
            raise ValueError(f"unknown factor must not carry a value: {factor['factor_id']}")

    observable_ids = {item["observable_id"] for item in record["observation_design"]["observables"]}
    hypothesis_ids = {item["hypothesis_id"] for item in record["hypotheses"]}
    for prediction in record["predictions"]:
        if prediction["observable_id"] not in observable_ids:
            raise ValueError("prediction references unknown observable")
        if prediction["hypothesis_id"] not in hypothesis_ids:
            raise ValueError("prediction references unknown hypothesis")

    certificate = record["certificate"]
    if certificate["kind"] == "method_only" and certificate["result"] != "defer":
        raise ValueError("method-only records cannot be promoted")
    if record["status"] == "unpromoted_research_draft" and certificate["result"] == "pass_with_qualification":
        raise ValueError("unpromoted draft cannot carry a passing certificate")


def validate_example() -> dict[str, Any]:
    record = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValueError("example must be a JSON object")
    validate_record(record)
    return record


def validate_manifest() -> None:
    rows = [line.split("  ", 1) for line in MANIFEST.read_text(encoding="utf-8").splitlines() if line.strip()]
    observed: set[str] = set()
    for digest, relative in rows:
        if relative in observed or Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError(f"invalid manifest entry: {relative}")
        target = ROOT / relative
        if not target.is_file() or target.name == MANIFEST.name:
            raise ValueError(f"missing or recursive manifest entry: {relative}")
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != digest:
            raise ValueError(f"manifest digest mismatch: {relative}")
        observed.add(relative)
    expected = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and path != MANIFEST
    }
    if observed != expected:
        raise ValueError(f"manifest inventory mismatch: missing={sorted(expected - observed)} extra={sorted(observed - expected)}")


def validate_pdf_identity() -> None:
    identity = json.loads(PDF_IDENTITY.read_text(encoding="utf-8"))
    if identity.get("status") != "unpromoted_default_branch_research_draft":
        raise ValueError("PDF identity has an invalid promotion status")
    metadata = json.loads((ROOT / "draft_metadata.json").read_text(encoding="utf-8"))
    base = identity.get("audited_base_commit"), identity.get("audited_base_tree")
    expected_base = metadata.get("audited_base_commit"), metadata.get("audited_base_tree")
    if base != expected_base or identity.get("identity_excludes_self") is not True:
        raise ValueError("PDF identity is not bound to the frozen base reference")
    if identity.get("runtime", {}).get("browser") in {None, "", "not_run"}:
        raise ValueError("PDF identity lacks the actual renderer identity")
    bindings = [identity.get("source"), identity.get("builder")]
    for binding in bindings:
        if not isinstance(binding, dict) or binding.get("name") is None:
            raise ValueError("PDF identity lacks a source or builder binding")
        target = ROOT / str(binding["name"])
        if not target.is_file() or binding.get("sha256") != hashlib.sha256(target.read_bytes()).hexdigest():
            raise ValueError(f"PDF identity digest mismatch: {binding.get('name')}")
    for binding in identity.get("input_bindings", []):
        if not isinstance(binding, dict) or binding.get("name") is None:
            raise ValueError("PDF identity has an invalid input binding")
        target = ROOT.parents[2] / str(binding["name"])
        if not target.is_file() or binding.get("sha256") != hashlib.sha256(target.read_bytes()).hexdigest():
            raise ValueError(f"PDF input digest mismatch: {binding.get('name')}")
    for artifact in identity.get("artifacts", []):
        target = ROOT / str(artifact.get("name"))
        if (
            not target.is_file()
            or artifact.get("bytes") != target.stat().st_size
            or artifact.get("sha256") != hashlib.sha256(target.read_bytes()).hexdigest()
        ):
            raise ValueError(f"PDF artifact identity mismatch: {artifact.get('name')}")


if __name__ == "__main__":
    validate_example()
    validate_manifest()
    validate_pdf_identity()
    print("visibility framework contract passed")
