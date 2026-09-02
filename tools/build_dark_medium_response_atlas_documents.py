"""Build the namespaced Dark-Medium Response Atlas HTML and tagged PDF.

This builder never reads Git HEAD and never writes the frozen v1.0.7 outputs.
Its mutable boundary is the versioned Atlas package only.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
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

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "resources" / "dark-medium-response-atlas" / "v0.1.0"
SOURCE = PACKAGE / "dark-medium-response-atlas-v0.1.0.md"
CSS = PACKAGE / "dark-medium-response-atlas-v0.1.0.css"
HTML = PACKAGE / "dark-medium-response-atlas-v0.1.0.html"
PDF = PACKAGE / "dark-medium-response-atlas-v0.1.0.pdf"
SPEC_PATH = PACKAGE / "RELEASE_SPEC.json"
IDENTITY = PACKAGE / "publication-identity.json"
HTML_REPORT = PACKAGE / "html-accessibility.json"
PDF_REPORT = PACKAGE / "pdf-inspection.json"
TEMP_ROOT = ROOT / "tmp" / "dark-medium-response-atlas-document-build"
ATLAS_HELPER = ROOT / "tools" / "dark_medium_response_atlas_document_helpers.py"
HTML_INSPECTOR = ROOT / "tools" / "check_dark_medium_response_atlas_html.py"
PDF_INSPECTOR = ROOT / "tools" / "inspect_dark_medium_response_atlas_pdf.py"
PDF_HELPER = ROOT / "tools" / "dark_medium_response_atlas_pdf_helpers.py"
EXPECTED_TABLE_COUNT = 4
FORMULA_ALT_PREFIX = "Formula in TeX: "
TRANSPARENT_PIXEL = "data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs="

sys.path.insert(0, str(ROOT))
from tools.dark_medium_response_atlas_document_helpers import (  # noqa: E402
    canonicalize_structure_ids,
    embedded_font_css,
    normalize_outline_titles,
    normalize_structure_semantics,
    postprocess_tables,
)


def load_spec() -> dict[str, Any]:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    expected = {
        "publication_line_id": "dark-medium-response-atlas",
        "version": "0.1.0",
        "tag": "dark-medium-response-atlas-v0.1.0",
        "namespace": "resources/dark-medium-response-atlas/v0.1.0",
        "build_epoch": "2026-09-01T00:00:00Z",
        "build_epoch_unix": 1788220800,
    }
    for key, value in expected.items():
        if spec.get(key) != value:
            raise RuntimeError(f"Atlas release specification drift for {key}: {spec.get(key)!r}")
    if spec.get("pages", {}).get("citation_route") != (
        "/resources/dark-medium-response-atlas/v0.1.0/"
    ):
        raise RuntimeError("Atlas citation route is not immutable and versioned")
    return spec


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_link_or_junction(path: Path) -> bool:
    junction_check = getattr(path, "is_junction", None)
    return path.is_symlink() or bool(junction_check and junction_check())


def ensure_safe_directory(path: Path) -> None:
    relative = path.relative_to(ROOT)
    current = ROOT
    for part in relative.parts:
        current /= part
        if is_link_or_junction(current):
            raise RuntimeError(f"Unsafe symbolic link or junction: {current}")
        if current.exists() and not current.is_dir():
            raise RuntimeError(f"Expected directory component: {current}")
    path.mkdir(parents=True, exist_ok=True)
    if path.resolve() != ROOT.resolve().joinpath(*relative.parts):
        raise RuntimeError(f"Output directory escaped repository: {path}")


def canonical_url(spec: dict[str, Any]) -> str:
    return "https://jkolantree.github.io/astra" + str(spec["pages"]["citation_route"])


def publication_footer(spec: dict[str, Any]) -> str:
    release_url = f"{spec['repository']}/releases/tag/{spec['tag']}"
    return f"""
<footer aria-label="Publication information">
  <nav aria-label="Publication resources">
    <ul class="publication-resources">
      <li><a href="./{HTML.name}">HTML</a></li>
      <li><a href="./{PDF.name}">PDF</a></li>
      <li><a href="./dark-medium-response-atlas-v0.1.0-source.tar.gz">Source archive</a></li>
      <li><a href="./claim-ledger.csv">Claim ledger</a></li>
      <li><a href="./source-ledger.csv">Source ledger</a></li>
      <li><a href="./novelty-ledger.csv">Novelty ledger</a></li>
      <li><a href="./SHA256SUMS">Checksums</a></li>
      <li><a href="./CITATION.cff">Citation metadata</a></li>
      <li><a href="./LICENSE_MAP.md">Rights</a></li>
      <li><a href="{release_url}">Tagged prerelease</a></li>
      <li><a href="https://github.com/jkolantree/astra/issues/new/choose">Question it</a></li>
    </ul>
  </nav>
  <p>Substantive OpenAI Codex assistance is disclosed. Scientific judgment,
  authorship, and responsibility remain with the human project owner.</p>
</footer>
"""


def normalize_html(raw: str, spec: dict[str, Any]) -> str:
    if raw.count("</head>") != 1 or raw.count("<body>") != 1 or raw.count("</body>") != 1:
        raise RuntimeError("Pandoc output lacks one canonical document shell")
    url = canonical_url(spec)
    head = (
        embedded_font_css()
        + f'<link rel="canonical" href="{url}">'
        + '<meta name="description" content="A response-first atlas of path, compensation, '
        'memory, observation, and hidden-sector identifiability.">'
    )
    html = raw.replace("</head>", head + "</head>", 1)
    html = html.replace(
        "<body>",
        '<body>\n<a class="skip-link" href="#main-content">Skip to main content</a>',
        1,
    )
    nav_end = html.find("</nav>")
    if nav_end < 0:
        raise RuntimeError("Generated HTML lacks the document table of contents")
    nav_end += len("</nav>")
    html = html[:nav_end] + '\n<main id="main-content" tabindex="-1">' + html[nav_end:]
    html = html.replace("</body>", "</main>\n" + publication_footer(spec) + "</body>", 1)
    containers = re.compile(
        r"<(?P<tag>div|section)(?P<attrs>[^>]*)>(?P<body>.*?)</(?P=tag)>",
        flags=re.DOTALL,
    )
    status_matches = [
        match
        for match in containers.finditer(html)
        if re.search(
            r'\bclass="[^"]*\bstatus-box\b[^"]*"',
            match.group("attrs"),
        )
    ]
    if len(status_matches) != 1:
        raise RuntimeError("Source must produce exactly one compact status box")
    status_match = status_matches[0]
    html = (
        html[: status_match.start()]
        + f'<aside{status_match.group("attrs")}>'
        + status_match.group("body")
        + "</aside>"
        + html[status_match.end() :]
    )
    html = postprocess_tables(html, expected_count=EXPECTED_TABLE_COUNT)
    html = "\n".join(line.rstrip() for line in html.splitlines()) + "\n"
    if re.search(r"[A-Za-z]:\\|/Users/|/home/", html):
        raise RuntimeError("Machine-local path leaked into Atlas HTML")
    return html


def build_html(spec: dict[str, Any]) -> None:
    resources = os.pathsep.join((str(PACKAGE), str(ROOT)))
    with tempfile.TemporaryDirectory(prefix="atlas-html-", dir=TEMP_ROOT) as temp_dir:
        temporary = Path(temp_dir) / HTML.name
        pypandoc.convert_file(
            str(SOURCE),
            "html5",
            outputfile=str(temporary),
            extra_args=[
                "--from=markdown+fenced_divs+raw_html+tex_math_dollars",
                "--standalone",
                "--toc",
                "--toc-depth=3",
                "--mathml",
                "--embed-resources",
                f"--resource-path={resources}",
                f"--css={CSS}",
                f"--metadata=pagetitle:{spec['title']}",
                "--metadata=lang:en-US",
            ],
        )
        result = normalize_html(temporary.read_text(encoding="utf-8"), spec)
        temporary.write_text(result, encoding="utf-8", newline="\n")
        HTML.write_bytes(temporary.read_bytes())


def sanitize_pdf(
    raw: Path,
    destination: Path,
    spec: dict[str, Any],
    *,
    headings: list[str],
    formula_count: int,
) -> None:
    epoch = str(spec["build_epoch"])
    pdf_date = "D:" + re.sub(r"[-:T]", "", epoch)
    subject = "ASTRA supplemental working paper and methods proposal; not peer reviewed"
    producer = (
        "ASTRA Dark-Medium Response Atlas deterministic build v0.1.0; pikepdf 10.11.0"
    )
    with pikepdf.open(raw) as pdf:
        normalize_structure_semantics(pdf, expected_formula_count=formula_count)
        normalize_outline_titles(pdf, headings)
        canonicalize_structure_ids(pdf)
        for key in list(pdf.docinfo):
            del pdf.docinfo[key]
        pdf.docinfo.update(
            {
                "/Title": str(spec["title"]),
                "/Author": str(spec["author"]),
                "/Subject": subject,
                "/Keywords": "ASTRA, dark medium, response theory, identifiability, path dependence",
                "/Creator": "Pandoc 3.6.1 and Playwright 1.62.0 Chromium",
                "/Producer": producer,
                "/CreationDate": pdf_date,
                "/ModDate": pdf_date,
            }
        )
        pdf.Root["/Lang"] = pikepdf.String("en-US")
        pdf.Root["/ViewerPreferences"] = pikepdf.Dictionary(DisplayDocTitle=True)
        if "/Metadata" in pdf.Root:
            del pdf.Root["/Metadata"]
        with pdf.open_metadata(set_pikepdf_as_editor=False, update_docinfo=False) as metadata:
            metadata["dc:title"] = str(spec["title"])
            metadata["dc:creator"] = [str(spec["author"])]
            metadata["dc:description"] = subject
            metadata["dc:language"] = ["en-US"]
            metadata["xmp:CreateDate"] = epoch
            metadata["xmp:ModifyDate"] = epoch
            metadata["xmp:MetadataDate"] = epoch
            metadata["xmp:CreatorTool"] = "Pandoc 3.6.1 and Playwright 1.62.0 Chromium"
            metadata["pdf:Producer"] = producer
        if "/ID" in pdf.trailer:
            del pdf.trailer["/ID"]
        pdf.save(
            destination,
            deterministic_id=True,
            object_stream_mode=pikepdf.ObjectStreamMode.generate,
            compress_streams=True,
        )


def build_pdf(spec: dict[str, Any]) -> str:
    url = canonical_url(spec)
    with tempfile.TemporaryDirectory(prefix="atlas-pdf-", dir=TEMP_ROOT) as temp_dir:
        raw = Path(temp_dir) / "raw.pdf"
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--disable-gpu"])
            try:
                browser_version = browser.version
                page = browser.new_page()
                page.goto(HTML.resolve().as_uri(), wait_until="networkidle")
                page.emulate_media(media="print", reduced_motion="reduce")
                page.evaluate("() => document.fonts.ready")
                semantic = page.evaluate(
                    r"""({ formulaAltPrefix, transparentPixel, canonicalUrl, htmlName }) => {
                      const style = document.createElement("style");
                      style.textContent =
                        "body,body *{font-variant-ligatures:none!important;" +
                        "font-feature-settings:'liga' 0,'clig' 0,'dlig' 0!important}" +
                        ".pdf-formula-shell{display:inline-block;position:relative}" +
                        ".pdf-formula-shell.pdf-formula-block{display:block}" +
                        ".pdf-formula-semantic{height:100%;inset:0;position:absolute;width:100%}";
                      document.head.append(style);
                      const formulas = [...document.querySelectorAll("math")];
                      formulas.forEach((math) => {
                        const annotation = math.querySelector(
                          'annotation[encoding="application/x-tex"]'
                        );
                        const tex = (annotation?.textContent || math.textContent || "")
                          .replace(/\s+/g, " ").trim();
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
                      for (const anchor of document.querySelectorAll("a[href]")) {
                        const raw = anchor.getAttribute("href");
                        if (!raw || raw.startsWith("#") ||
                            /^[a-z][a-z0-9+.-]*:/i.test(raw)) continue;
                        const resolved = new URL(raw, canonicalUrl);
                        if (resolved.pathname.endsWith("/" + htmlName)) {
                          anchor.href = canonicalUrl + (resolved.hash || "");
                        } else {
                          anchor.href = resolved.href;
                        }
                      }
                      const headings = [...document.querySelectorAll("h1,h2,h3,h4,h5,h6")]
                        .map((heading) => heading.innerText.replace(/\s+/g, " ").trim());
                      if (headings.some((heading) => !heading)) {
                        throw new Error("Document contains an empty heading");
                      }
                      return { formulaCount: formulas.length, headings };
                    }""",
                    {
                        "formulaAltPrefix": FORMULA_ALT_PREFIX,
                        "transparentPixel": TRANSPARENT_PIXEL,
                        "canonicalUrl": url,
                        "htmlName": HTML.name,
                    },
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
        sanitize_pdf(
            raw,
            PDF,
            spec,
            headings=list(semantic["headings"]),
            formula_count=int(semantic["formulaCount"]),
        )
    return browser_version


def font_bindings() -> list[dict[str, Any]]:
    runtime = json.loads((ROOT / "RUNTIME.json").read_text(encoding="utf-8"))
    font_dir = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
    bindings = []
    for record in runtime["pdf_renderer"]["font_sources"]["files"]:
        path = font_dir / str(record["file"])
        observed = {"file": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)}
        expected = {key: record[key] for key in observed}
        if observed != expected:
            raise RuntimeError(f"Atlas source-font drift: {observed}")
        bindings.append(observed)
    return bindings


def write_identity(spec: dict[str, Any], browser_version: str) -> None:
    normalized_text = re.sub(
        r"\s+",
        " ",
        "\n".join((page.extract_text() or "") for page in PdfReader(PDF).pages),
    ).strip()
    inputs = [
        SOURCE,
        CSS,
        SPEC_PATH,
        Path(__file__),
        ATLAS_HELPER,
        HTML_INSPECTOR,
        PDF_INSPECTOR,
        PDF_HELPER,
        ROOT / "RUNTIME.json",
        ROOT / "requirements-lock.txt",
    ]
    artifacts = [HTML, PDF, HTML_REPORT, PDF_REPORT]
    identity = {
        "schema": (
            "https://jkolantree.github.io/astra/schemas/"
            "dark-medium-response-atlas-publication-identity-v1.schema.json"
        ),
        "publication_line_id": spec["publication_line_id"],
        "version": spec["version"],
        "title": spec["title"],
        "canonical_url": canonical_url(spec),
        "build_epoch": spec["build_epoch"],
        "identity_excludes_self": True,
        "inputs": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in inputs
        ],
        "font_sources": font_bindings(),
        "artifacts": [
            {
                "path": path.relative_to(PACKAGE).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in artifacts
        ],
        "pdf_pages": len(PdfReader(PDF).pages),
        "pdf_normalized_text_sha256": hashlib.sha256(
            normalized_text.encode("utf-8")
        ).hexdigest(),
        "runtime": {
            "python": platform.python_version(),
            "pandoc": str(pypandoc.get_pandoc_version()),
            "pikepdf": pikepdf.__version__,
            "pypdf": importlib.metadata.version("pypdf"),
            "playwright": importlib.metadata.version("playwright"),
            "browser": browser_version,
            "matplotlib": matplotlib.__version__,
        },
        "accessibility": {
            "primary_reading_edition": HTML.name,
            "fixed_layout_edition": PDF.name,
            "pdf_claim": (
                "tagged and structurally checked; no PDF/UA conformance claim is made"
            ),
        },
    }
    IDENTITY.write_text(
        json.dumps(identity, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--html-only", action="store_true")
    parser.add_argument("--no-identity", action="store_true")
    args = parser.parse_args()
    ensure_safe_directory(ROOT / "tmp")
    ensure_safe_directory(TEMP_ROOT)
    os.environ.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "SOURCE_DATE_EPOCH": "1788220800",
            "TZ": "UTC",
            "TEMP": str(TEMP_ROOT),
            "TMP": str(TEMP_ROOT),
            "TMPDIR": str(TEMP_ROOT),
        }
    )
    spec = load_spec()
    build_html(spec)
    from tools.check_dark_medium_response_atlas_html import check_html

    check_html(HTML, write_report=True)
    if args.html_only:
        print(f"Built and checked {HTML.name}.")
        return
    browser_version = build_pdf(spec)
    from tools.inspect_dark_medium_response_atlas_pdf import inspect_pdf

    inspect_pdf(PDF, write_report=True)
    if not args.no_identity:
        write_identity(spec, browser_version)
    print(f"Built and checked {HTML.name} and {PDF.name}.")


if __name__ == "__main__":
    main()
