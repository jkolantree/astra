# Phase-Reservoir Topology as a Hidden State Variable in Planetary Evolution

This is the versioned reference package for **Solar-Planetary Phase-Partition Theory (SPPT)** and its inference layer, **ASTRA — Astronomical State-Topology and Reservoir Analysis**. SPPT represents planetary material and energy reservoirs as a physically constrained network whose topology may itself be a latent state; ASTRA compares admissible candidate networks against observations and simpler baselines.

Version **1.0.5** is a **not-peer-reviewed perspective and mathematical framework with reduced synthetic demonstrations**. It is not an empirical planetary validation, a mission-data retrieval, a claim of general hybrid-system well-posedness, or evidence of scientific priority. The benchmark is transparent and deliberately favorable; all generation constants are public. This corrective release supersedes v1.0.1 for current use without modifying its immutable tag or assets. The public v1.0.2, v1.0.3, and v1.0.4 tags are retained as release-process evidence, were not moved, and have no GitHub Releases.

## Read the work

- [Accessible preprint (self-contained HTML)](manuscript/SPPT_ASTRA_preprint_v1.0.5.html)
- [Preprint PDF](manuscript/SPPT_ASTRA_preprint_v1.0.5.pdf)
- [Accessible technical supplement (self-contained HTML)](manuscript/SPPT_ASTRA_technical_supplement_v1.0.5.html)
- [Technical supplement PDF](manuscript/SPPT_ASTRA_technical_supplement_v1.0.5.pdf)
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

## Typed-layer outlook and provenance boundary

The preprint includes a proposed-only ASTRA outlook prompted by four 2026 studies. A mixed iron-oxyhydroxide inclusion in one Juína diamond has no observed present fracture or exterior connection and is admitted as a qualified example of present isolation; permeability, past exchange, and its inferred deep history remain unmeasured or source-author hypotheses. Moonlight/animal spectroscopy, error-detected quantum sampling, and xenophagocytosis are admitted only as observation, certificate, and active-control analogies. None validates SPPT, changes its physical flux graph, or establishes a universal cross-domain law. No article text, third-party figure, collage, or chat transcript is redistributed.

The acknowledgments record the author-reported dream/collage/ChatGPT origin of the cold-trap/Saturn idea and later OpenAI language-model assistance. The unprovided collage is excluded because its component-image identities and publication rights were not established. This is conceptual provenance, not evidence. Every admitted evidentiary statement is bound to a primary source, calculation, data set, or test in `CLAIM_MATRIX.json`; proposed and deferred statements are labeled separately.

## Synthetic benchmark boundary

Across 64 frozen Gaussian-noise realizations, training BIC selects the minimum generating chain in 64/64 runs. The held-out forcing comparison occurs after selection and preserves a negative result: the overconnected triangle has lower held-out RMSE in 23/64 runs. Its added edge reaches the declared lower bound in 29/64 runs, so the shortcut distribution is censored. These are mechanically replayed synthetic outcomes, not proof, external validation, or a general false-positive-rate estimate.

An exact algebraic negative control sharpens that boundary. With the same capacities and only surface forcing and observation, the surface star $(k_{02},k_{12})=(5,6)$ and deep star $(k_{01},k_{02})=(30/11,11)$ have identical surface transfer functions for every forcing from equilibrium, despite different hidden states and labeled supports. The released chain point lies outside the ambiguous nonnegative branch, so 64/64 remains a pointwise selection result; it is not family-wide topology identification. Another spatial input or output, an intervention, or independently justified structural constraints may separate such equivalence classes, but identifiability must be recomputed for the augmented design.

The release-frozen 20-start design was adopted during release audit after replay of this same benchmark exposed a missed endpoint under the earlier 12-start design. The added unit and coordinate-wise decade anchors were therefore informed by benchmark behavior. These reruns are regression evidence for the repaired implementation, not untouched, blinded, or external evaluation. Both data serializations preserve every start vector, solver disposition, endpoint, convergence diagnostic, active bound, and failed outcome; CSV and JSON remain duplicate representations of one evidence source.

## Reproduce

Requirements:

- CPython **3.12.10** (`.python-version` and `RUNTIME.json`; do not accept another 3.12 microrelease)
- Git for Windows **2.55.0.windows.3**, using the exact installer, build commit, and executable identity in `RUNTIME.json`
- dependencies from `requirements-lock.txt`, installed with hashes
- a Haswell-compatible Windows x86-64 CPU with AVX2 and FMA3; the canonical verifier forces and probes the NumPy and SciPy OpenBLAS Haswell kernels with one thread and disables NumPy AVX-512 dispatch
- Playwright Chromium **151.0.7922.34**, revision **1234**, installed by Playwright 1.62.0 for tagged PDF generation
- the exact Matplotlib-distributed DejaVu and STIX source-font bytes recorded in `RUNTIME.json`; the document build does not use machine-installed fonts

On Windows PowerShell:

```powershell
py -3.12 -c "import platform; assert platform.python_version() == '3.12.10', platform.python_version()"
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-lock.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -I -B tools\verify.py --all
```

On another Windows shell, first verify that the selected interpreter is exactly CPython 3.12.10 and that the selected Git matches `RUNTIME.json`, then run the same Python module commands. The canonical controller commands require Python's `-I -B` flags before the script path so inherited import paths cannot run before verification begins. The canonical runtime and distribution archives are identified by hash in `RUNTIME.json`. `tools/verify.py --all` overrides hostile inherited thread or OpenBLAS-core values, verifies Git and the actual NumPy and SciPy kernels, and performs complete test discovery, lint and type checks, metadata/schema checks, privacy and path scans, scientific replay, figure regeneration, document rebuild, deterministic-output comparison, PDF inspection, manifest checks, and release-integrity negative tests.

Focused commands:

```text
python -P -s -B -m pytest -q
python -I -B scripts/make_figures.py
python -I -B tools/build_documents.py
python -I -B tools/verify.py
```

Builds write only beneath the repository or a disposable output root. Seeds, the 20 distinct fixed generic multistart points, every start and endpoint, optimizer convergence diagnostics, bound flags, and all negative outcomes are preserved in `data/`. The byte-identity claim is limited to the exercised release-artifact paths under the complete frozen runtime; it is not a claim of universal floating-point identity for future numerical code.

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
| `SOURCE_INVENTORY.json` | Hash, media, attribution, rights, alias, and excluded/deferred status for every supplied source artifact |
| `CLAIM_MATRIX.json` | Consequential claims, hypotheses, evidence classes, limitations, and dispositions |

## Citation

Canonical citation metadata are in [`CITATION.cff`](CITATION.cff). Cite the versioned GitHub release:

> Jacko T. (2026). *Phase-Reservoir Topology as a Hidden State Variable in Planetary Evolution*, version 1.0.5. GitHub. https://github.com/jkolantree/astra/releases/tag/v1.0.5

This is a GitHub-only release path. No DOI or Zenodo ingestion is claimed; adding either would be a separate, explicitly authorized publication step and a new version if any archived file changed.

## Licensing and correspondence

Original software is MIT licensed. Original manuscript text, documentation, figures, generated data, and results are CC BY 4.0. See [`LICENSE_MAP.md`](LICENSE_MAP.md) and [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md). Cited works remain under their own terms.

Use [GitHub Issues](https://github.com/jkolantree/astra/issues) for public correspondence. No private email, location, institution, ORCID, or legal identity is published.

The tracked `.mailmap` maps the already-public GitHub-handle author label used by early bootstrap commits to the release pseudonym Jacko T.; raw historical commit objects are not rewritten.
