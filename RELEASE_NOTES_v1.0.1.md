# SPPT/ASTRA v1.0.1

This is the first public versioned reference package for **Solar-Planetary Phase-Partition Theory (SPPT)** and its **Astronomical State-Topology and Reservoir Analysis (ASTRA)** inference layer.

## Scope and evidence

The release is a **not-peer-reviewed perspective and mathematical framework with reduced synthetic demonstrations**. Admitted analytical results are source-asserted and hand-checked; the reduced calculations and frozen synthetic benchmarks are mechanically replayed or independently reproduced as recorded in `CLAIM_MATRIX.json`. Numerical agreement is not proof, and the package contains no empirical planetary validation or claim of priority.

## Contents and reproduction

The seven release assets contain tagged PDFs, self-contained accessible HTML editions, a deterministic source/reproducibility archive, checksums, and a detached release identity. Reproduce the tracked package on the frozen Windows x86-64 reference runtime with:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-lock.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe tools\verify.py --all --workers 4
```

The release gate executes 55 discovered unit, invariant, evidence-boundary, document-contract, optimizer, and negative release-integrity tests; strict Ruff and mypy checks; CFF schema validation; privacy, path, metadata, citation-key, license, HTML, PDF, cache-boundary, and archive checks; the complete frozen numerical replay; figure regeneration; two byte-identity document builds; and fresh-clone, linked-worktree, and extracted-git-archive verification. The 64-seed ensemble uses frozen seeds, 12 declared multistarts per fitted family, convergence diagnostics, bound flags, and preserved negative outcomes.

## Synthetic-data status and limitations

Training BIC selects the generating chain in 64/64 frozen realizations. The post-selection held-out comparison preserves the negative result that the overconnected triangle has lower RMSE in 23/64 realizations; its shortcut reaches the declared lower bound in 29/64. The data are transparent, synthetic, deliberately favorable demonstrations—not blinded evidence, an external validation, a general false-positive-rate estimate, or predictive superiority over planetary observations.

The hybrid topology syntax does not establish general existence, uniqueness, reset-map closure, simultaneous-guard resolution, or non-Zeno behavior. The static and weak-cut results retain their stated positivity, connectivity, injectivity, equilibrium, and domain hypotheses. Electrochemical terms describe supplied free-energy conversion, not latent heat or spontaneous planetary sequestration.

## Licensing

Original software is MIT licensed. Original manuscript text, documentation, figures, and generated results are CC BY 4.0. Bibliographic references and third-party components retain their own terms. See `LICENSE_MAP.md` and `THIRD_PARTY_NOTICES.md` in the source archive.

## Preservation

Zenodo DOI pending automatic ingestion through the GitHub integration. No manual Zenodo deposit or separately reserved DOI is used.
