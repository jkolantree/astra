from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfReader

from tools import check_repository

ROOT = Path(__file__).resolve().parents[1]
RESOURCE = ROOT / "resources" / "earth-is-the-instrument" / "v0.1"
PDF = RESOURCE / "ASTRA_Earth_Is_the_Instrument_Working_Paper_v0.1.pdf"
FRAMEWORK_RESOURCE = ROOT / "resources" / "earth-is-the-instrument" / "v0.3.0"


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
        "supersedes v0.2.1 only within this supplemental publication line",
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
        "b2a1072c14f1afff43a161b57620cdd2f6ad19b03884e7b5d8fbdd023333e09d",
    ):
        assert required in semantic_text


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
def test_framework_v030_pdfs_are_tagged_searchable_and_bounded(
    name: str, pages: int
) -> None:
    reader = PdfReader(FRAMEWORK_RESOURCE / name)
    assert len(reader.pages) == pages
    assert str(reader.root_object.get("/Lang")) == "en-US"
    assert "/StructTreeRoot" in reader.root_object
    assert reader.get_fields() is None
    assert list(reader.attachments) == []
    assert all((page.extract_text() or "").strip() for page in reader.pages)


@pytest.mark.parametrize(
    "relative",
    (
        "resources/earth-is-the-instrument/v0.1/nested/unreviewed.pdf",
        "resources/unregistered/v0.1/README.md",
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
