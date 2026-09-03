from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import pytest

from tools.dark_medium_response_atlas_publish_guard import (
    GITHUB_API_VERSION,
    GuardError,
    HttpResponse,
    _token,
    require_immutable_releases_enabled,
    require_release_absent,
    validate_new_tag_event,
)

REPOSITORY = "jkolantree/astra"
TAG = "dark-medium-response-atlas-v0.1.0"
TAG_OBJECT = "a" * 40
COMMIT = "b" * 40
SECRET_SENTINEL = "atlas-settings-token-sentinel"


class Responses:
    def __init__(self, *responses: HttpResponse) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, Mapping[str, str]]] = []

    def __call__(self, url: str, headers: Mapping[str, str]) -> HttpResponse:
        self.calls.append((url, headers))
        if not self.responses:
            raise AssertionError("Unexpected HTTP request")
        return self.responses.pop(0)


def response(status: int, value: Any, *, raw: bool = False) -> HttpResponse:
    body = value if raw else json.dumps(value).encode("utf-8")
    assert isinstance(body, bytes)
    return HttpResponse(status=status, body=body)


def event_environment() -> dict[str, str]:
    return {
        "GITHUB_EVENT_NAME": "push",
        "GITHUB_REF": f"refs/tags/{TAG}",
        "GITHUB_REF_TYPE": "tag",
        "GITHUB_REF_NAME": TAG,
        "GITHUB_SHA": COMMIT,
        "GITHUB_REPOSITORY": REPOSITORY,
    }


def new_tag_event() -> dict[str, Any]:
    return {
        "ref": f"refs/tags/{TAG}",
        "before": "0" * 40,
        "after": TAG_OBJECT,
        "created": True,
        "deleted": False,
        "forced": False,
        "repository": {"id": 1319077150, "full_name": REPOSITORY},
    }


def test_new_atlas_tag_event_is_accepted() -> None:
    identity = validate_new_tag_event(new_tag_event(), event_environment())
    assert identity.tag == TAG
    assert identity.tag_object == TAG_OBJECT
    assert identity.commit == COMMIT


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("created", False),
        ("before", "c" * 40),
        ("forced", True),
        ("deleted", True),
    ),
)
def test_tag_collision_replay_deletion_or_force_is_rejected(field: str, value: Any) -> None:
    event = new_tag_event()
    event[field] = value
    with pytest.raises(GuardError, match="collision, replay, deletion, or forced update"):
        validate_new_tag_event(event, event_environment())


def test_missing_settings_authority_is_blocked_external_configuration() -> None:
    with pytest.raises(GuardError, match="BLOCKED_EXTERNAL_CONFIGURATION"):
        _token({}, "ATLAS_RELEASE_SETTINGS_TOKEN")


@pytest.mark.parametrize("status", (401, 403, 404, 500))
def test_denied_immutable_settings_access_fails_closed_without_token_leak(status: int) -> None:
    transport = Responses(response(status, {"message": "denied"}))
    with pytest.raises(GuardError, match=f"HTTP {status}") as failure:
        require_immutable_releases_enabled(
            REPOSITORY,
            SECRET_SENTINEL,
            transport=transport,
        )
    assert SECRET_SENTINEL not in str(failure.value)


def test_http_200_with_malformed_immutable_json_fails_closed() -> None:
    transport = Responses(response(200, b"not-json", raw=True))
    with pytest.raises(GuardError, match="not valid UTF-8 JSON"):
        require_immutable_releases_enabled(
            REPOSITORY,
            SECRET_SENTINEL,
            transport=transport,
        )


@pytest.mark.parametrize("value", ({"enabled": False}, {"enabled": "true"}, {}))
def test_http_200_without_literal_enabled_true_fails_closed(value: dict[str, Any]) -> None:
    transport = Responses(response(200, value))
    with pytest.raises(GuardError, match="not explicitly reported as enabled"):
        require_immutable_releases_enabled(
            REPOSITORY,
            SECRET_SENTINEL,
            transport=transport,
        )


def test_literal_enabled_true_uses_versioned_github_headers() -> None:
    transport = Responses(response(200, {"enabled": True}))
    require_immutable_releases_enabled(
        REPOSITORY,
        SECRET_SENTINEL,
        transport=transport,
    )
    assert len(transport.calls) == 1
    url, headers = transport.calls[0]
    assert url == "https://api.github.com/repos/jkolantree/astra/immutable-releases"
    assert headers["X-GitHub-Api-Version"] == GITHUB_API_VERSION
    assert headers["Authorization"] == f"Bearer {SECRET_SENTINEL}"


@pytest.mark.parametrize("draft", (False, True))
def test_existing_published_or_draft_release_is_a_collision(draft: bool) -> None:
    transport = Responses(response(200, [{"tag_name": TAG, "draft": draft}]))
    with pytest.raises(GuardError, match="already exists"):
        require_release_absent(
            REPOSITORY,
            TAG,
            "atlas-contents-token-sentinel",
            transport=transport,
        )


def test_release_absence_check_reads_beyond_first_full_page() -> None:
    first_page = [{"tag_name": f"unrelated-{index}"} for index in range(100)]
    transport = Responses(
        response(200, first_page),
        response(200, [{"tag_name": TAG, "draft": True}]),
    )
    with pytest.raises(GuardError, match="already exists"):
        require_release_absent(
            REPOSITORY,
            TAG,
            "atlas-contents-token-sentinel",
            transport=transport,
        )
    assert "page=1" in transport.calls[0][0]
    assert "page=2" in transport.calls[1][0]


def test_no_existing_release_is_accepted() -> None:
    transport = Responses(response(200, []))
    require_release_absent(
        REPOSITORY,
        TAG,
        "atlas-contents-token-sentinel",
        transport=transport,
    )
    assert len(transport.calls) == 1
