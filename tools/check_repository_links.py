"""Check repository-relative Markdown paths and fragments case-sensitively."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {".git", ".venv", "tmp", "dist", "build", "__pycache__"}

sys.path.insert(0, str(ROOT))
from tools.link_audit_common import (  # noqa: E402
    case_sensitive_path,
    classify_url,
    fragment_ids,
    markdown_links,
)


def markdown_files(root: Path = ROOT) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.md")
        if path.is_file() and not (set(path.relative_to(root).parts) & IGNORED_PARTS)
    )


def check_repository_links(root: Path = ROOT) -> dict[str, int]:
    failures: list[str] = []
    checked = 0
    fragments = 0
    for source in markdown_files(root):
        relative_source = source.relative_to(root).as_posix()
        for destination in markdown_links(source.read_text(encoding="utf-8")):
            kind, path_text, fragment = classify_url(destination)
            if kind in {"external", "ignored"}:
                continue
            checked += 1
            if kind == "unsafe" or "\\" in path_text:
                failures.append(f"{relative_source}: unsafe link {destination!r}")
                continue
            if not path_text:
                target = source
            elif path_text.startswith("/"):
                failures.append(f"{relative_source}: repository link is absolute {destination!r}")
                continue
            else:
                lexical = source.parent.relative_to(root) / Path(path_text)
                normalized = Path(*[part for part in lexical.parts if part != "."])
                parts: list[str] = []
                escaped = False
                for part in normalized.parts:
                    if part == "..":
                        if not parts:
                            escaped = True
                            break
                        parts.pop()
                    else:
                        parts.append(part)
                if escaped:
                    failures.append(f"{relative_source}: link escapes repository {destination!r}")
                    continue
                target = case_sensitive_path(root, Path(*parts))
                if target is None:
                    failures.append(f"{relative_source}: missing or case-drifted target {destination!r}")
                    continue
            if target.is_dir():
                readme = case_sensitive_path(target, Path("README.md"))
                if readme is None:
                    failures.append(f"{relative_source}: directory target has no README.md {destination!r}")
                    continue
                target = readme
            if not target.is_file():
                failures.append(f"{relative_source}: target is not a file {destination!r}")
                continue
            if fragment:
                fragments += 1
                if fragment not in fragment_ids(target):
                    failures.append(
                        f"{relative_source}: missing fragment #{fragment} in "
                        f"{target.relative_to(root).as_posix()}"
                    )
    if failures:
        raise RuntimeError("Repository link audit failed:\n" + "\n".join(failures))
    return {"markdown_files": len(markdown_files(root)), "local_links": checked, "fragments": fragments}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    result = check_repository_links()
    print(
        "Repository link audit passed for "
        f"{result['markdown_files']} Markdown files, {result['local_links']} local links, "
        f"and {result['fragments']} fragments."
    )


if __name__ == "__main__":
    main()
