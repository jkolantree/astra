---
title: "SPPT/ASTRA Integrated Core 1.1.0-alpha.1: Typed Composition and Bounded Research Checks"
author: "Jacko T."
lang: en-US
---

# Draft status and abstract

**Versioned alpha review candidate 1.1.0-alpha.1. Not peer reviewed. No empirical or runtime admission.**

ASTRA's proposed integrated core joins existing SPPT/reservoir calculations to typed capture, boundary-response, memory, observation and archive interfaces. The contribution presented here is a bounded software and mathematical assembly: explicit quantity contracts, one synthetic end-to-end fixture, a scoped claim register, selected counterexamples, and reproducible verification requirements. It is not a new empirical planetary or quantum theory. A successful interface test says that a specified calculation obeyed its declared contract; it does not establish that the declaration describes an experiment.

The assembly distinguishes physical tracer mass, dimensionless context, expected counts and expected retained record-equivalents. Unknown response remains unavailable. A first moment does not supply a count distribution or a no-record likelihood. SCM and potential-WKI calculations are separate mathematical research sections; they do not create a common microscopic law. The 93 scoped statements retain their individual evidence classes and do not inherit validation from the existence of an integration test. Literature examples motivate proposed tests but do not validate ASTRA.

# Motivation and scope

Transport, measurement and record retention can erase different information. Treating their outputs as the same physical quantity can hide the source of an inference failure. The proposed core makes these boundaries explicit and exposes a synthetic calculation that can be checked without interpreting every source-family claim as a theorem. Its source-family labels—Layers, Gamma, Xi, October, SCM and WKI—identify lineage and bounded reference implementations. They are not universal API or scientific guarantees.

The historical v1.0.7 manuscript, supplement, citation, schemas and release contract remain separate and unchanged. The already ancestral v1.0.8 candidate remains unpromoted. This integrated-core successor selects candidate identity astra-integrated-core-v1.1.0-alpha.1. It remains unpublished and supplies no promotion of an existing edition.

# Typed composition

A quantity is identified by its space, kind, unit, ordered basis and finite immutable values. Composition requires equality of every declared type coordinate. A stage also declares its mechanism, model identity, source-local claim keys and, for a certificate, its failure scope. Physical transport cannot silently turn kilograms into counts or energy. Observation and archive mappings must explicitly say how their outputs are obtained.

![Synthetic information flow. Tracer transport and capture precede a dimensionless context calculation; a detector maps captured mass to expected counts, and a separate archive records expected retained record-equivalents. Arrows identify interfaces, not empirically established laws.](../../resources/integrated-core/v1.1.0-alpha.1/generated/01_typed_pipeline.svg)

| Stage | Quantity and operation | Boundary |
|---|---|---|
| Transport and capture | Two tracer reservoirs; conservative exchange; capture moves part into a separate sample | Physical mass accounting |
| Boundary and Xi channel | Captured mass divided by reference mass drives a linear boundary model and discrete memory | Synthetic dimensionless context |
| Detector | Captured mass, declared efficiency and response determine a first moment | Expected count, no likelihood |
| Archive | Interval expected counts produce record-equivalents; a reset removes a fraction | Record balance, not mass |

Table: Declared stages in the synthetic case.

Calibration is a declaration with explicit fields. A hash string is not authenticated artifact evidence, and distinct training, calibration and holdout labels are not evidence of independent sampling. Structural proposal checks retain false calibration-readiness and empirical-admission flags. This separation is essential to avoid interpreting metadata completeness as a scientific result.

# Synthetic integration

The fixture initializes two equal-capacity reservoirs with tracer masses 3 and 1 kg and conductance 0.2 per second. Preparation uses five times from 0 to 2 seconds, spaced by 0.5 seconds. Existing reservoir propagation and SPPT tendency/inventory functions check the physical accounting independently. The available second-reservoir sample has volume 1 cubic metre; a quarter-volume capture moves a quarter of its prepared tracer mass into a separate compartment under an explicit Gamma reset ledger. A new exposure clock starts after preparation ends.

Let captured mass be $m_c$, reference mass $m_0$, and declared base detector efficiency $\eta_0$. The normalized boundary drive is $m_c/m_0$. Xi's persistence is per declared exposure interval, not a continuous decay constant. For synthetic nonnegative context $c_j$, this fixture defines

$$\eta_j=\frac{\eta_0}{1+c_j},\qquad E_j=m_c R\eta_j.$$

Here $R$ is a declared response in count/kg and $E_j$ is an interval expected count. This response factor is a design choice, not a fitted constitutive law. Repeated exposures non-destructively reuse the same sample under that toy law. No random count realization is generated.

Each interval contributes its expected count to a no-leak stock of expected record-equivalents. After the second interval a reset retains a quarter of the stock. The balance is

$$\sum_j E_j=S_{\mathrm{retained}}+S_{\mathrm{erased}}.$$

The implementation checks this separately from the conserved physical mass. Unknown efficiency produces unavailable counts and archive stock; a zero count expectation is valid; normalized composition has no value when its denominator is zero. Requests for a likelihood or exclusion that the interface does not provide fail explicitly.

# Reduction, memory and identifiability

A reduced process can be Markov while failing to preserve a declared output: a constant reduced state remains Markov even when an unobserved constant controls the output. Output sufficiency is therefore not a generic necessary condition for reduced-state Markov behavior. The finite diagnostic checks strong lumpability of one supplied transition matrix and output constancy separately. It does not establish a nonlinear reduction theorem.

Jacobian rank describes first-order numerical sensitivity. The map $\theta\mapsto\theta^3$ is injective at zero despite a zero derivative; a constant map is not injective. Neither a rank calculation nor a positive synthetic fit resolves nonlinear/local or global identifiability. Competing state-space, lag/kernel, adaptation, drift and physical transport models require explicit comparison under matched information and resource budgets.

# SCM: finite controls and a conditional mathematical limit

The SCM section retains nine finite replay families and selected counterexamples, rather than declaring all 32 source claims validated. Norm preservation is distinct from common unitarity. Ordinary-boost failure, spectator dependence, ensemble dependence and scalar mirror blindness remain limitations of the naive proposal. A density, instrument and operational no-signalling completion remains unadmitted. A single plane wave's global phase is not an operational quantum observable.

For $C^2$ real fields $u,v$ on a connected open Euclidean planar domain, the balanced-gradient conditions $|\nabla u|=|\nabla v|$ and $\nabla u\cdot\nabla v=0$ imply harmonicity. The supplement records the argument across the critical set. Smooth periodic scalar fields on a flat two-torus are then constant; whole-plane $L^2$ fields vanish. A normalized balanced field can exist on a bounded disk under different boundary conditions. These statements do not extend to arbitrary boundaries, dimension three and above, nonsmooth fields or persistence under time evolution.

# Potential-WKI benchmark and prior-art correction

For constant $a>0$ and $\beta>0$, the supplied wave equation is

$$i\psi_t=-\beta\partial_x\left(\frac{\psi_x}{\sqrt{1+a^2|\psi_x|^2}}\right).$$

The substitution $w=a\psi_x$ gives the complex WKI form after differentiation. The reviewed correction demotes CVG-03/04 to a potential-WKI/filament benchmark. We retain its source-reported prior-art classification; this draft is not a fresh exhaustive priority review. Differentiation loses a spatial mean or integration datum, boundary recovery is separate, and $a=0$ is a separate linear limit. The local graph-gauge calculation assumes smooth solutions that stay in the chart.

Six finite identity groups do not establish a PDE spectrum or nonlinear integration. The value $1/8$ follows the explicitly normalized substitution $\beta=a=A=k=1$ into a continuous-mode maximum formula; discrete-domain attainability and marginal sectors remain open. The transformed-background R6 comparison in the correction note remains unresolved. CVG-06/07 receive no executable support from those six groups, and CVG-08–12 were not reaudited. Signed material-coefficient work is energy accounting, not a new energy source or device validation.

# Literature as proposed tests

All 15 DOI identities have undergone bounded independent public-source checking. Access ranges from abstracts to publisher PDFs; supplements and artifact bytes remain incompletely verified. The supplement records each source/version and remaining gap. No article or dataset bytes are bundled.

The evaporation example retains both the 2024 positive interpretation and the 2026 planar-water null under their different conditions. Finite-channel wavefront statistics do not establish a general detector-response theorem. Slow-fast basin examples caution against assuming a valid reduction; they do not test this core. Earth-rotation papers motivate an overlap and convention audit rather than certifying a combined budget. Anatomy, sensory physiology and model-predicted forcing response remain separate evidence types. Dissent persuasiveness is not independently verified correction quality. The three BC008 papers are source/version-tracing test cases, not validation of a provenance system.

# Evidence and validation boundary

The distinct new-edition experiment has an exact 61-output contract: 31 retained scientific/Atlas outputs, thirteen newly named PNG/SVG pairs, one local gallery and three bounded JSON reports. Preparation 019 completed two genuinely fresh runs with identical hashes for every output; all 486 copied inputs retained their hashes and all 31 retained outputs matched frozen Linux hashes. The 26 historical schematics were absent from both run trees. New diagrams are explicitly non-equivalent to those historical figures.

| Evidence class | Completed bounded evidence | What remains unestablished |
|---|---|---|
| Synthetic integration and claims | 33 methods and 56 reported subtests per mode passed in 019 | Empirical calibration, general API theorem or whole-source validation |
| New freshness/report controls | 28 methods per mode passed in 019 | Historical 57-output gate or arbitrary input validity |
| WKI/report controls | 19 methods and 13 reported subtests per mode passed in 019 | PDE spectrum, boundary recovery, global dynamics or novelty |
| Historical preparation 019 suite | 689 pass / 23 fail on Python 3.12.10; 674 pass / 38 fail on 3.12.14, in both modes | Full-suite PASS or source/runtime/Pages admission |
| Literature | Fifteen bounded identity/access reviews with explicit source-specific gaps | Raw-data reproduction, generic cross-domain support or ASTRA performance |

Table: Engineering evidence is separated from scientific and release admission.

The proposed split route uses Python 3.12.10 for retained science, Atlas, SCM, synthetic integration and rendering, and Python 3.12.14 for WKI. Actual WKI reports from the latter passed the unchanged six-group validator. These are separate interpreters communicating through source-bound JSON reports; there is no implied unified runtime. The successor portable bootstrap is an offline proposal using already acquired inputs, with its own construction and relocation receipts. A locally packed 3.12.10 installation is not relabeled as the unavailable original provider archive.

The four reading assets (manuscript and supplement, each HTML and PDF) are a separate output family. They are rebuilt from these successor sources and declared diagram bytes; they are not silently counted among the 61 experimental outputs. Their two identity/inspection receipts and two full font notices are auxiliary files. The accompanying build records determine success; this prose does not predeclare a future build PASS.

Historical copied-output Linux PASS records retain their original scope; 018 diagnosed 31 fresh outputs and 26 missing schematics. The historical Windows scientific comparison still FAILS, including the retained benchmark value 1.3938628 versus 1.3938627 under unchanged tolerances. This is not a new Windows OS execution. The 019 distinct contract does not satisfy the old 57-output requirement. The companion's math controls passed, while 18 rendered media failed byte matching across Matplotlib 3.10.8 and 3.11.1; all original bytes remain unchanged. Recurrence remains prose/proposed tests without ODE or data replay. Six specialist companion browser checks remain not tested despite prior owner appearance approval. No empirical SCM/QG validation or novelty priority is claimed.

# Next falsifiable work

The useful next step is a specified observation law, independent calibration and a frozen target-domain experiment. Comparative work must disclose strong conventional alternatives, search effort, information, sensors, compute, holdout exposure, practical effect margins, uncertainty, multiplicity and failures. A favorable generator or deliberately weak negative control does not establish superiority. Any fresh confirmatory study must account for earlier benchmark exposure; fresh seeds alone do not turn development evidence into a holdout.

Runtime/source/document admission and release publication are separate decisions. A namespaced prerelease requires reviewed gates, new document evidence and exact public assets; a version spelling or tag namespace cannot bypass the historical contract.

# Attribution and reading guide

The companion technical supplement gives exact source roles, the synthetic fixture, scoped claims, literature access and reproduction limits. Original source-family notices remain in the repository. The historical reading editions are preserved as historical editions.

Copyright 2026 Jacko T., to the extent of rights controlled by the author. Original draft prose and the inherited flow diagram retain their CC BY 4.0 mapping. Newly authored edition diagrams retain the package's private-review boundary with no new blanket reuse grant; embedding does not relicense them. Substantial ChatGPT/Codex assistance is disclosed; no exclusive ownership of AI output is asserted. Cited works and factual metadata retain their own terms. No third-party article, data or figure bytes are included. Embedded DejaVu/Bitstream Vera/Arev and STIX fonts retain their supplied notices; the full notices accompany the reading editions. Code remains MIT. This is an unpublished, versioned alpha review candidate, not external peer review, runtime admission or release authority.
