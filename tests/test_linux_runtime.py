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
