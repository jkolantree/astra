"""Install hash-pinned Linux tools locally; never modify the host configuration."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def download(record: dict, destination: Path) -> Path:
    path = destination / record["asset"]
    if not path.exists():
        with urllib.request.urlopen(record["source"], timeout=120) as response:
            payload = response.read()
        if hashlib.sha256(payload).hexdigest() != record["sha256"]:
            raise RuntimeError("Downloaded archive digest mismatch")
        path.write_bytes(payload)
    if hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
        raise RuntimeError("Cached archive digest mismatch")
    return path


def main() -> None:
    if not sys.flags.isolated or not sys.dont_write_bytecode:
        raise RuntimeError("Use python3 -I -B tools/bootstrap_linux.py")
    runtime = json.loads((ROOT / "RUNTIME-linux.json").read_text())
    destination = ROOT / "tmp/linux-bootstrap"
    # Reuse the controller's path checks before writing or extracting anything.
    sys.path.insert(0, str(ROOT))
    from tools.verify import ensure_safe_directory

    for directory in (destination, destination / "python", destination / "git"):
        ensure_safe_directory(directory)
    archive = download(runtime["reference_distribution"], destination)
    with tarfile.open(archive) as bundle:
        bundle.extractall(destination, filter="data")
    git_archive = download(runtime["git"], destination)
    subprocess.run(["dpkg-deb", "--extract", str(git_archive), str(destination / "git")], check=True)
    python = destination / "python/bin/python3.12"
    for executable, expected in (
        (python, runtime["reference_distribution"]["executable_sha256"]),
        (destination / "git/usr/bin/git", runtime["git"]["executable_sha256"]),
    ):
        if hashlib.sha256(executable.read_bytes()).hexdigest() != expected:
            raise RuntimeError("Extracted executable digest mismatch")
    venv = ROOT / ".venv"
    ensure_safe_directory(venv)
    subprocess.run([str(python), "-I", "-B", "-m", "venv", str(venv)], check=True)
    python = venv / "bin/python"
    subprocess.run([
        str(python), "-I", "-B", "-m", "pip", "install", "--require-hashes",
        "-r", str(ROOT / "requirements-lock.txt"),
    ], check=True)
    environment = os.environ.copy()
    environment["PLAYWRIGHT_BROWSERS_PATH"] = str(ROOT / "tmp/linux-browsers")
    subprocess.run([str(python), "-I", "-B", "-m", "playwright", "install", "chromium"],
                   env=environment, check=True)
    print("Linux tools installed locally. Run .venv/bin/python -I -B tools/verify.py.")


if __name__ == "__main__":
    main()
