"""Canonical deterministic replay for every released scientific output."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def is_link_or_junction(path: Path) -> bool:
    junction_check = getattr(path, "is_junction", None)
    return path.is_symlink() or bool(junction_check and junction_check())


def ensure_safe_directory(path: Path) -> None:
    try:
        relative = path.relative_to(ROOT)
    except ValueError as exc:
        raise RuntimeError(f"Output path is outside the repository: {path}") from exc
    expected = ROOT.resolve().joinpath(*relative.parts)
    current = ROOT
    for part in relative.parts:
        current /= part
        if is_link_or_junction(current):
            raise RuntimeError(f"Unsafe symbolic link or junction in output path: {current}")
        if current != path and current.exists() and not current.is_dir():
            raise RuntimeError(f"Non-directory component in output path: {current}")
    if path.resolve() != expected:
        raise RuntimeError(f"Output path resolves outside its expected location: {path}")
    if path.exists() and not path.is_dir():
        raise RuntimeError(f"Expected output directory but found a non-directory: {path}")
    path.mkdir(parents=True, exist_ok=True)
    if is_link_or_junction(path) or path.resolve() != expected:
        raise RuntimeError(f"Unsafe output directory after creation: {path}")


def run(script: str, *arguments: str, environment: dict[str, str]) -> None:
    command = [
        sys.executable,
        "-P",
        "-s",
        "-B",
        str(ROOT / "scripts" / script),
        *arguments,
    ]
    subprocess.run(command, cwd=ROOT, env=environment, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.workers < 1:
        raise ValueError("workers must be positive")

    environment = os.environ.copy()
    for name in tuple(environment):
        if name.startswith(("PYTHON", "PYTEST")):
            environment.pop(name)
    runtime = json.loads((ROOT / "RUNTIME.json").read_text(encoding="utf-8"))
    release_spec = json.loads((ROOT / "RELEASE_SPEC.json").read_text(encoding="utf-8"))
    numeric_kernel = runtime["numeric_kernel"]
    core_type = str(numeric_kernel["core_type"])
    threads = str(numeric_kernel["threads"])
    environment.update(
        {
            "PYTHONHASHSEED": "0",
            "TZ": "UTC",
            "SOURCE_DATE_EPOCH": str(release_spec["build_epoch_unix"]),
            "OPENBLAS_CORETYPE": core_type,
            "OMP_NUM_THREADS": threads,
            "OPENBLAS_NUM_THREADS": threads,
            "MKL_NUM_THREADS": threads,
            "NUMEXPR_NUM_THREADS": threads,
            "NPY_DISABLE_CPU_FEATURES": ",".join(
                runtime["numeric_kernel"]["numpy_disabled_cpu_features"]
            ),
            "MPLBACKEND": "Agg",
            "MPLCONFIGDIR": str(ROOT / "tmp" / "matplotlib"),
            "TEMP": str(ROOT / "tmp"),
            "TMP": str(ROOT / "tmp"),
            "TMPDIR": str(ROOT / "tmp"),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPYCACHEPREFIX": str(ROOT / "tmp" / "pycache"),
        }
    )
    ensure_safe_directory(ROOT / "tmp")
    ensure_safe_directory(ROOT / "tmp" / "matplotlib")
    ensure_safe_directory(ROOT / "tmp" / "pycache")

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
