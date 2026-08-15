from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright
from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[1]
PAGES_WORKFLOW = ROOT / ".github" / "workflows" / "pages.yml"
VERIFY_WORKFLOW = ROOT / ".github" / "workflows" / "verify.yml"
COVER_SVG = ROOT / "docs" / "sppt-astra-cover.svg"
COVER_ALT = (
    "Conceptual SPPT/ASTRA network with observed boundary and surface data, a latent "
    "state, candidate graph paths, and an observe-infer-test sequence"
)

COMMUNICATIONS_BASE_COMMIT = "5743f09daf924ea695d25053934b4f576aac594b"
COMMUNICATIONS_BASE_TREE = "1ac773d75142558ed6503b9504c298fb30327b7c"
PAGES_COVER_MILESTONE_PATHS = (
    ".github/workflows/pages.yml",
    "MANIFEST.sha256",
    "README.md",
    "docs/index.html",
    "docs/sppt-astra-cover.svg",
    "evidence/claim_source_coverage_v1.0.7_maintenance_overlay_m1.json",
    "tests/test_pages_contract.py",
)

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
        self.math_count = 0
        self.form_count = 0
        self.control_count = 0

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
        elif tag == "math":
            self.math_count += 1
        elif tag == "form":
            self.form_count += 1
        elif tag in {"input", "select", "textarea"}:
            self.control_count += 1


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
        "releases/tags/${current_tag}",
        ".draft == false",
        ".prerelease == false",
        ".immutable == true",
    )
    assert all(gate in script for gate in required_release_gates)
    assert 'latest_release="$(gh api "repos/${GITHUB_REPOSITORY}/releases/latest")"' in script
    assert "$(jq -er '.id' <<<\"$latest_release\")" in script
    assert f'communications_base_commit="{COMMUNICATIONS_BASE_COMMIT}"' in script
    assert f'communications_base_tree="{COMMUNICATIONS_BASE_TREE}"' in script
    assert 'test "$(git cat-file -t "$communications_base_commit")" = commit' in script
    assert (
        'test "$(git rev-parse "${communications_base_commit}^{tree}")" = '
        '"$communications_base_tree"' in script
    )
    assert 'git merge-base --is-ancestor "$communications_base_commit" HEAD' in script
    assert 'if test "$(git rev-parse HEAD)" != "$communications_base_commit"' in script
    assert 'git diff --name-only "$communications_base_commit" HEAD' in script
    allowlist = re.search(r'case "\$changed_path" in\s*\n\s*([^\n]+)\) ;;', script)
    assert allowlist is not None
    assert tuple(allowlist.group(1).split("|")) == PAGES_COVER_MILESTONE_PATHS
    assert 'git diff --name-only "${current_ref}^{commit}" HEAD' not in script
    assert "docs/resources/earth-is-the-instrument/v0.3.0/*" not in script
    assert "resources/earth-is-the-instrument/v0.3.0/*" not in script
    assert "Unexpected post-M1 change cannot enter Pages" in script

    deploy = workflow["jobs"]["deploy"]
    assert deploy["needs"] == "build"
    assert deploy["environment"]["name"] == "github-pages"
    assert deploy["permissions"] == {"pages": "write", "id-token": "write"}


def test_bauhaus_cover_is_accessible_self_contained_and_semantically_spare() -> None:
    raw = COVER_SVG.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    source = raw.decode("utf-8")
    root = ET.fromstring(source)
    assert root.tag == "{http://www.w3.org/2000/svg}svg"
    assert root.attrib["viewBox"] == "0 0 1600 900"
    assert root.attrib["role"] == "img"
    assert root.attrib["aria-labelledby"] == "cover-title cover-desc"
    assert root.attrib["preserveAspectRatio"] == "xMidYMid meet"

    elements_by_id: dict[str, ET.Element] = {}
    for element in root.iter():
        element_id = element.attrib.get("id")
        if element_id is not None:
            assert element_id not in elements_by_id
            elements_by_id[element_id] = element
    assert elements_by_id["cover-title"].text == (
        "SPPT and ASTRA: a planet as a constrained network"
    )
    description = elements_by_id["cover-desc"].text or ""
    assert "Blue marks observed boundary signals and measured surface responses" in description
    assert "red marks the latent state" in description
    assert "ochre marks candidate graph links and nodes" in description
    assert "observe, infer, and test" in description
    assert "not a scale model, measurement, or claim of planetary validation" in description
    for consumer in (ROOT / "README.md", ROOT / "docs" / "index.html"):
        consumer_text = consumer.read_text(encoding="utf-8")
        assert f'alt="{COVER_ALT}"' in consumer_text
        assert (
            "observe boundary signals and measured responses, infer a conditional "
            "latent state, then test candidate graphs against declared gates"
            in consumer_text
        )
        assert "sppt-astra-cover.svg" in consumer_text
    circle_tag = "{http://www.w3.org/2000/svg}circle"
    rect_tag = "{http://www.w3.org/2000/svg}rect"
    assert elements_by_id["observed-key"].tag == circle_tag
    assert elements_by_id["boundary-node-top"].tag == circle_tag
    for attribute in ("fill", "stroke"):
        assert (
            elements_by_id["observed-key"].attrib[attribute]
            == elements_by_id["boundary-node-top"].attrib[attribute]
        )
    for hero_path in ("observed-boundary-arc", "observed-response-path"):
        for attribute in ("stroke", "stroke-width", "stroke-linecap"):
            assert (
                elements_by_id["observed-key-line"].attrib[attribute]
                == elements_by_id[hero_path].attrib[attribute]
            )
    for surface_node in ("surface-node-left", "surface-node-right"):
        assert (
            elements_by_id[surface_node].attrib["fill"]
            == elements_by_id["observed-key"].attrib["fill"]
        )
    assert elements_by_id["latent-key"].tag == circle_tag
    assert elements_by_id["deep-state"].tag == circle_tag
    for attribute in ("fill", "stroke"):
        assert (
            elements_by_id["latent-key"].attrib[attribute]
            == elements_by_id["deep-state"].attrib[attribute]
        )
    assert elements_by_id["candidate-key-node"].tag == rect_tag
    assert elements_by_id["candidate-node-square"].tag == rect_tag
    for candidate_path in ("candidate-path-primary", "candidate-path-secondary"):
        for attribute in ("stroke", "stroke-width", "stroke-linecap"):
            assert (
                elements_by_id["candidate-key"].attrib[attribute]
                == elements_by_id[candidate_path].attrib[attribute]
            )
    for candidate_node in ("candidate-key-node", "candidate-node-round", "candidate-node-square"):
        assert (
            elements_by_id[candidate_node].attrib["fill"]
            == elements_by_id["candidate-key"].attrib["stroke"]
        )

    semantic_accents = {
        "#3d7fc4": {
            ("observed-key-line", "stroke"),
            ("observed-key", "fill"),
            ("observed-boundary-arc", "stroke"),
            ("observed-node-left", "fill"),
            ("boundary-node-top", "fill"),
            ("observed-node-right", "fill"),
            ("observed-response-path", "stroke"),
            ("surface-node-left", "fill"),
            ("surface-node-right", "fill"),
            ("observe-index", "fill"),
        },
        "#d94b3d": {
            ("latent-key", "fill"),
            ("deep-state", "fill"),
            ("infer-index", "fill"),
        },
        "#b17800": {
            ("candidate-key", "stroke"),
            ("candidate-key-node", "fill"),
            ("candidate-path-primary", "stroke"),
            ("candidate-path-secondary", "stroke"),
            ("candidate-node-round", "fill"),
            ("candidate-node-square", "fill"),
            ("test-index", "fill"),
        },
    }
    approved_palette = {
        "#111111",
        "#3d7fc4",
        "#b17800",
        "#d8d0bd",
        "#d94b3d",
        "#f1e9d2",
        "#fff9e9",
    }
    assert set(re.findall(r"#[0-9a-fA-F]{6}\b", source)) == approved_palette
    assert "rgb(" not in source.casefold()
    assert "hsl(" not in source.casefold()
    assert all("style" not in element.attrib for element in root.iter())
    paint_values = {
        value
        for element in root.iter()
        for attribute in ("fill", "stroke")
        if (value := element.attrib.get(attribute)) is not None
    }
    assert paint_values <= approved_palette | {"none"}
    style_elements = list(root.iter("{http://www.w3.org/2000/svg}style"))
    assert len(style_elements) == 1
    style_text = "".join(style_elements[0].itertext())
    assert "@" not in style_text
    assert "\\" not in style_text
    assert "/*" not in style_text
    assert "*/" not in style_text
    declaration_names = re.findall(r"([a-zA-Z][a-zA-Z-]*)[ \t]*:", style_text)
    assert len(declaration_names) == style_text.count(":")
    assert {name.casefold() for name in declaration_names} == {
        "font-family",
        "font-size",
        "font-weight",
        "letter-spacing",
    }
    observed_accent_uses = {color: set() for color in semantic_accents}
    for element in root.iter():
        for attribute in ("fill", "stroke"):
            value = element.attrib.get(attribute)
            if value in observed_accent_uses:
                element_id = element.attrib.get("id")
                assert element_id is not None
                observed_accent_uses[value].add((element_id, attribute))
    assert observed_accent_uses == semantic_accents
    assert elements_by_id["observe-index"].attrib["fill"] == "#3d7fc4"
    assert elements_by_id["infer-index"].attrib["fill"] == "#d94b3d"
    assert elements_by_id["test-index"].attrib["fill"] == "#b17800"
    assert "#2c69ae" not in source
    assert "#4b88c9" not in source
    assert "#a77a00" not in source
    assert "stroke-dasharray" not in source

    semantic_text = " ".join("".join(root.itertext()).split())
    for phrase in (
        "A PLANET AS A CONSTRAINED NETWORK",
        "BOUNDARY SIGNALS",
        "SURFACE measured response",
        "DEEP STATE",
        "PATHS testable links",
        "01 / OBSERVE Measure surface signals.",
        "02 / INFER Infer latent structure.",
        "03 / TEST Test candidate graphs.",
        "GATES / CONSERVATION",
        "HELD-OUT PREDICTION",
    ):
        assert phrase in semantic_text

    svg_namespace = "{http://www.w3.org/2000/svg}"
    text_elements = list(root.iter(f"{svg_namespace}text"))
    assert len(text_elements) <= 26
    assert all("".join(element.itertext()).strip() for element in text_elements)
    font_sizes = [int(value) for value in re.findall(r"font-size:[ \t]*(\d+)px", source)]
    assert font_sizes
    assert min(font_sizes) >= 24

    allowed_tags = {
        "circle",
        "desc",
        "g",
        "line",
        "path",
        "rect",
        "style",
        "svg",
        "text",
        "title",
    }
    assert {element.tag.removeprefix(svg_namespace) for element in root.iter()} == allowed_tags
    allowed_attributes = {
        "aria-labelledby",
        "class",
        "cx",
        "cy",
        "d",
        "fill",
        "height",
        "id",
        "preserveAspectRatio",
        "r",
        "role",
        "stroke",
        "stroke-linecap",
        "stroke-opacity",
        "stroke-width",
        "text-anchor",
        "transform",
        "viewBox",
        "width",
        "x",
        "x1",
        "x2",
        "y",
        "y1",
        "y2",
    }
    attribute_names = {
        attribute.rsplit("}", 1)[-1]
        for element in root.iter()
        for attribute in element.attrib
    }
    assert attribute_names == allowed_attributes
    assert all(
        attribute.rsplit("}", 1)[-1].casefold() != "href"
        for element in root.iter()
        for attribute in element.attrib
    )
    assert re.search(r"\burl[ \t\r\n]*\(", source, flags=re.IGNORECASE) is None
    assert "<?" not in source
    assert "<!doctype" not in source.casefold()

    opacity_elements = [
        (element.tag.removeprefix(svg_namespace), element.attrib)
        for element in root.iter()
        if "stroke-opacity" in element.attrib
    ]
    assert opacity_elements == [
        (
            "line",
            {
                "x1": "535",
                "y1": "28",
                "x2": "535",
                "y2": "160",
                "stroke": "#f1e9d2",
                "stroke-opacity": "0.35",
                "stroke-width": "2",
            },
        ),
        (
            "line",
            {
                "x1": "1045",
                "y1": "28",
                "x2": "1045",
                "y2": "160",
                "stroke": "#f1e9d2",
                "stroke-opacity": "0.35",
                "stroke-width": "2",
            },
        ),
        (
            "line",
            {
                "x1": "88",
                "y1": "176",
                "x2": "1512",
                "y2": "176",
                "stroke": "#f1e9d2",
                "stroke-opacity": "0.45",
                "stroke-width": "2",
            },
        ),
    ]

    def channel(component: int) -> float:
        normalized = component / 255
        return normalized / 12.92 if normalized <= 0.04045 else ((normalized + 0.055) / 1.055) ** 2.4

    def luminance(color: str) -> float:
        values = tuple(int(color[index : index + 2], 16) for index in (1, 3, 5))
        red, green, blue = (channel(value) for value in values)
        return 0.2126 * red + 0.7152 * green + 0.0722 * blue

    def contrast(first: str, second: str) -> float:
        light, dark = sorted((luminance(first), luminance(second)), reverse=True)
        return (light + 0.05) / (dark + 0.05)

    assert contrast("#111111", "#f1e9d2") >= 4.5
    assert contrast("#fff9e9", "#111111") >= 4.5
    assert contrast("#d8d0bd", "#111111") >= 4.5
    for semantic_accent in semantic_accents:
        assert contrast(semantic_accent, "#111111") >= 4.5
        assert contrast(semantic_accent, "#f1e9d2") >= 3
    assert contrast("#111111", "#d94b3d") >= 4.5


def test_bauhaus_cover_has_measured_label_clearance_at_repository_scale() -> None:
    source = COVER_SVG.read_text(encoding="utf-8")
    clearance_ids = (
        "boundary-label",
        "boundary-node-top",
        "surface-label",
        "surface-note",
        "surface-node-left",
        "network-boundary",
        "observed-key",
        "observed-key-label",
        "latent-key",
        "latent-key-label",
        "candidate-key-node",
        "candidate-key-label",
        "deep-label",
        "deep-note",
        "paths-label",
        "paths-note",
        "process-band",
        "observe-index",
        "observe-title",
        "observe-copy",
        "infer-index",
        "infer-title",
        "infer-copy",
        "test-index",
        "test-title",
        "test-copy",
        "gates-label",
    )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=["--disable-gpu"])
        page = browser.new_page(viewport={"width": 1600, "height": 900})
        page.set_content(
            "<style>html,body{margin:0;width:1600px;height:900px;overflow:hidden}"
            "svg{display:block;width:1600px;height:900px}</style>" + source,
            wait_until="load",
        )
        boxes = page.evaluate(
            """ids => Object.fromEntries(ids.map(id => {
                const element = document.getElementById(id);
                if (element === null) throw new Error(`missing element: ${id}`);
                const box = element.getBoundingClientRect();
                return [id, {left: box.left, top: box.top, right: box.right,
                             bottom: box.bottom, width: box.width, height: box.height}];
            }))""",
            clearance_ids,
        )

        assert boxes["boundary-node-top"]["top"] - boxes["boundary-label"]["bottom"] >= 28
        assert (
            boxes["surface-node-left"]["left"]
            - max(boxes["surface-label"]["right"], boxes["surface-note"]["right"])
            >= 32
        )
        assert boxes["paths-label"]["left"] - boxes["network-boundary"]["right"] >= 48
        assert boxes["process-band"]["top"] - boxes["network-boundary"]["bottom"] >= 48
        for mark_id, label_id in (
            ("observed-key", "observed-key-label"),
            ("latent-key", "latent-key-label"),
            ("candidate-key-node", "candidate-key-label"),
        ):
            assert boxes[label_id]["left"] - boxes[mark_id]["right"] >= 10
        assert boxes["latent-key"]["left"] - boxes["observed-key-label"]["right"] >= 32
        assert (
            boxes["candidate-key-node"]["left"] - boxes["latent-key-label"]["right"]
            >= 32
        )
        assert boxes["network-boundary"]["left"] - boxes["candidate-key-label"]["right"] >= 48

        for title_id, copy_id in (
            ("surface-label", "surface-note"),
            ("deep-label", "deep-note"),
            ("paths-label", "paths-note"),
            ("observe-index", "observe-title"),
            ("observe-title", "observe-copy"),
            ("infer-index", "infer-title"),
            ("infer-title", "infer-copy"),
            ("test-index", "test-title"),
            ("test-title", "test-copy"),
        ):
            assert boxes[copy_id]["top"] - boxes[title_id]["bottom"] >= 10

        assert boxes["observe-title"]["right"] <= 535 - 32
        assert boxes["infer-title"]["right"] <= 1045 - 32
        assert boxes["test-copy"]["right"] <= 1512

        text_boxes = page.locator("svg text").evaluate_all(
            """nodes => nodes.map(node => {
                const box = node.getBoundingClientRect();
                return {left: box.left, top: box.top, right: box.right,
                        bottom: box.bottom};
            })"""
        )
        assert min(box["left"] for box in text_boxes) >= 64
        assert min(box["top"] for box in text_boxes) >= 64
        assert max(box["right"] for box in text_boxes) <= 1600 - 64
        assert max(box["bottom"] for box in text_boxes) <= 900 - 64

        page.set_viewport_size({"width": 960, "height": 540})
        page.set_content(
            "<style>html,body{margin:0;width:960px;height:540px;overflow:hidden}"
            "svg{display:block;width:960px;height:540px}</style>" + source,
            wait_until="load",
        )
        repository_font_sizes = page.locator("svg text").evaluate_all(
            """nodes => nodes.map(node => {
                const matrix = node.getScreenCTM();
                if (matrix === null) throw new Error("missing screen transform");
                const scaleY = Math.hypot(matrix.b, matrix.d);
                return parseFloat(getComputedStyle(node).fontSize) * scaleY;
            })"""
        )
        assert min(repository_font_sizes) >= 14.4 - 0.01
        assert page.evaluate("document.documentElement.scrollWidth") == 960
        assert page.evaluate("document.documentElement.scrollHeight") == 540
        browser.close()


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
    assert "$2 == name { count += 1 } END { print count + 0 }" in script
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


def test_pages_workflow_admits_only_the_verified_supplemental_releases() -> None:
    workflow = load_yaml(PAGES_WORKFLOW)
    script = str(workflow["jobs"]["build"]["steps"][1]["run"])

    required_values = (
        'paper_version="v0.1"',
        'paper_tag="earth-instrument-wp-0.1"',
        'paper_path="resources/earth-is-the-instrument/${paper_version}"',
        'paper_pdf="ASTRA_Earth_Is_the_Instrument_Working_Paper_v0.1.pdf"',
        'paper_assets=("$paper_pdf" "FONT_NOTICES.txt" "SHA256SUMS.txt" "cover.png")',
        'paper_payloads=("$paper_pdf" "FONT_NOTICES.txt" "cover.png")',
        'test "$(git cat-file -t "$paper_ref")" = tag',
        'git merge-base --is-ancestor "$paper_commit" HEAD',
        "releases/tags/${paper_tag}",
        ".prerelease == true",
        "(.assets | map(.name) | sort) == $assets",
        'select(test("^sha256:[0-9a-f]{64}$"))',
        'actual_digest="sha256:$(sha256sum "$paper_release_dir/$asset"',
        'git show "${paper_ref}^{commit}:${paper_path}/SHA256SUMS.txt"',
        '"$paper_release_dir/TAG_SHA256SUMS.txt"',
        'test "$(wc -l < "$paper_release_dir/SHA256SUMS.txt")" -eq 3',
        "sha256sum --check --strict SHA256SUMS.txt",
        'cp -- "$paper_release_dir/$asset" "$paper_target_dir/$asset"',
        'framework_version="v0.3.0"',
        'framework_tag="earth-instrument-framework-v0.3.0"',
        'framework_path="resources/earth-is-the-instrument/${framework_version}"',
        'framework_main="ASTRA_Framework_v0.3.0_Earth_Is_The_Instrument.pdf"',
        'framework_ground="ASTRA_v0.3.0_Public_Ground_Reading.pdf"',
        'framework_audit="ASTRA_Dual_Rent_Local_to_Global_Audit_Form_v0.3.0.pdf"',
        'framework_report="ASTRA_v0.3.0_Verification_Report.pdf"',
        'framework_archive="ASTRA_Framework_v0.3.0_Dual_Rent_Arithmetic_Seams.zip"',
        '"${framework_archive}.sha256"',
        '"${framework_archive}.verify.txt"',
        '"PUBLICATION_AUDIT.md"',
        'test "$(git cat-file -t "$framework_ref")" = tag',
        'git merge-base --is-ancestor "$framework_commit" HEAD',
        "releases/tags/${framework_tag}",
        'git show "${framework_ref}^{commit}:${framework_path}/SHA256SUMS.txt"',
        '"$framework_release_dir/TAG_SHA256SUMS.txt"',
        'test "$(wc -l < "$framework_release_dir/SHA256SUMS.txt")" -eq 10',
        'sha256sum --check --strict "${framework_archive}.sha256"',
        'grep -Fx -- "verification_status: PASS" "${framework_archive}.verify.txt"',
        'cp -- "$framework_release_dir/$asset" "$framework_target_dir/$asset"',
        'cp -- "$framework_path/ERRATA.md" "$framework_target_dir/ERRATA.md"',
        'framework_pages_roster=(',
        '"audit-form/index.html"',
        '"errata/index.html"',
        '"ground-reading/index.html"',
        '<(find "$framework_target_dir" -type f -printf \'%P\\n\' | sort)',
        'write_redirect "$site/resources/earth-is-the-instrument" "./${framework_version}/"',
        'write_redirect "$site/resources/earth-is-the-instrument/latest" "../${framework_version}/"',
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
        "./v1.0.7/preprint/",
        "./v1.0.7/supplement/",
        "./latest/",
        "./editions/",
        "./resources/",
        "./resources/earth-is-the-instrument/v0.3.0/",
        "./resources/earth-is-the-instrument/v0.3.0/ground-reading/",
        "./resources/earth-is-the-instrument/v0.3.0/errata/",
        "./resources/earth-is-the-instrument/v0.1/",
        "./schemas/",
    } <= links
    skip_links = [link for link in parser.links if "skip-link" in link.get("class", "").split()]
    assert skip_links == [{"class": "skip-link", "href": "#main-content"}]

    script = str(load_yaml(PAGES_WORKFLOW)["jobs"]["build"]["steps"][1]["run"])
    assert 'version_dir="$site/$tag"' in script
    assert 'write_redirect "$site/latest" "../${current_tag}/"' in script
    assert 'write_redirect "$site/latest/preprint" "../../${current_tag}/preprint/"' in script
    assert 'write_redirect "$site/latest/supplement" "../../${current_tag}/supplement/"' in script
    assert 'cp -R -- "$source_root/schemas" "$version_dir/schemas"' in script
    assert 'target="$site/schemas/$relative"' in script
    assert "Current reference edition" in script
    assert "Earlier immutable reference editions" in script
    assert "for ((index=${#release_tags[@]} - 1; index >= 0; index--))" in script
    assert 'test "$tag" != "$current_tag"' in script
    assert "GitHub Latest</li>" in script

    spec = json.loads((ROOT / "RELEASE_SPEC.json").read_text(encoding="utf-8"))
    schema_root = "https://jkolantree.github.io/astra/schemas/"
    schema_paths = sorted((ROOT / "schemas").glob("*.schema.json"))
    assert schema_paths
    for path in schema_paths:
        schema = json.loads(path.read_text(encoding="utf-8"))
        assert schema["$id"] == f"{schema_root}{path.name}"
        assert spec["version"] == "1.0.7"


def test_working_paper_pages_companion_is_text_first_and_well_bounded() -> None:
    path = ROOT / "docs" / "resources" / "earth-is-the-instrument" / "v0.1" / "index.html"
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
        "../v0.3.0/",
        "https://github.com/jkolantree/astra/blob/main/RELEASE_NOTES_earth-instrument-wp-0.1.md",
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
    meta_keys = {meta.get("name") or meta.get("property") for meta in parser.metas}
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
            "og:image:alt",
        } <= meta_keys

    semantic = " ".join(re.sub(r"<[^>]+>", " ", html).split())
    required_boundaries = (
        "supplemental exploratory working paper",
        "Historical edition",
        "current edition in this supplemental line is ASTRA Framework v0.3.0",
        "Project-level provenance",
        "substantive ChatGPT assistance",
        "Kansas motto",
        "project is independent and unaffiliated",
        "not peer reviewed",
        "Neither edition amends or supersedes the current SPPT/ASTRA v1.0.7 core",
        "provides empirical validation",
        "not a tagged PDF",
        "no reuse license is asserted for the PDF or cover image",
        "available by August 2026",
        "does not establish a particular artifact's historicity",
        "pixel-for-pixel with no differences",
        "rather than silently rewriting the immutable v0.1 PDF",
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


def test_framework_v030_pages_companions_are_accessible_and_release_bound() -> None:
    root = ROOT / "docs" / "resources" / "earth-is-the-instrument" / "v0.3.0"
    landing_html = (root / "index.html").read_text(encoding="utf-8")
    landing = LandingPageParser()
    landing.feed(landing_html)
    assert landing.lang == "en-US"
    assert landing.main_ids == ["main-content"]
    assert len(landing.ids) == len(set(landing.ids))
    assert landing.scripts == []
    assert landing.caption_count == 1
    assert landing.th_scopes.count("col") == 2
    assert landing.th_scopes.count("row") == 7
    assert any(
        image.get("src") == "./cover.png"
        and image.get("width") == "510"
        and image.get("height") == "660"
        and "Earth Is the Instrument" in image.get("alt", "")
        for image in landing.images
    )
    landing_links = {link.get("href", "") for link in landing.links}
    assert {
        "#main-content",
        "./ground-reading/",
        "./audit-form/",
        "./ASTRA_Framework_v0.3.0_Earth_Is_The_Instrument.pdf",
        "./ASTRA_v0.3.0_Public_Ground_Reading.pdf",
        "./ASTRA_Dual_Rent_Local_to_Global_Audit_Form_v0.3.0.pdf",
        "./ASTRA_v0.3.0_Verification_Report.pdf",
        "./errata/",
        "./PUBLICATION_AUDIT.md",
        "./FONT_NOTICES.txt",
        "./SHA256SUMS.txt",
        "https://github.com/jkolantree/astra/releases/tag/earth-instrument-framework-v0.3.0",
    } <= landing_links
    landing_semantic = " ".join(re.sub(r"<[^>]+>", " ", landing_html).split())
    for value in (
        "not peer reviewed",
        "supersedes an internal v0.2.1 predecessor preserved in its archive",
        "no public v0.2.1 tag or GitHub Release was created",
        "not claimed to conform to PDF/UA",
        "internal package and release report",
        "substantive assistance from OpenAI's ChatGPT",
        "Ad Astra Per Aspera",
        'internal version of Astra as "our next major model"',
        "not affiliated with, sponsored by, endorsed by, reviewed by, operated by, or produced for OpenAI",
        "role-based review architecture, not a separate institution",
        "The main framework PDF discloses language-model assistance",
        "The three compact companion PDFs do not carry that disclosure",
        "Choose a reading path",
        "post-publication errata",
        "35,343,563 bytes",
        "b2a1072c14f1afff43a161b57620cdd2f6ad19b03884e7b5d8fbdd023333e09d",
        "2f8c26c92826c0464ae88048d9c3e68a4404ee5d9b8f46a660a0733ccddd75ab",
    ):
        assert value in landing_semantic
    assert (
        "Jacko T. (2026). Earth Is the Instrument: Dual-Rent Seams, Prime Spectra, "
        "Local-to-Global Certificates, Geological Memory, and the Search for Human Origins . "
        "ASTRA Framework v0.3.0. GitHub."
    ) in landing_semantic
    assert "The four preserved PDFs already disclose" not in landing_semantic

    ground_html = (root / "ground-reading" / "index.html").read_text(encoding="utf-8")
    ground = LandingPageParser()
    ground.feed(ground_html)
    assert ground.lang == "en-US"
    assert ground.main_ids == ["main-content"]
    assert len(ground.ids) == len(set(ground.ids))
    assert ground.scripts == []
    assert ground.math_count == 4
    assert "https://isa-afp.org/entries/Jacobian_Counterexample.html" in ground_html
    assert "https://arxiv.org/abs/2608.00222" in ground_html
    assert "recent preprint rather than peer-reviewed publication" in ground_html
    assert "two-dimensional Jacobian conjecture remains open" in ground_html
    assert "../errata/" in ground_html

    audit_html = (root / "audit-form" / "index.html").read_text(encoding="utf-8")
    worksheet = LandingPageParser()
    worksheet.feed(audit_html)
    assert worksheet.lang == "en-US"
    assert worksheet.main_ids == ["main-content"]
    assert len(worksheet.ids) == len(set(worksheet.ids))
    assert worksheet.scripts == []
    assert worksheet.form_count == 0
    assert worksheet.control_count == 51
    assert not re.search(
        r"<form\b|\baction\s*=|localStorage|sessionStorage|document[.]cookie|fetch\s*\(",
        audit_html,
        flags=re.IGNORECASE,
    )
    assert "not sent by this page" in audit_html
    assert "static, not electronically fillable" in audit_html
    assert "../errata/" in audit_html

    errata_html = (root / "errata" / "index.html").read_text(encoding="utf-8")
    errata = LandingPageParser()
    errata.feed(errata_html)
    assert errata.lang == "en-US"
    assert errata.main_ids == ["main-content"]
    assert len(errata.ids) == len(set(errata.ids))
    assert errata.scripts == []
    errata_semantic = " ".join(re.sub(r"<[^>]+>", " ", errata_html).split())
    assert "all four preserved PDFs" in errata_semantic
    assert "The 171-page main framework PDF contains the disclosure" in errata_semantic
    assert "public ground reading, audit form, and verification report do not" in errata_semantic
    assert "No public v0.2.1 tag or GitHub Release was created" in errata_semantic
    assert "do not replace, edit, or reissue any PDF" in errata_semantic


def test_pages_home_scopes_rights_and_separates_publication_tracks() -> None:
    html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    semantic = " ".join(re.sub(r"<[^>]+>", " ", html).split())
    assert "Current reference framework — v1.0.7" in semantic
    assert "Current supplemental framework — v0.3.0" in semantic
    assert "ASTRA Framework v0.3.0" in semantic
    assert "supersedes an internal v0.2.1 predecessor preserved in its archive" in semantic
    assert "no public v0.2.1 tag or GitHub Release was created" in semantic
    assert "does not amend or supersede stable SPPT/ASTRA v1.0.7, enter its claim-admission matrix, inherit its verification" in semantic
    assert "inherit its verification, or provide empirical validation" in semantic
    assert "Separately supplied resources retain the rights stated" in semantic
    assert "Original manuscript, documentation, figures, and data" not in semantic
    assert 'href="./v1.0.7/preprint/"' in html
    assert 'href="./v1.0.7/supplement/"' in html
    assert 'href="./latest/"' in html
    assert 'href="./resources/earth-is-the-instrument/v0.3.0/ground-reading/"' in html
    assert 'href="./resources/earth-is-the-instrument/v0.3.0/audit-form/"' in html

    css = (ROOT / "docs" / "style.css").read_text(encoding="utf-8")
    assert re.search(r"[.]cover-link,\s*[.]cover-link img,\s*[.]paper-cover", css)


def test_pages_home_and_working_paper_reflow_at_narrow_widths() -> None:
    paths = (
        ROOT / "docs" / "index.html",
        ROOT / "docs" / "resources" / "earth-is-the-instrument" / "v0.3.0" / "index.html",
        ROOT
        / "docs"
        / "resources"
        / "earth-is-the-instrument"
        / "v0.3.0"
        / "ground-reading"
        / "index.html",
        ROOT
        / "docs"
        / "resources"
        / "earth-is-the-instrument"
        / "v0.3.0"
        / "audit-form"
        / "index.html",
        ROOT
        / "docs"
        / "resources"
        / "earth-is-the-instrument"
        / "v0.3.0"
        / "errata"
        / "index.html",
        ROOT / "docs" / "resources" / "earth-is-the-instrument" / "v0.1" / "index.html",
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


def test_resource_index_marks_v030_current_without_changing_core_version() -> None:
    html = (ROOT / "docs" / "resources" / "index.html").read_text(encoding="utf-8")
    semantic = " ".join(re.sub(r"<[^>]+>", " ", html).split())
    assert "ASTRA Framework v0.3.0" in semantic
    assert "Current supplemental edition" in semantic
    assert "supersedes an internal v0.2.1 predecessor preserved in its archive" in semantic
    assert "not a public v0.2.1 release" in semantic
    assert "Working Paper 0.1" in semantic
    assert "Historical edition" in semantic
    assert "separate from stable SPPT/ASTRA v1.0.7" in semantic
    assert "| Edition |" not in (
        ROOT / "resources" / "README.md"
    ).read_text(encoding="utf-8")
    assert "./earth-is-the-instrument/latest/" in html
    assert "./earth-is-the-instrument/v0.3.0/errata/" in html


def test_resource_index_separates_published_routes_from_repository_drafts() -> None:
    html = (ROOT / "docs" / "resources" / "index.html").read_text(encoding="utf-8")
    semantic = " ".join(re.sub(r"<[^>]+>", " ", html).split())
    assert (
        "Published editions have reading routes; unpromoted drafts remain source-tree-only."
        in semantic
    )
    assert "Other versioned package" in semantic
    assert "Sector-Complete Instrument" in semantic
    assert "has no Pages route, DOI, or Zenodo record" in semantic
    assert "Repository-visible unpromoted drafts" in semantic
    assert "not Pages editions or release assets" in semantic
    assert "do not enter the v1.0.7 claim matrix" in semantic
    for relative in (
        "cosmic-visibility-framework/draft-v0.1.0",
        "sppt-bridge-protocol/draft-v0.1.0",
        "coherence-cell-exploration/draft-v0.1.0",
        "active-support-audit/draft-v0.1.0",
    ):
        assert f"https://github.com/jkolantree/astra/tree/main/resources/{relative}" in html


def test_not_found_page_routes_to_both_current_publication_tracks() -> None:
    html = (ROOT / "docs" / "404.html").read_text(encoding="utf-8")
    parser = LandingPageParser()
    parser.feed(html)
    links = {link.get("href", "") for link in parser.links}
    assert {
        "/astra/",
        "/astra/latest/",
        "/astra/resources/",
        "/astra/resources/earth-is-the-instrument/latest/",
    } <= links


def test_skip_link_uses_high_contrast_focus_on_dark_header() -> None:
    css = (ROOT / "docs" / "style.css").read_text(encoding="utf-8")
    assert re.search(
        r"\.skip-link:focus-visible\s*\{[^}]*outline-color:[ \t]*#ffffff",
        css,
        flags=re.DOTALL,
    )

    def channel(value: int) -> float:
        normalized = value / 255
        return (
            normalized / 12.92 if normalized <= 0.04045 else ((normalized + 0.055) / 1.055) ** 2.4
        )

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
    assert config["contact_links"][1]["url"].endswith(
        "/astra/resources/earth-is-the-instrument/latest/"
    )

    for name in expected:
        form_text = (forms_root / name).read_text(encoding="utf-8")
        form = load_yaml(forms_root / name)
        assert all(form.get(key) for key in ("name", "description", "title", "body"))
        assert "v1.0.6" in form_text
        assert "earth-instrument-framework-v0.3.0" in form_text
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
