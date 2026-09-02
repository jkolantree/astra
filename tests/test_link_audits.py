from __future__ import annotations

import urllib.error
from pathlib import Path

import pytest

from tools.check_external_links import observation_safe_url, probe
from tools.check_pages_links import check_pages_links
from tools.check_repository_links import check_repository_links
from tools.link_audit_common import markdown_links


def test_markdown_extractor_does_not_treat_bracket_math_as_a_link() -> None:
    text = (
        "The interval [0, 1], commutator [A, B], and $[r_M](q)$ are mathematics. "
        "[Read](guide.md#scope)."
    )
    assert markdown_links(text) == ["guide.md#scope"]


def test_repository_links_are_case_sensitive_and_fragment_checked(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("[Guide](guide.md#scope)\n", encoding="utf-8")
    (tmp_path / "guide.md").write_text("# Guide\n\n## Scope\n", encoding="utf-8")
    assert check_repository_links(tmp_path)["local_links"] == 1
    (tmp_path / "README.md").write_text("[Guide](Guide.md#scope)\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="case-drifted"):
        check_repository_links(tmp_path)
    (tmp_path / "README.md").write_text("[Guide](guide.md#missing)\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="missing fragment"):
        check_repository_links(tmp_path)


def test_pages_audit_covers_redirect_canonical_asset_and_fragment(tmp_path: Path) -> None:
    (tmp_path / "style.css").write_text("body { color: #111; }\n", encoding="utf-8")
    (tmp_path / "index.html").write_text(
        """<!doctype html><html><head>
<link rel="canonical" href="https://jkolantree.github.io/astra/">
<link rel="stylesheet" href="/astra/style.css"></head>
<body><main id="main"><a href="./version/#paper">Read</a><a href="/astra/paper/#paper">Root route</a></main></body></html>
""",
        encoding="utf-8",
    )
    version = tmp_path / "version"
    version.mkdir()
    (version / "index.html").write_text(
        """<!doctype html><html><head><meta http-equiv="refresh" content="0; url=../paper/"></head>
<body><main id="paper"><a href="../paper/">Continue</a></main></body></html>
""",
        encoding="utf-8",
    )
    paper = tmp_path / "paper"
    paper.mkdir()
    (paper / "index.html").write_text(
        "<!doctype html><html><body><main id=\"paper\">Paper</main></body></html>\n",
        encoding="utf-8",
    )
    result = check_pages_links(tmp_path)
    assert result["html_files"] == 3
    assert result["canonicals"] == 1
    assert result["redirects"] == 1
    (tmp_path / "style.css").unlink()
    with pytest.raises(RuntimeError, match="target is missing"):
        check_pages_links(tmp_path)


def test_external_probe_classifies_404_as_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(*_args: object, **_kwargs: object) -> object:
        raise urllib.error.HTTPError(
            "https://example.invalid/missing", 404, "Not Found", {}, None
        )

    monkeypatch.setattr("urllib.request.urlopen", missing)
    result = probe("https://example.invalid/missing")
    assert result["outcome"] == "missing"
    assert result["status"] == 404


def test_external_probe_classifies_403_as_transport_unresolved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def blocked(*_args: object, **_kwargs: object) -> object:
        raise urllib.error.HTTPError(
            "https://example.invalid/blocked", 403, "Forbidden", {}, None
        )

    monkeypatch.setattr("urllib.request.urlopen", blocked)
    result = probe("https://example.invalid/blocked")
    assert result["outcome"] == "transport_unresolved"
    assert result["status"] == 403


def test_external_observation_url_omits_redirect_telemetry_and_userinfo() -> None:
    redirect_with_userinfo = (
        "https://name:secret" + "@" + "example.invalid:8443/path?q=tracking#fragment"
    )
    assert observation_safe_url(redirect_with_userinfo) == "https://example.invalid:8443/path"
