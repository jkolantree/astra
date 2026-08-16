from __future__ import annotations

import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from pypdf import PdfReader

from tools import check_repository

ROOT = Path(__file__).resolve().parents[1]
RESOURCE = ROOT / "resources" / "earth-is-the-instrument" / "v0.1"
PDF = RESOURCE / "ASTRA_Earth_Is_the_Instrument_Working_Paper_v0.1.pdf"
FRAMEWORK_RESOURCE = ROOT / "resources" / "earth-is-the-instrument" / "v0.3.0"
V108_RESOURCE = ROOT / check_repository.SPPT_ASTRA_V108_CANDIDATE_ROOT
V108_PACKAGE = V108_RESOURCE / "package"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_working_paper_resource_contract() -> None:
    check_repository.check_working_paper_resource()


def test_working_paper_has_text_first_publication_boundary() -> None:
    text = (RESOURCE / "README.md").read_text(encoding="utf-8")
    semantic_text = " ".join(text.replace("**", "").split())
    assert "not peer reviewed" in semantic_text
    assert "does not amend or supersede SPPT/ASTRA v1.0.6" in semantic_text
    assert "not a tagged PDF" in semantic_text
    assert "### Figure descriptions" in text
    assert "issues/new?template=accessibility.yml" in text
    for label in (
        "Seven 2026 signals:",
        "Plate-boundary classes:",
        "Distributed geological nursery:",
        "Boundary-state ladder:",
        "Geology as archive and censor:",
        "Monuments as reorganized geology:",
        "Candidate origin stories:",
        "ASTRA instrument test:",
    ):
        assert label in semantic_text


def test_working_paper_pdf_is_searchable_but_not_claimed_as_tagged() -> None:
    reader = PdfReader(PDF)
    assert len(reader.pages) == 44
    assert reader.metadata is not None
    assert reader.metadata.title == "Earth Is the Instrument"
    assert all((page.extract_text() or "").strip() for page in reader.pages)
    assert "/StructTreeRoot" not in reader.root_object


def test_framework_v030_resource_contract() -> None:
    check_repository.check_framework_v030_resource()


def test_framework_v030_has_separate_version_and_evidence_boundaries() -> None:
    text = (FRAMEWORK_RESOURCE / "README.md").read_text(encoding="utf-8")
    semantic_text = " ".join(text.replace("**", "").split())
    for required in (
        "not peer reviewed",
        "supersedes the internal v0.2.1 predecessor preserved inside its release archive",
        "no public v0.2.1 tag or GitHub Release was created",
        "does not amend or supersede the immutable SPPT/ASTRA v1.0.6",
        "24 PASS, 2 PARTIAL, and 0 FAIL",
        "not external scientific review or endorsement",
        "not claimed as PDF/UA-conformant or fully accessible",
        "29 isolated regression tests",
        "90 of 90 checks",
        "does not freeze a complete TeX environment",
        "without publishing private object identifiers",
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
    ):
        assert required in semantic_text
    assert "The four preserved PDFs already disclose" not in semantic_text
    citation_text = " ".join(text.replace("*", "").replace(">", "").split())
    assert (
        "Jacko T. (2026). Earth Is the Instrument: Dual-Rent Seams, Prime Spectra, "
        "Local-to-Global Certificates, Geological Memory, and the Search for Human "
        "Origins. ASTRA Framework v0.3.0. GitHub."
    ) in citation_text


def test_framework_v030_errata_match_pdf_disclosures_and_immutable_scope() -> None:
    errata = " ".join(
        (FRAMEWORK_RESOURCE / "ERRATA.md").read_text(encoding="utf-8").replace("**", "").split()
    )
    assert "The 171-page main framework PDF contains that disclosure" in errata
    assert "The public ground reading, audit form, and verification report do not" in errata
    assert "No public v0.2.1 tag or GitHub Release was created" in errata
    assert "does not replace, edit, or reissue any PDF" in errata

    pdf_text = {
        path.name: "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
        for path in FRAMEWORK_RESOURCE.glob("*.pdf")
    }
    main = pdf_text["ASTRA_Framework_v0.3.0_Earth_Is_The_Instrument.pdf"]
    assert "Language-model assistance" in main
    assert "Authorial responsibility" in main
    for name, text in pdf_text.items():
        if name != "ASTRA_Framework_v0.3.0_Earth_Is_The_Instrument.pdf":
            assert "Language-model assistance" not in text


def test_framework_v030_release_checksums_bind_ten_payloads() -> None:
    lines = (FRAMEWORK_RESOURCE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 10
    names = {line.split("  ", 1)[1] for line in lines}
    assert names == set(check_repository.FRAMEWORK_RELEASE_PAYLOADS)
    assert {
        "ASTRA_Framework_v0.3.0_Dual_Rent_Arithmetic_Seams.zip",
        "ASTRA_Framework_v0.3.0_Dual_Rent_Arithmetic_Seams.zip.sha256",
        "ASTRA_Framework_v0.3.0_Dual_Rent_Arithmetic_Seams.zip.verify.txt",
        "FONT_NOTICES.txt",
        "PUBLICATION_AUDIT.md",
        "cover.png",
    } <= names


@pytest.mark.parametrize(
    ("name", "pages"),
    (
        ("ASTRA_Dual_Rent_Local_to_Global_Audit_Form_v0.3.0.pdf", 1),
        ("ASTRA_Framework_v0.3.0_Earth_Is_The_Instrument.pdf", 171),
        ("ASTRA_v0.3.0_Public_Ground_Reading.pdf", 2),
        ("ASTRA_v0.3.0_Verification_Report.pdf", 3),
    ),
)
def test_framework_v030_pdfs_are_tagged_searchable_and_bounded(name: str, pages: int) -> None:
    reader = PdfReader(FRAMEWORK_RESOURCE / name)
    assert len(reader.pages) == pages
    assert str(reader.root_object.get("/Lang")) == "en-US"
    assert "/StructTreeRoot" in reader.root_object
    assert reader.get_fields() is None
    assert list(reader.attachments) == []
    assert all((page.extract_text() or "").strip() for page in reader.pages)


def test_sppt_astra_v108_candidate_resource_contract() -> None:
    check_repository.check_sppt_astra_v108_candidate_resource()


def test_sppt_astra_v108_candidate_is_explicitly_unpromoted_and_origin_bound() -> None:
    text = " ".join((V108_RESOURCE / "README.md").read_text(encoding="utf-8").split())
    assert "Status: repository-visible, unpromoted successor candidate." in text
    assert "not the stable SPPT/ASTRA release" in text
    assert "not peer reviewed" in text
    assert "no tag, GitHub Release, Pages route, DOI, or Zenodo record" in text
    assert "Immutable SPPT/ASTRA v1.0.7 remains the stable citation target." in text
    assert check_repository.SPPT_ASTRA_V108_FROZEN_COMMIT in text
    assert check_repository.SPPT_ASTRA_V108_ORIGIN_SHA256 in text


def test_sppt_astra_v108_candidate_remains_under_privacy_and_license_checks() -> None:
    paths = [
        V108_RESOURCE / relative for relative in check_repository.SPPT_ASTRA_V108_CANDIDATE_FILES
    ]
    fixture_exemptions = {
        path.relative_to(ROOT).as_posix()
        for path in paths
        if path.relative_to(ROOT).as_posix() in check_repository.PATTERN_FIXTURE_FILES
    }
    assert fixture_exemptions == set()
    check_repository.check_text_privacy(paths)
    check_repository.check_license_map(paths)
    check_repository.check_png_metadata(paths)


def test_sppt_astra_v108_ledger_preserves_v107_ids_and_adds_20_without_collision() -> None:
    matrix_path = ROOT / "CLAIM_MATRIX.json"
    embedded_matrix_path = V108_PACKAGE / "source" / "CLAIM_MATRIX_v1.0.7.json"
    assert file_sha256(matrix_path) == check_repository.SPPT_ASTRA_V107_MATRIX_SHA256
    assert file_sha256(embedded_matrix_path) == check_repository.SPPT_ASTRA_V107_MATRIX_SHA256
    assert embedded_matrix_path.read_bytes() == matrix_path.read_bytes()

    matrix = json.loads(embedded_matrix_path.read_text(encoding="utf-8"))
    additions = json.loads(
        (V108_PACKAGE / "source" / "claim_ledger_v1.0.8_additions.json").read_text(encoding="utf-8")
    )
    ledger = json.loads((V108_PACKAGE / "claim_ledger.json").read_text(encoding="utf-8"))
    canonical_claims = matrix["claims"]
    canonical_ids = [claim["id"] for claim in canonical_claims]
    addition_ids = [claim["claim_id"] for claim in additions]
    ledger_ids = [claim["claim_id"] for claim in ledger]

    assert len(canonical_claims) == len(set(canonical_ids)) == 55
    assert len(additions) == len(set(addition_ids)) == 20
    assert set(canonical_ids).isdisjoint(addition_ids)
    assert all(claim_id.startswith("V108-") for claim_id in addition_ids)
    assert len(ledger) == len(set(ledger_ids)) == 75
    assert ledger_ids == canonical_ids + addition_ids

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
        assert projected == {
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

    with (V108_PACKAGE / "claim_ledger.csv").open(encoding="utf-8", newline="") as handle:
        assert list(csv.DictReader(handle)) == ledger


def test_sppt_astra_v108_has_exactly_18_live_text_self_contained_figure_pairs() -> None:
    figures = V108_PACKAGE / "figures"
    pngs = sorted(figures.glob("*.png"))
    svgs = sorted(figures.glob("*.svg"))
    expected_stems = set(check_repository.SPPT_ASTRA_V108_FIGURE_STEMS)
    assert len(pngs) == len(svgs) == 18
    assert {path.stem for path in pngs} == expected_stems
    assert {path.stem for path in svgs} == expected_stems

    svg_namespace = "http://www.w3.org/2000/svg"
    dc_namespace = "http://purl.org/dc/elements/1.1/"
    url_pattern = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE)
    for path in svgs:
        raw = path.read_text(encoding="utf-8")
        assert "<!DOCTYPE" not in raw.upper()
        root = ET.fromstring(raw)
        assert any(
            "".join(node.itertext()).strip() for node in root.findall(f".//{{{svg_namespace}}}text")
        )
        metadata = root.find(f"{{{svg_namespace}}}metadata")
        assert metadata is not None
        assert [
            (node.text or "").strip() for node in metadata.findall(f".//{{{dc_namespace}}}date")
        ] == [check_repository.SPPT_ASTRA_V108_SVG_DATE]
        assert [
            (node.text or "").strip()
            for node in metadata.findall(f".//{{{dc_namespace}}}description")
        ] == ["Original ASTRA candidate figure"]
        assert [
            (node.text or "").strip() for node in metadata.findall(f".//{{{dc_namespace}}}format")
        ] == ["image/svg+xml"]
        assert [
            (node.text or "").strip() for node in metadata.findall(f".//{{{dc_namespace}}}title")
        ] == ["ASTRA / Jacko T."]
        for element in root.iter():
            assert element.tag.rsplit("}", 1)[-1] not in {"foreignObject", "script"}
            values = [*element.attrib.values(), element.text or ""]
            for attribute, value in element.attrib.items():
                if attribute.rsplit("}", 1)[-1] in {"href", "src"}:
                    assert value.startswith(("#", "data:"))
            assert all("@import" not in value.lower() for value in values)
            assert all(
                match.group(2).strip().startswith("#")
                for value in values
                for match in url_pattern.finditer(value)
            )


def test_sppt_astra_v108_manifest_and_checksums_bind_exact_package_bytes() -> None:
    package_files = {
        path.relative_to(V108_PACKAGE).as_posix()
        for path in V108_PACKAGE.rglob("*")
        if path.is_file()
    }
    sums_path = V108_PACKAGE / "SHA256SUMS.txt"
    checksum_lines = sums_path.read_text(encoding="utf-8").splitlines()
    checksum_records: dict[str, str] = {}
    checksum_names: list[str] = []
    for line in checksum_lines:
        match = re.fullmatch(r"([0-9a-f]{64})  ([^\r\n]+)", line)
        assert match is not None
        digest, name = match.groups()
        assert name not in checksum_records
        checksum_records[name] = digest
        checksum_names.append(name)
    assert checksum_names == sorted(checksum_names)
    assert set(checksum_names) == package_files - {"SHA256SUMS.txt"}
    assert all(
        file_sha256(V108_PACKAGE / name) == digest for name, digest in checksum_records.items()
    )

    manifest = json.loads(
        (V108_PACKAGE / "candidate_package_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["status"] == "reviewed_unpromoted_candidate"
    assert manifest["source_package_sha256"] == check_repository.SPPT_ASTRA_V108_ORIGIN_SHA256
    assert manifest["repository_basis"]["audited_commit"] == (
        check_repository.SPPT_ASTRA_V108_FROZEN_COMMIT
    )
    assert manifest["repository_basis"]["stable_release"] == "v1.0.7"
    assert manifest["verification"]["verdict"] == "REVIEWED_UNPROMOTED_CANDIDATE"
    payload = manifest["payload"]
    payload_names = [entry["path"] for entry in payload]
    expected_payload = package_files - {"SHA256SUMS.txt", "candidate_package_manifest.json"}
    assert payload_names == sorted(payload_names)
    assert set(payload_names) == expected_payload
    assert len(payload_names) == manifest["payload_file_count_excluding_manifest_and_sha256sums"]
    assert (
        sum((V108_PACKAGE / name).stat().st_size for name in payload_names)
        == manifest["payload_total_bytes_excluding_manifest_and_sha256sums"]
    )
    for entry in payload:
        path = V108_PACKAGE / entry["path"]
        assert set(entry) == {"path", "bytes", "sha256"}
        assert entry["bytes"] == path.stat().st_size
        assert entry["sha256"] == file_sha256(path)


def test_candidate_docx_suffix_is_admitted_only_at_the_exact_contract_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    exact = tmp_path / check_repository.SPPT_ASTRA_V108_DOCX_PATH
    exact.parent.mkdir(parents=True)
    exact.write_bytes(b"candidate-docx")
    monkeypatch.setattr(check_repository, "ROOT", tmp_path)
    assert [path.relative_to(tmp_path).as_posix() for path in check_repository.public_files()] == [
        check_repository.SPPT_ASTRA_V108_DOCX_PATH
    ]

    rogue = exact.with_name("unregistered.docx")
    rogue.write_bytes(b"rogue-docx")
    with pytest.raises(RuntimeError, match="Unregistered supplemental resource"):
        check_repository.public_files()


@pytest.mark.parametrize(
    "relative",
    (
        "resources/earth-is-the-instrument/v0.1/nested/unreviewed.pdf",
        "resources/unregistered/v0.1/README.md",
        "resources/sppt-astra-v1.0.8-candidate/package/unregistered.docx",
    ),
)
def test_public_files_rejects_unregistered_resources(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, relative: str
) -> None:
    unexpected = tmp_path / relative
    unexpected.parent.mkdir(parents=True)
    unexpected.write_bytes(b"unreviewed")
    monkeypatch.setattr(check_repository, "ROOT", tmp_path)
    with pytest.raises(RuntimeError, match="Unregistered supplemental resource"):
        check_repository.public_files()
