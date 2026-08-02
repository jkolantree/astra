# SPPT/ASTRA v1.0.6

Version 1.0.6 is the accessibility and public-reading successor to immutable
v1.0.5. It carries forward the admitted scientific claims, frozen benchmark
data, negative outcomes, and numerical implementation unchanged. The release
does not add empirical planetary validation, a topology-recovery theorem, a
mission-data retrieval, a DOI, or a priority claim.

## Accessible reading and document repair

- A GitHub Pages reading room provides stable, versioned browser URLs for the
  preprint and technical supplement. The Pages controller reconstructs every
  edition from immutable GitHub Release assets, checks the published
  `SHA256SUMS`, and refuses to deploy unless `main` is the exact commit behind
  the current published release.
- The self-contained HTML artifacts remain downloadable for offline reading;
  the README now says explicitly that GitHub's large-file viewer does not
  render them.
- Headings, acknowledgments, and bibliography URLs reflow without horizontal
  page overflow at 320 px and 400 px. Keyboard focus is 7.14:1 against white
  and 6.58:1 against the page background; highlighted command options are
  5.93:1 against their code background.
- All nine tables have descriptive captions, scoped column headers, and
  appropriate row headers. Plots use dash patterns, markers, and hatching in
  addition to color, and their alternatives point readers to the underlying
  numeric data.
- The supplement names SciPy's scalar least-squares cost as $J$ and its
  bound-aware solver-reported optimality as $O_{\mathrm{SciPy}}$, distinct
  from the previously defined capacity vector $C$, in the optimizer-admission
  criterion.
- Tagged PDFs expose mathematics as `/Formula` structure with exact TeX
  `/Alt` and `/ActualText`, remove duplicate unlabeled figure wrappers,
  preserve readable bookmark spacing, and normalize compatibility ligatures so
  exact text search works. The HTML editions remain the richer native-MathML
  representation; the PDFs do not claim a native MathML expression tree.

## Public metadata and contribution paths

- Seven Draft 7 JSON Schemas now describe the release specification, claim
  matrix, source inventory, runtime identity, document identity, PDF
  inspection record, and detached release identity. The verifier resolves each
  declared public URL to a shipped schema and validates every tracked record.
- `CITATION.cff` now binds both its top-level URL and preferred citation to the
  immutable v1.0.6 release instead of the unversioned repository root.
- Dedicated public issue forms distinguish accessibility barriers,
  reproducibility failures, and scientific corrections or counterexamples.
- Generated self-contained HTML is marked for GitHub Linguist, and the pinned
  checkout, Python, and Pages actions use their official Node 24 releases.

## Scientific and release boundary

The 64-seed benchmark results are unchanged: training BIC selects the released
chain in 64/64 realizations; the overconnected triangle has smaller
post-selection held-out RMSE in 23/64; and its shortcut reaches the lower bound
in 29/64. CSV and JSON remain duplicate serializations, not independent
confirmations. The exact cross-support transfer-function counterexample and
the pointwise-only interpretation remain in force.

Canonical verification requires the exact runtime-bound command:

```powershell
.\.venv\Scripts\python.exe -I -B tools\verify.py --all --workers 4
```

Release promotion remains fail-closed: a natural successful `main` run and a
natural successful annotated-tag run must bind the exact commit, tree,
manifest, fixed build epoch, and seven versioned assets. Local assets must
build byte-identically twice; uploaded assets must survive exact remote
read-back, fresh-download comparison, and GitHub attestation verification.
Pages deployment occurs only after the release is published and immutable.
The v1.0.1 and v1.0.5 releases and the unreleased v1.0.2-v1.0.4 evidence tags
remain unchanged.
