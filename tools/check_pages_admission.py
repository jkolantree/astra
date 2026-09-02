"""Validate and copy the exact ASTRA Pages shell admitted by its manifest."""

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
DOCS = ROOT / "docs"
MANIFEST = ROOT / "evidence" / "pages_admission_v1.json"
SCHEMA = ROOT / "schemas" / "pages-admission-v1.schema.json"

sys.path.insert(0, str(ROOT))
from tools.build_pages_admission import (  # noqa: E402
    BASE_COMMIT,
    BASE_TREE,
    RELEASE_ROUTES,
    docs_entries,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise RuntimeError(
            f"{label} keys mismatch: missing={sorted(expected - set(value))}; "
            f"unexpected={sorted(set(value) - expected)}"
        )


def _require_basename(value: object, label: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", value) is None:
        raise RuntimeError(f"{label} is not a portable basename")
    return value


def _require_route(value: object, label: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"/[a-z0-9./-]+/", value) is None:
        raise RuntimeError(f"{label} is not a safe absolute route")
    return value


def validate_manifest_shape(value: dict[str, Any]) -> None:
    """Validate the small admission contract without a runtime-only dependency.

    Pages needs this checker before it can assemble the release artifact.  The
    repository suite separately validates the JSON Schema; this redundant,
    deliberately narrow validator keeps the deployment workflow bootstrap
    limited to CPython's standard library.
    """

    _require_exact_keys(
        value,
        {"schema", "manifest_version", "base", "head_shell", "release_routes", "policy"},
        "Pages admission manifest",
    )
    if value["schema"] != "https://jkolantree.github.io/astra/schemas/pages-admission-v1.schema.json":
        raise RuntimeError("Pages admission manifest schema identity drifted")
    if value["manifest_version"] != "1.0.0":
        raise RuntimeError("Pages admission manifest version drifted")

    base = value["base"]
    if not isinstance(base, dict):
        raise RuntimeError("Pages admission base must be an object")
    _require_exact_keys(base, {"commit", "tree", "relationship"}, "Pages admission base")
    for field in ("commit", "tree"):
        if not isinstance(base[field], str) or re.fullmatch(r"[0-9a-f]{40}", base[field]) is None:
            raise RuntimeError(f"Pages admission base {field} is invalid")
    if base["relationship"] != "fresh_current_main_pages_admission_base":
        raise RuntimeError("Pages admission base relationship drifted")

    shell = value["head_shell"]
    if not isinstance(shell, dict):
        raise RuntimeError("Pages admission shell must be an object")
    _require_exact_keys(shell, {"root", "files"}, "Pages admission shell")
    if shell["root"] != "docs" or not isinstance(shell["files"], list) or not shell["files"]:
        raise RuntimeError("Pages admission shell is incomplete")
    paths: list[str] = []
    for index, item in enumerate(shell["files"]):
        if not isinstance(item, dict):
            raise RuntimeError(f"Pages shell file {index} is not an object")
        _require_exact_keys(item, {"path", "bytes", "sha256"}, f"Pages shell file {index}")
        path = item["path"]
        if (
            not isinstance(path, str)
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", path) is None
            or "/../" in f"/{path}/"
        ):
            raise RuntimeError(f"Pages shell file {index} has an unsafe path")
        if not isinstance(item["bytes"], int) or item["bytes"] < 1:
            raise RuntimeError(f"Pages shell file {index} has invalid byte count")
        if not isinstance(item["sha256"], str) or re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is None:
            raise RuntimeError(f"Pages shell file {index} has invalid SHA-256")
        paths.append(path)
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise RuntimeError("Pages shell paths must be unique and sorted")

    routes = value["release_routes"]
    if not isinstance(routes, list) or len(routes) < 4:
        raise RuntimeError("Pages admission must name every release-derived route")
    lines: set[str] = set()
    for index, route in enumerate(routes):
        if not isinstance(route, dict):
            raise RuntimeError(f"Pages route {index} is not an object")
        _require_exact_keys(
            route,
            {"line", "tag", "versioned_route", "latest_route", "kind", "asset_allowlist"},
            f"Pages route {index}",
        )
        line = route["line"]
        if not isinstance(line, str) or re.fullmatch(r"[a-z0-9-]+", line) is None:
            raise RuntimeError(f"Pages route {index} has an invalid line")
        if line in lines:
            raise RuntimeError(f"Pages route line is duplicated: {line}")
        lines.add(line)
        if not isinstance(route["tag"], str) or not route["tag"]:
            raise RuntimeError(f"Pages route {index} has an invalid tag")
        _require_route(route["versioned_route"], f"Pages route {index} versioned route")
        if route["latest_route"] is not None:
            _require_route(route["latest_route"], f"Pages route {index} latest route")
        if route["kind"] not in {"core-release", "supplemental-release"}:
            raise RuntimeError(f"Pages route {index} has an invalid kind")
        assets = route["asset_allowlist"]
        if not isinstance(assets, list) or not assets:
            raise RuntimeError(f"Pages route {index} has no asset allowlist")
        names = [_require_basename(name, f"Pages route {index} asset") for name in assets]
        if len(names) != len(set(names)):
            raise RuntimeError(f"Pages route {index} has duplicate assets")

    policy = value["policy"]
    if not isinstance(policy, dict):
        raise RuntimeError("Pages admission policy must be an object")
    expected_policy = {
        "copy_exact_head_shell_only": True,
        "release_bytes_required_for_publication_routes": True,
        "reject_unadmitted_docs": True,
        "reject_draft_and_candidate_content": True,
    }
    _require_exact_keys(policy, set(expected_policy), "Pages admission policy")
    if policy != expected_policy:
        raise RuntimeError("Pages admission policy drifted")


def load_manifest(path: Path = MANIFEST) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("Pages admission manifest is not an object")
    validate_manifest_shape(value)
    return value


def check_pages_admission(path: Path = MANIFEST) -> dict[str, Any]:
    record = load_manifest(path)
    if record["base"] != {
        "commit": BASE_COMMIT,
        "tree": BASE_TREE,
        "relationship": "fresh_current_main_pages_admission_base",
    }:
        raise RuntimeError("Pages admission base identity drifted")
    if record["release_routes"] != RELEASE_ROUTES:
        raise RuntimeError("Pages admission release-route contract drifted")
    expected = record["head_shell"]["files"]
    observed = docs_entries(DOCS)
    if observed != expected:
        expected_paths = {item["path"] for item in expected}
        observed_paths = {item["path"] for item in observed}
        raise RuntimeError(
            "Pages shell admission mismatch: "
            f"missing={sorted(expected_paths - observed_paths)}; "
            f"unexpected={sorted(observed_paths - expected_paths)}"
        )
    for item in expected:
        source = DOCS / str(item["path"])
        if source.stat().st_size != item["bytes"] or sha256(source) != item["sha256"]:
            raise RuntimeError(f"Pages shell byte mismatch: {item['path']}")
    return record


def copy_admitted_shell(destination: Path, manifest: Path = MANIFEST) -> None:
    record = check_pages_admission(manifest)
    destination = destination.resolve()
    if destination in {ROOT.resolve(), DOCS.resolve()}:
        raise RuntimeError("Pages destination must not overwrite a source directory")
    junction_check = getattr(destination, "is_junction", None)
    if destination.is_symlink() or bool(junction_check and junction_check()):
        raise RuntimeError("Pages destination must not be a link or junction")
    destination.mkdir(parents=True, exist_ok=True)
    for item in record["head_shell"]["files"]:
        relative = Path(str(item["path"]))
        source = DOCS / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if target.stat().st_size != item["bytes"] or sha256(target) != item["sha256"]:
            raise RuntimeError(f"Pages shell copy mismatch: {relative.as_posix()}")
    observed = {
        path.relative_to(destination).as_posix()
        for path in destination.rglob("*")
        if path.is_file()
    }
    expected = {str(item["path"]) for item in record["head_shell"]["files"]}
    if observed != expected:
        raise RuntimeError("Pages shell copy produced an unexpected roster")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--copy-to", type=Path)
    args = parser.parse_args()
    check_pages_admission()
    if args.copy_to is not None:
        copy_admitted_shell(args.copy_to)
    print("Pages admission manifest passed.")


if __name__ == "__main__":
    main()
