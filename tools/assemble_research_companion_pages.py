"""Assemble the explicitly admitted research companion without changing release routes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_pages_admission import (  # noqa: E402
    COMPANION_PATHS,
    COMPANION_ROOT,
    CURRENT_SHELL_PATHS,
    SHELL_PATHS,
)
from tools.check_pages_admission import check_pages_admission  # noqa: E402

REVIEW = ROOT / "evidence/research_companion_pages_review_v1.json"
REVIEW_SCHEMA = "https://jkolantree.github.io/astra/schemas/research-companion-pages-review-v1.schema.json"
COVERAGE_CHECKS = (
    "desktop_and_mobile_layout",
    "keyboard_and_focus",
    "reduced_motion",
    "media_playback",
    "console_and_network",
    "assistive_technology",
)
COVERAGE_STATUSES = {"passed", "failed", "not-tested"}
VISUAL_SUFFIXES = {".html", ".css", ".svg", ".png", ".gif", ".mp4", ".pdf", ".docx"}
VISUAL_SOURCE_PATHS = tuple(
    (f"docs/{name}", name) for name in SHELL_PATHS
    if Path(name).suffix in VISUAL_SUFFIXES
) + tuple(
    (f"{COMPANION_ROOT}/{name}", f"{COMPANION_ROOT}/{name}") for name in COMPANION_PATHS
    if Path(name).suffix in VISUAL_SUFFIXES
)
CANDIDATE_INPUTS = (
    ".github/workflows/pages.yml",
    "evidence/RESEARCH_COMPANION_PAGES_REVIEW.md",
    "evidence/pages_admission_v2.json",
    "schemas/README.md",
    "schemas/pages-admission-v2.schema.json",
    "schemas/research-companion-pages-review-v1.schema.json",
    "tools/assemble_research_companion_pages.py",
    "tools/build_pages_admission.py",
    "tools/build_explorer_gateway.py",
    "tools/check_pages_admission.py",
    "tools/check_pages_links.py",
    "tools/link_audit_common.py",
)
CURRENT_REVIEW = ROOT / "evidence/pages_publication_review_current.json"
CURRENT_REVIEW_KIND = "owner_authorized_current_pages_agent_review_v1"
CURRENT_CANDIDATE_INPUTS = (
    ".github/workflows/pages.yml",
    "evidence/pages_admission_current.json",
    "schemas/pages-admission-current-v1.schema.json",
    "tools/assemble_pages.py",
    "tools/assemble_research_companion_pages.py",
    "tools/build_pages_admission.py",
    "tools/check_pages_admission.py",
    "tools/check_pages_links.py",
    "tools/dark_medium_response_atlas_release.py",
    "tools/link_audit_common.py",
)
CURRENT_VISUAL_SOURCE_PATHS = tuple(
    (f"docs/{name}", name) for name in CURRENT_SHELL_PATHS
    if Path(name).suffix in VISUAL_SUFFIXES
) + tuple(
    (f"{COMPANION_ROOT}/{name}", f"{COMPANION_ROOT}/{name}")
    for name in COMPANION_PATHS if Path(name).suffix in VISUAL_SUFFIXES
)

ALIAS = """<!doctype html>
<html lang="en-US">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="0; url=../">
  <title>Research companion · Draft | ASTRA</title>
</head>
<body><main>
  <h1>ASTRA explorer</h1>
  <p>Unpromoted research draft. Stable SPPT/ASTRA v1.0.7 retains its separate authority.</p>
  <p><a href="../">Open the explorer</a></p>
</main></body>
</html>
""".encode()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def candidate_digest(root: Path = ROOT, *, current: bool = False) -> str:
    """Bind review to admitted source bytes and the code that assembles them.

    The admission file covers all shell, companion and support bytes. The
    approval record and repository-wide manifest are excluded to avoid cycles.
    """
    inputs = CURRENT_CANDIDATE_INPUTS if current else CANDIDATE_INPUTS
    values = [{"path": name, "sha256": digest(root / name)} for name in inputs]
    return hashlib.sha256(json.dumps(values, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def reject_links(path: Path) -> None:
    for part in (path, *path.parents):
        is_junction = getattr(part, "is_junction", None)
        if part.is_symlink() or bool(is_junction and is_junction()):
            raise RuntimeError("Pages inputs and destination must not use links or junctions")


def visual_content_digest(root: Path = ROOT, *, current: bool = False) -> str:
    """Bind visual acceptance to the unchanged rendered pages and media.

    Operational Markdown and gate code are excluded from this narrower digest;
    they remain covered by admission and the final-publication candidate digest.
    This allows a truthful owner review to survive a gate-only refinement.
    """
    paths = CURRENT_VISUAL_SOURCE_PATHS if current else VISUAL_SOURCE_PATHS
    values = [{"path": target, "sha256": digest(root / source)} for source, target in paths]
    values.append({"path": "explore/index.html", "sha256": hashlib.sha256(ALIAS).hexdigest()})
    values.sort(key=lambda item: item["path"])
    return hashlib.sha256(json.dumps(values, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _review_object(value: object, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise RuntimeError(f"Research companion {label} is malformed")
    return value


def _review_text(value: object, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"Research companion {label} must be stated")


def require_visual_review(path: Path = REVIEW, *, root: Path = ROOT) -> dict[str, str]:
    reject_links(path)
    record = _review_object(
        json.loads(path.read_text(encoding="utf-8")),
        {"schema", "candidate_sha256", "visual_review", "coverage", "publication_approval"},
        "publication review record",
    )
    if record["schema"] != REVIEW_SCHEMA:
        raise RuntimeError("Research companion review schema identity drifted")
    if record["candidate_sha256"] != candidate_digest(root):
        raise RuntimeError("Research companion publication approval is stale for the current candidate")
    visual = _review_object(
        record["visual_review"],
        {"status", "basis", "surface", "scope", "content_sha256", "preview_candidate_sha256"},
        "manual visual review",
    )
    if visual["status"] != "accepted":
        raise RuntimeError("Research companion publication blocked: manual visual acceptance is pending")
    for field in ("basis", "surface", "scope"):
        _review_text(visual[field], f"visual review {field}")
    preview_digest = visual["preview_candidate_sha256"]
    if not isinstance(preview_digest, str) or re.fullmatch(r"[0-9a-f]{64}", preview_digest) is None:
        raise RuntimeError("Research companion reviewed preview identity is malformed")
    if visual["content_sha256"] != visual_content_digest(root):
        raise RuntimeError("Research companion visual acceptance is stale for the rendered content")
    coverage = _review_object(record["coverage"], set(COVERAGE_CHECKS), "specialist coverage")
    if any(not isinstance(value, str) or value not in COVERAGE_STATUSES for value in coverage.values()):
        raise RuntimeError("Research companion coverage must use passed, failed or not-tested")
    if "failed" in coverage.values():
        raise RuntimeError("Research companion publication blocked: a declared review check failed")
    approval = _review_object(record["publication_approval"], {"status", "basis"}, "final publication approval")
    if approval["status"] != "approved":
        raise RuntimeError("Research companion publication blocked: final publication approval is pending")
    _review_text(approval["basis"], "final publication approval basis")
    # Unperformed specialist checks remain visible and do not become false
    # passes. No private screenshot or other personal evidence is required.
    return coverage


def require_current_review(
    path: Path = CURRENT_REVIEW, *, root: Path = ROOT,
) -> dict[str, str]:
    """Keep owner publication authority separate from agent visual observations."""
    reject_links(path)
    record = _review_object(
        json.loads(path.read_text(encoding="utf-8")),
        {"kind", "candidate_sha256", "visual_review", "coverage", "publication_authorization"},
        "current publication review",
    )
    if record["kind"] != CURRENT_REVIEW_KIND:
        raise RuntimeError("Current Pages review identity drifted")
    if record["candidate_sha256"] != candidate_digest(root, current=True):
        raise RuntimeError("Current Pages publication review is stale for the current candidate")
    visual = _review_object(
        record["visual_review"],
        {"status", "reviewer", "owner_visual_review_claimed", "basis", "surface", "scope", "content_sha256"},
        "current agent visual review",
    )
    if visual["status"] != "accepted":
        raise RuntimeError("Current Pages agent visual review is pending")
    if visual["reviewer"] != "Codex agent" or visual["owner_visual_review_claimed"] is not False:
        raise RuntimeError("Current Pages review must not claim owner visual acceptance")
    for field in ("basis", "surface", "scope"):
        _review_text(visual[field], f"current visual review {field}")
    if visual["content_sha256"] != visual_content_digest(root, current=True):
        raise RuntimeError("Current Pages review is stale for the rendered content")
    coverage = _review_object(record["coverage"], set(COVERAGE_CHECKS), "current review coverage")
    if any(not isinstance(value, str) or value not in COVERAGE_STATUSES for value in coverage.values()):
        raise RuntimeError("Current Pages review coverage is invalid")
    if "failed" in coverage.values():
        raise RuntimeError("Current Pages publication blocked: a review check failed")
    authorization = _review_object(
        record["publication_authorization"],
        {"status", "actor", "basis", "scope", "scientific_release_authorized"},
        "current publication authorization",
    )
    if authorization["status"] != "authorized" or authorization["actor"] != "repository owner":
        raise RuntimeError("Current Pages owner publication authorization is pending")
    _review_text(authorization["basis"], "current owner publication basis")
    if authorization["scope"] != "current GitHub code and existing ASTRA website":
        raise RuntimeError("Current Pages publication scope drifted")
    if authorization["scientific_release_authorized"] is not False:
        raise RuntimeError("Current Pages authorization does not create a scientific release")
    return coverage


def snapshot(site: Path) -> dict[str, str]:
    entries = {}
    for path in sorted(site.rglob("*")):
        reject_links(path)
        if path.is_file():
            entries[path.relative_to(site).as_posix()] = digest(path)
    return entries


def assemble(
    site: Path, *, require_reviewed: bool = False, current: bool = False,
) -> dict[str, Any]:
    record = check_pages_admission(current=current)
    review = require_current_review if current else require_visual_review
    coverage = review() if require_reviewed else None
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
    result: dict[str, Any] = {"new_files": len(after) - len(before), "preserved_files": len(before), "status": "draft-unpromoted"}
    if coverage is not None:
        result["review_coverage"] = coverage
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", type=Path)
    parser.add_argument("--current", action="store_true")
    parser.add_argument("--require-reviewed", action="store_true")
    parser.add_argument("--candidate-digest", action="store_true")
    parser.add_argument("--visual-content-digest", action="store_true")
    args = parser.parse_args()
    if args.candidate_digest or args.visual_content_digest:
        check_pages_admission(current=args.current)
        print(visual_content_digest(current=args.current) if args.visual_content_digest else candidate_digest(current=args.current))
        return
    if args.site is None:
        parser.error("--site is required for assembly")
    print(json.dumps(assemble(args.site, require_reviewed=args.require_reviewed, current=args.current), sort_keys=True))


if __name__ == "__main__":
    main()
