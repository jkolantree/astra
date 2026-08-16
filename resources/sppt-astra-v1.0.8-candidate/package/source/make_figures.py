from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle

OUT = Path(__file__).resolve().parents[1] / "figures"
OUT.mkdir(parents=True, exist_ok=True)

NAVY = "#071B2A"
NAVY2 = "#0D2B3E"
GOLD = "#D9B83E"
COPPER = "#A35332"
LAPIS = "#2F64A3"
MAL = "#3E9878"
OFF = "#F7F3EA"
GRAY = "#61717C"
RED = "#93443D"
SKY = "#A9C9DA"
INK = "#11212B"
WHITE = "#FFFFFF"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 14,
        "axes.labelsize": 10,
        "figure.dpi": 120,
        "savefig.dpi": 260,
        "svg.fonttype": "none",
        "svg.hashsalt": "astra-sppt-v1.0.8-endogenous-visibility",
    }
)


def save(fig: plt.Figure, name: str) -> None:
    """Save to a fixed canvas. Do not use bbox_inches='tight'; it can crop titles."""
    fig.savefig(
        OUT / f"{name}.png",
        facecolor=fig.get_facecolor(),
        metadata={"Creation Time": "2026-08-16T00:00:00Z"},
        pad_inches=0.04,
    )
    svg_path = OUT / f"{name}.svg"
    fig.savefig(
        svg_path,
        facecolor=fig.get_facecolor(),
        metadata={
            "Creator": "ASTRA / Jacko T.",
            "Date": "2026-08-16T00:00:00Z",
            "Description": "Original ASTRA candidate figure",
        },
        pad_inches=0.04,
    )
    # Matplotlib emits a legacy SVG 1.1 external DTD declaration.  The
    # figures are intentionally self-contained, so remove that network-shaped
    # reference while preserving the authored SVG content byte-for-byte.
    svg_text = svg_path.read_text(encoding="utf-8")
    external_doctype = (
        '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"\n'
        '  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n'
    )
    if svg_text.count(external_doctype) != 1:
        raise RuntimeError(f"unexpected SVG doctype in {svg_path}")
    svg_text = svg_text.replace(external_doctype, "")
    svg_text = "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n"
    svg_path.write_text(svg_text, encoding="utf-8", newline="\n")
    plt.close(fig)


def _wrap_lines(text: str, width: int) -> str:
    parts = []
    for paragraph in text.split("\n"):
        parts.append(textwrap.fill(paragraph, width=max(8, width), break_long_words=False))
    return "\n".join(parts)


def box(
    ax: plt.Axes,
    xy: tuple[float, float],
    wh: tuple[float, float],
    title: str,
    fc: str,
    *,
    ec: str = INK,
    tc: str = WHITE,
    fs: float | None = None,
    lw: float = 1.1,
    radius: float = 0.018,
    subtitle: str | None = None,
    subtitle_tc: str | None = None,
) -> FancyBboxPatch:
    x, y = xy
    w, h = wh
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0.009,rounding_size={radius}",
        facecolor=fc,
        edgecolor=ec,
        linewidth=lw,
        clip_on=True,
    )
    ax.add_patch(patch)

    # Width in normalized axes coordinates is mapped to a conservative character count.
    chars = max(8, int(54 * w))
    title_text = _wrap_lines(title, chars)
    title_len = max((len(line) for line in title_text.splitlines()), default=1)
    if fs is None:
        fs = 10.2
        if title_len > 18:
            fs = 9.2
        if title_len > 24:
            fs = 8.2
        if h < 0.12:
            fs = min(fs, 8.5)
    title_lines = title_text.count("\n") + 1
    if subtitle:
        # Reserve a distinct upper title band and lower subtitle band. This is
        # intentionally conservative because the figures are often reduced in
        # the final document.
        if title_lines >= 3:
            fs = min(fs, 7.4)
        elif title_lines == 2:
            fs = min(fs, 8.7)
        title_y = y + h * (0.74 if title_lines <= 2 else 0.76)
    else:
        title_y = y + h * 0.50
    ax.text(
        x + w / 2,
        title_y,
        title_text,
        ha="center",
        va="center",
        color=tc,
        weight="bold",
        fontsize=fs,
        linespacing=0.98,
        clip_on=True,
        zorder=3,
    )
    if subtitle:
        subtitle_text = _wrap_lines(subtitle, max(9, int(66 * w)))
        subtitle_lines = subtitle_text.count("\n") + 1
        sub_fs = max(5.8, min(fs - 1.7, 7.7))
        if subtitle_lines >= 4:
            sub_fs = min(sub_fs, 5.9)
        elif subtitle_lines == 3:
            sub_fs = min(sub_fs, 6.4)
        ax.text(
            x + w / 2,
            y + h * (0.24 if subtitle_lines <= 2 else 0.22),
            subtitle_text,
            ha="center",
            va="center",
            color=subtitle_tc or tc,
            fontsize=sub_fs,
            linespacing=0.92,
            clip_on=True,
            zorder=3,
        )
    return patch


def arrow(
    ax: plt.Axes,
    a: tuple[float, float],
    b: tuple[float, float],
    *,
    color: str = GRAY,
    lw: float = 1.3,
    style: str = "-|>",
    rad: float = 0.0,
) -> None:
    ax.add_patch(
        FancyArrowPatch(
            a,
            b,
            arrowstyle=style,
            mutation_scale=11,
            linewidth=lw,
            color=color,
            connectionstyle=f"arc3,rad={rad}",
            clip_on=True,
            zorder=2,
        )
    )


def canvas(figsize=(10.5, 6.3), title: str | None = None):
    fig, ax = plt.subplots(figsize=figsize, facecolor=OFF)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    if title:
        ax.text(
            0.5,
            0.965,
            title,
            ha="center",
            va="top",
            weight="bold",
            color=INK,
            fontsize=14.2,
            clip_on=True,
        )
    return fig, ax


# ---------------------------------------------------------------------------
# Figure 01: repository architecture; use a small number of short labels.
# ---------------------------------------------------------------------------
fig, ax = canvas(title="Repository lines and the v1.0.8 candidate boundary")
box(ax, (0.34, 0.78), (0.32, 0.105), "SPPT / ASTRA v1.0.7", NAVY, subtitle="stable release")
box(ax, (0.08, 0.53), (0.23, 0.13), "Published supplements", COPPER, subtitle="Earth v0.3.0")
box(ax, (0.385, 0.53), (0.23, 0.13), "Methods alpha", LAPIS, subtitle="Sector-Complete Instrument")
box(
    ax,
    (0.69, 0.53),
    (0.23, 0.13),
    "Unpromoted drafts",
    MAL,
    subtitle="Active Support · Bridge\nVisibility · AEOF",
)
for x in (0.195, 0.50, 0.805):
    arrow(ax, (0.50, 0.78), (x, 0.66), color=GRAY, lw=1.0)
box(
    ax,
    (0.22, 0.25),
    (0.56, 0.14),
    "v1.0.8 candidate review",
    NAVY2,
    subtitle="admit typed methods only after claim-local evidence and release gates",
)
for x in (0.195, 0.50, 0.805):
    arrow(ax, (x, 0.53), (0.50, 0.39), color=GOLD, lw=1.2)
ax.text(
    0.50,
    0.10,
    "The candidate is a new manuscript. It does not rewrite v1.0.7 or any immutable publication line.",
    ha="center",
    va="center",
    color=RED,
    fontsize=9.5,
    weight="bold",
    wrap=True,
)
save(fig, "figure_01_repository_architecture")


# ---------------------------------------------------------------------------
# Figure 02: state architecture. Short text in boxes, details in a lower legend.
# ---------------------------------------------------------------------------
fig, ax = canvas(title="From hidden topology to stateful edges and operator-aware inference")
headers = [
    ("Physical state", NAVY, "graph · fields · edge state"),
    ("Mode / support", MAL, "route · waveform · active region"),
    ("Environment", COPPER, "sources · sinks · exchanged flux"),
    ("Observation", LAPIS, "visibility · sector · detector"),
]
xs = [0.04, 0.285, 0.53, 0.775]
for (t, c, s), x in zip(headers, xs, strict=True):
    box(ax, (x, 0.69), (0.185, 0.135), t, c, subtitle=s)
for i in range(3):
    arrow(ax, (xs[i] + 0.185, 0.758), (xs[i + 1], 0.758), color=GOLD, lw=1.5)
for x in [0.132, 0.377, 0.622, 0.867]:
    arrow(ax, (x, 0.69), (0.50, 0.53), color=GRAY, lw=1.0)
box(
    ax,
    (0.29, 0.37),
    (0.42, 0.16),
    "Stateful-edge contract",
    NAVY2,
    subtitle="carrier · law · state · support · closure · observable · falsifier",
)
outputs = [
    ("Dynamical rent", COPPER, "future changes"),
    ("Epistemic rent", LAPIS, "generators separate"),
    ("Bounded certificate", MAL, "claim stops at tested scope"),
]
for (t, c, s), x in zip(outputs, [0.07, 0.375, 0.68], strict=True):
    box(ax, (x, 0.105), (0.25, 0.13), t, c, subtitle=s)
    arrow(ax, (0.50, 0.37), (x + 0.125, 0.235), color=GOLD, lw=1.1)
save(fig, "figure_02_stateful_edge_architecture")


# ---------------------------------------------------------------------------
# Figure 03: edge contract as a two-row grid, not one compressed strip.
# ---------------------------------------------------------------------------
fig, ax = canvas(figsize=(10.8, 6.4), title="Minimum contract for a proposed physical edge")
items = [
    ("1. Endpoints", "declared reservoirs", NAVY),
    ("2. Carrier", "matter · charge · heat · momentum", COPPER),
    ("3. Constitutive law", "domain · units · signs", MAL),
    ("4. Edge state", "strain · composition · damage · memory", GOLD),
    ("5. Active support", "where and when coupling acts", LAPIS),
    ("6. Closure ledger", "environment and controller exchange", COPPER),
    ("7. Observation", "detector basis and unresolved sectors", LAPIS),
    ("8. Falsifier", "predeclared intervention or held-out test", NAVY),
]
positions = [(0.05 + 0.235 * c, 0.59 - 0.25 * r) for r in range(2) for c in range(4)]
for (t, s, c), (x, y) in zip(items, positions, strict=True):
    box(
        ax,
        (x, y),
        (0.205, 0.16),
        t,
        c,
        tc=INK if c == GOLD else WHITE,
        subtitle=s,
        subtitle_tc=INK if c == GOLD else WHITE,
    )
for c in range(3):
    arrow(ax, (0.255 + 0.235 * c, 0.67), (0.285 + 0.235 * c, 0.67), color=GRAY, lw=0.9)
    arrow(ax, (0.255 + 0.235 * c, 0.42), (0.285 + 0.235 * c, 0.42), color=GRAY, lw=0.9)
for c in range(4):
    arrow(ax, (0.1525 + 0.235 * c, 0.59), (0.1525 + 0.235 * c, 0.50), color=GRAY, lw=0.9)
ax.text(
    0.50,
    0.105,
    "A complete record is necessary for review. It is not evidence that the edge exists.",
    ha="center",
    color=RED,
    fontsize=10,
    weight="bold",
)
save(fig, "figure_03_edge_contract")


# ---------------------------------------------------------------------------
# Figure 04: closure-conditioned nonreciprocity.
# ---------------------------------------------------------------------------
fig, ax = canvas(title="Effective nonreciprocity in an open, driven colloidal subsystem")
ax.add_patch(Rectangle((0.10, 0.17), 0.80, 0.05, facecolor=GRAY, alpha=0.7))
ax.add_patch(Rectangle((0.10, 0.76), 0.80, 0.05, facecolor=GRAY, alpha=0.7))
ax.add_patch(
    Rectangle((0.10, 0.22), 0.80, 0.54, facecolor=SKY, alpha=0.17, edgecolor=LAPIS, linewidth=1.0)
)
ax.text(0.50, 0.86, "External AC drive and electrodes", ha="center", color=INK, weight="bold")
ax.add_patch(Circle((0.40, 0.48), 0.07, facecolor=COPPER, edgecolor=INK, linewidth=1.3))
ax.add_patch(Circle((0.60, 0.48), 0.048, facecolor=GOLD, edgecolor=INK, linewidth=1.3))
ax.text(0.40, 0.48, "L", ha="center", va="center", color=WHITE, weight="bold")
ax.text(0.60, 0.48, "S", ha="center", va="center", color=INK, weight="bold")
arrow(ax, (0.47, 0.51), (0.545, 0.51), color=RED, lw=3.0)
arrow(ax, (0.545, 0.45), (0.47, 0.45), color=LAPIS, lw=1.4)
ax.text(0.505, 0.60, "unequal effective pair response", ha="center", fontsize=9.2)
arrow(ax, (0.50, 0.36), (0.68, 0.36), color=MAL, lw=2.4)
ax.text(0.59, 0.30, "pair translation", ha="center", color=MAL, weight="bold")
box(ax, (0.12, 0.56), (0.18, 0.115), "Field / fluid", LAPIS, subtitle="momentum channel")
box(ax, (0.70, 0.56), (0.18, 0.115), "Electrode / fluid", COPPER, subtitle="reaction channel")
arrow(ax, (0.30, 0.615), (0.37, 0.53), color=LAPIS, lw=1.0)
arrow(ax, (0.70, 0.615), (0.63, 0.53), color=COPPER, lw=1.0)
ax.text(
    0.50,
    0.095,
    "The particle-only forces need not cancel. The enlarged apparatus must still close momentum and energy.",
    ha="center",
    color=RED,
    fontsize=9.5,
    weight="bold",
)
save(fig, "figure_04_nonreciprocity_closure")


# ---------------------------------------------------------------------------
# Figure 05: conceptual chart with caption note removed from plotting area.
# ---------------------------------------------------------------------------
t = np.logspace(-1, 2.2, 300)
rec = 0.8 * t**0.32
nr = 1.7 * (1 - np.exp(-t / 4)) + 0.13 * np.sin(2.4 * np.log1p(t))
fig, ax = plt.subplots(figsize=(9.0, 5.2), facecolor=OFF, layout="constrained")
ax.plot(t, rec, label="reciprocal: scale keeps growing", lw=2.2, color=LAPIS)
ax.plot(t, nr, label="active nonreciprocal: dynamic saturation", lw=2.2, color=COPPER)
ax.set_xscale("log")
ax.set_xlabel("time (normalized)")
ax.set_ylabel("characteristic cluster scale (conceptual)")
ax.set_title("Coarsening versus dynamic saturation", weight="bold", color=INK, pad=10)
ax.grid(alpha=0.20)
ax.legend(frameon=False, loc="upper left", fontsize=8.7)
save(fig, "figure_05_arrested_coarsening_model")


# ---------------------------------------------------------------------------
# Figure 06: catalyst state with compact callouts.
# ---------------------------------------------------------------------------
fig, ax = canvas(title="Self-rewriting catalyst edge: fast strain, slow surface history")
ax.add_patch(Rectangle((0.12, 0.20), 0.76, 0.15, facecolor=GRAY, edgecolor=INK))
ax.text(
    0.50, 0.275, "NiTi shape-memory substrate", ha="center", va="center", color=WHITE, weight="bold"
)
ax.add_patch(Rectangle((0.18, 0.35), 0.64, 0.15, facecolor=COPPER, edgecolor=INK))
ax.text(
    0.50,
    0.425,
    "Cu3Pt intermetallic subsurface",
    ha="center",
    va="center",
    color=WHITE,
    weight="bold",
)
ax.add_patch(Rectangle((0.18, 0.50), 0.64, 0.065, facecolor=GOLD, edgecolor=INK))
ax.text(
    0.50,
    0.532,
    "reported Pt-enriched surface after cycling",
    ha="center",
    va="center",
    color=INK,
    weight="bold",
    fontsize=8.9,
)
for x in (0.26, 0.42, 0.58, 0.74):
    ax.text(x, 0.69, "O2", ha="center", fontsize=10.5, weight="bold", color=LAPIS)
    arrow(ax, (x, 0.655), (x, 0.575), color=LAPIS, lw=1.1)
box(ax, (0.05, 0.61), (0.17, 0.14), "Fast state", MAL, subtitle="elastic strain")
box(ax, (0.78, 0.61), (0.17, 0.14), "Slow state", COPPER, subtitle="composition · defects")
arrow(ax, (0.22, 0.675), (0.31, 0.555), color=MAL, lw=1.1)
arrow(ax, (0.78, 0.675), (0.69, 0.555), color=COPPER, lw=1.1)
arrow(ax, (0.34, 0.13), (0.19, 0.13), color=LAPIS, lw=2.0)
arrow(ax, (0.66, 0.13), (0.81, 0.13), color=LAPIS, lw=2.0)
ax.text(0.50, 0.095, "controlled in-plane strain", ha="center", color=LAPIS, weight="bold")
ax.text(
    0.50,
    0.84,
    "ORR response can depend on present mechanical state and accumulated interface history.",
    ha="center",
    fontsize=10.2,
    color=RED,
    weight="bold",
)
save(fig, "figure_06_catalyst_self_rewriting_edge")


# ---------------------------------------------------------------------------
# Figure 07: bar chart. No disclaimer text inside axes.
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8.2, 4.9), facecolor=OFF, layout="constrained")
labels = ["Cu3Pt\n+0.80% tension", "Cu3Pt\n-0.99% compression", "Pure Pt\ncomparison"]
vals = [840, 855, 856]
colors = [COPPER, MAL, LAPIS]
bars = ax.bar(labels, vals, color=colors, edgecolor=INK, width=0.60)
ax.set_ylim(820, 865)
ax.set_ylabel("reported potential at 1.0 mA cm$^{-2}$ (mV)")
ax.set_title("Reported ORR values under the study conditions", weight="bold", color=INK, pad=10)
for bar, value in zip(bars, vals, strict=True):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        value + 1.0,
        f"{value} mV",
        ha="center",
        weight="bold",
        fontsize=9,
    )
ax.grid(axis="y", alpha=0.20)
save(fig, "figure_07_orr_reported_values")


# ---------------------------------------------------------------------------
# Figure 08: operator stack in two readable rows.
# ---------------------------------------------------------------------------
fig, ax = canvas(figsize=(10.8, 6.5), title="Unified ASTRA operator stack")
steps = [
    ("Source / history", NAVY),
    ("Forcing / support", MAL),
    ("Stateful edge", COPPER),
    ("Output / residue", GOLD),
    ("Visibility / sample", LAPIS),
    ("Sector observable", MAL),
    ("Bounded certificate", NAVY2),
]
positions = [(0.04 + 0.24 * c, 0.66) for c in range(4)] + [
    (0.16 + 0.24 * c, 0.40) for c in range(3)
]
for (title, color), (x, y) in zip(steps, positions, strict=True):
    box(ax, (x, y), (0.20, 0.13), title, color, tc=INK if color == GOLD else WHITE)
for i in range(3):
    arrow(ax, (positions[i][0] + 0.20, 0.725), (positions[i + 1][0], 0.725), color=GRAY, lw=1.0)
arrow(ax, (positions[3][0] + 0.10, 0.66), (positions[4][0] + 0.10, 0.53), color=GRAY, lw=1.0)
for i in range(4, 6):
    arrow(ax, (positions[i][0] + 0.20, 0.465), (positions[i + 1][0], 0.465), color=GRAY, lw=1.0)
box(
    ax, (0.14, 0.15), (0.28, 0.12), "Dynamical rent", COPPER, subtitle="intervention changes future"
)
box(
    ax,
    (0.58, 0.15),
    (0.28, 0.12),
    "Epistemic rent",
    LAPIS,
    subtitle="protocol changes discrimination",
)
arrow(ax, (0.50, 0.40), (0.28, 0.27), color=GOLD, lw=1.1)
arrow(ax, (0.50, 0.40), (0.72, 0.27), color=GOLD, lw=1.1)
ax.text(
    0.50,
    0.065,
    "Physical transport, control, observation, archive, and certificate arrows remain distinct.",
    ha="center",
    color=RED,
    fontsize=9.5,
    weight="bold",
)
save(fig, "figure_08_operator_stack")


# ---------------------------------------------------------------------------
# Figure 09: bridge protocol.
# ---------------------------------------------------------------------------
fig, ax = canvas(figsize=(10.5, 5.0), title="SPPT Bridge Protocol: proposed promotion path")
steps = [
    ("Conservation", "contract", NAVY),
    ("Thermodynamic", "ledger", COPPER),
    ("Observational", "equivalence", LAPIS),
    ("Intervention", "design", MAL),
    ("Held-out", "prediction", GOLD),
]
xs = [0.04, 0.235, 0.43, 0.625, 0.82]
for i, (t, s, c) in enumerate(steps):
    box(
        ax,
        (xs[i], 0.40),
        (0.16, 0.22),
        t,
        c,
        tc=INK if c == GOLD else WHITE,
        fs=7.8 if t == "Thermodynamic" else None,
        subtitle=s,
        subtitle_tc=INK if c == GOLD else WHITE,
    )
    if i < 4:
        arrow(ax, (xs[i] + 0.16, 0.51), (xs[i + 1], 0.51), color=GRAY, lw=1.2)
ax.text(
    0.50,
    0.20,
    "Failure at any gate means defer or demote. A typed record is not automatic scientific admission.",
    ha="center",
    color=RED,
    weight="bold",
    fontsize=9.6,
)
save(fig, "figure_09_bridge_protocol")


# ---------------------------------------------------------------------------
# Figure 10: dual rent.
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7.7, 6.5), facecolor=OFF, layout="constrained")
ax.set_xlim(-1, 1)
ax.set_ylim(-1, 1)
ax.axhline(0, color=GRAY, lw=1)
ax.axvline(0, color=GRAY, lw=1)
ax.set_xlabel("epistemic rent: change in generator discrimination")
ax.set_ylabel("dynamical rent: change in reachable futures")
ax.set_title("Dual-rent seam classification", weight="bold", color=INK, pad=10)
ax.text(
    0.50,
    0.58,
    "CONTROL +\nINSTRUMENT",
    ha="center",
    va="center",
    fontsize=10.2,
    weight="bold",
    color=MAL,
)
ax.text(
    -0.50,
    0.58,
    "STATEFUL\nMASK",
    ha="center",
    va="center",
    fontsize=10.2,
    weight="bold",
    color=COPPER,
)
ax.text(
    0.50,
    -0.58,
    "DIAGNOSTIC\nAMPLIFIER",
    ha="center",
    va="center",
    fontsize=10.2,
    weight="bold",
    color=LAPIS,
)
ax.text(
    -0.50,
    -0.58,
    "COSMETIC /\nOMIT",
    ha="center",
    va="center",
    fontsize=10.2,
    weight="bold",
    color=GRAY,
)
ax.grid(alpha=0.12)
save(fig, "figure_10_dual_rent")


# ---------------------------------------------------------------------------
# Figure 11: application map; avoid long box subtitles.
# ---------------------------------------------------------------------------
fig, ax = canvas(title="One methodology, domain-specific constitutive laws")
box(
    ax,
    (0.37, 0.41),
    (0.26, 0.17),
    "Stateful edge +\noperator audit",
    NAVY2,
    subtitle="shared bookkeeping",
)
applications = [
    ("Planetary interiors", "phase connectivity", COPPER, 0.07, 0.72),
    ("Cosmology", "visibility operators", LAPIS, 0.385, 0.75),
    ("Active matter", "environment closure", MAL, 0.70, 0.72),
    ("Catalysis", "strain · surface history", GOLD, 0.71, 0.18),
    ("Origins / Earth", "archive · residue", COPPER, 0.385, 0.10),
    ("Mathematics", "local-to-global", LAPIS, 0.06, 0.18),
]
for t, s, c, x, y in applications:
    box(
        ax,
        (x, y),
        (0.23, 0.12),
        t,
        c,
        tc=INK if c == GOLD else WHITE,
        subtitle=s,
        subtitle_tc=INK if c == GOLD else WHITE,
    )
    arrow(ax, (x + 0.115, y + 0.06), (0.50, 0.495), color=GRAY, lw=0.9)
ax.text(
    0.50,
    0.035,
    "Shared abstractions earn value only when each domain supplies units, laws, controls, and falsifiers.",
    ha="center",
    color=RED,
    weight="bold",
    fontsize=9.4,
)
save(fig, "figure_11_application_map")


# ---------------------------------------------------------------------------
# Figure 12: promotion gates.
# ---------------------------------------------------------------------------
fig, ax = canvas(figsize=(10.8, 6.4), title="Fail-closed v1.0.8 promotion gates")
gates = [
    ("1. Source identity", "record · version · rights"),
    ("2. Claim entailment", "exact wording · scope"),
    ("3. Physical closure", "units · signs · sources · sinks"),
    ("4. Identifiability", "equivalence classes · null directions"),
    ("5. Intervention", "predeclared support or sector change"),
    ("6. Held-out prediction", "calibration · out-of-set test"),
    ("7. Reproducibility", "runtime · seeds · hashes · failures"),
    ("8. Release identity", "tag · commit · tree · remote read-back"),
]
for i, (t, s) in enumerate(gates):
    row, col = divmod(i, 2)
    x = 0.07 + 0.46 * col
    y = 0.77 - 0.18 * row
    c = [NAVY, COPPER, LAPIS, MAL][row]
    box(ax, (x, y), (0.40, 0.115), t, c, subtitle=s)
ax.text(
    0.50,
    0.055,
    "This document passes a drafting audit only. It is not a release, empirical validation, or immutable certificate.",
    ha="center",
    color=RED,
    weight="bold",
    fontsize=9.4,
)
save(fig, "figure_12_promotion_gates")


# ---------------------------------------------------------------------------
# Figure 13: temporal-interface audit added for the 2023 accelerating-wave paper.
# ---------------------------------------------------------------------------
fig, ax = canvas(
    figsize=(10.8, 6.5),
    title="Temporal-interface audit: what changes, what is observed, what is claimed",
)
box(
    ax,
    (0.05, 0.67),
    (0.25, 0.15),
    "Spatial interface",
    NAVY,
    subtitle="properties vary with position: n(x)",
)
box(
    ax,
    (0.375, 0.67),
    (0.25, 0.15),
    "Temporal interface",
    LAPIS,
    subtitle="properties are externally changed: n(t)",
)
box(
    ax,
    (0.70, 0.67),
    (0.25, 0.15),
    "Accelerating-wave model",
    COPPER,
    subtitle="prescribed c(t) and an extra derivative term",
)
arrow(ax, (0.30, 0.745), (0.375, 0.745), color=GRAY, lw=1.0)
arrow(ax, (0.625, 0.745), (0.70, 0.745), color=GRAY, lw=1.0)
box(ax, (0.08, 0.38), (0.20, 0.14), "Control / pump", MAL, subtitle="what drives n(t)?")
box(
    ax,
    (0.31, 0.38),
    (0.20, 0.14),
    "Reference frame",
    GOLD,
    tc=INK,
    subtitle="which frequency, wavelength, momentum?",
    subtitle_tc=INK,
)
box(
    ax, (0.54, 0.38), (0.20, 0.14), "Global ledger", COPPER, subtitle="field + medium + pump energy"
)
box(
    ax, (0.77, 0.38), (0.16, 0.14), "Time-reversal test", NAVY, subtitle="what exactly is reversed?"
)
for x in (0.18, 0.41, 0.64, 0.85):
    arrow(ax, (0.50, 0.67), (x, 0.52), color=GOLD, lw=1.0)
box(
    ax,
    (0.24, 0.12),
    (0.52, 0.13),
    "Bounded ASTRA certificate",
    NAVY2,
    subtitle="the equation is published theory; a universal microscopic arrow of time remains unestablished",
)
for x in (0.18, 0.41, 0.64, 0.85):
    arrow(ax, (x, 0.38), (0.50, 0.25), color=GRAY, lw=0.9)
save(fig, "figure_13_temporal_interface_audit")


# ---------------------------------------------------------------------------
# Figure 14: endogenous visibility feedback.
# ---------------------------------------------------------------------------
fig, ax = canvas(title="Endogenous visibility: the source can alter its own transducer")
box(ax, (0.05, 0.62), (0.19, 0.14), "Hidden source", RED, subtitle="engine or candidate process")
box(
    ax,
    (0.31, 0.62),
    (0.22, 0.14),
    "Stateful transducer",
    LAPIS,
    subtitle="envelope · plasma · archive",
)
box(ax, (0.61, 0.62), (0.16, 0.14), "Detector", NAVY, subtitle="protocol and threshold")
box(ax, (0.82, 0.62), (0.13, 0.14), "Data", MAL, subtitle="bounded record")
arrow(ax, (0.24, 0.69), (0.31, 0.69), color=GOLD, lw=1.8)
arrow(ax, (0.53, 0.69), (0.61, 0.69), color=GOLD, lw=1.8)
arrow(ax, (0.77, 0.69), (0.82, 0.69), color=GOLD, lw=1.8)
# feedback loop
arrow(ax, (0.42, 0.61), (0.18, 0.45), color=RED, lw=1.5, rad=-0.18)
arrow(ax, (0.18, 0.45), (0.42, 0.61), color=RED, lw=1.5, rad=-0.18)
ax.text(
    0.27,
    0.43,
    "source-transducer feedback",
    ha="center",
    va="center",
    color=RED,
    weight="bold",
    fontsize=9.3,
)
box(
    ax,
    (0.12, 0.19),
    (0.24, 0.13),
    "Measure the source",
    COPPER,
    subtitle="independent engine channel",
)
box(
    ax, (0.40, 0.19), (0.24, 0.13), "Measure the medium", LAPIS, subtitle="state, drift, saturation"
)
box(ax, (0.68, 0.19), (0.20, 0.13), "Change protocol", MAL, subtitle="forcing, band, sector")
ax.text(
    0.50,
    0.08,
    "A fixed visibility operator is valid only after backreaction is bounded.",
    ha="center",
    color=INK,
    weight="bold",
    fontsize=10.2,
)
save(fig, "figure_14_endogenous_visibility")

# ---------------------------------------------------------------------------
# Figure 15: source-shell separation.
# ---------------------------------------------------------------------------
fig, ax = canvas(title="Source-shell separation: the emergent spectrum is jointly produced")
ax.add_patch(Circle((0.23, 0.56), 0.075, facecolor=RED, edgecolor=INK, linewidth=1.2))
ax.text(0.23, 0.56, "ENGINE", ha="center", va="center", color=WHITE, weight="bold", fontsize=9.5)
for r, c, alpha in [(0.15, COPPER, 0.25), (0.21, GOLD, 0.20), (0.27, SKY, 0.22)]:
    ax.add_patch(Circle((0.23, 0.56), r, facecolor=c, edgecolor=c, alpha=alpha, linewidth=1.0))
ax.text(0.23, 0.26, "dense gas envelope", ha="center", color=INK, weight="bold", fontsize=10)
box(ax, (0.48, 0.60), (0.19, 0.13), "Absorption", COPPER, subtitle="Balmer population")
box(ax, (0.48, 0.40), (0.19, 0.13), "Scattering", LAPIS, subtitle="line shape and width")
box(ax, (0.48, 0.20), (0.19, 0.13), "Re-emission", MAL, subtitle="continuum and lines")
for y in (0.665, 0.465, 0.265):
    arrow(ax, (0.38, 0.56), (0.48, y), color=GOLD, lw=1.3)
box(ax, (0.76, 0.38), (0.18, 0.22), "Observed spectrum", NAVY, subtitle="engine filtered by shell")
for y in (0.665, 0.465, 0.265):
    arrow(ax, (0.67, y), (0.76, 0.49), color=GRAY, lw=1.1)
ax.text(
    0.50,
    0.08,
    "Line width is not a transparent mass proxy when radiative transfer dominates.",
    ha="center",
    color=RED,
    weight="bold",
    fontsize=9.8,
)
save(fig, "figure_15_source_shell_separation")

# ---------------------------------------------------------------------------
# Figure 16: cross-channel rescue.
# ---------------------------------------------------------------------------
fig, ax = canvas(title="Cross-channel rescue: a weak trigger becomes an identified event")
box(ax, (0.04, 0.58), (0.18, 0.15), "Soft X-ray trigger", LAPIS, subtitle="weak but time-localized")
box(ax, (0.27, 0.58), (0.18, 0.15), "Optical match", MAL, subtitle="position and association")
box(ax, (0.50, 0.58), (0.18, 0.15), "Spectroscopy", COPPER, subtitle="Type Ic-BL class")
box(
    ax,
    (0.73, 0.58),
    (0.18, 0.15),
    "Radio / late time",
    GOLD,
    tc=INK,
    subtitle="jet and engine bounds",
    subtitle_tc=INK,
)
for x in (0.22, 0.45, 0.68):
    arrow(ax, (x, 0.655), (x + 0.05, 0.655), color=GRAY, lw=1.4)
box(
    ax,
    (0.28, 0.27),
    (0.44, 0.16),
    "Engine-driven transient certificate",
    NAVY,
    subtitle="association + class + temporal power + bounded alternatives",
)
for x in (0.13, 0.36, 0.59, 0.82):
    arrow(ax, (x, 0.58), (0.50, 0.43), color=GOLD, lw=1.0)
ax.text(
    0.50,
    0.10,
    "More exposure in one ambiguous band is not equivalent to an orthogonal messenger.",
    ha="center",
    color=INK,
    weight="bold",
    fontsize=9.8,
)
save(fig, "figure_16_cross_channel_rescue")

# ---------------------------------------------------------------------------
# Figure 17: self-detuning plasma.
# ---------------------------------------------------------------------------
fig, ax = canvas(title="Self-detuning visibility: nonlinear response can shut the channel")
labels = [
    (0.04, "Hidden drive", RED, "dark-photon field"),
    (0.25, "Resonant mode", LAPIS, "Langmuir wave grows"),
    (0.46, "Medium changes", COPPER, "density structure forms"),
    (0.67, "Frequency shifts", GOLD, "local resonance detunes"),
    (0.84, "Saturation", MAL, "conversion is suppressed"),
]
for x, title, color, sub in labels:
    w = 0.14 if x < 0.84 else 0.12
    box(
        ax,
        (x, 0.56),
        (w, 0.16),
        title,
        color,
        tc=INK if color == GOLD else WHITE,
        subtitle=sub,
        subtitle_tc=INK if color == GOLD else WHITE,
    )
for i in range(len(labels) - 1):
    x = labels[i][0] + (0.14 if labels[i][0] < 0.84 else 0.12)
    arrow(ax, (x, 0.64), (labels[i + 1][0], 0.64), color=GRAY, lw=1.3)
box(
    ax,
    (0.30, 0.24),
    (0.40, 0.14),
    "Backreaction audit",
    NAVY,
    subtitle="compare resonance shift with effective width",
)
arrow(ax, (0.72, 0.56), (0.66, 0.38), color=RED, lw=1.4, rad=0.15)
ax.text(
    0.50,
    0.10,
    r"Proposed diagnostic: $\Xi_{br}=|\delta\omega_{medium}|/\Gamma_{res}$",
    ha="center",
    color=INK,
    weight="bold",
    fontsize=10,
)
save(fig, "figure_17_self_detuning_plasma")

# ---------------------------------------------------------------------------
# Figure 18: catastrophic tomography.
# ---------------------------------------------------------------------------
fig, ax = canvas(title="Catastrophic tomography: exposure and context loss occur together")
box(
    ax,
    (0.05, 0.58),
    (0.18, 0.16),
    "Differentiated parent",
    NAVY,
    subtitle="ice-rich shell · altered interior",
)
box(ax, (0.30, 0.58), (0.17, 0.16), "Catastrophe", RED, subtitle="capture · collision · shredding")
box(ax, (0.54, 0.58), (0.17, 0.16), "Debris filter", COPPER, subtitle="heating · escape · sorting")
box(ax, (0.78, 0.58), (0.17, 0.16), "Reaccreted archive", MAL, subtitle="moons and rings")
for x in (0.23, 0.47, 0.71):
    arrow(ax, (x, 0.66), (x + 0.07, 0.66), color=GOLD, lw=1.5)
box(
    ax,
    (0.12, 0.24),
    (0.30, 0.14),
    "Information gained",
    LAPIS,
    subtitle="deep mineralogy becomes exposed",
)
box(
    ax,
    (0.58, 0.24),
    (0.30, 0.14),
    "Information lost",
    RED,
    subtitle="depth · parent · chronology · geometry",
)
arrow(ax, (0.86, 0.58), (0.73, 0.38), color=GRAY, lw=1.1)
arrow(ax, (0.86, 0.58), (0.27, 0.38), color=GRAY, lw=1.1, rad=-0.2)
ax.text(
    0.50,
    0.09,
    "An exposed interior is a transformed archive, not a pristine cross-section.",
    ha="center",
    color=INK,
    weight="bold",
    fontsize=10,
)
save(fig, "figure_18_catastrophic_tomography")

print("generated", len(list(OUT.glob("figure_*.png"))), "PNG figures")
