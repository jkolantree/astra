#!/usr/bin/env python3
"""Validate and serialize the unpromoted SPPT/ASTRA v1.0.8 candidate.

Run without arguments for a read-only verification.  ``--write`` refreshes the
canonical visual-manifest CSV, derived verification summary, package manifest,
and checksum inventory from the final package bytes.  It never creates a
release archive, tag, or remote publication.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any
from xml.etree import ElementTree

from pypdf import PdfReader

SOURCE_DIR = Path(__file__).resolve().parent
PACKAGE_DIR = SOURCE_DIR.parent
REPOSITORY_ROOT = SOURCE_DIR.parents[3]
SUMMARY_PATH = PACKAGE_DIR / "verification" / "verification_summary.json"
GATES_PATH = PACKAGE_DIR / "verification" / "acceptance_gate_matrix.csv"
MANIFEST_PATH = PACKAGE_DIR / "candidate_package_manifest.json"
SUMS_PATH = PACKAGE_DIR / "SHA256SUMS.txt"
VISUAL_CSV_PATH = PACKAGE_DIR / "visual_manifest.csv"

SOURCE_PACKAGE_SHA256 = "55b8962176680859064fa2ebc009bb45ddc0cce987bce0bc16206faa4c7c387a"
REPOSITORY_COMMIT = "f8b32ef0af9cb6804f256490b4daafbdba43740e"
STABLE_RELEASE_COMMIT = "7454b8134cf28c233fe54a11ae4b65e256844821"
FROZEN_MATRIX_SHA256 = "c7b52c0afc887342ad4bdc42f91f979fc49e1cd0b21b8e7c1c31946033de9bed"
FIXED_SVG_DATE = "2026-08-16T00:00:00Z"

DOCUMENTS = {
    "canonical": PACKAGE_DIR / "ASTRA_SPPT_v1.0.8_Endogenous_Visibility_Candidate.pdf",
    "peer_review": (
        PACKAGE_DIR / "ASTRA_SPPT_v1.0.8_Endogenous_Visibility_Candidate_Peer_Review.pdf"
    ),
    "tagged_reading": (
        PACKAGE_DIR / "ASTRA_SPPT_v1.0.8_Endogenous_Visibility_Candidate_Tagged_Reading_Edition.pdf"
    ),
    "verification_report": (
        PACKAGE_DIR / "verification" / "ASTRA_SPPT_v1.0.8_Candidate_Verification_Report.pdf"
    ),
}
DOCX_PATH = PACKAGE_DIR / "ASTRA_SPPT_v1.0.8_Endogenous_Visibility_Candidate.docx"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"cannot serialize an empty CSV: {path.name}")
    fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized_rows(rows))


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def scalar_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def normalized_rows(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [{key: scalar_text(value) for key, value in row.items()} for row in rows]


def validate_safe_relative_path(path: str) -> None:
    pure = PurePosixPath(path)
    if (
        not path
        or "\\" in path
        or path.startswith("/")
        or path.endswith("/")
        or "//" in path
        or pure.is_absolute()
        or any(part in {"", ".", ".."} for part in pure.parts)
        or any(ord(character) < 32 for character in path)
    ):
        raise ValueError(f"unsafe package path: {path!r}")


def validate_ledgers() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    claims = load_json(PACKAGE_DIR / "claim_ledger.json")
    sources = load_json(PACKAGE_DIR / "source_ledger.json")
    visuals = load_json(PACKAGE_DIR / "visual_manifest.json")
    if normalized_rows(claims) != load_csv(PACKAGE_DIR / "claim_ledger.csv"):
        raise ValueError("claim ledger CSV/JSON mismatch")
    if normalized_rows(sources) != load_csv(PACKAGE_DIR / "source_ledger.csv"):
        raise ValueError("source ledger CSV/JSON mismatch")
    if normalized_rows(visuals) != load_csv(PACKAGE_DIR / "visual_manifest.csv"):
        raise ValueError("visual manifest CSV/JSON mismatch")

    claim_ids = [row["claim_id"] for row in claims]
    if len(claims) != 75 or len(set(claim_ids)) != 75:
        raise ValueError("candidate must contain exactly 75 unique claim IDs")
    if len(sources) != 51 or len({row["source_id"] for row in sources}) != 51:
        raise ValueError("candidate must contain exactly 51 unique source records")
    if len(visuals) != 18 or len({row["figure_id"] for row in visuals}) != 18:
        raise ValueError("candidate must contain exactly 18 unique visual records")

    embedded = SOURCE_DIR / "CLAIM_MATRIX_v1.0.7.json"
    if sha256(embedded) != FROZEN_MATRIX_SHA256:
        raise ValueError("embedded v1.0.7 claim matrix identity drift")
    if embedded.read_bytes() != (REPOSITORY_ROOT / "CLAIM_MATRIX.json").read_bytes():
        raise ValueError("embedded v1.0.7 claim matrix differs from repository authority")
    canonical_ids = {row["id"] for row in load_json(embedded)["claims"]}
    if {claim_id for claim_id in claim_ids if not claim_id.startswith("V108-")} != canonical_ids:
        raise ValueError("canonical claim-ID roster drift")
    if len([claim_id for claim_id in claim_ids if claim_id.startswith("V108-")]) != 20:
        raise ValueError("candidate must contain exactly 20 successor claim IDs")
    return claims, sources, visuals


def validate_figures(visuals: list[dict[str, Any]]) -> None:
    expected_png = {row["file_png"] for row in visuals}
    expected_svg = {row["file_svg"] for row in visuals}
    observed_png = {
        path.relative_to(PACKAGE_DIR).as_posix() for path in (PACKAGE_DIR / "figures").glob("*.png")
    }
    observed_svg = {
        path.relative_to(PACKAGE_DIR).as_posix() for path in (PACKAGE_DIR / "figures").glob("*.svg")
    }
    if observed_png != expected_png or observed_svg != expected_svg:
        raise ValueError("figure files differ from the visual-manifest roster")

    namespace = {"svg": "http://www.w3.org/2000/svg"}
    href_names = {"href", "{http://www.w3.org/1999/xlink}href"}
    for relative in sorted(expected_svg):
        path = PACKAGE_DIR / relative
        text = path.read_text(encoding="utf-8")
        if "<!DOCTYPE" in text or "<script" in text or "<foreignObject" in text:
            raise ValueError(f"unsafe or external SVG construct: {relative}")
        if text.count(f"<dc:date>{FIXED_SVG_DATE}</dc:date>") != 1:
            raise ValueError(f"non-fixed SVG metadata date: {relative}")
        root = ElementTree.fromstring(text)
        if not root.findall(".//svg:text", namespace):
            raise ValueError(f"SVG has no live text: {relative}")
        for element in root.iter():
            for name, value in element.attrib.items():
                if name in href_names and not value.startswith("#"):
                    raise ValueError(f"external SVG reference in {relative}: {value!r}")


def outline_count(items: list[Any]) -> int:
    return sum(outline_count(item) if isinstance(item, list) else 1 for item in items)


def dereference(value: Any) -> Any:
    getter = getattr(value, "get_object", None)
    return getter() if getter is not None else value


def pdf_identity(path: Path) -> dict[str, Any]:
    reader = PdfReader(str(path), strict=True)
    if reader.is_encrypted:
        raise ValueError(f"encrypted PDF: {path.name}")
    annotations = 0
    uri_links = 0
    for page in reader.pages:
        page_annotations = dereference(page.get("/Annots", []))
        annotations += len(page_annotations)
        for annotation in page_annotations:
            obj = dereference(annotation)
            action = dereference(obj.get("/A"))
            if action and action.get("/S") == "/URI":
                uri_links += 1
    root = reader.trailer["/Root"]
    return {
        "pages": len(reader.pages),
        "outlines": outline_count(reader.outline),
        "annotations": annotations,
        "uri_links": uri_links,
        "tagged": "/StructTreeRoot" in root,
        "language": str(root.get("/Lang", "")),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def docx_identity() -> dict[str, Any]:
    with zipfile.ZipFile(DOCX_PATH) as archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise ValueError(f"DOCX CRC failure: {bad_member}")
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("DOCX contains duplicate members")
        if "word/document.xml" not in names or "[Content_Types].xml" not in names:
            raise ValueError("DOCX lacks required package members")
        media = [name for name in names if name.startswith("word/media/")]
        document_xml = archive.read("word/document.xml")
        drawing_count = document_xml.count(b"<wp:inline") + document_xml.count(b"<wp:anchor")
        description_count = len(re.findall(rb'<wp:docPr\b[^>]*\bdescr="[^"]+"', document_xml))
        timestamps = {member.date_time for member in archive.infolist()}
    if len(media) != 18 or drawing_count != 18 or description_count != 18:
        raise ValueError("DOCX must contain 18 described figure drawings")
    if timestamps != {(2026, 8, 16, 0, 0, 0)}:
        raise ValueError("DOCX member timestamps are not normalized")
    return {
        "media_files": len(media),
        "described_drawings": description_count,
        "member_timestamp": "2026-08-16T00:00:00Z",
        "bytes": DOCX_PATH.stat().st_size,
        "sha256": sha256(DOCX_PATH),
    }


def gate_counts() -> dict[str, int]:
    rows = load_csv(GATES_PATH)
    counts = Counter(row["status"] for row in rows)
    allowed = {"PASS", "FAIL", "NOT_RUN", "DEFERRED", "ENVIRONMENT_LIMITED"}
    if not counts or set(counts) - allowed:
        raise ValueError(f"unknown acceptance-gate status: {sorted(set(counts) - allowed)}")
    if counts.get("FAIL", 0):
        raise ValueError("acceptance matrix contains a failing gate")
    return {key: counts[key] for key in sorted(counts)}


def verification_summary() -> dict[str, Any]:
    claims, sources, visuals = validate_ledgers()
    validate_figures(visuals)
    documents = {name: pdf_identity(path) for name, path in DOCUMENTS.items()}
    docx = docx_identity()
    return {
        "verdict": "REVIEWED_UNPROMOTED_CANDIDATE",
        "source_package_sha256": SOURCE_PACKAGE_SHA256,
        "repository_main_commit": REPOSITORY_COMMIT,
        "stable_release": "v1.0.7",
        "build_runtime": "CPython 3.12.10",
        "documents": documents,
        "docx": docx,
        "claim_count": len(claims),
        "source_count": len(sources),
        "figure_count": len(visuals),
        "acceptance_gate_counts": gate_counts(),
        "not_certified": [
            "release promotion or immutable v1.0.8 identity",
            "external peer review",
            "independent experimental or raw-data reproduction",
            "DOCX page-layout equivalence in Word or LibreOffice",
            "PDF/UA conformance",
        ],
    }


def package_files(*, include_manifest: bool) -> list[Path]:
    excluded = {SUMS_PATH.resolve()}
    if not include_manifest:
        excluded.add(MANIFEST_PATH.resolve())
    files = [
        path
        for path in PACKAGE_DIR.rglob("*")
        if path.is_file()
        and path.resolve() not in excluded
        and "__pycache__" not in path.parts
        and ".pyc" not in path.suffixes
    ]
    relative = [path.relative_to(PACKAGE_DIR).as_posix() for path in files]
    for path in relative:
        validate_safe_relative_path(path)
    if len(relative) != len(set(relative)):
        raise ValueError("duplicate package paths")
    return [path for _, path in sorted(zip(relative, files, strict=True))]


def payload_entries() -> list[dict[str, Any]]:
    return [
        {
            "path": path.relative_to(PACKAGE_DIR).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in package_files(include_manifest=False)
    ]


def package_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    payload = payload_entries()
    return {
        "package": "SPPT / ASTRA v1.0.8 Candidate - Endogenous Visibility",
        "status": "reviewed_unpromoted_candidate",
        "source_package_sha256": SOURCE_PACKAGE_SHA256,
        "created_utc": "2026-08-16T00:00:00Z",
        "repository_basis": {
            "repository": "jkolantree/astra",
            "audited_commit": REPOSITORY_COMMIT,
            "stable_release": "v1.0.7",
            "stable_release_commit": STABLE_RELEASE_COMMIT,
            "repository_write_performed_by_source_package": False,
        },
        "document_counts": {
            "canonical_pdf_pages": summary["documents"]["canonical"]["pages"],
            "peer_review_pdf_pages": summary["documents"]["peer_review"]["pages"],
            "tagged_pdf_pages": summary["documents"]["tagged_reading"]["pages"],
            "verification_report_pages": summary["documents"]["verification_report"]["pages"],
            "atomic_claims": summary["claim_count"],
            "source_records": summary["source_count"],
            "scientific_figures": summary["figure_count"],
        },
        "acceptance_gate_counts": summary["acceptance_gate_counts"],
        "verification": summary,
        "payload_file_count_excluding_manifest_and_sha256sums": len(payload),
        "payload_total_bytes_excluding_manifest_and_sha256sums": sum(
            entry["bytes"] for entry in payload
        ),
        "payload": payload,
    }


def checksum_text() -> str:
    lines = []
    for path in package_files(include_manifest=True):
        relative = path.relative_to(PACKAGE_DIR).as_posix()
        lines.append(f"{sha256(path)}  {relative}")
    return "\n".join(lines) + "\n"


def verify_serialized(summary: dict[str, Any], manifest: dict[str, Any]) -> None:
    if load_json(SUMMARY_PATH) != summary:
        raise ValueError("verification_summary.json is stale; run with --write")
    if load_json(MANIFEST_PATH) != manifest:
        raise ValueError("candidate_package_manifest.json is stale; run with --write")
    if SUMS_PATH.read_text(encoding="utf-8") != checksum_text():
        raise ValueError("SHA256SUMS.txt is stale; run with --write")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="refresh derived identity files")
    arguments = parser.parse_args()

    if arguments.write:
        write_csv(VISUAL_CSV_PATH, load_json(PACKAGE_DIR / "visual_manifest.json"))
    summary = verification_summary()
    if arguments.write:
        write_json(SUMMARY_PATH, summary)
        manifest = package_manifest(summary)
        write_json(MANIFEST_PATH, manifest)
        SUMS_PATH.write_text(checksum_text(), encoding="utf-8", newline="\n")
    else:
        verify_serialized(summary, package_manifest(summary))
    print(
        "candidate verification complete: "
        f"{summary['claim_count']} claims, {summary['source_count']} sources, "
        f"{summary['figure_count']} figures"
    )


if __name__ == "__main__":
    main()
