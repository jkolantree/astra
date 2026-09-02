"""Atlas-local PDF inspection helpers with no core release-spec dependency."""

from __future__ import annotations

import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import matplotlib
import pikepdf
from pypdf import PdfReader

from tools.dark_medium_response_atlas_document_helpers import (
    STRUCTURE_ID_PREFIX,
    attribute_dictionaries,
    name_tree_key,
    structure_elements,
)

ROOT = Path(__file__).resolve().parents[1]


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def dereference(value: Any) -> Any:
    try:
        return value.get_object()
    except (AttributeError, ValueError):
        return value


class HeadingTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._heading_depth = 0
        self._annotation_depth = 0
        self._parts: list[str] = []
        self.headings: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if re.fullmatch(r"h[1-6]", tag):
            if self._heading_depth:
                raise RuntimeError("Nested HTML headings are not supported")
            self._heading_depth = 1
            self._parts = []
        elif self._heading_depth and tag == "annotation":
            self._annotation_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if self._heading_depth and tag == "annotation":
            self._annotation_depth -= 1
        elif re.fullmatch(r"h[1-6]", tag) and self._heading_depth:
            title = re.sub(r"\s+", " ", "".join(self._parts)).strip()
            if not title:
                raise RuntimeError("HTML contains an empty heading")
            self.headings.append(title)
            self._heading_depth = 0
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._heading_depth and not self._annotation_depth:
            self._parts.append(data)


def html_heading_titles(path: Path) -> list[str]:
    parser = HeadingTextParser()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    if not parser.headings:
        raise RuntimeError(f"HTML headings are missing from {path.name}")
    return parser.headings


def pdf_outline_titles(reader: PdfReader) -> list[str]:
    titles: list[str] = []

    def visit(values: list[Any]) -> None:
        for value in values:
            if isinstance(value, list):
                visit(value)
                continue
            title = getattr(value, "title", None)
            if title is not None:
                titles.append(re.sub(r"\s+", " ", str(title)).strip())

    visit(reader.outline)
    return titles


def validate_structure_identifiers(pdf: pikepdf.Pdf) -> dict[str, int]:
    root = pdf.Root.get("/StructTreeRoot")
    if not isinstance(root, pikepdf.Dictionary):
        raise RuntimeError("Tagged PDF structure tree is missing")
    elements = list(structure_elements(root.get("/K", pikepdf.Array())))
    identified = [element for element in elements if "/ID" in element]
    identifiers = [str(element["/ID"]) for element in identified]
    expected = [f"{STRUCTURE_ID_PREFIX}{index:08d}" for index in range(len(identified))]
    if not identifiers or identifiers != expected:
        raise RuntimeError(f"Tagged-PDF structure IDs are not canonical: {identifiers}")
    if len(identifiers) != len(set(identifiers)):
        raise RuntimeError("Tagged-PDF structure IDs are not unique")
    if "/IDTree" not in root:
        raise RuntimeError("Tagged-PDF canonical structure IDs require an IDTree")
    name_tree = pikepdf.NameTree(root["/IDTree"])
    tree_keys = {name_tree_key(key) for key in name_tree}
    if tree_keys != set(identifiers):
        raise RuntimeError("Tagged-PDF IDTree is not closed over canonical structure IDs")
    for identifier, element in zip(identifiers, identified, strict=True):
        if name_tree[identifier].objgen != element.objgen:
            raise RuntimeError(f"Tagged-PDF IDTree target mismatch for {identifier!r}")

    header_references: list[str] = []
    for element in elements:
        if "/A" not in element:
            continue
        for attribute in attribute_dictionaries(element["/A"]):
            if "/Headers" not in attribute:
                continue
            headers = attribute["/Headers"]
            if not isinstance(headers, pikepdf.Array):
                raise RuntimeError("Tagged-PDF table Headers attribute must be an array")
            header_references.extend(str(header) for header in headers)
    if not header_references:
        raise RuntimeError("Tagged-PDF table header references are missing")
    unresolved = sorted(set(header_references) - set(identifiers))
    if unresolved:
        raise RuntimeError(f"Tagged-PDF table header references are unresolved: {unresolved}")
    by_identifier = dict(zip(identifiers, identified, strict=True))
    invalid_targets = sorted(
        identifier
        for identifier in set(header_references)
        if str(by_identifier[identifier].get("/S", "")) != "/TH"
    )
    if invalid_targets:
        raise RuntimeError(
            "Tagged-PDF table header references do not target TH: "
            f"{invalid_targets}"
        )
    return {
        "canonical_structure_id_count": len(identifiers),
        "table_header_reference_count": len(header_references),
    }


def font_record(name: Any, font_reference: Any) -> dict[str, Any]:
    font = dereference(font_reference)
    subtype = str(font.get("/Subtype", ""))
    descendant = font
    if subtype == "/Type0" and "/DescendantFonts" in font:
        descendants = dereference(font["/DescendantFonts"])
        if descendants:
            descendant = dereference(descendants[0])
    descriptor = dereference(descendant.get("/FontDescriptor", {}))
    if subtype == "/Type3":
        char_procedures = dereference(font.get("/CharProcs", {}))
        embedded = bool(char_procedures) and all(
            isinstance(dereference(procedure), pikepdf.Stream)
            for procedure in char_procedures.values()
        )
    else:
        embedded = any(key in descriptor for key in ("/FontFile", "/FontFile2", "/FontFile3"))
    return {
        "resource_name": str(name),
        "base_font": str(
            font.get(
                "/BaseFont",
                descendant.get(
                    "/BaseFont",
                    descriptor.get("/FontName", descriptor.get("/FontFamily", "")),
                ),
            )
        ),
        "subtype": subtype,
        "embedded": embedded,
        "to_unicode": "/ToUnicode" in font,
    }


def verify_bundled_font_sources(
    font_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    runtime = json.loads((ROOT / "RUNTIME.json").read_text(encoding="utf-8"))
    source_specification = runtime["pdf_renderer"]["font_sources"]
    expected_provider = f"matplotlib {matplotlib.__version__}"
    if source_specification["provider"] != expected_provider:
        raise RuntimeError(
            f"PDF font provider drift: expected {source_specification['provider']}, "
            f"observed {expected_provider}"
        )
    font_dir = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
    observed: list[dict[str, Any]] = []
    for specification in source_specification["files"]:
        font_path = font_dir / specification["file"]
        if not font_path.is_file():
            raise RuntimeError(f"Pinned PDF font source is missing: {font_path}")
        identity = {
            "file": specification["file"],
            "bytes": font_path.stat().st_size,
            "sha256": sha256_path(font_path),
        }
        expected = {key: specification[key] for key in identity}
        if identity != expected:
            raise RuntimeError(f"Bundled PDF source-font identity drift: {identity}")
        observed.append(identity)
    base_fonts = " ".join(record["base_font"] for record in font_records)
    if "DejaVu" not in base_fonts or "STIXGeneral" not in base_fonts:
        raise RuntimeError(f"Expected bundled DejaVu and STIX PDF fonts: {font_records}")
    return observed


def validate_pdf_font_records(font_records: list[dict[str, Any]]) -> None:
    if not font_records or any(not record["embedded"] for record in font_records):
        raise RuntimeError(f"Every PDF font must be embedded: {font_records}")
    allowed_font_fragments = ("DejaVu", "STIXGeneral")
    if any(
        not any(fragment in record["base_font"] for fragment in allowed_font_fragments)
        for record in font_records
    ):
        raise RuntimeError(f"Unexpected PDF font: {font_records}")
    if any(record["subtype"] == "/Type0" and not record["to_unicode"] for record in font_records):
        raise RuntimeError(f"Every Type0 PDF font needs ToUnicode: {font_records}")
    if any(record["subtype"] == "/Type3" and not record["to_unicode"] for record in font_records):
        raise RuntimeError(f"Every Type3 PDF font needs ToUnicode: {font_records}")
