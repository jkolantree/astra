"""Verify the companion's operational sources against unchanged Linux v1 science.

This explicit admission does not rewrite or fall back from the historical v1
contract. Runtime, scientific sources and expected outputs retain v1 identities.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RECORD = "evidence/linux-companion-sources-v1.json"
ADMISSION_ID = "linux-companion-sources-v1"
PREDECESSOR = "evidence/linux-research-v1.json"
PREDECESSOR_SHA256 = "f261262b55b0d44cfd5f46c8f6823a89489d803ca8cb685f22b60833fff35078"
REPLACEMENTS = {
    "tools/build_pages_admission.py",
    "tools/check_pages_admission.py",
    "tools/check_repository.py",
}
ADDITIONAL_INPUTS = {
    ".github/workflows/verify.yml",
    "LICENSE_MAP.md",
    "REPRODUCING.md",
    "evidence/linux-companion-sources-v1.md",
    "ruff.toml",
    "tests/test_linux_companion.py",
    "tests/test_linux_runtime.py",
    "tools/verify_linux_companion.py",
}


def read_input(path: Path) -> bytes:
    for part in (path, *path.parents):
        if part.is_symlink() or part.is_junction():
            raise RuntimeError("Operational-source inputs must not use links")
    return path.read_bytes()


def require_digest(path: Path, expected: object) -> None:
    if not isinstance(expected, str) or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
        raise RuntimeError("Operational-source digest is malformed")
    if not path.is_file() or hashlib.sha256(read_input(path)).hexdigest() != expected:
        raise RuntimeError(f"Operational-source byte identity mismatch: {path.name}")


def exact_object(value: object, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise RuntimeError(f"Operational-source {label} inventory is malformed")
    return value


def check_sources(root: Path = ROOT) -> dict[str, Any]:
    # Validate the historical record before trusting any inherited source/output
    # hash. The new record can replace only the three explicit operational paths.
    require_digest(root / PREDECESSOR, PREDECESSOR_SHA256)
    baseline = json.loads((root / PREDECESSOR).read_text())
    record = exact_object(json.loads(read_input(root / RECORD)), {
        "admission_id", "predecessor", "source_replacements", "additional_source_sha256",
    }, "record")
    if record["admission_id"] != ADMISSION_ID or record["predecessor"] != {
        "path": PREDECESSOR, "sha256": PREDECESSOR_SHA256,
    }:
        raise RuntimeError("Operational-source predecessor or admission identity changed")
    replacements = exact_object(record["source_replacements"], REPLACEMENTS, "replacement")
    additional = exact_object(record["additional_source_sha256"], ADDITIONAL_INPUTS, "additional source")
    for name, item in replacements.items():
        item = exact_object(item, {"predecessor_sha256", "sha256", "reason"}, "replacement entry")
        if item["predecessor_sha256"] != baseline["source_sha256"][name]:
            raise RuntimeError("Operational-source replacement predecessor changed")
        if not isinstance(item["reason"], str) or not item["reason"].strip():
            raise RuntimeError("Operational-source replacement reason must be stated")
    for name, expected in baseline["source_sha256"].items():
        if name in replacements:
            expected = replacements[name]["sha256"]
        require_digest(root / name, expected)
    for name, expected in additional.items():
        require_digest(root / name, expected)
    return baseline


def main() -> None:
    if not sys.flags.isolated or not sys.dont_write_bytecode:
        raise RuntimeError("Run with -I -B")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="Refit and render twice in isolation")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.workers != 4:
        raise ValueError("Linux research v1 fixes the worker count at four")
    baseline = check_sources()
    sys.path.insert(0, str(ROOT))
    from tools import verify_linux
    from tools.verify_linux_baseline import check_outputs, check_replay_tree

    # The original runtime, full development suite and clean/archive gates run
    # without overrides, bypass flags, replacement tools or relaxed tolerances.
    subprocess.run([sys.executable, "-I", "-B", str(ROOT / "tools/verify.py")], check=True)
    if not args.all:
        print(f"{ADMISSION_ID} development checks passed; Linux v1 replay not exercised.")
        return
    _, environment = verify_linux.configure()
    from tools.check_repository import public_files

    original = {p.relative_to(ROOT).as_posix(): verify_linux.digest(p) for p in public_files()}
    report = verify_linux.replay(environment, args.workers, historical_required=False)
    try:
        check_replay_tree(ROOT / report["replay_directory"], original, set(baseline["output_sha256"]))
        report["staged_inventory_and_sources_unchanged"] = True
        check_outputs(baseline["output_sha256"], report["linux_output_sha256"])
    except RuntimeError as error:
        report["linux_baseline_gate"] = "FAIL"
        report["baseline_error"] = str(error)
        raise
    else:
        report["linux_baseline_gate"] = "PASS"
    finally:
        report["baseline_id"] = baseline["baseline_id"]
        report["baseline_record_sha256"] = PREDECESSOR_SHA256
        report["source_admission_id"] = ADMISSION_ID
        report["source_admission_sha256"] = verify_linux.digest(ROOT / RECORD)
        (ROOT / "tmp/linux-companion-verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"{ADMISSION_ID}: Linux v1 output byte gate passed. Historical scientific comparison: "
          + report["historical_scientific_equivalence"] + ". No publication authorized.")


if __name__ == "__main__":
    main()
