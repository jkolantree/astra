"""Regenerate the v1.0.8 candidate claim and source ledgers.

The immutable v1.0.7 ``CLAIM_MATRIX.json`` is embedded byte-for-byte and is the
authority for its 55 public claim identifiers. This generator projects those
records into the candidate ledger without changing their identifiers,
statements, support items, limitations, evidence classes, or dispositions.

Projection rules for fields absent from the frozen matrix are explicit:

* ``scientific_status`` is derived only from ``disposition`` through
  ``SCIENTIFIC_STATUS``;
* ``falsifier_or_next_test`` states that no separate frozen field exists and
  directs readers to the preserved limitations and support;
* canonical ``support`` and ``limitations_or_counterexamples`` lists are joined
  with ``LIST_SEPARATOR`` after checking that the separator occurs in no item.
  Their exact list structure remains in the byte-identical embedded matrix.

One frozen v1.0.7 support list contains the historical token
``darkMatterCoherence2026``. Rewriting it would violate the exact-core boundary.
The candidate source ledger therefore resolves that token as a strictly typed
legacy alias to the inspectable Cosmic Visibility draft at the frozen commit.
The alias is not an independently published source, and neither the v1.0.8
manuscript nor its bibliography cites the uninspectable conversation artifact.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

SOURCE_DIR = Path(__file__).resolve().parent
PACKAGE_DIR = SOURCE_DIR.parent
EMBEDDED_MATRIX = SOURCE_DIR / "CLAIM_MATRIX_v1.0.7.json"
ADDITIONS_SOURCE = SOURCE_DIR / "claim_ledger_v1.0.8_additions.json"
SOURCES_SOURCE = SOURCE_DIR / "source_ledger_v1.0.8_records.json"
CLAIM_JSON = PACKAGE_DIR / "claim_ledger.json"
CLAIM_CSV = PACKAGE_DIR / "claim_ledger.csv"
SOURCE_JSON = PACKAGE_DIR / "source_ledger.json"
SOURCE_CSV = PACKAGE_DIR / "source_ledger.csv"

FROZEN_MATRIX_SHA256 = "c7b52c0afc887342ad4bdc42f91f979fc49e1cd0b21b8e7c1c31946033de9bed"
FROZEN_COMMIT = "f8b32ef0af9cb6804f256490b4daafbdba43740e"
LIST_SEPARATOR = " || "

CLAIM_FIELDS = [
    "claim_id",
    "statement",
    "claim_type",
    "scientific_status",
    "evidence_class",
    "disposition",
    "support",
    "limitations",
    "falsifier_or_next_test",
]
SOURCE_FIELDS = [
    "source_id",
    "authors",
    "title",
    "year",
    "venue_or_publisher",
    "doi",
    "url",
    "source_type",
    "publication_status",
    "access_date",
    "verification_status",
    "claims_supported",
    "notes",
]

SCIENTIFIC_STATUS = {
    "admit": "Admitted",
    "admit_with_qualification": "Admitted with qualification",
    "proposed_only": "Proposed only",
    "deferred": "Deferred",
    "rejected": "Rejected",
}

EXPECTED_ADDITION_IDS = [
    "V108-M001",
    "V108-M002",
    "V108-F002",
    "V108-R001",
    "V108-R002",
    "V108-E001",
    "V108-A001",
    "V108-D001",
    "V108-E002a",
    "V108-E002b",
    "V108-A002",
    "V108-D002",
    "V108-E003",
    "V108-A003",
    "V108-D003",
    "V108-E004",
    "V108-A004",
    "V108-D004",
    "V108-F001",
    "V108-D005",
]

REQUIRED_SOURCE_IDS = {
    "astraRepo2026",
    "astraRelease106",
    "astraManuscript106",
    "astraClaims106",
    "spptSupplement106",
    "astraRelease107",
    "astraManuscript107",
    "astraClaims107",
    "spptSupplement107",
    "astraMainM1",
    "darkMatterCoherence2026",
    "oleary2009",
    "jiang2017",
}


def sha256(path: Path) -> str:
    """Return the SHA-256 digest of *path*."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    """Load UTF-8 JSON from *path*."""

    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path: Path, value: Any) -> None:
    """Write stable UTF-8 JSON with a final newline."""

    text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    """Write a stable CSV serialization."""

    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def flatten_exact(items: list[str]) -> str:
    """Join a canonical string list without modifying any item."""

    if any(LIST_SEPARATOR in item for item in items):
        raise ValueError(f"canonical item contains reserved {LIST_SEPARATOR!r}")
    return LIST_SEPARATOR.join(items)


def project_canonical_claim(claim: dict[str, Any]) -> dict[str, str]:
    """Project one frozen claim into the candidate ledger schema."""

    disposition = claim["disposition"]
    if disposition not in SCIENTIFIC_STATUS:
        raise ValueError(f"unknown canonical disposition: {disposition}")
    return {
        "claim_id": claim["id"],
        "statement": claim["statement"],
        "claim_type": claim["claim_type"],
        "scientific_status": SCIENTIFIC_STATUS[disposition],
        "evidence_class": claim["evidence_class"],
        "disposition": disposition,
        "support": flatten_exact(claim["support"]),
        "limitations": flatten_exact(claim["limitations_or_counterexamples"]),
        "falsifier_or_next_test": (
            "No separate field exists in the frozen v1.0.7 matrix; use its "
            "preserved limitations and cited support."
        ),
    }


def validate_fields(rows: list[dict[str, str]], fields: list[str], label: str) -> None:
    """Require schema-exact scalar ledger rows."""

    required = set(fields)
    for index, row in enumerate(rows):
        if set(row) != required:
            raise ValueError(f"{label} row {index} has wrong fields")
        if any(not isinstance(row[field], str) for field in fields):
            raise ValueError(f"{label} row {index} has a non-string field")


def validate_sources(sources: list[dict[str, str]]) -> None:
    """Validate source identity, version binding, and the legacy alias boundary."""

    validate_fields(sources, SOURCE_FIELDS, "source")
    source_ids = [source["source_id"] for source in sources]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("source ledger contains duplicate identifiers")
    missing = sorted(REQUIRED_SOURCE_IDS - set(source_ids))
    if missing:
        raise ValueError(f"source ledger is missing required identifiers: {missing}")

    for source in sources:
        url = source["url"]
        if "/blob/main/" in url or "/tree/main/" in url:
            raise ValueError(f"mutable main-branch URL remains: {source['source_id']}")

    by_id = {source["source_id"]: source for source in sources}
    legacy_alias = by_id["darkMatterCoherence2026"]
    expected_alias_url = (
        f"https://github.com/jkolantree/astra/blob/{FROZEN_COMMIT}/"
        "resources/cosmic-visibility-framework/draft-v0.1.0/CORE_FRAMEWORK.md"
    )
    if (
        legacy_alias["source_type"] != ("frozen historical identifier / repository-bound alias")
        or legacy_alias["url"] != expected_alias_url
    ):
        raise ValueError("historical darkMatterCoherence2026 token is not a bound alias")


def generate() -> None:
    """Generate both ledgers from frozen, package-local sources."""

    if sha256(EMBEDDED_MATRIX) != FROZEN_MATRIX_SHA256:
        raise ValueError("embedded matrix does not match immutable v1.0.7 bytes")
    matrix = load_json(EMBEDDED_MATRIX)
    canonical_claims = matrix["claims"]
    canonical_ids = [claim["id"] for claim in canonical_claims]
    if len(canonical_claims) != 55 or len(set(canonical_ids)) != 55:
        raise ValueError("frozen matrix must contain exactly 55 unique claims")

    additions = load_json(ADDITIONS_SOURCE)
    validate_fields(additions, CLAIM_FIELDS, "candidate addition")
    addition_ids = [claim["claim_id"] for claim in additions]
    if addition_ids != EXPECTED_ADDITION_IDS:
        raise ValueError("candidate additions do not match the frozen 20-ID order")
    if set(canonical_ids) & set(addition_ids):
        raise ValueError("candidate additions collide with frozen public claim IDs")
    if any(claim["disposition"] not in SCIENTIFIC_STATUS for claim in additions):
        raise ValueError("candidate addition has a noncanonical disposition")

    claims = [project_canonical_claim(claim) for claim in canonical_claims] + additions
    claim_ids = [claim["claim_id"] for claim in claims]
    if len(claims) != 75 or len(set(claim_ids)) != 75:
        raise ValueError("candidate ledger must contain 75 unique claim identifiers")
    if "V108-R003" in claim_ids:
        raise ValueError("V108-R003 is intentionally not assigned")
    validate_fields(claims, CLAIM_FIELDS, "claim")

    sources = load_json(SOURCES_SOURCE)
    validate_sources(sources)

    write_json(CLAIM_JSON, claims)
    write_csv(CLAIM_CSV, claims, CLAIM_FIELDS)
    write_json(SOURCE_JSON, sources)
    write_csv(SOURCE_CSV, sources, SOURCE_FIELDS)


if __name__ == "__main__":
    generate()
