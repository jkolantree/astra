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
DRAFT_OVERLAY_RELATIVE = Path(
    "evidence/claim_source_coverage_v1.0.7_maintenance_overlay_m1.json"
)
DRAFT_SCHEMA_RELATIVE = Path("schemas/claim-source-coverage-overlay-m1.schema.json")
DRAFT_SCHEMA_URL = (
    "https://jkolantree.github.io/astra/schemas/"
    "claim-source-coverage-overlay-m1.schema.json"
)
DRAFT_SCHEMA_SHA256 = "e0012b0421d8dc3281683fc014b14123b08bc8369fda4271c4bc07f836a60e7e"
DRAFT_RELEASE_IDENTITY = {
    "tag": "v1.0.7",
    "tag_object": "b5dc469dc05e07d62d736a4c3ddc749a54e8ebbd",
    "commit": "7454b8134cf28c233fe54a11ae4b65e256844821",
    "tree": "3aaa2ec8c62d7c5c925e557cd79b3b43446aaf1d",
}
DRAFT_DOCUMENT_RELATIVES = (
    "manuscript/SPPT_ASTRA_preprint_v1.0.7.html",
    "manuscript/SPPT_ASTRA_preprint_v1.0.7.pdf",
    "manuscript/SPPT_ASTRA_technical_supplement_v1.0.7.html",
    "manuscript/SPPT_ASTRA_technical_supplement_v1.0.7.pdf",
    "manuscript/document_semantic_identity.json",
    "manuscript/pdf_inspection.json",
)
DRAFT_TAGGED_CONTRACTS = {
    "RELEASE_SPEC.json": "c45b2e713eb21b556f61bb92070af7b8181cc1feefb7967369dadb241f727097",
    "RUNTIME.json": "f3fa00ed692fc6738b47f6c8a44e9c5ac062d269ac452cfbcf90c4ef8ff39485",
    "requirements-lock.txt": "69b83ca86466525e912ea7c2d4a614d426ab44411ccc2789febc32f54c255721",
    "evidence/claim_source_coverage_v1.0.7.json": (
        "d8112ef57f44b2aa863d89bdf712e769e6635baffe13d2fa2fd6440be8a0e6f3"
    ),
    "schemas/claim-source-coverage-v1.schema.json": (
        "f21db7df57f3af75770584510162b6c1d739711b18ec6c0df1b902fe3542706e"
    ),
}
DRAFT_SOURCE_RELATIVE = "manuscript/manuscript.md"
DRAFT_SOURCE_SHA256 = "ce55ea375ae5fbc28d06a52e3a2ea6e118294fc2b5925aef99365c39a637c292"
DRAFT_CLOSURE_PATHS = [
    "MANIFEST.sha256",
    DRAFT_OVERLAY_RELATIVE.as_posix(),
]
DRAFT_MILESTONE_PATHS = [
    "AGENTS.md",
    "LICENSE_MAP.md",
    "README.md",
    "evidence/README.md",
    "manuscript/manuscript.md",
    "schemas/README.md",
    "schemas/claim-source-coverage-overlay-m1.schema.json",
    "tests/test_claim_source_coverage.py",
    "tests/test_document_contract.py",
    "tools/build_claim_source_coverage.py",
    "tools/check_repository.py",
]
ATLAS_S2_OVERLAY_RELATIVE = Path(
    "evidence/dark_medium_response_atlas_publication_successor_overlay_s2.json"
)
ATLAS_RELEASE_TAG = "dark-medium-response-atlas-v0.1.0"
ATLAS_PACKAGE = ROOT / "resources" / "dark-medium-response-atlas" / "v0.1.0"
ATLAS_DOCUMENT_OUTPUTS = (
    ATLAS_PACKAGE / "dark-medium-response-atlas-v0.1.0.html",
    ATLAS_PACKAGE / "dark-medium-response-atlas-v0.1.0.pdf",
    ATLAS_PACKAGE / "html-accessibility.json",
    ATLAS_PACKAGE / "pdf-inspection.json",
    ATLAS_PACKAGE / "publication-identity.json",
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


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def strict_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_json_keys,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise RuntimeError(f"Invalid JSON object at {path.relative_to(ROOT)}: {error}") from error
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected a JSON object at {path.relative_to(ROOT)}")
    return value


def require_exact(observed: Any, expected: Any, label: str) -> None:
    if observed != expected:
        raise RuntimeError(f"Draft verification boundary drift for {label}: {observed!r}")


def sanitized_git_environment(environment: dict[str, str]) -> dict[str, str]:
    result = environment.copy()
    for name in tuple(result):
        if name.startswith("GIT_"):
            result.pop(name)
    result.update(
        {
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_KEY_0": "safe.directory",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_VALUE_0": str(ROOT.resolve()),
            "GIT_NO_REPLACE_OBJECTS": "1",
        }
    )
    return result


def capture_git(
    arguments: list[str], *, environment: dict[str, str], binary: bool = False
) -> str | bytes:
    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=ROOT,
            env=sanitized_git_environment(environment),
            check=True,
            capture_output=True,
            text=not binary,
        )
    except subprocess.CalledProcessError as error:
        raise RuntimeError(f"Git command failed during draft verification: git {' '.join(arguments)}") from error
    output = completed.stdout
    if binary:
        if not isinstance(output, bytes):
            raise TypeError("Expected binary Git output")
        return output
    if not isinstance(output, str):
        raise TypeError("Expected text Git output")
    return output


def strict_tag_identity(tag: str, environment: dict[str, str]) -> dict[str, str]:
    object_type = str(
        capture_git(["cat-file", "-t", f"refs/tags/{tag}"], environment=environment)
    ).strip()
    if object_type != "tag":
        raise RuntimeError(f"Release tag must be annotated; observed {object_type!r}")
    tag_object = str(
        capture_git(["rev-parse", f"refs/tags/{tag}"], environment=environment)
    ).strip()
    commit = str(
        capture_git(["rev-parse", f"refs/tags/{tag}^{{commit}}"], environment=environment)
    ).strip()
    payload = str(
        capture_git(["cat-file", "-p", f"refs/tags/{tag}"], environment=environment)
    )
    header_lines = payload.partition("\n\n")[0].splitlines()
    expected_keys = ["object", "type", "tag", "tagger"]
    observed_keys = [line.split(" ", 1)[0] for line in header_lines]
    if observed_keys != expected_keys or any(" " not in line for line in header_lines):
        raise RuntimeError(f"Release tag {tag} has noncanonical annotated-tag headers")
    headers = dict(line.split(" ", 1) for line in header_lines)
    if headers.get("type") != "commit" or headers.get("object") != commit:
        raise RuntimeError(f"Release tag {tag} must directly target a commit")
    if headers.get("tag") != tag:
        raise RuntimeError(f"Annotated tag's internal name differs from {tag}")
    tree = str(
        capture_git(["rev-parse", f"{commit}^{{tree}}"], environment=environment)
    ).strip()
    return {"tag_object": tag_object, "commit": commit, "tree": tree}


def tagged_blob_bytes(commit: str, relative: str, environment: dict[str, str]) -> bytes:
    value = capture_git(
        ["cat-file", "blob", f"{commit}:{relative}"],
        environment=environment,
        binary=True,
    )
    if not isinstance(value, bytes):
        raise TypeError("Expected binary Git blob output")
    return value


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
        controlled_python("tools/check_repository_links.py"),
        controlled_python("tools/check_external_links.py"),
        controlled_python("tools/check_pages_admission.py"),
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


def validate_candidate_overlay_record(record: dict[str, Any]) -> dict[str, Any]:
    require_exact(record.get("schema"), DRAFT_SCHEMA_URL, "overlay schema identity")
    require_exact(record.get("status"), "candidate_only", "overlay status")
    require_exact(
        record.get("reference_release"),
        {
            "bibliography_path": "manuscript/references.bib",
            "bibliography_sha256": (
                "8ac6e1f29fea60da7dc583c7c122fb1394a807624f67fa052908e38574dd4b22"
            ),
            "claim_matrix_path": "CLAIM_MATRIX.json",
            "claim_matrix_sha256": (
                "c7b52c0afc887342ad4bdc42f91f979fc49e1cd0b21b8e7c1c31946033de9bed"
            ),
            "identity_status": "immutable_release_with_local_overlay",
            "line": "core",
            "source_inventory_path": "SOURCE_INVENTORY.json",
            "source_inventory_sha256": (
                "e94030de854a7bbb2b75cbe22b4bb303f2cda004328a1bf7e49a76b068221406"
            ),
            "version": "1.0.7",
        },
        "reference release",
    )
    generator = record.get("generator")
    if not isinstance(generator, dict):
        raise RuntimeError("Draft verification boundary requires a generator record")
    expected_generator = {
        "dependency_lock_path": "requirements-lock.txt",
        "dependency_lock_sha256": DRAFT_TAGGED_CONTRACTS["requirements-lock.txt"],
        "output_path": DRAFT_OVERLAY_RELATIVE.as_posix(),
        "required_runtime": "python==3.12.10",
        "runtime": "python==3.12.10",
        "runtime_classification": "release_authoritative",
        "runtime_classification_scope": "cpython-version-and-tagged-runtime-lock-contracts",
        "runtime_contract_path": "RUNTIME.json",
        "runtime_contract_sha256": DRAFT_TAGGED_CONTRACTS["RUNTIME.json"],
        "runtime_implementation": "CPython",
        "version": "0.4.1",
    }
    for key, expected_generator_value in expected_generator.items():
        require_exact(generator.get(key), expected_generator_value, f"generator.{key}")

    overlay = record.get("maintenance_overlay")
    if not isinstance(overlay, dict):
        raise RuntimeError("Draft verification boundary requires maintenance_overlay")
    expected_overlay = {
        "overlay_id": "astra-core-integrity-m1",
        "promotion_status": "unpromoted_source_repair",
        "baseline_commit": "f66027da807a35a1682033ba41348e81f9ceb7e7",
        "baseline_tree": "2854b9c0ea13cf08d1f6c559cb471acee7e2b74e",
        "milestone_changed_paths": DRAFT_MILESTONE_PATHS,
        "identity_closure_paths": DRAFT_CLOSURE_PATHS,
        "authoritative_source_path": DRAFT_SOURCE_RELATIVE,
        "authoritative_source_sha256": DRAFT_SOURCE_SHA256,
        "frozen_record_path": "evidence/claim_source_coverage_v1.0.7.json",
        "frozen_record_sha256": DRAFT_TAGGED_CONTRACTS[
            "evidence/claim_source_coverage_v1.0.7.json"
        ],
        "release_tag": DRAFT_RELEASE_IDENTITY["tag"],
        "release_tag_object": DRAFT_RELEASE_IDENTITY["tag_object"],
        "release_commit": DRAFT_RELEASE_IDENTITY["commit"],
        "release_tree": DRAFT_RELEASE_IDENTITY["tree"],
    }
    for key, expected_overlay_value in expected_overlay.items():
        require_exact(overlay.get(key), expected_overlay_value, f"maintenance_overlay.{key}")
    projection = overlay.get("source_projection")
    if not isinstance(projection, dict):
        raise RuntimeError("Draft verification boundary requires a source projection")
    projection_expected = {
        "scheme": "astra-source-projection-v1",
        "scope": "astra-core-integrity-m1-repository-source-v1",
        "serialization": "astra-binary-length-prefixed-v1",
        "path_encoding": "ascii-posix",
        "canonical_byte_domain": "git-index-blob",
        "excluded_paths": DRAFT_CLOSURE_PATHS,
    }
    for key, expected_projection_value in projection_expected.items():
        require_exact(
            projection.get(key), expected_projection_value, f"source_projection.{key}"
        )
    return overlay


def load_candidate_overlay_record() -> dict[str, Any] | None:
    overlay_path = ROOT / DRAFT_OVERLAY_RELATIVE
    if not overlay_path.exists():
        return None
    if is_link_or_junction(overlay_path) or not overlay_path.is_file():
        raise RuntimeError("Draft maintenance overlay must be a regular file")
    schema_path = ROOT / DRAFT_SCHEMA_RELATIVE
    if is_link_or_junction(schema_path) or not schema_path.is_file():
        raise RuntimeError("Draft maintenance schema must be a regular file")
    require_exact(sha256(schema_path), DRAFT_SCHEMA_SHA256, "overlay schema bytes")
    record = strict_json_object(overlay_path)
    schema = strict_json_object(schema_path)
    from jsonschema import Draft7Validator, FormatChecker

    Draft7Validator.check_schema(schema)
    errors = sorted(
        Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(record),
        key=lambda error: repr(list(error.absolute_path)),
    )
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.absolute_path) or "<root>"
        raise RuntimeError(f"Draft maintenance overlay schema failure at {location}: {first.message}")
    validate_candidate_overlay_record(record)
    return record


def indexed_regular_mode(relative: str, environment: dict[str, str]) -> str:
    output = str(
        capture_git(["ls-files", "--stage", "--", relative], environment=environment)
    )
    lines = output.splitlines()
    if len(lines) != 1:
        raise RuntimeError(f"Expected one stage-0 Git index entry for {relative}")
    match = re.fullmatch(r"([0-7]{6}) [0-9a-f]{40} 0\t(.+)", lines[0])
    if match is None or match.group(2) != relative:
        raise RuntimeError(f"Malformed or non-stage-0 Git index entry for {relative}")
    return match.group(1)


def indexed_baseline_source_changes(environment: dict[str, str]) -> set[str]:
    raw = capture_git(
        [
            "diff",
            "--cached",
            "--no-renames",
            "--name-only",
            "-z",
            "f66027da807a35a1682033ba41348e81f9ceb7e7",
            "--",
        ],
        environment=environment,
        binary=True,
    )
    if not isinstance(raw, bytes):
        raise TypeError("Expected binary Git path output")
    try:
        paths = {item.decode("ascii") for item in raw.split(b"\0") if item}
    except UnicodeDecodeError as error:
        raise RuntimeError("Non-ASCII path blocks the draft verification boundary") from error
    return paths - set(DRAFT_CLOSURE_PATHS)


def verify_candidate_baseline_delta(
    overlay: dict[str, Any], environment: dict[str, str]
) -> None:
    changes = indexed_baseline_source_changes(environment)
    missing = set(DRAFT_MILESTONE_PATHS) - changes
    if missing:
        raise RuntimeError(
            "Draft verification boundary is missing milestone changes: "
            + ", ".join(sorted(missing))
        )
    require_exact(
        overlay.get("additional_baseline_changed_paths"),
        sorted(changes - set(DRAFT_MILESTONE_PATHS)),
        "maintenance_overlay.additional_baseline_changed_paths",
    )


def atlas_publication_overlay_present(environment: dict[str, str]) -> bool:
    """Require the committed S2 reconstruction before it can replace the M1 delta gate."""

    path = ROOT / ATLAS_S2_OVERLAY_RELATIVE
    if not path.exists():
        return False
    if is_link_or_junction(path) or not path.is_file():
        raise RuntimeError("Atlas S2 publication overlay must be a regular file")
    record = strict_json_object(path)
    expected = {
        "overlay_id": "dark-medium-response-atlas-publication-successor-s2",
        "status": "publication_candidate",
    }
    if {key: record.get(key) for key in expected} != expected:
        raise RuntimeError("Atlas S2 publication overlay identity is malformed")
    dirty = str(
        capture_git(["status", "--porcelain=v1", "--untracked-files=no"], environment=environment)
    ).strip()
    if dirty:
        raise RuntimeError("Atlas S2 boundary requires a clean committed worktree")
    current_bytes = path.read_bytes()
    revisions = str(
        capture_git(
            ["rev-list", "HEAD", "--", ATLAS_S2_OVERLAY_RELATIVE.as_posix()],
            environment=environment,
        )
    ).splitlines()
    for revision in revisions:
        candidate = revision.strip()
        if re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", candidate) is None:
            raise RuntimeError("Atlas S2 history contains an invalid commit identity")
        blob = capture_git(
            ["show", f"{candidate}:{ATLAS_S2_OVERLAY_RELATIVE.as_posix()}"],
            environment=environment,
            binary=True,
        )
        if not isinstance(blob, bytes):
            raise TypeError("Expected binary Atlas S2 blob")
        if blob != current_bytes:
            continue
        run(
            isolated_python(
                "tools/build_dark_medium_response_atlas_publication_successor_overlay.py",
                "--verify-commit",
                candidate,
            ),
            environment=environment,
        )
        return True
    raise RuntimeError(
        "Atlas S2 publication overlay is not byte-verified from a committed candidate"
    )


def verify_candidate_not_at_tag(
    environment: dict[str, str], *, allow_atlas_tag: bool = False
) -> None:
    github_ref = environment.get("GITHUB_REF", "")
    if github_ref.startswith("refs/tags/") or environment.get("GITHUB_REF_TYPE") == "tag":
        if (
            allow_atlas_tag
            and github_ref == f"refs/tags/{ATLAS_RELEASE_TAG}"
            and environment.get("GITHUB_REF_TYPE") == "tag"
        ):
            return
        raise RuntimeError("An unpromoted draft overlay cannot authorize a tag-event verification")
    tags_at_head = [
        tag
        for tag in str(
            capture_git(["tag", "--points-at", "HEAD"], environment=environment)
        ).splitlines()
        if tag
    ]
    if tags_at_head and not (allow_atlas_tag and tags_at_head == [ATLAS_RELEASE_TAG]):
        raise RuntimeError("An unpromoted draft overlay cannot authorize verification at a tag")


def verify_tagged_draft_contracts(commit: str, environment: dict[str, str]) -> None:
    for relative, expected_digest in DRAFT_TAGGED_CONTRACTS.items():
        path = ROOT / Path(relative)
        if is_link_or_junction(path) or not path.is_file():
            raise RuntimeError(f"Draft-boundary contract must be a regular file: {relative}")
        current = path.read_bytes()
        require_exact(sha256_bytes(current), expected_digest, f"contract bytes for {relative}")
        tagged = tagged_blob_bytes(commit, relative, environment)
        if current != tagged:
            raise RuntimeError(f"Draft-boundary contract differs from v1.0.7: {relative}")


def verify_unpromoted_source(
    commit: str, overlay: dict[str, Any], environment: dict[str, str]
) -> None:
    source_path = ROOT / DRAFT_SOURCE_RELATIVE
    if is_link_or_junction(source_path) or not source_path.is_file():
        raise RuntimeError("The unpromoted authoritative source must be a regular file")
    require_exact(indexed_regular_mode(DRAFT_SOURCE_RELATIVE, environment), "100644", "source mode")
    source = source_path.read_bytes()
    require_exact(sha256_bytes(source), overlay["authoritative_source_sha256"], "source bytes")
    if source == tagged_blob_bytes(commit, DRAFT_SOURCE_RELATIVE, environment):
        raise RuntimeError("The unpromoted source does not differ from immutable v1.0.7")


def candidate_document_commit(environment: dict[str, str]) -> str | None:
    record = load_candidate_overlay_record()
    if record is None:
        return None
    overlay = record["maintenance_overlay"]
    atlas_s2 = atlas_publication_overlay_present(environment)
    if not atlas_s2:
        verify_candidate_baseline_delta(overlay, environment)
    verify_candidate_not_at_tag(environment, allow_atlas_tag=atlas_s2)

    tag = DRAFT_RELEASE_IDENTITY["tag"]
    observed_tag = strict_tag_identity(tag, environment)
    expected_tag = {key: DRAFT_RELEASE_IDENTITY[key] for key in ("tag_object", "commit", "tree")}
    require_exact(observed_tag, expected_tag, "immutable v1.0.7 tag identity")
    require_exact(RELEASE_SPEC.get("version"), "1.0.7", "release-spec version")
    require_exact(RELEASE_SPEC.get("tag"), tag, "release-spec tag")

    commit = DRAFT_RELEASE_IDENTITY["commit"]
    verify_tagged_draft_contracts(commit, environment)
    verify_unpromoted_source(commit, overlay, environment)
    return commit


def tagged_document_identity(
    commit: str, environment: dict[str, str]
) -> dict[str, dict[str, Any]]:
    try:
        relatives = tuple(path.relative_to(ROOT).as_posix() for path in DOCUMENT_OUTPUTS)
    except ValueError as error:
        raise RuntimeError("A document output path is outside the repository") from error
    require_exact(relatives, DRAFT_DOCUMENT_RELATIVES, "frozen document roster")
    records: dict[str, dict[str, Any]] = {}
    for path, relative in zip(DOCUMENT_OUTPUTS, relatives, strict=True):
        if is_link_or_junction(path) or not path.is_file():
            raise RuntimeError(f"Frozen document output must be a regular file: {relative}")
        require_exact(indexed_regular_mode(relative, environment), "100644", f"mode for {relative}")
        value = tagged_blob_bytes(commit, relative, environment)
        records[relative] = {"bytes": len(value), "sha256": sha256_bytes(value)}
    return records


def verify_frozen_document_outputs(commit: str, environment: dict[str, str]) -> None:
    expected = tagged_document_identity(commit, environment)
    observed = identity(list(DOCUMENT_OUTPUTS))
    if observed != expected:
        difference = identity_difference(expected, observed)
        raise RuntimeError(
            "Frozen document outputs differ from immutable v1.0.7: "
            + json.dumps(difference, sort_keys=True)
        )


def verify_strict_document_replay(environment: dict[str, str]) -> None:
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


def verify_document_boundary(environment: dict[str, str]) -> str:
    candidate_commit = candidate_document_commit(environment)
    if candidate_commit is None:
        verify_strict_document_replay(environment)
        return "strict_replay"
    verify_frozen_document_outputs(candidate_commit, environment)
    return "frozen_v1.0.7"


def verify_atlas_document_replay(environment: dict[str, str]) -> None:
    """Replay the separate Atlas producer twice without touching core outputs."""

    before = identity(list(ATLAS_DOCUMENT_OUTPUTS))
    command = controlled_python("tools/build_dark_medium_response_atlas_documents.py")
    run(command, environment=environment)
    first = identity(list(ATLAS_DOCUMENT_OUTPUTS))
    if first != before:
        difference = identity_difference(before, first)
        raise RuntimeError(
            "Atlas document outputs were stale or non-deterministic: "
            + json.dumps(difference, sort_keys=True)
        )
    run(command, environment=environment)
    second = identity(list(ATLAS_DOCUMENT_OUTPUTS))
    if second != first:
        difference = identity_difference(first, second)
        raise RuntimeError(
            "Consecutive Atlas document builds are not byte-identical: "
            + json.dumps(difference, sort_keys=True)
        )


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

    document_mode = verify_document_boundary(environment)
    verify_atlas_document_replay(environment)
    verify_focused(environment)
    if document_mode == "strict_replay":
        print("Full deterministic scientific, core-document, and Atlas-document replay passed.")
    else:
        print(
            "Full deterministic scientific replay passed; immutable v1.0.7 document bytes "
            "match the annotated release tag and the separate Atlas document producer "
            "replayed byte-identically."
        )


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
