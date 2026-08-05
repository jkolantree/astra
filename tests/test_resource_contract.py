from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfReader

from tools import check_repository

ROOT = Path(__file__).resolve().parents[1]
RESOURCE = ROOT / "resources" / "earth-is-the-instrument" / "v0.1"
PDF = RESOURCE / "ASTRA_Earth_Is_the_Instrument_Working_Paper_v0.1.pdf"


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
