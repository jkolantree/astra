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

from PIL import Image
from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[1]
IGNORED_ROOTS = {".git", ".venv", ".pytest_cache", ".mypy_cache", ".ruff_cache", "tmp", "dist", "build"}
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
    "RELEASE_NOTES_v1.0.1.md",
    "RELEASE_NOTES_v1.0.2.md",
    "RELEASE_NOTES_v1.0.3.md",
    "RELEASE_NOTES_v1.0.4.md",
    "RELEASE_NOTES_v1.0.5.md",
    "RELEASE_SPEC.json",
    "RUNTIME.json",
    "SOURCE_INVENTORY.json",
    "THIRD_PARTY_NOTICES.md",
    "pyproject.toml",
    "requirements.in",
    "requirements-lock.txt",
}
DIRECTORY_RULES = {
    ".github/workflows": {".yml", ".yaml"},
    "data": {".csv", ".json"},
    "evidence": {".md", ".txt"},
    "figures": {".png", ".pdf"},
    "licenses": {".txt"},
    "manuscript": {".bib", ".css", ".html", ".json", ".md", ".pdf"},
    "scripts": {".py"},
    "src": {".py"},
    "tests": {".py"},
    "tools": {".py"},
}
TEXT_SUFFIXES = {"", ".bib", ".cff", ".css", ".csv", ".in", ".json", ".md", ".py", ".toml", ".txt", ".yaml", ".yml"}
PRIVATE_PATTERNS = {
    "local Windows path": re.compile(r"[A-Za-z]:\\", re.IGNORECASE),
    "local POSIX path": re.compile(r"(?:/Users/|/home/|/usr/share/)", re.IGNORECASE),
    "private location": re.compile(
        r"\b[A-Z][A-Za-z .'-]+,\s*(?:USA|United States)\b"
    ),
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
            matched = next((root for root in DIRECTORY_RULES if parent == root or parent.startswith(root + "/")), None)
            if matched is None or path.suffix.lower() not in DIRECTORY_RULES[matched]:
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
        self.table_headers = 0
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
        elif tag == "th":
            self.table_headers += 1
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
    if parser.tables and parser.table_headers < parser.tables:
        failures.append(f"table header count {parser.table_headers} for {parser.tables} tables")
    if parser.math < 1:
        failures.append("no structured MathML")
    if parser.main != 1 or parser.nav != 1 or parser.skip_link != 1:
        failures.append(
            f"landmarks main={parser.main} nav={parser.nav} skip={parser.skip_link}"
        )
    if parser.external_resources:
        failures.append(f"non-embedded resources: {parser.external_resources[:3]}")
    for href in parser.links:
        if not href:
            continue
        parsed = urlparse(href)
        if parsed.scheme and parsed.scheme not in {"http", "https"}:
            failures.append(f"unsafe link scheme: {href}")
    if PRIVATE_PATTERNS["local Windows path"].search(text) or PRIVATE_PATTERNS["local POSIX path"].search(text):
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
    parsed_epoch = datetime.strptime(build_epoch, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=UTC
    )
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
    preferred = citation.get("preferred-citation", {})
    if str(preferred.get("version")) != version or preferred.get("url") != (
        f"{spec['repository']}/releases/tag/{tag}"
    ):
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
    required_readme_values = (*expected_documents, f"{spec['repository']}/releases/tag/{tag}")
    if any(value not in readme for value in required_readme_values):
        raise RuntimeError("README current-release links differ from RELEASE_SPEC.json")

    identity = json.loads(
        (ROOT / "manuscript" / "document_semantic_identity.json").read_text(
            encoding="utf-8"
        )
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
        item["sha256"] for item in artifacts if item["canonical_relative_path"].endswith("preprint_v1.0.1.pdf")
    )
    if len(aliases) != 1 or aliases[0]["sha256"] != preprint_hash:
        raise RuntimeError("The byte-identical PDF alias relationship is not preserved")
    ensemble_relationships = [
        item["relationship"] for item in artifacts if "synthetic_topology_ensemble" in item["canonical_relative_path"]
    ]
    if len(ensemble_relationships) != 2 or not all("not independent evidence" in value for value in ensemble_relationships):
        raise RuntimeError("Duplicate CSV/JSON evidence is not explicitly deduplicated")
    synthesis = next(
        item for item in artifacts if item["canonical_relative_path"] == "pasted-text.txt"
    )
    if "not independent evidence" not in synthesis["relationship"] or "not redistributed verbatim" not in synthesis["rights_status"]:
        raise RuntimeError("Author-supplied synthesis must remain excluded as independent or verbatim evidence")


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
    check_metadata_agreement()
    check_claim_matrix()
    check_source_inventory()
    check_dependency_lock()
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
