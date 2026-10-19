"""Structural proposal admission; calibration readiness is a separate gate."""

import json
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

FOG_KEYS = {"reference", "resolution", "generator_family", "chronology", "system_boundary"}
REQUIRED = {
    "contract_id",
    "schema_version",
    "query",
    "fog",
    "falsifier",
    "legal_interventions",
    "units",
    "operators",
    "nuisance_support",
    "calibration",
    "dependence_roots",
    "split",
    "acceptance",
    "source_ids",
    "relation_type",
    "source_verification",
    "framework_validation",
    "release_status",
    "supersedes",
}


def validate_bridge(record: object) -> list[str]:
    if not isinstance(record, dict):
        return ["record must be an object"]
    errors = ["missing " + k for k in sorted(REQUIRED - record.keys())]
    for k in ("contract_id", "query", "falsifier", "schema_version"):
        if not isinstance(record.get(k), str) or not record[k].strip():
            errors.append(k + " must be explicit")
    fog = record.get("fog")
    if (
        not isinstance(fog, dict)
        or set(fog) != FOG_KEYS
        or any(not isinstance(v, str) or not v.strip() for v in fog.values())
    ):
        errors.append("FOG requires exactly five explicit coordinates")
    if record.get("schema_version") != "0.2.0":
        errors.append("unsupported schema version")
    if record.get("release_status") != "unpromoted-research-candidate":
        errors.append("this gate cannot promote a release")
    if record.get("framework_validation") != "not-empirically-validated":
        errors.append("this structural gate cannot confer empirical validation")
    units = record.get("units")
    if (
        not isinstance(units, dict)
        or not units
        or any(not isinstance(v, str) or not v for v in units.values())
    ):
        errors.append("units missing")
    for k in ["operators", "legal_interventions", "dependence_roots", "source_ids"]:
        if not isinstance(record.get(k), list) or not record[k]:
            errors.append(k + " must be a nonempty list")
    for k in ["nuisance_support", "calibration", "split", "acceptance", "supersedes"]:
        if not isinstance(record.get(k), dict) or not record[k]:
            errors.append(k + " must be an explicit record")
    cal = record.get("calibration")
    if not isinstance(cal, dict) or cal.get("status") not in ["planned", "verified"]:
        errors.append("calibration status missing")
    return errors


def audit_bridges(records: Iterable[object]) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    ids = []
    for r in records:
        errors = validate_bridge(r)
        cid = r.get("contract_id") if isinstance(r, dict) else None
        if cid in ids:
            errors.append("duplicate contract ID")
        ids.append(cid)
        # This module validates declarations only. No supplied artifact bytes,
        # calibration units/covariance, or independent split are authenticated.
        calibration = r.get("calibration") if isinstance(r, dict) else None
        calibration_declared = (
            not errors and isinstance(calibration, dict) and calibration.get("status") == "verified"
        )
        calibration_ready = False
        results.append(
            {
                "contract_id": cid,
                "structural_proposal_pass": not errors,
                "calibration_declared": calibration_declared,
                "calibration_ready": calibration_ready,
                "readiness_status": "not-assessed-declaration-only",
                "empirical_admission": False,
                "errors": errors,
            }
        )
    return {
        "schema_version": "0.2.0",
        "results": results,
        "structural_pass_count": sum(r["structural_proposal_pass"] for r in results),
        "calibration_ready_count": sum(r["calibration_ready"] for r in results),
        "empirical_admission_count": 0,
    }


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contracts", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    results = audit_bridges(json.loads(args.contracts.read_text()))
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(results, stream, indent=2, allow_nan=False)
        stream.write("\n")
    return 0 if all(not row["errors"] for row in results["results"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
