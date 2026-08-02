from __future__ import annotations

import io
import json
import re
from pathlib import Path

import matplotlib
import pikepdf
import pytest

from tools import build_documents, inspect_pdf

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = (ROOT / "manuscript" / "manuscript.md").read_text(encoding="utf-8")
SUPPLEMENT = (ROOT / "manuscript" / "supplement.md").read_text(encoding="utf-8")
BIBLIOGRAPHY = (ROOT / "manuscript" / "references.bib").read_text(encoding="utf-8")


def tagged_table_fixture(
    identifiers: list[str],
    *,
    header_references: list[str] | None = None,
    orphan_identifier: str | None = None,
) -> pikepdf.Pdf:
    pdf = pikepdf.Pdf.new()
    headers = [
        pdf.make_indirect(
            pikepdf.Dictionary(
                {
                    "/Type": pikepdf.Name("/StructElem"),
                    "/S": pikepdf.Name("/TH"),
                    "/ID": pikepdf.String(identifier),
                }
            )
        )
        for identifier in identifiers
    ]
    references = header_references if header_references is not None else identifiers
    data_cell = pdf.make_indirect(
        pikepdf.Dictionary(
            {
                "/Type": pikepdf.Name("/StructElem"),
                "/S": pikepdf.Name("/TD"),
                "/A": pikepdf.Dictionary(
                    {
                        "/O": pikepdf.Name("/Table"),
                        "/Headers": pikepdf.Array(
                            [pikepdf.String(identifier) for identifier in references]
                        ),
                    }
                ),
            }
        )
    )
    structure_root = pdf.make_indirect(
        pikepdf.Dictionary({"/K": pikepdf.Array([*headers, data_cell])})
    )
    name_tree = pikepdf.NameTree.new(pdf)
    for identifier, header in zip(identifiers, headers, strict=True):
        name_tree[identifier] = header
    if orphan_identifier is not None:
        orphan = pdf.make_indirect(
            pikepdf.Dictionary(
                {
                    "/Type": pikepdf.Name("/StructElem"),
                    "/S": pikepdf.Name("/TH"),
                    "/ID": pikepdf.String(orphan_identifier),
                }
            )
        )
        name_tree[orphan_identifier] = orphan
    structure_root["/IDTree"] = name_tree.obj
    pdf.Root["/StructTreeRoot"] = structure_root
    return pdf


def deterministic_pdf_bytes(pdf: pikepdf.Pdf) -> bytes:
    if "/ID" in pdf.trailer:
        del pdf.trailer["/ID"]
    stream = io.BytesIO()
    pdf.save(
        stream,
        deterministic_id=True,
        object_stream_mode=pikepdf.ObjectStreamMode.generate,
        compress_streams=True,
    )
    return stream.getvalue()


def test_released_bibliography_entry_count_is_frozen() -> None:
    assert len(re.findall(r"(?m)^@", BIBLIOGRAPHY)) == 42


def test_tagged_structure_allocator_ids_are_canonicalized_by_logical_order() -> None:
    first = tagged_table_fixture(["node00001650", "node00001651"])
    second = tagged_table_fixture(["node00001649", "node00001650"])
    build_documents.canonicalize_structure_ids(first)
    build_documents.canonicalize_structure_ids(second)
    assert inspect_pdf.validate_structure_identifiers(first) == {
        "canonical_structure_id_count": 2,
        "table_header_reference_count": 2,
    }
    assert inspect_pdf.validate_structure_identifiers(second) == {
        "canonical_structure_id_count": 2,
        "table_header_reference_count": 2,
    }
    assert deterministic_pdf_bytes(first) == deterministic_pdf_bytes(second)


def test_pdf_sanitizer_canonicalizes_structure_and_permanent_trailer_id(
    tmp_path: Path,
) -> None:
    first = tagged_table_fixture(["node00001650", "node00001651"])
    second = tagged_table_fixture(["node00001649", "node00001650"])
    raw_first = tmp_path / "raw-first.pdf"
    raw_second = tmp_path / "raw-second.pdf"
    output_first = tmp_path / "output-first.pdf"
    output_second = tmp_path / "output-second.pdf"
    first.save(raw_first, deterministic_id=True)
    second.save(raw_second, deterministic_id=True)
    first.close()
    second.close()
    assert raw_first.read_bytes() != raw_second.read_bytes()

    build_documents.sanitize_pdf(raw_first, output_first, "Tagged PDF fixture")
    build_documents.sanitize_pdf(raw_second, output_second, "Tagged PDF fixture")
    assert output_first.read_bytes() == output_second.read_bytes()
    with pikepdf.open(output_first) as canonical:
        assert inspect_pdf.validate_structure_identifiers(canonical) == {
            "canonical_structure_id_count": 2,
            "table_header_reference_count": 2,
        }


def test_duplicate_tagged_structure_id_is_rejected() -> None:
    pdf = tagged_table_fixture(["node00000001", "node00000001"])
    with pytest.raises(RuntimeError, match="Duplicate tagged-PDF structure IDs"):
        build_documents.canonicalize_structure_ids(pdf)


def test_orphan_tagged_structure_id_is_rejected() -> None:
    pdf = tagged_table_fixture(["node00000001"], orphan_identifier="node00000002")
    with pytest.raises(RuntimeError, match="IDTree is not closed"):
        build_documents.canonicalize_structure_ids(pdf)


def test_unresolved_tagged_table_header_is_rejected() -> None:
    pdf = tagged_table_fixture(
        ["node00000001"], header_references=["node00000002"]
    )
    with pytest.raises(RuntimeError, match="header reference is unresolved"):
        build_documents.canonicalize_structure_ids(pdf)


def test_current_arxiv_author_spellings_are_canonical() -> None:
    assert "Delaye, Lukas" in BIBLIOGRAPHY
    assert (
        "Riegler, Ben and Calder, Robb and Fortuin, Vincent" in BIBLIOGRAPHY
    )


def test_private_and_machine_local_metadata_are_absent() -> None:
    public_text = "\n".join((MANUSCRIPT, SUPPLEMENT, BIBLIOGRAPHY))
    for forbidden_pattern in (
        r"^\s*(?:contact|correspondence)\s*[:=]\s*(?:TBD|TODO|pending|placeholder)\b",
        r"/usr/share/",
        r"[A-Za-z]:\\",
        r"\b[A-Z][A-Za-z .'-]+,\s*(?:USA|United States)\b",
    ):
        assert (
            re.search(
                forbidden_pattern,
                public_text,
                flags=re.IGNORECASE | re.MULTILINE,
            )
            is None
        )
    assert "https://github.com/jkolantree/astra/issues" in MANUSCRIPT


def test_unsupported_blinding_claim_is_absent() -> None:
    for unsupported in (
        "A blinded three-reservoir",
        "a blinded three-reservoir",
        "blinded validation establishes",
        "blinded benchmark establishes",
    ):
        assert unsupported not in MANUSCRIPT
        assert unsupported not in SUPPLEMENT
    assert "neither blind nor external validation" in MANUSCRIPT
    assert "not untouched, blinded, or external evaluation" in MANUSCRIPT
    assert "not blinded or external validation" in SUPPLEMENT


def test_required_mathematical_hypotheses_are_explicit() -> None:
    for phrase in (
        "every node capacity be strictly positive",
        "positive-weight conductance graph be connected",
        "nonempty proper node set",
        "fixed conductance $K>0$",
        "injective on the declared physical temperature domain",
        "lies in the range of $L$",
        "simultaneous-guard priority",
        "reset-map closure",
        "Zeno accumulation",
        "symmetric positive-definite noise covariance",
    ):
        assert phrase in MANUSCRIPT


def test_required_scientific_qualifications_are_explicit() -> None:
    for phrase in (
        "raw inventory-loop magnitude increases monotonically",
        "maximal at $\\omega\\tau_r=1$",
        "substrate-dependent wetting factor",
        "supplied electrochemical free energy",
        "not latent heat",
        "neither blind nor external validation",
        "triangle also attains a smaller held-out RMSE",
        "none of the four studies validates SPPT",
        "edge-type substitution",
        "Neither the dream, the collage, nor model output is scientific evidence",
    ):
        assert phrase in MANUSCRIPT


def test_citation_keys_resolve_and_known_failures_are_removed() -> None:
    citation_keys = set(re.findall(r"@([A-Za-z0-9_:-]+)", MANUSCRIPT))
    bib_keys = set(re.findall(r"^@[A-Za-z]+\{([^,]+),", BIBLIOGRAPHY, flags=re.MULTILINE))
    assert citation_keys <= bib_keys
    assert "pages = {5045}" in BIBLIOGRAPHY
    assert "Delaye, Lukas" in BIBLIOGRAPHY
    assert "van den Berg, Arie" in BIBLIOGRAPHY
    assert "Kaare, Kätlin and Scarlat, Raluca O." in BIBLIOGRAPHY
    for doi in (
        "10.1080/1751696X.2026.2696260",
        "10.1038/s41598-026-46683-8",
        "10.1016/j.cell.2026.05.016",
    ):
        assert doi in BIBLIOGRAPHY
    assert "arXiv:2607.25941v1" in BIBLIOGRAPHY
    assert "https://arxiv.org/abs/2607.25941" in BIBLIOGRAPHY
    assert "10.48550/arXiv.2607.25941" not in BIBLIOGRAPHY
    assert "Nature Communications 15, 5169" not in BIBLIOGRAPHY


def test_proprietary_or_machine_pdf_font_is_rejected() -> None:
    records = [
        {
            "base_font": "/AAAAAA+TimesNewRomanPSMT",
            "subtype": "/Type0",
            "embedded": True,
            "to_unicode": True,
        }
    ]
    with pytest.raises(RuntimeError, match="Unexpected PDF font"):
        inspect_pdf.validate_pdf_font_records(records)


def test_bundled_font_source_mutation_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    font_dir = tmp_path / "fonts" / "ttf"
    font_dir.mkdir(parents=True)
    font_path = font_dir / "fixture.ttf"
    font_path.write_bytes(b"font")
    runtime = {
        "pdf_renderer": {
            "font_sources": {
                "provider": f"matplotlib {matplotlib.__version__}",
                "files": [
                    {
                        "file": font_path.name,
                        "bytes": font_path.stat().st_size,
                        "sha256": inspect_pdf.sha256_path(font_path),
                    }
                ],
            }
        }
    }
    (tmp_path / "RUNTIME.json").write_text(
        json.dumps(runtime), encoding="utf-8", newline="\n"
    )
    monkeypatch.setattr(inspect_pdf, "ROOT", tmp_path)
    monkeypatch.setattr(matplotlib, "get_data_path", lambda: str(tmp_path))
    records = [{"base_font": "/DejaVu"}, {"base_font": "/STIXGeneral"}]
    inspect_pdf.verify_bundled_font_sources(records)
    font_path.write_bytes(b"font!")
    with pytest.raises(RuntimeError, match="source-font identity drift"):
        inspect_pdf.verify_bundled_font_sources(records)
