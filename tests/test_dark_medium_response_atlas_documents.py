from __future__ import annotations

from tools.build_dark_medium_response_atlas_documents import (
    CSS,
    HTML,
    PDF,
    SOURCE,
    canonical_url,
    load_spec,
    publication_footer,
)


def test_atlas_document_builder_has_a_fixed_versioned_identity() -> None:
    spec = load_spec()
    assert canonical_url(spec) == (
        "https://jkolantree.github.io/astra/resources/"
        "dark-medium-response-atlas/v0.1.0/"
    )
    assert spec["tag"] == "dark-medium-response-atlas-v0.1.0"
    assert spec["pages"]["citation_route"] == spec["pages"]["versioned_route"]
    assert HTML.is_file()
    assert PDF.is_file()
    assert SOURCE.is_file()
    assert CSS.is_file()


def test_atlas_publication_footer_uses_versioned_local_records() -> None:
    footer = publication_footer(load_spec())
    expected = {
        "./dark-medium-response-atlas-v0.1.0.html",
        "./dark-medium-response-atlas-v0.1.0.pdf",
        "./dark-medium-response-atlas-v0.1.0-source.tar.gz",
        "./claim-ledger.csv",
        "./source-ledger.csv",
        "./novelty-ledger.csv",
        "./SHA256SUMS",
        "./CITATION.cff",
        "./LICENSE_MAP.md",
    }
    for destination in expected:
        assert f'href="{destination}"' in footer
    assert "dark-medium-response-atlas-v0.1.0" in footer
    assert "Scientific judgment" in footer


def test_atlas_source_does_not_use_deprecated_math_markup() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    readme = SOURCE.with_name("README.md").read_text(encoding="utf-8")
    assert "{\\rm " not in source
    assert "\\centernot" not in source
    assert "not peer reviewed" in readme
    assert "did not claim a dark-matter detection" in source
