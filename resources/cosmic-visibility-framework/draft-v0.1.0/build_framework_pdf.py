"""Build the unpromoted Cosmic Visibility Framework HTML and PDF.

The namespaced builder never reads Git HEAD. It binds the result to the source
hash, explicit audited base metadata, fixed build epoch, and renderer identity.
It leaves the immutable v1.0.6 build pipeline untouched.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

import matplotlib
import pikepdf
import pypandoc
from playwright.sync_api import sync_playwright
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[3]
DRAFT = Path(__file__).resolve().parent
SOURCE = DRAFT / "CORE_FRAMEWORK.md"
HTML = DRAFT / "COSMIC_VISIBILITY_FRAMEWORK_v0.1.0.html"
PDF = DRAFT / "COSMIC_VISIBILITY_FRAMEWORK_v0.1.0.pdf"
IDENTITY = DRAFT / "pdf_build_identity.json"
CSS = ROOT / "manuscript" / "style.css"
TITLE = "Cosmic Visibility and Sampling Framework"
AUTHOR = "Jacko T."
VERSION = "0.1.0"
BUILD_EPOCH = "2026-08-09T00:00:00Z"
PDF_DATE = "D:20260809000000Z"
PDF_SUBJECT = "ASTRA cosmic visibility research draft; not peer reviewed"
PDF_PRODUCER = "ASTRA deterministic successor-draft build; pikepdf 10.11.0"
BROWSER_VERSION = "not_run"
FORMULA_ALT_PREFIX = "Formula in TeX: "
TRANSPARENT_PIXEL = "data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs="

sys.path.insert(0, str(ROOT))
from tools.build_documents import (  # noqa: E402
    canonicalize_structure_ids,
    normalize_outline_titles,
    normalize_structure_semantics,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def embedded_font_css() -> str:
    font_dir = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
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
    declarations = []
    for filename, family, style, weight in variants:
        encoded = base64.b64encode((font_dir / filename).read_bytes()).decode("ascii")
        declarations.append(
            "@font-face {"
            f"font-family:'{family}';font-style:{style};font-weight:{weight};"
            f"src:url(data:font/ttf;base64,{encoded}) format('truetype');"
            "font-display:block;}"
        )
    return "<style>" + "".join(declarations) + "</style>"


def table_scopes(html: str) -> str:
    pattern = re.compile(r"<table(?P<attrs>[^>]*)>.*?</table>", re.DOTALL)

    def process(match: re.Match[str]) -> str:
        table = match.group(0)

        def header(cell: re.Match[str]) -> str:
            attrs = cell.group("attrs")
            return cell.group(0) if "scope=" in attrs else f'<th{attrs} scope="col">'

        table = re.sub(r"<th(?P<attrs>[^>]*)>", header, table)
        body_match = re.search(r"<tbody>(?P<body>.*?)</tbody>", table, re.DOTALL)
        if body_match is None:
            return table
        body = body_match.group("body")

        def row(row_match: re.Match[str]) -> str:
            source = row_match.group(0)
            cell = re.search(r"<td(?P<attrs>[^>]*)>(?P<content>.*?)</td>", source, re.DOTALL)
            if cell is None:
                return source
            replacement = f'<th{cell.group("attrs")} scope="row">{cell.group("content")}</th>'
            return source[: cell.start()] + replacement + source[cell.end() :]

        body = re.sub(r"<tr>.*?</tr>", row, body, flags=re.DOTALL)
        return table[: body_match.start("body")] + body + table[body_match.end("body") :]

    return pattern.sub(process, html)


def inline_svg_assets(html: str) -> str:
    """Inline original SVGs so the embedded PDF font CSS applies to their text."""
    pattern = re.compile(
        r'<img(?P<before>[^>]*?)src="data:image/svg\+xml;base64,(?P<data>[^"]+)"(?P<after>[^>]*)>',
        re.DOTALL,
    )

    def replace(match: re.Match[str]) -> str:
        svg = base64.b64decode(match.group("data")).decode("utf-8")
        if not svg.lstrip().startswith("<svg"):
            raise RuntimeError("Embedded SVG image does not decode to an SVG root")
        # Pandoc's embedded image CSS does not apply after replacing the
        # <img> with an inline SVG. Make the original vector responsive to the
        # document column so its rightmost labels stay inside the page.
        svg = re.sub(
            r"<svg(?P<attrs>\s[^>]*)>",
            r'<svg\g<attrs> style="display:block;max-width:100%;width:100%;height:auto">',
            svg,
            count=1,
        )
        return svg

    return pattern.sub(replace, html)


def build_html() -> None:
    if not SOURCE.is_file():
        raise RuntimeError(f"Missing source: {SOURCE}")
    resources = os.pathsep.join((str(DRAFT), str(ROOT), str(ROOT / "figures")))
    with tempfile.TemporaryDirectory(prefix="cosmic-visibility-html-") as temp_dir:
        temporary = Path(temp_dir) / HTML.name
        pypandoc.convert_file(
            str(SOURCE),
            "html5",
            outputfile=str(temporary),
            extra_args=[
                "--standalone",
                "--toc",
                "--toc-depth=2",
                "--mathml",
                "--embed-resources",
                f"--resource-path={resources}",
                f"--css={CSS}",
                f"--metadata=pagetitle:{TITLE}",
                "--metadata=lang:en-US",
            ],
        )
        html = temporary.read_text(encoding="utf-8")
        html = html.replace("</head>", embedded_font_css() + "</head>", 1)
        html = html.replace(
            "<body>",
            '<body>\n<a class="skip-link" href="#main-content">Skip to main content</a>',
            1,
        )
        nav_end = html.find("</nav>")
        if nav_end < 0:
            raise RuntimeError("Generated HTML lacks a table-of-contents landmark")
        nav_end += len("</nav>")
        html = html[:nav_end] + '\n<main id="main-content" tabindex="-1">' + html[nav_end:]
        html = html.replace("</body>", "</main>\n</body>", 1)
        html = table_scopes(html)
        html = inline_svg_assets(html)
        html = "\n".join(line.rstrip() for line in html.splitlines()) + "\n"
        temporary.write_text(html, encoding="utf-8", newline="\n")
        HTML.write_bytes(temporary.read_bytes())
    if re.search(
        r"[A-Za-z]:\\\\|/Users/|/home/|\\b[A-Z][A-Za-z .'-]+,\\s*(?:USA|United States)\\b",
        html,
        re.IGNORECASE,
    ):
        raise RuntimeError("Private or machine-local content leaked into HTML")
    if html.count("<svg") < 2:
        raise RuntimeError("Original SVG figures were not inlined into HTML")


def sanitize_pdf(raw: Path, headings: list[str], formula_count: int) -> None:
    with pikepdf.open(raw) as pdf:
        normalize_structure_semantics(pdf, expected_formula_count=formula_count)
        normalize_outline_titles(pdf, headings)
        canonicalize_structure_ids(pdf)
        for key in list(pdf.docinfo):
            del pdf.docinfo[key]
        pdf.docinfo.update(
            {
                "/Title": TITLE,
                "/Author": AUTHOR,
                "/Subject": PDF_SUBJECT,
                "/Keywords": "ASTRA, cosmic visibility, sampling, operator-aware inference",
                "/Creator": "Pandoc 3.6.1 and Playwright 1.62.0 Chromium",
                "/Producer": PDF_PRODUCER,
                "/CreationDate": PDF_DATE,
                "/ModDate": PDF_DATE,
            }
        )
        pdf.Root["/Lang"] = pikepdf.String("en-US")
        pdf.Root["/ViewerPreferences"] = pikepdf.Dictionary(DisplayDocTitle=True)
        if "/Metadata" in pdf.Root:
            del pdf.Root["/Metadata"]
        with pdf.open_metadata(set_pikepdf_as_editor=False, update_docinfo=False) as metadata:
            metadata["dc:title"] = TITLE
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
            PDF,
            deterministic_id=True,
            object_stream_mode=pikepdf.ObjectStreamMode.generate,
            compress_streams=True,
        )


def build_pdf() -> None:
    global BROWSER_VERSION
    with tempfile.TemporaryDirectory(prefix="cosmic-visibility-pdf-") as temp_dir:
        raw = Path(temp_dir) / "raw.pdf"
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--disable-gpu"])
            try:
                BROWSER_VERSION = browser.version
                page = browser.new_page()
                page.goto(HTML.resolve().as_uri(), wait_until="networkidle")
                page.emulate_media(media="print")
                page.evaluate("document.fonts.ready")
                result = page.evaluate(
                    """
                    ({ formulaAltPrefix, transparentPixel }) => {
                      const style = document.createElement("style");
                      style.textContent =
                        "body, body * { font-variant-ligatures: none !important; " +
                        "font-feature-settings: 'liga' 0, 'clig' 0, 'dlig' 0 !important; }" +
                        ".pdf-formula-shell { display: inline-block; position: relative; }" +
                        ".pdf-formula-shell.pdf-formula-block { display: block; }" +
                        ".pdf-formula-semantic { height: 100%; inset: 0; position: absolute; width: 100%; }";
                      document.head.append(style);
                      const formulas = [...document.querySelectorAll("math")];
                      formulas.forEach((math) => {
                        const annotation = math.querySelector(
                          'annotation[encoding="application/x-tex"]'
                        );
                        const tex = (annotation?.textContent || math.textContent || "")
                          .replace(/\\\\s+/g, " ").trim();
                        if (!tex) throw new Error("MathML formula lacks a text alternative");
                        const shell = document.createElement("span");
                        shell.className = "pdf-formula-shell";
                        if (math.getAttribute("display") === "block") {
                          shell.classList.add("pdf-formula-block");
                        }
                        const image = document.createElement("img");
                        image.className = "pdf-formula-semantic";
                        image.alt = formulaAltPrefix + tex;
                        image.src = transparentPixel;
                        math.replaceWith(shell);
                        math.setAttribute("aria-hidden", "true");
                        shell.append(image, math);
                      });
                      const headings = [...document.querySelectorAll("h1,h2,h3,h4,h5,h6")]
                        .map((heading) => heading.innerText.replace(/\\s+/g, " ").trim());
                      return { formulaCount: formulas.length, headings };
                    }
                    """,
                    {"formulaAltPrefix": FORMULA_ALT_PREFIX, "transparentPixel": TRANSPARENT_PIXEL},
                )
                page.pdf(
                    path=str(raw),
                    format="Letter",
                    print_background=True,
                    prefer_css_page_size=True,
                    tagged=True,
                    outline=True,
                )
            finally:
                browser.close()
        sanitize_pdf(raw, list(result["headings"]), int(result["formulaCount"]))


def write_identity() -> None:
    metadata: dict[str, Any] = {}
    metadata_path = DRAFT / "draft_metadata.json"
    if metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    record: dict[str, Any] = {
        "schema": "astra-cosmic-visibility-pdf-build-v1",
        "status": "unpromoted_default_branch_research_draft",
        "title": TITLE,
        "version": VERSION,
        "build_epoch": BUILD_EPOCH,
        "audited_base_commit": metadata.get("audited_base_commit", "6982f700bdad2f8e19a3ab4121f1afb0aa323d92"),
        "audited_base_tree": metadata.get("audited_base_tree", "7aee19aa1bc31ac9d918ff797dc51dfb50d6afae"),
        "identity_excludes_self": True,
        "source": {"name": SOURCE.name, "sha256": sha256(SOURCE)},
        "builder": {"name": Path(__file__).name, "sha256": sha256(Path(__file__))},
        "input_bindings": [
            {"name": "manuscript/style.css", "sha256": sha256(CSS)},
            *[
                {
                    "name": f"resources/cosmic-visibility-framework/draft-v0.1.0/figures/{figure.name}",
                    "sha256": sha256(figure),
                }
                for figure in sorted((DRAFT / "figures").glob("*.svg"))
            ],
        ],
        "artifacts": [
            {"name": HTML.name, "bytes": HTML.stat().st_size, "sha256": sha256(HTML)},
            {"name": PDF.name, "bytes": PDF.stat().st_size, "sha256": sha256(PDF), "pages": len(PdfReader(PDF).pages)},
        ],
        "runtime": {
            "python": "3.12.10",
            "pandoc": str(pypandoc.get_pandoc_version()),
            "pikepdf": pikepdf.__version__,
            "matplotlib": matplotlib.__version__,
            "playwright": "1.62.0",
            "browser": BROWSER_VERSION,
            "font_provider": "matplotlib bundled DejaVu/STIX",
        },
        "rights": {
            "original_prose_and_vector_art": "CC BY 4.0 to the extent held by the project author",
            "third_party_sources": "citation leads only; no source bytes redistributed",
        },
    }
    IDENTITY.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--html-only", action="store_true")
    parser.add_argument("--no-identity", action="store_true")
    args = parser.parse_args()
    build_html()
    if not args.html_only:
        build_pdf()
        if not args.no_identity:
            write_identity()
    print("Built " + HTML.name + ("" if args.html_only else " and " + PDF.name))


if __name__ == "__main__":
    main()
