"""The gateway keeps one model source and resolves assets at both route depths."""

from __future__ import annotations

import hashlib
import json
import re
import struct
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

from tools import assemble_research_companion_pages as companion
from tools import build_explorer_gateway as gateway
from tools.link_audit_common import parse_html

ROOT = Path(__file__).resolve().parents[1]


def test_root_gateway_is_generated_from_one_explorer_source() -> None:
    source = gateway.SOURCE.read_text()
    home = gateway.OUTPUT.read_text()
    assert home == gateway.render(source)
    for name in ("fixture", "model-code", "render-code"):
        pattern = rf'<script id="{name}"[^>]*>(.*?)</script>'
        original = re.search(pattern, source, re.S)
        generated = re.search(pattern, home, re.S)
        assert original is not None and generated is not None
        assert original[1] == generated[1]
    assert not parse_html(gateway.OUTPUT).refreshes
    assert not parse_html(gateway.SOURCE).refreshes
    assert 'url=../"' in companion.ALIAS.decode()
    assert 'href="../"' in companion.ALIAS.decode()


def test_rebase_preserves_fragments_queries_and_external_destinations() -> None:
    assert gateway.root_reference("#pinned") == "#pinned"
    assert gateway.root_reference("../../../../library/#cite") == "library/#cite"
    assert gateway.root_reference("recurrence.md") == gateway.SOURCE_ROUTE + "recurrence.md"
    assert gateway.root_reference("../package/a.png?download=1#note") == (
        "resources/sppt-scm-research-companion/draft-v0.1.0/package/a.png?download=1#note"
    )
    for url in ("https://example.invalid/a", "//example.invalid/a", "/astra/library/", "data:image/png;base64,a"):
        assert gateway.root_reference(url) == url


def test_root_and_namespaced_pages_have_the_same_link_targets() -> None:
    original = parse_html(gateway.SOURCE)
    generated = parse_html(gateway.OUTPUT)
    assert generated.ids == original.ids
    assert generated.references == [
        (attribute, gateway.root_reference(destination))
        for attribute, destination in original.references
    ]
    assert ("href", "library/") in generated.references
    assert {"laboratory", "pinned", "geometry", "atlas", "motion", "library"} <= set(generated.ids)


def test_research_library_preserves_publication_destinations_and_returns_home() -> None:
    page = parse_html(ROOT / "docs/library/index.html")
    links = {destination for attribute, destination in page.references if attribute == "href"}
    assert {
        "../", "../v1.0.7/preprint/", "../v1.0.7/supplement/",
        "../resources/dark-medium-response-atlas/v0.1.0/",
        "../resources/earth-is-the-instrument/v0.3.0/",
        "../resources/earth-is-the-instrument/v0.3.0/ground-reading/",
    } <= links
    assert ("href", "../style.css") in page.references
    assert ("src", "../sppt-astra-cover.svg") in page.references
    assert not page.refreshes


def test_readme_is_a_short_gateway_with_defined_name_and_reviewed_scientific_limits() -> None:
    text = (ROOT / "README.md").read_text()
    visible = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    assert len(visible.split()) < 330
    assert "Astronomical State-Topology and Reservoir Analysis" in text
    assert "https://jkolantree.github.io/astra/" in text
    assert "not peer reviewed" in text
    assert "does not establish empirical validation" in text
    assert "PUBLICATIONS.md#research-overview" in text
    assert "## Current" not in text and "## Working paper" not in text


def test_selected_hero_keeps_original_bytes_credentials_and_uncropped_dimensions() -> None:
    image = ROOT / "docs/assets/astra-midnight-occultation.png"
    payload = image.read_bytes()
    expected = "a589e2502ae973b1e46593bbf02a953c043fc3d5005a732186878ead11286f45"
    assert len(payload) == 1500399
    assert hashlib.sha256(payload).hexdigest() == expected
    assert payload[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">II", payload[16:24]) == (1774, 887)
    offset, chunks = 8, []
    while offset < len(payload):
        length = struct.unpack(">I", payload[offset:offset + 4])[0]
        chunks.append(payload[offset + 4:offset + 8])
        offset += length + 12
    assert offset == len(payload) and b"caBX" in chunks
    record = json.loads((ROOT / "docs/assets/midnight-occultation-provenance.json").read_text())
    assert record["sha256"] == expected
    assert record["dimensions"] == [1774, 887]
    assert record["preservation"]["embedded_c2pa_retained"] is True
    for page in (gateway.SOURCE, gateway.OUTPUT):
        text = page.read_text()
        assert 'width="1774" height="887"' in text
        assert "aspect-ratio:2/1;object-fit:contain" in text
        assert "pending-transfer" not in text and "hero-placeholder" not in text
    readme = (ROOT / "README.md").read_text()
    assert "](docs/assets/astra-midnight-occultation.png)](https://jkolantree.github.io/astra/)" in readme
    assert "not a spacecraft image or scientific evidence" in readme


class ReadingStructure(HTMLParser):
    """Collect structural evidence without claiming browser accessibility review."""

    def __init__(self) -> None:
        super().__init__()
        self.elements: list[tuple[str, dict[str, str | None]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.elements.append((tag, dict(attrs)))


def test_reading_routes_are_available_without_script_or_disclosure_controls() -> None:
    reading = ROOT / "docs/understand"
    for path in sorted(reading.rglob("*.html")):
        text = path.read_text()
        parser = ReadingStructure()
        parser.feed(text)
        tags = Counter(tag for tag, _ in parser.elements)
        ids = [attrs["id"] for _, attrs in parser.elements if "id" in attrs]
        assert tags["h1"] == tags["main"] == 1
        assert len(ids) == len(set(ids))
        assert not {"script", "details", "dialog", "iframe"} & tags.keys()
        assert ("a", {"class": "skip", "href": "#main"}) in parser.elements
        assert ("html", {"lang": "en-US"}) in parser.elements
        for tag, attrs in parser.elements:
            assert "hidden" not in attrs and attrs.get("aria-hidden") != "true"
            for attribute in ("aria-labelledby", "aria-describedby"):
                if attrs.get(attribute):
                    assert set(str(attrs[attribute]).split()) <= set(ids)
            if tag == "nav":
                assert attrs.get("aria-label") or attrs.get("aria-labelledby")
        assert not re.search(r"\[Insert|Integration guidance|TODO|TBD|placeholder", text, re.I)
    landing = ReadingStructure()
    landing.feed((reading / "index.html").read_text())
    assert sum(tag == "article" and attrs.get("class") == "card"
               for tag, attrs in landing.elements) == 8


def test_reading_is_reachable_from_both_explorer_routes_and_returns_to_models() -> None:
    home = parse_html(gateway.OUTPUT)
    source = parse_html(gateway.SOURCE)
    assert ("href", "understand/") in home.references
    assert ("href", "../../../../understand/") in source.references
    assert ("href", "../understand/") in parse_html(ROOT / "docs/library/index.html").references
    framework = parse_html(ROOT / "docs/understand/geometry/index.html")
    planets = parse_html(ROOT / "docs/understand/worlds/index.html")
    assert {("href", "../../#pinned"), ("href", "../../#geometry"),
            ("href", "../worlds/#rings"), ("href", "../worlds/#moon")} <= set(framework.references)
    assert ("href", "../../#laboratory") in planets.references
    assert "decagon-source-note" in planets.ids
    predictions = parse_html(ROOT / "docs/understand/predictions/index.html")
    assert {"wave", "gradient", "ensemble", "boundary", "chemistry", "rings",
            "grains", "titan", "moon", "methane"} <= predictions.ids
    landing = parse_html(ROOT / "docs/understand/index.html")
    assert ("href", "#predictions") in landing.references
    assert ("href", "../#predictions") in predictions.references
    assert ("href", "../predictions/#wave") in framework.references
    assert ("href", "../predictions/#rings") in planets.references
    persistence = parse_html(ROOT / "docs/understand/persistence/index.html")
    assert {"lunar-retention", "different-meanings", "perceptual-history",
            "probe-and-reanalysis", "neural-hypothesis", "next-tests"} <= persistence.ids
    assert ("href", "persistence/") in landing.references
    assert ("href", "../persistence/") in framework.references
    assert ("href", "../persistence/") in planets.references
    assert ("href", "../#persistence") in persistence.references
    # The corrected reanalysis must travel with the original probe study.
    for source in (
        "https://www.nature.com/articles/nn.4546",
        "https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.3001436",
        "https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.3001603",
        "https://www.nature.com/articles/s41550-026-02822-9",
    ):
        assert ("href", source) in persistence.references
    connections = parse_html(ROOT / "docs/understand/connections/index.html")
    assert {"levels", "holography", "retained-mode", "recovery", "geometry",
            "worked-example", "toy-dynamics", "toy-information", "toy-populations",
            "toy-code", "toy-counterexamples", "scm", "experience", "recent-work",
            "cmb", "next-step"} <= connections.ids
    assert ("href", "connections/") in landing.references
    assert ("href", "../connections/") in framework.references
    assert ("href", "../connections/") in persistence.references
    assert ("href", "../#connections") in connections.references
