"""Explicit-output wrapper for the unchanged reviewed SCM replay."""

import argparse
import json
from pathlib import Path

import scm_replay_checks as replay_checks


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump({"status": "RUNNING"}, stream)
        stream.flush()
        result = replay_checks.run_checks()
        if result.get("total_checks") != 9 or len(result.get("checks", [])) != 9:
            raise ValueError("Exactly the nine reviewed SCM check families are required")
        status = "PASS" if all(c.get("passed") is True for c in result["checks"]) else "FAIL"
        if result["status"] != status:
            raise ValueError("Inconsistent SCM status")
        stream.seek(0)
        stream.truncate()
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(
        json.dumps({"status": status, "passed_checks": result["passed_checks"], "total_checks": 9})
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
