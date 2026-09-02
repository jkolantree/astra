"""Render every Atlas PDF page for human visual inspection.

Rendered PNGs and their manifest are disposable review material under tmp/.
This tool deliberately does not write the tracked visual-review verdict.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]
PDF = (
    ROOT
    / "resources"
    / "dark-medium-response-atlas"
    / "v0.1.0"
    / "dark-medium-response-atlas-v0.1.0.pdf"
)
OUTPUT = ROOT / "tmp" / "dark-medium-response-atlas-render"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_output(path: Path) -> Path:
    resolved_root = ROOT.resolve()
    resolved = path.resolve()
    if resolved != (ROOT / "tmp" / "dark-medium-response-atlas-render").resolve():
        raise RuntimeError(f"Atlas render output must be the canonical disposable path: {path}")
    if resolved_root not in resolved.parents:
        raise RuntimeError(f"Atlas render output escaped the repository: {path}")
    current = ROOT
    for part in path.relative_to(ROOT).parts:
        current /= part
        junction_check = getattr(current, "is_junction", None)
        if current.is_symlink() or bool(junction_check and junction_check()):
            raise RuntimeError(f"Atlas render output contains a link or junction: {current}")
    return resolved


def render(pdf_path: Path = PDF, output: Path = OUTPUT, *, dpi: int = 160) -> dict[str, object]:
    if dpi < 144:
        raise RuntimeError("Readable visual review requires at least 144 DPI")
    output = _safe_output(output)
    output.mkdir(parents=True, exist_ok=True)
    admitted_names = {"render-manifest.json"}
    document = pdfium.PdfDocument(pdf_path)
    page_records: list[dict[str, object]] = []
    try:
        for index in range(len(document)):
            name = f"page-{index + 1:04d}.png"
            admitted_names.add(name)
            destination = output / name
            page = document[index]
            bitmap = page.render(scale=dpi / 72, rotation=0)
            image = bitmap.to_pil()
            image.save(destination, format="PNG", compress_level=9, optimize=False)
            page_records.append(
                {
                    "page": index + 1,
                    "render": name,
                    "width": image.width,
                    "height": image.height,
                    "bytes": destination.stat().st_size,
                    "sha256": sha256(destination),
                }
            )
            image.close()
            bitmap.close()
            page.close()
    finally:
        document.close()
    unexpected = sorted(
        path.name
        for path in output.iterdir()
        if not path.is_file() or path.name not in admitted_names
    )
    if unexpected:
        raise RuntimeError("Unexpected Atlas render output: " + ", ".join(unexpected))
    manifest = {
        "pdf": pdf_path.name,
        "pdf_bytes": pdf_path.stat().st_size,
        "pdf_sha256": sha256(pdf_path),
        "dpi": dpi,
        "page_count": len(page_records),
        "pages": page_records,
    }
    (output / "render-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dpi", type=int, default=160)
    args = parser.parse_args()
    manifest = render(dpi=args.dpi)
    print(
        f"Rendered {manifest['page_count']} Atlas PDF pages at {manifest['dpi']} DPI "
        f"to {OUTPUT.relative_to(ROOT).as_posix()}."
    )


if __name__ == "__main__":
    main()
