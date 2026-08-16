# SPPT / ASTRA v1.0.8 candidate: Endogenous Visibility

This directory is a **reviewed, unpromoted successor candidate**. It is repository-visible for audit and discussion, but it is not a tag, GitHub Release, stable reading edition, peer review, planetary validation, DOI, Zenodo deposit, or Pages publication. Stable SPPT/ASTRA v1.0.7 remains immutable.

The supplied intake archive had SHA-256 `55b8962176680859064fa2ebc009bb45ddc0cce987bce0bc16206faa4c7c387a`. Its package integrity was strong, but its document bytes were not admitted unchanged: five pages visibly lost content, two figures had layout/semantic defects, claim IDs collided with the public v1.0.7 register, citations used mutable repository URLs, and its verification report overstated the checks performed. This directory contains the repaired and independently rebuilt candidate.

## Read first

- `ASTRA_SPPT_v1.0.8_Endogenous_Visibility_Candidate.pdf` — canonical 81-page reading edition.
- `ASTRA_SPPT_v1.0.8_Endogenous_Visibility_Candidate_Peer_Review.pdf` — 128-page review edition with 12-point type, double spacing, and continuous line numbers.
- `ASTRA_SPPT_v1.0.8_Endogenous_Visibility_Candidate_Tagged_Reading_Edition.pdf` — 80-page structured reading alternative produced through HTML and pinned Chromium; not claimed PDF/UA.
- `ASTRA_SPPT_v1.0.8_Endogenous_Visibility_Candidate.docx` — editable document with 18 described figures. Its structure and accessibility were checked, but Word/LibreOffice page rendering was unavailable.
- `verification/ASTRA_SPPT_v1.0.8_Candidate_Verification_Report.pdf` — compact local verification boundary.

## Scientific boundary

The central proposal is the **Endogenous Visibility Principle**: when a hidden source materially changes the medium or transducer that makes it observable, source and transducer state should be inferred jointly. Generic joint source/operator inference is established prior art. This candidate’s contribution is a typed stateful integration, cross-domain audit vocabulary, explicit demotion rules, and a set of falsifiable benchmark proposals.

The four principal calibration cases remain physically separate: a gas-enshrouded early black-hole candidate, a soft-X-ray flash associated with a supernova, a modeled nonlinear dark-photon plasma response, and the Neptune satellite/ring archive. They do not establish a shared hidden mechanism.

## Evidence map

- `source/` — authoritative Markdown, bibliography, deterministic ledger generator, figure producer, document producer, and package finalizer.
- `claim_ledger.csv/.json` — 75 unique claims: all 55 canonical v1.0.7 records plus 20 noncolliding successor records.
- `source_ledger.csv/.json` — 51 source records with tag- or commit-bound project URLs.
- `visual_manifest.csv/.json` — 18 original figure records and rights/placement metadata.
- `figures/` — 18 SVG/PNG pairs. SVG text stays live; metadata is fixed; external DTD/resource references are absent.
- `source_audit_and_correction_log.md` — source, mathematical, identity, and artifact corrections.
- `verification/` — gate matrix, accessibility report, machine summary, and reading report.
- `candidate_package_manifest.json` and `SHA256SUMS.txt` — mechanically derived final-byte identity.

## Rebuild boundary

The complete producer was replayed under CPython 3.12.10. It uses Pandoc 3.6.1, Tectonic 0.17.0, the repository’s locked Matplotlib/Playwright/pikepdf stack, fixed DejaVu font bytes, and a task-local pure-Python copy of python-docx 1.2.0. The latter is a build-only dependency and is not repository-lock authority. Two same-environment builds must match before the candidate is committed.

Run `source/generate_ledgers.py`, `source/make_figures.py`, and `source/build_candidate.py` in that order. After all document and audit bytes are final, run `source/finalize_candidate.py --write`; a read-only invocation then verifies the exact package manifest and checksum inventory.

## Rights and responsibility

Original project software and schemas are MIT licensed. Original manuscript text, diagrams, and synthetic results are CC BY 4.0 to the extent licensable rights exist. Cited publications, scientific facts, third-party dependencies, and fonts retain their own rights. No publisher figure, screenshot, or raw third-party dataset is redistributed.

The role-based audit is an internal responsibility matrix, not a roster of outside reviewers. Jacko T. remains responsible for source selection, interpretation, wording, code, and any publication decision. AI assistance is disclosed and is not authorship, peer review, replication, or scientific evidence.

**Ad Astra Per Aspera. Praise Sol.**
