# Visual preflight report

## Scope

The repaired candidate contains a selectable text-only cover and 18 original scientific figures, each supplied as SVG plus proportional PNG. No publisher art, news screenshot, or raw third-party image is redistributed.

## Intake failures preserved

The supplied package was not promoted unchanged. Independent full-page review found visible content loss on canonical pages 6, 30, and 63 and peer-review pages 45 and 96. Figure 9 left essentially no internal margin around “Thermodynamic.” Figure 10 used an unexplained yellow point. All 18 SVGs had outlined glyphs rather than live text and carried live generation timestamps. The original report’s “all pages passed” verdict was therefore invalid for those bytes.

## Repairs

- Reflowed the audited-commit record and the active-support/prime-reduction symbolic chains.
- Shortened the compact Appendix B commit display while retaining the full hash in Appendix C and the machine ledger.
- Enlarged the Figure 9 thermodynamic gate and reduced its title optically.
- Removed all unexplained Figure 10 points; quadrant labels now carry the classification.
- Regenerated all SVGs with live text, fixed hash salt/date, and no external DTD/resource.
- Kept fixed canvases, proportional placement, and native selectable cover text.

## Final PDF checks

| Edition | Pages | Poppler review | PDFium render | Out-of-page words |
|---|---:|---|---|---:|
| Canonical | 81 | all pages | all pages | 0 |
| Peer review | 128 | all pages | all pages | 0 |
| Tagged reading | 80 | all pages | all pages | 0 |
| Verification report | 4 | all pages | all pages | 0 |

The previously truncated phrases `residue → prediction` and `exact lifting or obstruction`, plus the full audited commit hash, are extractable in every manuscript edition where they belong. No replacement-character glyph was found. Contact sheets showed no unintended blank page, missing figure, page collision, or gross overflow; suspect regions were inspected at full size.

All PDF fonts are embedded and mapped to Unicode. The Tectonic editions use
Type 0/Type 1 fonts; the Chromium editions also contain embedded Type 3 subsets,
each with a `ToUnicode` map. The tagged reading PDF has a structure tree and
`en-US` language metadata; it is not claimed PDF/UA conformant.

## DOCX boundary

The DOCX opens as a valid package, has deterministic member timestamps, and contains 18 media files and 18 nonempty image descriptions. Its accessibility audit reports 0 high, 0 medium, and 49 low raw-URL findings. Word and LibreOffice were unavailable, so DOCX page-layout inspection is `ENVIRONMENT_LIMITED`; no page-count or cross-renderer-equivalence claim is made.

## Tool limits

Ghostscript was unavailable, so no Ghostscript interpretation result is claimed. Poppler and PDFium results do not transfer to unavailable renderers.

## Verdict

The final PDF and figure surfaces pass the declared local visual/structural checks. This is an artifact verdict for an unpromoted candidate, not scientific peer review, empirical reproduction, or release certification.
