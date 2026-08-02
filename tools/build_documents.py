"""Build self-contained HTML and fixed-metadata PDF reading editions."""
from __future__ import annotations

import argparse
import base64
import hashlib
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
