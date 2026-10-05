"""Verify Linux research v1 independently of the historical Windows comparison.

This controller never records or updates expected hashes. Baseline changes require
an explicitly reviewed successor record, not regeneration of expected values.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "evidence/linux-research-v1.json"


def check_outputs(expected: dict[str, str], observed: dict[str, str]) -> None:
    if expected.keys() != observed.keys():
        raise RuntimeError("Linux baseline output inventory changed")
    changed = [name for name in expected if expected[name] != observed[name]]
    if changed:
        raise RuntimeError("Linux baseline byte drift: " + ", ".join(changed))


def check_replay_tree(
    directory: Path, original: dict[str, str], outputs: set[str]
) -> None:
    """Reject extra files and changes to copied source, not just output hash drift."""
    from tools.check_repository import IGNORED_NAMES
    from tools.verify_linux import digest

    actual = set()
    for path in directory.rglob("*"):
        relative = path.relative_to(directory)
        if any(part in IGNORED_NAMES for part in relative.parts):
            continue
        if path.is_symlink():
            raise RuntimeError("Linux replay contains a symbolic link")
        if path.is_file():
            actual.add(relative.as_posix())
    if actual != original.keys():
        raise RuntimeError("Linux replay file inventory changed")
    for name in actual - outputs:
        if digest(directory / name) != original[name]:
            raise RuntimeError("Linux replay modified copied source: " + name)


def main() -> None:
    if not sys.flags.isolated or not sys.dont_write_bytecode:
        raise RuntimeError("Run with -I -B")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="Refit and render twice in isolation")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.workers != 4:
        raise ValueError("Linux research v1 fixes the worker count at four")
    sys.path.insert(0, str(ROOT))
    from tools import verify_linux

    record = json.loads(RECORD.read_text())
    if record["baseline_id"] != "linux-research-v1":
        raise RuntimeError("Unexpected Linux baseline identity")
    for name, expected in record["source_sha256"].items():
        verify_linux.require_digest(ROOT / name, expected)
    subprocess.run([sys.executable, "-I", "-B", str(ROOT / "tools/verify.py")], check=True)
    if not args.all:
        print("Linux research v1 source/runtime/development checks passed; replay not exercised.")
        return
    _, environment = verify_linux.configure()
    from tools.check_repository import public_files

    original = {p.relative_to(ROOT).as_posix(): verify_linux.digest(p) for p in public_files()}
    report = verify_linux.replay(environment, args.workers, historical_required=False)
    try:
        check_replay_tree(ROOT / report["replay_directory"], original, set(record["output_sha256"]))
        report["staged_inventory_and_sources_unchanged"] = True
        check_outputs(record["output_sha256"], report["linux_output_sha256"])
    except RuntimeError as error:
        report["linux_baseline_gate"] = "FAIL"
        report["baseline_error"] = str(error)
        raise
    else:
        report["linux_baseline_gate"] = "PASS"
    finally:
        report["baseline_id"] = record["baseline_id"]
        report["baseline_record_sha256"] = verify_linux.digest(RECORD)
        (ROOT / "tmp/linux-baseline-verification.json").write_text(
            json.dumps(report, indent=2) + "\n"
        )
    print("Linux research v1 byte gate passed. Historical scientific comparison: "
          + report["historical_scientific_equivalence"] + ". No publication authorized.")


if __name__ == "__main__":
    main()
