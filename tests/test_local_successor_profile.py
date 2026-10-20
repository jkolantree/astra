"""Local integration must bind changed bytes without admitting historical records."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools import local_successor_profile as profile


@pytest.fixture
def contract(monkeypatch: pytest.MonkeyPatch) -> dict:
    names = set(profile.LOCAL_ONLY_PATHS) | {"README.md", "tools/local_successor_profile.py"}
    names.update(f"tools/fixture_{index}.py" for index in range(627 - len(names)))
    base = {name: {"bytes": 1, "sha256": profile.sha256(b"x")} for name in sorted(names)}
    monkeypatch.setattr(profile, "SUCCESSOR_BASE_MAP_SHA256", profile.sha256(profile.canonical(base)))
    files = copy.deepcopy(base)
    files["README.md"] = {"bytes": 1, "sha256": profile.sha256(b"y")}
    return {
        "schema_version": 2,
        "kind": "local_successor_validation_contract",
        "profile": "local-successor",
        "status": "LOCAL_DEVELOPMENT_NOT_RELEASE_ADMISSION",
        "authority": dict(profile.AUTHORITY),
        "basis": {"inventory_sha256": profile.BASE_INVENTORY_SHA256,
                  "reconciliation_sha256": profile.RECONCILIATION_SHA256},
        "base_files": base,
        "files": files,
        "modified_paths": ["README.md"],
        "added_paths": [],
        "local_only_paths": sorted(profile.LOCAL_ONLY_PATHS),
        "payload_bytes": 627,
    }


def test_exact_local_delta_is_accepted_without_historical_admission(contract: dict) -> None:
    assert profile.validate_contract(contract) == contract["files"]
    assert not any(contract["authority"].values())


@pytest.mark.parametrize("fault", [
    "base", "undeclared_change", "removed", "extra", "case_collision", "path_escape",
    "retained_bytes", "admission", "partition", "byte_total", "unrelated_source",
])
def test_contract_rejects_unreviewed_or_out_of_scope_delta(contract: dict, fault: str) -> None:
    files = contract["files"]
    identity = {"bytes": 1, "sha256": profile.sha256(b"z")}
    if fault == "base":
        contract["base_files"]["README.md"] = identity
    elif fault == "undeclared_change":
        files["tools/fixture_0.py"] = identity
    elif fault == "removed":
        del files["tools/fixture_0.py"]
    elif fault in {"extra", "case_collision", "path_escape", "unrelated_source"}:
        name = {"extra": "tools/extra.py", "case_collision": "readme.md",
                "path_escape": "../outside.py", "unrelated_source": "src/new_model.py"}[fault]
        files[name] = identity
        contract["payload_bytes"] += 1
        if fault == "unrelated_source":
            contract["added_paths"] = [name]
    elif fault == "retained_bytes":
        name = sorted(profile.LOCAL_ONLY_PATHS)[0]
        files[name] = identity
        contract["modified_paths"] = sorted(["README.md", name])
    elif fault == "admission":
        contract["authority"]["source_admitted"] = True
    elif fault == "partition":
        contract["local_only_paths"].pop()
    elif fault == "byte_total":
        contract["payload_bytes"] += 1
    with pytest.raises(RuntimeError):
        profile.validate_contract(contract)


def test_wrong_digest_stops_before_payload_or_candidate_checks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "snapshot"
    root.mkdir()
    path = tmp_path / "contract.json"
    path.write_text("{}", encoding="utf-8")

    def forbidden(*_args):
        raise AssertionError("Payload checks must not start with an untrusted contract")

    monkeypatch.setattr(profile, "observe_payload", forbidden)
    # Exercise each contract in its own explicit context, regardless of whether
    # pytest itself is running in GitHub Actions or from a tag.
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("GITHUB_REF", raising=False)
    for variable, value in (("GITHUB_ACTIONS", "true"), ("GITHUB_REF", "refs/tags/fixture")):
        with monkeypatch.context() as hosted:
            hosted.setenv(variable, value)
            with pytest.raises(RuntimeError, match="unavailable in hosted or tag contexts"):
                profile.run(root, str(path), "0" * 64)
    with pytest.raises(RuntimeError, match="External contract digest differs"):
        profile.run(root, str(path), "0" * 64)


def test_payload_rejects_changed_and_extra_files(tmp_path: Path) -> None:
    source = tmp_path / "source.py"
    source.write_bytes(b"x")
    expected = {"source.py": {"bytes": 1, "sha256": profile.sha256(b"x")}}
    assert profile.observe_payload(tmp_path, expected) == [source]
    source.write_bytes(b"y")
    with pytest.raises(RuntimeError, match="Successor bytes differ"):
        profile.observe_payload(tmp_path, expected)
    source.write_bytes(b"x")
    (tmp_path / "extra").write_bytes(b"x")
    with pytest.raises(RuntimeError, match="Missing or unexpected"):
        profile.observe_payload(tmp_path, expected)


def test_duplicate_contract_keys_are_rejected() -> None:
    with pytest.raises(RuntimeError, match="Duplicate JSON key"):
        profile.strict_json(b'{"files":{},"files":{}}')


def test_development_controls_environment_and_requires_every_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "source"
    root.mkdir()
    (root / "RUNTIME.json").write_bytes(
        (Path(__file__).resolve().parents[1] / "RUNTIME.json").read_bytes()
    )
    monkeypatch.setenv("PYTEST_ADDOPTS", "-k nonexistent")
    monkeypatch.setenv("PYTEST_PLUGINS", "untrusted_plugin")
    commands = []

    def fake(command, **kwargs):
        commands.append(command)
        if "pytest" in command:
            Path(command[command.index("--junitxml") + 1]).write_text(
                '<testsuites><testsuite tests="1" failures="0" errors="0" skipped="0"/></testsuites>'
            )
        assert "PYTEST_ADDOPTS" not in kwargs["env"]
        assert "PYTEST_PLUGINS" not in kwargs["env"]
        assert kwargs["env"]["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(profile.subprocess, "run", fake)
    result = profile.run_development(root, [], str(tmp_path / "scratch"))
    assert set(result) == profile.DEVELOPMENT_GATES
    command = next(command for command in commands if "pytest" in command)
    assert command[command.index("-o") + 1] == "addopts="
    assert "no:cacheprovider" in command
    monkeypatch.setattr(profile, "DEVELOPMENT_GATES", profile.DEVELOPMENT_GATES | {"missing_gate"})
    with pytest.raises(RuntimeError, match="Development gate roster differs"):
        profile.run_development(root, [], str(tmp_path / "other-scratch"))


def test_development_refuses_scratch_inside_source(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="Scratch directory must be separate"):
        profile.run_development(tmp_path, [], str(tmp_path / "scratch"))


@pytest.mark.parametrize("fault", [
    None, "source_map", "source_changed", "selection", "deferrals", "python",
    "dependencies", "host_exit", "malformed", "malformed_counts", "skipped", "browser_scope",
])
def test_cross_host_result_cannot_omit_or_substitute_test_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str | None,
) -> None:
    files = {"tools/local_successor_profile.py": {"bytes": 1, "sha256": "a" * 64}}
    observation = {
        "returncode": 0, "source_unchanged": True,
        "source_map_sha256": profile.sha256(profile.canonical(files)),
        "native_symlink_probe": "PASS", "locked_dependency_versions": "PASS", "python": "3.12.10",
        "test_targets": list(profile.DEVELOPMENT_TESTS),
        "deferred_tests": dict(profile.DEFERRED_TESTS),
        "windows_browser_tests": list(profile.WINDOWS_BROWSER_TESTS),
        "junit_counts": {"tests": 1, "failures": 0, "errors": 0, "skipped": 0},
    }
    changes = {
        "source_map": ("source_map_sha256", "0" * 64),
        "source_changed": ("source_unchanged", False), "selection": ("test_targets", []),
        "deferrals": ("deferred_tests", {}), "python": ("python", "3.12.14"),
        "dependencies": ("locked_dependency_versions", "UNKNOWN"),
        "browser_scope": ("windows_browser_tests", []),
    }
    if fault in changes:
        key, value = changes[fault]
        observation[key] = value
    if fault == "skipped":
        observation["junit_counts"]["skipped"] = 1
    if fault == "malformed_counts":
        observation["junit_counts"] = None
    calls = []

    def fake(command, **kwargs):
        calls.append(command)
        if "wslpath" in command:
            return subprocess.CompletedProcess(command, 0, "/source\n", "")
        request = json.loads(kwargs["input"])
        assert request["files"] == files
        assert command[command.index("-I"):command.index("-I") + 2] == ["-I", "-B"]
        output = "not-json" if fault == "malformed" else json.dumps(observation)
        return subprocess.CompletedProcess(command, 1 if fault == "host_exit" else 0, output, "")

    monkeypatch.setattr(profile.subprocess, "run", fake)
    result = profile.run_wsl_tests(tmp_path, files, {
        "distribution": "Ubuntu", "python": "/private/python", "work_directory": "/private/trial",
    })
    assert len(calls) == 2
    assert result["status"] == ("PASS" if fault is None else "FAIL")


def test_host_scratch_traversal_is_rejected_before_writes(tmp_path: Path) -> None:
    # The host entrypoint requires a genuinely isolated interpreter. The outer
    # current-development suite intentionally uses -P -s -B rather than -I.
    # Model only the platform precondition; leave flags and path guards real.
    code = """
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, sys.argv[1])
from tools import local_successor_profile as profile
with patch.object(profile.platform, "system", return_value="Linux"), \\
     patch.object(profile.platform, "python_version", return_value="3.12.10"):
    try:
        profile.run_host_tests(Path(sys.argv[2]), {}, sys.argv[3])
    except RuntimeError as error:
        assert str(error) == "Unsafe host scratch path", str(error)
        print(str(error))
    else:
        raise AssertionError("Traversal was not rejected")
"""
    completed = subprocess.run(
        [sys.executable, "-I", "-B", "-c", code,
         str(Path(profile.__file__).resolve().parents[1]),
         str(tmp_path), str(tmp_path / ".." / "escaped")],
        text=True, capture_output=True, check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert completed.stdout.strip() == "Unsafe host scratch path"
    assert not (tmp_path.parent / "escaped").exists()


def test_test_file_roster_cannot_silently_omit_new_tests(tmp_path: Path) -> None:
    (tmp_path / "tests").mkdir()
    for name in (*profile.DEVELOPMENT_TESTS, *profile.EXCLUDED_TEST_FILES):
        (tmp_path / name).write_text("# fixture\n")
    profile.validate_test_roster(tmp_path)
    (tmp_path / "tests/test_unreviewed.py").write_text("# fixture\n")
    with pytest.raises(RuntimeError, match="test-file roster differs"):
        profile.validate_test_roster(tmp_path)


def test_documentation_javascript_is_checked_text_not_a_public_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tools import check_repository as checker

    script = tmp_path / "docs/understand/signals/signals.js"
    script.parent.mkdir(parents=True)
    script.write_text("const value = 1;\n", encoding="utf-8")
    monkeypatch.setattr(checker, "ROOT", tmp_path)
    assert profile.public_check_projection(tmp_path, [script], checker) == [script]
    checker.check_text_privacy([script])
    script.write_text("// C:" + chr(92) + "private\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="local Windows path"):
        checker.check_text_privacy([script])
    # Register this source type only for documentation. Other suffixes and
    # directories still fail; Pages admission separately binds the exact roster.
    for name in ("docs/unexpected.exe", "scripts/unregistered.js"):
        with pytest.raises(RuntimeError, match="Unregistered suffix"):
            profile.public_check_projection(tmp_path, [tmp_path / name], checker)


@pytest.mark.parametrize("skipped", [0, 1])
def test_test_process_rejects_skips_even_with_success_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, skipped: int,
) -> None:
    (tmp_path / "test-results.xml").write_text(
        f'<testsuites><testsuite tests="1" failures="0" errors="0" skipped="{skipped}"/></testsuites>'
    )
    monkeypatch.setattr(profile.subprocess, "run", lambda *a, **k:
                        subprocess.CompletedProcess(a[0], 0, "", ""))
    result = profile.run_test_command(["pytest"], tmp_path, {}, tmp_path)
    assert result["status"] == ("PASS" if skipped == 0 else "FAIL")


def test_browser_routing_preserves_every_reviewed_test(tmp_path: Path) -> None:
    native = profile.pytest_command(["python"], tmp_path, native_host=True)
    browser = profile.pytest_command(["python"], tmp_path, browser_only=True)
    assert set(profile.DEVELOPMENT_TESTS).issubset(native)
    assert {arg.removeprefix("--deselect=") for arg in native if arg.startswith("--deselect=")} == (
        set(profile.DEFERRED_TESTS) | set(profile.WINDOWS_BROWSER_TESTS)
    )
    assert set(profile.WINDOWS_BROWSER_TESTS).issubset(browser)
    assert not any(arg.startswith("--deselect=") for arg in browser)
