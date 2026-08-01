"""Inspect released PDFs for syntax, metadata, structure, fonts, links, and text."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

import pikepdf
from fontTools.ttLib import TTCollection, TTFont
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "manuscript"
AUTHOR = "Jacko T."
FIXED_DATE = "D:20260801000000Z"
PDFS = (
    MANUSCRIPT / "SPPT_ASTRA_preprint_v1.0.1.pdf",
    MANUSCRIPT / "SPPT_ASTRA_technical_supplement_v1.0.1.pdf",
)
PRIVATE_PATTERN = re.compile(
    r"(?:^\s*(?:contact|correspondence)\s*[:=]\s*(?:TBD|TODO|pending|placeholder)\b|"
    r"[A-Za-z]:\\|/Users/|/home/|"
    r"\b[A-Z][A-Za-z .'-]+,\s*(?:USA|United States)\b)",
    re.IGNORECASE | re.MULTILINE,
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def dereference(value: Any) -> Any:
    try:
        return value.get_object()
    except (AttributeError, ValueError):
        return value


def font_record(name: Any, font_reference: Any) -> dict[str, Any]:
    font = dereference(font_reference)
    subtype = str(font.get("/Subtype", ""))
    descendant = font
    if subtype == "/Type0" and "/DescendantFonts" in font:
        descendants = dereference(font["/DescendantFonts"])
        if descendants:
            descendant = dereference(descendants[0])
    descriptor = dereference(descendant.get("/FontDescriptor", {}))
    embedded = any(key in descriptor for key in ("/FontFile", "/FontFile2", "/FontFile3"))
    return {
        "resource_name": str(name),
        "base_font": str(font.get("/BaseFont", descendant.get("/BaseFont", ""))),
        "subtype": subtype,
        "embedded": embedded,
        "to_unicode": "/ToUnicode" in font,
    }


def verify_windows_font_embedding_permissions(
    font_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    runtime = json.loads((ROOT / "RUNTIME.json").read_text(encoding="utf-8"))
    specifications = {
        item["postscript_name"]: item for item in runtime["pdf_renderer"]["system_fonts"]
    }
    windows_root = os.environ.get("WINDIR")
    if not windows_root:
        raise RuntimeError("WINDIR is required to audit embedded Windows font sources")
    observed: list[dict[str, Any]] = []
    base_fonts = " ".join(record["base_font"] for record in font_records)
    if "CambriaMath" in base_fonts:
        specification = specifications["CambriaMath"]
        collection_path = Path(windows_root) / "Fonts" / specification["file"]
        if not collection_path.is_file():
            raise RuntimeError("Cambria Math was embedded but its source font cannot be audited")
        identity = {
            "postscript_name": "CambriaMath",
            "file": specification["file"],
            "bytes": collection_path.stat().st_size,
            "sha256": sha256_path(collection_path),
        }
        if identity != {key: specification[key] for key in identity}:
            raise RuntimeError(f"Cambria Math source-font identity drift: {identity}")
        collection = TTCollection(collection_path)
        permissions = {
            font["name"].getDebugName(6): int(font["OS/2"].fsType)
            for font in collection.fonts
        }
        if permissions.get("CambriaMath") != 8:
            raise RuntimeError(f"Cambria Math embedding flag is not editable (8): {permissions}")
        identity["embedding_fs_type"] = 8
        observed.append(identity)
    if "TimesNewRomanPSMT" in base_fonts:
        specification = specifications["TimesNewRomanPSMT"]
        times_path = Path(windows_root) / "Fonts" / specification["file"]
        if not times_path.is_file():
            raise RuntimeError("Times New Roman was embedded but its source font cannot be audited")
        identity = {
            "postscript_name": "TimesNewRomanPSMT",
            "file": specification["file"],
            "bytes": times_path.stat().st_size,
            "sha256": sha256_path(times_path),
        }
        if identity != {key: specification[key] for key in identity}:
            raise RuntimeError(f"Times New Roman source-font identity drift: {identity}")
        times = TTFont(times_path)
        if int(times["OS/2"].fsType) != 8:
            raise RuntimeError("Times New Roman embedding flag is not editable (8)")
        identity["embedding_fs_type"] = 8
        observed.append(identity)
    return observed


def inspect(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    reader = PdfReader(path)
    if reader.is_encrypted:
        raise RuntimeError(f"{path.name} must not be encrypted")
    page_text = [(page.extract_text() or "").strip() for page in reader.pages]
    if not page_text or any(not text for text in page_text):
        raise RuntimeError(f"Every page of {path.name} must have extractable text")
    for page_number, text in enumerate(page_text, start=1):
        if text.splitlines()[-1].strip() != str(page_number):
            raise RuntimeError(
                f"Page {page_number} of {path.name} is missing its visible page number"
            )
    normalized = re.sub(r"\s+", " ", "\n".join(page_text)).strip()
    if PRIVATE_PATTERN.search(normalized):
        raise RuntimeError(f"Private or machine-local text found in {path.name}")

    with pikepdf.open(path) as pdf:
        syntax_warnings = pdf.check_pdf_syntax()
        if syntax_warnings:
            raise RuntimeError(f"PDF syntax warnings in {path.name}: {syntax_warnings}")
        root = pdf.Root
        if "/StructTreeRoot" not in root:
            raise RuntimeError(f"Tagged structure tree missing from {path.name}")
        mark_info = dereference(root.get("/MarkInfo", {}))
        if not bool(mark_info.get("/Marked", False)):
            raise RuntimeError(f"Marked=true missing from {path.name}")
        if str(root.get("/Lang", "")) != "en-US":
            raise RuntimeError(f"Document language is not en-US in {path.name}")
        preferences = dereference(root.get("/ViewerPreferences", {}))
        if not bool(preferences.get("/DisplayDocTitle", False)):
            raise RuntimeError(f"DisplayDocTitle is not enabled in {path.name}")
        if "/Outlines" not in root:
            raise RuntimeError(f"Document outline missing from {path.name}")

        docinfo = {str(key): str(value) for key, value in pdf.docinfo.items()}
        expected_metadata = {
            "/Author": AUTHOR,
            "/CreationDate": FIXED_DATE,
            "/ModDate": FIXED_DATE,
        }
        for key, expected in expected_metadata.items():
            if docinfo.get(key) != expected:
                raise RuntimeError(f"{path.name} metadata {key} does not equal {expected!r}")
        if PRIVATE_PATTERN.search(json.dumps(docinfo, ensure_ascii=False)):
            raise RuntimeError(f"Private or machine-local PDF metadata found in {path.name}")

        fonts: dict[tuple[str, str], dict[str, Any]] = {}
        links: list[str] = []
        for page in pdf.pages:
            resources = dereference(page.obj.get("/Resources", {}))
            font_dictionary = dereference(resources.get("/Font", {}))
            for name, font_reference in font_dictionary.items():
                record = font_record(name, font_reference)
                fonts[(record["base_font"], record["subtype"])] = record
            annotations = dereference(page.obj.get("/Annots", []))
            for annotation_reference in annotations:
                annotation = dereference(annotation_reference)
                if str(annotation.get("/Subtype", "")) != "/Link":
                    continue
                action = dereference(annotation.get("/A", {}))
                if str(action.get("/S", "")) == "/URI":
                    uri = str(action.get("/URI", ""))
                    if not uri.startswith(("https://", "http://", "mailto:")):
                        raise RuntimeError(f"Unsafe PDF link {uri!r} in {path.name}")
                    links.append(uri)

        font_records = sorted(fonts.values(), key=lambda item: (item["base_font"], item["subtype"]))
        if not font_records or any(not record["embedded"] for record in font_records):
            raise RuntimeError(f"Every font must be embedded in {path.name}: {font_records}")
        allowed_font_fragments = ("DejaVu", "CambriaMath", "TimesNewRomanPSMT")
        if any(
            not any(fragment in record["base_font"] for fragment in allowed_font_fragments)
            for record in font_records
        ):
            raise RuntimeError(f"Unexpected font in {path.name}: {font_records}")
        if any(record["subtype"] == "/Type0" and not record["to_unicode"] for record in font_records):
            raise RuntimeError(f"Every Type0 font needs ToUnicode in {path.name}")
        source_font_identities = verify_windows_font_embedding_permissions(font_records)

        figure_tags = 0
        figure_leaf_tags = 0
        figure_alt_tags = 0
        for obj in pdf.objects:
            candidate = dereference(obj)
            if not isinstance(candidate, pikepdf.Dictionary):
                continue
            if str(candidate.get("/S", "")) == "/Figure":
                figure_tags += 1
                if "/Pg" not in candidate:
                    continue
                figure_leaf_tags += 1
                alt = str(candidate.get("/Alt", "")).strip()
                if alt:
                    figure_alt_tags += 1
        if figure_leaf_tags < 1 or figure_alt_tags != figure_leaf_tags:
            raise RuntimeError(
                f"Every tagged figure needs alt text in {path.name}: "
                f"{figure_alt_tags}/{figure_leaf_tags}"
            )

        with pdf.open_metadata(set_pikepdf_as_editor=False) as xmp:
            xmp_summary = {
                "title": str(xmp.get("dc:title", "")),
                "creator": list(xmp.get("dc:creator", [])),
                "language": list(xmp.get("dc:language", [])),
                "created": str(xmp.get("xmp:CreateDate", "")),
                "modified": str(xmp.get("xmp:ModifyDate", "")),
            }
        if xmp_summary["creator"] != [AUTHOR] or xmp_summary["language"] != ["en-US"]:
            raise RuntimeError(f"XMP identity mismatch in {path.name}: {xmp_summary}")

    return {
        "file": path.name,
        "bytes": len(raw),
        "sha256": sha256_bytes(raw),
        "pages": len(reader.pages),
        "all_pages_have_extractable_text": True,
        "all_pages_have_visible_page_numbers": True,
        "normalized_text_sha256": sha256_bytes(normalized.encode("utf-8")),
        "tagged": True,
        "figure_tags": figure_tags,
        "figure_leaf_tags": figure_leaf_tags,
        "figure_alt_tags": figure_alt_tags,
        "outline_present": True,
        "language": "en-US",
        "display_doc_title": True,
        "fonts": font_records,
        "source_font_identities": source_font_identities,
        "external_link_count": len(links),
        "external_links": sorted(set(links)),
        "metadata": docinfo,
        "xmp": xmp_summary,
        "syntax_warnings": [],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()
    paths = tuple(args.paths) or PDFS
    report = {
        "schema": "https://github.com/jkolantree/astra/schemas/pdf-inspection-v1",
        "records": [inspect(path.resolve()) for path in paths],
    }
    serialized = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.write:
        (MANUSCRIPT / "pdf_inspection.json").write_text(
            serialized, encoding="utf-8", newline="\n"
        )
    else:
        print(serialized, end="")


if __name__ == "__main__":
    main()
