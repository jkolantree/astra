from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = (ROOT / "manuscript" / "manuscript.md").read_text(encoding="utf-8")
SUPPLEMENT = (ROOT / "manuscript" / "supplement.md").read_text(encoding="utf-8")
BIBLIOGRAPHY = (ROOT / "manuscript" / "references.bib").read_text(encoding="utf-8")


def test_released_bibliography_entry_count_is_frozen() -> None:
    assert len(re.findall(r"(?m)^@", BIBLIOGRAPHY)) == 42


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
