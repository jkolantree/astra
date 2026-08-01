"""Canonical deterministic replay for every released scientific output."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(script: str, *arguments: str, environment: dict[str, str]) -> None:
    command = [sys.executable, str(ROOT / "scripts" / script), *arguments]
    subprocess.run(command, cwd=ROOT, env=environment, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.workers < 1:
        raise ValueError("workers must be positive")

    environment = os.environ.copy()
    python_path = [str(ROOT / "src"), str(ROOT)]
    if environment.get("PYTHONPATH"):
        python_path.append(environment["PYTHONPATH"])
    environment.update(
        {
            "PYTHONHASHSEED": "0",
            "TZ": "UTC",
            "SOURCE_DATE_EPOCH": "1785542400",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "MPLBACKEND": "Agg",
            "MPLCONFIGDIR": str(ROOT / "tmp" / "matplotlib"),
            "TEMP": str(ROOT / "tmp"),
            "TMP": str(ROOT / "tmp"),
            "TMPDIR": str(ROOT / "tmp"),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": os.pathsep.join(python_path),
        }
    )
    (ROOT / "tmp" / "matplotlib").mkdir(parents=True, exist_ok=True)

    run("generate_astra_figures.py", environment=environment)
    run("synthetic_topology_benchmark.py", environment=environment)
    run(
        "benchmark_ensemble.py",
        "--seeds",
        "64",
        "--seed-start",
        "20260801",
        "--workers",
        str(args.workers),
        environment=environment,
    )
    print("Reproduced every released scientific data and figure artifact.")


if __name__ == "__main__":
    main()
