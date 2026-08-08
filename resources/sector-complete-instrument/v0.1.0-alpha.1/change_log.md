# Change log: ASTRA sector-complete instrument module

## Local integration bridge — 2026-08-07

- Added the module as a namespaced GitHub prerelease under
  `resources/sector-complete-instrument/v0.1.0-alpha.1`; immutable core and
  Earth-release identities remain unchanged.
- Repaired the supplied code/schema mismatch: the typed transduction record now
  emits an object-valued conservation ledger, unresolved-sector bounds, and an
  identifiability object required by the JSON Schema.
- Made the benchmark headless and byte-stable for text outputs by forcing the
  Matplotlib `Agg` backend and LF-normalizing JSON/CSV/checksum writes.
- Reclassified the out-of-set chi-square value as a best-of-four selection
  diagnostic and records a conservative selection-adjusted upper bound plus
  log-survival value; it is not an unadjusted universal p-value.
- Added source-level magnet bridges for Amaral (published null search), Ji
  (LeMaMa metrology), and Tian (accepted interaction-bounds record), preserving
  their different units, status, and dark-matter limitations.
- The supplied PDF/DOCX visual claims remain producer-reported review inputs;
  they are not release assets, and no PDF accessibility result is claimed.

## Corrections

- Removed the invalid observation equation based on `Tr[O, E(rho)]`.
- Replaced it with POVM/channel and quantum-instrument forms.
- Removed generic additive noise from the universal equation. Counts use a multinomial model in the benchmark; continuous measurements require their own likelihood and units.
- Separated probability normalization from energy, charge, entropy, and accessible-information accounting.

## New typed fields

- input/output carrier;
- input/output sector;
- selection and conditioning;
- interface Hilbert/state description;
- active control route;
- observable basis;
- calibration and units;
- conservation/exchange ledger;
- unresolved-sector bounds;
- model-mediated inversion;
- identifiability quotient and Fisher null directions;
- predeclared rejection test;
- interpretation status.

## New benchmark

- four generators: reflect, absorb, local transmit, string transmit;
- local equivalence class explicitly preserved;
- sector-complete measurement resolves the frozen model;
- broken-duality, detector-noise, finite-boundary, and model-mismatch controls;
- frozen JSON/CSV outputs, figures, SHA-256, and 29 local tests.

## Guardrails

- no claim that the benchmark models a real duality defect;
- no claim that cited papers identify dark matter;
- all dark-matter records remain `proposed_only`;
- no core release, Earth-line release, Pages route, DOI, or Zenodo action was
  taken.
