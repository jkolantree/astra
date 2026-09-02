"""Audit every internal route, asset, fragment, canonical, and redirect in a Pages artifact."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_ORIGIN = "https://jkolantree.github.io"
PUBLIC_PREFIX = "/astra/"

sys.path.insert(0, str(ROOT))
from tools.link_audit_common import classify_url, parse_html, site_reference_path  # noqa: E402


def _target(site: Path, page_relative: str, destination: str) -> tuple[Path | None, str]:
    if destination.startswith(PUBLIC_ORIGIN + PUBLIC_PREFIX):
        destination = destination.removeprefix(PUBLIC_ORIGIN + PUBLIC_PREFIX)
        page_relative = ""
    elif destination.startswith(PUBLIC_PREFIX):
        destination = destination.removeprefix(PUBLIC_PREFIX)
        page_relative = ""
    kind, _path, _fragment = classify_url(destination)
    if kind in {"external", "ignored"}:
        return None, ""
    if kind == "unsafe" or "\\" in destination:
        raise RuntimeError(f"Unsafe Pages destination: {destination!r}")
    relative, fragment = site_reference_path(page_relative, destination)
    if not relative:
        relative = "index.html"
    candidate = site / relative
    if destination.split("#", 1)[0].endswith("/") or candidate.is_dir():
        candidate /= "index.html"
    try:
        candidate.resolve().relative_to(site.resolve())
    except ValueError as error:
        raise RuntimeError(f"Pages destination escapes artifact: {destination!r}") from error
    return candidate, fragment


def check_pages_links(site: Path) -> dict[str, int]:
    site = site.resolve()
    if not site.is_dir():
        raise RuntimeError(f"Assembled Pages directory is missing: {site}")
    failures: list[str] = []
    html_files = sorted(site.rglob("*.html"))
    assets = 0
    fragments = 0
    canonicals = 0
    redirects = 0
    for page in html_files:
        relative = page.relative_to(site).as_posix()
        inventory = parse_html(page)
        if len(inventory.canonicals) > 1:
            failures.append(f"{relative}: multiple canonical tags")
        canonicals += len(inventory.canonicals)
        references = list(inventory.references)
        references.extend(("refresh", value) for value in inventory.refreshes)
        redirects += len(inventory.refreshes)
        for attribute, destination in references:
            try:
                target, fragment = _target(site, relative, destination)
            except RuntimeError as error:
                failures.append(f"{relative}: {error}")
                continue
            if target is None:
                continue
            assets += 1
            if not target.is_file():
                failures.append(
                    f"{relative}: {attribute} target is missing: {destination!r} -> "
                    f"{target.relative_to(site).as_posix()}"
                )
                continue
            if fragment:
                fragments += 1
                if target.suffix.casefold() not in {".html", ".htm"}:
                    failures.append(f"{relative}: fragment targets a non-HTML asset {destination!r}")
                elif fragment not in parse_html(target).ids:
                    failures.append(f"{relative}: missing fragment #{fragment} in {target.relative_to(site).as_posix()}")
        if page.suffix.casefold() == ".html":
            raw = page.read_text(encoding="utf-8")
            for css_url in re.findall(r"(?i)url\(\s*['\"]?([^)'\"]+)", raw):
                if css_url.startswith("data:"):
                    continue
                try:
                    target, _fragment = _target(site, relative, css_url)
                except RuntimeError as error:
                    failures.append(f"{relative}: {error}")
                    continue
                if target is not None and not target.is_file():
                    failures.append(f"{relative}: inline CSS asset is missing {css_url!r}")
    for stylesheet in sorted(site.rglob("*.css")):
        relative = stylesheet.relative_to(site).as_posix()
        for css_url in re.findall(
            r"(?i)url\(\s*['\"]?([^)'\"]+)", stylesheet.read_text(encoding="utf-8")
        ):
            if css_url.startswith("data:"):
                continue
            try:
                target, _fragment = _target(site, relative, css_url)
            except RuntimeError as error:
                failures.append(f"{relative}: {error}")
                continue
            if target is not None and not target.is_file():
                failures.append(f"{relative}: CSS asset is missing {css_url!r}")
    if failures:
        raise RuntimeError("Assembled Pages link audit failed:\n" + "\n".join(failures))
    return {
        "html_files": len(html_files),
        "internal_references": assets,
        "fragments": fragments,
        "canonicals": canonicals,
        "redirects": redirects,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("site", type=Path)
    args = parser.parse_args()
    result = check_pages_links(args.site)
    print(
        "Assembled Pages link audit passed for "
        f"{result['html_files']} HTML files and {result['internal_references']} internal references."
    )


if __name__ == "__main__":
    main()
