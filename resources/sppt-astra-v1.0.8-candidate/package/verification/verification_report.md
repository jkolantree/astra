---
title: "SPPT / ASTRA v1.0.8 Candidate Verification Report"
author: "Jacko T. / ASTRA role-based audit"
date: "16 August 2026"
---

# Verdict

**REVIEWED UNPROMOTED CANDIDATE.** The repaired source, ledgers, figures, document derivatives, and package identity pass the declared local checks. This is not a v1.0.8 release, external peer review, empirical validation, or authorization to alter the immutable v1.0.7 edition.

# Repository and intake identity

- Stable release: `v1.0.7`, commit `7454b8134cf28c233fe54a11ae4b65e256844821`.
- Candidate source basis: `main` commit `f8b32ef0af9cb6804f256490b4daafbdba43740e`.
- Supplied intake ZIP SHA-256: `55b8962176680859064fa2ebc009bb45ddc0cce987bce0bc16206faa4c7c387a`.
- The intake ZIP had 67 files, no unsafe or duplicate members, and matching internal checksums. Its known-defective document bytes were not promoted unchanged.

# Scientific and identity repair

- 75 unique claims: all 55 canonical v1.0.7 records preserved, plus 20 noncolliding `V108-*` records.
- 51 unique source records; 49 of 49 manuscript citation keys resolve.
- Public claim IDs are not reused. `V108-R002` records the frozen candidate basis and `V108-F002` refines the dynamic-arrest definition without changing `V107-F003`.
- Generic joint source/transducer inference is identified as prior art; the candidate contribution is the typed stateful integration and audit vocabulary.
- The M1 weak-cut, dynamic-arrest, and claim-coverage corrections remain visibly unpromoted.

# Rebuilt outputs

| Output | Pages | Verified role |
|---|---:|---|
| Canonical PDF | 81 | ordinary reading and repository review |
| Peer-review PDF | 128 | 12-point, double-spaced, continuously line-numbered review copy |
| Tagged reading PDF | 80 | HTML/Chromium structured reading alternative; not PDF/UA |
| Verification-report PDF | 4 | compact package-boundary report |
| Editable DOCX | not rendered locally | editing source with 18 described figures and deterministic package metadata |

The complete producer ran under CPython 3.12.10 with Pandoc 3.6.1, Tectonic 0.17.0, Matplotlib 3.11.1, Playwright 1.62.0, pikepdf 10.11.0, and a task-local pure-Python copy of python-docx 1.2.0. The latter is a build-only dependency and is not part of the repository runtime lock.

# Visual and structural verification

- All 81 canonical, 128 peer-review, 80 tagged, and 4 report pages were rendered with Poppler and reviewed through contact sheets and targeted full-page views.
- PDFium independently rendered all four PDFs without error.
- Geometry scans found zero words outside any page box and confirmed the formerly clipped commit, active-support, and prime-reduction passages are complete.
- All PDF fonts are embedded and mapped to Unicode. Chromium's structured editions include embedded Type 3 subsets; each has a `ToUnicode` map.
- The tagged reading edition has a structure tree and `en-US` language metadata; no PDF/UA claim is made.
- All 18 SVG/PNG pairs were regenerated. SVG labels remain live text, metadata dates are fixed, and external DTD/resource references are absent.
- Figure 9 now gives “Thermodynamic” a safe internal margin. Figure 10 no longer uses unexplained color-coded points.
- DOCX accessibility: 0 high, 0 medium, 49 low findings. The low findings are displayed raw URLs, not missing image descriptions.

# Acceptance summary

| Status | Count |
|---|---:|
| PASS | 31 |
| ENVIRONMENT_LIMITED | 2 |
| NOT_RUN | 6 |
| DEFERRED | 1 |
| FAIL | 0 |

The complete matrix is `verification/acceptance_gate_matrix.csv`.

# Limits and external gates

- Word and LibreOffice were unavailable, so DOCX page-layout equivalence is `ENVIRONMENT_LIMITED`; structural, metadata, relationship, image-description, and accessibility checks did run.
- Ghostscript was unavailable, so no Ghostscript pass is claimed.
- GitHub PR CI is external to these package bytes and remains `NOT_RUN` until push.
- Fresh release replay, a tag, GitHub Release, Pages publication, DOI, and Zenodo action are outside this candidate.
- External peer review, independent raw-data reanalysis, experimental replication, and a complete sentence-level source-entailment audit remain absent or deferred.

The local checks support repository admission as an unpromoted review candidate. They do not certify the scientific proposal as established fact or transform this branch into an immutable release.
