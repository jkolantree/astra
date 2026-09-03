"""Fail-closed repository, metadata, accessibility, privacy, and license checks."""

from __future__ import annotations

import csv
import fnmatch
import hashlib
import json
import os
import re
import tomllib
import xml.etree.ElementTree as ET
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
    "CONTRIBUTING.md",
    "CITATION.cff",
    "CLAIM_MATRIX.json",
    "LICENSE",
    "LICENSE_MAP.md",
    "MANIFEST.sha256",
    "PROVENANCE.md",
    "PUBLICATIONS.md",
    "README.md",
    "REPRODUCING.md",
    "RELEASE_NOTES_earth-instrument-framework-v0.3.0.md",
    "RELEASE_NOTES_earth-instrument-wp-0.1.md",
    "RELEASE_NOTES_v1.0.1.md",
    "RELEASE_NOTES_v1.0.2.md",
    "RELEASE_NOTES_v1.0.3.md",
    "RELEASE_NOTES_v1.0.4.md",
    "RELEASE_NOTES_v1.0.5.md",
    "RELEASE_NOTES_v1.0.6.md",
    "RELEASE_NOTES_v1.0.7.md",
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
    "figures": {".png", ".pdf", ".svg"},
    "licenses": {".txt"},
    "manuscript": {".bib", ".css", ".html", ".json", ".md", ".pdf"},
    "resources": {
        ".bib",
        ".cff",
        ".css",
        ".csv",
        ".html",
        ".json",
        ".md",
        ".pdf",
        ".png",
        ".py",
        ".sha256",
        ".svg",
        ".txt",
    },
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
    "tools/build_dark_medium_response_atlas_documents.py",
    "tools/check_dark_medium_response_atlas_html.py",
    "tools/check_external_links.py",
    "tools/check_pages_links.py",
    "tools/check_repository_links.py",
    "tools/check_repository.py",
    "tools/inspect_pdf.py",
    "tools/inspect_dark_medium_response_atlas_pdf.py",
    "tests/test_document_contract.py",
    "tests/test_release_integrity.py",
    "resources/cosmic-visibility-framework/draft-v0.1.0/build_framework_pdf.py",
}
ALLOWED_EVIDENCE = {
    "source_asserted",
    "hand_checked",
    "independently_reproduced",
    "mechanically_replayed",
    "kernel_verified",
    "externally_published",
    "structural_inference",
    "proposed_only",
    "deferred",
    "rejected",
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
ACTIVE_SUPPORT_RESOURCE_ROOT = "resources/active-support-audit/draft-v0.1.0"
ACTIVE_SUPPORT_RESOURCE_FILES = (
    "CHANGE_LOG.md",
    "METHODS_NOTE.md",
    "README.md",
    "claim_ledger.csv",
    "draft_metadata.json",
    "source_ledger.csv",
)
COHERENCE_CELL_RESOURCE_ROOT = "resources/coherence-cell-exploration/draft-v0.1.0"
COHERENCE_CELL_RESOURCE_FILES = (
    "aeof_ledger.csv",
    "CHANGE_LOG.md",
    "LICENSE_MAP.md",
    "METHODS_NOTE.md",
    "README.md",
    "claim_ledger.csv",
    "draft_metadata.json",
    "novelty_ledger.csv",
    "source_ledger.csv",
)
SPPT_BRIDGE_RESOURCE_ROOT = "resources/sppt-bridge-protocol/draft-v0.1.0"
SPPT_BRIDGE_RESOURCE_FILES = (
    "BRIDGE_MANIFEST.sha256",
    "example_protocol.json",
    "README.md",
    "bridge_contract.py",
    "bridge_protocol.schema.json",
    "schema_validation_environment.json",
    "test_bridge_contract.py",
    "validate_schema.py",
)
COSMIC_VISIBILITY_RESOURCE_ROOT = "resources/cosmic-visibility-framework/draft-v0.1.0"
COSMIC_VISIBILITY_RESOURCE_FILES = (
    "CHANGE_LOG.md",
    "CORE_FRAMEWORK.md",
    "COSMIC_VISIBILITY_FRAMEWORK_v0.1.0.html",
    "COSMIC_VISIBILITY_FRAMEWORK_v0.1.0.pdf",
    "LICENSE_MAP.md",
    "pdf_build_identity.json",
    "README.md",
    "VISIBILITY_MANIFEST.sha256",
    "claim_ledger.csv",
    "draft_metadata.json",
    "example_visibility_record.json",
    "novelty_ledger.csv",
    "source_ledger.csv",
    "test_visibility_framework.py",
    "validate_framework.py",
    "visibility_framework.schema.json",
    "build_framework_pdf.py",
    "figures/evidence_ladder.svg",
    "figures/visibility_kernel_chain.svg",
)
DARK_MEDIUM_RESOURCE_ROOT = "resources/dark-medium-response-atlas"
DARK_MEDIUM_DRAFT_FILES = (
    "CHANGE_LOG.md",
    "DARK_MEDIUM_RESPONSE_ATLAS.md",
    "LICENSE_MAP.md",
    "README.md",
    "claim_ledger.csv",
    "draft_metadata.json",
    "novelty_ledger.csv",
    "source_ledger.csv",
)
DARK_MEDIUM_FINAL_FILES = (
    "CHANGELOG.md",
    "CITATION.cff",
    "LICENSE_MAP.md",
    "README.md",
    "RELEASE_NOTES.md",
    "RELEASE_SPEC.json",
    "claim-ledger.csv",
    "dark-medium-response-atlas-v0.1.0.css",
    "dark-medium-response-atlas-v0.1.0.html",
    "dark-medium-response-atlas-v0.1.0.md",
    "dark-medium-response-atlas-v0.1.0.pdf",
    "external-link-observations.json",
    "html-accessibility.json",
    "novelty-ledger.csv",
    "pdf-inspection.json",
    "publication-identity.json",
    "source-ledger.csv",
    "visual-review.json",
)
SPPT_ASTRA_V108_CANDIDATE_ROOT = "resources/sppt-astra-v1.0.8-candidate"
SPPT_ASTRA_V108_ORIGIN_SHA256 = "55b8962176680859064fa2ebc009bb45ddc0cce987bce0bc16206faa4c7c387a"
SPPT_ASTRA_V107_MATRIX_SHA256 = "c7b52c0afc887342ad4bdc42f91f979fc49e1cd0b21b8e7c1c31946033de9bed"
SPPT_ASTRA_V108_FROZEN_COMMIT = "f8b32ef0af9cb6804f256490b4daafbdba43740e"
SPPT_ASTRA_V108_SVG_DATE = "2026-08-16T00:00:00Z"
SPPT_ASTRA_V108_FIGURE_STEMS = (
    "figure_01_repository_architecture",
    "figure_02_stateful_edge_architecture",
    "figure_03_edge_contract",
    "figure_04_nonreciprocity_closure",
    "figure_05_arrested_coarsening_model",
    "figure_06_catalyst_self_rewriting_edge",
    "figure_07_orr_reported_values",
    "figure_08_operator_stack",
    "figure_09_bridge_protocol",
    "figure_10_dual_rent",
    "figure_11_application_map",
    "figure_12_promotion_gates",
    "figure_13_temporal_interface_audit",
    "figure_14_endogenous_visibility",
    "figure_15_source_shell_separation",
    "figure_16_cross_channel_rescue",
    "figure_17_self_detuning_plasma",
    "figure_18_catastrophic_tomography",
)
SPPT_ASTRA_V108_CANDIDATE_FILES = (
    "README.md",
    "package/ASTRA_SPPT_v1.0.8_Endogenous_Visibility_Candidate.docx",
    "package/ASTRA_SPPT_v1.0.8_Endogenous_Visibility_Candidate.pdf",
    "package/ASTRA_SPPT_v1.0.8_Endogenous_Visibility_Candidate_Peer_Review.pdf",
    "package/ASTRA_SPPT_v1.0.8_Endogenous_Visibility_Candidate_Tagged_Reading_Edition.pdf",
    "package/LICENSES.md",
    "package/README.md",
    "package/SHA256SUMS.txt",
    "package/THIRD_PARTY_NOTICES.md",
    "package/candidate_package_manifest.json",
    "package/candidate_release_notes.md",
    "package/change_log_from_v1.0.7.md",
    "package/claim_ledger.csv",
    "package/claim_ledger.json",
    "package/formatting_and_submission_guide.md",
    "package/integration_graph.json",
    "package/repository_audit.md",
    "package/source/ASTRA_SPPT_v1.0.8_Endogenous_Visibility_Candidate.md",
    "package/source/CLAIM_MATRIX_v1.0.7.json",
    "package/source/build_candidate.py",
    "package/source/claim_ledger_v1.0.8_additions.json",
    "package/source/finalize_candidate.py",
    "package/source/generate_ledgers.py",
    "package/source/make_figures.py",
    "package/source/references.bib",
    "package/source/source_ledger_v1.0.8_records.json",
    "package/source_audit_and_correction_log.md",
    "package/source_ledger.csv",
    "package/source_ledger.json",
    "package/verification/ASTRA_SPPT_v1.0.8_Candidate_Verification_Report.pdf",
    "package/verification/acceptance_gate_matrix.csv",
    "package/verification/docx_a11y_report.json",
    "package/verification/verification_report.md",
    "package/verification/verification_summary.json",
    "package/visual_manifest.csv",
    "package/visual_manifest.json",
    "package/visual_preflight_report.md",
    *(
        f"package/figures/{stem}.{suffix}"
        for stem in SPPT_ASTRA_V108_FIGURE_STEMS
        for suffix in ("png", "svg")
    ),
)
SPPT_ASTRA_V108_DOCX_PATH = (
    f"{SPPT_ASTRA_V108_CANDIDATE_ROOT}/package/"
    "ASTRA_SPPT_v1.0.8_Endogenous_Visibility_Candidate.docx"
)
RESOURCE_EXACT_SUFFIX_ALLOWLIST = {SPPT_ASTRA_V108_DOCX_PATH}
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
    *(f"{ACTIVE_SUPPORT_RESOURCE_ROOT}/{name}" for name in ACTIVE_SUPPORT_RESOURCE_FILES),
    *(f"{COHERENCE_CELL_RESOURCE_ROOT}/{name}" for name in COHERENCE_CELL_RESOURCE_FILES),
    *(f"{SPPT_BRIDGE_RESOURCE_ROOT}/{name}" for name in SPPT_BRIDGE_RESOURCE_FILES),
    *(f"{COSMIC_VISIBILITY_RESOURCE_ROOT}/{name}" for name in COSMIC_VISIBILITY_RESOURCE_FILES),
    *(
        f"{DARK_MEDIUM_RESOURCE_ROOT}/draft-v0.1.0/{name}"
        for name in DARK_MEDIUM_DRAFT_FILES
    ),
    *(f"{DARK_MEDIUM_RESOURCE_ROOT}/v0.1.0/{name}" for name in DARK_MEDIUM_FINAL_FILES),
    *(f"{SPPT_ASTRA_V108_CANDIDATE_ROOT}/{name}" for name in SPPT_ASTRA_V108_CANDIDATE_FILES),
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
            if matched is None:
                raise RuntimeError(f"Unexpected repository path: {relative.as_posix()}")
            if matched == "resources" and relative.as_posix() not in RESOURCE_PATH_ALLOWLIST:
                raise RuntimeError(f"Unregistered supplemental resource: {relative.as_posix()}")
            suffix_allowed = path.suffix.lower() in DIRECTORY_RULES[matched]
            if matched == "resources" and relative.as_posix() in RESOURCE_EXACT_SUFFIX_ALLOWLIST:
                suffix_allowed = True
            if not suffix_allowed:
                raise RuntimeError(f"Unexpected repository path: {relative.as_posix()}")
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


def _check_sppt_astra_v108_claim_ledger(package_root: Path) -> None:
    matrix_path = ROOT / "CLAIM_MATRIX.json"
    embedded_matrix_path = package_root / "source" / "CLAIM_MATRIX_v1.0.7.json"
    if sha256(matrix_path) != SPPT_ASTRA_V107_MATRIX_SHA256:
        raise RuntimeError("Repository v1.0.7 claim matrix bytes drifted")
    if sha256(embedded_matrix_path) != SPPT_ASTRA_V107_MATRIX_SHA256:
        raise RuntimeError("Candidate embedded v1.0.7 claim matrix bytes drifted")

    matrix = json.loads(embedded_matrix_path.read_text(encoding="utf-8"))
    additions = json.loads(
        (package_root / "source" / "claim_ledger_v1.0.8_additions.json").read_text(encoding="utf-8")
    )
    ledger = json.loads((package_root / "claim_ledger.json").read_text(encoding="utf-8"))
    canonical_claims = matrix.get("claims")
    if not isinstance(canonical_claims, list) or len(canonical_claims) != 55:
        raise RuntimeError("Candidate v1.0.7 matrix must contain exactly 55 claims")
    if not isinstance(additions, list) or len(additions) != 20:
        raise RuntimeError("Candidate v1.0.8 additions must contain exactly 20 claims")
    if not isinstance(ledger, list) or len(ledger) != 75:
        raise RuntimeError("Candidate successor ledger must contain exactly 75 claims")

    canonical_ids = [claim.get("id") for claim in canonical_claims]
    addition_ids = [claim.get("claim_id") for claim in additions]
    ledger_ids = [claim.get("claim_id") for claim in ledger]
    if len(set(canonical_ids)) != 55:
        raise RuntimeError("Frozen v1.0.7 claim matrix contains duplicate identifiers")
    if len(set(addition_ids)) != 20 or set(canonical_ids) & set(addition_ids):
        raise RuntimeError("Candidate claim identifiers collide with each other or v1.0.7")
    if any(
        not isinstance(claim_id, str) or not claim_id.startswith("V108-")
        for claim_id in addition_ids
    ):
        raise RuntimeError("Candidate additions must use distinct V108 claim identifiers")
    if ledger_ids != canonical_ids + addition_ids or len(set(ledger_ids)) != 75:
        raise RuntimeError("Candidate ledger order, coverage, or identifier uniqueness drifted")

    status_by_disposition = {
        "admit": "Admitted",
        "admit_with_qualification": "Admitted with qualification",
        "proposed_only": "Proposed only",
        "deferred": "Deferred",
        "rejected": "Rejected",
    }
    inherited_falsifier = (
        "No separate field exists in the frozen v1.0.7 matrix; use its "
        "preserved limitations and cited support."
    )
    for canonical, projected in zip(canonical_claims, ledger[:55], strict=True):
        expected = {
            "claim_id": canonical["id"],
            "statement": canonical["statement"],
            "claim_type": canonical["claim_type"],
            "scientific_status": status_by_disposition[canonical["disposition"]],
            "evidence_class": canonical["evidence_class"],
            "disposition": canonical["disposition"],
            "support": " || ".join(canonical["support"]),
            "limitations": " || ".join(canonical["limitations_or_counterexamples"]),
            "falsifier_or_next_test": inherited_falsifier,
        }
        if projected != expected:
            raise RuntimeError(f"Candidate projection drifted for v1.0.7 claim {canonical['id']}")

    with (package_root / "claim_ledger.csv").open(encoding="utf-8", newline="") as handle:
        csv_ledger = list(csv.DictReader(handle))
    if csv_ledger != ledger:
        raise RuntimeError("Candidate claim ledger CSV and JSON disagree")


def _check_sppt_astra_v108_svg(path: Path) -> None:
    raw = path.read_text(encoding="utf-8")
    if "<!DOCTYPE" in raw.upper():
        raise RuntimeError(f"Candidate SVG contains an external-DTD surface: {path.name}")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as error:
        raise RuntimeError(f"Candidate SVG is not well formed: {path.name}") from error

    svg_namespace = "http://www.w3.org/2000/svg"
    dc_namespace = "http://purl.org/dc/elements/1.1/"
    if root.tag != f"{{{svg_namespace}}}svg":
        raise RuntimeError(f"Candidate SVG has the wrong root element: {path.name}")
    live_text = [
        "".join(node.itertext()).strip() for node in root.findall(f".//{{{svg_namespace}}}text")
    ]
    if not any(live_text):
        raise RuntimeError(f"Candidate SVG has no live text: {path.name}")

    metadata = root.find(f"{{{svg_namespace}}}metadata")
    if metadata is None:
        raise RuntimeError(f"Candidate SVG has no fixed metadata: {path.name}")

    def metadata_values(name: str) -> list[str]:
        return [
            (node.text or "").strip() for node in metadata.findall(f".//{{{dc_namespace}}}{name}")
        ]

    if metadata_values("date") != [SPPT_ASTRA_V108_SVG_DATE]:
        raise RuntimeError(f"Candidate SVG creation date is not fixed: {path.name}")
    if metadata_values("description") != ["Original ASTRA candidate figure"]:
        raise RuntimeError(f"Candidate SVG description metadata drifted: {path.name}")
    if metadata_values("format") != ["image/svg+xml"]:
        raise RuntimeError(f"Candidate SVG format metadata drifted: {path.name}")
    if metadata_values("title") != ["ASTRA / Jacko T."]:
        raise RuntimeError(f"Candidate SVG creator metadata drifted: {path.name}")

    url_pattern = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE)
    for element in root.iter():
        local_tag = element.tag.rsplit("}", 1)[-1]
        if local_tag in {"foreignObject", "script"}:
            raise RuntimeError(
                f"Candidate SVG contains active/external-capable content: {path.name}"
            )
        values = [*element.attrib.values(), element.text or ""]
        for attribute, value in element.attrib.items():
            local_attribute = attribute.rsplit("}", 1)[-1]
            if local_attribute in {"href", "src"} and not value.startswith(("#", "data:")):
                raise RuntimeError(f"Candidate SVG contains an external reference: {path.name}")
        for value in values:
            if "@import" in value.lower():
                raise RuntimeError(f"Candidate SVG contains a stylesheet import: {path.name}")
            for match in url_pattern.finditer(value):
                if not match.group(2).strip().startswith("#"):
                    raise RuntimeError(f"Candidate SVG contains an external URL: {path.name}")


def _check_sppt_astra_v108_package_identity(package_root: Path) -> None:
    package_roster = {
        name.removeprefix("package/")
        for name in SPPT_ASTRA_V108_CANDIDATE_FILES
        if name.startswith("package/")
    }
    sums_path = package_root / "SHA256SUMS.txt"
    manifest_path = package_root / "candidate_package_manifest.json"
    if not sums_path.is_file() and not manifest_path.is_file():
        return
    if not sums_path.is_file() or not manifest_path.is_file():
        raise RuntimeError("Candidate manifest and checksum sidecar must be present together")

    checksum_text = sums_path.read_text(encoding="utf-8")
    if not checksum_text.endswith("\n"):
        raise RuntimeError("Candidate checksum sidecar must end with a newline")
    checksum_records: dict[str, str] = {}
    checksum_names: list[str] = []
    for line in checksum_text.splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([^\r\n]+)", line)
        if match is None:
            raise RuntimeError(f"Malformed candidate checksum line: {line!r}")
        digest, name = match.groups()
        parts = name.split("/")
        if (
            name.startswith("/")
            or "\\" in name
            or ":" in parts[0]
            or any(part in {"", ".", ".."} for part in parts)
        ):
            raise RuntimeError(f"Unsafe candidate checksum path: {name}")
        if name in checksum_records:
            raise RuntimeError(f"Duplicate candidate checksum path: {name}")
        checksum_records[name] = digest
        checksum_names.append(name)

    expected_checksum_names = package_roster - {"SHA256SUMS.txt"}
    if set(checksum_names) != expected_checksum_names or checksum_names != sorted(checksum_names):
        raise RuntimeError("Candidate checksum roster or canonical ordering drifted")
    for name, expected_digest in checksum_records.items():
        if sha256(package_root / name) != expected_digest:
            raise RuntimeError(f"Candidate checksum mismatch: {name}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "reviewed_unpromoted_candidate":
        raise RuntimeError("Candidate manifest does not preserve the unpromoted boundary")
    if manifest.get("source_package_sha256") != SPPT_ASTRA_V108_ORIGIN_SHA256:
        raise RuntimeError("Candidate manifest origin-package identity drifted")
    repository_basis = manifest.get("repository_basis")
    if not isinstance(repository_basis, dict) or (
        repository_basis.get("audited_commit") != SPPT_ASTRA_V108_FROZEN_COMMIT
        or repository_basis.get("stable_release") != "v1.0.7"
    ):
        raise RuntimeError("Candidate manifest repository basis drifted")
    verification = manifest.get("verification")
    if not isinstance(verification, dict) or (
        verification.get("verdict") != "REVIEWED_UNPROMOTED_CANDIDATE"
    ):
        raise RuntimeError("Candidate verification verdict does not preserve its boundary")
    payload = manifest.get("payload")
    if not isinstance(payload, list):
        raise RuntimeError("Candidate package manifest has no payload list")
    payload_names: list[str] = []
    payload_records: dict[str, dict[str, object]] = {}
    for entry in payload:
        if not isinstance(entry, dict) or set(entry) != {"path", "bytes", "sha256"}:
            raise RuntimeError("Candidate manifest payload entry has the wrong fields")
        name = entry["path"]
        if not isinstance(name, str) or name in payload_records:
            raise RuntimeError("Candidate manifest payload paths are invalid or duplicated")
        payload_names.append(name)
        payload_records[name] = entry

    expected_payload_names = package_roster - {
        "SHA256SUMS.txt",
        "candidate_package_manifest.json",
    }
    if set(payload_names) != expected_payload_names or payload_names != sorted(payload_names):
        raise RuntimeError("Candidate manifest payload roster or canonical ordering drifted")
    expected_total_bytes = 0
    for name, entry in payload_records.items():
        path = package_root / name
        size = path.stat().st_size
        digest = sha256(path)
        expected_total_bytes += size
        if entry["bytes"] != size or entry["sha256"] != digest:
            raise RuntimeError(f"Candidate manifest payload identity mismatch: {name}")
    if manifest.get("payload_file_count_excluding_manifest_and_sha256sums") != len(
        expected_payload_names
    ):
        raise RuntimeError("Candidate manifest payload count drifted")
    if manifest.get("payload_total_bytes_excluding_manifest_and_sha256sums") != (
        expected_total_bytes
    ):
        raise RuntimeError("Candidate manifest payload byte total drifted")


def check_sppt_astra_v108_candidate_resource() -> None:
    resource_root = ROOT / SPPT_ASTRA_V108_CANDIDATE_ROOT
    if not resource_root.is_dir():
        raise RuntimeError("SPPT/ASTRA v1.0.8 candidate resource directory is missing")
    observed_roster = {
        path.relative_to(resource_root).as_posix()
        for path in resource_root.rglob("*")
        if path.is_file()
    }
    expected_roster = set(SPPT_ASTRA_V108_CANDIDATE_FILES)
    if observed_roster != expected_roster:
        raise RuntimeError(
            "SPPT/ASTRA v1.0.8 candidate roster differs from its contract: "
            f"missing={sorted(expected_roster - observed_roster)}, "
            f"unexpected={sorted(observed_roster - expected_roster)}"
        )

    readme = " ".join((resource_root / "README.md").read_text(encoding="utf-8").split())
    required_boundaries = (
        "Status: repository-visible, unpromoted successor candidate.",
        "not the stable SPPT/ASTRA release",
        "not peer reviewed",
        "no tag, GitHub Release, Pages route, DOI, or Zenodo record",
        "Immutable SPPT/ASTRA v1.0.7 remains the stable citation target.",
        SPPT_ASTRA_V108_FROZEN_COMMIT,
        SPPT_ASTRA_V108_ORIGIN_SHA256,
    )
    for boundary in required_boundaries:
        if boundary not in readme:
            raise RuntimeError(f"SPPT/ASTRA v1.0.8 candidate boundary omits: {boundary}")

    package_root = resource_root / "package"
    figures_root = package_root / "figures"
    png_stems = {path.stem for path in figures_root.glob("*.png")}
    svg_paths = sorted(figures_root.glob("*.svg"))
    svg_stems = {path.stem for path in svg_paths}
    expected_stems = set(SPPT_ASTRA_V108_FIGURE_STEMS)
    if png_stems != expected_stems or svg_stems != expected_stems:
        raise RuntimeError("Candidate must contain the exact 18 PNG/SVG figure pairs")
    for svg_path in svg_paths:
        _check_sppt_astra_v108_svg(svg_path)

    _check_sppt_astra_v108_claim_ledger(package_root)
    _check_sppt_astra_v108_package_identity(package_root)


def check_private_operator_policy_boundary() -> None:
    """Keep private operator policy out of the future public repository tree."""

    if (ROOT / "AGENTS.md").exists():
        raise RuntimeError("Private AGENTS.md remains in the public repository root")
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    if "/AGENTS.md" not in ignored:
        raise RuntimeError("Root .gitignore does not reserve private AGENTS.md")


def _atlas_csv(path: Path, required_fields: set[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or set(reader.fieldnames) != required_fields:
            raise RuntimeError(f"Atlas CSV header drift: {path.relative_to(ROOT)}")
        rows = list(reader)
    if not rows:
        raise RuntimeError(f"Atlas CSV is empty: {path.relative_to(ROOT)}")
    return rows


def _atlas_file_record(path: Path) -> dict[str, object]:
    return {"path": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)}


def check_dark_medium_response_atlas_resource() -> None:
    """Verify the bounded, namespaced Atlas package without core promotion."""

    root = ROOT / DARK_MEDIUM_RESOURCE_ROOT
    draft = root / "draft-v0.1.0"
    package = root / "v0.1.0"
    observed_draft = {path.name for path in draft.iterdir() if path.is_file()}
    observed_final = {path.name for path in package.iterdir() if path.is_file()}
    if observed_draft != set(DARK_MEDIUM_DRAFT_FILES):
        raise RuntimeError(
            "Dark-Medium historical draft roster drifted: "
            f"expected={sorted(DARK_MEDIUM_DRAFT_FILES)}, observed={sorted(observed_draft)}"
        )
    if observed_final != set(DARK_MEDIUM_FINAL_FILES):
        raise RuntimeError(
            "Dark-Medium final package roster drifted: "
            f"expected={sorted(DARK_MEDIUM_FINAL_FILES)}, observed={sorted(observed_final)}"
        )

    spec = json.loads((package / "RELEASE_SPEC.json").read_text(encoding="utf-8"))
    expected_spec = {
        "publication_line_id": "dark-medium-response-atlas",
        "version": "0.1.0",
        "tag": "dark-medium-response-atlas-v0.1.0",
        "namespace": "resources/dark-medium-response-atlas/v0.1.0",
        "identity_excludes_self": True,
        "github_release": {
            "draft": False,
            "prerelease": True,
            "make_latest": False,
            "immutable_required": True,
        },
        "pages": {
            "publish": True,
            "versioned_route": "/resources/dark-medium-response-atlas/v0.1.0/",
            "latest_route": "/resources/dark-medium-response-atlas/latest/",
            "citation_route": "/resources/dark-medium-response-atlas/v0.1.0/",
        },
        "external_identifiers": {"doi": False, "zenodo": False},
    }
    for key, expected in expected_spec.items():
        if spec.get(key) != expected:
            raise RuntimeError(f"Dark-Medium release specification drift for {key}")
    asset_names = spec.get("release_asset_allowlist")
    checksum_names = spec.get("checksum_asset_names")
    if (
        asset_names
        != [
            "dark-medium-response-atlas-v0.1.0.html",
            "dark-medium-response-atlas-v0.1.0.pdf",
            "dark-medium-response-atlas-v0.1.0-source.tar.gz",
            "SHA256SUMS",
            "dark-medium-response-atlas-v0.1.0-release-identity.json",
        ]
        or checksum_names != asset_names[:3]
    ):
        raise RuntimeError("Dark-Medium release-asset contract is not exact")

    cff = YAML(typ="safe").load((package / "CITATION.cff").read_text(encoding="utf-8"))
    if not isinstance(cff, dict) or {
        "version": str(cff.get("version", "")),
        "date-released": str(cff.get("date-released", "")),
        "url": str(cff.get("url", "")),
        "license": str(cff.get("license", "")),
    } != {
        "version": "0.1.0",
        "date-released": "2026-09-01",
        "url": "https://jkolantree.github.io/astra/resources/dark-medium-response-atlas/v0.1.0/",
        "license": "CC-BY-4.0",
    }:
        raise RuntimeError("Dark-Medium citation metadata does not bind the versioned route")

    html = package / "dark-medium-response-atlas-v0.1.0.html"
    pdf = package / "dark-medium-response-atlas-v0.1.0.pdf"
    html_report = json.loads((package / "html-accessibility.json").read_text(encoding="utf-8"))
    pdf_report = json.loads((package / "pdf-inspection.json").read_text(encoding="utf-8"))
    visual_review = json.loads((package / "visual-review.json").read_text(encoding="utf-8"))
    identity = json.loads((package / "publication-identity.json").read_text(encoding="utf-8"))
    if (
        html_report.get("file") != html.name
        or html_report.get("bytes") != html.stat().st_size
        or html_report.get("sha256") != sha256(html)
    ):
        raise RuntimeError("Dark-Medium HTML accessibility record does not match its artifact")
    if (
        pdf_report.get("file") != pdf.name
        or pdf_report.get("bytes") != pdf.stat().st_size
        or pdf_report.get("sha256") != sha256(pdf)
    ):
        raise RuntimeError("Dark-Medium PDF inspection record does not match its artifact")
    if (
        visual_review.get("file") != pdf.name
        or visual_review.get("sha256") != sha256(pdf)
        or visual_review.get("page_count") != pdf_report.get("pages")
        or visual_review.get("render_dpi", 0) < 144
        or visual_review.get("result") != "PASS"
    ):
        raise RuntimeError("Dark-Medium visual-review record does not bind the inspected PDF")
    reviewed_pages = visual_review.get("reviewed_pages")
    if (
        not isinstance(reviewed_pages, list)
        or [item.get("page") for item in reviewed_pages if isinstance(item, dict)]
        != list(range(1, int(pdf_report["pages"]) + 1))
        or any(not isinstance(item, dict) or item.get("status") != "PASS" for item in reviewed_pages)
    ):
        raise RuntimeError("Dark-Medium visual review is not a complete passing page record")

    canonical = "https://jkolantree.github.io/astra/resources/dark-medium-response-atlas/v0.1.0/"
    if (
        identity.get("canonical_url") != canonical
        or identity.get("publication_line_id") != spec["publication_line_id"]
        or identity.get("version") != spec["version"]
        or identity.get("pdf_pages") != pdf_report.get("pages")
        or identity.get("pdf_normalized_text_sha256")
        != pdf_report.get("normalized_text_sha256")
    ):
        raise RuntimeError("Dark-Medium publication identity does not match the package")
    expected_identity_artifacts = [
        _atlas_file_record(path)
        for path in (html, pdf, package / "html-accessibility.json", package / "pdf-inspection.json")
    ]
    if identity.get("artifacts") != expected_identity_artifacts:
        raise RuntimeError("Dark-Medium publication identity artifact roster drifted")

    source_rows = _atlas_csv(
        package / "source-ledger.csv",
        {
            "source_id",
            "title",
            "authors_or_group",
            "record_date",
            "venue_or_record",
            "canonical_url",
            "identifier",
            "record_status",
            "rights_status",
            "role",
            "source_bytes_archived",
            "alias_of",
            "notes",
        },
    )
    source_ids = {row["source_id"] for row in source_rows}
    if len(source_ids) != len(source_rows) or any(not value.startswith("S") for value in source_ids):
        raise RuntimeError("Dark-Medium source ledger identifiers are not unique")
    claim_rows = _atlas_csv(
        package / "claim-ledger.csv",
        {
            "claim_id",
            "claim_type",
            "claim_statement",
            "assumptions_or_boundary",
            "observable_or_endpoint",
            "null_model",
            "falsifier_or_next_test",
            "source_ids",
            "evidence_status",
            "disposition",
            "limitations",
        },
    )
    claim_ids = [row["claim_id"] for row in claim_rows]
    if len(set(claim_ids)) != len(claim_ids) or any(not value.startswith("DMA-") for value in claim_ids):
        raise RuntimeError("Dark-Medium claim identifiers are not unique")
    for row in claim_rows:
        declared = [value.strip() for value in row["source_ids"].split(";") if value.strip()]
        if not declared or not set(declared) <= source_ids:
            raise RuntimeError(f"Dark-Medium claim has unknown source IDs: {row['claim_id']}")
    novelty_rows = _atlas_csv(
        package / "novelty-ledger.csv",
        {
            "novelty_id",
            "proposition",
            "contribution_type",
            "prior_art_source_ids",
            "delta_from_prior",
            "predicted_artifact",
            "falsifier_or_stop",
            "search_scope",
            "novelty_status",
            "evidence_status",
            "priority_language",
        },
    )
    for row in novelty_rows:
        declared = [value.strip() for value in row["prior_art_source_ids"].split(";") if value.strip()]
        if not declared or not set(declared) <= source_ids:
            raise RuntimeError(f"Dark-Medium novelty row has unknown sources: {row['novelty_id']}")
        if not row["priority_language"].strip():
            raise RuntimeError(f"Dark-Medium novelty row lacks its priority-language field: {row['novelty_id']}")

    observations = json.loads(
        (package / "external-link-observations.json").read_text(encoding="utf-8")
    )
    records = observations.get("observations") if isinstance(observations, dict) else None
    if not isinstance(records, list) or not records or observations.get("generated_at") is None:
        raise RuntimeError("Dark-Medium external-link audit has not been recorded")
    urls = [item.get("url") for item in records if isinstance(item, dict)]
    if urls != sorted(set(urls)) or any(item.get("outcome") in {"missing", "not_checked"} for item in records):
        raise RuntimeError("Dark-Medium external-link audit is incomplete or has a definite failure")

    readme = (package / "README.md").read_text(encoding="utf-8")
    source = (package / "dark-medium-response-atlas-v0.1.0.md").read_text(encoding="utf-8")
    public_text = re.sub(r"\s+", " ", readme + "\n" + source).casefold()
    for boundary in (
        "not peer reviewed",
        "did not claim a dark-matter detection",
        "not the citation identity",
    ):
        if boundary not in public_text:
            raise RuntimeError(f"Dark-Medium public boundary is absent: {boundary}")


def check_publication_map() -> None:
    readme = " ".join((ROOT / "README.md").read_text(encoding="utf-8").replace("**", "").split())
    required_readme_values = (
        "SPPT/ASTRA v1.0.7 is the Current core reference",
        "Dark-Medium Response Atlas v0.1.0",
        "Working paper",
        "not peer reviewed",
        "methods proposals, not empirical validation",
        "publication history",
        "repository-level `CITATION.cff` belongs only to the Current SPPT/ASTRA core",
        "REPRODUCING.md",
        "PROVENANCE.md",
        "CONTRIBUTING.md",
        "release assets and checksums are the fixed distribution record",
    )
    for value in required_readme_values:
        if value not in readme:
            raise RuntimeError(f"Root publication map omits: {value}")
    if "| Publication track |" in readme:
        raise RuntimeError("Root publication map regressed to a wide narrow-screen table")

    publications = " ".join(
        (ROOT / "PUBLICATIONS.md")
        .read_text(encoding="utf-8")
        .replace("*", "")
        .replace("`", "")
        .split()
    )
    for value in (
        "2026-09-01 as the artifact and edition date",
        "creation of the annotated tag and publication of the release on 2026-09-02",
        "GitHub release display label, Dark-Medium Response Atlas v0.1.0, is abbreviated",
        "Dark-Medium Response Atlas v0.1.0 — Path, Compensation, Memory, and Observation",
        "immutable v0.1.0 files and release assets remain unchanged",
    ):
        if value not in publications:
            raise RuntimeError(f"Publication history omits Atlas metadata clarification: {value}")

    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    for heading in (
        "## Unreleased",
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
        "v1.0.7 reference package" not in evidence_readme
        or "--all --workers 4" not in evidence_readme
        or "claim_source_coverage_v1.0.7_maintenance_overlay_m1.json" not in evidence_readme
        or "does not amend" not in evidence_readme
        or "dark_medium_response_atlas_publication_successor_overlay_s2.json"
        not in evidence_readme
        or "no peer-review, empirical-validation, priority, DOI, core-claim, or"
        not in evidence_readme
    ):
        raise RuntimeError(
            "Evidence README does not identify the release, overlay boundary, and command"
        )
    schemas_readme = (ROOT / "schemas" / "README.md").read_text(encoding="utf-8")
    if (
        "currently **v1.0.7**" not in schemas_readme
        or "Supplemental resources" not in schemas_readme
        or "claim-source-coverage-overlay-m1.schema.json" not in schemas_readme
        or "dark-medium-response-atlas-publication-successor-overlay-s2.schema.json"
        not in schemas_readme
        or "supplemental-release-identity-v2.schema.json" not in schemas_readme
    ):
        raise RuntimeError(
            "Schema README does not identify its publication and candidate boundaries"
        )


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
    if not expected_edition_names <= observed_editions:
        raise RuntimeError(
            "Versioned manuscript edition roster differs from the current release: "
            f"expected at least {sorted(expected_edition_names)}, observed {sorted(observed_editions)}"
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
        ROOT / "evidence" / "claim_source_coverage_v1.0.7.json",
        ROOT / "evidence" / "claim_source_coverage_v1.0.7_maintenance_overlay_m1.json",
        ROOT / "evidence" / "dark_medium_response_atlas_successor_overlay_s1.json",
        ROOT / "evidence" / "dark_medium_response_atlas_publication_successor_overlay_s2.json",
        ROOT / "evidence" / "pages_admission_v1.json",
        ROOT / "RUNTIME.json",
        ROOT / "manuscript" / "document_semantic_identity.json",
        ROOT / "manuscript" / "pdf_inspection.json",
        ROOT
        / "resources"
        / "sector-complete-instrument"
        / "v0.1.0-alpha.1"
        / "RELEASE_SPEC.json",
        ROOT
        / "resources"
        / "dark-medium-response-atlas"
        / "v0.1.0"
        / "RELEASE_SPEC.json",
        ROOT
        / "resources"
        / "dark-medium-response-atlas"
        / "v0.1.0"
        / "external-link-observations.json",
        ROOT
        / "resources"
        / "dark-medium-response-atlas"
        / "v0.1.0"
        / "html-accessibility.json",
        ROOT
        / "resources"
        / "dark-medium-response-atlas"
        / "v0.1.0"
        / "pdf-inspection.json",
        ROOT
        / "resources"
        / "dark-medium-response-atlas"
        / "v0.1.0"
        / "publication-identity.json",
        ROOT
        / "resources"
        / "dark-medium-response-atlas"
        / "v0.1.0"
        / "visual-review.json",
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
    check_private_operator_policy_boundary()
    paths = public_files()
    spec = json.loads((ROOT / "RELEASE_SPEC.json").read_text(encoding="utf-8"))
    version = str(spec["version"])
    check_text_privacy(paths)
    check_license_map(paths)
    check_png_metadata(paths)
    check_working_paper_resource()
    check_framework_v030_resource()
    check_sppt_astra_v108_candidate_resource()
    check_dark_medium_response_atlas_resource()
    check_publication_map()
    check_metadata_agreement()
    check_claim_matrix()
    check_source_inventory()
    check_dependency_lock()
    check_public_json_schemas()
    check_runtime_identity()
    check_html(
        ROOT / "manuscript" / f"SPPT_ASTRA_preprint_v{version}.html",
        "SPPT / ASTRA v1.0.7: Stateful Edges and Operator-Aware Inference",
    )
    check_html(
        ROOT / "manuscript" / f"SPPT_ASTRA_technical_supplement_v{version}.html",
        "Technical Supplement: Synthetic Pointwise Topology Selection and Identifiability Limits",
    )
    print(f"Repository contract passed for {len(paths)} public files.")


if __name__ == "__main__":
    main()
