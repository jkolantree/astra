"""Build self-contained HTML and fixed-metadata PDF reading editions."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

import matplotlib
import pikepdf
import pypandoc
from playwright.sync_api import sync_playwright
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "manuscript"
TEMP_ROOT = ROOT / "tmp" / "document-build"
FIXED_PDF_DATE = "D:20260801000000Z"
VERSION = "1.0.1"
AUTHOR = "Jacko T."

DOCUMENTS = (
    (
        MANUSCRIPT / "manuscript.md",
        MANUSCRIPT / f"SPPT_ASTRA_preprint_v{VERSION}.html",
        MANUSCRIPT / f"SPPT_ASTRA_preprint_v{VERSION}.pdf",
        "Phase-Reservoir Topology as a Hidden State Variable in Planetary Evolution",
    ),
    (
        MANUSCRIPT / "supplement.md",
        MANUSCRIPT / f"SPPT_ASTRA_technical_supplement_v{VERSION}.html",
        MANUSCRIPT / f"SPPT_ASTRA_technical_supplement_v{VERSION}.pdf",
        "Technical Supplement: Synthetic Identifiability and Topology-Recovery Tests",
    ),
)


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


def sanitize_pdf(source: Path, destination: Path, title: str) -> None:
    with pikepdf.open(source) as pdf:
        for key in list(pdf.docinfo):
            del pdf.docinfo[key]
        pdf.docinfo.update(
            {
                "/Title": title,
                "/Author": AUTHOR,
                "/Subject": "SPPT/ASTRA v1.0.1; not peer reviewed",
                "/Keywords": "SPPT, ASTRA, planetary evolution, reservoir networks",
                "/Creator": "Pandoc 3.6.1 and Playwright 1.62.0 Chromium",
                "/Producer": "SPPT-ASTRA reproducibility build v1.0.1; pikepdf 10.11.0",
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
            metadata["dc:description"] = "SPPT/ASTRA v1.0.1; not peer reviewed"
            metadata["dc:language"] = ["en-US"]
            metadata["xmp:CreateDate"] = "2026-08-01T00:00:00Z"
            metadata["xmp:ModifyDate"] = "2026-08-01T00:00:00Z"
            metadata["xmp:MetadataDate"] = "2026-08-01T00:00:00Z"
            metadata["xmp:CreatorTool"] = "Pandoc 3.6.1 and Playwright 1.62.0 Chromium"
            metadata["pdf:Producer"] = (
                "SPPT-ASTRA reproducibility build v1.0.1; pikepdf 10.11.0"
            )
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
        sanitize_pdf(raw_pdf, output, title)


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
                    "tagged PDF with document language, outline, embedded fonts, extractable text, "
                    "and figure alternative text; self-contained HTML is the primary accessible reading edition"
                ),
            }
        )
    identity = {
        "schema": "https://github.com/jkolantree/astra/schemas/document-semantic-identity-v1",
        "build_epoch": "2026-08-01T00:00:00Z",
        "records": records,
    }
    (MANUSCRIPT / "document_semantic_identity.json").write_text(
        json.dumps(identity, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )


def main() -> None:
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(TEMP_ROOT)
    for variable in ("TEMP", "TMP", "TMPDIR"):
        os.environ[variable] = str(TEMP_ROOT)
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    parser = argparse.ArgumentParser()
    parser.add_argument("--html-only", action="store_true", help="Build deterministic self-contained HTML only.")
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
