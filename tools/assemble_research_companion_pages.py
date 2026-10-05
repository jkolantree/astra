"""Assemble the explicitly admitted research companion without changing release routes."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.check_pages_admission import check_pages_admission  # noqa: E402

REVIEW = ROOT / "evidence/research_companion_pages_review_v1.json"
REVIEW_SCHEMA = "https://jkolantree.github.io/astra/schemas/research-companion-pages-review-v1.schema.json"
CHECKS = (
    "permitted_browser_surface",
    "desktop_and_mobile_layout",
    "keyboard_and_focus",
    "reduced_motion",
    "media_playback",
    "console_and_network",
    "assistive_technology",
    "final_publication_approval",
)
CANDIDATE_INPUTS = (
    ".github/workflows/pages.yml",
    "evidence/pages_admission_v2.json",
    "schemas/pages-admission-v2.schema.json",
    "schemas/research-companion-pages-review-v1.schema.json",
    "tools/assemble_research_companion_pages.py",
    "tools/build_pages_admission.py",
    "tools/check_pages_admission.py",
    "tools/check_pages_links.py",
    "tools/link_audit_common.py",
)
ALIAS = """<!doctype html>
<html lang="en-US">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="0; url=../resources/sppt-scm-research-companion/draft-v0.1.0/explorer/">
  <title>Research companion · Draft | ASTRA</title>
</head>
<body><main>
  <h1>SPPT / SCM research companion</h1>
  <p>Unpromoted research draft. Stable SPPT/ASTRA v1.0.7 retains its separate authority.</p>
  <p><a href="../resources/sppt-scm-research-companion/draft-v0.1.0/explorer/">Open the explorer</a></p>
</main></body>
</html>
""".encode()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def candidate_digest(root: Path = ROOT) -> str:
    """Bind review to admitted source bytes and the code that assembles them.

    The admission file covers all shell, companion and support bytes. The
    approval record and repository-wide manifest are excluded to avoid cycles.
    """
    values = [{"path": name, "sha256": digest(root / name)} for name in CANDIDATE_INPUTS]
    return hashlib.sha256(json.dumps(values, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def reject_links(path: Path) -> None:
    for part in (path, *path.parents):
        is_junction = getattr(part, "is_junction", None)
        if part.is_symlink() or bool(is_junction and is_junction()):
            raise RuntimeError("Pages inputs and destination must not use links or junctions")


def require_visual_review(path: Path = REVIEW, *, root: Path = ROOT) -> None:
    record = json.loads(path.read_text(encoding="utf-8"))
    fields = {"schema", "status", "candidate_sha256", "surface", "checks", "evidence"}
    if not isinstance(record, dict) or set(record) != fields or record["schema"] != REVIEW_SCHEMA:
        raise RuntimeError("Research companion browser-review record is malformed")
    if record["candidate_sha256"] != candidate_digest(root):
        raise RuntimeError("Research companion browser review is stale for the current candidate")
    if record["status"] != "approved":
        raise RuntimeError("Research companion publication blocked: permitted browser review and final approval are pending")
    if not isinstance(record["surface"], str) or not record["surface"].strip():
        raise RuntimeError("Browser review must identify the explicitly permitted surface")
    if record["checks"] != dict.fromkeys(CHECKS, True) or any(
        value is not True for value in record["checks"].values()
    ):
        raise RuntimeError("Research companion browser-review checklist is incomplete")
    evidence = record["evidence"]
    if not isinstance(evidence, list) or not evidence:
        raise RuntimeError("Browser review requires inspected screenshots and a written review")
    seen: set[str] = set()
    suffixes: set[str] = set()
    for item in evidence:
        if not isinstance(item, dict) or set(item) != {"path", "bytes", "sha256"}:
            raise RuntimeError("Browser-review evidence record is malformed")
        name = item["path"]
        if not isinstance(name, str):
            raise RuntimeError("Browser-review evidence path is malformed")
        relative = Path(name)
        if (
            relative.as_posix() != name
            or relative.is_absolute()
            or ".." in relative.parts
            or "\\" in name
            or relative.parent != Path("evidence/research-companion-browser-review")
            or relative.suffix not in {".png", ".md"}
            or name in seen
        ):
            raise RuntimeError("Browser-review evidence must have unique, bounded public paths")
        source = root / relative
        reject_links(source)
        if not source.is_file() or source.stat().st_size != item["bytes"] or digest(source) != item["sha256"]:
            raise RuntimeError("Browser-review evidence bytes differ from the reviewed record")
        if relative.suffix == ".png" and not source.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            raise RuntimeError("Browser-review screenshot is not a PNG")
        seen.add(name)
        suffixes.add(relative.suffix)
    if suffixes != {".png", ".md"}:
        raise RuntimeError("Browser review requires both screenshots and a written review")


def snapshot(site: Path) -> dict[str, str]:
    entries = {}
    for path in sorted(site.rglob("*")):
        reject_links(path)
        if path.is_file():
            entries[path.relative_to(site).as_posix()] = digest(path)
    return entries


def assemble(site: Path, *, require_reviewed: bool = False) -> dict[str, Any]:
    record = check_pages_admission()
    if require_reviewed:
        require_visual_review()
    reject_links(site)
    site = site.resolve()
    if site == ROOT or ROOT in site.parents or not site.is_dir():
        raise RuntimeError("Companion assembly requires an existing artifact outside the source tree")
    before = snapshot(site)
    for item in record["head_shell"]["files"]:
        if before.get(item["path"]) != item["sha256"]:
            raise RuntimeError("Research companion assembly requires the exact admitted Pages shell")
    companion = record["research_companion"]
    namespace = companion["root"]
    if (site / namespace).exists() or (site / "explore").exists():
        raise RuntimeError("Research companion route collision; existing routes must not be overwritten")
    copies = [
        {**item, "path": f"{namespace}/{item['path']}"}
        for item in companion["files"]
    ] + companion["support_files"]
    # Preflight every destination before writing any bytes. Identical existing
    # notices are reused; no pre-existing file is overwritten.
    for item in copies:
        source = ROOT / item["path"]
        target = site / item["path"]
        reject_links(source)
        reject_links(target)
        if digest(source) != item["sha256"] or source.stat().st_size != item["bytes"]:
            raise RuntimeError("Research companion source changed after admission")
        if target.exists() and (not target.is_file() or digest(target) != item["sha256"]):
            raise RuntimeError("Research companion support-file collision")
        if any(parent.exists() and not parent.is_dir() for parent in target.parents):
            raise RuntimeError("Research companion destination parent is not a directory")
    for item in copies:
        target = site / item["path"]
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / item["path"], target)
        if target.stat().st_size != item["bytes"] or digest(target) != item["sha256"]:
            raise RuntimeError("Research companion copy does not match admitted bytes")
    (site / "explore").mkdir()
    (site / "explore/index.html").write_bytes(ALIAS)
    after = snapshot(site)
    if any(after.get(name) != value for name, value in before.items()):
        raise RuntimeError("Research companion assembly changed an existing Pages file")
    expected = set(before) | {item["path"] for item in copies} | {"explore/index.html"}
    if set(after) != expected:
        raise RuntimeError("Research companion assembly produced an unexpected file roster")
    return {"new_files": len(after) - len(before), "preserved_files": len(before), "status": "draft-unpromoted"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", type=Path)
    parser.add_argument("--require-reviewed", action="store_true")
    parser.add_argument("--candidate-digest", action="store_true")
    args = parser.parse_args()
    if args.candidate_digest:
        check_pages_admission()
        print(candidate_digest())
        return
    if args.site is None:
        parser.error("--site is required for assembly")
    print(json.dumps(assemble(args.site, require_reviewed=args.require_reviewed), sort_keys=True))


if __name__ == "__main__":
    main()
