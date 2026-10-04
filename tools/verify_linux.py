"""Linux development gates; never promote or overwrite historical release artifacts."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "RUNTIME-linux.json"
# An order of magnitude tighter than the benchmark's frozen algebra tolerance.
# Discrete decisions, counts, keys, string identities and array lengths stay exact.
RTOL = ATOL = 1e-12


def equivalent(expected: Any, observed: Any, path: str = "root") -> None:
    """Compare scientific values, not serialized bytes; reject NaN and schema drift."""
    if type(expected) is not type(observed):
        raise RuntimeError(f"Scientific type drift at {path}")
    if isinstance(expected, dict):
        if expected.keys() != observed.keys():
            raise RuntimeError(f"Scientific key drift at {path}")
        for key in expected:
            equivalent(expected[key], observed[key], f"{path}/{key}")
    elif isinstance(expected, list):
        if len(expected) != len(observed):
            raise RuntimeError(f"Scientific length drift at {path}")
        for index, (left, right) in enumerate(zip(expected, observed, strict=True)):
            equivalent(left, right, f"{path}/{index}")
    elif isinstance(expected, float):
        if not (math.isfinite(expected) and math.isfinite(observed)
                and math.isclose(expected, observed, rel_tol=RTOL, abs_tol=ATOL)):
            raise RuntimeError(f"Scientific numeric drift at {path}: {expected!r} -> {observed!r}")
    elif expected != observed:
        raise RuntimeError(f"Scientific discrete drift at {path}: {expected!r} -> {observed!r}")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_digest(path: Path, expected: str) -> None:
    if not path.is_file() or digest(path) != expected:
        raise RuntimeError(f"Linux runtime byte identity mismatch: {path.name}")


def verify_linux_identity(runtime: dict[str, Any]) -> None:
    distribution = runtime["reference_distribution"]
    os_release = platform.freedesktop_os_release()
    observed = (platform.system(), platform.machine(), os_release["ID"],
                os_release["VERSION_ID"], list(platform.libc_ver()))
    expected = (distribution["system"], distribution["machine"],
                distribution["distribution_id"], distribution["distribution_version"],
                distribution["libc"])
    if observed != expected:
        raise RuntimeError(f"Linux platform drift: expected {expected}, observed {observed}")
    require_digest(Path(sys.executable).resolve(), distribution["executable_sha256"])
    require_digest(Path(sys.base_prefix) / "lib/libpython3.12.so.1.0",
                   distribution["libpython_sha256"])
    import matplotlib
    import numpy

    site = Path(numpy.__file__).resolve().parent.parent
    for library in runtime["numeric_kernel"]["libraries"]:
        paths = list((site / library["library_directory"]).glob(library["library_glob"]))
        if len(paths) != 1:
            raise RuntimeError("Linux numerical library inventory drift")
        require_digest(paths[0], library["sha256"])
    fonts = runtime["pdf_renderer"]["font_sources"]
    for font in fonts["files"]:
        require_digest(Path(matplotlib.get_data_path()) / "fonts/ttf" / font["file"], font["sha256"])
    renderer = runtime["pdf_renderer"]
    executable = (ROOT / "tmp/linux-browsers" / f"chromium_headless_shell-{renderer['revision']}"
                  / "chrome-headless-shell-linux64/chrome-headless-shell")
    require_digest(executable, renderer["headless_executable_sha256"])
    # The source platform contract is a frozen historical input, never a migration output.
    require_digest(ROOT / "RUNTIME.json",
                   "f3fa00ed692fc6738b47f6c8a44e9c5ac062d269ac452cfbcf90c4ef8ff39485")


def configure() -> tuple[Any, dict[str, str]]:
    from tools import verify

    verify.RUNTIME_PATH = PROFILE
    environment = verify.configure_environment()
    git_bin = ROOT / "tmp/linux-bootstrap/git/usr/bin"
    environment["PATH"] = str(git_bin) + os.pathsep + environment.get("PATH", "")
    environment["GIT_EXEC_PATH"] = str(ROOT / "tmp/linux-bootstrap/git/usr/lib/git-core")
    environment["PLAYWRIGHT_BROWSERS_PATH"] = str(ROOT / "tmp/linux-browsers")
    for key, relative in (("XDG_CACHE_HOME", "tmp/linux-cache"), ("PIP_CACHE_DIR", "tmp/pip-cache")):
        verify.ensure_safe_directory(ROOT / relative)
        environment[key] = str(ROOT / relative)
    os.environ.update(environment)
    return verify, environment


def check_scientific_files(original: Path, generated: Path) -> None:
    for path in sorted((original / "data").rglob("*")):
        if not path.is_file():
            continue
        other = generated / path.relative_to(original)
        if path.suffix == ".json":
            equivalent(json.loads(path.read_text()), json.loads(other.read_text()), str(path.name))
        elif path.suffix == ".csv":
            def rows(source: Path) -> list[list[Any]]:
                parsed = []
                for row in csv.reader(source.read_text().splitlines()):
                    values: list[Any] = []
                    for value in row:
                        try:
                            # Preserve integral counters and class IDs exactly.
                            numeric = int(value) if value.lstrip("-").isdigit() else float(value)
                            values.append(numeric)
                        except ValueError:
                            values.append(value)
                    parsed.append(values)
                return parsed
            equivalent(rows(path), rows(other), path.name)
        elif path.read_bytes() != other.read_bytes():
            raise RuntimeError(f"Unclassified scientific byte drift: {path.name}")


def replay(environment: dict[str, str], workers: int) -> dict[str, Any]:
    from tools import check_repository

    destination = Path(tempfile.mkdtemp(prefix="linux-replay-", dir=ROOT / "tmp"))
    paths = check_repository.public_files()
    before = {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}
    for path in paths:
        target = destination / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    outputs = [name for name in before if name.startswith(("data/", "figures/"))]
    atlas = "resources/dark-medium-response-atlas/v0.1.0/"
    outputs += [atlas + name for name in (
        "dark-medium-response-atlas-v0.1.0.html", "dark-medium-response-atlas-v0.1.0.pdf",
        "html-accessibility.json", "pdf-inspection.json",
    )]
    passes = []
    for _ in range(2):
        for script, arguments in (
            ("scripts/make_figures.py", ["--workers", str(workers)]),
            ("tools/build_dark_medium_response_atlas_documents.py", ["--no-identity"]),
        ):
            subprocess.run([sys.executable, "-I", "-B", str(destination / script), *arguments],
                           cwd=destination, env=environment, check=True)
        passes.append({name: digest(destination / name) for name in outputs})
    if passes[0] != passes[1]:
        raise RuntimeError("Consecutive Linux scientific/Atlas replays are not byte-identical")
    check_scientific_files(ROOT, destination)
    from pypdf import PdfReader

    pdf_name = atlas + "dark-medium-response-atlas-v0.1.0.pdf"
    def text_pages(path: Path) -> list[str]:
        return [" ".join((page.extract_text() or "").split()) for page in PdfReader(path).pages]
    historical_pages = text_pages(ROOT / pdf_name)
    linux_pages = text_pages(destination / pdf_name)
    html_name = atlas + "dark-medium-response-atlas-v0.1.0.html"
    if before[html_name] != passes[0][html_name]:
        raise RuntimeError("Linux Atlas HTML differs from the historical content and font bytes")
    if any(digest(ROOT / name) != expected for name, expected in before.items()):
        raise RuntimeError("Linux replay changed the source checkout")
    return {
        "classification": "linux_repeatable_science_equivalent_unpromoted",
        "runtime_sha256": digest(PROFILE),
        "linux_output_sha256": passes[0],
        "different_from_windows_bytes": [name for name in outputs if passes[0][name] != before[name]],
        "scientific_tolerance": {"relative": RTOL, "absolute": ATOL, "discrete": "exact"},
        "core_documents": "immutable historical bytes; current source is an unpromoted draft",
        "atlas_documents": "two checked Linux builds; no release identity generated",
        "atlas_html": "exact historical bytes, including embedded fonts",
        "atlas_pdf_comparison": {
            "historical_pages": len(historical_pages), "linux_pages": len(linux_pages),
            "same_normalized_page_text": historical_pages == linux_pages,
            "same_normalized_document_text": " ".join(historical_pages) == " ".join(linux_pages),
            "scope": "PDF differences remain unpromoted; independent PDF inspection must pass",
        },
    }


def main() -> None:
    if not sys.flags.isolated or not sys.dont_write_bytecode:
        raise RuntimeError("Use -I -B before tools/verify_linux.py")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--runtime-only", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.workers < 1:
        raise ValueError("workers must be positive")
    sys.path.insert(0, str(ROOT))
    verify, environment = configure()
    verify_linux_identity(json.loads(PROFILE.read_text()))
    verify.verify_runtime(environment)
    if args.runtime_only:
        print("Linux runtime identity passed (no scientific or release claim).")
        return
    commands = (
        ["tools/check_repository.py"],
        ["-m", "pytest", "-q", "-o", "addopts=", "--strict-config", "--strict-markers",
         "-p", "no:cacheprovider", "--tb=short",
         "--deselect=tests/test_dark_medium_response_benchmark.py::"
         "test_retained_evaluation_reproduces_with_frozen_sources", "tests"],
        ["-m", "ruff", "check", "."], ["-m", "mypy", "src"],
        ["-c", "from cffconvert.cli.cli import cli; cli()", "--validate"],
        ["tools/check_repository_links.py"], ["tools/check_external_links.py"],
        ["tools/check_pages_admission.py"], ["tools/inspect_pdf.py"],
        ["tools/release_integrity.py", "verify-manifest"],
    )
    for arguments in commands:
        # Isolated controllers require -I; repository imports in other scripts need
        # the controller's established child environment (same as Windows verifier).
        command = (verify.isolated_python(*arguments) if arguments[0] == "tools/release_integrity.py"
                   else verify.controlled_python(*arguments))
        verify.run(command, environment=environment)
    verify.run(["git", "diff", "--check"], environment=environment)
    from tools import release_integrity

    # Reuse the complete tracked-inventory/archive checks with the Linux tool
    # identity, without invoking any tag, release, fetch, or publication operation.
    release_integrity.RUNTIME_PATH = PROFILE
    release_integrity.assert_clean_worktree()
    release_integrity.verify_git_archive_inventory()
    if args.all:
        result = replay(environment, args.workers)
        (ROOT / "tmp/linux-verification.json").write_text(json.dumps(result, indent=2) + "\n")
        print("Linux replay passed; platform byte differences recorded in tmp/linux-verification.json.")
    print("Linux development gates passed. Historical Windows release replay was not exercised.")


if __name__ == "__main__":
    main()
