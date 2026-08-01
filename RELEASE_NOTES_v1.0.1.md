# SPPT/ASTRA v1.0.1

This is the first public versioned reference package for **Solar-Planetary Phase-Partition Theory (SPPT)** and its **Astronomical State-Topology and Reservoir Analysis (ASTRA)** inference layer.

## Scope and evidence

The release is a **not-peer-reviewed perspective and mathematical framework with reduced synthetic demonstrations**. Admitted analytical results are source-asserted and hand-checked; the reduced calculations and frozen synthetic benchmarks are mechanically replayed or independently reproduced as recorded in `CLAIM_MATRIX.json`. Numerical agreement is not proof, and the package contains no empirical planetary validation or claim of priority.

## Contents and reproduction

The seven release assets contain tagged PDFs, self-contained accessible HTML editions, a deterministic source/reproducibility archive, checksums, and a detached release identity. Reproduce the tracked package on the frozen Windows x86-64 reference runtime with:

```powershell
py -3.12 -c "import platform; assert platform.python_version() == '3.12.10', platform.python_version()"
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-lock.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe tools\verify.py --all --workers 4
```

The release gate executes 67 discovered unit, invariant, evidence-boundary, document-contract, optimizer, runtime-identity, and negative release-integrity tests; strict Ruff and mypy checks; CFF schema validation; privacy, path, metadata, citation-key, license, HTML, PDF, cache-boundary, and archive checks; the complete frozen numerical replay; figure regeneration; two byte-identity document builds; and fresh-clone, linked-worktree, and extracted-git-archive verification. The 64-seed ensemble uses frozen seeds, 20 distinct generic multistarts per fitted family, full per-start and per-endpoint convergence diagnostics, a fail-closed materially-better-endpoint check, bound flags, and preserved negative outcomes. The 20-start design was strengthened during release audit after this same benchmark exposed a missed endpoint under the earlier 12-start design, so the reruns are regression evidence rather than untouched evaluation. Byte identity is scoped to the exercised outputs under CPython 3.12.10, Git for Windows 2.55.0.windows.3, the probed single-thread NumPy and SciPy OpenBLAS Haswell kernels, and the recorded PDF font inputs on compatible Windows x86-64 hardware.

## Synthetic-data status and limitations

Training BIC selects the generating chain in 64/64 frozen realizations. The post-selection held-out comparison preserves the negative result that the overconnected triangle has lower RMSE in 23/64 realizations; its shortcut reaches the declared lower bound in 29/64. The data are transparent, synthetic, deliberately favorable demonstrations—not blinded evidence, an external validation, a general false-positive-rate estimate, or predictive superiority over planetary observations.

The hybrid topology syntax does not establish general existence, uniqueness, reset-map closure, simultaneous-guard resolution, or non-Zeno behavior. The static and weak-cut results retain their stated positivity, connectivity, injectivity, equilibrium, and domain hypotheses. Electrochemical terms describe supplied free-energy conversion, not latent heat or spontaneous planetary sequestration.

The manuscript also contains a proposed-only typed-layer research outlook added after review of four 2026 primary studies. One diamond inclusion with no observed present fracture or exterior connection is a qualified present-isolation example; permeability and past exchange were not measured. The moonlight, quantum-sampling, and xenophagocytosis studies are structural analogies only. None validates SPPT or changes the implemented physical core. A universal selectivity--throughput law is explicitly deferred, and a new no-go rule forbids substituting an observation, semantic association, biological recognition signal, or certificate for a physical transport edge without a constitutive bridge.

Conceptual provenance records the author-reported dream/collage/ChatGPT origin of the cold-trap/Saturn idea and subsequent OpenAI language-model assistance. Neither the dream, the excluded collage, the unpublished chat, nor model output is evidence. No third-party article text or figure is redistributed.

## Licensing

Original software is MIT licensed. Original manuscript text, documentation, figures, and generated results are CC BY 4.0. Bibliographic references and third-party components retain their own terms. See `LICENSE_MAP.md` and `THIRD_PARTY_NOTICES.md` in the source archive.

## Preservation

Zenodo DOI pending automatic ingestion through the GitHub integration. No manual Zenodo deposit or separately reserved DOI is used.
