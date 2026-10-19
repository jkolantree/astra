"""Linux development gates; never promote or overwrite historical release artifacts."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections.abc import Collection
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "RUNTIME-linux.json"
# An order of magnitude tighter than the benchmark's frozen algebra tolerance.
# Discrete decisions, counts, keys, string identities and array lengths stay exact.
RTOL = ATOL = 1e-12

# Exact copied-input roles, not a directory-wide exclusion or runtime admission.
# A successor source admission must bind these fixtures and this controller.
REPLAY_COPIED_INPUTS = frozenset({
    "data/integrated-core/bridge_contracts.json",
    "data/integrated-core/integrated_case.json",
})
ATLAS_PREFIX = "resources/dark-medium-response-atlas/v0.1.0/"
REPLAY_ATLAS_OUTPUTS = tuple(ATLAS_PREFIX + name for name in (
    "dark-medium-response-atlas-v0.1.0.html", "dark-medium-response-atlas-v0.1.0.pdf",
    "html-accessibility.json", "pdf-inspection.json",
))


def replay_output_names(source_names: Collection[str]) -> list[str]:
    """Separate exact copied fixtures from generated data/figures/Atlas outputs.

    Unknown data paths remain outputs and therefore fail a frozen output-inventory
    check. This function does not admit input bytes or alter expected output hashes.
    """
    names = set(source_names)
    missing = set(REPLAY_ATLAS_OUTPUTS) - names
    if missing:
        raise RuntimeError("Linux replay is missing declared Atlas outputs: " + ", ".join(sorted(missing)))
    outputs = {
        name for name in names
        if name.startswith(("data/", "figures/")) and name not in REPLAY_COPIED_INPUTS
    }
    return sorted(outputs | set(REPLAY_ATLAS_OUTPUTS))


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
    shell = runtime["ci_distribution"]["test_shell"]
    require_digest(ROOT / "tmp/linux-bootstrap/powershell/pwsh", shell["executable_sha256"])
    version = subprocess.run(
        ["pwsh", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command",
         "$PSVersionTable.PSVersion.ToString()"], check=True, capture_output=True, text=True,
    ).stdout.strip()
    if version != shell["version"]:
        raise RuntimeError("PowerShell test runtime drift")
    # The source platform contract is a frozen historical input, never a migration output.
    require_digest(ROOT / "RUNTIME.json",
                   "f3fa00ed692fc6738b47f6c8a44e9c5ac062d269ac452cfbcf90c4ef8ff39485")


def configure() -> tuple[Any, dict[str, str]]:
    from tools import verify

    verify.RUNTIME_PATH = PROFILE
    environment = verify.configure_environment()
    git_bin = ROOT / "tmp/linux-bootstrap/git/usr/bin"
    environment["PATH"] = os.pathsep.join((str(git_bin), str(ROOT / "tmp/linux-bootstrap/powershell"),
                                          environment.get("PATH", "")))
    environment["GIT_EXEC_PATH"] = str(ROOT / "tmp/linux-bootstrap/git/usr/lib/git-core")
    environment["PLAYWRIGHT_BROWSERS_PATH"] = str(ROOT / "tmp/linux-browsers")
    for key, relative in (("XDG_CACHE_HOME", "tmp/linux-cache"), ("PIP_CACHE_DIR", "tmp/pip-cache"),
                          ("XDG_CONFIG_HOME", "tmp/linux-config"), ("XDG_DATA_HOME", "tmp/linux-data")):
        verify.ensure_safe_directory(ROOT / relative)
        environment[key] = str(ROOT / relative)
    environment["POWERSHELL_TELEMETRY_OPTOUT"] = "1"
    os.environ.update(environment)
    return verify, environment


def check_scientific_files(original: Path, generated: Path) -> None:
    for path in sorted((original / "data").rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(original)
        other = generated / relative
        if relative.as_posix() in REPLAY_COPIED_INPUTS:
            if path.read_bytes() != other.read_bytes():
                raise RuntimeError("Linux replay modified copied input: " + relative.as_posix())
            continue
        if path.suffix == ".json":
            equivalent(json.loads(path.read_text()), json.loads(other.read_text()), str(path.name))
        elif path.suffix == ".csv":
            def rows(source: Path) -> list[list[Any]]:
                parsed = []
                for row in csv.reader(source.read_text().splitlines()):
                    values: list[Any] = []
                    for value in row:
                        try:
                            if value.startswith(("[", "{")):
                                values.append(json.loads(value))
                                continue
                            if ";" in value:
                                values.append([float(item) for item in value.split(";")])
                                continue
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


def replay_path(directory: Path, name: str) -> Path:
    """Check member spelling and every existing ancestor before any filesystem use."""
    relative = PurePosixPath(name)
    if relative.is_absolute() or relative.as_posix() != name or any(
        part in {"", ".", ".."} for part in relative.parts
    ):
        raise RuntimeError("Unsafe Linux replay member: " + name)
    path = directory
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise RuntimeError("Linux replay contains a symbolic link: " + name)
    return path


def replay_file(directory: Path, name: str) -> Path:
    """Resolve a regular, unlinked member without following parent symlinks."""
    path = replay_path(directory, name)
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise RuntimeError("Linux replay requires an unlinked regular file: " + name)
    return path


def write_replay_report(report: dict[str, Any]) -> None:
    """Replace a local receipt atomically without writing through a linked path."""
    name = "tmp/linux-verification.json"
    path = replay_path(ROOT, name)
    if path.exists():
        replay_file(ROOT, name)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".linux-receipt-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(json.dumps(report, indent=2) + "\n")
        replay_path(ROOT, name)
        if path.exists():
            replay_file(ROOT, name)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def fresh_replay_passes(
    destination: Path, before: dict[str, str], outputs: list[str],
    environment: dict[str, str], workers: int, report: dict[str, Any],
) -> list[dict[str, str]]:
    """Copy inputs only; require every output to be newly created on each pass.

    Frozen output hashes are expectations only and are never written to this tree.
    The caller checks the complete frozen inventory before staging anything.
    """
    from tools.verify_linux_baseline import check_replay_tree

    for name in sorted(before.keys() - set(outputs)):
        source = replay_file(ROOT, name)
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    passes = []
    for number in (1, 2):
        report["active_pass"] = number
        for name in outputs:
            path = replay_path(destination, name)
            # lexists semantics also catch broken symlinks. Validate before unlink.
            if path.exists() or path.is_symlink():
                replay_file(destination, name).unlink()
            path.parent.mkdir(parents=True, exist_ok=True)
        report["output_files_present_before_pass"] = 0
        for script, arguments in (
            ("scripts/make_figures.py", ["--workers", str(workers)]),
            ("tools/build_dark_medium_response_atlas_documents.py",
             ["--no-identity", "--linux-layout"]),
        ):
            subprocess.run([sys.executable, "-I", "-B", str(destination / script), *arguments],
                           cwd=destination, env=environment, check=True)
        # Check fixture/source changes before diagnosing missing generated outputs.
        for name in sorted(before.keys() - set(outputs)):
            if digest(replay_file(destination, name)) != before[name]:
                raise RuntimeError("Linux replay modified copied source: " + name)
        observed = {}
        for name in outputs:
            path = destination / name
            if path.exists() or path.is_symlink():
                observed[name] = digest(replay_file(destination, name))
        missing = sorted(set(outputs) - observed.keys())
        report["pass_inventory"].append({
            "pass": number, "required_count": len(outputs),
            "generated_count": len(observed), "missing": missing,
            "output_sha256": observed,
        })
        if missing:
            raise RuntimeError("Linux replay missing freshly generated outputs: " + ", ".join(missing))
        check_replay_tree(destination, before, set(outputs))
        passes.append(observed)
    return passes


def replay(
    environment: dict[str, str], workers: int, *, historical_required: bool = True
) -> dict[str, Any]:
    """Persist incomplete/failing receipts even for staging or child-process errors."""
    report: dict[str, Any] = {
        "classification": "linux_replay_incomplete_unpromoted",
        "pass_inventory": [], "historical_scientific_equivalence": "NOT_RUN",
        "linux_baseline_gate": "NOT_RUN", "source_checkout_unchanged": None,
        "freshness_gate": "INCOMPLETE",
    }
    write_replay_report(report)
    try:
        result = _replay(environment, workers, historical_required=historical_required, report=report)
    except Exception as error:
        report["classification"] = "blocked_linux_migration"
        if report["freshness_gate"] == "INCOMPLETE":
            report["freshness_gate"] = "FAIL"
        report["blocking_error"] = str(error)
        report["error_type"] = type(error).__name__
        if isinstance(error, subprocess.CalledProcessError):
            report["child_exit_code"] = error.returncode
        try:
            write_replay_report(report)
        except Exception as receipt_error:
            error.add_note("Could not safely persist failure receipt: " + str(receipt_error))
        raise
    write_replay_report(report)
    return result


def _replay(
    environment: dict[str, str], workers: int, *, historical_required: bool,
    report: dict[str, Any],
) -> dict[str, Any]:
    from tools import check_repository
    from tools.verify_linux_baseline import check_outputs

    destination = Path(tempfile.mkdtemp(prefix="linux-replay-", dir=ROOT / "tmp"))
    paths = check_repository.public_files()
    before = {p.relative_to(ROOT).as_posix(): digest(replay_file(ROOT, p.relative_to(ROOT).as_posix()))
              for p in paths}
    outputs = replay_output_names(before)
    baseline_path = ROOT / "evidence/linux-research-v1.json"
    expected = json.loads(baseline_path.read_text())["output_sha256"]
    if set(outputs) != expected.keys():
        raise RuntimeError("Linux baseline output inventory changed before replay")
    report.update(replay_directory=destination.relative_to(ROOT).as_posix(),
                  baseline_record_sha256=digest(baseline_path), required_outputs=outputs,
                  runtime_sha256=digest(PROFILE))
    atlas = ATLAS_PREFIX
    try:
        passes = fresh_replay_passes(destination, before, outputs, environment, workers, report)
        report["freshness_gate"] = "PASS"
    finally:
        # Preservation diagnostics must never replace the primary child failure.
        try:
            after = {p.relative_to(ROOT).as_posix():
                     digest(replay_file(ROOT, p.relative_to(ROOT).as_posix()))
                     for p in check_repository.public_files()}
            report["source_checkout_unchanged"] = after == before
        except Exception as source_error:
            report["source_checkout_unchanged"] = False
            report["source_preservation_error"] = str(source_error)
    if not report["source_checkout_unchanged"]:
        raise RuntimeError("Linux replay changed the source checkout")
    report.update({
        "linux_output_sha256": passes[-1],
        "consecutive_linux_bytes_equal": passes[0] == passes[1],
        "different_from_windows_bytes": [name for name in outputs if passes[0][name] != before[name]],
        "scientific_tolerance": {"relative": RTOL, "absolute": ATOL, "discrete": "exact"},
        "core_documents": "immutable historical bytes; current source is an unpromoted draft",
        "atlas_documents": "two checked Linux builds; no release identity generated",
    })
    from pypdf import PdfReader

    pdf_name = atlas + "dark-medium-response-atlas-v0.1.0.pdf"

    def text_pages(path: Path) -> list[str]:
        return [" ".join((page.extract_text() or "").split()) for page in PdfReader(path).pages]

    historical_pages = text_pages(ROOT / pdf_name)
    linux_pages = text_pages(destination / pdf_name)
    html_name = atlas + "dark-medium-response-atlas-v0.1.0.html"
    report["atlas_html_identical"] = before[html_name] == passes[0][html_name]
    report["atlas_pdf_comparison"] = {
        "historical_pages": len(historical_pages), "linux_pages": len(linux_pages),
        "same_normalized_page_text": historical_pages == linux_pages,
        "same_normalized_document_text": " ".join(historical_pages) == " ".join(linux_pages),
        "scope": "PDF differences remain unpromoted; independent PDF inspection passed",
    }
    try:
        if not report["source_checkout_unchanged"]:
            raise RuntimeError("Linux replay changed the source checkout")
        if not report["consecutive_linux_bytes_equal"]:
            raise RuntimeError("Consecutive Linux scientific/Atlas replays are not byte-identical")
        try:
            for output_hashes in passes:
                check_outputs(expected, output_hashes)
        except RuntimeError:
            report["linux_baseline_gate"] = "FAIL"
            raise
        report["linux_baseline_gate"] = "PASS"
        if not report["atlas_html_identical"]:
            raise RuntimeError("Linux Atlas HTML differs from historical content and font bytes")
        try:
            check_scientific_files(ROOT, destination)
        except RuntimeError as error:
            report["historical_scientific_equivalence"] = "FAIL"
            report["historical_comparison_error"] = str(error)
            if historical_required:
                raise
        else:
            report["historical_scientific_equivalence"] = "PASS"
    except RuntimeError as error:
        report["classification"] = "blocked_linux_migration"
        report["blocking_error"] = str(error)
        raise
    report["classification"] = (
        "linux_repeatable_science_equivalent_unpromoted"
        if report["historical_scientific_equivalence"] == "PASS"
        else "linux_repeatable_historical_drift_unpromoted"
    )
    return report




# These three tests actually regenerate retained scientific results. Ordinary
# development still runs historical identity guards, temporary Git fixtures and
# website assembly tests; scientific replay remains an explicit separate mode.
CURRENT_REPLAY_TESTS = (
    "tests/test_dark_medium_response_benchmark.py::test_retained_evaluation_reproduces_with_frozen_sources",
    "tests/test_linux_runtime.py::test_retained_benchmark_linux_bytes_and_historical_scientific_equivalence",
    "tests/test_numerical_regressions.py::ScopedClaimControls::test_CORE08_repeatable_explicit_run",
)


def verify_current_development_dependencies() -> None:
    for name, expected in (("sympy", "1.14.0"), ("mpmath", "1.3.0")):
        if importlib.metadata.version(name) != expected:
            raise RuntimeError("Current-development dependency version differs: " + name)


def current_source_inventory() -> tuple[list[Path], dict[str, Any]]:
    """Bind regular current files to the real Git index, without rewriting receipts."""
    from tools import local_successor_profile as safety
    from tools import release_integrity

    if release_integrity.ROOT.resolve() != ROOT.resolve():
        raise RuntimeError("Current source inventory belongs to another repository")
    records = release_integrity.git(["ls-files", "--stage", "-z"], binary=True)
    if not isinstance(records, bytes):
        raise TypeError("Git index inventory must be bytes")
    files: dict[str, dict[str, Any]] = {}
    folded: set[str] = set()
    for entry in records.split(b"\0"):
        if not entry:
            continue
        metadata, raw_path = entry.split(b"\t", 1)
        mode, oid, stage = metadata.decode("ascii").split()
        name = raw_path.decode("utf-8")
        relative = PurePosixPath(name)
        if (mode not in {"100644", "100755"} or stage != "0"
                or len(oid) not in {40, 64} or any(c not in "0123456789abcdef" for c in oid)
                or relative.is_absolute() or relative.as_posix() != name
                or any(part in {".", "..", ""} for part in name.split("/"))
                or "\\" in name or ":" in name or name.casefold() in folded):
            raise RuntimeError("Unsafe or unmerged current index entry: " + name)
        folded.add(name.casefold())
        path = ROOT / relative
        safety.safe_parents(path)
        info = safety.safe_stat(path)
        if not stat.S_ISREG(info.st_mode):
            raise RuntimeError("Current indexed file is not regular: " + name)
        value = path.read_bytes()
        blob = hashlib.new("sha1" if len(oid) == 40 else "sha256")
        blob.update(f"blob {len(value)}\0".encode("ascii"))
        blob.update(value)
        if blob.hexdigest() != oid:
            raise RuntimeError("Current file differs from its Git index blob: " + name)
        files[name] = {"bytes": len(value), "sha256": hashlib.sha256(value).hexdigest()}
    if not files:
        raise RuntimeError("Current source inventory is empty")
    paths = safety.observe_payload(ROOT, files)
    source = {
        "head": str(release_integrity.git(["rev-parse", "HEAD"])).strip(),
        "head_tree": str(release_integrity.git(["rev-parse", "HEAD^{tree}"])).strip(),
        "files": files,
        "file_map_sha256": hashlib.sha256(safety.canonical(files)).hexdigest(),
    }
    return paths, source


def current_test_command(verify: Any, work: Path) -> list[str]:
    return verify.controlled_python(
        "-m", "pytest", "-q", "-ra", "-o", "addopts=", "--strict-config", "--strict-markers",
        "-p", "no:cacheprovider", "--basetemp", str(work / "pytest"),
        "--junitxml", str(work / "test-results.xml"),
        *["--deselect=" + node for node in CURRENT_REPLAY_TESTS], "tests",
    )


def require_current_test_result(path: Path) -> dict[str, int]:
    """A successful process with skipped, empty or malformed results is not a pass."""
    from tools.local_successor_profile import safe_stat

    if not stat.S_ISREG(safe_stat(path).st_mode):
        raise RuntimeError("Current test report must be a regular file")
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
    counts = dict.fromkeys(("tests", "failures", "errors", "skipped"), 0)
    try:
        for suite in suites:
            for key in counts:
                value = int(suite.attrib[key])
                if value < 0:
                    raise ValueError("Negative test count")
                counts[key] += value
    except (KeyError, ValueError) as error:
        raise RuntimeError("Malformed current test counts") from error
    if counts["tests"] <= 0 or any(counts[key] for key in ("failures", "errors", "skipped")):
        raise RuntimeError("Current tests are empty, failed, errored or skipped: " + json.dumps(counts))
    return counts


def run_current_development(verify: Any, environment: dict[str, str]) -> dict[str, Any]:
    """Check current source and Pages; do not invoke scientific/release reproduction."""
    import playwright

    from tools import check_repository, local_successor_profile, release_integrity

    paths, before = current_source_inventory()
    selected = local_successor_profile.public_check_projection(ROOT, paths, check_repository)
    work = Path(tempfile.mkdtemp(prefix="current-development-", dir=ROOT / "tmp"))
    node_directory = Path(playwright.__file__).parent / "driver"
    if not (node_directory / "node").is_file():
        raise RuntimeError("Playwright's native Node runtime is unavailable")
    environment = dict(environment, PATH=os.pathsep.join((str(node_directory), environment["PATH"])))
    source_names = [path.relative_to(ROOT).as_posix() for path in selected]
    link_code = (
        "from pathlib import Path;from tools.check_repository_links import check_repository_links;"
        "print(check_repository_links(sources=[Path(p).absolute() for p in "
        f"{[name for name in source_names if name.endswith('.md')]!r}]))"
    )
    commands = {
        "ordinary_tests": current_test_command(verify, work),
        "maintained_python_lint": verify.controlled_python(
            "-m", "ruff", "check", "--no-cache", *[name for name in source_names if name.endswith(".py")]),
        "source_type_checks": verify.controlled_python("-m", "mypy", "--cache-dir", str(work / "mypy"), "src"),
        "citation": verify.controlled_python("-c", "from cffconvert.cli.cli import cli;cli()", "--validate"),
        "maintained_repository_links": verify.controlled_python("-c", link_code),
        "retained_external_link_record": verify.controlled_python("tools/check_external_links.py"),
        "current_pages_admission": verify.controlled_python("tools/check_pages_admission.py", "--current"),
        "retained_pdf_inspection": verify.controlled_python("tools/inspect_pdf.py"),
        "diff_whitespace": ["git", "diff", "--check", "HEAD"],
    }
    results: dict[str, Any] = {}
    try:
        check_repository.check_cache_boundaries()
        check_repository.check_private_operator_policy_boundary()
        check_repository.check_repository_contents(selected, payload_paths=paths)
        results["repository_contents"] = {"status": "PASS"}
    except (OSError, RuntimeError, ValueError) as error:
        results["repository_contents"] = {"status": "FAIL", "error": str(error)}
    try:
        for name, command in commands.items():
            completed = subprocess.run(command, cwd=ROOT, env=environment, check=False,
                                       capture_output=True, text=True, encoding="utf-8", errors="replace")
            result = {"status": "PASS" if completed.returncode == 0 else "FAIL",
                      "returncode": completed.returncode, "command": command,
                      "stdout": completed.stdout, "stderr": completed.stderr}
            if name == "ordinary_tests":
                try:
                    result["junit_counts"] = require_current_test_result(work / "test-results.xml")
                except (OSError, RuntimeError, ET.ParseError) as error:
                    result.update(status="FAIL", result_error=str(error))
            results[name] = result
    finally:
        _, after = current_source_inventory()
        if before != after:
            raise RuntimeError("Current source/index identity changed during development checks")
    try:
        release_integrity.assert_clean_worktree()
        results["committed_source_identity"] = {"status": "PASS"}
    except RuntimeError as error:
        results["committed_source_identity"] = {"status": "FAIL", "error": str(error)}
    return {
        "status": "PASS_CURRENT_DEVELOPMENT" if all(x["status"] == "PASS" for x in results.values())
                  else "FAIL_CURRENT_DEVELOPMENT",
        "source": {key: value for key, value in before.items() if key != "files"},
        "tracked_files": len(paths), "maintained_files": len(selected), "gates": results,
        "scientific_replay_tests_not_run": list(CURRENT_REPLAY_TESTS),
        "retained_collection_policy": "tests/conftest.py retains the historical S1 exclusion",
        "historical_receipts": "PRESERVED_NOT_REISSUED", "scientific_replay": "NOT_RUN",
        "release_validation": "NOT_RUN", "publication": "NOT_PERFORMED",
        "result_directory": str(work.relative_to(ROOT)),
    }


def main() -> None:
    if not sys.flags.isolated or not sys.dont_write_bytecode:
        raise RuntimeError("Use -I -B before tools/verify_linux.py")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--runtime-only", action="store_true")
    parser.add_argument("--current-development", action="store_true",
                        help="Validate the current Git source and Pages without scientific replay")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.current_development and (args.all or args.runtime_only):
        parser.error("--current-development cannot combine with --all or --runtime-only")
    if args.current_development and (os.environ.get("GITHUB_REF", "").startswith("refs/tags/")
                                     or os.environ.get("GITHUB_REF_TYPE") == "tag"):
        parser.error("Current development does not authorize a tag-event verification")
    if args.workers < 1:
        raise ValueError("workers must be positive")
    sys.path.insert(0, str(ROOT))
    verify, environment = configure()
    verify_linux_identity(json.loads(PROFILE.read_text()))
    verify.verify_runtime(environment)
    if args.runtime_only:
        print("Linux runtime identity passed (no scientific or release claim).")
        return
    if args.current_development:
        verify_current_development_dependencies()
        result = run_current_development(verify, environment)
        report = ROOT / result["result_directory"] / "results.json"
        report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True))
        if result["status"] != "PASS_CURRENT_DEVELOPMENT":
            raise SystemExit(1)
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
        write_replay_report(result)
        print("Linux replay passed; platform byte differences recorded in tmp/linux-verification.json.")
    print("Linux development gates passed. Historical Windows release replay was not exercised.")


if __name__ == "__main__":
    main()
