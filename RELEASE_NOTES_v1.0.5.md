# SPPT/ASTRA v1.0.5

This is the publishable successor to the audited v1.0.2, v1.0.3, and v1.0.4 candidates. Their public tags are retained unchanged as negative release-process evidence, but none has a GitHub Release. Version 1.0.5 carries forward the same scientific corrections and frozen numerical results, makes the release-integrity tests independent of ambient GitHub Actions state, and supersedes v1.0.1 for current use without rewriting or replacing its immutable tag or assets.

## Publication-controller evidence and test-harness correction

The v1.0.4 commit passed natural `main` run `30762828768`, including the complete deterministic scientific and document replay, Git-archive verification, and the clean-worktree gate. Its one natural tag run, `30764066469`, then passed all production tag-controller gates: exact Git and Python, restoration of annotated tag object `b163ccfed005ffcbb4b15a49644ea27e09d5a7ba`, hash-locked dependency installation, independent post-install tag verification, and pinned Chromium installation.

The tag run stopped at the first Pytest pass inside canonical verification. A unit test intentionally simulates an incomplete tag event by removing `GITHUB_SHA` and expecting the missing tag-ref check to fail first. On an actual tag runner, however, that test inherited the real `GITHUB_REF_TYPE`, `GITHUB_REF_NAME`, and `GITHUB_REF`; its v1.0.1 fixture therefore encountered the ambient v1.0.4 name before reaching the intended missing-ref condition. The run recorded 203 passing tests and one harness failure. Scientific replay did not start, no v1.0.4 GitHub Release or draft was created, and no assets were uploaded.

Version 1.0.5 makes the test boundary hermetic. Before every release-integrity test, an automatic fixture clears all ten GitHub context variables read by production code:

```text
GITHUB_ACTIONS
GITHUB_EVENT_NAME
GITHUB_EVENT_PATH
GITHUB_REF
GITHUB_REF_NAME
GITHUB_REF_TYPE
GITHUB_REPOSITORY
GITHUB_REPOSITORY_ID
GITHUB_SERVER_URL
GITHUB_SHA
```

Each simulated scenario must then declare its complete context. The previously failing test and the complete suite pass with a real v1.0.4 tag context injected outside Pytest. The production controller and workflow are unchanged: their v1.0.4 restore and post-install identity gates already passed. The controller continues to model the typed chain

```text
tag ref -> annotated tag object -> direct commit target
```

and binds the creation payload's `after` object to the annotated tag while independently binding `GITHUB_SHA` and `HEAD` to the direct commit.

## Scientific scope carried forward unchanged

The package remains a not-peer-reviewed perspective and mathematical framework with reduced synthetic demonstrations. It contains no empirical planetary validation, general topology-recovery theorem, mission-data retrieval, or claim that numerical agreement constitutes proof.

The v1.0.2 scientific corrections remain in force:

- Figure 5 applies its unit internal power consistently to the deep reservoir in both transient and equilibrium calculations.
- Exact algebraic-statistical counterexamples show that distinct positive reservoir-network supports can share the same surface transfer function under the declared single-port design.
- The released generating chain remains distinguishable only pointwise in the declared nonnegative candidate domain; the work does not establish family-wide physical-topology identification.
- The one-frequency demonstration uses amplitude alone and illustrates conditioning and finite-grid localization, not noise resistance or a minimal-data theorem.
- Numerical routines preserve representable slow modes, reject unresolved finite-scale inputs, and fail closed on non-finite, asymmetric, or shape-invalid inputs.

The frozen ensemble results are unchanged:

- Training BIC selects the released generating chain in 64/64 realizations.
- The overconnected triangle has lower post-selection held-out RMSE in 23/64 realizations.
- The triangle shortcut reaches its declared lower bound in 29/64 realizations.
- The 20-start design remains post-audit regression evidence rather than untouched, blinded, or external evaluation.

The CSV and JSON are duplicate serializations of the same synthetic evidence, not independent confirmations.

## Verification, identity, and preservation

Canonical verification requires the exact runtime-bound command:

```powershell
py -3.12 -I -B tools\verify.py --all --workers 4
```

Release identity binds the annotated tag object, direct commit, tree, tracked manifest, fixed build epoch, and exactly seven versioned assets. Promotion additionally requires one natural successful `main` run, one natural successful tag run, two identical local asset builds, exact remote read-back, fresh-download equality, and post-publication attestation verification.

v1.0.1 remains immutable. The public, unreleased v1.0.2, v1.0.3, and v1.0.4 tags remain unchanged and have no GitHub Releases. Original software remains MIT licensed; original manuscript text, documentation, figures, and generated results remain CC BY 4.0. Publication remains GitHub-only; no Zenodo ingestion or release DOI is claimed.
