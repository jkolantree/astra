"""New edition schematics from reviewed declarative content; no external inputs.

Run only in an isolated source stage. Fixed canvas/font/export settings make
outputs comparable in the explicitly recorded installed renderer environment.
These are explanatory diagrams, not historical replacements or measurements.
"""

from __future__ import annotations

import hashlib
import html
import json
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[2]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    specs = json.loads((PACKAGE / "diagram-specs.json").read_text())
    require(specs["historical_equivalence"] is False, "Wrong edition boundary")
    diagrams = specs["diagrams"]
    require(len(diagrams) == 13, "Exactly thirteen reviewed schematics required")
    out = PACKAGE / "generated"
    require(not out.is_symlink(), "Linked output directory")
    out.mkdir(exist_ok=True)
    for path in out.iterdir():
        require(path.name in {"integrated-case.json", "scm-checks.json", "wki-checks.json"}
                and path.is_file() and not path.is_symlink(), "Existing diagram output")
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 12,
        "svg.fonttype": "path", "svg.hashsalt": "astra-integrated-new-diagrams-proposal",
        "figure.dpi": 100, "savefig.dpi": 160, "text.usetex": False,
        "axes.unicode_minus": True,
    })
    gallery = ["<!doctype html><html lang='en'><meta charset='utf-8'>",
               "<meta name='viewport' content='width=device-width,initial-scale=1'>",
               "<title>SPPT/ASTRA Integrated Core 1.1.0-alpha.1 — diagram atlas</title>",
               "<style>body{font:18px/1.5 system-ui,sans-serif;max-width:1100px;"
               "margin:auto;padding:24px;color:#173044;background:#f4f7f9}"
               "img{width:100%;height:auto}article{margin:40px 0}a{color:#075d80}"
               "code{overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><main>",
               "<h1>SPPT/ASTRA Integrated Core 1.1.0-alpha.1: diagram atlas</h1>",
               "<p>Unpublished integrated-core alpha candidate. These new schematics are not "
               "byte or scientific substitutes for the historical thirteen figures. "
               "No empirical validation, novelty priority or release admission is asserted.</p>",
               "<p>Actual bounded reports: <a href='integrated-case.json'>synthetic case</a>, "
               "<a href='scm-checks.json'>nine SCM families</a>, "
               "<a href='wki-checks.json'>six WKI groups</a>.</p>"]
    for d in diagrams:
        require(len(d["nodes"]) == 4, "Four explicit nodes required")
        require(d["id"].replace("_", "").isalnum(), "Unsafe diagram name")
        for ref in d["sources"]:
            p = ROOT / ref["path"]
            require(p.is_file() and not p.is_symlink(), "Missing source")
            require(hashlib.sha256(p.read_bytes()).hexdigest() == ref["sha256"],
                    "Source binding changed: " + ref["path"])
        fig = plt.figure(figsize=(12, 7.5), facecolor="#f4f7f9")
        ax = fig.add_axes((0, 0, 1, 1), xlim=(0, 12), ylim=(0, 7.5))
        ax.axis("off")
        ax.text(.55, 7.05, "ASTRA  /  INTEGRATED EDITION PROPOSAL  /  " + d["id"][:2],
                fontsize=10, color="#42657b", weight="bold")
        ax.text(.55, 6.55, d["title"], fontsize=22, color="#173044", weight="bold")
        ax.text(.55, 6.12, d["claim_status"], fontsize=12, color="#075d80")
        positions = [(0.6, 3.95), (6.65, 3.95), (0.6, 1.95), (6.65, 1.95)]
        for idx, (x, y) in enumerate(positions):
            node = d["nodes"][idx]
            ax.add_patch(FancyBboxPatch((x, y), 4.75, 1.4,
                         boxstyle="round,pad=0.03,rounding_size=0.12",
                         facecolor="white", edgecolor="#8ba6b5", linewidth=1.2))
            ax.text(x+.2, y+1.05, node["title"], fontsize=14, weight="bold", color="#173044")
            ax.text(x+.2, y+.75, node["body"], fontsize=11.5, va="top",
                    linespacing=1.55, color="#173044")
        for a, b, label in d["edges"]:
            x1, y1 = positions[a]; x2, y2 = positions[b]
            if y1 == y2:
                start = (x1 + (4.8 if x2 > x1 else -.04), y1+.65)
                stop = (x2 + (-.04 if x2 > x1 else 4.8), y2+.65)
            elif x1 == x2:
                start = (x1+2.4, y1-.02 if y2 < y1 else y1+1.45)
                stop = (x2+2.4, y2+1.45 if y2 < y1 else y2-.02)
            else:
                start = (x1+(4.5 if x2 > x1 else .3), y1-.02 if y2 < y1 else y1+1.45)
                stop = (x2+(.3 if x2 > x1 else 4.5), y2+1.45 if y2 < y1 else y2-.02)
            ax.add_patch(FancyArrowPatch(start, stop, arrowstyle="-|>",
                         mutation_scale=14, color="#287b91", linewidth=1.5))
            if label:
                lx, ly = (start[0]+stop[0])/2, (start[1]+stop[1])/2+.08
                if x1 != x2 and y1 != y2:
                    # Opposite diagonal arrows share a midpoint: separate labels.
                    offset = 1 if x2 > x1 else -1
                    lx += .30 * offset
                    ly += .15 * offset
                ax.text(lx, ly, label,
                        ha="center", fontsize=8, color="#075d80",
                        bbox={"facecolor":"#f4f7f9", "edgecolor":"none", "pad":1})
        equation = textwrap.fill(d["equation"], 114)
        ax.text(.6, 1.35, equation, fontsize=10, color="#173044", va="top")
        ax.text(.6, .77, textwrap.fill(d["scope"], 123), fontsize=9, va="top", color="#354c5c")
        ax.text(.6, .18, "Explanatory schematic • source-bound • no observed data • not a release",
                fontsize=8, color="#42657b")
        stem = out / d["id"]
        fig.savefig(stem.with_suffix(".png"), metadata={"Software":"ASTRA new-edition proposal"})
        fig.savefig(stem.with_suffix(".svg"), metadata={
            "Date":None, "Creator":"ASTRA new-edition proposal",
            "Title":d["title"], "Description":d["scope"],
        })
        plt.close(fig)
        # Standard Matplotlib SVG DTD is a public identifier, not an input fetch.
        # Remove it so downstream consumers never need an external DTD.
        svg = stem.with_suffix(".svg")
        text = svg.read_text()
        start = text.find("<!DOCTYPE")
        if start >= 0:
            end = text.index(">", start) + 1
            text = text[:start] + text[end:]
        svg.write_text(text)
        title = html.escape(d["title"]); scope = html.escape(d["scope"])
        gallery.append(f"<article><h2>{title}</h2><p>{html.escape(d['claim_status'])}</p>"
                       f"<img src='{d['id']}.svg' alt='{title}. {scope}'><p>{scope}</p>"
                       f"<p><a href='{d['id']}.png'>PNG</a> · <a href='{d['id']}.svg'>SVG</a></p>")
        gallery.append("<ol>" + "".join("<li><strong>"+html.escape(n["title"])+
                       "</strong>: "+html.escape(n["body"]).replace("\n", "; ")+"</li>"
                       for n in d["nodes"]) + "</ol><p>"+html.escape(d["equation"])+"</p>")
        gallery.append("<p>Directed connections (node numbers follow the list): " +
                       "; ".join(f"{a+1} → {b+1} {html.escape(label)}" for a,b,label in d["edges"])+".</p>")
        for ref in d["sources"]:
            gallery.append("<p>Source: <code>" + html.escape(ref["path"]) +
                           "</code>; SHA-256 <code>" + ref["sha256"] + "</code></p>")
        gallery.append("</article>")
    gallery.append("<footer><p>Font outlines: DejaVu Sans. No new blanket reuse license.</p>"
                   "<details><summary>Complete font notice</summary><pre>"+
                   html.escape((ROOT/"licenses/DEJAVU-FONTS.txt").read_text())+
                   "</pre></details></footer></main></html>")
    (out / "index.html").write_text("\n".join(gallery)+"\n")


if __name__ == "__main__":
    main()
