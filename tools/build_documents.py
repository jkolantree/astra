"""Build self-contained HTML and fixed-metadata PDF reading editions."""

from __future__ import annotations

import argparse
import base64
import hashlib
import html as html_module
import json
import os
import re
import tempfile
from collections.abc import Iterator
from pathlib import Path

import matplotlib
import pikepdf
import pypandoc
from playwright.sync_api import sync_playwright
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "manuscript"
TEMP_ROOT = ROOT / "tmp" / "document-build"
RELEASE_SPEC = json.loads((ROOT / "RELEASE_SPEC.json").read_text(encoding="utf-8"))
VERSION = str(RELEASE_SPEC["version"])
BUILD_EPOCH = str(RELEASE_SPEC["build_epoch"])
AUTHOR = str(RELEASE_SPEC["author"])
if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", BUILD_EPOCH):
    raise RuntimeError(f"Noncanonical release build epoch: {BUILD_EPOCH!r}")
FIXED_PDF_DATE = "D:" + re.sub(r"[-:T]", "", BUILD_EPOCH)
PDF_SUBJECT = f"SPPT/ASTRA v{VERSION}; not peer reviewed"
PDF_PRODUCER = f"SPPT-ASTRA reproducibility build v{VERSION}; pikepdf 10.11.0"
STRUCTURE_ID_PREFIX = "sppt-struct-"
FORMULA_ALT_PREFIX = "Formula in TeX: "
TRANSPARENT_PIXEL = "data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs="
EXPECTED_TABLE_COUNTS = {"manuscript.md": 11, "supplement.md": 6}

DOCUMENTS = (
    (
        MANUSCRIPT / "manuscript.md",
        MANUSCRIPT / f"SPPT_ASTRA_preprint_v{VERSION}.html",
        MANUSCRIPT / f"SPPT_ASTRA_preprint_v{VERSION}.pdf",
        "SPPT / ASTRA v1.0.7: Stateful Edges and Operator-Aware Inference",
    ),
    (
        MANUSCRIPT / "supplement.md",
        MANUSCRIPT / f"SPPT_ASTRA_technical_supplement_v{VERSION}.html",
        MANUSCRIPT / f"SPPT_ASTRA_technical_supplement_v{VERSION}.pdf",
        "Technical Supplement: Synthetic Pointwise Topology Selection and Identifiability Limits",
    ),
)


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
        browser = playwright.chromium.launch(headless=True, args=["--disable-gpu"])
        try:
            page = browser.new_page()
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


def build_html(source: Path, output: Path, title: str) -> None:
    resource_path = os.pathsep.join((str(MANUSCRIPT), str(ROOT), str(ROOT / "figures")))
    numbering_arguments = [] if source.name == "manuscript.md" else ["--number-sections"]
    with tempfile.TemporaryDirectory(prefix="sppt-astra-html-") as temp_dir:
        temporary_output = Path(temp_dir) / output.name
        pypandoc.convert_file(
            str(source),
            "html5",
            outputfile=str(temporary_output),
            extra_args=[
                "--standalone",
                "--toc",
                "--toc-depth=3",
                *numbering_arguments,
                "--citeproc",
                "--mathml",
                "--embed-resources",
                f"--resource-path={resource_path}",
                f"--bibliography={MANUSCRIPT / 'references.bib'}",
                f"--css={MANUSCRIPT / 'style.css'}",
                f"--metadata=pagetitle:{title}",
                "--metadata=lang:en-US",
            ],
        )
        html = temporary_output.read_text(encoding="utf-8")
        html = html.replace("</head>", embedded_font_css() + "</head>", 1)
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
        html = postprocess_tables(html, expected_count=EXPECTED_TABLE_COUNTS[source.name])
        html = "\n".join(line.rstrip() for line in html.splitlines()) + "\n"
        temporary_output.write_text(html, encoding="utf-8", newline="\n")
        # Copy into the tracked path so an existing Windows ACL is preserved.
        # Replacing the inode/file with a sandbox-owned temporary file can make
        # the generated HTML unreadable to the host-side Git process.
        output.write_bytes(temporary_output.read_bytes())
    if re.search(
        r"(?:^\s*(?:contact|correspondence)\s*[:=]\s*(?:TBD|TODO|pending|placeholder)\b|"
        r"[A-Za-z]:\\|/Users/|/home/|nature\.csl|"
        r"\b[A-Z][A-Za-z .'-]+,\s*(?:USA|United States)\b)",
        html,
        re.IGNORECASE | re.MULTILINE,
    ):
        raise RuntimeError(f"Private or machine-local path leaked into {output.name}.")
    if "data:image/" not in html:
        raise RuntimeError(f"Expected embedded figure resources in {output.name}.")
    validate_html_accessibility(output)


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
                "/Keywords": "SPPT, ASTRA, planetary evolution, reservoir networks",
                "/Creator": "Pandoc 3.6.1 and Playwright 1.62.0 Chromium",
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
            metadata["xmp:CreatorTool"] = "Pandoc 3.6.1 and Playwright 1.62.0 Chromium"
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
            browser = playwright.chromium.launch(headless=True, args=["--disable-gpu"])
            page = browser.new_page()
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


def write_semantic_identity() -> None:
    records = []
    for source, html, pdf, title in DOCUMENTS:
        reader = PdfReader(pdf)
        normalized = normalized_pdf_text(pdf).encode("utf-8")
        records.append(
            {
                "source": source.name,
                "source_sha256": sha256(source),
                "html": html.name,
                "html_sha256": sha256(html),
                "pdf": pdf.name,
                "pdf_sha256": sha256(pdf),
                "pdf_pages": len(reader.pages),
                "pdf_normalized_text_sha256": hashlib.sha256(normalized).hexdigest(),
                "title": title,
                "author": AUTHOR,
                "version": VERSION,
                "language": "en-US",
                "pdf_accessibility": (
                    "tagged PDF with document language, normalized outline, embedded fonts, "
                    "extractable ligature-free text, formula alternatives, and figure alternative text; "
                    "self-contained HTML is the primary accessible reading edition"
                ),
            }
        )
    identity = {
        "schema": (
            "https://jkolantree.github.io/astra/schemas/document-semantic-identity-v1.schema.json"
        ),
        "build_epoch": BUILD_EPOCH,
        "records": records,
    }
    (MANUSCRIPT / "document_semantic_identity.json").write_text(
        json.dumps(identity, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )


def main() -> None:
    ensure_safe_directory(ROOT / "tmp")
    ensure_safe_directory(TEMP_ROOT)
    tempfile.tempdir = str(TEMP_ROOT)
    for variable in ("TEMP", "TMP", "TMPDIR"):
        os.environ[variable] = str(TEMP_ROOT)
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--html-only", action="store_true", help="Build deterministic self-contained HTML only."
    )
    args = parser.parse_args()
    for source, html, pdf, title in DOCUMENTS:
        build_html(source, html, title)
        if not args.html_only:
            build_pdf(html, pdf, title)
    if not args.html_only:
        write_semantic_identity()
    print("Built synchronized SPPT/ASTRA reading editions.")


if __name__ == "__main__":
    main()
