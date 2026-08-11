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
CLAIM_MATRIX_PATH = ROOT / "CLAIM_MATRIX.json"
COVERAGE_PATH = ROOT / "evidence" / "claim_source_coverage_v1.0.7.json"


def markdown_section(start_heading: str, end_heading: str) -> str:
    start = MANUSCRIPT.index(start_heading)
    end = MANUSCRIPT.index(end_heading, start)
    return MANUSCRIPT[start:end]


def normalize_markdown_cell(value: str) -> str:
    """Normalize only escaped table pipes and Markdown-insignificant whitespace."""
    return re.sub(r"\s+", " ", value.replace(r"\|", "|").strip())


def appendix_b_claim_rows() -> list[tuple[str, str, str, str]]:
    appendix = markdown_section(
        "# Appendix B - v1.0.7 atomic claims",
        "# Appendix C - Repository snapshot",
    )
    lines = appendix.splitlines()
    header_index = next(
        index for index, line in enumerate(lines) if re.match(r"^\|\s*ID\s*\|", line)
    )
    assert re.match(r"^\|\s*-+\s*\|", lines[header_index + 1])
    rows: list[tuple[str, str, str, str]] = []
    for line in lines[header_index + 2 :]:
        if not line.startswith("|"):
            break
        cells = [
            normalize_markdown_cell(cell)
            for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))
        ]
        assert len(cells) == 4, f"Malformed Appendix B claim row: {line}"
        rows.append((cells[0], cells[1], cells[2], cells[3]))
    return rows


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


def tagged_semantic_fixture() -> tuple[pikepdf.Pdf, pikepdf.Object, pikepdf.Object]:
    pdf = pikepdf.Pdf.new()
    image = pdf.make_indirect(
        pikepdf.Dictionary(
            {
                "/Type": pikepdf.Name("/StructElem"),
                "/S": pikepdf.Name("/Figure"),
                "/Alt": pikepdf.String("Labeled scientific figure"),
                "/Pg": pikepdf.Dictionary(),
                "/K": 1,
            }
        )
    )
    formula = pdf.make_indirect(
        pikepdf.Dictionary(
            {
                "/Type": pikepdf.Name("/StructElem"),
                "/S": pikepdf.Name("/Figure"),
                "/Alt": pikepdf.String("Formula in TeX: x^2"),
                "/Pg": pikepdf.Dictionary(),
                "/K": 2,
            }
        )
    )
    outer = pdf.make_indirect(
        pikepdf.Dictionary(
            {
                "/Type": pikepdf.Name("/StructElem"),
                "/S": pikepdf.Name("/Figure"),
                "/K": pikepdf.Array([image, formula]),
            }
        )
    )
    pdf.Root["/StructTreeRoot"] = pdf.make_indirect(
        pikepdf.Dictionary({"/K": pikepdf.Array([outer])})
    )
    return pdf, outer, formula


def test_released_bibliography_entry_count_is_frozen() -> None:
    assert len(re.findall(r"(?m)^@", BIBLIOGRAPHY)) == 77


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
    pdf = tagged_table_fixture(["node00000001"], header_references=["node00000002"])
    with pytest.raises(RuntimeError, match="header reference is unresolved"):
        build_documents.canonicalize_structure_ids(pdf)


def test_pdf_semantics_promote_formula_and_flatten_only_labeled_figure_container() -> None:
    pdf, outer, formula = tagged_semantic_fixture()
    counts = build_documents.normalize_structure_semantics(pdf, expected_formula_count=1)
    assert counts == {
        "formula_count": 1,
        "retagged_figure_container_count": 1,
        "retagged_root_container_count": 0,
    }
    assert str(outer["/S"]) == "/Div"
    assert str(formula["/S"]) == "/Formula"
    assert str(formula["/Alt"]) == "Formula in TeX: x^2"
    assert str(formula["/ActualText"]) == "x^2"


def test_pdf_semantics_reject_formula_count_mismatch() -> None:
    pdf, _outer, _formula = tagged_semantic_fixture()
    with pytest.raises(RuntimeError, match="formula count does not match"):
        build_documents.normalize_structure_semantics(pdf, expected_formula_count=2)


def test_pdf_semantics_reject_ambiguous_unlabeled_figure() -> None:
    pdf = pikepdf.Pdf.new()
    figure = pdf.make_indirect(
        pikepdf.Dictionary(
            {
                "/Type": pikepdf.Name("/StructElem"),
                "/S": pikepdf.Name("/Figure"),
                "/K": 1,
            }
        )
    )
    pdf.Root["/StructTreeRoot"] = pdf.make_indirect(
        pikepdf.Dictionary({"/K": pikepdf.Array([figure])})
    )
    with pytest.raises(RuntimeError, match="not a verified outer container"):
        build_documents.normalize_structure_semantics(pdf, expected_formula_count=0)


def test_pdf_semantics_promote_root_nonstruct_container_to_part() -> None:
    pdf = pikepdf.Pdf.new()
    formula = pdf.make_indirect(
        pikepdf.Dictionary(
            {
                "/Type": pikepdf.Name("/StructElem"),
                "/S": pikepdf.Name("/Figure"),
                "/Alt": pikepdf.String("Formula in TeX: y=mx+b"),
                "/Pg": pikepdf.Dictionary(),
                "/K": 1,
            }
        )
    )
    container = pdf.make_indirect(
        pikepdf.Dictionary(
            {
                "/Type": pikepdf.Name("/StructElem"),
                "/S": pikepdf.Name("/NonStruct"),
                "/K": formula,
            }
        )
    )
    document = pdf.make_indirect(
        pikepdf.Dictionary(
            {
                "/Type": pikepdf.Name("/StructElem"),
                "/S": pikepdf.Name("/Document"),
                "/K": container,
            }
        )
    )
    container["/P"] = document
    formula["/P"] = container
    pdf.Root["/StructTreeRoot"] = pdf.make_indirect(pikepdf.Dictionary({"/K": document}))
    counts = build_documents.normalize_structure_semantics(pdf, expected_formula_count=1)
    assert counts["retagged_root_container_count"] == 1
    assert str(container["/S"]) == "/Part"
    assert str(formula["/S"]) == "/Formula"


def test_pdf_outline_titles_are_replaced_from_html_heading_text() -> None:
    pdf = pikepdf.Pdf.new()
    second = pdf.make_indirect(pikepdf.Dictionary({"/Title": pikepdf.String("andmemory")}))
    first = pdf.make_indirect(
        pikepdf.Dictionary({"/Title": pikepdf.String("HiddenState"), "/Next": second})
    )
    pdf.Root["/Outlines"] = pdf.make_indirect(
        pikepdf.Dictionary({"/First": first, "/Last": second})
    )
    build_documents.normalize_outline_titles(pdf, ["Hidden State", "and memory"])
    assert [str(item["/Title"]) for item in build_documents.outline_elements(pdf)] == [
        "Hidden State",
        "and memory",
    ]


def test_generated_html_tables_have_caption_and_explicit_header_scopes() -> None:
    source = """
<table><caption>Candidate supports</caption><thead><tr>
<th>Graph family</th><th>Edges</th></tr></thead><tbody>
<tr><td>Chain</td><td>(0,1), (1,2)</td></tr></tbody></table>
<table><caption>Ranked results</caption><thead><tr>
<th>Rank</th><th>Graph</th><th>BIC</th></tr></thead><tbody>
<tr><td>1</td><td>Chain</td><td>-4314.159</td></tr></tbody></table>
"""
    processed = build_documents.postprocess_tables(source, expected_count=2)
    assert processed.count('scope="col"') == 5
    assert '<th scope="row">Chain</th><td>(0,1), (1,2)</td>' in processed
    assert '<td>1</td><th scope="row">Chain</th><td>-4314.159</td>' in processed
    assert processed.count("<caption>") == 2


def test_generated_html_table_without_caption_is_rejected() -> None:
    source = (
        "<table><thead><tr><th>Artifact</th></tr></thead>"
        "<tbody><tr><td>report.json</td></tr></tbody></table>"
    )
    with pytest.raises(RuntimeError, match="needs one nonempty source caption"):
        build_documents.postprocess_tables(source, expected_count=1)


def test_audited_focus_and_command_contrast_thresholds_are_measured() -> None:
    assert build_documents.contrast_ratio(
        "rgb(246, 195, 68)", "rgb(255, 255, 255)"
    ) == pytest.approx(1.64, abs=0.01)
    assert build_documents.contrast_ratio("rgb(0, 90, 156)", "rgb(255, 255, 255)") >= 3
    assert build_documents.contrast_ratio(
        "rgb(125, 144, 41)", "rgb(244, 246, 248)"
    ) == pytest.approx(3.29, abs=0.01)
    assert build_documents.contrast_ratio("rgb(83, 102, 0)", "rgb(244, 246, 248)") >= 4.5


def test_html_heading_extraction_preserves_spaces_and_ignores_tex_annotation(
    tmp_path: Path,
) -> None:
    html_path = tmp_path / "edition.html"
    html_path.write_text(
        "<h1>Hidden\nState</h1><h2>Pointwise <math>x"
        '<annotation encoding="application/x-tex">x^2</annotation></math> Topology</h2>',
        encoding="utf-8",
    )
    assert inspect_pdf.html_heading_titles(html_path) == [
        "Hidden State",
        "Pointwise x Topology",
    ]


def test_compatibility_ligatures_and_broken_exact_search_are_rejected() -> None:
    inspect_pdf.validate_extracted_text(
        "structural identifiability remains bounded", filename="good.pdf"
    )
    with pytest.raises(RuntimeError, match="Compatibility ligatures"):
        inspect_pdf.validate_extracted_text(
            "structural identi\ufb01ability", filename="ligature.pdf"
        )
    with pytest.raises(RuntimeError, match="Exact-search sentinel"):
        inspect_pdf.validate_extracted_text("structural observability", filename="missing.pdf")


def test_current_arxiv_author_spellings_are_canonical() -> None:
    assert "Delaye, Lukas" in BIBLIOGRAPHY
    assert "Riegler, Ben and Calder, Robb and Fortuin, Vincent" in BIBLIOGRAPHY


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


def test_appendix_b_v107_claims_match_the_machine_register() -> None:
    matrix = json.loads(CLAIM_MATRIX_PATH.read_text(encoding="utf-8"))
    expected = [
        claim
        for claim in matrix["claims"]
        if claim["id"].startswith("V107-")
        and claim["claim_type"] not in {"repository audit", "release disposition"}
    ]
    rows = appendix_b_claim_rows()
    identifiers = [row[0] for row in rows]

    assert len(identifiers) == len(set(identifiers))
    assert set(identifiers) == {claim["id"] for claim in expected}
    displayed = {row[0]: row[1:] for row in rows}
    for claim in expected:
        assert displayed[claim["id"]] == (
            normalize_markdown_cell(claim["statement"]),
            normalize_markdown_cell(claim["evidence_class"]),
            normalize_markdown_cell(claim["disposition"]),
        )


def test_weak_cut_boundary_excludes_low_capacity_shortcut() -> None:
    section = normalize_markdown_cell(
        markdown_section(
            "## 2.3 Memory, traps, and bottlenecks",
            "## 2.4 Static non-identifiability remains the baseline warning",
        )
    )
    assert "a low-capacity cut or weak conductance cut produces a slow relaxation bound" not in section
    assert (
        "weak cut conductance relative to the aggregate capacities on both sides "
        "yields a small Rayleigh quotient and therefore a slow-relaxation upper bound"
    ) in section
    assert "Low capacity alone does not imply slow relaxation." in section
    for hypothesis in (
        "connected positive-conductance graph",
        "strictly positive node capacities",
        "nonempty proper cut",
    ):
        assert hypothesis in section


def test_claim_source_completeness_boundary_uses_coverage_record() -> None:
    coverage = json.loads(COVERAGE_PATH.read_text(encoding="utf-8"))
    summary = coverage["summary"]
    section = normalize_markdown_cell(
        markdown_section(
            "## 26.5 Stage 4 - claim and source audit record",
            "## 26.6 Stage 5 - release engineering record",
        )
    )

    assert "For every new claim the release record includes" not in section
    assert (
        f"{summary['claims_with_current_path_support']} claims with some structural path support"
        in section
    )
    assert f"{summary['claims_with_exact_locators']} with exact locators" in section
    for boundary in (
        "External entailment was not reverified.",
        "Admitted source-record hashes and retrieval dates are not recorded.",
        "Claim-local commands, runtimes, and run IDs are incomplete",
        "does not establish sentence-level completeness",
    ):
        assert boundary in section


def test_dynamic_arrest_is_bounded_proposed_only_and_counterexample_safe() -> None:
    section = markdown_section(
        "## 6.1 Static arrest versus dynamic arrest",
        "## 6.2 Topology as an ensemble rather than one graph",
    )
    normalized = normalize_markdown_cell(section)

    assert "PROPOSED_ONLY" in section
    assert "bounded or statistically stationary" in normalized
    assert "persistent nonzero microscopic turnover" in normalized
    for declared_axis in (
        "observation window",
        "ensemble",
        "sampling resolution",
        "noise treatment",
    ):
        assert declared_axis in normalized
    assert "preregistered long-window trend statistic" in normalized
    assert "it is not proof of boundedness or stationarity" in normalized
    assert "Vanishing logarithmic slope alone is insufficient" in normalized
    assert r"$\ell(t)=\log(1+t)$" in section
    assert "is unbounded even though its logarithmic slope" in normalized
    assert r"$\ell(t)=2+\sin(t)$" in section
    assert "does not converge to zero and has unbounded limsup magnitude" in normalized
    assert r"\limsup_{t\to\infty}" not in section


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


def test_type3_font_char_procedures_are_embedded_and_require_unicode_map() -> None:
    pdf = pikepdf.Pdf.new()
    font = pdf.make_indirect(
        pikepdf.Dictionary(
            {
                "/Type": pikepdf.Name("/Font"),
                "/Subtype": pikepdf.Name("/Type3"),
                "/CharProcs": pikepdf.Dictionary({"/g0": pdf.make_stream(b"0 0 d0")}),
                "/FontDescriptor": pikepdf.Dictionary(
                    {"/FontName": pikepdf.Name("/AAAAAA+DejaVuSansMono")}
                ),
                "/ToUnicode": pdf.make_stream(b"fixture"),
            }
        )
    )
    record = inspect_pdf.font_record("/F1", font)
    assert record == {
        "resource_name": "/F1",
        "base_font": "/AAAAAA+DejaVuSansMono",
        "subtype": "/Type3",
        "embedded": True,
        "to_unicode": True,
    }
    inspect_pdf.validate_pdf_font_records([record])
    record["to_unicode"] = False
    with pytest.raises(RuntimeError, match="Type3 PDF font needs ToUnicode"):
        inspect_pdf.validate_pdf_font_records([record])


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
    (tmp_path / "RUNTIME.json").write_text(json.dumps(runtime), encoding="utf-8", newline="\n")
    monkeypatch.setattr(inspect_pdf, "ROOT", tmp_path)
    monkeypatch.setattr(matplotlib, "get_data_path", lambda: str(tmp_path))
    records = [{"base_font": "/DejaVu"}, {"base_font": "/STIXGeneral"}]
    inspect_pdf.verify_bundled_font_sources(records)
    font_path.write_bytes(b"font!")
    with pytest.raises(RuntimeError, match="source-font identity drift"):
        inspect_pdf.verify_bundled_font_sources(records)
