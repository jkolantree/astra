"""Shared, deterministic URL and fragment helpers for ASTRA link audits."""

from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

EXTERNAL_SCHEMES = {"http", "https", "mailto"}
IGNORED_SCHEMES = {"data", "javascript", "tel"}


class HTMLInventory(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.references: list[tuple[str, str]] = []
        self.canonicals: list[str] = []
        self.refreshes: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.casefold(): value or "" for key, value in attrs}
        if values.get("id"):
            self.ids.add(values["id"])
        if values.get("name") and tag.casefold() == "a":
            self.ids.add(values["name"])
        for attribute in ("href", "src", "poster"):
            if values.get(attribute):
                self.references.append((attribute, values[attribute]))
        rel = {part.casefold() for part in values.get("rel", "").split()}
        if tag.casefold() == "link" and "canonical" in rel and values.get("href"):
            self.canonicals.append(values["href"])
        if (
            tag.casefold() == "meta"
            and values.get("http-equiv", "").casefold() == "refresh"
        ):
            match = re.search(r"(?i)(?:^|;)\s*url\s*=\s*(['\"]?)(.*?)\1\s*$", values.get("content", ""))
            if match and match.group(2):
                self.refreshes.append(html.unescape(match.group(2)))


def parse_html(path: Path) -> HTMLInventory:
    parser = HTMLInventory()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    return parser


def strip_markdown_fences(text: str) -> str:
    output: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if match:
            token = match.group(1)
            if fence is None:
                fence = token[0]
            elif token[0] == fence:
                fence = None
            output.append("")
        else:
            output.append(line if fence is None else "")
    return "\n".join(output)


def markdown_links(text: str) -> list[str]:
    """Extract actual inline Markdown link/image destinations.

    Requiring the literal `](` transition avoids treating mathematical bracket
    notation as a link. Fenced code is removed before matching.
    """

    value = strip_markdown_fences(text)
    # Math often uses TeX constructs such as `r_M(q)` or `[r_M](q)` that look
    # deceptively like Markdown links. Remove math spans before recognizing the
    # literal Markdown `](` transition.
    value = re.sub(r"\$\$.*?\$\$", "", value, flags=re.DOTALL)
    value = re.sub(r"\\\[.*?\\\]", "", value, flags=re.DOTALL)
    value = re.sub(r"\\\(.*?\\\)", "", value, flags=re.DOTALL)
    value = re.sub(r"(?<!\\)\$[^$\n]+\$", "", value)
    destinations: list[str] = []
    pattern = re.compile(r"!?\[[^\]\n]*\]\(\s*(<[^>\n]+>|[^\s)\n]+)(?:\s+['\"][^\n]*['\"])?\s*\)")
    for match in pattern.finditer(value):
        destination = match.group(1)
        if destination.startswith("<") and destination.endswith(">"):
            destination = destination[1:-1]
        destinations.append(html.unescape(destination))
    return destinations


def github_heading_ids(text: str) -> set[str]:
    ids: set[str] = set()
    counts: dict[str, int] = {}
    for line in strip_markdown_fences(text).splitlines():
        match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        heading = re.sub(r"\{#[A-Za-z0-9_.:-]+[^}]*\}\s*$", "", match.group(1))
        heading = re.sub(r"!?(?:\[([^\]]*)\]\([^)]*\))", r"\1", heading)
        heading = re.sub(r"[`*_~]", "", heading)
        heading = html.unescape(re.sub(r"<[^>]+>", "", heading)).casefold()
        slug = re.sub(r"[^\w\- ]", "", heading, flags=re.UNICODE)
        slug = re.sub(r"[\s-]+", "-", slug).strip("-")
        if not slug:
            continue
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        ids.add(slug if count == 0 else f"{slug}-{count}")
    return ids


def classify_url(value: str) -> tuple[str, str, str]:
    parsed = urlsplit(value)
    scheme = parsed.scheme.casefold()
    if scheme in EXTERNAL_SCHEMES:
        return "external", value, parsed.fragment
    if scheme in IGNORED_SCHEMES:
        return "ignored", value, parsed.fragment
    if scheme or parsed.netloc:
        return "unsafe", value, parsed.fragment
    return "local", unquote(parsed.path), unquote(parsed.fragment)


def case_sensitive_path(root: Path, relative: Path) -> Path | None:
    if relative.is_absolute() or ".." in relative.parts:
        return None
    current = root
    for part in relative.parts:
        if part in {"", "."}:
            continue
        if not current.is_dir():
            return None
        exact = {child.name: child for child in current.iterdir()}.get(part)
        if exact is None:
            return None
        current = exact
    return current


def site_reference_path(page_relative: str, destination: str) -> tuple[str, str]:
    base = "https://local.invalid/" + page_relative
    resolved = urlsplit(urljoin(base, destination))
    return unquote(resolved.path).lstrip("/"), unquote(resolved.fragment)


def fragment_ids(path: Path) -> set[str]:
    if path.suffix.casefold() in {".html", ".htm"}:
        return parse_html(path).ids
    if path.suffix.casefold() == ".md":
        return github_heading_ids(path.read_text(encoding="utf-8"))
    return set()
