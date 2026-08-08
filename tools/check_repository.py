"""Fail-closed repository, metadata, accessibility, privacy, and license checks."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import tomllib
from datetime import UTC, date, datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from jsonschema import Draft7Validator, FormatChecker
from PIL import Image
from pypdf import PdfReader
from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[1]
IGNORED_ROOTS = {
    ".git",
    ".venv",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "tmp",
    "dist",
    "build",
}
IGNORED_NAMES = IGNORED_ROOTS | {"__pycache__"}
DISPOSABLE_ROOTS = {".git", ".venv", "tmp", "dist", "build"}
FORBIDDEN_CACHE_NAMES = {".pytest_cache", ".mypy_cache", ".ruff_cache", "__pycache__"}
ROOT_ALLOWLIST = {
    ".gitattributes",
    ".gitignore",
    ".mailmap",
    ".python-version",
    "CHANGELOG.md",
    "CITATION.cff",
    "CLAIM_MATRIX.json",
    "LICENSE",
    "LICENSE_MAP.md",
    "MANIFEST.sha256",
    "README.md",
    "RELEASE_NOTES_earth-instrument-framework-v0.3.0.md",
    "RELEASE_NOTES_earth-instrument-wp-0.1.md",
    "RELEASE_NOTES_v1.0.1.md",
    "RELEASE_NOTES_v1.0.2.md",
    "RELEASE_NOTES_v1.0.3.md",
    "RELEASE_NOTES_v1.0.4.md",
    "RELEASE_NOTES_v1.0.5.md",
    "RELEASE_NOTES_v1.0.6.md",
    "RELEASE_SPEC.json",
    "RUNTIME.json",
    "SOURCE_INVENTORY.json",
    "THIRD_PARTY_NOTICES.md",
    "pyproject.toml",
    "requirements.in",
    "requirements-lock.txt",
}
DIRECTORY_RULES = {
    ".github/ISSUE_TEMPLATE": {".md", ".yaml", ".yml"},
    ".github/workflows": {".yml", ".yaml"},
    "data": {".csv", ".json"},
    "evidence": {".json", ".md", ".txt"},
    "figures": {".png", ".pdf"},
    "licenses": {".txt"},
    "manuscript": {".bib", ".css", ".html", ".json", ".md", ".pdf"},
    "resources": {".cff", ".csv", ".json", ".md", ".pdf", ".png", ".py", ".sha256", ".txt"},
    "docs": {".css", ".html", ".json", ".md", ".png", ".svg", ".txt"},
    "schemas": {".json", ".md"},
    "scripts": {".py"},
    "src": {".py"},
    "tests": {".py"},
    "tools": {".py"},
}
TEXT_SUFFIXES = {
    "",
    ".bib",
    ".cff",
    ".css",
    ".csv",
    ".in",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
PRIVATE_PATTERNS = {
    "local Windows path": re.compile(r"[A-Za-z]:\\", re.IGNORECASE),
    "local POSIX path": re.compile(r"(?:/Users/|/home/|/usr/share/)", re.IGNORECASE),
    "private location": re.compile(r"\b[A-Z][A-Za-z .'-]+,\s*(?:USA|United States)\b"),
    "placeholder contact": re.compile(
        r"^\s*(?:contact|correspondence)\s*[:=]\s*(?:TBD|TODO|pending|placeholder)\b",
        re.IGNORECASE | re.MULTILINE,
    ),
    "credential marker": re.compile(
        r"(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----|AKIA[0-9A-Z]{16})"
    ),
    "email address": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
}
PATTERN_FIXTURE_FILES = {
    "tools/build_documents.py",
    "tools/check_repository.py",
    "tools/inspect_pdf.py",
    "tests/test_document_contract.py",
    "tests/test_release_integrity.py",
}
ALLOWED_EVIDENCE = {
    "source_asserted",
    "hand_checked",
    "independently_reproduced",
    "mechanically_replayed",
    "kernel_verified",
    "externally_published",
}
ALLOWED_DISPOSITIONS = {
    "admit",
    "admit_with_qualification",
    "proposed_only",
    "deferred",
    "rejected",
}
RELEASE_METADATA_PNGS = {
    "figure_1_phase_reservoir_network.png",
    "figure_2_trap_memory_hysteresis.png",
    "figure_3_spectral_bottleneck.png",
    "figure_4_carbon_phase_relay.png",
    "figure_5_static_degeneracy_transient_resolution.png",
    "figure_6_topology_aware_inference.png",
    "figure_7_state_dependent_transport_feedback.png",
    "supplement_figure_S2_single_frequency_degeneracy.png",
    "supplement_figure_S3_multifrequency_localization.png",
    "supplement_figure_S4_frequency_response_amplitude.png",
    "supplement_figure_S5_frequency_response_phase.png",
}
WORKING_PAPER_ROOT = ROOT / "resources" / "earth-is-the-instrument" / "v0.1"
WORKING_PAPER_NAME = "ASTRA_Earth_Is_the_Instrument_Working_Paper_v0.1.pdf"
WORKING_PAPER_SHA256 = "d0eaf61661e69395a6f3895167abb55d7b801480391f672966d359194e9b46d0"
WORKING_PAPER_COVER_SHA256 = "815cf7cfa65145965093c6a4d82fce47a8663c9808775cdc8145cd300a18bd87"
WORKING_PAPER_FONT_NOTICES_SHA256 = (
    "5c1555ad05d23624ef81dba298876e88680f10c5c7251e58af78791f7b94f853"
)
FRAMEWORK_RESOURCE_ROOT = ROOT / "resources" / "earth-is-the-instrument" / "v0.3.0"
FRAMEWORK_RELEASE_PAYLOADS = {
    "ASTRA_Dual_Rent_Local_to_Global_Audit_Form_v0.3.0.pdf": (
        "62ee91f1d855fba12781e44aed8a5958b159508459bce53e5dc9eaefe48936ef"
    ),
    "ASTRA_Framework_v0.3.0_Dual_Rent_Arithmetic_Seams.zip": (
        "b2a1072c14f1afff43a161b57620cdd2f6ad19b03884e7b5d8fbdd023333e09d"
    ),
    "ASTRA_Framework_v0.3.0_Dual_Rent_Arithmetic_Seams.zip.sha256": (
        "9eab58be3a619e41d0675a78cb61c88d72de1470316d068e77197dcd3ed826ee"
    ),
    "ASTRA_Framework_v0.3.0_Dual_Rent_Arithmetic_Seams.zip.verify.txt": (
        "60ef6d22759cf5960a81248fab3f223fce1bbedb2b8719c199df4bdefee7c278"
    ),
    "ASTRA_Framework_v0.3.0_Earth_Is_The_Instrument.pdf": (
        "39c722bb8ace94a28b08aa92d0596cc5342b156d8da05ff00737f5f23b8319e1"
    ),
    "ASTRA_v0.3.0_Public_Ground_Reading.pdf": (
        "cc722b73741049440caaf307d0fbeee7b543755c53f8114a114b7adcef0e7c28"
    ),
    "ASTRA_v0.3.0_Verification_Report.pdf": (
        "a7c0f9b9b979ec6bc5aeb685aa3165a5d1c89a60f712573a5a1871cf2831b35e"
    ),
    "FONT_NOTICES.txt": "a4d44d9e3b473d1addd0957ece7fa5151ea21799f84828f9b43acd6d2d89d744",
    "PUBLICATION_AUDIT.md": "0baa79bac2bac4c2a1b3caaca305f8240a436a93d1fd856c481909ddab9e9cc1",
    "cover.png": "1f576806300e68d9ca9d747775d36ce544914c5954fd84e68796f4762b0ba304",
}
FRAMEWORK_RELEASE_ONLY = {
    "ASTRA_Framework_v0.3.0_Dual_Rent_Arithmetic_Seams.zip",
    "ASTRA_Framework_v0.3.0_Dual_Rent_Arithmetic_Seams.zip.sha256",
    "ASTRA_Framework_v0.3.0_Dual_Rent_Arithmetic_Seams.zip.verify.txt",
}
FRAMEWORK_RESOURCE_FILES = {
    name: digest
    for name, digest in FRAMEWORK_RELEASE_PAYLOADS.items()
    if name not in FRAMEWORK_RELEASE_ONLY
}
SECTOR_RESOURCE_ROOT = "resources/sector-complete-instrument/v0.1.0-alpha.1"
SECTOR_RESOURCE_FILES = (
    "CITATION.cff",
    "README.md",
    "LICENSE_MAP.md",
    "MANIFEST.sha256",
    "RELEASE_NOTES.md",
    "RELEASE_SPEC.json",
    "THIRD_PARTY_NOTICES.md",
    "change_log.md",
    "claim_ledger.csv",
    "package_metadata.json",
    "source_ledger.csv",
    "data/benchmark_config.json",
    "data/broken_duality_control.csv",
    "data/detector_noise_information.csv",
    "data/example_sector_complete_record.json",
    "data/finite_boundary_control.csv",
    "data/local_response_matrix.csv",
    "data/sector_complete_benchmark.json",
    "data/sector_complete_benchmark.json.sha256",
    "data/sector_complete_response_matrix.csv",
    "figures/contact_sheet.png",
    "figures/figure_00_sector_complete_workflow.png",
    "figures/figure_01_local_response_matrix.png",
    "figures/figure_02_sector_complete_response_matrix.png",
    "figures/figure_03_fisher_eigenvalues.png",
    "figures/figure_04_information_vs_detector_noise.png",
    "figures/figure_05_finite_boundary_control.png",
    "figures/figure_06_broken_duality_control.png",
    "figures/figure_07_local_classification_confusion.png",
    "figures/figure_08_sector_complete_classification_confusion.png",
    "figures/figure_09_four_generator_state_flow.png",
    "figures/figure_10_dark_matter_firewall.png",
    "schema/sector_complete_instrument.schema.json",
    "scripts/run_sector_complete_benchmark.py",
    "source/ASTRA_Sector_Complete_Instrument_Module_v0.1.0-alpha.1.md",
    "source/ASTRA_v0.3.2_Integration_Patch.md",
    "source/source_map.csv",
    "src/astra_sector_complete.py",
    "templates/dark_matter_hidden_sector_proposed_only.json",
    "tests/test_sector_complete.py",
    "verification/BINARY_REVIEW_STATUS.md",
    "verification/LOCAL_AUDIT.md",
    "verification/producer_acceptance_gate_matrix.csv",
    "verification/producer_verification_report.md",
)
FRAMEWORK_RESOURCE_COVER = "cover.png"
RESOURCE_PATH_ALLOWLIST = {
    "resources/README.md",
    f"resources/earth-is-the-instrument/v0.1/{WORKING_PAPER_NAME}",
    "resources/earth-is-the-instrument/v0.1/FONT_NOTICES.txt",
    "resources/earth-is-the-instrument/v0.1/README.md",
    "resources/earth-is-the-instrument/v0.1/SHA256SUMS.txt",
    "resources/earth-is-the-instrument/v0.1/cover.png",
    *(
        f"resources/earth-is-the-instrument/v0.3.0/{name}"
        for name in (
            *FRAMEWORK_RESOURCE_FILES,
            "ERRATA.md",
            "README.md",
            "SHA256SUMS.txt",
        )
    ),
    *(f"{SECTOR_RESOURCE_ROOT}/{name}" for name in SECTOR_RESOURCE_FILES),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_link_or_junction(path: Path) -> bool:
    junction_check = getattr(path, "is_junction", None)
    return path.is_symlink() or bool(junction_check and junction_check())


def public_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if not relative.parts:
            continue
        if relative.parts[0] in IGNORED_ROOTS:
            if len(relative.parts) == 1 and is_link_or_junction(path):
                raise RuntimeError(f"Unsafe symbolic link or junction: {relative.as_posix()}")
            continue
        if any(part in IGNORED_NAMES for part in relative.parts):
            continue
        if is_link_or_junction(path):
            raise RuntimeError(f"Unsafe symbolic link or junction: {relative.as_posix()}")
        if not path.is_file():
            continue
        if len(relative.parts) == 1:
            if relative.as_posix() not in ROOT_ALLOWLIST:
                raise RuntimeError(f"Unexpected root file: {relative.as_posix()}")
        else:
            parent = relative.parent.as_posix()
            matched = next(
                (
                    root
                    for root in DIRECTORY_RULES
                    if parent == root or parent.startswith(root + "/")
                ),
                None,
            )
            if matched is None or path.suffix.lower() not in DIRECTORY_RULES[matched]:
                raise RuntimeError(f"Unexpected repository path: {relative.as_posix()}")
            if matched == "resources" and relative.as_posix() not in RESOURCE_PATH_ALLOWLIST:
                raise RuntimeError(f"Unregistered supplemental resource: {relative.as_posix()}")
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(ROOT).as_posix())


def check_cache_boundaries() -> None:
    offenders: list[str] = []
    for current, directories, _ in os.walk(ROOT):
        current_path = Path(current)
        relative = current_path.relative_to(ROOT)
        if relative.parts and relative.parts[0] in DISPOSABLE_ROOTS:
            directories[:] = []
            continue
        for name in tuple(directories):
            if name in DISPOSABLE_ROOTS:
                directories.remove(name)
            elif name in FORBIDDEN_CACHE_NAMES:
                offenders.append((relative / name).as_posix())
                directories.remove(name)
    if offenders:
        raise RuntimeError(
            "Cache directories outside the disposable tmp root: " + ", ".join(sorted(offenders))
        )


def read_frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.DOTALL)
    if not match:
        raise RuntimeError(f"Missing YAML frontmatter: {path.relative_to(ROOT)}")
    yaml = YAML(typ="safe")
    return dict(yaml.load(match.group(1)))


class AccessibilityParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang = ""
        self.title_depth = 0
        self.title_text: list[str] = []
        self.images = 0
        self.images_with_alt = 0
        self.tables = 0
        self.table_captions = 0
        self.table_headers = 0
        self.table_column_headers = 0
        self.table_row_headers = 0
        self.math = 0
        self.main = 0
        self.nav = 0
        self.skip_link = 0
        self.links: list[str] = []
        self.external_resources: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "html":
            self.lang = values.get("lang") or ""
        elif tag == "title":
            self.title_depth += 1
        elif tag == "img":
            self.images += 1
            if (values.get("alt") or "").strip() and (values.get("aria-label") or "").strip():
                self.images_with_alt += 1
            source = values.get("src") or ""
            if not source.startswith("data:image/"):
                self.external_resources.append(source)
        elif tag == "table":
            self.tables += 1
        elif tag == "caption":
            self.table_captions += 1
        elif tag == "th":
            self.table_headers += 1
            if values.get("scope") == "col":
                self.table_column_headers += 1
            elif values.get("scope") == "row":
                self.table_row_headers += 1
        elif tag == "math":
            self.math += 1
        elif tag == "main":
            self.main += 1
        elif tag == "nav" and values.get("role") == "doc-toc":
            self.nav += 1
        elif tag == "a":
            href = values.get("href") or ""
            self.links.append(href)
            if values.get("class") == "skip-link" and href == "#main-content":
                self.skip_link += 1
        elif tag in {"link", "script"}:
            source = values.get("href") or values.get("src") or ""
            if source and not source.startswith(("data:", "#")):
                self.external_resources.append(source)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self.title_depth:
            self.title_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.title_depth:
            self.title_text.append(data)


def check_html(path: Path, expected_title: str) -> None:
    text = path.read_text(encoding="utf-8")
    parser = AccessibilityParser()
    parser.feed(text)
    title = " ".join("".join(parser.title_text).split())
    failures = []
    if parser.lang != "en-US":
        failures.append("lang is not en-US")
    if expected_title not in title:
        failures.append(f"unexpected title {title!r}")
    if parser.images < 1 or parser.images_with_alt != parser.images:
        failures.append(f"image alt/aria coverage {parser.images_with_alt}/{parser.images}")
    if parser.tables and parser.table_captions != parser.tables:
        failures.append(f"table caption count {parser.table_captions} for {parser.tables} tables")
    if parser.tables and parser.table_column_headers < parser.tables:
        failures.append(
            f"scoped column-header count {parser.table_column_headers} for {parser.tables} tables"
        )
    if parser.tables and parser.table_row_headers < parser.tables:
        failures.append(
            f"scoped row-header count {parser.table_row_headers} for {parser.tables} tables"
        )
    if parser.math < 1:
        failures.append("no structured MathML")
    if parser.main != 1 or parser.nav != 1 or parser.skip_link != 1:
        failures.append(f"landmarks main={parser.main} nav={parser.nav} skip={parser.skip_link}")
    if parser.external_resources:
        failures.append(f"non-embedded resources: {parser.external_resources[:3]}")
    for href in parser.links:
        if not href:
            continue
        parsed = urlparse(href)
        if parsed.scheme and parsed.scheme not in {"http", "https"}:
            failures.append(f"unsafe link scheme: {href}")
    if PRIVATE_PATTERNS["local Windows path"].search(text) or PRIVATE_PATTERNS[
        "local POSIX path"
    ].search(text):
        failures.append("machine-local path")
    if failures:
        raise RuntimeError(f"HTML accessibility check failed for {path.name}: {failures}")


def check_png_metadata(paths: list[Path]) -> None:
    for path in paths:
        if path.suffix.lower() != ".png":
            continue
        with Image.open(path) as image:
            text_metadata = json.dumps(image.info, default=str, ensure_ascii=False)
        for label, pattern in PRIVATE_PATTERNS.items():
            if pattern.search(text_metadata):
                raise RuntimeError(f"{label} in PNG metadata: {path.relative_to(ROOT)}")


def check_working_paper_resource() -> None:
    resource_index = ROOT / "resources" / "README.md"
    pdf_path = WORKING_PAPER_ROOT / WORKING_PAPER_NAME
    cover_path = WORKING_PAPER_ROOT / "cover.png"
    font_notices_path = WORKING_PAPER_ROOT / "FONT_NOTICES.txt"
    readme_path = WORKING_PAPER_ROOT / "README.md"
    sums_path = WORKING_PAPER_ROOT / "SHA256SUMS.txt"
    expected_roster = {
        pdf_path.name,
        cover_path.name,
        font_notices_path.name,
        readme_path.name,
        sums_path.name,
    }

    if not resource_index.is_file() or not WORKING_PAPER_ROOT.is_dir():
        raise RuntimeError("Working-paper resource collection is incomplete")
    observed_roster = {
        path.relative_to(WORKING_PAPER_ROOT).as_posix()
        for path in WORKING_PAPER_ROOT.rglob("*")
        if path.is_file()
    }
    if observed_roster != expected_roster:
        raise RuntimeError(
            "Working-paper file roster differs from its contract: "
            f"expected {sorted(expected_roster)}, observed {sorted(observed_roster)}"
        )

    expected_sums = (
        f"{WORKING_PAPER_SHA256}  {WORKING_PAPER_NAME}\n"
        f"{WORKING_PAPER_FONT_NOTICES_SHA256}  FONT_NOTICES.txt\n"
        f"{WORKING_PAPER_COVER_SHA256}  cover.png\n"
    )
    if sums_path.read_text(encoding="utf-8") != expected_sums:
        raise RuntimeError("Working-paper checksum sidecar is not canonical")
    if sha256(pdf_path) != WORKING_PAPER_SHA256:
        raise RuntimeError("Working-paper PDF checksum mismatch")
    if sha256(cover_path) != WORKING_PAPER_COVER_SHA256:
        raise RuntimeError("Working-paper cover checksum mismatch")
    if sha256(font_notices_path) != WORKING_PAPER_FONT_NOTICES_SHA256:
        raise RuntimeError("Working-paper font-notices checksum mismatch")

    with Image.open(cover_path) as cover:
        if cover.size != (480, 622) or cover.mode != "RGB":
            raise RuntimeError(
                f"Working-paper cover contract mismatch: size={cover.size}, mode={cover.mode}"
            )

    reader = PdfReader(pdf_path)
    if len(reader.pages) != 44:
        raise RuntimeError(f"Working-paper page count is {len(reader.pages)}, expected 44")
    expected_labels = ["Cover", "i", "ii", "iii", "iv", *map(str, range(1, 40))]
    if reader.page_labels != expected_labels:
        raise RuntimeError("Working-paper page labels do not match the visible numbering")

    metadata = reader.metadata
    expected_metadata = {
        "/Title": "Earth Is the Instrument",
        "/Subject": "Plate tectonics, geological memory, boundary states, and human origins",
        "/Author": "ASTRA Framework Working Paper",
        "/Creator": "ASTRA Framework Working Paper 0.1",
        "/Producer": "SPPT/ASTRA supplemental publication pipeline",
        "/CreationDate": "D:20260804000000Z",
        "/ModDate": "D:20260805000000Z",
    }
    if metadata is None or any(
        metadata.get(key) != value for key, value in expected_metadata.items()
    ):
        raise RuntimeError("Working-paper PDF metadata differs from the publication contract")
    root = reader.root_object
    if str(root.get("/Lang")) != "en-US":
        raise RuntimeError("Working-paper PDF language is not en-US")
    preferences = root.get("/ViewerPreferences")
    preferences = preferences.get_object() if hasattr(preferences, "get_object") else preferences
    if preferences is None or not bool(preferences.get("/DisplayDocTitle")):
        raise RuntimeError("Working-paper PDF does not display its document title")
    if "/StructTreeRoot" in root or "/MarkInfo" in root:
        raise RuntimeError("Working-paper accessibility statement is stale: PDF is now tagged")

    open_action = root.get("/OpenAction")
    open_action = open_action.get_object() if hasattr(open_action, "get_object") else open_action
    if (
        not isinstance(open_action, list)
        or len(open_action) != 2
        or str(open_action[1]) != "/Fit"
        or reader.get_page_number(open_action[0].get_object()) != 0
    ):
        raise RuntimeError("Working-paper opening action is not the safe first-page fit view")
    if reader.get_fields() is not None or list(reader.attachments):
        raise RuntimeError("Working-paper PDF contains forms or embedded attachments")

    dangerous_keys = {"/AA", "/JS", "/JavaScript", "/Launch", "/RichMedia"}
    dangerous_actions = {"/GoToE", "/GoToR", "/ImportData", "/JavaScript", "/Launch", "/SubmitForm"}
    seen: set[int] = set()

    def walk_pdf_objects(value: object):
        resolved = value.get_object() if hasattr(value, "get_object") else value
        identifier = id(resolved)
        if identifier in seen:
            return
        seen.add(identifier)
        if isinstance(resolved, dict):
            yield resolved
            for child in resolved.values():
                yield from walk_pdf_objects(child)
        elif isinstance(resolved, (list, tuple)):
            for child in resolved:
                yield from walk_pdf_objects(child)

    for mapping in walk_pdf_objects(root):
        present = dangerous_keys.intersection(map(str, mapping.keys()))
        if present:
            raise RuntimeError(f"Working-paper PDF contains unsafe keys: {sorted(present)}")
        action = str(mapping.get("/S", ""))
        if action in dangerous_actions:
            raise RuntimeError(f"Working-paper PDF contains unsafe action: {mapping.get('/S')}")
        if action == "/URI":
            target = str(mapping.get("/URI", ""))
            parsed_target = urlparse(target)
            if (
                parsed_target.scheme != "https"
                or parsed_target.hostname not in {"doi.org", "volcanoes.usgs.gov"}
                or parsed_target.username is not None
                or parsed_target.password is not None
            ):
                raise RuntimeError(f"Working-paper PDF contains an unsafe URI: {target}")

    expected_destinations = {
        "section.2.3": (9, 59.76, 732.24),
        "section.3.2": (12, 59.76, 732.24),
        "section.4.2": (16, 59.76, 732.24),
        "section.4.4": (17, 59.76, 732.24),
        "section.6.1": (22, 59.76, 732.24),
        "section.7.2": (24, 59.76, 732.24),
        "section.8.1": (27, 59.76, 732.24),
        "section.8.4": (29, 59.76, 732.24),
        "section.9.2": (31, 59.76, 732.24),
        "table.0.1": (2, 59.76, 465.96),
    }
    observed_destinations = {
        name: (
            reader.get_destination_page_number(reader.named_destinations[name]),
            round(float(reader.named_destinations[name].left), 2),
            round(float(reader.named_destinations[name].top), 2),
        )
        for name in expected_destinations
        if name in reader.named_destinations
    }
    if observed_destinations != expected_destinations:
        raise RuntimeError(
            "Working-paper corrected destinations differ from the contract: "
            f"{observed_destinations}"
        )

    def flatten_outline(entries: list[object]):
        for entry in entries:
            if isinstance(entry, list):
                yield from flatten_outline(entry)
            else:
                yield entry

    epistemic_items = [
        item
        for item in flatten_outline(reader.outline)
        if getattr(item, "title", "") == "Epistemic vocabulary"
    ]
    if len(epistemic_items) != 1 or reader.get_destination_page_number(epistemic_items[0]) != 2:
        raise RuntimeError("Working-paper Epistemic vocabulary bookmark is premature")

    extracted_pages = [page.extract_text() or "" for page in reader.pages]
    if any(not text.strip() for text in extracted_pages):
        raise RuntimeError("Working-paper PDF has a page without extractable text")
    privacy_text = "\n".join(extracted_pages) + "\n" + json.dumps(dict(metadata))
    for label, pattern in PRIVATE_PATTERNS.items():
        if pattern.search(privacy_text):
            raise RuntimeError(f"{label} in working-paper text or metadata")

    readme = readme_path.read_text(encoding="utf-8")
    semantic_readme = " ".join(readme.replace("**", "").split())
    required_readme_values = (
        "supplemental exploratory working paper",
        "not peer reviewed",
        "does not amend or supersede SPPT/ASTRA v1.0.6",
        "not a tagged PDF",
        "Figure descriptions",
        "available by August 2026",
        "no reuse license is asserted",
        "explicitly authorized its public distribution",
        "Project-level provenance",
        "substantive ChatGPT assistance",
        "Kansas motto",
        "project is independent and unaffiliated",
        "No independent rights or provenance claim",
        "FONT_NOTICES.txt",
        "Inter",
        "EB Garamond",
        "Latin Modern Math",
        "DejaVu Sans",
        "SIL Open Font License 1.1",
        "GUST Font License",
        "ASTRA Framework Working Paper. (2026).",
        "ASTRA_Earth_Is_The_Instrument_Working_Paper_0.1_cover_geometry_fixed.pdf",
        "480 by 622 pixel rendering",
        "issues/new?template=accessibility.yml",
        "releases/tag/earth-instrument-wp-0.1",
        WORKING_PAPER_SHA256,
        "1982d988981e046ed3b083835144fb83d4e98b2dca92454903472c265f4e7220",
    )
    if any(value not in semantic_readme for value in required_readme_values):
        raise RuntimeError("Working-paper reading guide omits a required publication boundary")
    figure_labels = (
        "Seven 2026 signals:",
        "Plate-boundary classes:",
        "Distributed geological nursery:",
        "Boundary-state ladder:",
        "Geology as archive and censor:",
        "Monuments as reorganized geology:",
        "Candidate origin stories:",
        "ASTRA instrument test:",
    )
    if any(label not in semantic_readme for label in figure_labels):
        raise RuntimeError("Working-paper guide does not describe all eight figures")
    forbidden_readme_claims = (
        "fully accessible PDF",
        "empirically validates SPPT/ASTRA",
        "amends SPPT/ASTRA v1.0.6",
        "supersedes SPPT/ASTRA v1.0.6",
    )
    if any(claim in semantic_readme for claim in forbidden_readme_claims):
        raise RuntimeError("Working-paper guide contains a contradictory publication claim")

    collection_index = " ".join(resource_index.read_text(encoding="utf-8").split())
    if (
        "earth-is-the-instrument/v0.1/" not in collection_index
        or "does not replace, revise, or supersede the current" not in collection_index
        or "inherit its verification status" not in collection_index
    ):
        raise RuntimeError("Supplemental resource index omits the working-paper boundary")

    font_notices = font_notices_path.read_text(encoding="utf-8")
    required_font_notices = (
        "Copyright (c) 2016 The Inter Project Authors",
        "Copyright 2010-2013 Georg A. Duffner",
        "Copyright 2012--2014 for Latin Modern Math OTF",
        "SIL OPEN FONT LICENSE Version 1.1",
        "GUST FONT LICENSE preliminary version - 2006-09-30",
        "licenses/DEJAVU-FONTS.txt",
    )
    if any(value not in font_notices for value in required_font_notices):
        raise RuntimeError("Working-paper font notices are incomplete")

    license_map = (ROOT / "LICENSE_MAP.md").read_text(encoding="utf-8")
    required_license_boundaries = (
        "It does not\nassert copyright ownership of separately supplied resources",
        f"resources/earth-is-the-instrument/v0.1/{WORKING_PAPER_NAME}",
        "resources/earth-is-the-instrument/v0.1/cover.png",
        "resources/earth-is-the-instrument/v0.1/FONT_NOTICES.txt",
        "no reuse license is asserted",
    )
    if any(value not in license_map for value in required_license_boundaries):
        raise RuntimeError("License map omits the working-paper rights boundary")


def check_framework_v030_resource() -> None:
    readme_path = FRAMEWORK_RESOURCE_ROOT / "README.md"
    sums_path = FRAMEWORK_RESOURCE_ROOT / "SHA256SUMS.txt"
    expected_roster = {
        *FRAMEWORK_RESOURCE_FILES,
        FRAMEWORK_RESOURCE_COVER,
        "ERRATA.md",
        readme_path.name,
        sums_path.name,
    }

    if not FRAMEWORK_RESOURCE_ROOT.is_dir():
        raise RuntimeError("ASTRA Framework v0.3.0 resource directory is missing")
    observed_roster = {
        path.relative_to(FRAMEWORK_RESOURCE_ROOT).as_posix()
        for path in FRAMEWORK_RESOURCE_ROOT.rglob("*")
        if path.is_file()
    }
    if observed_roster != expected_roster:
        raise RuntimeError(
            "ASTRA Framework v0.3.0 file roster differs from its contract: "
            f"expected {sorted(expected_roster)}, observed {sorted(observed_roster)}"
        )

    expected_sums = "".join(
        f"{digest}  {name}\n" for name, digest in FRAMEWORK_RELEASE_PAYLOADS.items()
    )
    if sums_path.read_text(encoding="utf-8") != expected_sums:
        raise RuntimeError("ASTRA Framework v0.3.0 checksum sidecar is not canonical")
    if len(FRAMEWORK_RELEASE_PAYLOADS) != 10:
        raise RuntimeError("ASTRA Framework v0.3.0 release payload roster must contain ten files")
    for name, expected_digest in FRAMEWORK_RESOURCE_FILES.items():
        if sha256(FRAMEWORK_RESOURCE_ROOT / name) != expected_digest:
            raise RuntimeError(f"ASTRA Framework v0.3.0 checksum mismatch: {name}")

    with Image.open(FRAMEWORK_RESOURCE_ROOT / FRAMEWORK_RESOURCE_COVER) as cover:
        width, height = cover.size
        if (
            min(width, height) < 480
            or abs((width / height) - (612 / 792)) > 0.002
            or cover.mode not in {"RGB", "RGBA"}
        ):
            raise RuntimeError(
                "ASTRA Framework v0.3.0 cover contract mismatch: "
                f"size={cover.size}, mode={cover.mode}"
            )

    expected_pdf_pages = {
        "ASTRA_Dual_Rent_Local_to_Global_Audit_Form_v0.3.0.pdf": 1,
        "ASTRA_Framework_v0.3.0_Earth_Is_The_Instrument.pdf": 171,
        "ASTRA_v0.3.0_Public_Ground_Reading.pdf": 2,
        "ASTRA_v0.3.0_Verification_Report.pdf": 3,
    }
    pdf_texts: dict[str, str] = {}
    for name, expected_pages in expected_pdf_pages.items():
        reader = PdfReader(FRAMEWORK_RESOURCE_ROOT / name)
        if len(reader.pages) != expected_pages:
            raise RuntimeError(
                f"ASTRA Framework v0.3.0 page count mismatch for {name}: "
                f"{len(reader.pages)} != {expected_pages}"
            )
        if str(reader.root_object.get("/Lang")) != "en-US":
            raise RuntimeError(f"ASTRA Framework v0.3.0 PDF language is not en-US: {name}")
        if "/StructTreeRoot" not in reader.root_object:
            raise RuntimeError(f"ASTRA Framework v0.3.0 PDF is not tagged: {name}")
        if reader.get_fields() is not None or list(reader.attachments):
            raise RuntimeError(f"ASTRA Framework v0.3.0 PDF contains forms or attachments: {name}")
        extracted_pages = [page.extract_text() or "" for page in reader.pages]
        pdf_texts[name] = "\n".join(extracted_pages)
        if any(not text.strip() for text in extracted_pages):
            raise RuntimeError(f"ASTRA Framework v0.3.0 PDF has an empty text page: {name}")
        privacy_text = "\n".join(extracted_pages) + "\n" + json.dumps(dict(reader.metadata or {}))
        for label, pattern in PRIVATE_PATTERNS.items():
            if pattern.search(privacy_text):
                raise RuntimeError(
                    f"{label} in ASTRA Framework v0.3.0 PDF text or metadata: {name}"
                )

    main_text = pdf_texts["ASTRA_Framework_v0.3.0_Earth_Is_The_Instrument.pdf"]
    if "Language-model assistance" not in main_text or "Authorial responsibility" not in main_text:
        raise RuntimeError("ASTRA Framework v0.3.0 main PDF omits its AI/responsibility disclosure")
    for name in (
        "ASTRA_Dual_Rent_Local_to_Global_Audit_Form_v0.3.0.pdf",
        "ASTRA_v0.3.0_Public_Ground_Reading.pdf",
        "ASTRA_v0.3.0_Verification_Report.pdf",
    ):
        if "Language-model assistance" in pdf_texts[name]:
            raise RuntimeError(
                f"ASTRA Framework v0.3.0 companion unexpectedly claims an AI disclosure: {name}"
            )

    readme = readme_path.read_text(encoding="utf-8")
    semantic_readme = " ".join(readme.replace("**", "").split())
    required_readme_values = (
        "foundational working paper",
        "not peer reviewed",
        "supersedes the internal v0.2.1 predecessor preserved inside its release archive",
        "no public v0.2.1 tag or GitHub Release was created",
        "does not amend or supersede the immutable SPPT/ASTRA v1.0.6",
        "24 PASS, 2 PARTIAL, and 0 FAIL",
        "internal release audit, not external scientific review or endorsement",
        "not claimed as PDF/UA-conformant or fully accessible",
        "29 isolated regression tests",
        "90 of 90 checks",
        "does not freeze a complete TeX environment",
        "without publishing private object identifiers",
        "bounded certificates",
        "not empirical validation of SPPT/ASTRA",
        "substantive assistance from OpenAI's ChatGPT",
        "Ad Astra Per Aspera",
        'internal version of Astra as "our next major model"',
        "not affiliated with, sponsored by, endorsed by, reviewed by, operated by, or produced for OpenAI",
        "role-based review architecture, not a separate institution",
        "The main framework PDF discloses language-model assistance",
        "The three compact companion PDFs do not carry that disclosure",
        "post-publication errata",
        "b2a1072c14f1afff43a161b57620cdd2f6ad19b03884e7b5d8fbdd023333e09d",
        "earth-instrument-framework-v0.3.0",
        "issues/new/choose",
    )
    if any(value not in semantic_readme for value in required_readme_values):
        raise RuntimeError("ASTRA Framework v0.3.0 guide omits a publication boundary")
    if "The four preserved PDFs already disclose" in semantic_readme:
        raise RuntimeError("ASTRA Framework v0.3.0 guide overstates PDF-level AI disclosures")

    errata = " ".join(
        (FRAMEWORK_RESOURCE_ROOT / "ERRATA.md")
        .read_text(encoding="utf-8")
        .replace("**", "")
        .split()
    )
    for value in (
        "The 171-page main framework PDF contains that disclosure",
        "The public ground reading, audit form, and verification report do not",
        "No public v0.2.1 tag or GitHub Release was created",
        "does not replace, edit, or reissue any PDF, archive member, checksum, tag, or release asset",
    ):
        if value not in errata:
            raise RuntimeError(f"ASTRA Framework v0.3.0 errata omit: {value}")

    resource_index = " ".join(
        (ROOT / "resources" / "README.md").read_text(encoding="utf-8").split()
    )
    if (
        "earth-is-the-instrument/v0.3.0/" not in resource_index
        or "does not replace, revise, or supersede the current SPPT/ASTRA" not in resource_index
    ):
        raise RuntimeError("Supplemental resource index omits the v0.3.0 boundary")

    license_map = (ROOT / "LICENSE_MAP.md").read_text(encoding="utf-8")
    for name in FRAMEWORK_RESOURCE_FILES:
        if f"resources/earth-is-the-instrument/v0.3.0/{name}" not in license_map:
            raise RuntimeError(f"License map omits ASTRA Framework v0.3.0 file: {name}")
    if "resources/earth-is-the-instrument/v0.3.0/ERRATA.md" not in license_map:
        raise RuntimeError("License map omits ASTRA Framework v0.3.0 errata")


def check_publication_map() -> None:
    readme = " ".join((ROOT / "README.md").read_text(encoding="utf-8").replace("**", "").split())
    required_readme_values = (
        "Publication map",
        "v1.0.6 — current reference edition",
        "v0.3.0 — current supplemental edition",
        "v0.1 — historical edition",
        "The bare `/latest/` route and repository-level `CITATION.cff` refer only to the SPPT/ASTRA reference line",
        "resources/earth-is-the-instrument/latest/",
        "resources/earth-is-the-instrument/v0.3.0/ground-reading/",
        "resources/earth-is-the-instrument/v0.3.0/audit-form/",
        "earth-instrument-framework-v0.3.0",
        "earth-instrument-wp-0.1",
        "supersedes the internal v0.2.1 predecessor preserved in its release archive",
        "No public v0.2.1 tag or GitHub Release was created",
        "core reference tags matching `v*`",
    )
    for value in required_readme_values:
        if value not in readme:
            raise RuntimeError(f"Root publication map omits: {value}")
    if "| Publication track |" in readme:
        raise RuntimeError("Root publication map regressed to a wide narrow-screen table")

    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    for heading in (
        "## Earth Is the Instrument framework 0.3.0 — 2026-08-06",
        "## Earth Is the Instrument working paper 0.1 — 2026-08-05",
        "## 1.0.6 — 2026-08-02",
    ):
        if heading not in changelog:
            raise RuntimeError(f"Changelog omits released publication section: {heading}")
    unreleased = changelog.split("## Earth Is the Instrument framework 0.3.0", 1)[0]
    if (
        "Adds *ASTRA Framework v0.3.0" in unreleased
        or "Publishes *Earth Is the Instrument* Working Paper 0.1" in unreleased
    ):
        raise RuntimeError("Published supplemental releases remain under Unreleased")

    notes = {
        "earth-instrument-framework-v0.3.0": (
            ROOT / "RELEASE_NOTES_earth-instrument-framework-v0.3.0.md",
            "3c0392e12230e9415f5a40ae6008dd498291d67b366898e97bd8b0a04fe099c5",
        ),
        "earth-instrument-wp-0.1": (
            ROOT / "RELEASE_NOTES_earth-instrument-wp-0.1.md",
            "8e53a4bec211af4a1ebe8df1c2ae15f49213649b445c0a2b64b392c4c9131aba",
        ),
    }
    note_texts: dict[str, str] = {}
    for tag, (path, expected_body_digest) in notes.items():
        text = path.read_text(encoding="utf-8")
        if "Archived immutable release-body record" not in text or tag not in text:
            raise RuntimeError(f"Archived supplemental release body is incomplete: {path.name}")
        try:
            body = (
                text.split("<!-- BEGIN IMMUTABLE RELEASE BODY -->", 1)[1]
                .split("<!-- END IMMUTABLE RELEASE BODY -->", 1)[0]
                .strip()
            )
        except IndexError as error:
            raise RuntimeError(
                f"Archived release-body markers are incomplete: {path.name}"
            ) from error
        if hashlib.sha256(body.encode("utf-8")).hexdigest() != expected_body_digest:
            raise RuntimeError(f"Archived immutable release body changed: {path.name}")
        note_texts[tag] = text
    if "post-publication errata" not in note_texts["earth-instrument-framework-v0.3.0"]:
        raise RuntimeError("v0.3.0 release-body archive omits its erratum link")
    if "project-level disclosure" not in note_texts["earth-instrument-wp-0.1"]:
        raise RuntimeError("v0.1 release-body archive omits the current provenance disclosure")

    evidence_readme = (ROOT / "evidence" / "README.md").read_text(encoding="utf-8")
    if (
        "v1.0.6 reference package" not in evidence_readme
        or "--all --workers 4" not in evidence_readme
    ):
        raise RuntimeError("Evidence README does not identify the core release and command")
    schemas_readme = (ROOT / "schemas" / "README.md").read_text(encoding="utf-8")
    if (
        "currently **v1.0.6**" not in schemas_readme
        or "Supplemental resources" not in schemas_readme
    ):
        raise RuntimeError("Schema README does not identify its publication-line scope")


def check_text_privacy(paths: list[Path]) -> None:
    for path in paths:
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if path.relative_to(ROOT).as_posix() in PATTERN_FIXTURE_FILES:
            continue
        text = path.read_text(encoding="utf-8").replace(
            "307349551+jkolantree@users.noreply.github.com", "PUBLIC_GITHUB_NOREPLY"
        )
        for label, pattern in PRIVATE_PATTERNS.items():
            if pattern.search(text):
                raise RuntimeError(f"{label} in {path.relative_to(ROOT).as_posix()}")


def check_license_map(paths: list[Path]) -> None:
    license_map = (ROOT / "LICENSE_MAP.md").read_text(encoding="utf-8")
    if "CC0-like" in license_map:
        raise RuntimeError("License map contains an undefined CC0-like label")
    for required_embedded_rights_statement in (
        "The `manuscript/**` CC BY 4.0 mapping applies only to original authored content.",
        "Embedded DejaVu, Bitstream Vera, and Arev components retain the third-party terms",
        "embedded STIX components retain the SIL Open Font License 1.1 terms",
        "No proprietary or machine-installed font file or subset is distributed",
    ):
        if required_embedded_rights_statement not in license_map:
            raise RuntimeError(
                "License map omits embedded-font rights qualification: "
                f"{required_embedded_rights_statement}"
            )
    rows: list[tuple[list[str], str]] = []
    for line in license_map.splitlines():
        if not line.startswith("| `"):
            continue
        cells = line.split("|")
        if len(cells) < 4:
            raise RuntimeError(f"Malformed license-map row: {line}")
        patterns = re.findall(r"`([^`]+)`", cells[1])
        license_label = cells[2].strip()
        if not patterns or not license_label:
            raise RuntimeError(f"Incomplete license-map row: {line}")
        rows.append((patterns, license_label))

    def matches(relative: str, pattern: str) -> bool:
        if pattern.endswith("/**"):
            return relative.startswith(pattern[:-3] + "/")
        return fnmatch.fnmatchcase(relative, pattern)

    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        matched = [
            license_label
            for patterns, license_label in rows
            if any(matches(relative, pattern) for pattern in patterns)
        ]
        if len(matched) != 1:
            raise RuntimeError(
                f"Public file must have exactly one explicit license mapping: {relative}; "
                f"observed {matched}"
            )


def check_metadata_agreement() -> None:
    spec = json.loads((ROOT / "RELEASE_SPEC.json").read_text(encoding="utf-8"))
    version = str(spec["version"])
    tag = str(spec["tag"])
    if not re.fullmatch(r"\d+\.\d+\.\d+", version) or tag != f"v{version}":
        raise RuntimeError("RELEASE_SPEC.json version and tag disagree")
    release_date = date.fromisoformat(str(spec["release_date"]))
    build_epoch = str(spec["build_epoch"])
    expected_build_epoch = f"{release_date.isoformat()}T00:00:00Z"
    if build_epoch != expected_build_epoch:
        raise RuntimeError("Release build epoch must be midnight UTC on the release date")
    parsed_epoch = datetime.strptime(build_epoch, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    if type(spec.get("build_epoch_unix")) is not int or spec["build_epoch_unix"] != int(
        parsed_epoch.timestamp()
    ):
        raise RuntimeError("Release ISO and Unix build epochs disagree")
    if type(spec.get("repository_id")) is not int or spec["repository_id"] <= 0:
        raise RuntimeError("RELEASE_SPEC.json requires a positive GitHub repository ID")
    expected_release_names = [
        f"SPPT_ASTRA_preprint_v{version}.pdf",
        f"SPPT_ASTRA_preprint_v{version}.html",
        f"SPPT_ASTRA_technical_supplement_v{version}.pdf",
        f"SPPT_ASTRA_technical_supplement_v{version}.html",
        f"SPPT_ASTRA_v{version}_source.tar.gz",
        "SHA256SUMS",
        f"release-identity-v{version}.json",
    ]
    if spec.get("release_asset_allowlist") != expected_release_names:
        raise RuntimeError("Release asset names are not exactly bound to the release version")

    yaml = YAML(typ="safe")
    citation = yaml.load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))
    manuscript = read_frontmatter(ROOT / "manuscript" / "manuscript.md")
    supplement = read_frontmatter(ROOT / "manuscript" / "supplement.md")
    expected = {
        "title": spec["title"],
        "version": version,
        "author": spec["author"],
        "date": f"{release_date.day} {release_date:%B %Y}",
    }
    for source_name, source in (("manuscript", manuscript), ("supplement", supplement)):
        for key in ("version", "author", "date"):
            if str(source.get(key)) != expected[key]:
                raise RuntimeError(f"{source_name} metadata mismatch for {key}")
    if str(manuscript.get("title")) != expected["title"]:
        raise RuntimeError("Manuscript title differs from RELEASE_SPEC.json")
    if citation["title"] != expected["title"] or str(citation["version"]) != expected["version"]:
        raise RuntimeError("CITATION.cff title/version mismatch")
    if str(citation["date-released"]) != spec["release_date"]:
        raise RuntimeError("CITATION.cff release date mismatch")
    if citation["authors"] != [{"name": expected["author"]}]:
        raise RuntimeError("CITATION.cff pseudonymous author mismatch")
    if citation["repository-code"] != spec["repository"] or citation["license"] != "MIT":
        raise RuntimeError("CITATION.cff repository/license mismatch")
    release_url = f"{spec['repository']}/releases/tag/{tag}"
    if citation.get("url") != release_url:
        raise RuntimeError("CITATION.cff top-level URL is not bound to the release tag")
    preferred = citation.get("preferred-citation", {})
    if str(preferred.get("version")) != version or preferred.get("url") != release_url:
        raise RuntimeError("CITATION.cff preferred citation is not bound to the release tag")

    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    if str(project["project"].get("version")) != version:
        raise RuntimeError("pyproject.toml version differs from RELEASE_SPEC.json")
    inventory = json.loads((ROOT / "SOURCE_INVENTORY.json").read_text(encoding="utf-8"))
    if str(inventory.get("authority", {}).get("version")) != version:
        raise RuntimeError("Source-inventory authority version differs from RELEASE_SPEC.json")
    matrix = json.loads((ROOT / "CLAIM_MATRIX.json").read_text(encoding="utf-8"))
    if matrix.get("title") != f"SPPT/ASTRA v{version} consequential claim-admission matrix":
        raise RuntimeError("Claim-matrix title differs from RELEASE_SPEC.json")

    notes_path = ROOT / f"RELEASE_NOTES_v{version}.md"
    if not notes_path.is_file():
        raise RuntimeError(f"Current release notes are missing: {notes_path.name}")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    expected_documents = (
        f"manuscript/SPPT_ASTRA_preprint_v{version}.html",
        f"manuscript/SPPT_ASTRA_preprint_v{version}.pdf",
        f"manuscript/SPPT_ASTRA_technical_supplement_v{version}.html",
        f"manuscript/SPPT_ASTRA_technical_supplement_v{version}.pdf",
    )
    edition_pattern = re.compile(
        r"SPPT_ASTRA_(?:preprint|technical_supplement)_v\d+\.\d+\.\d+\.(?:html|pdf)"
    )
    observed_editions = {
        path.name
        for path in (ROOT / "manuscript").iterdir()
        if path.is_file() and edition_pattern.fullmatch(path.name)
    }
    expected_edition_names = {Path(relative).name for relative in expected_documents}
    if observed_editions != expected_edition_names:
        raise RuntimeError(
            "Versioned manuscript edition roster differs from the current release: "
            f"expected {sorted(expected_edition_names)}, observed {sorted(observed_editions)}"
        )
    pages_root = "https://jkolantree.github.io/astra"
    required_readme_values = (
        *expected_documents,
        release_url,
        f"{pages_root}/{tag}/preprint/",
        f"{pages_root}/{tag}/supplement/",
    )
    if any(value not in readme for value in required_readme_values):
        raise RuntimeError("README current-release links differ from RELEASE_SPEC.json")

    identity = json.loads(
        (ROOT / "manuscript" / "document_semantic_identity.json").read_text(encoding="utf-8")
    )
    if identity.get("build_epoch") != build_epoch or len(identity.get("records", [])) != 2:
        raise RuntimeError("Document semantic identity differs from RELEASE_SPEC.json")
    expected_editions = {
        "manuscript.md": (
            f"SPPT_ASTRA_preprint_v{version}.html",
            f"SPPT_ASTRA_preprint_v{version}.pdf",
        ),
        "supplement.md": (
            f"SPPT_ASTRA_technical_supplement_v{version}.html",
            f"SPPT_ASTRA_technical_supplement_v{version}.pdf",
        ),
    }
    for record in identity["records"]:
        expected_files = expected_editions.get(record.get("source"))
        if expected_files is None or (
            str(record.get("version")) != version
            or record.get("author") != expected["author"]
            or (record.get("html"), record.get("pdf")) != expected_files
        ):
            raise RuntimeError("Document semantic-identity record differs from release metadata")

    expected_png_software = f"SPPT-ASTRA reproducibility build v{version}"
    for filename in sorted(RELEASE_METADATA_PNGS):
        with Image.open(ROOT / "figures" / filename) as image:
            if image.info.get("Software") != expected_png_software:
                raise RuntimeError(f"Figure release metadata drift: {filename}")


def check_claim_matrix() -> None:
    matrix = json.loads((ROOT / "CLAIM_MATRIX.json").read_text(encoding="utf-8"))
    claims = matrix.get("claims", [])
    identifiers = [claim.get("id") for claim in claims]
    if len(claims) < 15 or len(identifiers) != len(set(identifiers)):
        raise RuntimeError("Claim matrix needs at least 15 unique stable claims")
    required = {
        "id",
        "statement",
        "claim_type",
        "hypotheses",
        "domain_units_signs_boundary_quantifiers",
        "support",
        "evidence_class",
        "limitations_or_counterexamples",
        "disposition",
    }
    for claim in claims:
        missing = required - claim.keys()
        if missing:
            raise RuntimeError(f"Claim {claim.get('id')} missing fields {sorted(missing)}")
        if claim["evidence_class"] not in ALLOWED_EVIDENCE:
            raise RuntimeError(f"Invalid evidence class for {claim['id']}")
        if claim["disposition"] not in ALLOWED_DISPOSITIONS:
            raise RuntimeError(f"Invalid disposition for {claim['id']}")
        if claim["disposition"] in {"admit", "admit_with_qualification"} and not claim["support"]:
            raise RuntimeError(f"Admitted claim {claim['id']} has no support")
        if claim["evidence_class"] == "mechanically_replayed" and re.search(
            r"\b(?:proved|proof|external validation)\b", claim["statement"], re.IGNORECASE
        ):
            raise RuntimeError(
                f"Mechanical or numerical agreement was promoted to proof/external validation in {claim['id']}"
            )
    indexed = {claim["id"]: claim for claim in claims}
    required_hypotheses = {
        "SPPT-C005": ("strictly positive", "connected", "nonempty proper"),
        "SPPT-C008": ("K>0", "injective", "equilibrium exists"),
        "SPPT-C006": ("dTu/dTd", "differentiable"),
        "ASTRA-C013": ("20 distinct generic starts", "acceptance gate"),
    }
    for identifier, phrases in required_hypotheses.items():
        claim = indexed.get(identifier)
        if claim is None:
            raise RuntimeError(f"Required consequential claim missing: {identifier}")
        searchable = " ".join(claim["hypotheses"] + claim["limitations_or_counterexamples"])
        for phrase in phrases:
            if phrase.lower() not in searchable.lower():
                raise RuntimeError(f"Weakened hypothesis {phrase!r} in {identifier}")


def check_source_inventory() -> None:
    inventory = json.loads((ROOT / "SOURCE_INVENTORY.json").read_text(encoding="utf-8"))
    artifacts = inventory.get("artifacts", [])
    if len(artifacts) != 16:
        raise RuntimeError(f"Expected 16 supplied artifacts, found {len(artifacts)}")
    required = {
        "canonical_relative_path",
        "bytes",
        "sha256",
        "media_type",
        "displayed_attribution",
        "embedded_attribution",
        "license",
        "rights_status",
        "relationship",
    }
    for item in artifacts:
        if required - item.keys():
            raise RuntimeError(f"Incomplete source inventory item: {item}")
        if not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
            raise RuntimeError(f"Invalid source hash: {item['canonical_relative_path']}")
    aliases = inventory.get("discovered_aliases", [])
    preprint_hash = next(
        item["sha256"]
        for item in artifacts
        if item["canonical_relative_path"].endswith("preprint_v1.0.1.pdf")
    )
    if len(aliases) != 1 or aliases[0]["sha256"] != preprint_hash:
        raise RuntimeError("The byte-identical PDF alias relationship is not preserved")
    ensemble_relationships = [
        item["relationship"]
        for item in artifacts
        if "synthetic_topology_ensemble" in item["canonical_relative_path"]
    ]
    if len(ensemble_relationships) != 2 or not all(
        "not independent evidence" in value for value in ensemble_relationships
    ):
        raise RuntimeError("Duplicate CSV/JSON evidence is not explicitly deduplicated")
    synthesis = next(
        item for item in artifacts if item["canonical_relative_path"] == "pasted-text.txt"
    )
    if (
        "not independent evidence" not in synthesis["relationship"]
        or "not redistributed verbatim" not in synthesis["rights_status"]
    ):
        raise RuntimeError(
            "Author-supplied synthesis must remain excluded as independent or verbatim evidence"
        )


def check_dependency_lock() -> None:
    lock = (ROOT / "requirements-lock.txt").read_text(encoding="utf-8")
    if "--hash=sha256:" not in lock or "not pinned" in lock:
        raise RuntimeError("Dependency lock is not fully hash-pinned")
    for requirement in (ROOT / "requirements.in").read_text(encoding="utf-8").splitlines():
        requirement = requirement.strip()
        if not requirement or requirement.startswith("#"):
            continue
        package = requirement.split("==", 1)[0].lower()
        if not re.search(rf"(?m)^{re.escape(package)}==", lock):
            raise RuntimeError(f"Direct dependency missing from lock: {package}")


def check_public_json_schemas() -> None:
    schema_root = ROOT / "schemas"
    expected_prefix = "https://jkolantree.github.io/astra/schemas/"
    records = (
        ROOT / "RELEASE_SPEC.json",
        ROOT / "CLAIM_MATRIX.json",
        ROOT / "SOURCE_INVENTORY.json",
        ROOT / "evidence" / "claim_source_coverage_v1.0.6_draft.json",
        ROOT / "RUNTIME.json",
        ROOT / "manuscript" / "document_semantic_identity.json",
        ROOT / "manuscript" / "pdf_inspection.json",
        ROOT
        / "resources"
        / "sector-complete-instrument"
        / "v0.1.0-alpha.1"
        / "RELEASE_SPEC.json",
    )
    referenced_schema_files: set[Path] = set()
    for record_path in records:
        instance = json.loads(record_path.read_text(encoding="utf-8"))
        declared = instance.get("schema")
        if not isinstance(declared, str) or not declared.startswith(expected_prefix):
            raise RuntimeError(
                f"Non-public or missing schema URL in {record_path.relative_to(ROOT)}"
            )
        schema_path = schema_root / declared.removeprefix(expected_prefix)
        if schema_path.parent != schema_root or not schema_path.is_file():
            raise RuntimeError(
                f"Declared schema is not shipped: {record_path.relative_to(ROOT)} -> {declared}"
            )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        if schema.get("$id") != declared:
            raise RuntimeError(f"Schema $id differs from its public URL: {schema_path.name}")
        errors = sorted(
            Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(instance),
            key=lambda error: tuple(str(part) for part in error.absolute_path),
        )
        if errors:
            first = errors[0]
            location = "/".join(str(part) for part in first.absolute_path) or "<root>"
            raise RuntimeError(
                f"JSON schema validation failed for {record_path.relative_to(ROOT)} at "
                f"{location}: {first.message}"
            )
        referenced_schema_files.add(schema_path)

        related_schema = instance.get("identity_schema")
        if related_schema is not None:
            if not isinstance(related_schema, str) or not related_schema.startswith(expected_prefix):
                raise RuntimeError(
                    f"Non-public or missing related schema URL in {record_path.relative_to(ROOT)}"
                )
            related_path = schema_root / related_schema.removeprefix(expected_prefix)
            if related_path.parent != schema_root or not related_path.is_file():
                raise RuntimeError(
                    f"Related schema is not shipped: {record_path.relative_to(ROOT)} -> {related_schema}"
                )
            related_schema_doc = json.loads(related_path.read_text(encoding="utf-8"))
            if related_schema_doc.get("$id") != related_schema:
                raise RuntimeError(f"Related schema $id differs from its public URL: {related_path.name}")
            referenced_schema_files.add(related_path)

    release_identity = schema_root / "release-identity-v1.schema.json"
    if not release_identity.is_file():
        raise RuntimeError("Detached release-identity schema is not shipped")
    release_identity_schema = json.loads(release_identity.read_text(encoding="utf-8"))
    if release_identity_schema.get("$id") != expected_prefix + release_identity.name:
        raise RuntimeError("Detached release-identity schema has the wrong public $id")
    referenced_schema_files.add(release_identity)

    shipped = set(schema_root.glob("*.schema.json"))
    if shipped != referenced_schema_files:
        unexpected = sorted(path.name for path in shipped - referenced_schema_files)
        missing = sorted(path.name for path in referenced_schema_files - shipped)
        raise RuntimeError(
            f"Public schema inventory mismatch: unexpected={unexpected}, missing={missing}"
        )


def check_runtime_identity() -> None:
    runtime = json.loads((ROOT / "RUNTIME.json").read_text(encoding="utf-8"))
    lock_record = runtime.get("dependency_lock", {})
    lock_path = ROOT / str(lock_record.get("file", ""))
    if lock_path != ROOT / "requirements-lock.txt" or not lock_path.is_file():
        raise RuntimeError("Runtime identity points to the wrong dependency lock")
    if lock_record.get("sha256") != sha256(lock_path):
        raise RuntimeError("Runtime identity dependency-lock digest mismatch")
    if runtime.get("python") != (ROOT / ".python-version").read_text(encoding="utf-8").strip():
        raise RuntimeError("Runtime identity and .python-version disagree")
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    if project["project"].get("requires-python") != f"=={runtime.get('python')}":
        raise RuntimeError("Runtime identity and pyproject.toml Python requirement disagree")
    git_identity = runtime.get("git", {})
    required_git_fields = {
        "provider",
        "version",
        "build_commit",
        "asset",
        "source",
        "sha256",
        "executable_sha256",
    }
    if set(git_identity) != required_git_fields:
        raise RuntimeError("Runtime identity has incomplete Git for Windows provenance")
    expected_mailmap = (
        "Jacko T. <307349551+jkolantree@users.noreply.github.com> "
        "<307349551+jkolantree@users.noreply.github.com>\n"
    )
    if (ROOT / ".mailmap").read_text(encoding="utf-8") != expected_mailmap:
        raise RuntimeError("Public pseudonym mailmap drift")


def main() -> None:
    check_cache_boundaries()
    paths = public_files()
    spec = json.loads((ROOT / "RELEASE_SPEC.json").read_text(encoding="utf-8"))
    version = str(spec["version"])
    check_text_privacy(paths)
    check_license_map(paths)
    check_png_metadata(paths)
    check_working_paper_resource()
    check_framework_v030_resource()
    check_publication_map()
    check_metadata_agreement()
    check_claim_matrix()
    check_source_inventory()
    check_dependency_lock()
    check_public_json_schemas()
    check_runtime_identity()
    check_html(
        ROOT / "manuscript" / f"SPPT_ASTRA_preprint_v{version}.html",
        "Phase-Reservoir Topology as a Hidden State Variable in Planetary Evolution",
    )
    check_html(
        ROOT / "manuscript" / f"SPPT_ASTRA_technical_supplement_v{version}.html",
        "Technical Supplement: Synthetic Pointwise Topology Selection and Identifiability Limits",
    )
    print(f"Repository contract passed for {len(paths)} public files.")


if __name__ == "__main__":
    main()
