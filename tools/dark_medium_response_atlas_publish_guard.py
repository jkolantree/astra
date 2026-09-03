"""Fail-closed GitHub control-plane checks for an Atlas publication.

The deterministic asset controller remains in
``dark_medium_response_atlas_release.py``.  This module handles only the
mutable GitHub control plane: new-tag event identity, the immutable-release
setting, and release-name collisions.  Credentials are read from environment
variables and are never written or included in diagnostics.
"""

from __future__ import annotations

if __name__ == "__main__":
    import sys as _bootstrap_sys

    if not _bootstrap_sys.flags.isolated or not _bootstrap_sys.dont_write_bytecode:
        raise SystemExit(
            "Unsafe startup: run Python with -I -B before "
            "tools/dark_medium_response_atlas_publish_guard.py"
        )

import argparse
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

EXPECTED_REPOSITORY = "jkolantree/astra"
EXPECTED_REPOSITORY_ID = 1319077150
GITHUB_API_ROOT = "https://api.github.com"
GITHUB_API_VERSION = "2026-03-10"
ATLAS_TAG = re.compile(
    r"dark-medium-response-atlas-v(?:0|[1-9][0-9]*)\."
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?"
)
SHA1 = re.compile(r"[0-9a-f]{40}")
ZERO_SHA1 = "0" * 40
MAX_RESPONSE_BYTES = 16 * 1024 * 1024
MAX_RELEASE_PAGES = 1000


class GuardError(RuntimeError):
    """A publication precondition could not be established."""


@dataclass(frozen=True)
class TagPushIdentity:
    tag: str
    tag_object: str
    commit: str


@dataclass(frozen=True)
class HttpResponse:
    status: int
    body: bytes


Transport = Callable[[str, Mapping[str, str]], HttpResponse]


class _RejectRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        request: urllib.request.Request,
        file_pointer: Any,
        code: int,
        message: str,
        headers: Mapping[str, str],
        new_url: str,
    ) -> None:
        return None


def _https_get(url: str, headers: Mapping[str, str]) -> HttpResponse:
    if not url.startswith(f"{GITHUB_API_ROOT}/"):
        raise GuardError("Refusing to send GitHub authority to an unexpected API origin.")
    request = urllib.request.Request(url, headers=dict(headers), method="GET")
    opener = urllib.request.build_opener(_RejectRedirects())
    try:
        with opener.open(request, timeout=30) as response:
            body = response.read(MAX_RESPONSE_BYTES + 1)
            status = response.status
    except urllib.error.HTTPError as error:
        raise GuardError(f"GitHub API request was denied or failed with HTTP {error.code}.") from None
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise GuardError(f"GitHub API request failed before a valid response: {type(error).__name__}.") from None
    if len(body) > MAX_RESPONSE_BYTES:
        raise GuardError("GitHub API response exceeded the fail-closed size limit.")
    return HttpResponse(status=status, body=body)


def _token(environ: Mapping[str, str], name: str) -> str:
    value = environ.get(name, "")
    if not value or value != value.strip() or any(character.isspace() for character in value):
        if name == "ATLAS_RELEASE_SETTINGS_TOKEN":
            raise GuardError(
                "BLOCKED_EXTERNAL_CONFIGURATION: the dedicated immutable-settings "
                "credential is missing or malformed."
            )
        raise GuardError("The release API credential is missing or malformed.")
    return value


def _headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "astra-dark-medium-response-atlas-publish-guard",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }


def _json(body: bytes, label: str) -> Any:
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GuardError(f"{label} was not valid UTF-8 JSON.") from error


def _repository(value: str) -> str:
    if value.casefold() != EXPECTED_REPOSITORY.casefold():
        raise GuardError("GitHub repository identity does not match the declared Atlas repository.")
    return EXPECTED_REPOSITORY


def validate_new_tag_event(
    event: Mapping[str, Any], environ: Mapping[str, str]
) -> TagPushIdentity:
    """Require a newly created, non-forced Atlas annotated-tag push context."""

    tag = environ.get("GITHUB_REF_NAME", "")
    expected_ref = f"refs/tags/{tag}"
    repository = event.get("repository")
    if ATLAS_TAG.fullmatch(tag) is None:
        raise GuardError("The push does not name a supported Atlas release tag.")
    if (
        environ.get("GITHUB_EVENT_NAME") != "push"
        or environ.get("GITHUB_REF") != expected_ref
        or environ.get("GITHUB_REF_TYPE") != "tag"
        or event.get("ref") != expected_ref
    ):
        raise GuardError("Release workflow did not receive the exact Atlas tag event.")
    if (
        event.get("created") is not True
        or event.get("deleted") is not False
        or event.get("forced") is not False
        or event.get("before") != ZERO_SHA1
    ):
        raise GuardError(
            "Atlas tag collision, replay, deletion, or forced update detected; refusing publication."
        )
    tag_object = event.get("after")
    commit = environ.get("GITHUB_SHA", "")
    if not isinstance(tag_object, str) or SHA1.fullmatch(tag_object) is None:
        raise GuardError("Atlas tag push-event object identity is malformed.")
    if SHA1.fullmatch(commit) is None:
        raise GuardError("Atlas checked-out commit identity is malformed.")
    if (
        not isinstance(repository, Mapping)
        or not isinstance(repository.get("full_name"), str)
        or repository["full_name"].casefold() != EXPECTED_REPOSITORY.casefold()
        or repository.get("id") != EXPECTED_REPOSITORY_ID
        or environ.get("GITHUB_REPOSITORY", "").casefold() != EXPECTED_REPOSITORY.casefold()
    ):
        raise GuardError("Atlas tag event repository identity is incorrect.")
    return TagPushIdentity(tag=tag, tag_object=tag_object, commit=commit)


def require_immutable_releases_enabled(
    repository: str,
    token: str,
    *,
    transport: Transport = _https_get,
) -> None:
    """Require a literal JSON boolean ``enabled: true`` from GitHub."""

    repository = _repository(repository)
    url = f"{GITHUB_API_ROOT}/repos/{repository}/immutable-releases"
    response = transport(url, _headers(token))
    if response.status != 200:
        raise GuardError(
            f"Immutable-release authority returned HTTP {response.status}; refusing publication."
        )
    value = _json(response.body, "Immutable-release setting response")
    if not isinstance(value, dict):
        raise GuardError("Immutable-release setting response was not a JSON object.")
    enabled = value.get("enabled")
    if type(enabled) is not bool or enabled is not True:
        raise GuardError(
            "Immutable GitHub Releases were not explicitly reported as enabled; refusing publication."
        )


def require_release_absent(
    repository: str,
    tag: str,
    token: str,
    *,
    transport: Transport = _https_get,
) -> None:
    """Reject any existing draft or published release with the exact tag."""

    repository = _repository(repository)
    if ATLAS_TAG.fullmatch(tag) is None:
        raise GuardError("Refusing to query releases for an unsupported Atlas tag.")
    headers = _headers(token)
    for page in range(1, MAX_RELEASE_PAGES + 1):
        query = urllib.parse.urlencode({"per_page": 100, "page": page})
        url = f"{GITHUB_API_ROOT}/repos/{repository}/releases?{query}"
        response = transport(url, headers)
        if response.status != 200:
            raise GuardError(
                f"Release collision check returned HTTP {response.status}; refusing publication."
            )
        value = _json(response.body, "Release collision response")
        if not isinstance(value, list):
            raise GuardError("Release collision response was not a JSON array.")
        for release in value:
            if not isinstance(release, dict) or not isinstance(release.get("tag_name"), str):
                raise GuardError("Release collision response contained a malformed release record.")
            if release["tag_name"] == tag:
                raise GuardError(
                    "An Atlas release already exists for this tag; refusing to create, edit, "
                    "replace, or adopt it."
                )
        if len(value) < 100:
            return
    raise GuardError("Release listing exceeded the fail-closed pagination limit.")


def _event_from_environment(environ: Mapping[str, str]) -> Mapping[str, Any]:
    path_value = environ.get("GITHUB_EVENT_PATH", "")
    if not path_value:
        raise GuardError("GitHub event path is missing.")
    path = Path(path_value)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GuardError("GitHub tag event is unavailable or malformed.") from error
    if not isinstance(value, dict):
        raise GuardError("GitHub tag event must be a JSON object.")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("require-new-tag-event")
    subparsers.add_parser("require-immutable-releases")
    subparsers.add_parser("require-release-absent")
    arguments = parser.parse_args()
    environ = os.environ
    try:
        if arguments.command == "require-new-tag-event":
            identity = validate_new_tag_event(_event_from_environment(environ), environ)
            print(f"New non-forced Atlas tag event verified for {identity.tag}.")
        elif arguments.command == "require-immutable-releases":
            require_immutable_releases_enabled(
                environ.get("GITHUB_REPOSITORY", ""),
                _token(environ, "ATLAS_RELEASE_SETTINGS_TOKEN"),
            )
            print("Immutable GitHub Releases are explicitly enabled.")
        elif arguments.command == "require-release-absent":
            tag = environ.get("GITHUB_REF_NAME", "")
            require_release_absent(
                environ.get("GITHUB_REPOSITORY", ""),
                tag,
                _token(environ, "ATLAS_RELEASE_CONTENTS_TOKEN"),
            )
            print(f"No draft or published GitHub Release exists for {tag}.")
    except GuardError as error:
        raise SystemExit(str(error)) from None


if __name__ == "__main__":
    main()
