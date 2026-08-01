"""Canonical fail-closed verification for SPPT/ASTRA v1.0.1."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]
TEMP_ROOT = ROOT / "tmp" / "verification"
RUNTIME_PATH = ROOT / "RUNTIME.json"
LOCK_PATH = ROOT / "requirements-lock.txt"

DOCUMENT_OUTPUTS = (
    ROOT / "manuscript" / "SPPT_ASTRA_preprint_v1.0.1.html",
    ROOT / "manuscript" / "SPPT_ASTRA_preprint_v1.0.1.pdf",
    ROOT / "manuscript" / "SPPT_ASTRA_technical_supplement_v1.0.1.html",
    ROOT / "manuscript" / "SPPT_ASTRA_technical_supplement_v1.0.1.pdf",
    ROOT / "manuscript" / "document_semantic_identity.json",
    ROOT / "manuscript" / "pdf_inspection.json",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def configure_environment() -> dict[str, str]:
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(TEMP_ROOT)
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONHASHSEED": "0",
            "PYTHONDONTWRITEBYTECODE": "1",
            "TZ": "UTC",
            "SOURCE_DATE_EPOCH": "1785542400",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "MPLBACKEND": "Agg",
            "MPLCONFIGDIR": str(ROOT / "tmp" / "matplotlib"),
            "TEMP": str(TEMP_ROOT),
            "TMP": str(TEMP_ROOT),
            "TMPDIR": str(TEMP_ROOT),
        }
    )
    os.environ.update(environment)
    return environment


def run(command: list[str], *, environment: dict[str, str]) -> None:
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, env=environment, check=True)


def locked_distributions() -> dict[str, str]:
    matches = re.findall(
        r"(?m)^([A-Za-z0-9_.-]+)==([^\s\\]+)", LOCK_PATH.read_text(encoding="utf-8")
    )
    if not matches:
        raise RuntimeError("Dependency lock contains no exact requirements")
    locked: dict[str, str] = {}
    for name, version in matches:
        normalized = canonicalize_name(name)
        if normalized in locked:
            raise RuntimeError(f"Duplicate locked distribution: {normalized}")
        locked[normalized] = version
    return locked


def verify_installed_distributions() -> None:
    for name, expected in locked_distributions().items():
        try:
            observed = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError as error:
            raise RuntimeError(f"Locked dependency is missing: {name}=={expected}") from error
        if observed != expected:
            raise RuntimeError(
                f"Locked dependency drift: {name} expected {expected}, observed {observed}"
            )


def verify_runtime(environment: dict[str, str]) -> None:
    runtime = json.loads(RUNTIME_PATH.read_text(encoding="utf-8"))
    observed_python = platform.python_version()
    if observed_python != runtime["python"]:
        raise RuntimeError(
            f"Python runtime drift: expected {runtime['python']}, observed {observed_python}"
        )
    if platform.system() != "Windows" or platform.machine().lower() not in {"amd64", "x86_64"}:
        raise RuntimeError("The deterministic reference build requires Windows x86-64")
    lock_identity = runtime["dependency_lock"]
    if lock_identity != {"file": LOCK_PATH.name, "sha256": sha256(LOCK_PATH)}:
        raise RuntimeError("Dependency-lock identity drift")

    verify_installed_distributions()
    run([sys.executable, "-m", "pip", "check"], environment=environment)

    import playwright
    import pypandoc
    from playwright.sync_api import sync_playwright

    pandoc_version = str(pypandoc.get_pandoc_version())
    if pandoc_version != runtime["pandoc"]["version"]:
        raise RuntimeError(f"Pandoc runtime drift: {pandoc_version}")
    browsers_path = Path(playwright.__file__).parent / "driver" / "package" / "browsers.json"
    browser_registry = json.loads(browsers_path.read_text(encoding="utf-8"))
    chromium_record = next(
        item for item in browser_registry["browsers"] if item["name"] == "chromium"
    )
    renderer = runtime["pdf_renderer"]
    if chromium_record["revision"] != renderer["revision"]:
        raise RuntimeError("Playwright Chromium revision drift")
    if chromium_record.get("browserVersion") != renderer["version"]:
        raise RuntimeError("Playwright Chromium registry-version drift")
    with sync_playwright() as playwright_api:
        browser = playwright_api.chromium.launch(headless=True, args=["--disable-gpu"])
        observed_browser = browser.version
        browser.close()
    if observed_browser != renderer["version"]:
        raise RuntimeError(
            f"Chromium runtime drift: expected {renderer['version']}, observed {observed_browser}"
        )


def cffconvert_command() -> list[str]:
    suffix = ".exe" if os.name == "nt" else ""
    executable = Path(sys.executable).parent / f"cffconvert{suffix}"
    if not executable.is_file():
        located = shutil.which("cffconvert")
        if located is None:
            raise RuntimeError("cffconvert executable is missing from the locked environment")
        executable = Path(located)
    return [str(executable), "--validate"]


def verify_focused(environment: dict[str, str]) -> None:
    verify_runtime(environment)
    commands = (
        [sys.executable, "-m", "pytest", "-q"],
        [sys.executable, "-m", "ruff", "check", "."],
        [sys.executable, "-m", "mypy", "src"],
        cffconvert_command(),
        [sys.executable, "tools/check_repository.py"],
        [sys.executable, "tools/inspect_pdf.py"],
    )
    for command in commands:
        run(command, environment=environment)
    if (ROOT / ".git").exists():
        run(["git", "diff", "--check"], environment=environment)
        run(["git", "diff", "--cached", "--check"], environment=environment)
    if (ROOT / "MANIFEST.sha256").is_file():
        run(
            [sys.executable, "tools/release_integrity.py", "verify-manifest"],
            environment=environment,
        )


def identity(paths: tuple[Path, ...] | list[Path]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for path in sorted(paths):
        if not path.is_file():
            raise RuntimeError(f"Expected generated output is missing: {path.relative_to(ROOT)}")
        records[path.relative_to(ROOT).as_posix()] = {
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
    return records


def scientific_outputs() -> list[Path]:
    return sorted(
        path
        for directory in (ROOT / "data", ROOT / "figures")
        for path in directory.rglob("*")
        if path.is_file()
    )


def identity_difference(
    before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    return {
        "missing": sorted(before.keys() - after.keys()),
        "unexpected": sorted(after.keys() - before.keys()),
        "changed": {
            name: {"before": before[name], "after": after[name]}
            for name in sorted(before.keys() & after.keys())
            if before[name] != after[name]
        },
    }


def verify_full_replay(environment: dict[str, str], workers: int) -> None:
    science_before = identity(scientific_outputs())
    run(
        [sys.executable, "scripts/make_figures.py", "--workers", str(workers)],
        environment=environment,
    )
    science_after = identity(scientific_outputs())
    if science_after != science_before:
        difference = identity_difference(science_before, science_after)
        raise RuntimeError(
            "Scientific data or figures were stale or non-deterministic: "
            + json.dumps(difference, sort_keys=True)
        )

    documents_before = identity(list(DOCUMENT_OUTPUTS))
    run([sys.executable, "tools/build_documents.py"], environment=environment)
    run([sys.executable, "tools/inspect_pdf.py", "--write"], environment=environment)
    documents_first = identity(list(DOCUMENT_OUTPUTS))
    if documents_first != documents_before:
        difference = identity_difference(documents_before, documents_first)
        raise RuntimeError(
            "Tracked document outputs were stale or non-deterministic: "
            + json.dumps(difference, sort_keys=True)
        )
    run([sys.executable, "tools/build_documents.py"], environment=environment)
    run([sys.executable, "tools/inspect_pdf.py", "--write"], environment=environment)
    documents_second = identity(list(DOCUMENT_OUTPUTS))
    if documents_second != documents_first:
        difference = identity_difference(documents_first, documents_second)
        raise RuntimeError(
            "Consecutive document builds are not byte-identical: "
            + json.dumps(difference, sort_keys=True)
        )

    verify_focused(environment)
    print("Full deterministic scientific and document replay passed.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Replay every scientific and document output twice.")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.workers < 1:
        raise ValueError("workers must be positive")
    environment = configure_environment()
    if args.all:
        verify_full_replay(environment, args.workers)
    else:
        verify_focused(environment)
        print("Focused verification passed.")


if __name__ == "__main__":
    main()
