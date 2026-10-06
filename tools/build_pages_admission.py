"""Build the exact, non-self-referential ASTRA Pages admission manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUTPUT = ROOT / "evidence" / "pages_admission_v2.json"
BASE_COMMIT = "11a74c2ea98a2157c73d89dbea7f66975bbc68bf"
BASE_TREE = "ef8506855487bbcd3c2a78e982ac65f1a997858f"

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

COMPANION_ROOT = 'resources/sppt-scm-research-companion/draft-v0.1.0'
COMPANION_PATHS = (
    'FONT_NOTICES.txt',
    'README.md',
    'RIGHTS_AND_NOTICES.md',
    'explorer/README.md',
    'explorer/index.html',
    'explorer/provenance.json',
    'explorer/recurrence.md',
    'package/MANIFEST.sha256',
    'package/README.md',
    'package/research/Physics_Synthesis_ASTRA_SPPT_SCM_Public_Draft_2026-10-05.docx',
    'package/research/Physics_Synthesis_ASTRA_SPPT_SCM_Public_Draft_2026-10-05.pdf',
    'package/visuals/ASTRA_SPPT_SCM_Visual_Atlas_2026-10-05.pdf',
    'package/visuals/catalog.json',
    'package/visuals/illustrations/images/01-saturn-ring-dust-illustration.png',
    'package/visuals/illustrations/images/02-enceladus-plume-illustration.png',
    'package/visuals/illustrations/images/03-bent-filament-concept.png',
    'package/visuals/illustrations/provenance.json',
    'package/visuals/scientific/CAPTIONS_AND_SOURCES.md',
    'package/visuals/scientific/README.md',
    'package/visuals/scientific/animations/A1_pattern_vs_material_motion.gif',
    'package/visuals/scientific/animations/A1_pattern_vs_material_motion.mp4',
    'package/visuals/scientific/animations/A1_pattern_vs_material_motion_poster.png',
    'package/visuals/scientific/animations/A2_bending_graph_normal_frame.gif',
    'package/visuals/scientific/animations/A2_bending_graph_normal_frame.mp4',
    'package/visuals/scientific/animations/A2_bending_graph_normal_frame_poster.png',
    'package/visuals/scientific/figures/01_complete_observation_contract.png',
    'package/visuals/scientific/figures/01_complete_observation_contract.svg',
    'package/visuals/scientific/figures/02_complex_graph_normal_plane.png',
    'package/visuals/scientific/figures/02_complex_graph_normal_plane.svg',
    'package/visuals/scientific/figures/03_wki_discrete_growth_bands.png',
    'package/visuals/scientific/figures/03_wki_discrete_growth_bands.svg',
    'package/visuals/scientific/figures/04_phase_coherence_entanglement.png',
    'package/visuals/scientific/figures/04_phase_coherence_entanglement.svg',
    'package/visuals/scientific/figures/05_ring_inventory_optical_clock.png',
    'package/visuals/scientific/figures/05_ring_inventory_optical_clock.svg',
    'package/visuals/scientific/figures/06_planetary_transfer_comparison.png',
    'package/visuals/scientific/figures/06_planetary_transfer_comparison.svg',
    'package/visuals/scientific/generate_scientific_atlas.py',
    'package/visuals/scientific/manifest.json',
    'review.json',
)
SUPPORT_PATHS = ("LICENSE", "licenses/CC-BY-4.0.txt", "licenses/DEJAVU-FONTS.txt")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def docs_entries(root: Path = DOCS) -> list[dict[str, object]]:
    if root.is_symlink() or any(path.is_symlink() for path in root.rglob("*")):
        raise RuntimeError("Pages shell must not contain symlinks")
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


def file_record(root: Path, relative: str) -> dict[str, object]:
    path = root / relative
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise RuntimeError(f"Pages source must not be a symlink: {relative}")
    if not path.is_file():
        raise RuntimeError(f"Pages source is missing: {relative}")
    return {"path": relative, "bytes": path.stat().st_size, "sha256": sha256(path)}


def companion_record() -> dict[str, Any]:
    root = ROOT / COMPANION_ROOT
    observed = tuple(p.relative_to(root).as_posix() for p in sorted(root.rglob("*")) if p.is_file())
    if observed != COMPANION_PATHS or any(p.is_symlink() for p in root.rglob("*")):
        raise RuntimeError("Research companion Pages roster is not explicitly admitted")
    return {
        "status": "draft-unpromoted",
        "root": COMPANION_ROOT,
        "versioned_route": f"/{COMPANION_ROOT}/explorer/",
        "alias_route": "/explore/",
        "files": [file_record(root, path) for path in COMPANION_PATHS],
        "support_files": [file_record(ROOT, path) for path in SUPPORT_PATHS],
    }


def build_record() -> dict[str, Any]:
    return {
        "schema": "https://jkolantree.github.io/astra/schemas/pages-admission-v2.schema.json",
        "manifest_version": "2.0.0",
        "base": {
            "commit": BASE_COMMIT,
            "tree": BASE_TREE,
            "relationship": "fresh_current_main_pages_admission_base",
        },
        "head_shell": {"root": "docs", "files": docs_entries()},
        "release_routes": RELEASE_ROUTES,
        "research_companion": companion_record(),
        "policy": {
            "copy_exact_head_shell_only": True,
            "release_bytes_required_for_publication_routes": True,
            "reject_unadmitted_docs": True,
            "reject_unadmitted_draft_and_candidate_content": True,
            "research_companion_requires_separate_visual_approval": True,
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
