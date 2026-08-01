from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = (ROOT / "manuscript" / "manuscript.md").read_text(encoding="utf-8")
SUPPLEMENT = (ROOT / "manuscript" / "supplement.md").read_text(encoding="utf-8")
BIBLIOGRAPHY = (ROOT / "manuscript" / "references.bib").read_text(encoding="utf-8")


def test_private_and_machine_local_metadata_are_absent() -> None:
    public_text = "\n".join((MANUSCRIPT, SUPPLEMENT, BIBLIOGRAPHY))
    for forbidden in (
        "Kansas, USA",
        "author contact to be supplied",
        "/usr/share/",
        "Pirate Dude",
        "C:\\Users\\",
    ):
        assert forbidden not in public_text
    assert "https://github.com/jkolantree/astra/issues" in MANUSCRIPT


def test_unsupported_blinding_claim_is_absent() -> None:
    assert "A blinded three-reservoir" not in MANUSCRIPT
    assert "a blinded three-reservoir" not in SUPPLEMENT
    assert "neither blind nor external validation" in MANUSCRIPT
    assert "not blinded or external validation" in SUPPLEMENT
    assert MANUSCRIPT.count("blinded") == 0
    assert SUPPLEMENT.count("blinded") == 3  # one explicit nonclaim and two future milestones


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
    assert "Nature Communications 15, 5169" not in BIBLIOGRAPHY
