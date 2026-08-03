"""Inspect released PDFs for syntax, metadata, structure, fonts, links, and text."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Iterator
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import matplotlib
import pikepdf
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "manuscript"
RELEASE_SPEC = json.loads((ROOT / "RELEASE_SPEC.json").read_text(encoding="utf-8"))
VERSION = str(RELEASE_SPEC["version"])
BUILD_EPOCH = str(RELEASE_SPEC["build_epoch"])
AUTHOR = str(RELEASE_SPEC["author"])
if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", BUILD_EPOCH):
    raise RuntimeError(f"Noncanonical release build epoch: {BUILD_EPOCH!r}")
FIXED_DATE = "D:" + re.sub(r"[-:T]", "", BUILD_EPOCH)
PDF_SUBJECT = f"SPPT/ASTRA v{VERSION}; not peer reviewed"
PDF_PRODUCER = f"SPPT-ASTRA reproducibility build v{VERSION}; pikepdf 10.11.0"
STRUCTURE_ID_PREFIX = "sppt-struct-"
FORMULA_ALT_PREFIX = "Formula in TeX: "
COMPATIBILITY_LIGATURES = frozenset("\ufb00\ufb01\ufb02\ufb03\ufb04\ufb05\ufb06")
PDFS = (
    MANUSCRIPT / f"SPPT_ASTRA_preprint_v{VERSION}.pdf",
    MANUSCRIPT / f"SPPT_ASTRA_technical_supplement_v{VERSION}.pdf",
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


def structure_elements(value: object) -> Iterator[pikepdf.Object]:
    if isinstance(value, pikepdf.Array):
        for child in value:
            yield from structure_elements(child)
        return
    if not isinstance(value, pikepdf.Dictionary):
        return
    if str(value.get("/Type", "")) != "/StructElem" and "/S" not in value:
        return
    yield value
    if "/K" in value:
        yield from structure_elements(value["/K"])


def attribute_dictionaries(value: object) -> Iterator[pikepdf.Object]:
    if isinstance(value, pikepdf.Array):
        for child in value:
            yield from attribute_dictionaries(child)
    elif isinstance(value, pikepdf.Dictionary):
        yield value


def name_tree_key(value: bytes | str) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="strict")
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


def validate_extracted_text(text: str, *, filename: str) -> None:
    ligatures = sorted({character for character in text if character in COMPATIBILITY_LIGATURES})
    if ligatures:
        codepoints = [f"U+{ord(character):04X}" for character in ligatures]
        raise RuntimeError(
            f"Compatibility ligatures remain in extracted text from {filename}: {codepoints}"
        )
    if "identifiability" not in text.casefold():
        raise RuntimeError(f"Exact-search sentinel 'identifiability' is missing from {filename}")


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
            f"Tagged-PDF table header references do not target TH: {invalid_targets}"
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


def structure_ancestor_tags(element: pikepdf.Object) -> list[str]:
    tags: list[str] = []
    parent = element.get("/P")
    while isinstance(parent, pikepdf.Dictionary) and "/S" in parent:
        tags.append(str(parent.get("/S", "")))
        parent = parent.get("/P")
    return tags


def inspect(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    reader = PdfReader(path)
    if reader.is_encrypted:
        raise RuntimeError(f"{path.name} must not be encrypted")
    page_text = [(page.extract_text() or "").strip() for page in reader.pages]
    if not page_text or any(not text for text in page_text):
        raise RuntimeError(f"Every page of {path.name} must have extractable text")
    for page_number, text in enumerate(page_text, start=1):
        if text.splitlines()[0].strip() != str(page_number):
            raise RuntimeError(
                f"Page {page_number} of {path.name} is missing its visible page number"
            )
    normalized = re.sub(r"\s+", " ", "\n".join(page_text)).strip()
    validate_extracted_text(normalized, filename=path.name)
    if PRIVATE_PATTERN.search(normalized):
        raise RuntimeError(f"Private or machine-local text found in {path.name}")
    html_path = path.with_suffix(".html")
    if not html_path.is_file():
        raise RuntimeError(f"Matching HTML reading edition is missing for {path.name}")
    expected_outline_titles = html_heading_titles(html_path)
    outline_titles = pdf_outline_titles(reader)
    if outline_titles != expected_outline_titles:
        raise RuntimeError(
            f"PDF outline titles do not match HTML headings in {path.name}: "
            f"{outline_titles!r} != {expected_outline_titles!r}"
        )
    expected_formula_count = len(
        re.findall(r"<math(?:\s|>)", html_path.read_text(encoding="utf-8"))
    )
    if expected_formula_count < 1:
        raise RuntimeError(f"MathML formulas are missing from {html_path.name}")

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
        structure_identity = validate_structure_identifiers(pdf)

        docinfo = {str(key): str(value) for key, value in pdf.docinfo.items()}
        expected_metadata = {
            "/Author": AUTHOR,
            "/Subject": PDF_SUBJECT,
            "/Producer": PDF_PRODUCER,
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
        validate_pdf_font_records(font_records)
        source_font_identities = verify_bundled_font_sources(font_records)

        structure_root = root["/StructTreeRoot"]
        elements = list(structure_elements(structure_root.get("/K", pikepdf.Array())))
        figures = [element for element in elements if str(element.get("/S", "")) == "/Figure"]
        formulas = [element for element in elements if str(element.get("/S", "")) == "/Formula"]
        tables = [element for element in elements if str(element.get("/S", "")) == "/Table"]
        captions = [element for element in elements if str(element.get("/S", "")) == "/Caption"]
        header_scopes: list[str] = []
        for element in elements:
            if str(element.get("/S", "")) != "/TH":
                continue
            scopes = [
                str(attribute["/Scope"])
                for attribute in attribute_dictionaries(element.get("/A", pikepdf.Array()))
                if "/Scope" in attribute
            ]
            if len(scopes) != 1 or scopes[0] not in {"/Column", "/Row"}:
                raise RuntimeError(
                    f"Tagged table header has invalid Scope in {path.name}: {scopes}"
                )
            header_scopes.extend(scopes)
        table_tags = len(tables)
        table_caption_tags = len(captions)
        column_header_tags = header_scopes.count("/Column")
        row_header_tags = header_scopes.count("/Row")
        if (
            table_tags < 1
            or table_caption_tags != table_tags
            or column_header_tags < table_tags
            or row_header_tags < table_tags
        ):
            raise RuntimeError(
                f"Tagged table semantics are incomplete in {path.name}: "
                f"Table={table_tags}, Caption={table_caption_tags}, "
                f"ColumnTH={column_header_tags}, RowTH={row_header_tags}"
            )
        figure_tags = len(figures)
        figure_leaf_tags = sum("/Pg" in figure for figure in figures)
        figure_alt_tags = sum(bool(str(figure.get("/Alt", "")).strip()) for figure in figures)
        if figure_tags < 1 or figure_alt_tags != figure_tags:
            raise RuntimeError(
                f"Every tagged figure needs alt text in {path.name}: "
                f"{figure_alt_tags}/{figure_tags}"
            )
        if figure_leaf_tags != figure_tags:
            raise RuntimeError(
                f"Unflattened outer Figure tags remain in {path.name}: "
                f"{figure_leaf_tags}/{figure_tags} are page-bound"
            )
        formula_alt_tags = 0
        formula_actual_text_tags = 0
        for formula in formulas:
            alt = str(formula.get("/Alt", "")).strip()
            actual_text = str(formula.get("/ActualText", "")).strip()
            if alt.startswith(FORMULA_ALT_PREFIX) and alt.removeprefix(FORMULA_ALT_PREFIX).strip():
                formula_alt_tags += 1
            if actual_text:
                formula_actual_text_tags += 1
            if "/NonStruct" in structure_ancestor_tags(formula):
                raise RuntimeError(f"Formula remains nested under NonStruct in {path.name}")
        formula_tags = len(formulas)
        if (
            formula_tags != expected_formula_count
            or formula_alt_tags != formula_tags
            or formula_actual_text_tags != formula_tags
        ):
            raise RuntimeError(
                f"Every HTML MathML formula needs PDF Formula semantics in {path.name}: "
                f"HTML={expected_formula_count}, Formula={formula_tags}, "
                f"Alt={formula_alt_tags}, ActualText={formula_actual_text_tags}"
            )

        with pdf.open_metadata(set_pikepdf_as_editor=False) as xmp:
            xmp_summary = {
                "title": str(xmp.get("dc:title", "")),
                "creator": list(xmp.get("dc:creator", [])),
                "language": list(xmp.get("dc:language", [])),
                "created": str(xmp.get("xmp:CreateDate", "")),
                "modified": str(xmp.get("xmp:ModifyDate", "")),
            }
        if (
            xmp_summary["creator"] != [AUTHOR]
            or xmp_summary["language"] != ["en-US"]
            or xmp_summary["created"] != BUILD_EPOCH
            or xmp_summary["modified"] != BUILD_EPOCH
        ):
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
        "formula_tags": formula_tags,
        "formula_alt_tags": formula_alt_tags,
        "formula_actual_text_tags": formula_actual_text_tags,
        "table_tags": table_tags,
        "table_caption_tags": table_caption_tags,
        "column_header_tags": column_header_tags,
        "row_header_tags": row_header_tags,
        "outline_present": True,
        "outline_title_count": len(outline_titles),
        "outline_titles_match_html": True,
        "compatibility_ligature_count": 0,
        "exact_search_sentinels": ["identifiability"],
        "language": "en-US",
        "display_doc_title": True,
        "fonts": font_records,
        "source_font_identities": source_font_identities,
        "external_link_count": len(links),
        "external_links": sorted(set(links)),
        "metadata": docinfo,
        "xmp": xmp_summary,
        "syntax_warnings": [],
        **structure_identity,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()
    paths = tuple(args.paths) or PDFS
    report = {
        "schema": "https://jkolantree.github.io/astra/schemas/pdf-inspection-v1.schema.json",
        "records": [inspect(path.resolve()) for path in paths],
    }
    serialized = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.write:
        (MANUSCRIPT / "pdf_inspection.json").write_text(serialized, encoding="utf-8", newline="\n")
    else:
        print(serialized, end="")


if __name__ == "__main__":
    main()
