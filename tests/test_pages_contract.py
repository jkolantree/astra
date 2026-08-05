from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright
from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[1]
PAGES_WORKFLOW = ROOT / ".github" / "workflows" / "pages.yml"
VERIFY_WORKFLOW = ROOT / ".github" / "workflows" / "verify.yml"

ACTION_PINS = {
    "actions/checkout": "3d3c42e5aac5ba805825da76410c181273ba90b1",  # v7.0.1
    "actions/setup-python": "5fda3b95a4ea91299a34e894583c3862153e4b97",  # v7.0.0
    "actions/configure-pages": "45bfe0192ca1faeb007ade9deae92b16b8254a0d",  # v6.0.0
    "actions/upload-pages-artifact": "fc324d3547104276b827a68afc52ff2a11cc49c9",  # v5.0.0
    "actions/deploy-pages": "cd2ce8fcbc39b97be8ca5fce6e763baed58fa128",  # v5.0.0
}


def load_yaml(path: Path) -> dict[str, Any]:
    value = YAML(typ="safe").load(path)
    assert isinstance(value, dict)
    return value


def action_uses(workflow: dict[str, Any]) -> list[str]:
    return [
        str(step["uses"])
        for job in workflow["jobs"].values()
        for step in job.get("steps", [])
        if "uses" in step
    ]


class LandingPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.lang = ""
        self.links: list[dict[str, str]] = []
        self.images: list[dict[str, str]] = []
        self.link_elements: list[dict[str, str]] = []
        self.metas: list[dict[str, str]] = []
        self.main_ids: list[str] = []
        self.ids: list[str] = []
        self.scripts: list[dict[str, str]] = []
        self.th_scopes: list[str] = []
        self.caption_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if values.get("id"):
            self.ids.append(values["id"])
        if tag == "html":
            self.lang = values.get("lang", "")
        elif tag == "a":
            self.links.append(values)
        elif tag == "img":
            self.images.append(values)
        elif tag == "link":
            self.link_elements.append(values)
        elif tag == "meta":
            self.metas.append(values)
        elif tag == "main":
            self.main_ids.append(values.get("id", ""))
        elif tag == "script":
            self.scripts.append(values)
        elif tag == "th":
            self.th_scopes.append(values.get("scope", ""))
        elif tag == "caption":
            self.caption_count += 1


def test_pages_workflow_is_manual_main_only_and_release_bound() -> None:
    workflow = load_yaml(PAGES_WORKFLOW)
    assert workflow["on"] == {"workflow_dispatch": None}
    build = workflow["jobs"]["build"]
    assert build["if"] == "github.ref == 'refs/heads/main'"
    assert build["permissions"] == {"contents": "read"}

    script = str(build["steps"][1]["run"])
    required_release_gates = (
        'current_ref="refs/tags/${current_tag}"',
        'test "$(git cat-file -t "$current_ref")" = tag',
        'current_commit="$(git rev-parse "${current_ref}^{commit}")"',
        'git merge-base --is-ancestor "$current_commit" HEAD',
        'git show "${current_ref}^{commit}:RELEASE_SPEC.json"',
        'cmp --silent -- RELEASE_SPEC.json "$downloads/TAG_RELEASE_SPEC.json"',
        'releases/tags/${current_tag}',
        ".draft == false",
        ".prerelease == false",
        ".immutable == true",
    )
    assert all(gate in script for gate in required_release_gates)
    assert 'if test "$(git rev-parse HEAD)" != "$current_commit"' in script
    assert 'git diff --name-only "${paper_ref}^{commit}" HEAD' in script
    for allowed in (
        ".github/workflows/pages.yml",
        "CHANGELOG.md",
        "MANIFEST.sha256",
        "README.md",
        "docs/index.html",
        "docs/style.css",
        "docs/resources/index.html",
        "docs/resources/earth-is-the-instrument/v0.1/index.html",
        "tests/test_pages_contract.py",
    ):
        assert allowed in script
    assert "Unreleased non-communications change cannot enter Pages" in script

    deploy = workflow["jobs"]["deploy"]
    assert deploy["needs"] == "build"
    assert deploy["environment"]["name"] == "github-pages"
    assert deploy["permissions"] == {"pages": "write", "id-token": "write"}


def test_pages_workflow_verifies_exact_release_assets_before_copying() -> None:
    workflow = load_yaml(PAGES_WORKFLOW)
    script = str(workflow["jobs"]["build"]["steps"][1]["run"])

    required_assets = (
        'preprint="SPPT_ASTRA_preprint_${tag}.html"',
        'supplement="SPPT_ASTRA_technical_supplement_${tag}.html"',
        'source_archive="SPPT_ASTRA_${tag}_source.tar.gz"',
        "--pattern SHA256SUMS",
    )
    assert all(asset in script for asset in required_assets)
    assert '$2 == name { count += 1 } END { print count + 0 }' in script
    assert 'test "$(wc -l < "$release_dir/PAGES_SHA256SUMS")" -eq 3' in script
    assert "sha256sum --check --strict PAGES_SHA256SUMS" in script
    assert "Unsafe source-archive member" in script
    assert "Unsafe source-archive traversal" in script
    assert "Source archive contains a link" in script
    assert ".version == $version and .tag == $tag" in script

    assert 'cp -- "$release_dir/$preprint" "$version_dir/preprint/index.html"' in script
    assert 'cp -- "$release_dir/$supplement" "$version_dir/supplement/index.html"' in script
    assert 'target="$site/schemas/$relative"' in script
    assert "Unsafe schema path" in script
    assert 'cmp --silent -- "$schema" "$target"' in script


def test_pages_workflow_admits_only_the_verified_working_paper_release() -> None:
    workflow = load_yaml(PAGES_WORKFLOW)
    script = str(workflow["jobs"]["build"]["steps"][1]["run"])

    required_values = (
        'paper_tag="earth-instrument-wp-0.1"',
        'paper_path="resources/earth-is-the-instrument/v0.1"',
        'paper_pdf="ASTRA_Earth_Is_the_Instrument_Working_Paper_v0.1.pdf"',
        'paper_assets=("$paper_pdf" "FONT_NOTICES.txt" "SHA256SUMS.txt" "cover.png")',
        'paper_payloads=("$paper_pdf" "FONT_NOTICES.txt" "cover.png")',
        'test "$(git cat-file -t "$paper_ref")" = tag',
        'git merge-base --is-ancestor "$paper_commit" HEAD',
        'releases/tags/${paper_tag}',
        ".prerelease == true",
        '(.assets | map(.name) | sort) == $assets',
        'select(test("^sha256:[0-9a-f]{64}$"))',
        'actual_digest="sha256:$(sha256sum "$paper_release_dir/$asset"',
        'git show "${paper_ref}^{commit}:${paper_path}/SHA256SUMS.txt"',
        '"$paper_release_dir/TAG_SHA256SUMS.txt"',
        'test "$(wc -l < "$paper_release_dir/SHA256SUMS.txt")" -eq 3',
        "sha256sum --check --strict SHA256SUMS.txt",
        'cp -- "$paper_release_dir/$asset" "$paper_target_dir/$asset"',
        'write_redirect "$site/resources/earth-is-the-instrument" "./v0.1/"',
        'write_redirect "$site/resources/earth-is-the-instrument/latest" "../v0.1/"',
    )
    assert all(value in script for value in required_values)


def test_workflow_actions_use_current_immutable_pins() -> None:
    uses = action_uses(load_yaml(VERIFY_WORKFLOW)) + action_uses(load_yaml(PAGES_WORKFLOW))
    assert uses
    assert all(re.fullmatch(r"[^@]+@[0-9a-f]{40}", value) for value in uses)
    for action, pin in ACTION_PINS.items():
        matching = [value for value in uses if value.startswith(f"{action}@")]
        assert matching
        assert set(matching) == {f"{action}@{pin}"}


def test_landing_page_links_to_current_versioned_and_schema_paths() -> None:
    parser = LandingPageParser()
    parser.feed((ROOT / "docs" / "index.html").read_text(encoding="utf-8"))
    assert parser.lang == "en-US"
    assert parser.main_ids == ["main-content"]

    links = {link.get("href", "") for link in parser.links}
    assert {
        "#main-content",
        "./latest/preprint/",
        "./latest/supplement/",
        "./editions/",
        "./resources/",
        "./resources/earth-is-the-instrument/v0.1/",
        "./schemas/",
    } <= links
    skip_links = [
        link
        for link in parser.links
        if "skip-link" in link.get("class", "").split()
    ]
    assert skip_links == [{"class": "skip-link", "href": "#main-content"}]

    script = str(load_yaml(PAGES_WORKFLOW)["jobs"]["build"]["steps"][1]["run"])
    assert 'version_dir="$site/$tag"' in script
    assert 'write_redirect "$site/latest" "../${current_tag}/"' in script
    assert 'write_redirect "$site/latest/preprint" "../../${current_tag}/preprint/"' in script
    assert (
        'write_redirect "$site/latest/supplement" '
        '"../../${current_tag}/supplement/"' in script
    )
    assert 'cp -R -- "$source_root/schemas" "$version_dir/schemas"' in script
    assert 'target="$site/schemas/$relative"' in script

    spec = json.loads((ROOT / "RELEASE_SPEC.json").read_text(encoding="utf-8"))
    schema_root = "https://jkolantree.github.io/astra/schemas/"
    schema_paths = sorted((ROOT / "schemas").glob("*.schema.json"))
    assert schema_paths
    for path in schema_paths:
        schema = json.loads(path.read_text(encoding="utf-8"))
        assert schema["$id"] == f"{schema_root}{path.name}"
        assert spec["version"] == "1.0.6"


def test_working_paper_pages_companion_is_text_first_and_well_bounded() -> None:
    path = (
        ROOT
        / "docs"
        / "resources"
        / "earth-is-the-instrument"
        / "v0.1"
        / "index.html"
    )
    html = path.read_text(encoding="utf-8")
    parser = LandingPageParser()
    parser.feed(html)

    assert parser.lang == "en-US"
    assert parser.main_ids == ["main-content"]
    assert len(parser.ids) == len(set(parser.ids))
    assert parser.scripts == []
    assert parser.caption_count == 1
    assert parser.th_scopes.count("col") == 2
    assert parser.th_scopes.count("row") == 6

    links = {link.get("href", "") for link in parser.links}
    assert {
        "#main-content",
        "./ASTRA_Earth_Is_the_Instrument_Working_Paper_v0.1.pdf",
        "./SHA256SUMS.txt",
        "./FONT_NOTICES.txt",
        "https://github.com/jkolantree/astra/releases/tag/earth-instrument-wp-0.1",
        "https://github.com/jkolantree/astra/issues/new?template=accessibility.yml",
    } <= links
    assert any(
        image.get("src") == "./cover.png"
        and "cutaway Earth" in image.get("alt", "")
        and image.get("width") == "480"
        and image.get("height") == "622"
        for image in parser.images
    )
    assert any(
        link.get("rel") == "canonical"
        and link.get("href")
        == "https://jkolantree.github.io/astra/resources/earth-is-the-instrument/v0.1/"
        for link in parser.link_elements
    )
    meta_keys = {
        meta.get("name") or meta.get("property")
        for meta in parser.metas
    }
    assert {
        "description",
        "citation_title",
        "citation_author",
        "citation_publication_date",
        "citation_pdf_url",
        "og:title",
        "og:description",
        "og:url",
        "og:image",
    } <= meta_keys

    semantic = " ".join(re.sub(r"<[^>]+>", " ", html).split())
    required_boundaries = (
        "supplemental exploratory working paper",
        "not peer reviewed",
        "does not amend or supersede SPPT/ASTRA v1.0.6",
        "provide empirical validation",
        "not a tagged PDF",
        "no reuse license is asserted for the PDF or cover image",
        "available by August 2026",
        "does not establish a particular artifact's historicity",
        "pixel-for-pixel with no differences",
        "all three payload hashes verify",
        "author's classifications",
        "not a claim that Earth was engineered",
    )
    assert all(value in semantic for value in required_boundaries)
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
        assert label in semantic
    assert not re.search(r"<iframe|google-analytics|googletagmanager|plausible[.]io", html)


def test_pages_home_scopes_rights_and_separates_publication_tracks() -> None:
    html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    semantic = " ".join(re.sub(r"<[^>]+>", " ", html).split())
    assert "Reference framework — v1.0.6" in semantic
    assert "Supplemental working papers" in semantic
    assert "separate from SPPT/ASTRA v1.0.6" in semantic
    assert "neither amends that release nor provides empirical validation" in semantic
    assert "Separately supplied resources retain the rights stated" in semantic
    assert "Original manuscript, documentation, figures, and data" not in semantic

    css = (ROOT / "docs" / "style.css").read_text(encoding="utf-8")
    assert re.search(r"[.]cover-link,\s*[.]cover-link img,\s*[.]paper-cover", css)


def test_pages_home_and_working_paper_reflow_at_narrow_widths() -> None:
    paths = (
        ROOT / "docs" / "index.html",
        ROOT
        / "docs"
        / "resources"
        / "earth-is-the-instrument"
        / "v0.1"
        / "index.html",
    )
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=["--disable-gpu"])
        page = browser.new_page()
        for path in paths:
            for width in (320, 400):
                page.set_viewport_size({"width": width, "height": 900})
                page.goto(path.as_uri(), wait_until="load")
                dimensions = page.evaluate(
                    """() => ({
                      viewport: window.innerWidth,
                      rootClient: document.documentElement.clientWidth,
                      rootScroll: document.documentElement.scrollWidth,
                      bodyScroll: document.body.scrollWidth
                    })"""
                )
                assert dimensions == {
                    "viewport": width,
                    "rootClient": width,
                    "rootScroll": width,
                    "bodyScroll": width,
                }
        browser.close()


def test_skip_link_uses_high_contrast_focus_on_dark_header() -> None:
    css = (ROOT / "docs" / "style.css").read_text(encoding="utf-8")
    assert re.search(
        r"\.skip-link:focus-visible\s*\{[^}]*outline-color:[ \t]*#ffffff",
        css,
        flags=re.DOTALL,
    )

    def channel(value: int) -> float:
        normalized = value / 255
        return normalized / 12.92 if normalized <= 0.04045 else (
            (normalized + 0.055) / 1.055
        ) ** 2.4

    def luminance(rgb: tuple[int, int, int]) -> float:
        red, green, blue = (channel(value) for value in rgb)
        return 0.2126 * red + 0.7152 * green + 0.0722 * blue

    dark = luminance((23, 63, 95))
    white = luminance((255, 255, 255))
    assert (white + 0.05) / (dark + 0.05) >= 3


def test_issue_forms_parse_and_require_public_report_privacy_checks() -> None:
    forms_root = ROOT / ".github" / "ISSUE_TEMPLATE"
    expected = {
        "accessibility.yml",
        "reproducibility.yml",
        "scientific-correction.yml",
    }
    assert {path.name for path in forms_root.glob("*.yml")} == expected | {"config.yml"}

    config = load_yaml(forms_root / "config.yml")
    assert config["blank_issues_enabled"] is True
    assert config["contact_links"][0]["url"].endswith("/astra/latest/")

    for name in expected:
        form = load_yaml(forms_root / name)
        assert all(form.get(key) for key in ("name", "description", "title", "body"))
        field_ids = [field.get("id") for field in form["body"] if field.get("id")]
        assert len(field_ids) == len(set(field_ids))

        privacy_options = [
            option
            for field in form["body"]
            if field.get("type") == "checkboxes"
            for option in field.get("attributes", {}).get("options", [])
            if "removed secrets" in option.get("label", "").lower()
            and "private" in option.get("label", "").lower()
        ]
        assert privacy_options
        assert all(option.get("required") is True for option in privacy_options)
