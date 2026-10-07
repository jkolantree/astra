"""Private new-edition freshness experiment, not a release-admission controller.

Use two separate input-only directories. No expected output bytes are copied.
Historical source gates and comparisons are never rewritten by this tool.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import shutil
import signal
import stat
import subprocess
from pathlib import Path, PurePosixPath

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[1]
PREFIX = "resources/integrated-edition-proposal/"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_path(root: Path, name: str) -> Path:
    parts = PurePosixPath(name).parts
    require(bool(parts) and not name.startswith("/") and "\\" not in name
            and ":" not in name and all(x not in {"", ".", ".."} for x in parts)
            and PurePosixPath(name).as_posix() == name, "Unsafe member: " + name)
    current = root
    require(not root.is_symlink(), "Linked root")
    for part in parts:
        current /= part
        require(not current.is_symlink(), "Linked member: " + name)
    return current


def files(root: Path, *, repository: bool = False) -> dict[str, str]:
    result = {}
    for base, dirs, names in os.walk(root, followlinks=False):
        if repository and Path(base) == root:
            dirs[:] = [d for d in dirs if d != ".git"]
        for d in dirs:
            require(not (Path(base)/d).is_symlink(), "Linked directory")
        for name in names:
            p = Path(base)/name
            rel = p.relative_to(root).as_posix()
            safe_path(root, rel)
            s = p.lstat()
            require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1, "Nonregular or linked file: " + rel)
            result[rel] = digest(p)
    return result


def source_inventory() -> dict[str, str]:
    result = {}
    for line in (ROOT/"MANIFEST.sha256").read_text().splitlines():
        h, name = line.split("  ", 1)
        safe_path(ROOT, name)
        require(name not in result and len(h) == 64, "Bad source manifest")
        result[name] = h
    result["MANIFEST.sha256"] = digest(ROOT/"MANIFEST.sha256")
    require(files(ROOT, repository=True) == result, "Source tree differs from manifest")
    return result


def prepare_stage(stage: Path, inputs: dict[str, str], outputs: set[str]) -> None:
    require(not stage.exists() and not stage.is_symlink(), "Stage already exists")
    stage.mkdir(parents=True)
    for n, h in sorted(inputs.items()):
        p = safe_path(stage, n); p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(safe_path(ROOT, n), p)
        require(digest(p) == h, "Copy changed input")
    require(not any(safe_path(stage, n).exists() for n in outputs), "Output existed before run")
    require(files(stage) == inputs, "Stage not input-only")


def audit_stage(stage: Path, inputs: dict[str, str], outputs: set[str]) -> dict[str, str]:
    # Legacy builders write caches only beneath tmp; caches are recorded privately
    # and never treated as public inputs or outputs. Validate links there too.
    all_files = files(stage)
    public = {n: h for n, h in all_files.items() if not n.startswith("tmp/")}
    require(public.keys() == inputs.keys() | outputs, "Missing or extra public output")
    require(all(public[n] == h for n, h in inputs.items()), "Source/input mutation")
    return {n: public[n] for n in sorted(outputs)}


def child(python: str, stage: Path, env: dict[str, str], script: str,
          args: list[str], log: Path, *, timeout: float = 1200) -> None:
    command = [python, "-I", "-B", "-c",
               "import runpy,sys;sys.path[:0]=[sys.argv[1],sys.argv[1]+'/src',"
               "sys.argv[1]+'/scripts'];p=sys.argv[2];sys.argv=sys.argv[2:];"
               "runpy.run_path(p,run_name='__main__')",
               str(stage), str(stage/script), *args]
    with log.open("xb") as stream:
        process = subprocess.Popen(command, cwd=stage, env=env, stdin=subprocess.DEVNULL,
                                   stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = process.wait(timeout=timeout)
        except BaseException:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise
        if code:
            raise subprocess.CalledProcessError(code, command)


def save_receipt(work: Path, receipt: dict) -> None:
    name = work/"freshness-receipt.json"
    if name.exists() or name.is_symlink():
        s = name.lstat()
        require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1, "Unsafe receipt")
    temporary = work/"freshness-receipt.json.new"
    with temporary.open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True); stream.write("\n")
    temporary.replace(name)


def runtime_check(python: str, expected: dict) -> None:
    require(digest(Path(python).resolve()) == expected["executable_sha256"], "Interpreter hash mismatch")
    base_library = Path(python).resolve().parent.parent/"lib/libpython3.12.so.1.0"
    require(digest(base_library) == expected["libpython_sha256"], "libpython hash mismatch")
    actual = json.loads(subprocess.check_output([python, "-I", "-B", "-c",
        "import json,platform,importlib.metadata as m;print(json.dumps({'python':platform.python_version(),"
        "'packages':{x.metadata['Name'].lower().replace('_','-'):x.version for x in m.distributions()}}))"], text=True))
    require(actual["python"] == expected["python"] and actual["packages"] == expected["packages"],
            "Installed runtime metadata differs")
    # Full installed-file inventory is bound independently by the local runner.


def run(args: argparse.Namespace, receipt: dict) -> None:
    spec = json.loads((PACKAGE/"OUTPUTS.json").read_text())
    outputs = set(spec["outputs"])
    require(len(outputs) == len(spec["outputs"]) == 61, "Exact 61-output proposal required")
    excluded = set(spec["excluded_historical_outputs"])
    require(len(excluded) == 26 and outputs.isdisjoint(excluded), "Edition inventories overlap")
    before = source_inventory()
    require(not outputs.intersection(before) - set(spec["classes"]["retained_science_atlas"]),
            "New output bytes must not be source inputs")
    inputs = {n:h for n,h in before.items() if n not in outputs | excluded}
    runtime = json.loads((PACKAGE/"RUNTIME_PROPOSAL.json").read_text())
    runtime_check(args.science_python, runtime["science"])
    runtime_check(args.wki_python, runtime["wki"])
    receipt.update(source_sha256=before, input_files=len(inputs), outputs=sorted(outputs),
                   omitted_historical_schematics=sorted(excluded), passes=[])
    rt = json.loads((ROOT/"RUNTIME-linux.json").read_text())
    maps = []
    for number in (1, 2):
        stage = args.work / f"pass-{number}"
        prepare_stage(stage, inputs, outputs)
        record = {"pass":number,"outputs_present_before":0,"status":"RUNNING"}
        receipt["passes"].append(record)
        env = dict(os.environ)
        for key in list(env):
            if key.startswith(("PYTHON", "PYTEST")) or key in {"VIRTUAL_ENV", "MPLCONFIGDIR"}:
                env.pop(key)
        cache = stage/"tmp"; cache.mkdir()
        env.update(PYTHONHASHSEED="0", PYTHONDONTWRITEBYTECODE="1", TZ="UTC",
                   SOURCE_DATE_EPOCH="946684800", OPENBLAS_CORETYPE="HASWELL",
                   OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1",
                   NUMEXPR_NUM_THREADS="1", MPLBACKEND="Agg", MPLCONFIGDIR=str(cache/"mpl"),
                   TMPDIR=str(cache), TMP=str(cache), TEMP=str(cache),
                   XDG_CACHE_HOME=str(cache/"cache"), XDG_CONFIG_HOME=str(cache/"config"),
                   XDG_DATA_HOME=str(cache/"data"),
                   NPY_DISABLE_CPU_FEATURES=",".join(rt["numeric_kernel"]["numpy_disabled_cpu_features"]))
        generated = stage/PREFIX/"generated"; generated.mkdir()
        commands = [
            (args.science_python, "scripts/make_figures.py", ["--workers", "4"]),
            (args.science_python, "tools/build_dark_medium_response_atlas_documents.py", ["--no-identity", "--linux-layout"]),
            (args.science_python, "src/integrated_case.py", ["--case", "data/integrated-core/integrated_case.json", "--output", str(generated/"integrated-case.json")]),
            (args.science_python, "scripts/run_scm_checks.py", ["--output", str(generated/"scm-checks.json")]),
            (args.wki_python, "scripts/wki_check_algebra.py", ["--output", str(generated/"wki-checks.json")]),
            (args.science_python, PREFIX+"validate_reports.py", []),
            (args.science_python, PREFIX+"render_diagrams.py", []),
        ]
        for i, (py, script, arguments) in enumerate(commands):
            record.update(current_command=script, command_number=i+1)
            save_receipt(args.work, receipt)
            child(py, stage, env, script, arguments, args.work/f"pass-{number}-command-{i+1}.log")
        observed = audit_stage(stage, inputs, outputs)
        for n,h in spec["frozen_linux_comparison_sha256"].items():
            require(observed[n] == h, "Retained Linux output changed: " + n)
        require(files(ROOT, repository=True) == before, "Original source changed")
        record.update(status="PASS",fresh_output_count=len(observed),output_sha256=observed,
                      copied_input_sha256=inputs, retained_linux_31_byte_comparison="PASS")
        maps.append(observed)
        save_receipt(args.work, receipt)
    require(maps[0] == maps[1], "Fresh new-edition runs differ")
    runtime_check(args.science_python, runtime["science"])
    runtime_check(args.wki_python, runtime["wki"])
    receipt.update(status="PASS_PRIVATE_NEW_EDITION_FRESHNESS", two_fresh_runs_identical=True,
                   historical_57_gate="UNCHANGED_NOT_PASSED_BY_THIS_EXPERIMENT",
                   historical_windows_scientific_comparison="FAIL_PRESERVED_NOT_WAIVED")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--science-python", required=True)
    parser.add_argument("--wki-python", required=True)
    parser.add_argument("--work", type=Path, required=True)
    args = parser.parse_args()
    require(args.work.is_absolute() and not args.work.exists(), "New absolute work directory required")
    require(not args.work.is_relative_to(ROOT), "Work must be outside source tree")
    for p in [args.work, *args.work.parents]:
        require(not p.is_symlink(), "Linked work ancestor")
    args.work.mkdir(parents=True)
    receipt = {"status":"INCOMPLETE", "source_admitted":False, "runtime_admitted":False,
               "pages_admitted":False,"empirical_admission":False,"release_admitted":False}
    save_receipt(args.work, receipt)
    primary_error = None
    try:
        run(args, receipt)
    except BaseException as error:
        primary_error = error
        receipt.update(status="FAIL", error_type=type(error).__name__, error=str(error))
        raise
    finally:
        try:
            save_receipt(args.work, receipt)
        except BaseException as receipt_error:
            if primary_error is None:
                raise
            primary_error.add_note("Receipt update also failed: " + str(receipt_error))


if __name__ == "__main__":
    main()
