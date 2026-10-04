"""Negative controls for Linux migration and its scientific/byte boundaries."""
from __future__ import annotations

import importlib.util
import json
import platform
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
def test_replay_records_failure_without_overwriting_historical_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, unstable: bool
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

    monkeypatch.setattr(verify_linux.subprocess, "run", build)
    with pytest.raises(RuntimeError, match="not byte-identical" if unstable else "Scientific numeric drift"):
        verify_linux.replay({}, 4)
    report = json.loads((root / "tmp/linux-verification.json").read_text())
    assert report["classification"] == "blocked_linux_migration"
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
    assert "bootstrap_linux.py" in steps
    assert "verify.py --all --workers 4" in steps
