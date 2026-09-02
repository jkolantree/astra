"""Build the exact, non-self-referential ASTRA Pages admission manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUTPUT = ROOT / "evidence" / "pages_admission_v1.json"
BASE_COMMIT = "3c1a1325b6b365ba457a03b87cc73139d0c6a629"
BASE_TREE = "ff03d152c98deb65c7246fdd2283cebee71b5857"

RELEASE_ROUTES = [
    {
        "line": "sppt-astra-core",
        "tag": "v1.0.7",
        "versioned_route": "/v1.0.7/",
        "latest_route": "/latest/",
        "kind": "core-release",
        "asset_allowlist": [
            "SPPT_ASTRA_preprint_v1.0.7.html",
            "SPPT_ASTRA_technical_supplement_v1.0.7.html",
            "SPPT_ASTRA_v1.0.7_source.tar.gz",
            "SHA256SUMS",
        ],
    },
    {
        "line": "earth-is-the-instrument-working-paper",
        "tag": "earth-instrument-wp-0.1",
        "versioned_route": "/resources/earth-is-the-instrument/v0.1/",
        "latest_route": None,
        "kind": "supplemental-release",
        "asset_allowlist": [
            "ASTRA_Earth_Is_the_Instrument_Working_Paper_v0.1.pdf",
            "FONT_NOTICES.txt",
            "SHA256SUMS.txt",
            "cover.png",
        ],
    },
    {
        "line": "earth-is-the-instrument-framework",
        "tag": "earth-instrument-framework-v0.3.0",
        "versioned_route": "/resources/earth-is-the-instrument/v0.3.0/",
        "latest_route": "/resources/earth-is-the-instrument/latest/",
        "kind": "supplemental-release",
        "asset_allowlist": [
            "ASTRA_Framework_v0.3.0_Earth_Is_The_Instrument.pdf",
            "ASTRA_v0.3.0_Public_Ground_Reading.pdf",
            "ASTRA_Dual_Rent_Local_to_Global_Audit_Form_v0.3.0.pdf",
            "ASTRA_v0.3.0_Verification_Report.pdf",
            "SHA256SUMS.txt",
        ],
    },
    {
        "line": "dark-medium-response-atlas",
        "tag": "dark-medium-response-atlas-v0.1.0",
        "versioned_route": "/resources/dark-medium-response-atlas/v0.1.0/",
        "latest_route": "/resources/dark-medium-response-atlas/latest/",
        "kind": "supplemental-release",
        "asset_allowlist": [
            "dark-medium-response-atlas-v0.1.0.html",
            "dark-medium-response-atlas-v0.1.0.pdf",
            "dark-medium-response-atlas-v0.1.0-source.tar.gz",
            "SHA256SUMS",
            "dark-medium-response-atlas-v0.1.0-release-identity.json",
        ],
    },
]

SHELL_PATHS = (
    "404.html",
    "index.html",
    "resources/earth-is-the-instrument/v0.1/index.html",
    "resources/earth-is-the-instrument/v0.3.0/audit-form/index.html",
    "resources/earth-is-the-instrument/v0.3.0/companion.css",
    "resources/earth-is-the-instrument/v0.3.0/errata/index.html",
    "resources/earth-is-the-instrument/v0.3.0/ground-reading/index.html",
    "resources/earth-is-the-instrument/v0.3.0/index.html",
    "resources/index.html",
    "sppt-astra-cover.svg",
    "style.css",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def docs_entries(root: Path = DOCS) -> list[dict[str, object]]:
    observed = tuple(
        path.relative_to(root).as_posix()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    )
    if observed != SHELL_PATHS:
        raise RuntimeError(
            "Pages shell roster is not explicitly admitted: "
            f"missing={sorted(set(SHELL_PATHS) - set(observed))}; "
            f"unexpected={sorted(set(observed) - set(SHELL_PATHS))}"
        )
    return [
        {
            "path": relative,
            "bytes": (root / relative).stat().st_size,
            "sha256": sha256(root / relative),
        }
        for relative in SHELL_PATHS
    ]


def build_record() -> dict[str, Any]:
    return {
        "schema": "https://jkolantree.github.io/astra/schemas/pages-admission-v1.schema.json",
        "manifest_version": "1.0.0",
        "base": {
            "commit": BASE_COMMIT,
            "tree": BASE_TREE,
            "relationship": "fresh_current_main_pages_admission_base",
        },
        "head_shell": {"root": "docs", "files": docs_entries()},
        "release_routes": RELEASE_ROUTES,
        "policy": {
            "copy_exact_head_shell_only": True,
            "release_bytes_required_for_publication_routes": True,
            "reject_unadmitted_docs": True,
            "reject_draft_and_candidate_content": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    output = args.output.resolve()
    if output != OUTPUT.resolve():
        parser.error(f"output must be {OUTPUT.relative_to(ROOT).as_posix()}")
    output.write_text(
        json.dumps(build_record(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Wrote {OUTPUT.relative_to(ROOT).as_posix()}.")


if __name__ == "__main__":
    main()
