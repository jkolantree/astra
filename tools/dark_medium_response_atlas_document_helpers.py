"""Atlas-local HTML and tagged-PDF normalization helpers.

This module is intentionally independent of ``RELEASE_SPEC.json`` and the
core document builder, so the tagged Atlas source archive has a closed
document-production dependency boundary.
"""

from __future__ import annotations

import base64
import html as html_module
import re
from collections.abc import Iterator
from pathlib import Path

import matplotlib
import pikepdf

STRUCTURE_ID_PREFIX = "sppt-struct-"
FORMULA_ALT_PREFIX = "Formula in TeX: "


def embedded_font_css() -> str:
    """Return deterministic data-URI declarations for Matplotlib's bundled fonts."""
    font_dir = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
    declarations = []
    variants = (
        ("DejaVuSerif.ttf", "SPPT DejaVu Serif", "normal", "400"),
        ("DejaVuSerif-Bold.ttf", "SPPT DejaVu Serif", "normal", "700"),
        ("DejaVuSerif-Italic.ttf", "SPPT DejaVu Serif", "italic", "400"),
        ("DejaVuSerif-BoldItalic.ttf", "SPPT DejaVu Serif", "italic", "400"),
        ("DejaVuSans.ttf", "SPPT DejaVu Sans", "normal", "400"),
        ("DejaVuSans-Bold.ttf", "SPPT DejaVu Sans", "normal", "700"),
        ("DejaVuSansMono.ttf", "SPPT DejaVu Sans Mono", "normal", "400"),
        ("STIXGeneral.ttf", "SPPT STIX General", "normal", "400"),
    )
    for filename, family, style, weight in variants:
        encoded = base64.b64encode((font_dir / filename).read_bytes()).decode("ascii")
        declarations.append(
            "@font-face {"
            f"font-family:'{family}';font-style:{style};font-weight:{weight};"
            f"src:url(data:font/ttf;base64,{encoded}) format('truetype');"
            "font-display:block;}"
        )
    return "<style>" + "".join(declarations) + "</style>"


def structure_elements(value: object) -> Iterator[pikepdf.Object]:
    """Yield tagged structure elements in logical document order."""
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


def canonicalize_structure_ids(pdf: pikepdf.Pdf) -> None:
    """Replace Chromium's process-sensitive tagged-PDF IDs without breaking references."""
    root = pdf.Root.get("/StructTreeRoot")
    if not isinstance(root, pikepdf.Dictionary):
        raise RuntimeError("Tagged PDF structure tree is missing")
    elements = list(structure_elements(root.get("/K", pikepdf.Array())))
    identified = [element for element in elements if "/ID" in element]
    original_ids = [str(element["/ID"]) for element in identified]
    if len(original_ids) != len(set(original_ids)):
        raise RuntimeError("Duplicate tagged-PDF structure IDs")
    if not identified:
        if "/IDTree" in root:
            raise RuntimeError("Tagged-PDF IDTree exists without identified structure elements")
        return
    if any(element.objgen == (0, 0) for element in identified):
        raise RuntimeError("Tagged-PDF identified structure elements must be indirect objects")
    if "/IDTree" not in root:
        raise RuntimeError("Tagged-PDF identified structure elements require an IDTree")

    existing_tree = pikepdf.NameTree(root["/IDTree"])
    existing_keys = {name_tree_key(key) for key in existing_tree}
    if existing_keys != set(original_ids):
        raise RuntimeError("Tagged-PDF IDTree is not closed over reachable structure IDs")
    by_original_id = dict(zip(original_ids, identified, strict=True))
    for original_id, element in by_original_id.items():
        if existing_tree[original_id].objgen != element.objgen:
            raise RuntimeError(f"Tagged-PDF IDTree target mismatch for {original_id!r}")

    replacements = {
        original_id: f"{STRUCTURE_ID_PREFIX}{index:08d}"
        for index, original_id in enumerate(original_ids)
    }
    for original_id, element in by_original_id.items():
        element["/ID"] = pikepdf.String(replacements[original_id])

    header_references = 0
    for element in elements:
        if "/A" not in element:
            continue
        for attribute in attribute_dictionaries(element["/A"]):
            if "/Headers" not in attribute:
                continue
            headers = attribute["/Headers"]
            if not isinstance(headers, pikepdf.Array):
                raise RuntimeError("Tagged-PDF table Headers attribute must be an array")
            for index, header in enumerate(headers):
                original_id = str(header)
                if original_id not in replacements:
                    raise RuntimeError(
                        f"Tagged-PDF table header reference is unresolved: {original_id!r}"
                    )
                if str(by_original_id[original_id].get("/S", "")) != "/TH":
                    raise RuntimeError(
                        "Tagged-PDF table header reference does not target TH: "
                        f"{original_id!r}"
                    )
                headers[index] = pikepdf.String(replacements[original_id])
                header_references += 1
    if header_references == 0:
        raise RuntimeError("Tagged-PDF structure IDs are not used by any table Headers attribute")

    canonical_tree = pikepdf.NameTree.new(pdf)
    for original_id, element in by_original_id.items():
        canonical_tree[replacements[original_id]] = element
    root["/IDTree"] = canonical_tree.obj
    canonical_keys = {name_tree_key(key) for key in canonical_tree}
    if canonical_keys != set(replacements.values()):
        raise RuntimeError("Canonical tagged-PDF IDTree construction failed")


def plain_html_text(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", "", value)
    return re.sub(r"\s+", " ", html_module.unescape(without_tags)).strip()


def add_scope_to_header_cells(section: str, scope: str) -> str:
    def replace(match: re.Match[str]) -> str:
        attributes = match.group("attributes")
        if re.search(r"\bscope\s*=", attributes, flags=re.IGNORECASE):
            raise RuntimeError("Generated table header already has an unexpected scope")
        return f'<th{attributes} scope="{scope}">'

    return re.sub(
        r"<th(?P<attributes>[^>]*)>",
        replace,
        section,
        flags=re.IGNORECASE,
    )


def promote_row_header(row: str, column: int) -> str:
    cells = list(
        re.finditer(
            r"<td(?P<attributes>[^>]*)>(?P<content>.*?)</td>",
            row,
            flags=re.IGNORECASE | re.DOTALL,
        )
    )
    if column >= len(cells):
        raise RuntimeError(
            f"Generated table row has {len(cells)} cells; cannot promote column {column + 1}"
        )
    cell = cells[column]
    attributes = cell.group("attributes")
    replacement = f'<th{attributes} scope="row">{cell.group("content")}</th>'
    return row[: cell.start()] + replacement + row[cell.end() :]


def postprocess_tables(html: str, *, expected_count: int) -> str:
    """Add explicit table relationships that Pandoc Markdown cannot encode."""
    table_pattern = re.compile(r"<table(?P<attributes>[^>]*)>.*?</table>", re.DOTALL)
    tables = list(table_pattern.finditer(html))
    if len(tables) != expected_count:
        raise RuntimeError(f"Expected {expected_count} generated tables, observed {len(tables)}")

    def process_table(match: re.Match[str]) -> str:
        table = match.group(0)
        captions = re.findall(r"<caption(?:\s[^>]*)?>(.*?)</caption>", table, re.DOTALL)
        if len(captions) != 1 or not plain_html_text(captions[0]):
            raise RuntimeError("Every generated table needs one nonempty source caption")

        thead_match = re.search(r"<thead>(.*?)</thead>", table, re.DOTALL)
        tbody_match = re.search(r"<tbody>(.*?)</tbody>", table, re.DOTALL)
        if thead_match is None or tbody_match is None:
            raise RuntimeError("Generated table is missing thead or tbody")
        header_cells = re.findall(r"<th[^>]*>(.*?)</th>", thead_match.group(1), re.DOTALL)
        labels = [plain_html_text(cell) for cell in header_cells]
        if not labels:
            raise RuntimeError("Generated table has no column headers")
        row_header_column = 1 if labels[:2] == ["Rank", "Graph"] else 0

        processed_head = add_scope_to_header_cells(thead_match.group(1), "col")
        table = table[: thead_match.start(1)] + processed_head + table[thead_match.end(1) :]
        tbody_match = re.search(r"<tbody>(.*?)</tbody>", table, re.DOTALL)
        if tbody_match is None:
            raise RuntimeError("Generated table body disappeared during postprocessing")
        body = re.sub(
            r"<tr>.*?</tr>",
            lambda row: promote_row_header(row.group(0), row_header_column),
            tbody_match.group(1),
            flags=re.DOTALL,
        )
        if "<tr" in tbody_match.group(1) and 'scope="row"' not in body:
            raise RuntimeError("Generated table row headers were not promoted")
        return table[: tbody_match.start(1)] + body + table[tbody_match.end(1) :]

    return table_pattern.sub(process_table, html)


def normalize_structure_semantics(
    pdf: pikepdf.Pdf, *, expected_formula_count: int
) -> dict[str, int]:
    """Normalize Chromium's formula sentinels and nested figure containers."""
    root = pdf.Root.get("/StructTreeRoot")
    if not isinstance(root, pikepdf.Dictionary):
        raise RuntimeError("Tagged PDF structure tree is missing")
    elements = list(structure_elements(root.get("/K", pikepdf.Array())))
    formula_count = 0
    figure_container_count = 0
    root_container_count = 0
    for element in elements:
        if str(element.get("/S", "")) != "/NonStruct" or "/Pg" in element:
            continue
        parent = element.get("/P")
        descendants = list(structure_elements(element.get("/K", pikepdf.Array())))
        if (
            isinstance(parent, pikepdf.Dictionary)
            and str(parent.get("/S", "")) == "/Document"
            and any(str(child.get("/S", "")) != "/NonStruct" for child in descendants)
        ):
            element["/S"] = pikepdf.Name("/Part")
            root_container_count += 1
    for element in elements:
        if str(element.get("/S", "")) != "/Figure":
            continue
        alt = str(element.get("/Alt", "")).strip()
        if alt.startswith(FORMULA_ALT_PREFIX):
            tex = alt.removeprefix(FORMULA_ALT_PREFIX).strip()
            if not tex:
                raise RuntimeError("Tagged formula sentinel has empty TeX alternative text")
            element["/S"] = pikepdf.Name("/Formula")
            element["/Alt"] = pikepdf.String(f"Formula in TeX: {tex}")
            element["/ActualText"] = pikepdf.String(tex)
            formula_count += 1
            continue
        if alt:
            continue
        descendants = list(structure_elements(element.get("/K", pikepdf.Array())))
        labeled_figures = [
            descendant
            for descendant in descendants
            if str(descendant.get("/S", "")) == "/Figure"
            and str(descendant.get("/Alt", "")).strip()
        ]
        if "/Pg" not in element and labeled_figures:
            element["/S"] = pikepdf.Name("/Div")
            figure_container_count += 1
            continue
        raise RuntimeError("Unlabeled tagged Figure is not a verified outer container")
    if formula_count != expected_formula_count:
        raise RuntimeError(
            "Tagged formula count does not match HTML MathML count: "
            f"{formula_count} != {expected_formula_count}"
        )
    return {
        "formula_count": formula_count,
        "retagged_figure_container_count": figure_container_count,
        "retagged_root_container_count": root_container_count,
    }


def outline_elements(pdf: pikepdf.Pdf) -> Iterator[pikepdf.Object]:
    outlines = pdf.Root.get("/Outlines")
    if not isinstance(outlines, pikepdf.Dictionary):
        return

    def siblings(value: object) -> Iterator[pikepdf.Object]:
        current = value
        while isinstance(current, pikepdf.Dictionary):
            yield current
            if "/First" in current:
                yield from siblings(current["/First"])
            current = current.get("/Next")

    if "/First" in outlines:
        yield from siblings(outlines["/First"])


def normalize_outline_titles(pdf: pikepdf.Pdf, expected_titles: list[str]) -> None:
    items = list(outline_elements(pdf))
    if len(items) != len(expected_titles):
        raise RuntimeError(
            "PDF outline count does not match HTML headings: "
            f"{len(items)} != {len(expected_titles)}"
        )
    for item, title in zip(items, expected_titles, strict=True):
        normalized = re.sub(r"\s+", " ", title).strip()
        if not normalized:
            raise RuntimeError("HTML heading produced an empty PDF outline title")
        item["/Title"] = pikepdf.String(normalized)
