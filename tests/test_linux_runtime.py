"""Negative controls for Linux migration and its scientific/byte boundaries."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

import pytest

from tools import verify_linux

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(platform.system() != "Linux", reason="Linux byte baseline")
def test_retained_benchmark_linux_bytes_and_historical_scientific_equivalence() -> None:
    package = ROOT / "resources/dark-medium-response-benchmark/draft-v0.1.0"
    spec = importlib.util.spec_from_file_location("linux_benchmark", package / "benchmark.py")
    assert spec is not None and spec.loader is not None
    benchmark = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(benchmark)
    fixture = json.loads((ROOT / "evidence/linux-benchmark-results.json").read_text())
    assert fixture["runtime_sha256"] == verify_linux.digest(ROOT / "RUNTIME-linux.json")
    for name, expected_hash in fixture["source_sha256"].items():
        assert verify_linux.digest(package / name) == expected_hash
    produced = benchmark.run(benchmark.read_config())  # Includes original frozen-input gate.
    assert benchmark.canonical(produced) == benchmark.canonical(fixture["results"])
    verify_linux.equivalent(json.loads((package / "results.json").read_text()), produced)
    assert produced["comparative_utility"].startswith("UNESTABLISHED")
    for result in produced["evaluation"].values():
        assert result["same_fitted_classes"] == result["paired_trials"] == 384
        assert result["practical_criterion_met"] is False


@pytest.mark.parametrize("observed", [1.00000001, float("nan"), float("inf"), 1, True])
def test_scientific_comparison_rejects_numeric_or_type_drift(observed: object) -> None:
    with pytest.raises(RuntimeError, match="Scientific"):
        verify_linux.equivalent(1.0, observed)


@pytest.mark.parametrize("observed", [
    {"count": 65, "success": True, "score": 1.0},
    {"count": 64, "success": False, "score": 1.0},
    {"count": 64, "success": True},
])
def test_scientific_comparison_keeps_decisions_and_inventory_exact(observed: dict) -> None:
    with pytest.raises(RuntimeError, match="Scientific"):
        verify_linux.equivalent({"count": 64, "success": True, "score": 1.0}, observed)


def test_scientific_comparison_accepts_roundoff_without_claiming_byte_identity() -> None:
    verify_linux.equivalent([1.0, 0.0], [1.0 + 1e-14, 1e-15])
    assert json.dumps([1.0, 0.0]) != json.dumps([1.0 + 1e-14, 1e-15])


def test_linux_runtime_keeps_windows_contract_bytes_and_shared_lock() -> None:
    verify_linux.require_digest(ROOT / "RUNTIME.json",
                               "f3fa00ed692fc6738b47f6c8a44e9c5ac062d269ac452cfbcf90c4ef8ff39485")
    linux = json.loads((ROOT / "RUNTIME-linux.json").read_text())
    windows = json.loads((ROOT / "RUNTIME.json").read_text())
    assert linux["dependency_lock"] == windows["dependency_lock"]
    assert linux["pdf_renderer"]["font_sources"] == windows["pdf_renderer"]["font_sources"]
    assert all(item["library_glob"].endswith(".so") and len(item["sha256"]) == 64
               for item in linux["numeric_kernel"]["libraries"])


def test_runtime_digest_rejects_replaced_executable(tmp_path: Path) -> None:
    executable = tmp_path / "executable"
    executable.write_bytes(b"original")
    expected = verify_linux.digest(executable)
    executable.write_bytes(b"replacement")
    with pytest.raises(RuntimeError, match="byte identity"):
        verify_linux.require_digest(executable, expected)


def test_scientific_csv_gate_checks_embedded_optimizer_values(tmp_path: Path) -> None:
    original, generated = tmp_path / "original", tmp_path / "generated"
    for directory in (original, generated):
        (directory / "data").mkdir(parents=True)
    source = "graph,conductance\nchain,0.22;1.4\n"
    (original / "data/fit.csv").write_text(source)
    (generated / "data/fit.csv").write_text(source)
    verify_linux.check_scientific_files(original, generated)
    (generated / "data/fit.csv").write_text(source.replace("1.4", "1.4000001"))
    with pytest.raises(RuntimeError, match="Scientific numeric drift"):
        verify_linux.check_scientific_files(original, generated)


def test_bootstrap_rejects_cached_archive_corruption(tmp_path: Path) -> None:
    from tools.bootstrap_linux import download

    path = tmp_path / "archive.tar.gz"
    path.write_bytes(b"trusted")
    expected = verify_linux.digest(path)
    path.write_bytes(b"corrupt")
    with pytest.raises(RuntimeError, match="Cached archive digest"):
        download({"asset": path.name, "sha256": expected}, tmp_path)


@pytest.mark.parametrize("unstable", [False, True])
@pytest.mark.parametrize("historical_required", [False, True])
def test_replay_records_failure_without_overwriting_historical_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, unstable: bool, historical_required: bool
) -> None:
    from pypdf import PdfWriter

    from tools import check_repository

    root = tmp_path / "repository"
    (root / "tmp").mkdir(parents=True)
    (root / "data").mkdir()
    source = root / "data/fit.csv"
    source.write_text("value\n1.0\n")
    profile = root / "RUNTIME-linux.json"
    profile.write_text("{}\n")
    atlas = Path("resources/dark-medium-response-atlas/v0.1.0")
    (root / atlas).mkdir(parents=True)
    for name in ("html-accessibility.json", "pdf-inspection.json"):
        (root / atlas / name).write_text("{}\n")
    (root / atlas / "dark-medium-response-atlas-v0.1.0.html").write_text("fixed HTML")
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.write(root / atlas / "dark-medium-response-atlas-v0.1.0.pdf")
    import hashlib

    expected = {path.relative_to(root).as_posix(): verify_linux.digest(path)
                for path in (root / atlas).iterdir()}
    expected["data/fit.csv"] = hashlib.sha256(b"value\n2.0\n").hexdigest()
    (root / "evidence").mkdir()
    (root / "evidence/linux-research-v1.json").write_text(
        json.dumps({"output_sha256": expected})
    )
    paths = [path for path in root.rglob("*") if path.is_file()]
    monkeypatch.setattr(verify_linux, "ROOT", root)
    monkeypatch.setattr(verify_linux, "PROFILE", profile)
    monkeypatch.setattr(check_repository, "public_files", lambda: paths)
    count = 0

    def build(command: list[str], **kwargs: object) -> None:
        nonlocal count
        if command[3].endswith("scripts/make_figures.py"):
            count += 1
            destination = Path(command[3]).parents[1]
            value = count + 1 if unstable else 2
            (destination / "data/fit.csv").write_text(f"value\n{value}.0\n")
        else:
            destination = Path(command[3]).parents[1]
            for name in ("html-accessibility.json", "pdf-inspection.json"):
                (destination / atlas / name).write_text("{}\n")
            (destination / atlas / "dark-medium-response-atlas-v0.1.0.html").write_text("fixed HTML")
            produced = PdfWriter()
            produced.add_blank_page(width=200, height=200)
            produced.write(destination / atlas / "dark-medium-response-atlas-v0.1.0.pdf")

    monkeypatch.setattr(verify_linux.subprocess, "run", build)
    if unstable or historical_required:
        with pytest.raises(RuntimeError, match="not byte-identical" if unstable else "Scientific numeric drift"):
            verify_linux.replay({}, 4, historical_required=historical_required)
        report = json.loads((root / "tmp/linux-verification.json").read_text())
        assert report["classification"] == "blocked_linux_migration"
    else:
        report = verify_linux.replay({}, 4, historical_required=False)
        assert report["classification"] == "linux_repeatable_historical_drift_unpromoted"
        assert report["historical_scientific_equivalence"] == "FAIL"
    assert report["consecutive_linux_bytes_equal"] is not unstable
    assert report["source_checkout_unchanged"] is True
    assert source.read_text() == "value\n1.0\n"


def test_linux_ci_has_read_only_permissions_and_separate_release_gate() -> None:
    from ruamel.yaml import YAML

    workflow = YAML(typ="safe").load((ROOT / ".github/workflows/verify.yml").read_text())
    assert workflow["permissions"] == {"contents": "read"}
    job = workflow["jobs"]["linux"]
    assert job["container"] == "debian:13.6-slim"
    assert "refs/tags/" in workflow["jobs"]["verify"]["if"]
    steps = "\n".join(step.get("run", "") for step in job["steps"])
    assert "bootstrap_linux.py --current-development" in steps
    assert "verify_linux_companion.py --current-development" in steps
    assert "--all" not in steps



def test_current_development_includes_the_suite_and_only_three_replay_exclusions(tmp_path: Path) -> None:
    class Verify:
        @staticmethod
        def controlled_python(*args):
            return ["python", "-P", "-s", "-B", *args]

    command = verify_linux.current_test_command(Verify, tmp_path)
    assert command[-1] == "tests"
    assert {item.removeprefix("--deselect=") for item in command if item.startswith("--deselect=")} == {
        "tests/test_dark_medium_response_benchmark.py::test_retained_evaluation_reproduces_with_frozen_sources",
        "tests/test_linux_runtime.py::test_retained_benchmark_linux_bytes_and_historical_scientific_equivalence",
        "tests/test_numerical_regressions.py::ScopedClaimControls::test_CORE08_repeatable_explicit_run",
    }
    assert "--junitxml" in command
    assert "--basetemp" in command


@pytest.mark.parametrize("counts", [
    'tests="0" failures="0" errors="0" skipped="0"',
    'tests="3" failures="1" errors="0" skipped="0"',
    'tests="3" failures="0" errors="1" skipped="0"',
    'tests="3" failures="0" errors="0" skipped="1"',
    'tests="3" failures="-1" errors="0" skipped="0"',
    'tests="three" failures="0" errors="0" skipped="0"',
    'tests="3" failures="0" errors="0"',
])
def test_current_test_result_rejects_empty_failed_skipped_and_malformed_counts(
    tmp_path: Path, counts: str,
) -> None:
    report = tmp_path / "results.xml"
    report.write_text(f"<testsuites><testsuite {counts}/></testsuites>", encoding="utf-8")
    with pytest.raises(RuntimeError):
        verify_linux.require_current_test_result(report)


def test_current_test_result_accepts_real_nonempty_success(tmp_path: Path) -> None:
    report = tmp_path / "results.xml"
    report.write_text('<testsuites><testsuite tests="3" failures="0" errors="0" skipped="0"/></testsuites>',
                      encoding="utf-8")
    assert verify_linux.require_current_test_result(report) == {
        "tests": 3, "failures": 0, "errors": 0, "skipped": 0,
    }


@pytest.fixture
def current_index_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from tools import release_integrity

    root = tmp_path / "source"
    root.mkdir()
    (root / "README.md").write_bytes(b"current source\n")
    value = (root / "README.md").read_bytes()
    oid = hashlib.sha1(f"blob {len(value)}\0".encode() + value).hexdigest()
    record = {"entry": f"100644 {oid} 0\tREADME.md\0".encode()}
    monkeypatch.setattr(verify_linux, "ROOT", root)
    monkeypatch.setattr(release_integrity, "ROOT", root)

    def git(arguments, **_kwargs):
        if arguments == ["ls-files", "--stage", "-z"]:
            return record["entry"]
        if arguments == ["rev-parse", "HEAD"]:
            return "1" * 40 + "\n"
        if arguments == ["rev-parse", "HEAD^{tree}"]:
            return "2" * 40 + "\n"
        raise AssertionError(arguments)

    monkeypatch.setattr(release_integrity, "git", git)
    return root, record


def test_current_inventory_accepts_matching_index_and_preserves_manifest_semantics(current_index_fixture) -> None:
    root, _ = current_index_fixture
    paths, identity = verify_linux.current_source_inventory()
    assert paths == [root / "README.md"]
    assert identity["head"] == "1" * 40
    assert identity["head_tree"] == "2" * 40
    assert identity["files"]["README.md"]["sha256"] == hashlib.sha256(b"current source\n").hexdigest()
    assert not (root / "MANIFEST.sha256").exists()


@pytest.mark.parametrize("fault", ["changed", "extra", "missing", "unmerged", "symlink_mode", "traversal"])
def test_current_inventory_rejects_unindexed_or_unsafe_payload(current_index_fixture, fault: str) -> None:
    root, record = current_index_fixture
    verify_linux.current_source_inventory()  # Demonstrate a valid baseline first.
    if fault == "changed":
        (root / "README.md").write_bytes(b"changed")
    elif fault == "extra":
        (root / "unexpected.txt").write_bytes(b"extra")
    elif fault == "missing":
        (root / "README.md").unlink()
    elif fault == "unmerged":
        record["entry"] = record["entry"].replace(b" 0\t", b" 2\t")
    elif fault == "symlink_mode":
        record["entry"] = record["entry"].replace(b"100644", b"120000")
    else:
        record["entry"] = record["entry"].replace(b"README.md", b"../README.md")
    with pytest.raises((OSError, RuntimeError)):
        verify_linux.current_source_inventory()



@pytest.mark.parametrize(("extra", "tag_context", "message"), [
    (["--all"], False, "cannot combine"),
    (["--runtime-only"], False, "cannot combine"),
    ([], True, "does not authorize a tag-event"),
])
def test_current_development_cli_rejects_replay_combinations_and_tag_context(
    extra: list[str], tag_context: bool, message: str,
) -> None:
    environment = dict(os.environ)
    environment.pop("GITHUB_REF", None)
    environment.pop("GITHUB_REF_TYPE", None)
    if tag_context:
        environment.update(GITHUB_REF="refs/tags/v1.0.7", GITHUB_REF_TYPE="tag")
    completed = subprocess.run(
        [sys.executable, "-I", "-B", str(ROOT / "tools/verify_linux.py"),
         "--current-development", *extra],
        cwd=ROOT, env=environment, capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 2
    assert message in completed.stderr



def test_current_development_bootstrap_uses_separate_binary_only_hash_lock() -> None:
    from tools.bootstrap_linux import development_dependency_command

    command = development_dependency_command(Path("/private/python"))
    assert command[:6] == [str(Path("/private/python")), "-I", "-B", "-m", "pip", "install"]
    assert "--require-hashes" in command
    assert "--only-binary=:all:" in command
    assert command[-1] == str(ROOT / "requirements-development.txt")
    assert "requirements-lock.txt" not in " ".join(command)


def test_current_development_dependency_drift_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    versions = {"sympy": "1.14.0", "mpmath": "1.3.0"}
    monkeypatch.setattr(verify_linux.importlib.metadata, "version", versions.__getitem__)
    verify_linux.verify_current_development_dependencies()
    versions["sympy"] = "1.13.0"
    with pytest.raises(RuntimeError, match="dependency version differs: sympy"):
        verify_linux.verify_current_development_dependencies()
