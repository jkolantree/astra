# UNREPLAYED SUPPLIED PRODUCER REPORT — NOT A CURRENT VERIFICATION

This file is retained as provenance from the attached ZIP. Its PASS statements
were not accepted as independent evidence; the current local audit is
`LOCAL_AUDIT.md`, which records the render/tool limitations and repairs.

# ASTRA Sector-Complete Instrument Module v0.1.0-alpha.1
## Local verification report

**Verdict:** PASS for the declared local milestone.

**Scope:** mathematical correction, typed schema, frozen synthetic benchmark, controls, tests, documents, and local package integrity. This verdict is not an empirical validation of a real duality defect, hidden sector, dark matter, or any cited experiment.

## Blocking correction

- The prior trace-of-commutator observation equation was removed.
- `test_trace_of_commutator_is_zero` confirms the finite-dimensional regression guard.
- The module uses POVM/channel and quantum-instrument forms.
- Counts use a multinomial model in the benchmark; no universal additive-noise claim remains.

## Benchmark result

- Local equivalence classes: `{reflect}`, `{absorb, string_transmit}`, `{local_transmit}`.
- Sector-complete equivalence classes: four singleton classes.
- Local Fisher rank: 2.
- Sector-complete Fisher rank: 3.
- Local mutual information with 2% detector confusion: 1.343487 bits.
- Sector-complete mutual information with 2% detector confusion: 1.853974 bits.
- Local classification accuracy: 0.7525.
- Sector-complete classification accuracy: 1.0000.
- Out-of-set hybrid: rejected by the four-pure-generator candidate set.
- Frozen benchmark SHA-256: `ad7b450635e06410fe4a8e5f9227bc38f6a12eb1878fa2e1ada58cde3a65971a`.

## Controls

- broken-matching/reflection control: PASS;
- detector-confusion sweep: PASS;
- finite-boundary toy control: PASS;
- out-of-set model-mismatch control: PASS;
- probability and global-excitation ledger: PASS;
- energy and charge overclaim guard: PASS;
- dark-matter `proposed_only` firewall: PASS.

## Software

- `pytest`: 27 passed.
- Python source compilation: PASS.
- JSON Schema validation: PASS.
- Frozen JSON and CSV outputs generated successfully.

## Document QA

### Canonical PDF

- 23 US-Letter pages.
- Openable and not encrypted.
- Text is selectable.
- Visual inspection performed on all pages at 150 dpi.
- Independent Poppler and PDFium renders were inspected side by side; no missing figures, clipping, overlap, malformed equations, or renderer-specific geometry failures were found.
- PDF is not tagged. A separate tagged reading edition is included.

### Tagged reading PDF

- 22 US-Letter pages.
- LibreOffice reports `Tagged: yes`.
- Openable and not encrypted.
- Derived from the verified DOCX reading edition.

### DOCX

- 22 rendered pages.
- Every page visually inspected after LibreOffice rendering.
- Accessibility audit: 0 high, 0 medium, 0 low findings.
- No empty table-of-contents field remains.

## Source and provenance caveats

- The supplied methods input hash was recorded as supplied but could not be independently recomputed because the exact source object was not present locally.
- The source-map versions and primary links were carried from the supplied audit.
- This milestone did not independently verify every version of record or reproduce experiments from raw data.
- No external specialist, cited author, institution, journal, or collaboration is represented as having reviewed or endorsed the module.
- No repository, GitHub, Zenodo, DOI, release, tag, or publication action was taken.

## Acceptance gates

All 20 local gates in `verification/acceptance_gate_matrix.csv` pass.
