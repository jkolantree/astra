# Phase-Reservoir Topology as a Hidden State Variable in Planetary Evolution

This is the versioned reference package for **Solar-Planetary Phase-Partition Theory (SPPT)** and its inference layer, **ASTRA — Astronomical State-Topology and Reservoir Analysis**. SPPT represents planetary material and energy reservoirs as a physically constrained network whose topology may itself be a latent state; ASTRA compares admissible candidate networks against observations and simpler baselines.

Version **1.0.1** is a **not-peer-reviewed perspective and mathematical framework with reduced synthetic demonstrations**. It is not an empirical planetary validation, a mission-data retrieval, a claim of general hybrid-system well-posedness, or evidence of scientific priority. The benchmark is transparent and deliberately favorable; all generation constants are public.

## Read the work

- [Accessible preprint (self-contained HTML)](manuscript/SPPT_ASTRA_preprint_v1.0.1.html)
- [Preprint PDF](manuscript/SPPT_ASTRA_preprint_v1.0.1.pdf)
- [Accessible technical supplement (self-contained HTML)](manuscript/SPPT_ASTRA_technical_supplement_v1.0.1.html)
- [Technical supplement PDF](manuscript/SPPT_ASTRA_technical_supplement_v1.0.1.pdf)
- [Authoritative preprint source](manuscript/manuscript.md)
- [Authoritative supplement source](manuscript/supplement.md)
- [Claim-admission matrix](CLAIM_MATRIX.json)

The HTML editions are the primary accessible reading path. The PDFs are synchronized tagged visual editions with normalized metadata; their text, metadata, fonts, links, and structure are mechanically checked, and every rendered page is visually inspected at the release gate.

## Scientific scope

The release admits bounded results about:

- exact network inventory conservation under stated transport and reaction hypotheses;
- the periodic trap solution and its two distinct loop normalizations;
- a weak-cut spectral bound for positive capacities and a connected positive-weight graph;
- state-dependent transport with the complete derivative, including `K(1-dTu/dTd)`;
- classical heterogeneous nucleation with a substrate-dependent wetting factor;
- static-boundary non-identifiability for `K > 0` and an injective radiation law on the physical domain;
- deterministic reduced synthetic topology-selection and frequency-response demonstrations.

The raw inventory-loop magnitude is monotone in release time at fixed forcing frequency; only the release-normalized loop peaks at `omega*tau = 1`. Topology-changing dynamics are a proposed syntax, not a general existence, uniqueness, reset-closure, simultaneous-guard, or non-Zeno theorem. Electrochemical conversion is labeled supplied free-energy conversion, not latent heat or spontaneous planetary sequestration.

## Synthetic benchmark boundary

Across 64 frozen Gaussian-noise realizations, training BIC selects the minimum generating chain in 64/64 runs. The held-out forcing comparison occurs after selection and preserves a negative result: the overconnected triangle has lower held-out RMSE in 23/64 runs. Its added edge reaches the declared lower bound in 29/64 runs, so the shortcut distribution is censored. These are mechanically replayed synthetic outcomes, not proof, external validation, or a general false-positive-rate estimate.

## Reproduce

Requirements:

- CPython **3.12.13** (`.python-version`)
- dependencies from `requirements-lock.txt`, installed with hashes
- Playwright Chromium **151.0.7922.34**, revision **1234**, installed by Playwright 1.62.0 for tagged PDF generation

On Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-lock.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe tools\verify.py --all
```

On another supported shell, activate an equivalent Python 3.12.13 environment and run the same Python module commands. `tools/verify.py --all` performs complete test discovery, lint and type checks, metadata/schema checks, privacy and path scans, scientific replay, figure regeneration, document rebuild, deterministic-output comparison, PDF inspection, manifest checks, and release-integrity negative tests.

Focused commands:

```text
python -m pytest -q
python scripts/make_figures.py
python tools/build_documents.py
python tools/verify.py
```

Builds write only beneath the repository or a disposable output root. Seeds, multistart points, optimizer convergence diagnostics, bound flags, and all negative outcomes are preserved in `data/`.

## Repository map

| Path | Contents |
|---|---|
| `manuscript/` | Authoritative Markdown, bibliography, accessible HTML, synchronized PDF |
| `src/` | Auditable reduced SPPT and ASTRA calculations |
| `scripts/` | Deterministic scientific reproductions and figure generation |
| `tests/` | Unit, invariant, numerical, evidence-boundary, and release-integrity tests |
| `data/` | Generated CSV and JSON outputs, including all negative outcomes |
| `figures/` | Generated manuscript and supplement figures |
| `tools/` | Canonical verification, document, manifest, and release-identity tooling |
| `SOURCE_INVENTORY.json` | Hash, media, attribution, rights, and alias inventory for every supplied source artifact |
| `CLAIM_MATRIX.json` | Consequential claims, hypotheses, evidence classes, limitations, and dispositions |

## Citation

Canonical citation metadata are in [`CITATION.cff`](CITATION.cff). Until the automatic Zenodo record is verified, cite the versioned GitHub release:

> Jacko T. (2026). *Phase-Reservoir Topology as a Hidden State Variable in Planetary Evolution*, version 1.0.1. GitHub. https://github.com/jkolantree/astra/releases/tag/v1.0.1

The post-release documentation commit will add the verified version DOI, concept DOI badge if exposed, and final citation guidance without changing the release tag or archived bytes.

## Licensing and correspondence

Original software is MIT licensed. Original manuscript text, documentation, figures, generated data, and results are CC BY 4.0. See [`LICENSE_MAP.md`](LICENSE_MAP.md) and [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md). Cited works remain under their own terms.

Use [GitHub Issues](https://github.com/jkolantree/astra/issues) for public correspondence. No private email, location, institution, ORCID, or legal identity is published.
