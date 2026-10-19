"""Build versioned integrated-core alpha candidates; never admit a runtime or historical release."""

from __future__ import annotations

import argparse
import base64
import hashlib
import html as html_module
import importlib.metadata
import importlib.util
import json
import os
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from html.parser import HTMLParser
from pathlib import Path

import matplotlib
import pikepdf
import pypandoc
from playwright.sync_api import sync_playwright
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[3]
MANUSCRIPT = ROOT / "manuscript" / "integrated-core-v1.1.0-alpha.1"
PLAN = json.loads((MANUSCRIPT / "document-plan.json").read_text(encoding="utf-8"))
OUTPUT_ROOT = ROOT / "resources/integrated-core/v1.1.0-alpha.1/reading"
TEMP_ROOT = ROOT / "tmp" / "integrated-document-build"
BUILD_EPOCH = PLAN["draft_reproducibility_epoch"]
AUTHOR = PLAN["author"]
FIXED_PDF_DATE = "D:" + re.sub(r"[-:T]", "", BUILD_EPOCH)
PDF_SUBJECT = "SPPT/ASTRA Integrated Core 1.1.0-alpha.1; not peer reviewed; runtime not admitted"
PDF_PRODUCER = "SPPT/ASTRA Integrated Core 1.1.0-alpha.1; pikepdf " + importlib.metadata.version("pikepdf")
STRUCTURE_ID_PREFIX = "astra-draft-struct-"
FORMULA_ALT_PREFIX = "Formula in TeX: "
TRANSPARENT_PIXEL = "data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs="
# Scoped to the new draft editions; historical style bytes remain unchanged.
DRAFT_REFLOW_CSS = """<style id="integrated-draft-reflow">
@media screen {
  main { overflow-wrap: anywhere; }
}
</style>"""
BROWSER: Path | None = None
DOCUMENTS = tuple(
    (MANUSCRIPT / doc["source"], OUTPUT_ROOT / (doc["stem"] + ".html"),
     OUTPUT_ROOT / (doc["stem"] + ".pdf"), doc["title"])
    for doc in PLAN["documents"]
)


def validate_plan(plan: dict) -> None:
    if (plan.get("kind") != "INTEGRATED_CORE_ALPHA_DOCUMENT_PLAN"
            or plan.get("status") != "CANDIDATE_NOT_ADMITTED"
            or plan.get("release_version") != "1.1.0-alpha.1" or plan.get("release_tag") != "astra-integrated-core-v1.1.0-alpha.1"
            or plan.get("epoch_is_release_date") is not False
            or plan.get("output_directory") != "resources/integrated-core/v1.1.0-alpha.1/reading"
            or plan.get("language") != "en-US"):
        raise RuntimeError("Only the exact versioned, unadmitted integrated-core alpha plan is supported")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", plan["draft_reproducibility_epoch"]):
        raise RuntimeError("Noncanonical draft epoch")
    docs = plan.get("documents")
    if docs != [{'source': 'manuscript.md', 'stem': 'astra-integrated-core-v1.1.0-alpha.1-manuscript', 'title': 'SPPT/ASTRA Integrated Core 1.1.0-alpha.1: Typed Composition and Bounded Research Checks'}, {'source': 'supplement.md', 'stem': 'astra-integrated-core-v1.1.0-alpha.1-supplement', 'title': 'SPPT/ASTRA Integrated Core 1.1.0-alpha.1: Technical Supplement and Evidence Boundaries'}]:
        raise RuntimeError("Exact source, title and output association required")
    if not isinstance(docs, list) or len(docs) != 2:
        raise RuntimeError("Exactly two draft sources are required")
    if {d.get("source") for d in docs} != {"manuscript.md", "supplement.md"}:
        raise RuntimeError("Unexpected draft source paths")
    stems = [d.get("stem", "") for d in docs]
    if set(stems) != {"astra-integrated-core-v1.1.0-alpha.1-manuscript", "astra-integrated-core-v1.1.0-alpha.1-supplement"} or len(stems) != 2:
        raise RuntimeError("Unsafe or duplicate draft output stems")
    if any(not isinstance(d.get("title"), str) or not d["title"].strip() for d in docs):
        raise RuntimeError("Draft titles must be explicit")


def ast_nodes(value: object) -> Iterator[dict]:
    if isinstance(value, dict):
        if "t" in value:
            yield value
        for child in value.values():
            yield from ast_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from ast_nodes(child)


def unique_pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise RuntimeError("Duplicate figure declaration key")
        result[key] = value
    return result


def validate_figure_declaration() -> dict:
    inputs = json.loads((MANUSCRIPT / "figure-inputs.json").read_text(), object_pairs_hook=unique_pairs)
    if inputs.get("status") != "DECLARED_FIGURE_INPUTS_NOT_ADMISSION" or len(inputs.get("figures", {})) != 13:
        raise RuntimeError("Exact thirteen-figure declaration required")
    for url, record in inputs["figures"].items():
        if (set(record) != {"source_path", "sha256", "title", "scope"}
                or not all(isinstance(record[k], str) and record[k] for k in record)
                or re.fullmatch(r"[0-9a-f]{64}", record["sha256"]) is None):
            raise RuntimeError("Malformed figure declaration entry")
        relative = Path(record["source_path"])
        if (not re.fullmatch(r"resources/integrated-core/v1.1.0-alpha.1/generated/[0-9]{2}_[a-z0-9_]+\.svg", relative.as_posix())
                or url != "../../" + relative.as_posix()):
            raise RuntimeError("Unsafe declared figure path")
        path = ROOT / relative
        if any(p.is_symlink() for p in [path, *path.parents]) or not path.is_file() or path.stat().st_nlink != 1:
            raise RuntimeError("Linked or missing declared figure")
        if sha256(path) != record["sha256"]:
            raise RuntimeError("Declared figure bytes mismatch")
        text = path.read_text()
        if "<!DOCTYPE" in text or "<!ENTITY" in text:
            raise RuntimeError("Active declared SVG content")
        for node in ET.fromstring(text).iter():
            if node.tag.split("}")[-1] in {"script", "foreignObject", "iframe", "image"}:
                raise RuntimeError("Active declared SVG content")
            for key, value in node.attrib.items():
                if key.split("}")[-1].lower().startswith("on") or (key.split("}")[-1] == "href" and not value.startswith("#")):
                    raise RuntimeError("Active declared SVG content")
    return inputs


def declared_figure(source: Path, url: str) -> dict:
    if url == "../../docs/integrated-core/flow.svg":
        return {"source_path": "docs/integrated-core/flow.svg", "sha256": sha256(ROOT / "docs/integrated-core/flow.svg")}
    inputs = validate_figure_declaration()
    if url not in inputs["figures"]:
        raise RuntimeError("Only local declared figures are supported")
    record = inputs["figures"][url]
    if (source.parent / url).resolve() != (ROOT / record["source_path"]).resolve():
        raise RuntimeError("Declared figure source location mismatch")
    return record


def source_contract(source: Path, title: str) -> dict:
    ast = json.loads(pypandoc.convert_file(
        str(source), "json", format="markdown+tex_math_single_backslash"))
    meta_title = ast.get("meta", {}).get("title", {})
    actual = pypandoc.convert_text(json.dumps({**ast, "blocks": [
        {"t": "Plain", "c": meta_title.get("c", [])}]}), "plain", format="json", extra_args=["--wrap=none"]).strip()
    if actual != title:
        raise RuntimeError("Draft title disagrees with source frontmatter")
    nodes = list(ast_nodes(ast))
    for node in nodes:
        if node["t"] in {"RawBlock", "RawInline"}:
            raise RuntimeError("Raw markup is not admitted in draft sources")
        if node["t"] == "Image":
            declared_figure(source, node["c"][-1][0])
        if node["t"] == "Link" and not node["c"][-1][0].startswith(("https://", "#")):
            raise RuntimeError("Draft links must be HTTPS or internal fragments")
    return {"tables": sum(n["t"] == "Table" for n in nodes),
            "figures": sum(n["t"] == "Image" for n in nodes),
            "formulas": sum(n["t"] == "Math" for n in nodes)}


def validate_source_snapshot() -> dict:
    snapshot = json.loads((MANUSCRIPT / "source-snapshot.json").read_text())
    if snapshot.get("status") != "DRAFT_SOURCE_SNAPSHOT_NOT_ADMISSION":
        raise RuntimeError("Unexpected draft source snapshot status")
    expected = json.loads((MANUSCRIPT / "snapshot-roster.json").read_text())
    if not snapshot.get("files") or sorted(r["path"] for r in snapshot["files"]) != expected or len({r["path"] for r in snapshot["files"]}) != len(expected):
        raise RuntimeError("Exact nonempty versioned source snapshot required")
    for record in snapshot["files"]:
        relative = Path(record["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise RuntimeError("Unsafe source snapshot path")
        source = ROOT / relative
        if source.is_symlink() or source.resolve() != ROOT.resolve() / relative:
            raise RuntimeError("Draft input path cannot use a symlink")
        if sha256(source) != record["sha256"]:
            raise RuntimeError("Draft source snapshot mismatch: " + record["path"])
    return snapshot


class DraftHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.fragments: list[str] = []
        self.tables = self.figures = self.formulas = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs = dict(attrs)
        if tag in {"script", "iframe", "object", "embed", "base"} or any(k.startswith("on") for k in attrs):
            raise RuntimeError("Active content is not allowed in a draft edition")
        if "id" in attrs:
            self.ids.append(str(attrs["id"]))
        href = attrs.get("href") or ""
        if href.startswith("#"):
            self.fragments.append(href[1:])
        elif href and not href.startswith("https://"):
            raise RuntimeError("Unsafe or machine-local HTML link")
        if tag == "link":
            raise RuntimeError("Stylesheets must be embedded")
        if tag == "img":
            self.figures += 1
            if not (attrs.get("src") or "").startswith("data:image/") or not attrs.get("alt"):
                raise RuntimeError("Figures must be embedded and have alternative text")
        self.tables += tag == "table"
        self.formulas += tag == "math"


def validate_static_html(html: str, expected: dict) -> dict:
    parser = DraftHTML()
    parser.feed(html)
    if len(parser.ids) != len(set(parser.ids)) or set(parser.fragments) - set(parser.ids):
        raise RuntimeError("Duplicate IDs or unresolved internal fragments")
    if (parser.tables, parser.figures, parser.formulas) != (
            expected["tables"], expected["figures"], expected["formulas"]):
        raise RuntimeError("HTML table/figure/formula counts disagree with the source AST")
    if historical_inspector().PRIVATE_PATTERN.search(html) or re.search(r"/workspace/|file://", html):
        raise RuntimeError("Machine-local path in HTML")
    if re.search(r"(?:url\(\s*['\"]?https?://|@import)", html, re.I):
        raise RuntimeError("Network stylesheet resources are prohibited")
    return {"tables": parser.tables, "figures": parser.figures, "formulas": parser.formulas,
            "internal_fragment_count": len(parser.fragments), "status": "PASS"}


def launch_browser(playwright):
    if BROWSER is None or not BROWSER.is_file():
        raise RuntimeError("An explicit existing browser is required for draft rendering")
    return playwright.chromium.launch(executable_path=str(BROWSER), headless=True,
                                     args=["--disable-gpu", "--disable-background-networking"])


def offline_page(browser):
    page = browser.new_page()
    page.route("**/*", lambda route: route.continue_() if route.request.url.startswith(
        ("file:", "data:", "about:")) else route.abort())
    return page


def is_link_or_junction(path: Path) -> bool:
    junction_check = getattr(path, "is_junction", None)
    return path.is_symlink() or bool(junction_check and junction_check())


def ensure_safe_directory(path: Path) -> None:
    try:
        relative = path.relative_to(ROOT)
    except ValueError as exc:
        raise RuntimeError(f"Output path is outside the repository: {path}") from exc
    expected = ROOT.resolve().joinpath(*relative.parts)
    current = ROOT
    for part in relative.parts:
        current /= part
        if is_link_or_junction(current):
            raise RuntimeError(f"Unsafe symbolic link or junction in output path: {current}")
        if current != path and current.exists() and not current.is_dir():
            raise RuntimeError(f"Non-directory component in output path: {current}")
    if path.resolve() != expected:
        raise RuntimeError(f"Output path resolves outside its expected location: {path}")
    if path.exists() and not path.is_dir():
        raise RuntimeError(f"Expected output directory but found a non-directory: {path}")
    path.mkdir(parents=True, exist_ok=True)
    if is_link_or_junction(path) or path.resolve() != expected:
        raise RuntimeError(f"Unsafe output directory after creation: {path}")


def ensure_safe_output(path: Path) -> None:
    if path.parent != OUTPUT_ROOT or path.name not in {'STIX-FONTS.txt', 'astra-integrated-core-v1.1.0-alpha.1-supplement.pdf', 'astra-integrated-core-v1.1.0-alpha.1-supplement.html', 'astra-integrated-core-v1.1.0-alpha.1-manuscript.html', 'DEJAVU-FONTS.txt', 'pdf_inspection.json', 'astra-integrated-core-v1.1.0-alpha.1-manuscript.pdf', 'document_identity.json'}:
        raise RuntimeError("Output must use the dedicated versioned path and exact filename")
    ensure_safe_directory(path.parent)
    if is_link_or_junction(path) or (path.exists() and not path.is_file()):
        raise RuntimeError("Unsafe draft output file")
    if path.exists() and path.stat().st_nlink != 1:
        raise RuntimeError("Hard-linked draft output file is unsafe")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def embedded_font_css() -> str:
    """Return deterministic data-URI declarations for Matplotlib's bundled fonts."""
    font_dir = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
    declarations = []
    variants = (
        ("DejaVuSerif.ttf", "SPPT DejaVu Serif", "normal", "400"),
        ("DejaVuSerif-Bold.ttf", "SPPT DejaVu Serif", "normal", "700"),
        ("DejaVuSerif-Italic.ttf", "SPPT DejaVu Serif", "italic", "400"),
        ("DejaVuSerif-BoldItalic.ttf", "SPPT DejaVu Serif", "italic", "700"),
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
                        f"Tagged-PDF table header reference does not target TH: {original_id!r}"
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


def css_rgb(value: str) -> tuple[int, int, int]:
    match = re.fullmatch(
        r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*(?:1(?:\.0*)?|0?\.\d+)\s*)?\)",
        value,
    )
    if match is None:
        raise RuntimeError(f"Unsupported computed CSS color: {value!r}")
    channels = tuple(int(channel) for channel in match.groups())
    if any(channel > 255 for channel in channels):
        raise RuntimeError(f"Computed CSS color is out of range: {value!r}")
    return channels


def relative_luminance(color: tuple[int, int, int]) -> float:
    def linearize(channel: int) -> float:
        normalized = channel / 255
        if normalized <= 0.04045:
            return normalized / 12.92
        return ((normalized + 0.055) / 1.055) ** 2.4

    red, green, blue = (linearize(channel) for channel in color)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(first: str, second: str) -> float:
    luminances = sorted((relative_luminance(css_rgb(first)), relative_luminance(css_rgb(second))))
    return (luminances[1] + 0.05) / (luminances[0] + 0.05)


def validate_html_accessibility(path: Path) -> dict[str, float | int | None]:
    """Fail closed on narrow reflow and the audited computed-color boundaries."""
    minimum_focus_contrast = float("inf")
    minimum_token_contrast = float("inf")
    scroll_widths: dict[int, int] = {}
    with sync_playwright() as playwright:
        browser = launch_browser(playwright)
        try:
            page = offline_page(browser)
            for width in (320, 400):
                page.set_viewport_size({"width": width, "height": 900})
                page.goto(path.resolve().as_uri(), wait_until="networkidle")
                dimensions = page.evaluate(
                    """
                    () => ({
                      viewportWidth: window.innerWidth,
                      rootClientWidth: document.documentElement.clientWidth,
                      rootScrollWidth: document.documentElement.scrollWidth,
                      bodyScrollWidth: document.body.scrollWidth,
                    })
                    """
                )
                observed_width = max(
                    int(dimensions["rootScrollWidth"]),
                    int(dimensions["bodyScrollWidth"]),
                )
                client_width = int(dimensions["rootClientWidth"])
                viewport_width = int(dimensions["viewportWidth"])
                scroll_widths[width] = observed_width
                if viewport_width != width or observed_width > client_width:
                    raise RuntimeError(
                        f"Narrow-screen reflow failed for {path.name} at {width}px: "
                        f"viewport={viewport_width}, client={client_width}, "
                        f"scroll={observed_width}"
                    )

            page.set_viewport_size({"width": 400, "height": 900})
            page.goto(path.resolve().as_uri(), wait_until="networkidle")
            page.keyboard.press("Tab")
            colors = page.evaluate(
                """
                () => {
                  const rgba = (value) => {
                    const match = value.match(/^rgba?\\(([^)]+)\\)$/);
                    if (!match) throw new Error(`Unsupported CSS color: ${value}`);
                    const parts = match[1].split(",").map((part) => Number(part.trim()));
                    return { value, alpha: parts.length === 4 ? parts[3] : 1 };
                  };
                  const opaqueBackground = (element) => {
                    for (let current = element; current; current = current.parentElement) {
                      const background = getComputedStyle(current).backgroundColor;
                      if (rgba(background).alpha === 1) return background;
                    }
                    return "rgb(255, 255, 255)";
                  };
                  const focused = document.activeElement;
                  if (!(focused instanceof HTMLElement) || focused === document.body) {
                    throw new Error("Keyboard Tab did not reach a focusable element");
                  }
                  const focusStyle = getComputedStyle(focused);
                  const tokens = [...document.querySelectorAll("code span.at")].map((token) => ({
                    foreground: getComputedStyle(token).color,
                    background: opaqueBackground(token),
                  }));
                  return {
                    focus: {
                      outline: focusStyle.outlineColor,
                      outlineStyle: focusStyle.outlineStyle,
                      outlineWidth: Number.parseFloat(focusStyle.outlineWidth),
                      adjacentBackground: opaqueBackground(focused),
                      pageBackground: getComputedStyle(document.documentElement).backgroundColor,
                    },
                    tokens,
                  };
                }
                """
            )
        finally:
            browser.close()

    focus = colors["focus"]
    if focus["outlineStyle"] in {"none", "hidden"} or float(focus["outlineWidth"]) < 2:
        raise RuntimeError(f"Keyboard focus indicator is not visibly outlined in {path.name}")
    minimum_focus_contrast = min(
        contrast_ratio(str(focus["outline"]), str(focus["adjacentBackground"])),
        contrast_ratio(str(focus["outline"]), str(focus["pageBackground"])),
    )
    if minimum_focus_contrast < 3:
        raise RuntimeError(
            f"Keyboard focus contrast is below 3:1 in {path.name}: {minimum_focus_contrast:.3f}:1"
        )

    tokens = colors["tokens"]
    if tokens:
        minimum_token_contrast = min(
            contrast_ratio(str(token["foreground"]), str(token["background"])) for token in tokens
        )
        if minimum_token_contrast < 4.5:
            raise RuntimeError(
                f"Command syntax contrast is below 4.5:1 in {path.name}: "
                f"{minimum_token_contrast:.3f}:1"
            )
    return {
        "viewport_320_scroll_width": scroll_widths[320],
        "viewport_400_scroll_width": scroll_widths[400],
        "minimum_focus_contrast": minimum_focus_contrast,
        "minimum_command_token_contrast": (minimum_token_contrast if tokens else None),
    }


def build_html(source: Path, output: Path, title: str) -> dict:
    expected = source_contract(source, title)
    resource_path = os.pathsep.join((str(MANUSCRIPT), str(ROOT), str(ROOT / "figures")))
    numbering_arguments = [] if source.name == "manuscript.md" else ["--number-sections"]
    with tempfile.TemporaryDirectory(prefix="sppt-astra-html-") as temp_dir:
        temporary_output = Path(temp_dir) / output.name
        pypandoc.convert_file(
            str(source),
            "html5",
            format="markdown+tex_math_single_backslash",
            outputfile=str(temporary_output),
            extra_args=[
                "--standalone",
                "--toc",
                "--toc-depth=3",
                *numbering_arguments,
                "--mathml",
                "--embed-resources",
                f"--resource-path={resource_path}",
                f"--css={ROOT / 'manuscript' / 'style.css'}",
                f"--metadata=pagetitle:{title}",
                "--metadata=lang:en-US",
            ],
        )
        html = temporary_output.read_text(encoding="utf-8")
        html = html.replace("</head>", embedded_font_css() + DRAFT_REFLOW_CSS + "</head>", 1)
        html = html.replace(
            "<body>",
            '<body>\n<a class="skip-link" href="#main-content">Skip to main content</a>',
            1,
        )
        navigation_end = html.find("</nav>")
        if navigation_end < 0:
            raise RuntimeError(
                f"Expected a table-of-contents navigation landmark in {output.name}."
            )
        navigation_end += len("</nav>")
        html = (
            html[:navigation_end]
            + '\n<main id="main-content" tabindex="-1">'
            + html[navigation_end:]
        )
        html = html.replace("</body>", "</main>\n</body>", 1)
        html = postprocess_tables(html, expected_count=expected["tables"])
        html = "\n".join(line.rstrip() for line in html.splitlines()) + "\n"
        temporary_output.write_text(html, encoding="utf-8", newline="\n")
        # Copy into the tracked path so an existing Windows ACL is preserved.
        # Replacing the inode/file with a sandbox-owned temporary file can make
        # the generated HTML unreadable to the host-side Git process.
        output.write_bytes(temporary_output.read_bytes())
    if "data:image/" not in html:
        raise RuntimeError(f"Expected embedded figure resources in {output.name}.")
    static = validate_static_html(html, expected)
    browser_check = validate_html_accessibility(output) if BROWSER is not None else None
    return {"static_html": static, "browser_accessibility": browser_check,
            "browser_status": "PASS" if browser_check is not None else "NOT_TESTED"}


def sanitize_pdf(
    source: Path,
    destination: Path,
    title: str,
    *,
    expected_formula_count: int = 0,
    outline_titles: list[str] | None = None,
) -> None:
    with pikepdf.open(source) as pdf:
        normalize_structure_semantics(pdf, expected_formula_count=expected_formula_count)
        if outline_titles is not None:
            normalize_outline_titles(pdf, outline_titles)
        canonicalize_structure_ids(pdf)
        for key in list(pdf.docinfo):
            del pdf.docinfo[key]
        pdf.docinfo.update(
            {
                "/Title": title,
                "/Author": AUTHOR,
                "/Subject": PDF_SUBJECT,
                "/Keywords": "ASTRA, integrated draft, typed composition, bounded research",
                "/Creator": "ASTRA draft builder; explicitly recorded local renderer",
                "/Producer": PDF_PRODUCER,
                "/CreationDate": FIXED_PDF_DATE,
                "/ModDate": FIXED_PDF_DATE,
            }
        )
        pdf.Root["/Lang"] = pikepdf.String("en-US")
        pdf.Root["/ViewerPreferences"] = pikepdf.Dictionary(DisplayDocTitle=True)
        if "/Metadata" in pdf.Root:
            del pdf.Root["/Metadata"]
        with pdf.open_metadata(set_pikepdf_as_editor=False, update_docinfo=False) as metadata:
            metadata["dc:title"] = title
            metadata["dc:creator"] = [AUTHOR]
            metadata["dc:description"] = PDF_SUBJECT
            metadata["dc:language"] = ["en-US"]
            metadata["xmp:CreateDate"] = BUILD_EPOCH
            metadata["xmp:ModifyDate"] = BUILD_EPOCH
            metadata["xmp:MetadataDate"] = BUILD_EPOCH
            metadata["xmp:CreatorTool"] = "ASTRA draft builder; explicitly recorded local renderer"
            metadata["pdf:Producer"] = PDF_PRODUCER
        if "/ID" in pdf.trailer:
            del pdf.trailer["/ID"]
        pdf.save(
            destination,
            deterministic_id=True,
            object_stream_mode=pikepdf.ObjectStreamMode.generate,
            compress_streams=True,
        )


def build_pdf(html: Path, output: Path, title: str) -> None:
    with tempfile.TemporaryDirectory(prefix="sppt-astra-pdf-") as temp_dir:
        raw_pdf = Path(temp_dir) / "raw.pdf"
        with sync_playwright() as playwright:
            browser = launch_browser(playwright)
            page = offline_page(browser)
            page.goto(html.resolve().as_uri(), wait_until="networkidle")
            page.emulate_media(media="print")
            page.evaluate("document.fonts.ready")
            semantic_identity = page.evaluate(
                """
                ({ formulaAltPrefix, transparentPixel }) => {
                  const style = document.createElement("style");
                  style.textContent = `
                    body, body * {
                      font-variant-ligatures: none !important;
                      font-feature-settings: "liga" 0, "clig" 0, "dlig" 0 !important;
                    }
                    .pdf-formula-shell {
                      display: inline-block;
                      position: relative;
                    }
                    .pdf-formula-shell.pdf-formula-block { display: block; }
                    .pdf-formula-semantic {
                      height: 100%;
                      inset: 0;
                      position: absolute;
                      width: 100%;
                    }
                  `;
                  document.head.append(style);
                  const formulas = [...document.querySelectorAll("math")];
                  formulas.forEach((math) => {
                    const annotation = math.querySelector(
                      'annotation[encoding="application/x-tex"]'
                    );
                    const tex = (annotation?.textContent || math.textContent || "")
                      .replace(/\\s+/g, " ")
                      .trim();
                    if (!tex) throw new Error("MathML formula lacks a text alternative");
                    const shell = document.createElement("span");
                    shell.className = "pdf-formula-shell";
                    if (math.getAttribute("display") === "block") {
                      shell.classList.add("pdf-formula-block");
                    }
                    const semanticImage = document.createElement("img");
                    semanticImage.className = "pdf-formula-semantic";
                    semanticImage.alt = formulaAltPrefix + tex;
                    semanticImage.src = transparentPixel;
                    math.replaceWith(shell);
                    math.setAttribute("aria-hidden", "true");
                    shell.append(semanticImage, math);
                  });
                  const headings = [...document.querySelectorAll("h1, h2, h3, h4, h5, h6")]
                    .map((heading) => heading.innerText.replace(/\\s+/g, " ").trim());
                  if (headings.some((heading) => !heading)) {
                    throw new Error("Document contains an empty heading");
                  }
                  return { formulaCount: formulas.length, headings };
                }
                """,
                {
                    "formulaAltPrefix": FORMULA_ALT_PREFIX,
                    "transparentPixel": TRANSPARENT_PIXEL,
                },
            )
            page.pdf(
                path=str(raw_pdf),
                format="Letter",
                print_background=True,
                prefer_css_page_size=True,
                tagged=True,
                outline=True,
            )
            browser.close()
        if not raw_pdf.is_file() or raw_pdf.stat().st_size == 0:
            raise RuntimeError(f"Playwright PDF build failed for {html.name}.")
        sanitize_pdf(
            raw_pdf,
            output,
            title,
            expected_formula_count=int(semantic_identity["formulaCount"]),
            outline_titles=list(semantic_identity["headings"]),
        )


def normalized_pdf_text(path: Path) -> str:
    text = "\n".join((page.extract_text() or "") for page in PdfReader(path).pages)
    return re.sub(r"\s+", " ", text).strip()


def historical_inspector():
    """Load unchanged checks without invoking historical writers or granting admission."""
    spec = importlib.util.spec_from_file_location("_integrated_draft_inspector", ROOT / "tools/inspect_pdf.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("PDF inspector could not be loaded")
    inspector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(inspector)
    return inspector


def inspect_draft_pdf(path: Path) -> dict:
    # Only explicit draft metadata changes in this private module instance.
    inspector = historical_inspector()
    inspector.AUTHOR = AUTHOR
    inspector.BUILD_EPOCH = BUILD_EPOCH
    inspector.FIXED_DATE = FIXED_PDF_DATE
    inspector.PDF_SUBJECT = PDF_SUBJECT
    inspector.PDF_PRODUCER = PDF_PRODUCER
    inspector.STRUCTURE_ID_PREFIX = STRUCTURE_ID_PREFIX
    result = inspector.inspect(path)
    expected_title = next(title for _, _, pdf, title in DOCUMENTS if pdf == path)
    if result["metadata"].get("/Title") != expected_title or result["xmp"]["title"] != expected_title:
        raise RuntimeError("PDF title differs from the successor plan")
    return result


def renderer_identity() -> dict:
    if BROWSER is None:
        return {"status": "NOT_USED", "runtime_admitted": False}
    version = subprocess.check_output([str(BROWSER), "--version"], text=True, timeout=15).strip()
    return {"status": "LOCAL_DRAFT_RENDERER", "version": version,
            "launcher_sha256": sha256(BROWSER), "runtime_admitted": False,
            "pinned_renderer_equivalence": "NOT_CLAIMED"}


def main() -> None:
    global BROWSER
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", type=Path, help="Explicit existing browser for draft accessibility/PDF checks; never downloaded")
    parser.add_argument("--pdf", action="store_true", help="Render and inspect unadmitted PDFs with --browser")
    args = parser.parse_args()
    validate_plan(PLAN)
    if args.pdf and args.browser is None:
        parser.error("--pdf requires an explicitly supplied existing --browser")
    BROWSER = args.browser.resolve() if args.browser else None
    if BROWSER is not None and not BROWSER.is_file():
        parser.error("Browser must already exist; no installation is performed")
    snapshot = validate_source_snapshot()
    ensure_safe_directory(TEMP_ROOT)
    tempfile.tempdir = str(TEMP_ROOT)
    outputs = [p for _, html, pdf, _ in DOCUMENTS for p in (html, pdf)]
    outputs += [OUTPUT_ROOT / name for name in (
        "document_identity.json", "pdf_inspection.json", "DEJAVU-FONTS.txt", "STIX-FONTS.txt")]
    for path in outputs:
        ensure_safe_output(path)
    for source, _, _, title in DOCUMENTS:
        source_contract(source, title)
    # A failed later pass must not leave an old success receipt claiming the new bytes.
    pending = json.dumps({"kind": "INTEGRATED_DOCUMENT_DRAFT_RECEIPT",
                          "status": "INCOMPLETE", "runtime_admitted": False}) + "\n"
    (OUTPUT_ROOT / "document_identity.json").write_text(pending)
    (OUTPUT_ROOT / "pdf_inspection.json").write_text(pending)
    records = []
    inspections = []
    for source, html, pdf, title in DOCUMENTS:
        checks = build_html(source, html, title)
        record = {"source": source.name, "source_sha256": sha256(source), "title": title,
                  "html": html.name, "html_sha256": sha256(html), **checks,
                  "pdf_status": "NOT_BUILT_THIS_RUN"}
        if args.pdf:
            build_pdf(html, pdf, title)
            inspection = inspect_draft_pdf(pdf)
            inspections.append(inspection)
            record.update(pdf=pdf.name, pdf_sha256=sha256(pdf), pdf_pages=inspection["pages"],
                          pdf_normalized_text_sha256=inspection["normalized_text_sha256"],
                          pdf_status="DRAFT_INSPECTION_PASS")
        records.append(record)
    for name in ("DEJAVU-FONTS.txt", "STIX-FONTS.txt"):
        (OUTPUT_ROOT / name).write_bytes((ROOT / "licenses" / name).read_bytes())
    identity = {"kind": "INTEGRATED_DOCUMENT_DRAFT_RECEIPT", "status": "CANDIDATE_NOT_ADMITTED",
                "release_version": "1.1.0-alpha.1", "release_tag": "astra-integrated-core-v1.1.0-alpha.1", "runtime_admitted": False,
                "draft_epoch": BUILD_EPOCH, "epoch_is_release_date": False,
                "plan_sha256": sha256(MANUSCRIPT / "document-plan.json"),
                "source_snapshot_sha256": sha256(MANUSCRIPT / "source-snapshot.json"),
                "source_snapshot": snapshot,
                "builder_sha256": sha256(Path(__file__)), "renderer": renderer_identity(),
                "figure_inputs_sha256": sha256(MANUSCRIPT / "figure-inputs.json"),
                "figure_inputs": json.loads((MANUSCRIPT / "figure-inputs.json").read_text()),
                "dependencies": {name: importlib.metadata.version(name) for name in (
                    "pypandoc-binary", "matplotlib", "pikepdf", "pypdf", "playwright")},
                "records": records}
    (OUTPUT_ROOT / "document_identity.json").write_text(json.dumps(identity, indent=2, sort_keys=True) + "\n")
    (OUTPUT_ROOT / "pdf_inspection.json").write_text(json.dumps({
        "kind": "DRAFT_PDF_INSPECTION", "runtime_admitted": False,
        "status": "PASS" if args.pdf else "NOT_BUILT_THIS_RUN", "records": inspections}, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "CANDIDATE_NOT_ADMITTED", "html_editions": len(records),
                      "pdf_editions": len(inspections), "runtime_admitted": False}))


if __name__ == "__main__":
    main()
