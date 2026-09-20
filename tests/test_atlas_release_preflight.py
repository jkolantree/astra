from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "atlas-release-preflight.yml"


def workflow() -> dict[str, Any]:
    value = YAML(typ="safe").load(WORKFLOW)
    assert isinstance(value, dict)
    return value


def steps() -> dict[str, Any]:
    return {step["name"]: step for step in workflow()["jobs"]["preflight"]["steps"]}


def run_step(name: str, environment: dict[str, str]) -> subprocess.CompletedProcess[str]:
    executable = shutil.which("pwsh")
    if executable is None:
        pytest.skip("Executable preflight script checks require PowerShell 7 (pwsh)")
    return subprocess.run(
        [executable, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", steps()[name]["run"]],
        env={**os.environ, **environment},
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )


def main_context() -> dict[str, str]:
    return {
        "GITHUB_EVENT_NAME": "workflow_dispatch",
        "GITHUB_REPOSITORY": "jkolantree/astra",
        "GITHUB_REPOSITORY_ID": "1319077150",
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_REF_TYPE": "branch",
        "GITHUB_SHA": "a" * 40,
    }


def test_preflight_has_only_the_declared_read_authority_and_no_publication_path() -> None:
    value = workflow()
    assert value["on"] == {"workflow_dispatch": None}
    assert value["permissions"] == {"contents": "read"}
    assert set(value["jobs"]) == {"preflight"}
    job = value["jobs"]["preflight"]
    assert set(job) == {"runs-on", "timeout-minutes", "steps"}
    assert job["runs-on"] == "windows-latest"
    assert job["timeout-minutes"] == 10
    declared_steps = steps()
    assert list(declared_steps) == [
        "Require the declared repository and main dispatch",
        "Require dedicated immutable-settings authority configuration",
        "Checkout the dispatched main commit",
        "Install exact Python",
        "Verify the declared CPython version",
        "Create short-lived immutable-settings reader token",
        "Require enabled immutable GitHub Releases",
        "Report the nonpublishing evidence boundary",
    ]
    assert len(job["steps"]) == len(declared_steps)
    assert all("continue-on-error" not in step for step in job["steps"])
    assert all("if" not in step for step in job["steps"][:-1])
    checkout = declared_steps["Checkout the dispatched main commit"]
    assert checkout["uses"] == "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
    assert checkout["with"] == {"ref": "${{ github.sha }}", "persist-credentials": False}
    python = declared_steps["Install exact Python"]
    assert python["uses"] == "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97"
    assert python["with"] == {"python-version-file": ".python-version"}
    token = declared_steps["Create short-lived immutable-settings reader token"]
    assert token["uses"] == "actions/create-github-app-token@bcd2ba49218906704ab6c1aa796996da409d3eb1"
    assert token["with"] == {
        "client-id": "${{ vars.ATLAS_RELEASE_APP_CLIENT_ID }}",
        "private-key": "${{ secrets.ATLAS_RELEASE_APP_PRIVATE_KEY }}",
        "owner": "${{ github.repository_owner }}",
        "repositories": "${{ github.event.repository.name }}",
        "permission-administration": "read",
    }
    setting = declared_steps["Require enabled immutable GitHub Releases"]
    assert setting["env"] == {
        "ATLAS_RELEASE_SETTINGS_TOKEN": "${{ steps.atlas-settings-token.outputs.token }}"
    }
    assert setting["run"].splitlines()[0] == (
        "python -I -B tools/dark_medium_response_atlas_publish_guard.py require-immutable-releases"
    )
    scripts = "\n".join(step.get("run", "") for step in job["steps"])
    for forbidden in (
        "dark_medium_response_atlas_release.py", "gh ", "git ", "Invoke-WebRequest",
        "Invoke-RestMethod", "ATLAS_RELEASE_CONTENTS_TOKEN", "GH_TOKEN", "private-key",
        "require-new-tag-event", "require-release-absent", "${{",
    ):
        assert forbidden not in scripts
    assert "RUNTIME.json" in declared_steps["Verify the declared CPython version"]["run"]
    assert "'CPython'" in declared_steps["Verify the declared CPython version"]["run"]


def test_exact_main_context_is_accepted() -> None:
    result = run_step("Require the declared repository and main dispatch", main_context())
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    ("key", "value"),
    (
        ("GITHUB_EVENT_NAME", "push"),
        ("GITHUB_REPOSITORY", "other/astra"),
        ("GITHUB_REPOSITORY_ID", "1"),
        ("GITHUB_REF", "refs/heads/feature"),
        ("GITHUB_REF", "refs/tags/dark-medium-response-atlas-v0.1.0"),
        ("GITHUB_REF_TYPE", "tag"),
        ("GITHUB_SHA", ""),
        ("GITHUB_SHA", "a" * 39),
    ),
)
def test_other_repository_ref_event_or_malformed_commit_fails_before_authority(
    key: str, value: str,
) -> None:
    result = run_step(
        "Require the declared repository and main dispatch", {**main_context(), key: value}
    )
    assert result.returncode != 0
    assert "requires the declared repository and an exact main dispatch" in result.stderr


@pytest.mark.parametrize(
    ("client_id", "configured"), (("", "true"), (" ", "true"), ("test-client", "false"), ("test-client", ""))
)
def test_absent_configuration_fails_closed(client_id: str, configured: str) -> None:
    result = run_step(
        "Require dedicated immutable-settings authority configuration",
        {
            "ATLAS_RELEASE_APP_CLIENT_ID": client_id,
            "ATLAS_RELEASE_APP_PRIVATE_KEY_CONFIGURED": configured,
            "ATLAS_RELEASE_APP_PRIVATE_KEY": "private-key-sentinel-must-not-be-read",
        },
    )
    assert result.returncode != 0
    assert "BLOCKED_EXTERNAL_CONFIGURATION" in result.stderr
    assert "private-key-sentinel-must-not-be-read" not in result.stdout + result.stderr


def test_configuration_presence_does_not_require_reading_the_private_key() -> None:
    configuration = steps()["Require dedicated immutable-settings authority configuration"]
    assert configuration["env"] == {
        "ATLAS_RELEASE_APP_CLIENT_ID": "${{ vars.ATLAS_RELEASE_APP_CLIENT_ID }}",
        "ATLAS_RELEASE_APP_PRIVATE_KEY_CONFIGURED": "${{ secrets.ATLAS_RELEASE_APP_PRIVATE_KEY != '' }}",
    }
    result = run_step(
        "Require dedicated immutable-settings authority configuration",
        {
            "ATLAS_RELEASE_APP_CLIENT_ID": "test-client",
            "ATLAS_RELEASE_APP_PRIVATE_KEY_CONFIGURED": "true",
            "ATLAS_RELEASE_APP_PRIVATE_KEY": "",
        },
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("settings_outcome", ("success", "failure", "skipped"))
def test_summary_never_claims_publication_or_exposes_credentials(
    tmp_path: Path, settings_outcome: str,
) -> None:
    summary = tmp_path / "summary.md"
    summary_step = steps()["Report the nonpublishing evidence boundary"]
    assert summary_step["if"] == "always()"
    assert summary_step["env"] == {
        "CONTEXT_OUTCOME": "${{ steps.context.outcome }}",
        "CONFIGURATION_OUTCOME": "${{ steps.configuration.outcome }}",
        "TOKEN_OUTCOME": "${{ steps.atlas-settings-token.outcome }}",
        "SETTINGS_OUTCOME": "${{ steps.settings.outcome }}",
    }
    result = run_step(
        "Report the nonpublishing evidence boundary",
        {
            "GITHUB_STEP_SUMMARY": str(summary),
            "CONTEXT_OUTCOME": "success",
            "CONFIGURATION_OUTCOME": "success",
            "TOKEN_OUTCOME": "success",
            "SETTINGS_OUTCOME": settings_outcome,
            "ATLAS_RELEASE_SETTINGS_TOKEN": "settings-token-sentinel-must-not-be-read",
        },
    )
    assert result.returncode == 0, result.stderr
    report = summary.read_text(encoding="utf-8-sig")
    assert "Configuration presence: success" in report
    assert "App installation token creation: success" in report
    assert f"Settings access and literal enabled:true: {settings_outcome}" in report
    assert "Actual publication: UNEXERCISED" in report
    assert "settings-token-sentinel-must-not-be-read" not in report + result.stdout + result.stderr
