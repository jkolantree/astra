"""The companion admission cannot replace scientific pins or relax v1 outputs."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tools import verify_linux_companion as companion

ROOT = Path(__file__).resolve().parents[1]


def source_tree(tmp_path: Path) -> Path:
    baseline = json.loads((ROOT / companion.PREDECESSOR).read_text())
    names = set(baseline["source_sha256"]) | companion.ADDITIONAL_INPUTS | {
        companion.RECORD, companion.PREDECESSOR,
    }
    for name in names:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    return tmp_path


def test_admission_preserves_original_runtime_science_and_output_authority() -> None:
    baseline = companion.check_sources()
    assert baseline == json.loads((ROOT / companion.PREDECESSOR).read_text())
    assert len(baseline["source_sha256"]) == 46
    assert len(baseline["output_sha256"]) == 57
    for name in ("pyproject.toml", "RUNTIME.json", "RUNTIME-linux.json",
                 "requirements-lock.txt", "tools/verify_linux_baseline.py"):
        companion.require_digest(ROOT / name, baseline["source_sha256"][name])


@pytest.mark.parametrize("fault", [
    "predecessor_bytes", "predecessor_identity", "admission_identity",
    "missing_replacement", "scientific_replacement", "runtime_replacement",
    "replacement_predecessor", "replacement_digest", "replacement_reason",
    "missing_additional", "extra_additional", "output_override", "missing_source",
    "changed_science", "changed_runtime", "changed_operational", "changed_lint",
    "changed_controller", "source_link", "record_link",
])
def test_source_admission_rejects_unauthorized_changes(tmp_path: Path, fault: str) -> None:
    root = source_tree(tmp_path)
    record_path = root / companion.RECORD
    record = json.loads(record_path.read_text())
    operational = "tools/check_pages_admission.py"
    if fault == "predecessor_bytes":
        (root / companion.PREDECESSOR).write_text("{}")
    elif fault == "predecessor_identity":
        record["predecessor"]["sha256"] = "0" * 64
    elif fault == "admission_identity":
        record["admission_id"] = "unreviewed"
    elif fault == "missing_replacement":
        del record["source_replacements"][operational]
    elif fault in {"scientific_replacement", "runtime_replacement"}:
        path = "src/sppt_core.py" if fault == "scientific_replacement" else "RUNTIME-linux.json"
        record["source_replacements"][path] = record["source_replacements"][operational]
    elif fault.startswith("replacement_"):
        field = {"replacement_predecessor": "predecessor_sha256",
                 "replacement_digest": "sha256", "replacement_reason": "reason"}[fault]
        record["source_replacements"][operational][field] = " " if field == "reason" else "0" * 64
    elif fault == "missing_additional":
        del record["additional_source_sha256"]["ruff.toml"]
    elif fault == "extra_additional":
        record["additional_source_sha256"]["../unexpected"] = "0" * 64
    elif fault == "output_override":
        record["output_sha256"] = {}
    elif fault == "missing_source":
        (root / operational).unlink()
    elif fault.startswith("changed_"):
        path = {
            "changed_science": "src/sppt_core.py", "changed_runtime": "pyproject.toml",
            "changed_operational": operational, "changed_lint": "ruff.toml",
            "changed_controller": "tools/verify_linux_companion.py",
        }[fault]
        with (root / path).open("ab") as handle:
            handle.write(b"\n# changed\n")
    elif fault == "source_link":
        target = root / operational
        copy = root / "same-bytes.py"
        target.rename(copy)
        target.symlink_to(copy)
    record_path.write_text(json.dumps(record))
    if fault == "record_link":
        copy = root / "same-record.json"
        record_path.rename(copy)
        record_path.symlink_to(copy)
    with pytest.raises(RuntimeError):
        companion.check_sources(root)


@pytest.mark.parametrize("name,expected", [
    ("resources/sppt-scm-research-companion/draft-v0.1.0/package/visuals/scientific/generate_scientific_atlas.py", 0),
    ("src/astra_reservoir.py", 1),
    ("resources/sppt-scm-research-companion/draft-v0.1.0/package/visuals/scientific/neighbor.py", 1),
])
def test_supplier_lint_exception_does_not_leak_to_other_files(name: str, expected: int) -> None:
    result = subprocess.run(
        [sys.executable, "-B", "-m", "ruff", "check", "--no-cache", "--output-format", "json",
         "--stdin-filename", name, "-"],
        input="import os\n", capture_output=True, text=True, cwd=ROOT, check=False,
    )
    assert result.returncode == expected, result.stderr
    assert {item["code"] for item in json.loads(result.stdout)} == ({"F401"} if expected else set())


def test_supplier_still_rejects_rules_outside_its_existing_exception() -> None:
    name = "resources/sppt-scm-research-companion/draft-v0.1.0/package/visuals/scientific/generate_scientific_atlas.py"
    result = subprocess.run(
        [sys.executable, "-B", "-m", "ruff", "check", "--no-cache", "--output-format", "json",
         "--stdin-filename", name, "-"],
        input="print(undefined_name)\n", capture_output=True, text=True, cwd=ROOT, check=False,
    )
    assert result.returncode == 1, result.stderr
    assert {item["code"] for item in json.loads(result.stdout)} == {"F821"}
