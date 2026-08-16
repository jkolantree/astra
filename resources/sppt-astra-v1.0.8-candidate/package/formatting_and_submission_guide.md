# Formatting and submission guide

## Purpose

The candidate provides complementary reading formats without pretending that one layout satisfies every review or accessibility context.

## Delivered formats

- **Canonical PDF:** 81 US-Letter pages, one column, 11-point serif body, linked contents, native selectable-text cover, and figures placed with their discussion.
- **Peer-review PDF:** 128 US-Letter pages, 12-point type, double spacing, one column, continuous line numbering, page numbers, and integrated figures/legends.
- **Tagged reading PDF:** 80 US-Letter pages generated through self-contained HTML and pinned Chromium. It has a structure tree and `en-US` metadata, but no PDF/UA claim.
- **Editable DOCX:** 11-point serif body, explicit paragraph spacing, repeating table headers, deterministic contents list, page numbers, and 18 image descriptions. Word/LibreOffice rendering was unavailable, so exact page count and cross-renderer layout remain `ENVIRONMENT_LIMITED`.

## Figure rules

- Eighteen figures are supplied as proportional PNG previews and SVG sources with live `<text>` labels.
- The generator fixes the canvas, SVG hash salt, metadata date, and DejaVu Sans font family.
- Legacy external SVG DTD declarations are removed; all drawable references are internal.
- Labels use safe internal margins and line weights intended to survive ordinary document reduction.
- Color is used only to distinguish declared roles or categorical regions; no unexplained data points remain.
- Captions identify the visual class, explain what the diagram does and does not establish, and state creator/source/license boundaries.

## Readability rules

- One principal argument per paragraph where practical.
- Technical qualifications follow the claim they constrain.
- Equations are introduced and interpreted in prose.
- Acronyms and domain terms are defined on first use.
- Long hashes and symbolic chains are reflowed or cross-referenced rather than forced through a page boundary.
- The candidate does not claim WCAG or PDF/UA conformance.

## Verification rule

Every final PDF page must be rendered after the last source edit. Contact-sheet review is paired with full-page inspection and an out-of-page word scan. A second renderer must open/render every page. DOCX structure/a11y checks do not substitute for Word or LibreOffice visual QA; when those applications are absent the result remains `ENVIRONMENT_LIMITED`.

## Submission boundary

This long-form methods/perspective candidate is not yet a journal submission. A future submission should either focus the endogenous-visibility method and move detailed audits/ledgers to supplements, or retain this document as an auditable preprint/monograph and submit narrower scientific studies separately. The appropriate study-specific reporting checklist must be chosen for any future empirical benchmark or experiment.

## Guidance consulted

- Nature, *Initial submission*: https://www.nature.com/nature/for-authors/initial-submission
- Nature, *Final submission*: https://www.nature.com/nature/for-authors/final-submission
- Nature Methods, *Writing and language*: https://www.nature.com/nmeth/submission-guidelines/writing-and-language
- PLOS Genetics, *Submission guidelines*: https://journals.plos.org/plosgenetics/s/submission-guidelines
- W3C, *WCAG 2.2 — Text Spacing*: https://www.w3.org/WAI/WCAG22/Understanding/text-spacing
- EQUATOR Network, *Selecting the appropriate reporting guideline*: https://www.equator-network.org/toolkits/selecting-the-appropriate-reporting-guideline/
