"""Semantic, responsive, keyboard, print, and reduced-motion Atlas checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "resources" / "dark-medium-response-atlas" / "v0.1.0"
HTML = PACKAGE / "dark-medium-response-atlas-v0.1.0.html"
REPORT = PACKAGE / "html-accessibility.json"
CANONICAL = (
    "https://jkolantree.github.io/astra/resources/"
    "dark-medium-response-atlas/v0.1.0/"
)
TITLE = "Dark-Medium Response Atlas v0.1.0 — Path, Compensation, Memory, and Observation"


class AtlasHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang = ""
        self.title_depth = 0
        self.title_parts: list[str] = []
        self.ids: list[str] = []
        self.headings: list[tuple[int, str]] = []
        self._heading_level = 0
        self._heading_parts: list[str] = []
        self.links: list[dict[str, str]] = []
        self.canonicals: list[str] = []
        self.main_ids: list[str] = []
        self.headers = 0
        self.footers = 0
        self.doc_tocs = 0
        self.status_boxes = 0
        self.tables = 0
        self.captions = 0
        self.col_headers = 0
        self.row_headers = 0
        self.math = 0
        self.images: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if values.get("id"):
            self.ids.append(values["id"])
        if tag == "html":
            self.lang = values.get("lang", "")
        elif tag == "title":
            self.title_depth += 1
        elif re.fullmatch(r"h[1-6]", tag):
            self._heading_level = int(tag[1])
            self._heading_parts = []
        elif tag == "a":
            self.links.append(values)
        elif tag == "link" and "canonical" in values.get("rel", "").split():
            self.canonicals.append(values.get("href", ""))
        elif tag == "main":
            self.main_ids.append(values.get("id", ""))
        elif tag == "header":
            self.headers += 1
        elif tag == "footer":
            self.footers += 1
        elif tag == "nav" and values.get("role") == "doc-toc":
            self.doc_tocs += 1
        elif tag == "aside" and "status-box" in values.get("class", "").split():
            self.status_boxes += 1
        elif tag == "table":
            self.tables += 1
        elif tag == "caption":
            self.captions += 1
        elif tag == "th" and values.get("scope") == "col":
            self.col_headers += 1
        elif tag == "th" and values.get("scope") == "row":
            self.row_headers += 1
        elif tag == "math":
            self.math += 1
        elif tag == "img":
            self.images.append(values)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self.title_depth:
            self.title_depth -= 1
        elif re.fullmatch(r"h[1-6]", tag) and self._heading_level:
            text = re.sub(r"\s+", " ", "".join(self._heading_parts)).strip()
            self.headings.append((self._heading_level, text))
            self._heading_level = 0
            self._heading_parts = []

    def handle_data(self, data: str) -> None:
        if self.title_depth:
            self.title_parts.append(data)
        if self._heading_level:
            self._heading_parts.append(data)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_rgb(value: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*[\d.]+)?\)", value)
    if match is None:
        raise RuntimeError(f"Unsupported computed color: {value!r}")
    return tuple(int(item) for item in match.groups())


def luminance(rgb: tuple[int, int, int]) -> float:
    def channel(value: int) -> float:
        normalized = value / 255
        return (
            normalized / 12.92
            if normalized <= 0.04045
            else ((normalized + 0.055) / 1.055) ** 2.4
        )

    red, green, blue = (channel(value) for value in rgb)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast(first: str, second: str) -> float:
    values = sorted((luminance(parse_rgb(first)), luminance(parse_rgb(second))))
    return (values[1] + 0.05) / (values[0] + 0.05)


def static_checks(path: Path) -> AtlasHTMLParser:
    raw = path.read_text(encoding="utf-8")
    parser = AtlasHTMLParser()
    parser.feed(raw)
    parser.close()
    title = re.sub(r"\s+", " ", "".join(parser.title_parts)).strip()
    failures: list[str] = []
    if parser.lang != "en-US":
        failures.append("document language is not en-US")
    if title != TITLE:
        failures.append(f"title mismatch: {title!r}")
    if parser.canonicals != [CANONICAL]:
        failures.append(f"canonical mismatch: {parser.canonicals}")
    if len(parser.ids) != len(set(parser.ids)):
        failures.append("duplicate HTML IDs")
    if parser.main_ids != ["main-content"]:
        failures.append(f"main landmarks: {parser.main_ids}")
    if (parser.headers, parser.footers, parser.doc_tocs, parser.status_boxes) != (1, 1, 1, 1):
        failures.append(
            "landmark counts "
            f"header={parser.headers} footer={parser.footers} "
            f"toc={parser.doc_tocs} status={parser.status_boxes}"
        )
    if parser.tables != 4 or parser.captions != parser.tables:
        failures.append(f"table/caption counts {parser.tables}/{parser.captions}")
    if parser.col_headers < parser.tables or parser.row_headers < parser.tables:
        failures.append("table header scopes are incomplete")
    if parser.math < 1:
        failures.append("structured MathML is absent")
    if any(not text for _level, text in parser.headings):
        failures.append("empty heading")
    levels = [level for level, _text in parser.headings]
    if any(
        current > previous + 1
        for previous, current in zip(levels, levels[1:], strict=False)
    ):
        failures.append("heading hierarchy skips a level")
    skip = [
        item
        for item in parser.links
        if "skip-link" in item.get("class", "").split()
    ]
    if skip != [{"class": "skip-link", "href": "#main-content"}]:
        failures.append(f"skip-link mismatch: {skip}")
    if any(not item.get("href") for item in parser.links):
        failures.append("empty link destination")
    if any(not item.get("alt", "").strip() for item in parser.images):
        failures.append("image without alternative text")
    if re.search(r"[A-Za-z]:\\|/Users/|/home/", raw):
        failures.append("machine-local path")
    if failures:
        raise RuntimeError("Atlas HTML static checks failed: " + "; ".join(failures))
    return parser


def browser_checks(path: Path) -> dict[str, Any]:
    results: dict[str, Any] = {"viewports": {}}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=["--disable-gpu"])
        try:
            page = browser.new_page()
            for width in (1440, 400, 320):
                page.set_viewport_size({"width": width, "height": 1000})
                page.emulate_media(media="screen", reduced_motion="no-preference")
                page.goto(path.resolve().as_uri(), wait_until="load")
                observed = page.evaluate(
                    """() => ({
                      viewport: window.innerWidth,
                      client: document.documentElement.clientWidth,
                      rootScroll: document.documentElement.scrollWidth,
                      bodyScroll: document.body.scrollWidth
                    })"""
                )
                if max(observed["rootScroll"], observed["bodyScroll"]) > observed["client"]:
                    raise RuntimeError(f"Horizontal overflow at {width}px: {observed}")
                results["viewports"][str(width)] = observed

            page.set_viewport_size({"width": 400, "height": 1000})
            page.goto(path.resolve().as_uri(), wait_until="load")
            unnamed = page.locator("a").evaluate_all(
                r"""(anchors) => anchors
                  .filter((anchor) => !(anchor.innerText || anchor.getAttribute("aria-label") || "")
                    .replace(/\s+/g, " ").trim())
                  .length"""
            )
            if unnamed:
                raise RuntimeError(f"{unnamed} links have no accessible name")
            page.keyboard.press("Tab")
            focus = page.evaluate(
                """() => {
                  const item = document.activeElement;
                  const style = getComputedStyle(item);
                  const background = getComputedStyle(item.parentElement || document.body)
                    .backgroundColor;
                  return {
                    className: item.className,
                    outlineColor: style.outlineColor,
                    outlineStyle: style.outlineStyle,
                    outlineWidth: parseFloat(style.outlineWidth),
                    background
                  };
                }"""
            )
            if "skip-link" not in str(focus["className"]).split():
                raise RuntimeError("First keyboard stop is not the skip link")
            if focus["outlineStyle"] in {"none", "hidden"} or float(focus["outlineWidth"]) < 2:
                raise RuntimeError(f"Focus indicator is not visible: {focus}")
            focus_contrast = contrast(str(focus["outlineColor"]), str(focus["background"]))
            if focus_contrast < 3:
                raise RuntimeError(f"Focus contrast is below 3:1: {focus_contrast:.3f}")
            page.keyboard.press("Enter")
            if page.evaluate("document.activeElement.id") != "main-content":
                raise RuntimeError("Skip link did not move keyboard focus to main content")

            page.set_viewport_size({"width": 816, "height": 1056})
            page.emulate_media(media="print", reduced_motion="reduce")
            page.goto(path.resolve().as_uri(), wait_until="load")
            print_state = page.evaluate(
                """() => ({
                  rootClient: document.documentElement.clientWidth,
                  rootScroll: document.documentElement.scrollWidth,
                  mainDisplay: getComputedStyle(document.querySelector("main")).display
                })"""
            )
            if print_state["rootScroll"] > print_state["rootClient"]:
                raise RuntimeError(f"Print layout overflows horizontally: {print_state}")
            if print_state["mainDisplay"] == "none":
                raise RuntimeError("Print layout hides main content")
            if page.evaluate("getComputedStyle(document.documentElement).scrollBehavior") != "auto":
                raise RuntimeError("Reduced-motion mode retains smooth scrolling")
            if page.evaluate("document.getAnimations().length") != 0:
                raise RuntimeError("Reduced-motion mode retains an active animation")
            results["keyboard"] = {
                "first_stop": "skip-link",
                "skip_target": "main-content",
                "minimum_focus_contrast": focus_contrast,
            }
            results["print"] = print_state
            results["reduced_motion"] = {"active_animation_count": 0}
            results["browser"] = browser.version
        finally:
            browser.close()
    return results


def check_html(path: Path = HTML, *, write_report: bool = False) -> dict[str, Any]:
    parser = static_checks(path)
    report = {
        "schema": (
            "https://jkolantree.github.io/astra/schemas/"
            "dark-medium-response-atlas-html-accessibility-v1.schema.json"
        ),
        "file": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "headings": len(parser.headings),
        "links": len(parser.links),
        "tables": parser.tables,
        "mathml_formulas": parser.math,
        **browser_checks(path),
    }
    if write_report:
        REPORT.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", type=Path, default=HTML)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    report = check_html(args.path.resolve(), write_report=args.write)
    if not args.write:
        print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
