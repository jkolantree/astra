"""Canonical fail-closed verification for the current SPPT/ASTRA release spec."""
from __future__ import annotations

if __name__ == "__main__":
    import sys as _bootstrap_sys

    if not _bootstrap_sys.flags.isolated or not _bootstrap_sys.dont_write_bytecode:
        raise SystemExit("Unsafe startup: run Python with -I -B before tools/verify.py")

import argparse
import ctypes
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

ROOT = Path(__file__).resolve().parents[1]
TEMP_ROOT = ROOT / "tmp" / "verification"
RUNTIME_PATH = ROOT / "RUNTIME.json"
LOCK_PATH = ROOT / "requirements-lock.txt"
RELEASE_SPEC = json.loads((ROOT / "RELEASE_SPEC.json").read_text(encoding="utf-8"))
VERSION = str(RELEASE_SPEC["version"])

DOCUMENT_OUTPUTS = (
    ROOT / "manuscript" / f"SPPT_ASTRA_preprint_v{VERSION}.html",
    ROOT / "manuscript" / f"SPPT_ASTRA_preprint_v{VERSION}.pdf",
    ROOT / "manuscript" / f"SPPT_ASTRA_technical_supplement_v{VERSION}.html",
    ROOT / "manuscript" / f"SPPT_ASTRA_technical_supplement_v{VERSION}.pdf",
    ROOT / "manuscript" / "document_semantic_identity.json",
    ROOT / "manuscript" / "pdf_inspection.json",
)
INHERITED_CONTROL_VARIABLES = {
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_CEILING_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_CONFIG_COUNT",
    "GIT_CONFIG_GLOBAL",
    "GIT_CONFIG_PARAMETERS",
    "GIT_CONFIG_SYSTEM",
    "GIT_DIR",
    "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    "GIT_INDEX_FILE",
    "GIT_NAMESPACE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_QUARANTINE_PATH",
    "GIT_REPLACE_REF_BASE",
    "GIT_WORK_TREE",
    "PYTEST_ADDOPTS",
    "PYTEST_PLUGINS",
    "PYTHONHOME",
    "PYTHONPATH",
    "PLAYWRIGHT_BROWSERS_PATH",
    "PYPANDOC_PANDOC",
}


def is_link_or_junction(path: Path) -> bool:
    junction_check = getattr(path, "is_junction", None)
    return path.is_symlink() or bool(junction_check and junction_check())


def assert_safe_repository_descendant(path: Path) -> None:
    try:
        relative = path.relative_to(ROOT)
    except ValueError as exc:
        raise RuntimeError(f"Output path is outside the repository: {path}") from exc
    expected = ROOT.resolve().joinpath(*relative.parts)
    current = ROOT
    for part in relative.parts:
        current /= part
        if is_link_or_junction(current):
            raise RuntimeError(f"Unsafe symbolic link or junction in output path: {current}")
        if current != path and current.exists() and not current.is_dir():
            raise RuntimeError(f"Non-directory component in output path: {current}")
    if path.resolve() != expected:
        raise RuntimeError(f"Output path resolves outside its expected location: {path}")


def ensure_safe_directory(path: Path) -> None:
    assert_safe_repository_descendant(path)
    if path.exists() and not path.is_dir():
        raise RuntimeError(f"Expected output directory but found a non-directory: {path}")
    path.mkdir(parents=True, exist_ok=True)
    assert_safe_repository_descendant(path)


def is_inherited_controller_variable(name: str) -> bool:
    return (
        name in INHERITED_CONTROL_VARIABLES
        or name.startswith("GIT_")
        or name.startswith("PYTEST_")
        or name.startswith("PYTHON")
    )


def require_isolated_mode() -> None:
    if not sys.flags.isolated or not sys.dont_write_bytecode:
        raise RuntimeError("Canonical verification requires Python isolated mode: use -I -B")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def controlled_python(*arguments: str) -> list[str]:
    """Return a safe-path child command that honors the sanitized hash seed."""
    return [sys.executable, "-P", "-s", "-B", *arguments]


def isolated_python(*arguments: str) -> list[str]:
    """Return an isolated child command for self-protecting controllers."""
    return [sys.executable, "-I", "-B", *arguments]


def configure_environment() -> dict[str, str]:
    runtime = json.loads(RUNTIME_PATH.read_text(encoding="utf-8"))
    numeric_kernel = runtime["numeric_kernel"]
    core_type = str(numeric_kernel["core_type"])
    threads = str(numeric_kernel["threads"])
    disabled_numpy_features = ",".join(numeric_kernel["numpy_disabled_cpu_features"])
    for path in (ROOT / "tmp", TEMP_ROOT, ROOT / "tmp" / "pycache", ROOT / "tmp" / "matplotlib"):
        ensure_safe_directory(path)
    tempfile.tempdir = str(TEMP_ROOT)
    environment = os.environ.copy()
    for name in tuple(environment):
        if is_inherited_controller_variable(name):
            environment.pop(name)
    environment.update(
        {
            "PYTHONHASHSEED": "0",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPYCACHEPREFIX": str(ROOT / "tmp" / "pycache"),
            "PYTHONNOUSERSITE": "1",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_KEY_0": "safe.directory",
            "GIT_CONFIG_VALUE_0": str(ROOT.resolve()),
            "GIT_NO_REPLACE_OBJECTS": "1",
            "TZ": "UTC",
            "SOURCE_DATE_EPOCH": str(RELEASE_SPEC["build_epoch_unix"]),
            "OPENBLAS_CORETYPE": core_type,
            "OMP_NUM_THREADS": threads,
            "OPENBLAS_NUM_THREADS": threads,
            "MKL_NUM_THREADS": threads,
            "NUMEXPR_NUM_THREADS": threads,
            "NPY_DISABLE_CPU_FEATURES": disabled_numpy_features,
            "MPLBACKEND": "Agg",
            "MPLCONFIGDIR": str(ROOT / "tmp" / "matplotlib"),
            "TEMP": str(TEMP_ROOT),
            "TMP": str(TEMP_ROOT),
            "TMPDIR": str(TEMP_ROOT),
        }
    )
    for name in tuple(os.environ):
        if is_inherited_controller_variable(name):
            os.environ.pop(name, None)
    os.environ.update(environment)
    return environment


def run(command: list[str], *, environment: dict[str, str]) -> None:
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, env=environment, check=True)


def locked_distributions() -> dict[str, str]:
    from packaging.utils import canonicalize_name

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


def observe_numeric_kernel(runtime: dict[str, Any]) -> dict[str, Any]:
    import numpy
    import scipy

    packages = {"numpy": numpy, "scipy": scipy}
    cpu_module = importlib.import_module("numpy._core._multiarray_umath")
    cpu_features = dict(cpu_module.__cpu_features__)
    libraries: list[dict[str, Any]] = []
    for specification in runtime["numeric_kernel"]["libraries"]:
        distribution = str(specification["distribution"])
        package = packages[distribution]
        package_file = package.__file__
        if package_file is None:
            raise RuntimeError(f"Cannot locate the {distribution} package")
        library_directory = Path(package_file).resolve().parent.parent / str(
            specification["library_directory"]
        )
        matches = sorted(library_directory.glob(str(specification["library_glob"])))
        if len(matches) != 1:
            raise RuntimeError(
                f"Expected one {distribution} OpenBLAS library, observed {len(matches)}"
            )
        library = ctypes.CDLL(str(matches[0]))
        core_function = getattr(library, str(specification["corename_symbol"]))
        core_function.restype = ctypes.c_char_p
        thread_function = getattr(library, str(specification["num_threads_symbol"]))
        thread_function.restype = ctypes.c_int
        core_bytes = core_function()
        if core_bytes is None:
            raise RuntimeError(f"{distribution} OpenBLAS returned no core name")
        configuration = package.__config__.CONFIG
        blas_configuration = configuration["Build Dependencies"]["blas"]
        libraries.append(
            {
                "distribution": distribution,
                "distribution_version": importlib.metadata.version(distribution),
                "blas_provider": blas_configuration["name"],
                "openblas_version": blas_configuration["version"],
                "core_type": core_bytes.decode("ascii"),
                "threads": int(thread_function()),
            }
        )
    return {"cpu_features": cpu_features, "libraries": libraries}


def validate_numeric_kernel_observation(
    runtime: dict[str, Any], observation: dict[str, Any]
) -> None:
    numeric_kernel = runtime["numeric_kernel"]
    missing_features = [
        feature
        for feature in numeric_kernel["required_cpu_features"]
        if not observation["cpu_features"].get(feature, False)
    ]
    if missing_features:
        raise RuntimeError(
            "The deterministic numeric kernel requires CPU features: "
            + ", ".join(missing_features)
        )
    enabled_forbidden = [
        feature
        for feature in numeric_kernel["numpy_disabled_cpu_features"]
        if observation["cpu_features"].get(feature, False)
    ]
    if enabled_forbidden:
        raise RuntimeError(
            "NumPy CPU-feature disabling failed for: " + ", ".join(enabled_forbidden)
        )
    observed_libraries = {
        item["distribution"]: item for item in observation["libraries"]
    }
    for specification in numeric_kernel["libraries"]:
        distribution = specification["distribution"]
        observed = observed_libraries.get(distribution)
        if observed is None:
            raise RuntimeError(f"Missing numeric-kernel observation for {distribution}")
        expected = {
            "distribution": distribution,
            "distribution_version": specification["distribution_version"],
            "blas_provider": "scipy-openblas",
            "openblas_version": specification["openblas_version"],
            "core_type": str(numeric_kernel["core_type"]).title(),
            "threads": numeric_kernel["threads"],
        }
        if observed != expected:
            raise RuntimeError(
                f"Numeric-kernel drift for {distribution}: expected {expected}, observed {observed}"
            )


def verify_numeric_kernel(runtime: dict[str, Any]) -> None:
    numeric_kernel = runtime["numeric_kernel"]
    expected_environment = {
        "OPENBLAS_CORETYPE": str(numeric_kernel["core_type"]),
        "OPENBLAS_NUM_THREADS": str(numeric_kernel["threads"]),
        "OMP_NUM_THREADS": str(numeric_kernel["threads"]),
        "MKL_NUM_THREADS": str(numeric_kernel["threads"]),
        "NUMEXPR_NUM_THREADS": str(numeric_kernel["threads"]),
        "NPY_DISABLE_CPU_FEATURES": ",".join(numeric_kernel["numpy_disabled_cpu_features"]),
    }
    observed_environment = {name: os.environ.get(name) for name in expected_environment}
    if observed_environment != expected_environment:
        raise RuntimeError(
            f"Numeric-kernel environment drift: expected {expected_environment}, "
            f"observed {observed_environment}"
        )
    validate_numeric_kernel_observation(runtime, observe_numeric_kernel(runtime))


def verify_runtime(environment: dict[str, str]) -> None:
    require_isolated_mode()
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

    git_process = subprocess.run(
        ["git", "version", "--build-options"],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
    git_lines = git_process.stdout.splitlines()
    git_version = git_lines[0].removeprefix("git version ") if git_lines else ""
    git_build = re.search(r"(?m)^built from commit: ([0-9a-f]{40})$", git_process.stdout)
    git_executable = shutil.which("git", path=environment.get("PATH"))
    observed_git = {
        "version": git_version,
        "build_commit": git_build.group(1) if git_build else "",
        "executable_sha256": sha256(Path(git_executable)) if git_executable else "",
    }
    expected_git = {key: runtime["git"][key] for key in observed_git}
    if observed_git != expected_git:
        raise RuntimeError(f"Git runtime drift: expected {expected_git}, observed {observed_git}")

    verify_installed_distributions()
    verify_numeric_kernel(runtime)
    run(controlled_python("-m", "pip", "check"), environment=environment)

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
    return controlled_python(
        "-c",
        "from cffconvert.cli.cli import cli; cli()",
        "--validate",
    )


def verify_focused(environment: dict[str, str]) -> None:
    verify_runtime(environment)
    run(controlled_python("tools/check_repository.py"), environment=environment)
    commands = (
        [
            *controlled_python(),
            "-m",
            "pytest",
            "-q",
            "-o",
            "addopts=",
            "--strict-config",
            "--strict-markers",
            "-p",
            "no:cacheprovider",
            "tests",
        ],
        controlled_python("-m", "ruff", "check", "."),
        controlled_python("-m", "mypy", "src"),
        cffconvert_command(),
        controlled_python("tools/inspect_pdf.py"),
    )
    for command in commands:
        run(command, environment=environment)
    run(controlled_python("tools/check_repository.py"), environment=environment)
    if (ROOT / ".git").exists():
        run(["git", "diff", "--check"], environment=environment)
        run(["git", "diff", "--cached", "--check"], environment=environment)
    manifest_command = isolated_python("tools/release_integrity.py", "verify-manifest")
    if (ROOT / ".git").exists():
        manifest_command.append("--tracked")
    run(
        manifest_command,
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
    verify_focused(environment)
    science_before = identity(scientific_outputs())
    run(
        controlled_python("scripts/make_figures.py", "--workers", str(workers)),
        environment=environment,
    )
    science_first = identity(scientific_outputs())
    if science_first != science_before:
        difference = identity_difference(science_before, science_first)
        raise RuntimeError(
            "Scientific data or figures were stale or non-deterministic: "
            + json.dumps(difference, sort_keys=True)
        )
    run(
        controlled_python("scripts/make_figures.py", "--workers", str(workers)),
        environment=environment,
    )
    science_second = identity(scientific_outputs())
    if science_second != science_first:
        difference = identity_difference(science_first, science_second)
        raise RuntimeError(
            "Consecutive scientific replays are not byte-identical: "
            + json.dumps(difference, sort_keys=True)
        )

    documents_before = identity(list(DOCUMENT_OUTPUTS))
    run(controlled_python("tools/build_documents.py"), environment=environment)
    run(controlled_python("tools/inspect_pdf.py", "--write"), environment=environment)
    documents_first = identity(list(DOCUMENT_OUTPUTS))
    if documents_first != documents_before:
        difference = identity_difference(documents_before, documents_first)
        raise RuntimeError(
            "Tracked document outputs were stale or non-deterministic: "
            + json.dumps(difference, sort_keys=True)
        )
    run(controlled_python("tools/build_documents.py"), environment=environment)
    run(controlled_python("tools/inspect_pdf.py", "--write"), environment=environment)
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
    require_isolated_mode()
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
