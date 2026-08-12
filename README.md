# Phase-Reservoir Topology as a Hidden State Variable in Planetary Evolution

<p align="center">
  <a href="docs/sppt-astra-cover.svg"><img src="docs/sppt-astra-cover.svg" width="960" alt="Conceptual SPPT/ASTRA network with observed boundary signals, a latent state, candidate paths, and an observe-infer-test sequence"></a>
</p>

*Reading order: observe boundary signals, infer candidate graphs, then reject what fails declared gates. [Open the full-size vector](docs/sppt-astra-cover.svg). This is not an observational image, scale model, or data visualization.*

This repository contains the reference package for **Solar-Planetary Phase-Partition Theory (SPPT)** and its inference layer, **ASTRA — Astronomical State-Topology and Reservoir Analysis**. SPPT represents planetary material and energy reservoirs as a physically constrained network whose topology may itself be a latent state; ASTRA compares admissible candidate networks against observations and simpler baselines.

> **Status.** The core work is a **not-peer-reviewed perspective and mathematical framework with reduced synthetic demonstrations**. It is not an empirical planetary validation, a mission-data retrieval, a general hybrid-system theorem, or evidence of scientific priority. The benchmark is transparent and deliberately favorable; its generation constants are public.
>
> **Citation boundary.** [SPPT/ASTRA v1.0.7](https://github.com/jkolantree/astra/releases/tag/v1.0.7) is the current stable core citation and reproduction target. The immutable [v1.0.6 release](https://github.com/jkolantree/astra/releases/tag/v1.0.6) remains the historical core baseline. Supplemental releases and namespaced research drafts retain their own identities and do not inherit the v1.0.7 claim matrix unless the release record says so.
>
> **Default-branch maintenance boundary.** The repository source includes an **unpromoted core-integrity M1 source-repair draft** that differs from the immutable v1.0.7 reading assets. It is not v1.0.8, a release candidate, or a published erratum. Cite and reproduce v1.0.7 from its tagged release and versioned Pages route unless a later release explicitly promotes the repaired source.

## In plain English: what this is and why it matters

Two planets can have similar ingredients and heat budgets yet evolve differently if those materials are connected differently. Imagine two buildings with the same rooms and pipes: if a valve is closed or a hallway is missing, heat and water take different routes. SPPT models a planet this way - as reservoirs and phases linked by physical processes whose connections may appear, disappear, or become bottlenecks. ASTRA is the inference and checking layer that asks which of those network arrangements is consistent with observations.

This matters because many planetary measurements are made at the boundary: temperature, light, gravity, magnetic fields, and atmospheric composition. Different interiors can produce the same surface snapshot. The framework therefore emphasizes transients, multiple independent channels, interventions, conservation checks, and comparisons with simpler fixed-topology models. The repository contains mathematical results and synthetic demonstrations of these ideas; it does not yet explain a real planet, identify dark matter, or provide mission validation. A topology-aware model earns its place only if it improves calibrated held-out predictions and survives counterexamples.

## Publication map

- **v1.0.7 — current stable reference edition (SPPT/ASTRA).** [Read the current core edition](https://jkolantree.github.io/astra/latest/) or open the immutable [release](https://github.com/jkolantree/astra/releases/tag/v1.0.7).
- **v1.0.6 — historical immutable core baseline.** [Read its versioned edition](https://jkolantree.github.io/astra/v1.0.6/preprint/) or open the [release](https://github.com/jkolantree/astra/releases/tag/v1.0.6).
- **v0.3.0 — current supplemental edition (*Earth Is the Instrument*), a working-paper release.** [Read the supplemental edition](https://jkolantree.github.io/astra/resources/earth-is-the-instrument/latest/) or open its immutable [release](https://github.com/jkolantree/astra/releases/tag/earth-instrument-framework-v0.3.0).
- **v1.0.7 Candidate Revision 2 — superseded public integration package.** [View the immutable prerelease](https://github.com/jkolantree/astra/releases/tag/sppt-astra-v1.0.7-rc.2) and its self-contained review archive. It records the review snapshot that preceded the stable v1.0.7 integration; its bytes and identity remain unchanged, and it has no separate Pages route, DOI, or Zenodo record.
- **Public namespaced alpha — Sector-Complete Instrument v0.1.0-alpha.1.** This synthetic methods module lives under [`resources/sector-complete-instrument/v0.1.0-alpha.1/`](resources/sector-complete-instrument/v0.1.0-alpha.1/); it is not ASTRA v0.3.2, does not amend either immutable line, and has no Pages route, DOI, or Zenodo record. Open the [GitHub prerelease](https://github.com/jkolantree/astra/releases/tag/sector-complete-instrument-v0.1.0-alpha.1).
- **Unpromoted methods draft — Mode-resolved active-support audit.** The default-branch [draft](resources/active-support-audit/draft-v0.1.0/) is a long-form ASTRA methods perspective on mode, waveform, geometry, phase matching, and observation. It remains separate from the v1.0.7 claim matrix and immutable assets.
- **v0.1 — historical edition (*Earth Is the Instrument* Working Paper).** [Read historical v0.1](https://jkolantree.github.io/astra/resources/earth-is-the-instrument/v0.1/) or open its immutable [release](https://github.com/jkolantree/astra/releases/tag/earth-instrument-wp-0.1).

- **Unpromoted successor prototypes.** The [SPPT Bridge Protocol](resources/sppt-bridge-protocol/draft-v0.1.0/) and [coherence-cell exploration](resources/coherence-cell-exploration/draft-v0.1.0/) are separate methods prototypes. They are not core equations, release assets, or validation claims.
- **Unpromoted cosmic visibility framework.** The [Cosmic Visibility and Sampling Framework](resources/cosmic-visibility-framework/draft-v0.1.0/) is a 28-page operator-aware research draft for separating source strength from transduction, propagation, archive, recovery, and detector visibility. It is a methods proposal only: no dark-matter or graviton detection, fourth Martian reservoir, shared physical mechanism, or replacement cosmology is claimed.

### Status vocabulary

- **Core stable:** SPPT/ASTRA v1.0.7 is the current citation, reproduction target, GitHub Latest release, and current core release identity. v1.0.6 is the immutable historical baseline.
- **Supplemental working-paper release:** *Earth Is the Instrument* v0.3.0 is a complete, separately versioned working-paper snapshot; it is supplemental and does not inherit the core claim matrix or verification.
- **Research preview:** Sector-Complete Instrument v0.1.0-alpha.1 is an explicitly alpha, synthetic methods module.
- **Integration candidate:** v1.0.7 Candidate Revision 2 is a superseded package-only review snapshot; the admitted stable core version is v1.0.7.

GitHub's **Pre-release** badge remains on the supplemental, preview, and candidate lines because they are not the core/latest line. It is a distribution/status flag, not a claim that every artifact is unfinished or that peer review has occurred.

The bare `/latest/` route and repository-level `CITATION.cff` refer only to the SPPT/ASTRA reference line. Published reading editions have their own versioned tags, citations, checksums, and `/resources/` routes; public namespaced releases without a reading route and repository-visible unpromoted drafts remain source-tree or release artifacts unless a route is stated explicitly. The project was developed with substantive ChatGPT assistance; the human-responsibility and independence disclosure appears below.

## Core reference package

- [Read the accessible v1.0.7 preprint on GitHub Pages](https://jkolantree.github.io/astra/v1.0.7/preprint/)
- [Read the accessible v1.0.7 technical supplement on GitHub Pages](https://jkolantree.github.io/astra/v1.0.7/supplement/)
- [Downloadable v1.0.7 preprint HTML](manuscript/SPPT_ASTRA_preprint_v1.0.7.html) — download the file, then open it in a web browser; GitHub's file viewer does not render this large self-contained edition
- [v1.0.7 preprint PDF](manuscript/SPPT_ASTRA_preprint_v1.0.7.pdf)
- [Downloadable v1.0.7 technical-supplement HTML](manuscript/SPPT_ASTRA_technical_supplement_v1.0.7.html) — download the file, then open it in a web browser
- [v1.0.7 technical supplement PDF](manuscript/SPPT_ASTRA_technical_supplement_v1.0.7.pdf)
- [Unpromoted core-integrity M1 preprint-source draft](manuscript/manuscript.md) — differs from immutable v1.0.7 reading assets and has no release identity
- [Authoritative supplement source](manuscript/supplement.md)
- [Claim-admission matrix](CLAIM_MATRIX.json)
- [Immutable v1.0.7 structured claim-to-source coverage](evidence/claim_source_coverage_v1.0.7.json)
- [Unpromoted core-integrity M1 maintenance overlay](evidence/claim_source_coverage_v1.0.7_maintenance_overlay_m1.json)

The versioned Pages editions are the primary accessible reading path for the reference package and published supplemental line. The downloadable HTML files are self-contained; the PDFs are synchronized tagged visual editions. Native MathML is available in HTML, while the PDFs do not claim a native MathML expression tree. Repository-visible unpromoted drafts remain source-tree artifacts rather than Pages editions. The frozen v1.0.7 coverage record and unpromoted M1 overlay have distinct schema and identity boundaries; neither overlay status nor default-branch source changes create a release or prove sentence-level completeness.

## Supplemental line: *Earth Is the Instrument*

<a href="https://jkolantree.github.io/astra/resources/earth-is-the-instrument/v0.3.0/"><img src="resources/earth-is-the-instrument/v0.3.0/cover.png" width="280" alt="Blue-and-gold cover titled Earth Is the Instrument, with an abstract planetary diagram"></a>

**Foundational working paper · evidence graded · not peer reviewed · separate from stable v1.0.7.**

- [Read the text-first guide to *ASTRA Framework v0.3.0 — Earth Is the Instrument*](https://jkolantree.github.io/astra/resources/earth-is-the-instrument/v0.3.0/), a separately versioned framework about dual-rent seams, local-to-global certificates, geological memory, evidence independence, and bounded arithmetic-seam tests.
- Start with the reflowable [public ground reading](https://jkolantree.github.io/astra/resources/earth-is-the-instrument/v0.3.0/ground-reading/) or use the [browser audit worksheet](https://jkolantree.github.io/astra/resources/earth-is-the-instrument/v0.3.0/audit-form/); both work at narrow screen widths.
- Fixed-layout download and print alternatives: [complete framework PDF (171 pages)](resources/earth-is-the-instrument/v0.3.0/ASTRA_Framework_v0.3.0_Earth_Is_The_Instrument.pdf), [two-page ground-reading PDF](resources/earth-is-the-instrument/v0.3.0/ASTRA_v0.3.0_Public_Ground_Reading.pdf), and [one-page audit-form PDF](resources/earth-is-the-instrument/v0.3.0/ASTRA_Dual_Rent_Local_to_Global_Audit_Form_v0.3.0.pdf).
- [Review the publication audit and known accessibility limits](resources/earth-is-the-instrument/v0.3.0/PUBLICATION_AUDIT.md).
- [Download the complete source and reproducibility archive from its versioned GitHub Release](https://github.com/jkolantree/astra/releases/tag/earth-instrument-framework-v0.3.0).

Within its own publication line, v0.3.0 supersedes the internal v0.2.1 predecessor preserved in its release archive. No public v0.2.1 tag or GitHub Release was created. It does not amend or supersede the stable SPPT/ASTRA v1.0.7 reference release or inherit its verification status; v1.0.6 remains the immutable historical baseline. The earlier [Working Paper 0.1](resources/earth-is-the-instrument/v0.1/) remains available, and the [v0.3.0 post-publication errata](resources/earth-is-the-instrument/v0.3.0/ERRATA.md) records documentation corrections that do not change immutable artifacts.

## Name, assistance, and independence

ASTRA is the project's own acronym for **Astronomical State-Topology and Reservoir Analysis**. The framework was developed by Jacko T. with substantive ChatGPT assistance in literature organization, adversarial review, equation checking, code drafting, visual design, editing, accessibility, and release engineering. Jacko T. selected the questions and final wording, reviewed the released work, and remains responsible for its sources, claims, interpretations, errors, omissions, code, and publication decisions. Model output is not a citation, experiment, proof, independent verification, peer review, or scientific evidence; the evidentiary basis is the cited literature, declared calculations, data, tests, and bounded certificates.

The name echoes [*Ad Astra Per Aspera* — "To the Stars Through Difficulties"](https://www.kansas.gov/kbi/about/kbiseal.shtml) as a general motto; this is a naming reference, not a claim of affiliation, endorsement, priority, or exclusive rights. ASTRA is an independent research project, and use of ChatGPT does not imply OpenAI endorsement.

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

The provenance record distinguishes author-reported inspirations and model assistance from evidence. The unprovided collage is excluded because its component identities and publication rights were not established. Each consequential claim listed in `CLAIM_MATRIX.json` is bound to a primary source, calculation, data set, or test; proposed and deferred statements are labeled separately. The matrix is a claim register, not a sentence-level completeness proof.

## Synthetic benchmark boundary

Across 64 frozen Gaussian-noise realizations, training BIC selects the minimum generating chain in 64/64 runs. The held-out forcing comparison occurs after selection and preserves a negative result: the overconnected triangle has lower held-out RMSE in 23/64 runs. Its added edge reaches the declared lower bound in 29/64 runs, so the shortcut distribution is censored. These are mechanically replayed synthetic outcomes, not proof, external validation, or a general false-positive-rate estimate.

An exact algebraic negative control sharpens that boundary. With the same capacities and only surface forcing and observation, the surface star $(k_{02},k_{12})=(5,6)$ and deep star $(k_{01},k_{02})=(30/11,11)$ have identical surface transfer functions for every forcing from equilibrium, despite different hidden states and labeled supports. The released chain point lies outside the ambiguous nonnegative branch, so 64/64 remains a pointwise selection result; it is not family-wide topology identification. Another spatial input or output, an intervention, or independently justified structural constraints may separate such equivalence classes, but identifiability must be recomputed for the augmented design.

The release-frozen 20-start design was informed by an earlier replay and is therefore regression evidence for the repaired implementation, not untouched, blinded, or external evaluation. Both data serializations preserve every start vector, solver disposition, endpoint, convergence diagnostic, active bound, and failed outcome; CSV and JSON remain duplicate representations of one evidence source.

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
.\.venv\Scripts\python.exe -I -B tools\verify.py --all --workers 4
```

On another Windows shell, first verify that the selected interpreter is exactly CPython 3.12.10 and that the selected Git matches `RUNTIME.json`, then run the same Python module commands. The canonical controller commands require Python's `-I -B` flags before the script path so inherited import paths cannot run before verification begins. The canonical runtime and distribution archives are identified by hash in `RUNTIME.json`. `tools/verify.py --all --workers 4` overrides hostile inherited thread or OpenBLAS-core values, verifies Git and the actual NumPy and SciPy kernels, and performs complete test discovery, lint and type checks, metadata/schema checks, privacy and path scans, scientific replay, figure regeneration, PDF inspection, manifest checks, and release-integrity negative tests. States without the exact unpromoted core-integrity M1 overlay rebuild the current-source documents twice and compare deterministic output. The exact overlay instead requires the repaired source to differ from v1.0.7 and proves that all six immutable v1.0.7 document outputs still match the fixed annotated release tag; it does not overwrite those frozen filenames with successor bytes. Any overlay, schema, source, tagged contract, tag identity, source or document index mode, or frozen-document mismatch fails closed, and current-source document replay remains deferred until the repaired source receives a successor release identity.

Focused commands:

```text
python -P -s -B -m pytest -q
python -I -B scripts/make_figures.py
python -I -B tools/build_documents.py
python -I -B tools/verify.py
```

Builds write only beneath the repository or a disposable output root. Seeds, the 20 distinct fixed generic multistart points, every start and endpoint, optimizer convergence diagnostics, bound flags, and all negative outcomes are preserved in `data/`. The byte-identity claim is limited to the exercised release-artifact paths under the complete frozen runtime; it is not a claim of universal floating-point identity for future numerical code.

## Verification routes and tag namespaces

The repository verification workflow runs for pull requests, `main`, and core reference tags matching `v*`. Its tag-event identity checks are intentionally bound to the core `RELEASE_SPEC.json`; they do not apply to namespaced supplemental tags. *Earth Is the Instrument* v0.3.0 instead retains its own 90-check package gate, checksum and archive records, successful exact-main repository verification, and release-bound Pages deployment. A future supplemental release that requires natural tag-event CI should use a dedicated supplemental controller rather than broadening the core tag pattern.

## Repository map

| Path | Contents |
|---|---|
| `manuscript/` | Authoritative Markdown, bibliography, accessible HTML, synchronized PDF |
| `docs/` | GitHub Pages landing files, including the public vector cover; the deployment workflow assembles immutable versioned reference editions and separately verified published supplemental-resource pages. Unpromoted drafts remain source-tree artifacts unless given an explicit route |
| `schemas/` | Published Draft 7 schemas for schema-declaring release metadata and audit records |
| `src/` | Auditable reduced SPPT and ASTRA calculations |
| `scripts/` | Deterministic scientific reproductions and figure generation |
| `tests/` | Unit, invariant, numerical, evidence-boundary, and release-integrity tests |
| `data/` | Generated CSV and JSON outputs, including all negative outcomes |
| `figures/` | Generated manuscript and supplement figures |
| `tools/` | Canonical verification, document, manifest, and release-identity tooling |
| `resources/` | Independently versioned exploratory and foundational working papers, complete packages, and text-first reading guides |
| `RELEASE_NOTES_earth-instrument-*.md` | Archived bodies of the immutable supplemental GitHub releases, with links to any post-publication errata |
| `SOURCE_INVENTORY.json` | Hash, media, attribution, rights, alias, and excluded/deferred status for every source artifact admitted to the v1.0.7 reference release |
| `CLAIM_MATRIX.json` | Consequential claims, hypotheses, evidence classes, limitations, and dispositions |

## Citation

The repository-level [`CITATION.cff`](CITATION.cff) describes only the current SPPT/ASTRA **reference** release. Cite that versioned GitHub release as:

> Jacko T. (2026). *SPPT / ASTRA v1.0.7: Stateful Edges and Operator-Aware Inference*. GitHub. https://github.com/jkolantree/astra/releases/tag/v1.0.7

For *Earth Is the Instrument*, use the citation printed on its [current supplemental edition](resources/earth-is-the-instrument/v0.3.0/#citation) or historical v0.1 page rather than GitHub's repository-level citation suggestion.

This is a GitHub-only release path. No DOI or Zenodo ingestion is claimed; adding either would be a separate, explicitly authorized publication step and a new version if any archived file changed.

## Licensing and correspondence

Original software is MIT licensed. Original manuscript text, documentation, figures, generated data, and results are CC BY 4.0. Separately supplied resources do not inherit those terms; their authorization, provenance, and reuse status are stated individually. See [`LICENSE_MAP.md`](LICENSE_MAP.md) and [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md). Cited works remain under their own terms.

Use [GitHub Issues](https://github.com/jkolantree/astra/issues) for public correspondence. No private email, location, institution, ORCID, or legal identity is published.

Historical commit objects are preserved; the immutable release history is not rewritten.
