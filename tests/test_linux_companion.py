"""The companion admission cannot replace scientific pins or relax v1 outputs."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools import verify_linux_companion as companion

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def admitted_source_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, dict]:
    """Synthetic byte/roster controls only; these files confer no source admission.

    Only the fixture's predecessor trust anchor is substituted, and pytest restores
    it afterward. Production hashing, inventory, and link checks remain real.
    No synthetic source is imported or executed; retained repository records are
    read without modification, including all 57 scientific-output pins.
    """
    baseline = json.loads((ROOT / companion.PREDECESSOR).read_text(encoding="utf-8"))
    names = set(baseline["source_sha256"]) | companion.ADDITIONAL_INPUTS
    payload = {name: f"synthetic predecessor source: {name}\n".encode() for name in names}
    baseline["source_sha256"] = {
        name: hashlib.sha256(payload[name]).hexdigest()
        for name in baseline["source_sha256"]
    }
    replacements = {}
    for name in sorted(companion.REPLACEMENTS):
        payload[name] = f"synthetic operational replacement: {name}\n".encode()
        replacements[name] = {
            "predecessor_sha256": baseline["source_sha256"][name],
            "sha256": hashlib.sha256(payload[name]).hexdigest(),
            "reason": "Synthetic test fixture; no runtime or scientific authority.",
        }
    baseline_bytes = (json.dumps(baseline, sort_keys=True) + "\n").encode()
    predecessor_digest = hashlib.sha256(baseline_bytes).hexdigest()
    record = {
        "admission_id": companion.ADMISSION_ID,
        "predecessor": {"path": companion.PREDECESSOR, "sha256": predecessor_digest},
        "source_replacements": replacements,
        "additional_source_sha256": {
            name: hashlib.sha256(payload[name]).hexdigest()
            for name in sorted(companion.ADDITIONAL_INPUTS)
        },
    }
    payload[companion.PREDECESSOR] = baseline_bytes
    payload[companion.RECORD] = (json.dumps(record, sort_keys=True) + "\n").encode()
    for name, data in payload.items():
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    monkeypatch.setattr(companion, "PREDECESSOR_SHA256", predecessor_digest)
    return tmp_path, baseline


def test_synthetic_source_admission_accepts_exact_fixture(admitted_source_tree) -> None:
    root, expected = admitted_source_tree
    baseline = companion.check_sources(root)
    assert baseline == expected
    retained = json.loads((ROOT / companion.PREDECESSOR).read_text(encoding="utf-8"))
    assert baseline["output_sha256"] == retained["output_sha256"]
    assert len(baseline["source_sha256"]) == 46
    assert len(baseline["output_sha256"]) == 57


def test_historical_admission_remains_frozen_and_rejects_current_successor() -> None:
    predecessor = (ROOT / companion.PREDECESSOR).read_bytes()
    record = (ROOT / companion.RECORD).read_bytes()
    assert hashlib.sha256(predecessor).hexdigest() == companion.PREDECESSOR_SHA256
    baseline = json.loads(predecessor)
    assert len(baseline["source_sha256"]) == 46
    assert len(baseline["output_sha256"]) == 57
    for name in ("pyproject.toml", "RUNTIME.json", "RUNTIME-linux.json",
                 "requirements-lock.txt", "tools/verify_linux_baseline.py"):
        companion.require_digest(ROOT / name, baseline["source_sha256"][name])
    changed = ROOT / "scripts/make_figures.py"
    assert hashlib.sha256(changed.read_bytes()).hexdigest() != baseline["source_sha256"][
        "scripts/make_figures.py"
    ]
    with pytest.raises(
        RuntimeError, match=r"^Operational-source byte identity mismatch: make_figures\.py$",
    ):
        companion.check_sources()
    assert (ROOT / companion.PREDECESSOR).read_bytes() == predecessor
    assert (ROOT / companion.RECORD).read_bytes() == record


@pytest.mark.parametrize("fault,message", [
    ("predecessor_bytes", r"byte identity mismatch: linux-research-v1\.json$"),
    ("predecessor_identity", "predecessor or admission identity changed"),
    ("admission_identity", "predecessor or admission identity changed"),
    ("missing_replacement", "replacement inventory is malformed"),
    ("scientific_replacement", "replacement inventory is malformed"),
    ("runtime_replacement", "replacement inventory is malformed"),
    ("replacement_predecessor", "replacement predecessor changed"),
    ("replacement_digest", r"byte identity mismatch: check_pages_admission\.py$"),
    ("replacement_reason", "replacement reason must be stated"),
    ("missing_additional", "additional source inventory is malformed"),
    ("extra_additional", "additional source inventory is malformed"),
    ("output_override", "record inventory is malformed"),
    ("missing_source", r"byte identity mismatch: check_pages_admission\.py$"),
    ("changed_science", r"byte identity mismatch: sppt_core\.py$"),
    ("changed_runtime", r"byte identity mismatch: pyproject\.toml$"),
    ("changed_operational", r"byte identity mismatch: check_pages_admission\.py$"),
    ("changed_lint", r"byte identity mismatch: ruff\.toml$"),
    ("changed_controller", r"byte identity mismatch: verify_linux_companion\.py$"),
    ("source_link", "Operational-source inputs must not use links"),
    ("record_link", "Operational-source inputs must not use links"),
])
def test_source_admission_rejects_unauthorized_changes(
    admitted_source_tree, fault: str, message: str,
) -> None:
    root, expected = admitted_source_tree
    # Each negative trial must first demonstrate a fully valid starting state.
    assert companion.check_sources(root) == expected
    record_path = root / companion.RECORD
    record = json.loads(record_path.read_text(encoding="utf-8"))
    operational = "tools/check_pages_admission.py"
    if fault == "predecessor_bytes":
        (root / companion.PREDECESSOR).write_text("{}", encoding="utf-8")
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
    record_path.write_text(json.dumps(record), encoding="utf-8")
    if fault == "record_link":
        copy = root / "same-record.json"
        record_path.rename(copy)
        record_path.symlink_to(copy)
    with pytest.raises(RuntimeError, match=message):
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
