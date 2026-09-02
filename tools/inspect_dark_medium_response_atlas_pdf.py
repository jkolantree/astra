"""Inspect the Atlas PDF without claiming PDF/UA conformance."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import pikepdf
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "resources" / "dark-medium-response-atlas" / "v0.1.0"
PDF = PACKAGE / "dark-medium-response-atlas-v0.1.0.pdf"
HTML = PACKAGE / "dark-medium-response-atlas-v0.1.0.html"
SPEC = json.loads((PACKAGE / "RELEASE_SPEC.json").read_text(encoding="utf-8"))
REPORT = PACKAGE / "pdf-inspection.json"
FORMULA_ALT_PREFIX = "Formula in TeX: "
COMPATIBILITY_LIGATURES = frozenset("\ufb00\ufb01\ufb02\ufb03\ufb04\ufb05\ufb06")

sys.path.insert(0, str(ROOT))
from tools.dark_medium_response_atlas_pdf_helpers import (  # noqa: E402
    attribute_dictionaries,
    dereference,
    font_record,
    html_heading_titles,
    pdf_outline_titles,
    structure_elements,
    validate_pdf_font_records,
    validate_structure_identifiers,
    verify_bundled_font_sources,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metadata_contract() -> dict[str, str]:
    epoch = str(SPEC["build_epoch"])
    return {
        "/Title": str(SPEC["title"]),
        "/Author": str(SPEC["author"]),
        "/Subject": "ASTRA supplemental working paper and methods proposal; not peer reviewed",
        "/Producer": (
            "ASTRA Dark-Medium Response Atlas deterministic build v0.1.0; "
            "pikepdf 10.11.0"
        ),
        "/CreationDate": "D:" + re.sub(r"[-:T]", "", epoch),
        "/ModDate": "D:" + re.sub(r"[-:T]", "", epoch),
    }


def inspect_pdf(path: Path = PDF, *, write_report: bool = False) -> dict[str, Any]:
    reader = PdfReader(path)
    if reader.is_encrypted:
        raise RuntimeError("Atlas PDF must not be encrypted")
    page_text = [(page.extract_text() or "").strip() for page in reader.pages]
    if not page_text or any(not text for text in page_text):
        raise RuntimeError("Every Atlas PDF page must have extractable text")
    text = re.sub(r"\s+", " ", "\n".join(page_text)).strip()
    remaining_ligatures = sorted(set(text) & COMPATIBILITY_LIGATURES)
    if remaining_ligatures:
        raise RuntimeError(f"Compatibility ligatures remain: {remaining_ligatures}")
    if "identifiability" not in text.casefold() or "five-minute summary" not in text.casefold():
        raise RuntimeError("Atlas exact-search sentinels are absent")
    if re.search(r"[A-Za-z]:\\|/Users/|/home/", text):
        raise RuntimeError("Machine-local text leaked into Atlas PDF")
    outlines = pdf_outline_titles(reader)
    expected_outlines = html_heading_titles(HTML)
    if outlines != expected_outlines:
        raise RuntimeError("Atlas PDF outline does not match the HTML heading sequence")
    expected_formula_count = len(re.findall(r"<math(?:\s|>)", HTML.read_text(encoding="utf-8")))
    if expected_formula_count < 1:
        raise RuntimeError("Atlas HTML has no MathML formulas")

    with pikepdf.open(path) as pdf:
        warnings = pdf.check_pdf_syntax()
        if warnings:
            raise RuntimeError(f"PDF syntax warnings: {warnings}")
        root = pdf.Root
        mark_info = dereference(root.get("/MarkInfo", {}))
        preferences = dereference(root.get("/ViewerPreferences", {}))
        if "/StructTreeRoot" not in root or not bool(mark_info.get("/Marked", False)):
            raise RuntimeError("Atlas PDF is not structurally tagged")
        if str(root.get("/Lang", "")) != "en-US":
            raise RuntimeError("Atlas PDF language is not en-US")
        if not bool(preferences.get("/DisplayDocTitle", False)):
            raise RuntimeError("Atlas PDF does not display its document title")
        structure_identity = validate_structure_identifiers(pdf)
        docinfo = {str(key): str(value) for key, value in pdf.docinfo.items()}
        for key, expected in metadata_contract().items():
            if docinfo.get(key) != expected:
                raise RuntimeError(f"Atlas PDF metadata mismatch for {key}: {docinfo.get(key)!r}")

        fonts: dict[tuple[str, str], dict[str, Any]] = {}
        links: list[str] = []
        link_rectangles = 0
        for page in pdf.pages:
            resources = dereference(page.obj.get("/Resources", {}))
            for name, reference in dereference(resources.get("/Font", {})).items():
                record = font_record(name, reference)
                fonts[(record["base_font"], record["subtype"])] = record
            annotations = dereference(page.obj.get("/Annots", []))
            for reference in annotations:
                annotation = dereference(reference)
                if str(annotation.get("/Subtype", "")) != "/Link":
                    continue
                rectangle = dereference(annotation.get("/Rect", []))
                if len(rectangle) != 4 or float(rectangle[2]) <= float(rectangle[0]) or float(
                    rectangle[3]
                ) <= float(rectangle[1]):
                    raise RuntimeError("Atlas PDF contains an empty link annotation")
                link_rectangles += 1
                action = dereference(annotation.get("/A", {}))
                if str(action.get("/S", "")) == "/URI":
                    uri = str(action.get("/URI", ""))
                    if not uri.startswith(("https://", "http://", "mailto:")):
                        raise RuntimeError(f"Unsafe or machine-local PDF URI: {uri!r}")
                    links.append(uri)
        font_records = sorted(fonts.values(), key=lambda item: (item["base_font"], item["subtype"]))
        validate_pdf_font_records(font_records)
        source_fonts = verify_bundled_font_sources(font_records)

        elements = list(structure_elements(root["/StructTreeRoot"].get("/K", pikepdf.Array())))
        formulas = [item for item in elements if str(item.get("/S", "")) == "/Formula"]
        tables = [item for item in elements if str(item.get("/S", "")) == "/Table"]
        captions = [item for item in elements if str(item.get("/S", "")) == "/Caption"]
        figures = [item for item in elements if str(item.get("/S", "")) == "/Figure"]
        if len(formulas) != expected_formula_count:
            raise RuntimeError("Atlas PDF Formula tags do not cover every HTML formula")
        if any(
            not str(item.get("/Alt", "")).startswith(FORMULA_ALT_PREFIX)
            or not str(item.get("/ActualText", "")).strip()
            for item in formulas
        ):
            raise RuntimeError("Atlas PDF formula alternatives are incomplete")
        if len(tables) != 4 or len(captions) != 4:
            raise RuntimeError("Atlas PDF table/caption tags are incomplete")
        header_scopes: list[str] = []
        for item in elements:
            if str(item.get("/S", "")) != "/TH":
                continue
            header_scopes.extend(
                str(attribute["/Scope"])
                for attribute in attribute_dictionaries(item.get("/A", pikepdf.Array()))
                if "/Scope" in attribute
            )
        if header_scopes.count("/Column") < 4 or header_scopes.count("/Row") < 4:
            raise RuntimeError("Atlas PDF table header scopes are incomplete")
        if any(not str(item.get("/Alt", "")).strip() for item in figures):
            raise RuntimeError("Atlas PDF figure alternative text is incomplete")

        with pdf.open_metadata(set_pikepdf_as_editor=False) as xmp:
            xmp_summary = {
                "title": str(xmp.get("dc:title", "")),
                "creator": list(xmp.get("dc:creator", [])),
                "language": list(xmp.get("dc:language", [])),
                "created": str(xmp.get("xmp:CreateDate", "")),
                "modified": str(xmp.get("xmp:ModifyDate", "")),
            }
        if xmp_summary != {
            "title": SPEC["title"],
            "creator": [SPEC["author"]],
            "language": ["en-US"],
            "created": SPEC["build_epoch"],
            "modified": SPEC["build_epoch"],
        }:
            raise RuntimeError(f"Atlas XMP metadata mismatch: {xmp_summary}")

    report = {
        "schema": (
            "https://jkolantree.github.io/astra/schemas/"
            "dark-medium-response-atlas-pdf-inspection-v1.schema.json"
        ),
        "file": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "pages": len(reader.pages),
        "normalized_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "tagged": True,
        "pdf_ua_claim": False,
        "outline_titles_match_html": True,
        "formula_tags": len(formulas),
        "table_tags": len(tables),
        "table_caption_tags": len(captions),
        "figure_tags": len(figures),
        "link_annotation_count": link_rectangles,
        "external_links": sorted(set(links)),
        "fonts": font_records,
        "source_font_identities": source_fonts,
        "metadata": docinfo,
        "xmp": xmp_summary,
        **structure_identity,
    }
    if write_report:
        REPORT.write_text(
            json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", type=Path, default=PDF)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    report = inspect_pdf(args.path.resolve(), write_report=args.write)
    if not args.write:
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
