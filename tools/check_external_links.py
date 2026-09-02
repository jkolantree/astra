"""Probe external links without misclassifying transport blocks as dead records."""

from __future__ import annotations

import argparse
import json
import ssl
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from jsonschema import Draft7Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "resources" / "dark-medium-response-atlas" / "v0.1.0"
OBSERVATIONS = PACKAGE / "external-link-observations.json"
SCHEMA = ROOT / "schemas" / "external-link-observations-v1.schema.json"
MISSING = {404, 410}
TRANSPORT = {401, 403, 429, 451}


def observation_safe_url(raw_url: str) -> str | None:
    """Keep a redirect target useful without retaining query-bound telemetry."""
    parsed = urlsplit(raw_url)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return None
    try:
        port = parsed.port
    except ValueError:
        return None
    host = parsed.hostname
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    authority = f"{host}:{port}" if port is not None else host
    return urlunsplit((parsed.scheme.lower(), authority, parsed.path, "", ""))


def probe(url: str, *, timeout: float = 15.0) -> dict[str, Any]:
    checked = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    headers = {"User-Agent": "ASTRA-link-audit/1.0 (+https://github.com/jkolantree/astra)"}
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
            context=ssl.create_default_context(),
        ) as response:
            status = int(response.status)
            final = response.geturl()
            response.read(1024)
    except urllib.error.HTTPError as error:
        status = int(error.code)
        final = error.geturl() or url
        detail = f"HTTP {status}"
        if status in MISSING:
            outcome = "missing"
        elif status in TRANSPORT or status >= 500:
            outcome = "transport_unresolved"
        else:
            outcome = "network_unresolved"
        return {
            "url": url,
            "checked_at": checked,
            "outcome": outcome,
            "status": status,
            "final_url": observation_safe_url(final),
            "detail": detail,
        }
    except (urllib.error.URLError, TimeoutError, ssl.SSLError) as error:
        return {
            "url": url,
            "checked_at": checked,
            "outcome": "network_unresolved",
            "status": None,
            "final_url": None,
            "detail": f"{type(error).__name__}: {error}",
        }
    outcome = "redirect_ok" if final.rstrip("/") != url.rstrip("/") else "http_ok"
    return {
        "url": url,
        "checked_at": checked,
        "outcome": outcome,
        "status": status,
        "final_url": observation_safe_url(final),
        "detail": f"HTTP {status}",
    }


def audit(path: Path = OBSERVATIONS, *, write: bool = False, workers: int = 8) -> dict[str, Any]:
    record = json.loads(path.read_text(encoding="utf-8"))
    Draft7Validator(
        json.loads(SCHEMA.read_text(encoding="utf-8")),
        format_checker=FormatChecker(),
    ).validate(record)
    urls = [item["url"] for item in record["observations"]]
    if urls != sorted(set(urls)):
        raise RuntimeError("External-link observation URLs must be unique and sorted")
    if write:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            observations = list(executor.map(probe, urls))
        generated = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        record["generated_at"] = generated
        record["observations"] = observations
        path.write_text(
            json.dumps(record, indent=2, sort_keys=False, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    unsafe_final_urls = [
        item["final_url"]
        for item in record["observations"]
        if item["final_url"] is not None
        and item["final_url"] != observation_safe_url(item["final_url"])
    ]
    if unsafe_final_urls:
        raise RuntimeError("External-link observations must omit query, fragment, and userinfo data")
    missing = [item for item in record["observations"] if item["outcome"] == "missing"]
    if missing:
        raise RuntimeError(
            "Definite external-link failures:\n"
            + "\n".join(f"{item['url']} -> HTTP {item.get('status')}" for item in missing)
        )
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    record = audit(write=args.write, workers=args.workers)
    counts: dict[str, int] = {}
    for observation in record["observations"]:
        counts[observation["outcome"]] = counts.get(observation["outcome"], 0) + 1
    print("External link audit completed: " + ", ".join(f"{key}={value}" for key, value in sorted(counts.items())))


if __name__ == "__main__":
    main()
