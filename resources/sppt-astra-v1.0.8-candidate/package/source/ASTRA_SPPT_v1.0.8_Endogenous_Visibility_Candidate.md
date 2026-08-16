---
title: "SPPT / ASTRA v1.0.8 Candidate: Endogenous Visibility"
subtitle: "Source-Coupled Transducers, Self-Detuning Media, Cross-Channel Rescue, Catastrophic Archives, and Global Certificates"
author: "Jacko T."
date: "16 August 2026"
lang: en-US
bibliography: references.bib
link-citations: true
reference-section-title: References
toc: true
toc-depth: 3
number-sections: false
geometry: margin=0.78in
fontsize: 11pt
colorlinks: true
linkcolor: blue
citecolor: blue
urlcolor: blue
mainfont: "DejaVu Serif"
sansfont: "DejaVu Sans"
monofont: "DejaVu Sans Mono"
header-includes:
  - |
    \usepackage{microtype}
    \usepackage{setspace}
    \setstretch{1.18}
    \usepackage{booktabs}
    \usepackage{longtable}
    \usepackage{array}
    \usepackage{amsmath,amssymb,mathtools,bm}
    \usepackage{float}
    \usepackage{caption}
    \usepackage{xcolor}
    \usepackage{fancyhdr}
    \usepackage{enumitem}
    \definecolor{ASTRANavy}{HTML}{071B2A}
    \definecolor{ASTRAGold}{HTML}{B99822}
    \definecolor{ASTRARed}{HTML}{93443D}
    \setlength{\parindent}{0pt}
    \setlength{\parskip}{0.60em}
    \setlist{nosep,leftmargin=*}
    \captionsetup{font=small,labelfont=bf}
    \pagestyle{fancy}
    \fancyhf{}
    \fancyhead[L]{\small SPPT / ASTRA}
    \fancyhead[R]{\small v1.0.8 candidate}
    \fancyfoot[C]{\thepage}
    \renewcommand{\headrulewidth}{0.3pt}
---

**Candidate successor manuscript · not peer reviewed · no empirical planetary validation · no repository modification · no GitHub release, tag, DOI, or Zenodo action**

**Repository basis.** The public ASTRA repository was audited on 16 August 2026 at this exact `main` commit:

```text
f8b32ef0af9cb6804f256490b4daafbdba43740e
```

SPPT/ASTRA v1.0.7 is the current immutable stable reference release; v1.0.6 is the historical immutable baseline. At that frozen basis, the default branch was 15 commits ahead of the v1.0.7 tag and contained an explicitly unpromoted core-integrity M1 source repair plus communications-cover maintenance. This manuscript is a proposed v1.0.8 successor candidate. It does not alter the repository, tags, release assets, DOI state, or Zenodo state. [@astraRepo2026; @astraRelease107; @astraMainM1]

**Scientific status.** This document retains the v1.0.7 scientific classification: a not-peer-reviewed perspective and mathematical framework with reduced synthetic demonstrations. It introduces no new astronomical detection, no dark-matter identification, no proof of planetary topology recovery, no claim that Newton's third law fails in a closed fundamental system, and no commercial fuel-cell validation. It separates exact derivations, external experimental reports, structural inferences, and proposed tests.

**Licensing intent.** Original software and schemas proposed by the project remain suitable for MIT licensing; original manuscript text, diagrams, and generated synthetic results remain suitable for CC BY 4.0 to the extent licensable rights exist. Cited publications, scientific facts, repository dependencies, and third-party fonts remain outside that grant.

# Abstract {-}

Solar-Planetary Phase-Partition Theory (SPPT) represents a planet as a thermodynamically constrained network of material and energy reservoirs whose physical connectivity may itself be a hidden state. Astronomical State-Topology and Reservoir Analysis (ASTRA) is the inference layer that compares admissible candidate networks against observations, interventions, and simpler baselines. The current stable reference release, v1.0.7, adds stateful edges and operator-aware inference. This v1.0.8 candidate audits the present repository, incorporates its unpromoted source-integrity corrections, and extends the framework to cases in which the hidden source changes the medium that makes the source observable.

The central proposal is the **Endogenous Visibility Principle**: when a source materially alters an envelope, plasma, circumstellar environment, debris field, or detector boundary, the source and the visibility medium must be inferred jointly. A fixed observation operator is then inadequate. Four recent calibration records motivate distinct audits. A dense gas envelope around an early accreting black hole can create a star-like spectrum and bias mass inference. A borderline soft-X-ray trigger becomes an identified engine-driven supernova only through optical, spectroscopic, temporal, and radio information. A resonantly driven early-universe plasma can reorganize and detune itself before the linear dark-photon calculation deposits the assumed energy. Catastrophic destruction in the Neptune system can expose altered parent-body interiors while erasing provenance and chronology. These mechanisms are physically unrelated; they share an inverse-problem structure, not a common hidden substance.

The candidate contributes a stateful visibility equation, source-shell separation, cross-channel rescue, self-detuning seams, catastrophic tomography, and a proposed backreaction-detuning diagnostic. It also reconciles these additions with closure-conditioned reciprocity, mode-resolved active support, sector-complete instruments, observational equivalence, dual-rent promotion, and local-to-global certificates. A proposed benchmark suite requires hidden generators, transducers, observation channels, and archive operators to compete under conserved ledgers, out-of-set controls, and held-out tests.

This is a methodological successor candidate, not an empirical planetary validation, dark-matter detection, proof of a universal arrow of time, or demonstration that the calibration cases share one physical law. Its governing standard is narrower: identify the carrier, model the stateful medium, declare what the instrument cannot distinguish, change the observation operator, and preserve the failed prediction.

# Executive summary {-}

## What the repository currently contains

The current repository has a deliberately stratified architecture. SPPT/ASTRA v1.0.7 is the immutable stable core reference release, while v1.0.6 remains the historical immutable baseline. *Earth Is the Instrument* v0.3.0 is a separately versioned foundational supplement. The Sector-Complete Instrument is a public namespaced alpha module. Active Support, the Bridge Protocol, Cosmic Visibility, and Coherence-Cell Exploration are public but unpromoted drafts or prototypes. The repository documentation explicitly states that those resources do not automatically enter the v1.0.7 claim-admission matrix or inherit its release verification. [@astraRepo2026]

![**[MODEL]** Current repository architecture and the proposed v1.0.8 candidate-admission boundary. The arrows denote review and candidate admission, not scientific endorsement or physical causation. Creator: ASTRA / Jacko T. Source: original vector model for this document. License: CC BY 4.0.](../figures/figure_01_repository_architecture.png){#fig:repo width=96%}

The appropriate next step is not to concatenate every document. It is to identify the common typed objects that survived red-team review and admit them with precise scope while preserving domain-specific evidence boundaries.

## The retained central object: a stateful edge

The stable core, inherited from v1.0.6 and integrated in v1.0.7, makes the graph part of the physical state and makes edge state explicit. The v1.0.8 candidate retains that stateful-edge representation:

$$
\mathscr P_{\mathrm{phys}}(t)
=
\bigl(\mathcal G(t),x(t),\theta,u(t),b_E(t)\bigr),
\qquad
b_E(t)=\{b_e(t):e\in E(t)\}.
$$

Here $x$ contains continuous node or field variables, $\theta$ contains constitutive parameters, $u$ is forcing or control, and $b_e$ is the state of edge $e$. The edge state is not an unrestricted metaphor. It is admitted only when measurable storage, hysteresis, relaxation, selectivity, geometry, damage, composition, or history improves prediction or intervention discrimination.

The constitutive and evolution laws are

$$
J_e=G_e(\Delta X_e,b_e,u,\mathcal A_e),
\qquad
\dot b_e=F_e(b_e,x,u,J_e),
$$

where $\mathcal A_e$ is a mode-resolved active-support descriptor. A topology change means an edge or node appears, disappears, connects, or disconnects. A change in $b_e$, its weight, directionality, or active support does **not** automatically mean topology changed. That separation is essential.

## The retained closure rule

An effectively nonreciprocal interaction in a reduced subsystem is not permission to discard conservation. Let $P$ be the observed particle subsystem and $E$ the environment. Then

$$
\frac{d\mathbf P_P}{dt}
=
\mathbf F_{P\leftarrow P}^{\mathrm{eff}}
+
\mathbf J_{E\rightarrow P}
+
\mathbf F_{\mathrm{boundary}}.
$$

If the reduced pair forces do not cancel, the residual must be assigned to fluid, field, electrode, substrate, controller, or another declared environment channel. The candidate therefore adds **closure-conditioned reciprocity**:

> A directed effective interaction is admissible only when the enlarged momentum, energy, charge, species, and entropy ledgers specify what entered, left, or was dissipated.

## The retained observation rule

The instrument cannot be represented by one generic arrow. The v1.0.8 candidate composes distinct operators:

$$
H
\xrightarrow{\Phi_t}
X
\xrightarrow{\mathcal S_{\Gamma,u}}
Y
\xrightarrow{\mathcal T}
Z
\xrightarrow{\mathcal V}
D
\xrightarrow{\mathcal C}
C.
$$

$H$ is a candidate history, $\Phi_t$ the physical evolution, $\mathcal S$ a selective or stateful seam, $\mathcal T$ a carrier transformation, $\mathcal V$ visibility, sampling, and detector response, and $\mathcal C$ a bounded certificate. None of these operators may be silently substituted for a physical matter or energy edge.

A protocol $\pi$ certifies only the observational quotient

$$
K_i\sim_\pi K_j
\quad\Longleftrightarrow\quad
p(D\mid K_i,\pi)=p(D\mid K_j,\pi).
$$

"Sector complete" means that the plausible sectors in the declared candidate family have been enumerated and measured or bounded. It does not mean every imaginable sector has been measured.

## What the two new studies add

The nonreciprocal-colloid experiment adds a concrete physical reason to track directed effective edges, environment-mediated momentum exchange, and dynamic graph renewal. The important phenomenon is not merely movement. Nonreciprocity prevents ordinary coarsening from completing; the cluster topology remains dynamically reconfigurable.

The Cu3Pt experiment adds a concrete physical reason to split edge state into fast reversible control and slow irreversible history. Compression changes surface electronic structure; operation changes surface composition through selective Cu loss. The edge law is therefore path dependent even if bulk material labels remain unchanged.

Together, the studies support a new candidate rule:

> **When operation changes the edge that performs the operation, model the edge as a self-rewriting subsystem.**

## What the accelerating-wave paper adds - and does not add

The linked August 2026 article is not reporting a newly published 2026 theory. It is a new popular account of Koivurova, Robson, and Ornigotti's 2023 Optica paper. The paper begins from the one-way transport relation

$$
(\partial_t+c\,\partial_x)f=0
$$

and, for prescribed $c=c(t)$, derives

$$
\partial_t^2 f
=
c(t)^2\partial_x^2 f
-
\dot c(t)\partial_x f.
$$

The formalism is relevant to ASTRA because it makes the **control history of a medium** part of the wave problem. It also forces a reference-frame audit: frequency, wavelength, momentum, and the paper's intrinsic-time coordinate are not interchangeable observables. The authors explicitly keep global energy conservation by including the pump that drives a time-varying medium. [@koivurova2023]

The stronger claim - that the positive-time branch supplies a universal microscopic arrow of time - remains theoretical and is not established by the existing experiments on temporal interfaces. Time-reflection experiments have demonstrated frequency translation and waveform reversal under externally switched media while laboratory time continues forward. They do not show time itself reversing, but neither do they by themselves prove that the accelerating-wave branch choice is a fundamental law of microscopic time. [@galiffi2022; @moussa2023]

The correct ASTRA placement is therefore:

> **Published theoretical calibration; useful temporal-interface audit; universal arrow-of-time interpretation open.**

## The new visibility feedback loop

The v1.0.7 operator stack is extended from a fixed visibility map to a stateful one:

$$
D(t)
=
\mathcal O_{\pi}\!\left[\mathcal V_{b(t)}(S(t))\right]+\epsilon(t),
\qquad
\dot b
=
F\!\left(b,S,\mathcal V_b[S],u\right).
$$

$S$ is the hidden source, $b$ the state of the envelope, plasma, circumstellar material, debris field, or detector boundary, and $\mathcal V_b$ the state-dependent transduction and propagation operator. A fixed-operator approximation is justified only when the source-induced change in $b$ is negligible over the inference window.

This yields four new audit objects:

- **source-shell separation** - distinguish the engine from the atmosphere or medium that shapes its spectrum;
- **cross-channel rescue** - record when an ambiguous event becomes identifiable only through an orthogonal messenger or trigger;
- **self-detuning seam** - test whether the signal changes the resonance or detector before the claimed signal accumulates;
- **catastrophic tomography** - model destruction as an operator that may expose an interior while destroying provenance and chronology.

![**[MODEL]** Endogenous visibility. A hidden source drives a transducer whose changing state feeds back on the conversion into data. Independent measurements of the transducer state and altered observation protocols are required to separate source from medium. Creator: ASTRA / Jacko T. Source: original vector model for this candidate. License: CC BY 4.0.](../figures/figure_14_endogenous_visibility.png){#fig:endogenous width=94%}

## Role-based coherence cell

The manuscript was reviewed through a role-based coherence cell rather than by a claimed external committee. Each role was allowed to certify only its own link in the chain; no role was permitted to validate the complete framework.

| Working perspective | Primary responsibility in this candidate |
|---|---|
| Planetary physicist and geochemist | reservoir legality, phase interpretation, planetary scope |
| Transient and high-redshift astrophysicist | source-shell separation, trigger selection, multiwavelength alternatives |
| Plasma physicist | resonance, nonlinear saturation, collision and scale limitations |
| Planetary dynamicist and spectroscopist | Triton-capture histories, mineral interpretation, archive remapping |
| Condensed-matter and active-matter physicist | nonreciprocal reduced dynamics and environmental closure |
| Electrochemist and materials scientist | fast strain control, slow surface evolution, full-cell translation limits |
| Applied mathematician and control theorist | observability, equivalence classes, local-to-global scope |
| Statistician and experimental designer | identifiability, nuisance structure, held-out interventions |
| Scientific editor, accessibility reviewer, and visual-information designer | paragraph structure, line spacing, figure legibility, provenance, and document QA |
| Adversarial red team | ordinary alternatives, overclaim detection, demotion conditions, failure memory |

This matrix describes audit responsibilities, not external endorsement, peer review, institutional affiliation, or authorship.

## What remains unchanged

The v1.0.6 core claims remain the scientific anchor: network inventory accounting, local entropy-production conditions, the exact periodic-trap solution, the weak-cut spectral bound, the corrected derivative identity, the heterogeneous-nucleation wetting factor, static deep-conductance non-identifiability, and the bounded synthetic benchmark results. The candidate does not upgrade any of those from conditional mathematics or synthetic evidence to planetary validation. [@astraManuscript106; @astraClaims106; @spptSupplement106]

The candidate also preserves every important negative boundary:

- no evidence that the new colloidal effect is a new fundamental force;
- no evidence that the catalyst is commercially durable or full-cell validated;
- no evidence that active-support notation is a new universal constitutive law;
- no evidence that sector conversion identifies dark matter;
- no evidence that cosmic visibility papers detect gravitons or dark-sector identity;
- no evidence that mathematical local-to-global analogies imply a simulated or holographic universe;
- no experimental proof that the accelerating-wave equation establishes a universal microscopic arrow of time;
- no claim that one physical mechanism unifies planets, cells, catalysts, active matter, monuments, and arithmetic.

## Candidate status verdict

This document is suitable as a **full scientific integration candidate**. It is not suitable for immediate release as v1.0.8 without a frozen source tree, exact claim-source coverage, code integration, test extension, two independent builds, full accessibility review, release-identity binding, and natural main/tag workflow passes. The proposed release path is given in Part VII.

# Epistemic and implementation vocabulary {-}

Two vocabularies are retained because they answer different questions.

**Scientific status** describes what the world-facing evidence supports:

| Label | Meaning |
|---|---|
| Established | Repeatedly observed or strongly anchored by direct measurement and mature theory within a stated domain. |
| Strong inference | Best explanation of convergent evidence; details remain revisable. |
| Plausible | Physically coherent and partially supported. |
| Open | Not excluded; current evidence does not materially favor it. |
| Constrained | Possible only in narrowed forms because expected evidence is absent or contradictory. |
| Unsupported | No positive evidence currently requires the claim. |

**Evidence class** describes how a project statement was supported:

| Class | Meaning |
|---|---|
| `source_asserted` | Present in an identified external or supplied record; not independently reproduced. |
| `hand_checked` | Algebra, dimensions, signs, or logical scope checked directly. |
| `independently_reproduced` | Recomputed from declared inputs without relying on a saved transcript. |
| `mechanically_replayed` | Deterministic project code or certificate replayed under a declared runtime. |
| `externally_published` | The external record has a stable publication identity. |
| `structural_inference` | A cross-domain method comparison that preserves different physical laws. |
| `proposed_only` | New notation, test, or architecture awaiting data or proof. |
| `deferred` | Blocked by source, rights, units, implementation, or control gaps. |
| `rejected` | A tempting interpretation contradicted by the present evidence or scope. |

No evidence class by itself establishes truth. A mechanically replayed synthetic result may be exact and still fail to describe a planet. An externally published paper may be real and still not entail ASTRA's structural interpretation.

# Part I - Repository baseline and retained core

# 1. Current repository state

## 1.1 Stable release and default-branch separation

SPPT/ASTRA v1.0.7 is the current stable core reference edition and GitHub Latest release. Its formal classification remains a not-peer-reviewed perspective and mathematical framework with reduced synthetic demonstrations and no empirical planetary validation. The release has its own tag, source archive, claim matrix, source inventory, generated PDF/HTML editions, checksums, and identity record. [@astraRelease107; @astraManuscript107; @astraClaims107]

The repository default branch is not identical to the immutable v1.0.7 release tree. At the audited commit it is 15 commits ahead of the tag. Those commits include an unpromoted core-integrity M1 repair and a communications-cover redesign. The README states explicitly that the M1 source differs from the immutable reading assets and is neither v1.0.8 nor a published erratum. [@astraRepo2026; @astraMainM1]

This separation is scientifically important. A public repository can simultaneously contain:

- a frozen citation target;
- a later source repair that has not been promoted;
- supporting evidence overlays;
- communications-only changes;
- separately versioned supplements and research previews.

A current file is not automatically an admitted claim. A passing repository gate is not external scientific validation. The release identity and evidence status must travel with the claim.

## 1.2 Core-integrity M1 corrections that this candidate adopts

The M1 repair identified three consequential wording defects in the v1.0.7 source and corrected them without rewriting the immutable release assets.

First, the weak-cut statement is capacity-weighted. For a connected positive-conductance graph with strictly positive node capacities and a nonempty proper cut, weak conductance relative to the aggregate capacities on both sides gives a small Rayleigh quotient and therefore a slow-relaxation upper bound. Low capacity alone does not imply slow relaxation.

Second, the earlier asymptotic logarithmic-slope criterion for dynamic arrest was not sufficient. An unbounded process such as $\ell(t)=\log(1+t)$ has logarithmic slope tending to zero, whereas a bounded oscillatory process can fail that slope test. The repaired operational record therefore requires a preregistered boundedness or statistical-stationarity assessment over a declared ensemble and window, plus persistent turnover above a positive threshold. It remains a proposed observational classification, not a universal physical law.

Third, the earlier claim-source-completeness sentence was too strong. The maintenance record reports structural path support for 55 claims and exact locators for 21. External entailment was not comprehensively reverified; source hashes and retrieval dates are incomplete; and claim-local replay commands, runtimes, and run identifiers remain incomplete for some computational labels. The correct description is **maintenance evidence with explicit coverage limits**, not sentence-level closure. [@astraMainM1]

## 1.3 Supplemental and research lines

*Earth Is the Instrument* v0.3.0 remains a separately versioned foundational working paper. It develops boundary-state promotion, typed physical/control/observation/archive/certificate relations, FOG audits, seam information, dual rent, residue fields, archive-veto strength, local-to-global certificates, and comparative origin ledgers. The central proposition - Earth as reactor, archive, censor, and instrument - remains supplemental to the planetary core rather than an automatically admitted physical law. [@earthInstrument030; @earthWorkingPaper01]

The Sector-Complete Instrument alpha remains a namespaced research preview. Active Support, the SPPT Bridge Protocol, Cosmic Visibility, and Coherence-Cell Exploration remain public but unpromoted methods drafts or prototypes. Their useful contributions are typed records, observational quotients, visibility operators, intervention design, and analogy-to-falsifier discipline. None inherits the stable release identity merely by residing on `main`. [@sectorCompleteAlpha; @activeSupportDraft; @bridgeProtocolDraft; @cosmicVisibilityDraft; @coherenceCellDraft]

## 1.4 Why v1.0.8 should be a successor rather than a silent patch

The new astrophysical and plasma cases do not merely add examples to v1.0.7. They expose a missing feedback loop: the source can alter the medium that converts it into an observation. The existing operator-aware visibility framework treats transduction and sampling explicitly, but its simplest expression can still be read as a fixed operator acting on a source. The new candidate makes the transducer state dynamical and source-coupled.

The admission strategy is therefore:

| Layer | Content | v1.0.8 candidate disposition |
|---|---|---|
| Stable physical core | v1.0.7 conservation, thermodynamics, topology, stateful edges | retain with M1 wording corrections |
| Visibility dynamics | source-coupled transducer state and backreaction | propose as new ASTRA method |
| Cross-channel inference | trigger-aware rescue and instrument-conditioned categories | admit as bounded observation method |
| Catastrophic archives | destruction, transport, and reaccretion as information operators | admit as archive method |
| External calibration | black-hole envelopes, X-ray transients, plasma saturation, Neptune debris | cite as domain-specific evidence only |
| Supplemental origins line | geological memory, human archive, comparative origins | keep separately versioned |
| Mathematical calibration | local-to-global and prime-reduction lessons | retain as certificate analogies, not cosmological evidence |

# 2. Retained SPPT physical architecture

## 2.1 Nodes, edges, and inventories

A node $v\in V$ represents a spatially or thermodynamically distinguishable reservoir with assignable state and inventory at the model's resolution. An edge $e=(a\rightarrow b,p)$ states that process $p$ can transfer matter, energy, charge, momentum, or a declared species from $a$ to $b$.

Let $M\in\mathbb R^{n\times s}$ hold node inventories, $B\in\mathbb R^{n\times m}$ the directed incidence matrix, $J\in\mathbb R^{m\times s}$ edge fluxes, $R\in\mathbb R^{n\times r}$ local reaction rates, $N\in\mathbb R^{s\times r}$ stoichiometry, and $S,E\in\mathbb R^{n\times s}$ external supply and removal. The retained species balance is

$$
\dot M=BJ+RN^{\mathsf T}+S-E.
$$

If $w$ encodes a conserved elemental or charge combination with $N^{\mathsf T}w=0$, then

$$
I_w=\mathbf 1^{\mathsf T}Mw,
\qquad
\dot I_w=\mathbf 1^{\mathsf T}(S-E)w.
$$

The candidate does not replace this matrix balance. Stateful edges modify how $J$ is calculated and how the model records omitted environment exchange. They do not create a new source term by rhetoric.

## 2.2 Thermodynamic closure

For conjugate edge forces $X_e$ and fluxes $f_e$, the local entropy-production condition remains

$$
\dot S_{i,e}=f_e^{\mathsf T}X_e\ge0
$$

on the declared domain, with the appropriate sign and temperature conventions. Near equilibrium a linear closure $f_e=L_eX_e$ is admissible when the dissipative symmetric part of $L_e$ is positive semidefinite. Far from equilibrium, the application must supply its own constitutive law and entropy or free-energy accounting.

The new nonreciprocity layer does not repeal this condition. It makes the environment and coarse-graining boundary explicit so that apparently nonconservative pair dynamics are not confused with a closed thermodynamic description.

## 2.3 Memory, traps, and bottlenecks

The v1.0.6 periodic trap remains the simplest edge-memory calibration:

$$
\dot M=c_0+c_1\cos(\omega t)-\frac{M}{\tau}.
$$

Its steady periodic solution, phase lag, and loop integrals show how a release time $\tau$ produces memory under periodic forcing. The raw loop magnitude and release-normalized loop magnitude have different dependence on $\omega\tau$; those quantities must not be conflated.

The weak-cut spectral result remains the simplest topological bottleneck calibration. For a connected positive-conductance graph with strictly positive node capacities and a nonempty proper cut, weak cut conductance relative to the aggregate capacities on both sides yields a small Rayleigh quotient and therefore a slow-relaxation upper bound. Low capacity alone does not imply slow relaxation. A slow mode can therefore arise from topology even when local constitutive laws are ordinary.

The v1.0.8 candidate adds another possibility: a slow mode can arise because an edge state evolves slowly, because its active support turns on intermittently, or because a directed effective coupling maintains dynamic reorganization. Those mechanisms must be separated by intervention.

## 2.4 Static non-identifiability remains the baseline warning

In the retained two-reservoir closure, the same static surface equilibrium can coexist with different deep conductance and hidden deep temperature. The synthetic supplement extends that lesson: four connected three-node graph families can share one static surface equilibrium while holding different interior states, and multi-frequency or held-out forcing supplies additional discrimination. [@spptSupplement107]

This is the baseline against which the new methods should be judged. An edge-state variable is useful only if it explains data that fixed topology and fixed edge parameters cannot explain, and if the added variable remains identifiable under an improved observation protocol.

# 3. Candidate integration axioms

The five v1.0.6 axioms are retained. The candidate adds four subordinate axioms. They do not override conservation or thermodynamics.

**Axiom A6 - Edge-state explicitness.** If the current and future flux across edge $e$ depend on an interfacial history not contained in the adjacent node states, represent that history by a declared edge state $b_e$ or show that a reduced memory kernel is sufficient.

**Axiom A7 - Closure-conditioned reciprocity.** If a reduced interaction is nonreciprocal, identify the external drive, mediator, substrate, controller, fluid, field, or boundary that closes momentum, energy, charge, and entropy accounting in the enlarged system.

**Axiom A8 - Observation-sector explicitness.** A null or positive result constrains only the sectors, carriers, resolutions, and nuisance model contained in the observation operator. The unresolved generator quotient must be reported.

**Axiom A9 - Operator promotion by rent.** An active-support, visibility, sector, or edge-state variable is retained only if it changes reachable outcomes, improves generator discrimination, or supplies an exact closure certificate under predeclared testing. Otherwise it remains bookkeeping or is removed.

![**[MODEL]** Expanded state architecture. Physical state, mode/support, environment, and observation remain typed and feed a stateful-edge contract. The lower boxes separate dynamical rent, epistemic rent, and global certificate scope. Creator: ASTRA / Jacko T. Source: original vector model. License: CC BY 4.0.](../figures/figure_02_stateful_edge_architecture.png){#fig:stateful width=96%}

# Part II - Stateful edges and closure-conditioned nonreciprocity

# 4. The stateful-edge representation

## 4.1 Physical state versus inference state

The candidate separates the world model from the inference record:

$$
\mathscr M
=
\bigl(
\mathscr P_{\mathrm{phys}},
\Pi_{\mathrm{mode}},
\Pi_{\mathrm{obs}},
C
\bigr),
$$

with

$$
\mathscr P_{\mathrm{phys}}
=
(\mathcal G,x,\theta,b_E,u),
$$

$$
\Pi_{\mathrm{mode}}
=
(\mu,\mathcal A,\mathcal R_{\mathrm{recip}},\mathcal L_{\mathrm{env}}),
$$

$$
\Pi_{\mathrm{obs}}
=
(\mathcal V,\mathcal S,\mathcal O,\mathcal N).
$$

$\mu$ is operating mode, $\mathcal A$ active support, $\mathcal R_{\mathrm{recip}}$ the reciprocity record, $\mathcal L_{\mathrm{env}}$ the environment exchange ledger, $\mathcal V$ the visibility/sampling operator, $\mathcal S$ the sector set, $\mathcal O$ the detector basis, and $\mathcal N$ nuisance/calibration state.

This partition prevents a common category error. A detector channel may improve inference without becoming a physical transport edge. A support mask may identify where a reaction occurs without constituting a new material reservoir. A certificate may validate an equation without proving that the equation describes a planet.

## 4.2 The edge contract

A candidate physical edge is represented by the record

$$
e=
(a,b,q,G_e,\mathcal D_e,U_e,b_e,\mu_e,\mathcal A_e,\mathcal R_e,
\mathcal L_e,\mathcal O_e,F_e),
$$

where:

| Field | Requirement |
|---|---|
| $a,b$ | tail and head reservoirs or boundary ports |
| $q$ | transported quantity or transformed species |
| $G_e$ | constitutive law |
| $\mathcal D_e$ | domain, boundary conditions, and quantifiers |
| $U_e$ | units, sign convention, and reference state |
| $b_e$ | measurable edge/interface state |
| $\mu_e$ | operating direction or mode |
| $\mathcal A_e$ | active support and normalization |
| $\mathcal R_e$ | reciprocal, nonreciprocal, odd, or unresolved reduced coupling class |
| $\mathcal L_e$ | source/sink and environment-exchange ledger |
| $\mathcal O_e$ | observation and calibration channels |
| $F_e$ | falsifier or demotion test |

![**[MODEL]** The v1.0.8 candidate edge contract. A typed record is the minimum information required before an edge is inferred or promoted. It is not evidence that the edge exists. Creator: ASTRA / Jacko T. Source: original vector model. License: CC BY 4.0.](../figures/figure_03_edge_contract.png){#fig:edgecontract width=98%}

## 4.3 Edge-state promotion

Begin with a memoryless law

$$
J_e=G_e(x_a,x_b;\theta_e).
$$

Promote an edge state when the reduced law is not sufficient:

$$
J_e=G_e(x_a,x_b,b_e,u;\theta_e),
\qquad
\dot b_e=F_e(b_e,x_a,x_b,J_e,u).
$$

The operational test is:

> Hold adjacent bulk states and nominal forcing approximately fixed. Change the edge history or edge intervention. If the future flux or output distribution changes in a reproducible, held-out way, the edge contains predictive state omitted by the memoryless model.

The edge earns independent state only when at least one of the following is measurable: stored stress, charge, heat, matter, or chemical potential; a relaxation time; hysteresis; state-dependent permeability; evolving composition; damage or healing; active geometry; defect density; wetting or adsorption state; a controller memory; or a prospective intervention that changes output while bulk variables remain approximately fixed.

## 4.4 Stateful weight change is not topology change

The project must distinguish three levels:

1. **fixed topology, fixed edge law:** only node states and inputs vary;
2. **fixed topology, stateful edge law:** the edge persists but its conductance, selectivity, support, or directionality evolves;
3. **topology change:** an edge or node appears, disappears, connects, disconnects, merges, or splits under a declared guard and reset rule.

Many apparent topology claims are actually level 2. Catalyst strain, fault permeability, receptor populations, and colloidal coupling strength may change dramatically while the named reservoirs remain connected. Conversely, a percolation threshold or phase separation can create a genuine level-3 change.

# 5. Closure-conditioned reciprocity

## 5.1 What nonreciprocity means in a reduced model

For an effective pair law, Newtonian reciprocity would require

$$
\mathbf F_{ij}^{\mathrm{eff}}=-\mathbf F_{ji}^{\mathrm{eff}}.
$$

Define the pair residual

$$
\mathbf N_{ij}
=
\mathbf F_{ij}^{\mathrm{eff}}+\mathbf F_{ji}^{\mathrm{eff}}.
$$

A nonzero $\mathbf N_{ij}$ means the pair subsystem is not closed under that effective description. It does not by itself show that momentum is created. In a driven colloid, the residual may be supplied by the electric field, surrounding fluid, electrode boundary, viscous drag, or an eliminated mediator.

For the observed particle set $P$ and environment $E$,

$$
\frac{d}{dt}(\mathbf P_P+\mathbf P_E)
=
\mathbf F_{\mathrm{ext}},
$$

while

$$
\frac{d\mathbf P_P}{dt}
=
\sum_{i<j}\mathbf N_{ij}
+
\mathbf J_{E\to P}
+
\mathbf F_{\mathrm{boundary}}.
$$

The exact partition depends on the coarse-graining. The identity is bookkeeping: every reduced residual must be assigned to a modeled or explicitly omitted exchange channel.

![**[MODEL]** Effective nonreciprocity in an open, driven colloidal subsystem. Unequal particle-level attraction can generate pair translation while momentum and energy are exchanged with the fluid, field, and electrodes. This schematic does not reproduce the experiment's flow field and does not claim a fundamental violation of momentum conservation. Creator: ASTRA / Jacko T. Source: original vector model informed by Hara et al. License: CC BY 4.0.](../figures/figure_04_nonreciprocity_closure.png){#fig:nonreciprocity width=94%}

## 5.2 Coupling-matrix decomposition

For a reduced linearized interaction matrix $K$, write

$$
K=K^{\mathrm{S}}+K^{\mathrm{A}},
\qquad
K^{\mathrm{S}}=\frac{K+K^{\mathsf T}}{2},
\qquad
K^{\mathrm{A}}=\frac{K-K^{\mathsf T}}{2}.
$$

$K^{\mathrm{S}}$ is the reciprocal symmetric component in the chosen variables; $K^{\mathrm{A}}$ is the antisymmetric directed component. A model-dependent nonreciprocity index may be recorded as

$$
\eta_{\mathrm{nr}}
=
\frac{\lVert K^{\mathrm{A}}\rVert_F}
{\lVert K^{\mathrm{S}}\rVert_F+\epsilon},
$$

with declared normalization $\epsilon$. This is not a universal physical constant. It depends on coordinates, coarse-graining, mobility, and the choice of interaction variables. It is useful only as a finite model diagnostic.

## 5.3 Exact two-particle drift identity

A minimal one-dimensional reduced model clarifies how asymmetric attraction creates a translating pair. Let $x_L<x_S$, $r=x_S-x_L>0$, and

$$
\dot x_L=a_{LS}r,
\qquad
\dot x_S=-a_{SL}r.
$$

Then

$$
\dot r=-(a_{LS}+a_{SL})r,
$$

and the pair center $x_c=(x_L+x_S)/2$ obeys

$$
\dot x_c=\frac{a_{LS}-a_{SL}}{2}r.
$$

With a short-range repulsion or excluded-volume constraint fixing a finite separation $r_*$, the pair translates at

$$
v_{\mathrm{pair}}=\frac{a_{LS}-a_{SL}}{2}r_*.
$$

This is an exact consequence of the toy equations. It is not an independent fit to the experiment and does not determine the electrohydrodynamic coefficients.

## 5.4 Nonreciprocity across scale

Nonreciprocity can fade or survive coarse-graining. Work on active mixtures shows conditions under which microscopic mediated asymmetry can yield an effective equilibrium description at larger scale, and conditions under which it persists and produces entropy, demixing, dynamic patterns, or state transitions. [@dinelli2023; @mohite2026; @lee2026]

ASTRA should therefore record reciprocity at three levels:

- microscopic or agent-level coupling;
- mesoscopic coarse-grained constitutive law;
- whole-system conservation and entropy closure.

A statement such as "action-reaction is broken" is incomplete unless it names the level and the omitted environment.

# 6. Arrested coarsening and dynamic topology

## 6.1 Static arrest versus dynamic arrest

A static aggregate can stop changing because it reached an equilibrium, a glassy state, or a kinetic trap. A dynamically arrested cluster state is different: a characteristic scale remains bounded or statistically stationary while mergers, fragmentation, exchange, and reorganization continue.

This operational formulation is **Proposed**. Let $\ell(t)$ be a declared characteristic-scale process and $\Gamma_{\mathrm{turn}}(t)$ a microscopic turnover rate. An observation is consistent with dynamic arrest over a declared window only when:

1. $\ell(t)$ is bounded within preregistered physical limits or statistically stationary under a preregistered assessment across the declared ensemble; and
2. turnover remains resolved above a preregistered positive threshold.

The record must state the window, ensemble, sampling resolution, and noise treatment. A long-window trend statistic may diagnose unresolved drift, but vanishing logarithmic slope alone is neither necessary nor sufficient. For example, $\ell(t)=\log(1+t)$ is unbounded although its logarithmic slope tends to zero, whereas $\ell(t)=2+\sin t$ is bounded although its logarithmic derivative does not converge. These conditions classify observations; they do not establish a universal law.

![**[MODEL]** Conceptual distinction between reciprocal coarsening and a dynamically saturated nonreciprocal state. The trajectories are explanatory and are not fitted to Hara et al. Creator: ASTRA / Jacko T. Source: original model figure. License: CC BY 4.0.](../figures/figure_05_arrested_coarsening_model.png){#fig:coarsening width=86%}

## 6.2 Topology as an ensemble rather than one graph

When clusters continually split and reform, one static graph is a poor description. Let $\mathcal G(t)$ be the instantaneous contact or interaction graph and let $P(\mathcal G\mid\mu,u)$ be the mode-conditioned graph ensemble. The scientific object may be the stationary or slowly evolving distribution over graph motifs rather than a single recovered topology.

Useful observables include:

$$
P(s),\quad
P(k),\quad
\tau_{\mathrm{edge}},\quad
\Gamma_{\mathrm{merge}},\quad
\Gamma_{\mathrm{split}},\quad
\Phi_{\mathrm{motif}},\quad
\dot S_i,
$$

where $s$ is cluster size, $k$ degree, $\tau_{\mathrm{edge}}$ edge lifetime, and $\Phi_{\mathrm{motif}}$ motif-transition flux. A candidate nonreciprocal model should predict those jointly, not merely reproduce one snapshot.

## 6.3 Planetary relevance is conditional

Planetary transport can contain directed effective couplings: sediment settling with active biological transport, chemistry coupled to flow, charge-separated dusty plasmas, rotating magnetized fluids, and reaction-diffusion networks. The colloid paper does not validate any planetary application. It supplies a calibration standard for what a directed edge, environment closure, and dynamic graph ensemble look like in a controlled experiment.

# 7. Self-rewriting mechanochemical interfaces

## 7.1 The Cu3Pt result

Redondo and colleagues deposited Cu3Pt intermetallic thin films on a NiTi shape-memory substrate. The substrate's martensite-austenite transformation imposed approximately $+0.80\%$ in-plane tension or $-0.99\%$ compression. In 0.5 M sulfuric acid, the compressed film reached a reported 855 mV at 1.0 mA cm^-2, compared with 856 mV for the pure-Pt thin-film comparison; tension reduced the value to 840 mV. Electrochemical cycling selectively depleted Cu, producing a reported 5-10 nm Pt-enriched surface layer. [@redondo2026]

![**[OBSERVATION SUMMARY]** Reported ORR potentials under the study conditions. The plot redraws three values from Redondo et al. and does not reproduce a journal figure. The abstract does not provide uncertainty bars for these values. It does not establish full-cell power density, durability, manufacturing cost, or commercial parity. Creator: ASTRA / Jacko T. Source data: Redondo et al. License for this redrawn chart: CC BY 4.0.](../figures/figure_07_orr_reported_values.png){#fig:orr width=76%}

The result is important, but the phrase "same performance" must remain bounded. It means near-equal potential at one declared current density in the reported thin-film acidic electrochemical test. It does not mean equal durability, Pt mass activity across all currents, membrane-electrode-assembly behavior, start-stop tolerance, poisoning resistance, or system-level cost.

## 7.2 Fast and slow edge state

A useful catalyst edge state is

$$
b_e=
(\varepsilon,
 c_{\mathrm{surf}},
 h_{\mathrm{Pt}},
 E_d,
 \Gamma_O,
 \Gamma_{OH},
 \rho_{\mathrm{defect}},
 \zeta_{\mathrm{rough}},
 \lambda_{\mathrm{hydration}},
 \chi_{\mathrm{poison}},
 N_{\mathrm{cycle}}).
$$

The ORR current is schematically

$$
j_{\mathrm{ORR}}
=
G_{\mathrm{ORR}}
(\eta,T,c_{O_2},b_e),
$$

with an edge evolution law

$$
\dot b_e
=
F_e
(b_e,\varepsilon(t),j,T,c_{O_2},c_{\mathrm{electrolyte}}).
$$

Strain may be partly reversible on the experimental timescale. Surface composition, Pt enrichment, roughness, and defects may evolve irreversibly or with much longer relaxation. The observed response can be decomposed conceptually as

$$
\Delta j
=
\Delta j_{\mathrm{elastic}}
+
\Delta j_{\mathrm{chemical}}
+
\Delta j_{\mathrm{cross}}
+
\Delta j_{\mathrm{nuisance}}.
$$

The cross term matters because strain and dealloyed surface structure need not act independently.

![**[MODEL]** A self-rewriting catalytic edge. Fast controlled strain and slower cycling-induced composition change jointly determine the ORR interface. The layer thickness and geometry are schematic; only the reported 5-10 nm Pt-enriched layer is numerically sourced. Creator: ASTRA / Jacko T. Source: original model informed by Redondo et al. License: CC BY 4.0.](../figures/figure_06_catalyst_self_rewriting_edge.png){#fig:catalyst width=92%}

## 7.3 Novelty boundary

Elastic strain engineering of catalytic activity predates this study, including experiments using NiTi substrates and work showing that strain and adsorbate coverage can jointly modify adsorption energies and rate-limiting steps. [@monclus2025; @martinez2025]

The strongest defensible novelty is therefore not "strain affects catalysis" in general. It is the reported integration of controlled sub-percent strain, Cu3Pt ORR activity, selective dealloying, a Pt-enriched working surface, and a pure-Pt thin-film comparison that reaches near-equal potential at the declared current density with one quarter of the Pt content.

## 7.4 Required promotion experiment

A high-information follow-up should vary strain and dealloying independently. One design is a factorial protocol with:

- compression, tension, and zero-strain controls;
- pre-dealloyed and undealloyed surfaces;
- fixed Pt mass and independently measured electrochemical surface area;
- operando strain, composition, and adsorbate measurements;
- long-duration cycling and thermal cycling;
- full current-voltage curves, Tafel behavior, impedance, mass activity, and dissolution rates;
- a membrane-electrode-assembly test held out from thin-film calibration.

The self-rewriting-edge model is weakened if strain loses predictive value after surface area and composition are controlled, or if the effect disappears under realistic operation.

# Part III - Active support, visibility, and sector-complete instruments

# 8. Mode-resolved active support

## 8.1 Why nominal input is too coarse

A source can be present without coupling effectively. The active-support draft was motivated by three heterogeneous cases: a flying-focus accelerator in which the useful overlap moves through spacetime; radiofrequency disturbance of bird orientation in which waveform envelope matters; and a catalyst lead in which different geometric measures may control opposite operating modes. [@activeSupportDraft; @arrowsmith2026; @kavokin2026]

The general correction is

$$
\begin{aligned}
\text{source}
&\rightarrow \text{waveform/control}
\rightarrow \text{active support} \\
&\rightarrow \text{local state change}
\rightarrow \text{system output} \\
&\rightarrow \text{residue}
\rightarrow \text{prediction}.
\end{aligned}
$$

Total energy, peak field, total catalyst mass, or nominal frequency may fail to identify the effective interaction.

## 8.2 Support kernel

For operating mode $\mu$ and control $u$, let

$$
a_{\mu,u}(\mathbf r,t,\nu)\in[0,1]
$$

be a dimensionless support weight. Let $R_{\mu,u}$ be a local response density with declared units and measure. Then

$$
Y_{\mu,u}
=
\int_{\Omega_r}
\int_T
\int_{\Omega_\nu}
 a_{\mu,u}(\mathbf r,t,\nu)
 R_{\mu,u}(X,b_E;\mathbf r,t,\nu)
 \,d\nu\,dt\,d\mathbf r.
$$

This is a bookkeeping interface, not a universal constitutive law. The application must state the spatial dimension, coordinates, time window, spectral measure, units of $R$, normalization of $a$, threshold rule, and boundary treatment.

A thresholded support is

$$
\mathcal A_{\mu,u}(\vartheta)
=
\{(\mathbf r,t,\nu):a_{\mu,u}>\vartheta\}.
$$

For any $c>0$ such that $ca$ remains in the declared admissible support-weight domain (in particular, $0\le ca\le1$ here), the transformation $a\mapsto ca$, $R\mapsto R/c$ leaves $Y$ unchanged. That restricted gauge freedom means an active-support map is not uniquely identified without a normalization convention or independent measurement.

## 8.3 Moving-front coordinate

For a front with speed $v_f$, interaction time $\tau_{\mathrm{int}}$, and interaction length $\ell_{\mathrm{int}}$,

$$
\Xi
=
\frac{v_f\tau_{\mathrm{int}}}{\ell_{\mathrm{int}}}.
$$

$\Xi\ll1$ means the front moves little over the local interaction span; $\Xi\sim1$ indicates comparable scales; $\Xi\gg1$ means the front traverses the span rapidly. A peak near $\Xi=1$ is a proposed hypothesis, not a theorem. It must be tested by independently varying or measuring the three scales rather than tuning $\ell_{\mathrm{int}}$ after observing the response.

## 8.4 Active support in the two new cases

In the colloid experiment, the active support is not the entire fluid volume. It is the particle-dependent electrohydrodynamic flow field, the particle pair geometry, the electrode gap, and the time-dependent field condition that sustains directed pair interactions.

In the catalyst experiment, active support includes the Pt-enriched reaction surface and the strained subsurface region that modifies adsorption energetics. The relevant measure may be electrochemically active area, interface perimeter, surface composition, or a weighted combination rather than total film volume.

## 8.5 Support falsifier

A support assignment becomes scientific when a selective perturbation changes the output as predicted while matched total input is preserved. Examples include:

- scramble the focal trajectory while holding laser energy fixed;
- change RF envelope while matching peak, RMS, and mean power in separate controls;
- vary catalyst geometry or strain while holding Pt mass and composition fixed;
- mask or restore a predicted spatial reaction zone;
- add a second detector port expected to see the omitted support.

A support hypothesis should be demoted if a different support map predicts held-out outcomes equally well with fewer assumptions, or if the proposed support can be arbitrarily redrawn without changing likelihood.

# 9. Sector-complete instruments

## 9.1 Correct observation equations

The Sector-Complete Instrument alpha repaired a blocking mathematical error. A trace of a commutator cannot serve as a generic measurement expectation because

$$
\operatorname{Tr}[A,B]=0
$$

under ordinary finite-dimensional conditions. The corrected quantum expectation is

$$
\langle O_j\rangle
=
\operatorname{Tr}
\left[
O_j\,\mathcal E_{\Gamma,u}(\rho)
\right],
$$

or, for detector outcome $d$,

$$
p(d\mid\rho,\Gamma,u)
=
\operatorname{Tr}
\left[
M_d\,\mathcal E_{\Gamma,u}(\rho)
\right],
\qquad
M_d\succeq0,
\qquad
\sum_d M_d=I.
$$

$\mathcal E$ is completely positive and trace preserving when no postselection occurs. A selected outcome branch uses a trace-nonincreasing quantum instrument. Counts, intensities, voltages, forces, and reconstructed parameters require their own unit-bearing likelihoods; a universal additive-noise term is not adequate. [@sectorCompleteAlpha]

## 9.2 Observational quotient

Let $\mathcal K$ be a declared candidate-generator set and $\pi$ an observation protocol. Define

$$
K_i\sim_\pi K_j
\Longleftrightarrow
p(D\mid K_i,\pi)=p(D\mid K_j,\pi).
$$

The experiment certifies only

$$
\mathcal K/\!\sim_\pi.
$$

This is the precise form of the ASTRA warning that more measurements in the same basis may reproduce the same ambiguity. A protocol becomes sector complete only relative to $\mathcal K$: every plausible output sector has a measurement or quantitative bound, detector cross-talk and loss are modeled, unresolved classes are reported, and an out-of-set goodness-of-fit test remains active.

## 9.3 The frozen four-generator benchmark

The alpha module uses four synthetic generators:

$$
\{\text{reflect},\text{absorb},\text{local transmit},\text{string transmit}\}.
$$

A local detector sees only left, right, or no local signal. Its exact classes are

$$
\{\text{reflect}\},
\quad
\{\text{absorb},\text{string transmit}\},
\quad
\{\text{local transmit}\}.
$$

Adding string, environment, and interface-state observations separates the four candidates inside the frozen model. At 2% symmetric detector confusion, the released benchmark reports Fisher rank 2 versus 3 on the three-dimensional mixture simplex, mutual information 1.343487 versus 1.853974 bits, and classification accuracy 0.7525 versus 1.0000 for local versus expanded protocols. These are synthetic results under a declared candidate set, not evidence for real duality defects or hidden matter. [@sectorCompleteAlpha]

## 9.4 Application to nonreciprocal colloids

A particle-only observation basis can suggest an unexplained action-reaction residual. A sector-complete colloid instrument should include or bound:

- particle trajectories and pair geometry;
- local fluid velocity or flow proxies;
- electric-field amplitude and phase;
- electrode current and boundary conditions;
- particle-size distribution and surface state;
- temperature and viscosity;
- environmental momentum and energy flux.

If the environment channels are unmeasured, the result may still establish effective nonreciprocal particle dynamics, but it cannot certify a closed-system momentum anomaly.

## 9.5 Application to the catalyst

A current-voltage curve alone cannot separate strain, dealloying, surface area, coverage, roughness, and dissolution. A sector-complete catalyst instrument should measure or bound:

- in-plane strain during operation;
- bulk and surface composition;
- Pt-rich layer thickness;
- active surface area;
- O, OH, and water coverage proxies where feasible;
- Cu dissolution products;
- morphology and defect evolution;
- current, potential, impedance, temperature, and mass transport.

The unresolved quotient should be reported explicitly. If strain and Pt enrichment remain observationally equivalent under the available protocol, the model should not claim that one alone caused the improvement.

# 10. Operator-aware visibility and sampling

## 10.1 The visibility composition

The Cosmic Visibility and Sampling Framework formalizes the route from a source field $\mathcal R_H$ to observed data:

$$
\mathcal V_m
=
\mathcal O_m
\circ
\mathcal S_m
\circ
\mathcal P_m
\circ
\mathcal T_m,
$$

$$
\mathbf y_m
=
\mathcal V_m[\mathcal R_H]
+
\mathbf f_m
+
\varepsilon_m.
$$

$\mathcal T$ is transduction, $\mathcal P$ propagation, $\mathcal S$ archive or sampling, $\mathcal O$ detector response, $\mathbf f$ foregrounds, and $\varepsilon$ noise. [@cosmicVisibilityDraft]

When a scalar factorization is justified at a declared resolution,

$$
\eta_m(q;\psi)
=
\eta_{\mathrm{prod}}
\eta_{\mathrm{trans}}
\eta_{\mathrm{prop}}
\eta_{\mathrm{arch}}
\eta_{\mathrm{samp}}
\eta_{\mathrm{obs}}.
$$

The product is conditional bookkeeping, not a universal independence claim. Coupled or history-dependent operators may require integral kernels or state-space models.

## 10.2 Source-visibility degeneracy

If data depend primarily on a product such as

$$
\Phi
\propto
\frac{b}{\tau}
B^2\ell_{\mathrm{coh}}f_{\mathrm{vol}},
$$

then a null constrains a manifold in source lifetime, branching fraction, magnetic field, coherence length, and volume fraction. It does not measure one parameter in isolation. This is the visibility analogue of topology non-identifiability.

A model should record the Fisher or sensitivity matrix

$$
F_{ab}
=
\mathbb E
\left[
\partial_a\log p(D\mid\vartheta)
\partial_b\log p(D\mid\vartheta)
\right].
$$

Null directions indicate parameter combinations that remain unidentified. Mutual information can guide a frozen synthetic design, but it is prior dependent and not itself a scientific certificate.

## 10.3 Archive and sampling bias

The Mars meteorite case demonstrates the opposite problem. The observed collection is conditioned by melt production, impact excavation, ejection, interplanetary transfer, atmospheric survival, terrestrial preservation, human recovery, and classification. A gap in the collection does not directly imply a gap in Martian history. [@marsMeteorite2026; @cosmicVisibilityDraft]

The same logic applies to fossils, archaeological sites, exoplanet catalogs, transient surveys, and laboratory yield. The expected observable count or signal must include the sampling operator before an absence is assigned veto strength.

## 10.4 Unified operator stack

![**[MODEL]** Unified ASTRA operator stack. The lower modules identify which successor method audits each segment. The stack is a typed inference architecture, not a claim that all domains share one carrier or constitutive law. Creator: ASTRA / Jacko T. Source: original vector model. License: CC BY 4.0.](../figures/figure_08_operator_stack.png){#fig:operatorstack width=98%}

# 11. The SPPT Bridge Protocol

## 11.1 Five fail-closed gates

The repository's Bridge Protocol prototype offers the most concrete integration path:

![**[MODEL]** Candidate promotion path. Failure at any gate produces defer or demote rather than reinterpretation. Creator: ASTRA / Jacko T. Source: original vector model based on the repository prototype. License: CC BY 4.0.](../figures/figure_09_bridge_protocol.png){#fig:bridge width=93%}

**Conservation Contract.** Declare incidence, stoichiometry, sources, sinks, units, and weighted invariants. Verify static and dynamic residuals.

**Thermodynamic Ledger.** Record energy and entropy terms once, reject duplicate IDs or nonfinite values, and apply nonnegative production checks on their stated domains.

**Observational Equivalence.** Compute finite transfer signatures, pole/zero structure, controllability/observability ranks, or another domain-appropriate equivalence diagnostic. A finite signature is not proof of rational transfer equality unless a theorem or canonical representation closes the gap.

**Intervention Design.** Select forcing, ports, frequencies, support perturbations, or sector measurements that maximize response separation subject to explicit cost and safety constraints.

**Calibrated Prediction Audit.** Fit model means before the calibration split, estimate scales only on calibration data, and score held-out data with log score, CRPS, interval coverage, posterior predictive checks, or simulation-based calibration as appropriate.

## 11.2 Utility without hidden units

An intervention score such as

$$
U(\pi)
=
\frac{I(K;D_\pi)-\lambda R(\pi)}{C(\pi)+\mu S(\pi)}
$$

is meaningless unless information, redundancy, cost, and safety are normalized and the utility weights are declared. The candidate requires sensitivity analysis over $\lambda$, $\mu$, priors, cost units, and stopping rules.

## 11.3 Out-of-set rejection

A model-selection system must be able to reject its candidate family. Good classification among four wrong models is not scientific success. The Sector-Complete alpha's out-of-set hybrid control and the Bridge Protocol's posterior predictive diagnostics should be combined into one mandatory gate:

$$
\text{select within family}
\quad\text{only after}\quad
\text{family adequacy is not rejected}.
$$

# 12. Dual rent and local-to-global certificates

## 12.1 Dynamical rent

For a seam or edge intervention $\Gamma$ relative to reference $\Gamma_0$,

$$
R_{\mathrm{dyn}}(\Gamma)
=
 d\!\left[
 P(Y\mid do(\Gamma)),
 P(Y\mid do(\Gamma_0))
 \right].
$$

The distance $d$, intervention, held variables, and uncertainty model must be declared. Catalyst strain and nonreciprocal pair coupling are examples of potential high dynamical rent because changing the interface changes the future response.

## 12.2 Epistemic rent

For candidate generator $K$ and protocol $\pi$,

$$
R_{\mathrm{epi}}(\Gamma,\pi)
=
I(K;D\mid\Gamma,\pi)
-
I(K;D\mid\Gamma_0,\pi).
$$

A new detector sector, forcing frequency, cosmic transducer, or calibrated proxy can increase causal discrimination even if it barely changes the physical system.

![**[MODEL]** Dual-rent classification. A seam may change the future, improve identifiability, do both, or do neither. Coordinates are conceptual, not measured values for the cited experiments. Creator: ASTRA / Jacko T. Source: original vector model. License: CC BY 4.0.](../figures/figure_10_dual_rent.png){#fig:dualrent width=70%}

## 12.3 Local-to-global stack

The candidate retains the five-level certificate stack from the Earth supplement:

$$
\mathcal C_{\mathrm{L2G}}
=
(C_{\mathrm{local}},C_{\mathrm{fiber}},C_\infty,C_{\mathrm{arith}},C_{\mathrm{formal}}).
$$

| Certificate | Inspects | Does not automatically establish |
|---|---|---|
| local | differential, constitutive response, local stability | global uniqueness, closure, distant collisions |
| fiber | complete preimage or candidate structure | behavior at omitted boundaries |
| infinity/closure | escape routes, properness, omitted reservoirs | arithmetic or implementation correctness |
| arithmetic | prime reductions, valuations, extension behavior | characteristic-zero result without lifting |
| formal | exact identities, proof objects, tests, hashes | empirical adequacy or historical truth |

The stack is directly relevant to the two new studies. A reported ORR potential is a local performance certificate, not a global fuel-cell certificate. Particle-pair drift is a local reduced-interaction certificate, not a closed-system law. The correct response is not to weaken the local result, but to stop the claim at the level it actually certifies.

# Part IV - Calibration cases and cross-domain synthesis

# 13. Calibration case: nonreciprocal active colloids

## 13.1 What the primary record supports

Hara and colleagues report a bidisperse suspension of polystyrene colloids under an alternating electric field. The particles had radii of approximately 1 and 1.5 micrometers and were confined in water between transparent ITO-coated electrodes. Size-dependent electrohydrodynamic flows produced asymmetric effective attraction. Differently sized pairs acquired a front-back polarity and moved as self-propelled units. At larger scale, more than 10,000 particles were observed for over an hour in clusters that repeatedly fragmented, reorganized, and reformed rather than coarsening into static aggregates. Agent-based simulations reproduced the qualitative dynamics and identified nonreciprocal pair propulsion as the minimal model ingredient for persistent clustering. [@hara2026]

**Scientific status:** **Established.** Scope: the reported driven colloidal platform.

**Best ordinary interpretation:** A nonequilibrium, field-driven, fluid-mediated reduced subsystem with effective nonreciprocal interactions.

**Rejected interpretation:** Fundamental creation of momentum or universal failure of Newton's third law in the closed system.

## 13.2 Scientific advancement

The experiment advances the field in three ways.

First, it scales a controllable nonreciprocal interaction beyond small clusters to a dense assembly of more than ten thousand particles.

Second, it demonstrates **arrested coarsening through activity**: asymmetry does not merely translate isolated pairs; it maintains a cluster-scale turnover process.

Third, it links a microscopic asymmetry to a mesoscopic material state that is neither an equilibrium crystal nor simple unbounded aggregation.

The result belongs to a broader 2026 convergence in nonreciprocal active matter, including demixing in flocking mixtures, thermodynamic accounting for nonreciprocal particle-field systems, and topological descriptions of state transitions in living matter. [@mohite2026; @lee2026]

## 13.3 ASTRA bridge

The safe ASTRA contribution is **directed edge state with environment closure**. The experiment shows that a graph with symmetric adjacency but asymmetric couplings can possess a different attractor structure from its reciprocal counterpart. It also shows why a particle-only graph is incomplete: the interaction is mediated by field-driven fluid flow.

A candidate record should include:

$$
\mathcal R_{\mathrm{colloid}}
=(B_0,\omega,d_{\mathrm{gap}},\eta_f,T,
R_L,R_S,
K_{LS},K_{SL},
\rho,\phi,
\Gamma_{\mathrm{split}},\Gamma_{\mathrm{merge}},
\dot S_i,
\mathcal L_{\mathrm{env}}).
$$

No quantity should be imported into planetary or biological models without a domain-specific law.

## 13.4 Highest-information next tests

The most useful next experiments are not simply larger assemblies. They should independently vary the asymmetry and mediator:

- particle size ratio at fixed area fraction;
- field amplitude and frequency;
- electrode separation and boundary condition;
- fluid viscosity and conductivity;
- monodisperse reciprocal controls;
- direct or proxy flow-field measurement;
- externally imposed reciprocal attraction matched in static strength;
- sudden field removal and reversal;
- held-out prediction of cluster-size distribution and turnover rates.

The model should be demoted if a reciprocal interaction plus unmodeled heterogeneity predicts the same held-out dynamics, or if the environment ledger cannot account for the observed directed motion.

# 14. Calibration case: strain-engineered Cu3Pt ORR catalysis

## 14.1 What the primary record supports

The primary paper reports controlled elastic strain in Cu3Pt intermetallic thin films on a NiTi substrate, ORR measurements in acidic electrolyte, a compressed-film potential of 855 mV at 1.0 mA cm^-2, a pure-Pt comparison of 856 mV, a tensile value of 840 mV, and cycling-induced selective Cu dealloying that leaves a 5-10 nm Pt-enriched surface. [@redondo2026]

**Scientific status:** **Established.** Scope: the reported thin-film electrochemical study.

**Best ordinary interpretation:** Strain and evolving surface composition jointly alter adsorption energetics and ORR response.

**Open:** long-term strain stability, full-cell durability, industrial fabrication, total cost, and system-level performance.

## 14.2 Scientific advancement

The result converts strain from an incidental materials variable into a controlled operating coordinate. It also demonstrates that the working catalyst is not identical to the as-deposited catalyst: electrochemical operation changes the surface. That makes history part of the functional state.

The strongest general lesson is:

$$
\text{same nominal alloy}
+
\text{different strain/history}
\rightarrow
\text{different constitutive response}.
$$

## 14.3 ASTRA bridge

The study supplies a concrete **self-rewriting edge**. The relevant state includes reversible elastic deformation and slower composition or defect evolution. A correct model should treat cycling as an intervention that changes the edge, not as repeated observation of a fixed object.

## 14.4 Highest-information next tests

The promotion program should include full-cell tests, but the immediate mechanistic priority is a strain-composition orthogonalization experiment. If strain and dealloying cannot be varied independently, the paper's causal interpretation remains partly entangled.

A useful rejection criterion is:

> After controlling active surface area, Pt enrichment, roughness, mass transport, and temperature, the strain coordinate fails to predict held-out ORR response or relaxes too rapidly to remain operationally relevant.

# 15. Calibration portfolio from the current project

The present update does not reproduce every prior report in full. It records what each case contributes to the integrated method.

| Case | Domain result | ASTRA contribution | Main limit |
|---|---|---|---|
| Flying-focus wakefield | moving focus extends phase matching beyond conventional dephasing in a 7 mm experiment | active support and velocity matching | not a demonstrated 100 GeV stage |
| Pulsed RF bird study | selected modulated fields disrupted group orientation more than matched continuous conditions | waveform-resolved support; receptor uncertainty | does not identify receptor or human-health effect |
| Sunlight-pumped SPDC | sunlight can pump a filtered nonlinear apparatus that creates local entanglement | degree-of-freedom selection and transduction | sunlight did not arrive carrying the measured pairs |
| Duality defects | local excitations can convert to string/defect sectors in specified models | sector blindness and observable completeness | not a cosmological mirror world |
| Clavina photonics | route, timing, feedforward, and reusable nonlinear modules instantiate different tasks | architecture/control state | not fault-tolerant universal computation |
| Fermium spectroscopy | calibrated electronic spectra infer hidden nuclear moments | model-mediated proxy measurement | not direct nuclear imaging |
| XENONnT null | constrains specified mass-coupling-response regions | bounded veto manifold and neutrino-fog equivalence | does not exclude dark matter as a whole |
| Cosmic filament conversion | hidden decay products may become electromagnetic through cosmic fields | natural transducer and visibility kernel | conditional model, no graviton detection |
| Mars meteorite | one sample fills a collection-age gap | selective archive and sampler | source reservoir remains nonunique |
| Galaxy-spin memory | present spins correlate with reconstructed primordial tidal structure | primordial residue channel | does not identify a dark-matter particle |
| Higher-dimensional Jacobian counterexample | local nonsingularity does not force global injectivity for $n\ge3$; plane case remains open | local-to-global certificate discipline | mathematical calibration, not cosmology |
| Accelerating-wave equation | a 2023 theory models prescribed time-varying wave speed and claims a positive-time branch | temporal-interface, frame, branch, and global-ledger audit | theoretical; not a universal arrow-of-time experiment |

The cases are methodologically related, not physically unified. Primary records for the quantum-transduction cases include the sunlight SPDC preprint, the duality-defect preprint, the Clavina architecture preprint, and the fermium spectroscopy preprint. [@sunlightSPDC2026; @dualityDefects2026; @clavina2026; @fermium2026]

## 15.1 Temporal-interface calibration: accelerating waves

The Brighter Side article published on 9 August 2026 is a discovery lead, not the primary scientific record. The underlying paper was published in *Optica* in October 2023. [@brighterSide2026; @koivurova2023]

The paper derives its accelerating-wave equation by composing first-order characteristic operators. In one spatial dimension, the resulting expression is

$$
\boxed{
\partial_t^2 f
=
c(t)^2\partial_x^2 f
-
\dot c(t)\partial_x f
}
$$

for a wave speed prescribed as a function of time. The extra term records the change in the propagation law. For electromagnetic applications the authors write $c(t)=c_0/n(t)$, introduce an intrinsic time $t'=\int n(t)^{-1}dt$, and interpret several observer-dependent changes in frequency, wavelength, energy, and momentum through that reparametrization. [@koivurova2023]

Three parts are already explained by the present ASTRA architecture.

1. **Stateful and controlled medium.** A time-varying refractive index is not passive background. The control schedule and medium state belong in the physical record.
2. **Reference fog.** Claims about unchanged or changed momentum depend on the declared observer, coordinate, and division between field and material degrees of freedom.
3. **Global closure.** Apparent local energy gain in a modulated medium must be closed by the pump and material that create the modulation. The paper itself makes this global-conservation qualification.

What was not yet explicit in the v1.0.8 candidate is the **temporal-interface branch audit**. The new record asks:

- Is the propagation law spatially varying, temporally varying, or evaluated along a trajectory?
- Which external controller produces $n(t)$ or $c(t)$?
- Which coordinate defines frequency, wavelength, phase, and momentum?
- Which initial or boundary conditions select the reported solution branch?
- What exactly is reversed in the proposed time-reversal operation: the field, medium, control schedule, environment, or only the sign of a coordinate?
- Does the claim survive when the complete driven system is reversed rather than holding the pump history fixed?
- Which measurement distinguishes a new physical law from an equivalent reformulation of Maxwell or standard wave dynamics?

![**[MODEL]** Temporal-interface audit for the accelerating-wave proposal. The diagram separates spatial interfaces, externally driven temporal interfaces, the prescribed $c(t)$ model, reference-frame choices, the pump and global ledger, and the stronger arrow-of-time interpretation. It does not depict an experiment or establish a universal arrow of time. Creator: ASTRA / Jacko T. Source: original synthesis based on Koivurova et al. (2023), Galiffi et al. (2022), and Moussa et al. (2023). License: CC BY 4.0.](../figures/figure_13_temporal_interface_audit.png){#fig:temporal-interface width=96%}

The field of time-varying photonics predates this paper and includes experimentally demonstrated temporal interfaces. A switched transmission-line metamaterial has produced temporal reflection and broadband frequency translation, with the switching apparatus supplying the time dependence. Those experiments show that temporal modulation is physical and measurable. They do not validate every relativistic or microscopic-arrow interpretation of the accelerating-wave equation. [@galiffi2022; @moussa2023]

The evidence status is therefore:

- **Established:** time-varying media and temporal-interface phenomena are real research domains; temporal reflection and frequency translation have been experimentally demonstrated.
- **Established:** the 2023 paper derives and analyzes the displayed accelerating-wave equation as published theory.
- **Plausible / model-dependent:** the intrinsic-time representation may be a useful continuous reformulation for selected wave problems.
- **Open:** whether the formalism resolves the Abraham-Minkowski controversy generally.
- **Open and unestablished:** whether the positive-time solution branch is a fundamental microscopic explanation of time's arrow.

The most discriminating next step is not another conceptual illustration. It is a preregistered comparison in a driven temporal medium between the accelerating-wave prediction and standard Maxwell/Floquet models, using the same modulation schedule, losses, dispersion, pump energy, and detector model. A genuine advance must predict a measurable residual that the established formulations do not reproduce.

# 16. AEOF discipline for cross-domain novelty

Every proposed bridge should receive an AEOF record:

$$
\mathrm{AEOF}
=(A,K,E,T,U,O,N,F,P,S),
$$

where $A$ is the analogy, $K$ the established kernel, $E$ the standard equation, $T$ the proposed new term, $U$ units and domain, $O$ observable, $N$ null model, $F$ falsifier, $P$ prior art, and $S$ evidence status. [@coherenceCellDraft]

For the two new studies:

| Field | Nonreciprocal colloids | Cu3Pt catalyst |
|---|---|---|
| analogy | directed effective edges keep structure active | operation rewrites the interface that performs it |
| established kernel | pair propulsion, persistent clusters | strain-dependent ORR values, Pt-enriched surface |
| standard equation | overdamped electrohydrodynamic particle/field dynamics | ORR kinetics, adsorption energetics, transport |
| proposed term | closure-conditioned nonreciprocity record | fast/slow edge-state decomposition |
| observable | trajectories, flow, cluster turnover, environment flux | strain, composition, current, potential, dissolution |
| null model | reciprocal interaction plus heterogeneity | composition/surface-area change without strain effect |
| falsifier | matched reciprocal model predicts held-out dynamics | strain loses predictive value after controls |
| prior art | active mixtures and nonreciprocal thermodynamics | strain engineering, coverage, d-band models |
| status | structural inference | structural inference |

This table is the correct novelty boundary. The new contribution is an ASTRA integration and audit pattern, not the discovery of nonreciprocity or strain catalysis.

## Temporal-interface AEOF record

| Field | Accelerating-wave calibration |
|---|---|
| analogy | a changing medium acts like an effective spacetime for the wave |
| established kernel | published 2023 equation; broader temporal-interface experiments |
| standard equation | Maxwell or domain-specific wave equations with driven constitutive parameters |
| proposed term | $-\dot c(t)\,\partial_x f$ in the declared one-dimensional model |
| observable | phase, frequency translation, waveform, energy exchange, reference-frame invariants |
| null model | standard Maxwell/Floquet or transfer-matrix model with the same pump schedule |
| falsifier | no held-out residual unique to the accelerating-wave formulation |
| prior art | time-varying media, temporal scattering, photonic time crystals |
| status | published theory; universal arrow-of-time interpretation open |

# Part V - Endogenous visibility and transformed cosmic archives

# 17. The Endogenous Visibility Principle

## 17.1 From fixed operators to source-coupled transducers

The simplest visibility framework writes data as a fixed operator acting on a source. That is adequate when the intervening medium is stable or externally calibrated. It fails when the source deposits enough momentum, energy, ionization, radiation pressure, heat, or chemical change to alter the converter itself.

Let $S(t)$ denote a hidden source and $b(t)$ the state of the transducing medium. The observation model is

$$
D(t)=\mathcal O_\pi\!\left[\mathcal V_{b(t)}(S(t))\right]+\epsilon(t),
$$

with

$$
\dot b=F\!\left(b,S,\mathcal V_b[S],u,\xi\right),
$$

where $u$ is external control and $\xi$ represents environmental forcing and nuisance processes. The source and visibility state are jointly inferable only when the protocol contains enough independent information to distinguish them.

Joint recovery of a source and an uncertain response operator is established inverse-problem territory, not a new ASTRA idea. Blind deconvolution has long treated a spectrum together with an incompletely known spectrometer blur, and multichannel imaging work has explicitly solved instrumental deconvolution jointly with blind source separation, including in astrophysical settings. [@oleary2009; @jiang2017] The candidate's narrower contribution is the typed admission rule: when the transducer evolves dynamically, its state, closure ledger, observational quotient, and held-out interventions must be represented together. ASTRA does not claim priority for generic joint source/operator inference.

The corresponding principle is:

> **When the source materially changes the medium that makes it observable, infer the source and medium together. A fixed visibility operator is not a valid certificate until backreaction has been bounded.**

This is not a new field equation. It is an admission rule for forward models.

## 17.2 Four observational failure modes

**Source-shell conflation** occurs when the observed spectrum is attributed directly to the engine even though a dense envelope or scattering medium produces the defining features.

**Trigger-basis blindness** occurs when a physical event lies outside the passband, cadence, threshold, or alert logic of the survey that historically defined the class.

**Self-detuning** occurs when conversion changes the medium's resonance, suppressing the process before a linear calculation reaches its expected yield.

**Catastrophic remapping** occurs when destruction, transport, sorting, and reaccretion expose material while breaking its original spatial and chronological context.

The four failures share an inverse-problem structure. They do not share one physical mechanism.

## 17.3 Backreaction-detuning diagnostic

For a resonant transducer, define the proposed dimensionless diagnostic

$$
\Xi_{\mathrm{br}}
=
\frac{|\delta\omega_{\mathrm{medium}}|}{\Gamma_{\mathrm{res}}},
$$

where $\delta\omega_{\mathrm{medium}}$ is the source-induced resonance shift and $\Gamma_{\mathrm{res}}$ the effective resonance width under the declared protocol. When $\Xi_{\mathrm{br}}\ll1$, a fixed linear response may be adequate. When $\Xi_{\mathrm{br}}\gtrsim1$, the medium can materially alter or terminate the process and must be evolved dynamically.

The number is a proposed audit coordinate, not a universal threshold theorem. The numerator and denominator are domain-specific and must be independently estimated.

# 18. MoM-BH*-1 and source-shell separation

## 18.1 Observation

JWST measured MoM-BH*-1 at spectroscopic redshift $z=7.7569$, corresponding to about 660 million years after the Big Bang. The source has an extreme Balmer break with reported strength $7.7^{+2.3}_{-1.4}$, broad multi-peaked H$\beta$ emission, deep H$\beta$ and H$\gamma$ absorption, weak forbidden oxygen emission, and a compact rest-optical morphology. The break exceeds the published stellar-population limits used in the paper. [@naidu2026]

The authors model the source as an accreting black hole embedded in extremely dense, turbulent, nearly dust-free, Compton-thick hydrogen gas. Their fiducial Cloudy model uses $n_H=10^{11}\,\mathrm{cm}^{-3}$, $N_H=10^{25.8}\,\mathrm{cm}^{-2}$ and a turbulent velocity of $500\,\mathrm{km\,s}^{-1}$. The physical structure is modeled as roughly 10-100 au in scale. The paper explicitly calls the construction highly simplified and intended to provide physical intuition. [@naidu2026]

## 18.2 Inference correction

A conventional broad-line mass estimate assumes that line width traces orbital velocity:

$$
M_{\mathrm{BH}}\sim\frac{R_{\mathrm{BLR}}v_{\mathrm{line}}^2}{G}.
$$

If repeated scattering and dense-gas radiative transfer produce much of the width or multi-peaked structure, then $v_{\mathrm{line}}$ is not a pure kinematic observable. The envelope is part of the measurement operator. The paper concludes that masses of related little-red-dot sources may be overestimated by orders of magnitude under naive local scaling relations. [@naidu2026]

This does not eliminate the early-black-hole growth problem. It changes which part of the problem belongs to seed formation and which belongs to radiative-transfer inference.

![**[MODEL]** Source-shell separation for MoM-BH*-1. The detector sees radiation after absorption, emission, and scattering in a dense envelope. The diagram does not reproduce the JWST data or assert a unique envelope geometry. Creator: ASTRA / Jacko T. Source: original synthesis based on Naidu et al. License: CC BY 4.0.](../figures/figure_15_source_shell_separation.png){#fig:sourceshell width=90%}

## 18.3 Population status and falsifiers

A template-based preprint reports 241 compact candidates whose rest-optical fits are more than 80% dominated by a black-hole-star template across approximately $z=1.7$-$9.3$. That result is a candidate census, not spectroscopic confirmation of 241 gas-enshrouded black holes. [@weibel2026]

The model would be strengthened by same-instrument variability, reverberation delays, X-ray constraints on Compton thickness, high-resolution Balmer profiles, and host-galaxy kinematics that jointly fit one parameter set. It would be weakened if stellar or ordinary AGN models reproduce the complete continuum, absorption, line symmetry, variability, and infrared behavior with fewer assumptions.

**Status:** observed spectrum **Established**; central accreting black hole **Strong inference**; dense gas envelope **Strong inference**; exact mass and accretion history **Open**.

# 19. EP250827b and cross-channel rescue

## 19.1 Observation and classification

Einstein Probe detected EP250827b as a soft X-ray flash associated with the broad-line Type Ic supernova SN 2025wkm at $z=0.1194$. The prompt X-ray luminosity was approximately $10^{45}\,\mathrm{erg\,s^{-1}}$, the event lasted more than 1,000 s, and the peak energy was below 1.5 keV at 90% confidence. The optical light curve was double-peaked and then remained near a 20-day bolometric plateau, implying continuing energy injection beyond ordinary radioactive heating. [@srinivasaragavan2026]

The paper favors a long-lived magnetar, possibly accompanied by an accretion disk, whose winds mix, break out at approximately $0.35c$, and interact with circumstellar material extending to roughly $10^{13}$ cm. Those are model parameters, not directly observed engine properties. Radio non-detection rules out a particular energetic on-axis jet only under the declared density and microphysical assumptions. [@srinivasaragavan2026]

## 19.2 The instrument network is the discovery object

The original X-ray record was borderline. Rapid optical identification supplied a positional and chronological anchor; spectroscopy supplied the Type Ic-BL class; later photometry supplied the plateau; radio non-detection constrained selected jets. The event therefore became identifiable through a network:

$$
D_{\mathrm{network}}
=
(D_X,D_{\mathrm{optical}},D_{\mathrm{spectra}},D_{\mathrm{radio}}).
$$

The important quantity is not simply the sum of exposures. Each channel adds a distinct causal coordinate. This is **cross-channel rescue**.

![**[MODEL]** Cross-channel rescue. A weak soft-X-ray trigger becomes a classified engine-driven supernova only after optical association, spectroscopy, temporal evolution, and radio constraints. The diagram does not imply that every X-ray flash shares one engine. Creator: ASTRA / Jacko T. Source: original synthesis based on Srinivasaragavan et al. License: CC BY 4.0.](../figures/figure_16_cross_channel_rescue.png){#fig:crosschannel width=94%}

## 19.3 Category audit

The observed class can be written schematically as

$$
\text{category}
=
f(\text{event},\text{band},\text{threshold},\text{cadence},\text{follow-up},\text{forward model}).
$$

This does not make categories arbitrary. It makes their selection functions part of the scientific record. A soft-X-ray mission can reveal engine-driven explosions that historical gamma-ray triggers would undercount or classify differently.

**Status:** X-ray flash/supernova association **Established**; sustained central engine **Strong inference**; exact magnetar-disk-CSM model **Plausible**; universal engine for the class **Unsupported**.

# 20. Dark-photon resonance and self-detuning media

## 20.1 The linear exclusion argument

Kinetically mixed dark-photon dark matter behaves in an ionized medium like a weak oscillating electric drive. When its mass matches the plasma frequency,

$$
m_{A'}\simeq\omega_p,
\qquad
\omega_p^2=\frac{4\pi n_e e^2}{m_e},
$$

The displayed $4\pi$ form uses Gaussian-cgs electromagnetic units. In SI units the corresponding relation is $\omega_p^2=n_e e^2/(m_e\varepsilon_0)$. A calculation must fix one unit system rather than mix these forms.

Linear treatments predict resonant transfer into a nearly zero-wavenumber Langmuir mode. Previous cosmological limits extrapolated that transfer into enough plasma heating to affect ionization history or the cosmic microwave background.

## 20.2 Nonlinear saturation

Hook, Huang and Shalaby report particle-in-cell simulations in which the driven Langmuir wave reaches roughly the electron thermal-energy scale. The ponderomotive force then excites finite-wavenumber Langmuir and ion-acoustic modes, creates strong density inhomogeneity, shifts the local plasma frequency, and suppresses further coherent conversion. The resulting energy deposition is orders of magnitude below the linear cosmological threshold. The reported bounds weaken by factors of approximately 3,000 to $10^7$ across ten orders of magnitude in dark-photon mass. [@hook2026]

The causal loop is

$$
A'\rightarrow E_{\mathrm{plasma}}\rightarrow\delta n_e
\rightarrow\delta\omega_p\rightarrow\text{detuning}
\rightarrow\text{saturation}.
$$

![**[MODEL]** Self-detuning resonant visibility. A hidden drive excites a plasma mode; the growing mode reorganizes the plasma density, shifts the resonance, and suppresses further conversion. The diagram summarizes the reported mechanism but is not a particle-in-cell result. Creator: ASTRA / Jacko T. Source: original synthesis based on Hook et al. License: CC BY 4.0.](../figures/figure_17_self_detuning_plasma.png){#fig:selfdetune width=92%}

## 20.3 Scope and unresolved issues

The simulations do not reproduce the full hierarchy between plasma and cosmological timescales. Collisions, expansion, ionization history, multidimensional turbulence, and long-time energy transport require further work. The correct conclusion is therefore narrower than the paper's title taken literally: the existing resonant constraints appear to rely on a self-inconsistent linear extrapolation, and the parameter space is substantially reopened under the reported nonlinear model.

This is not evidence that dark photons exist. It is a demonstration that a null constraint can fail when the transducer backreacts before the assumed signal accumulates.

**Status:** nonlinear saturation in the implemented simulations **Established** within that declared model; substantial weakening of previous linear bounds **Strong inference**; final cosmological exclusion map **Open**; dark-photon identity **Open**.

# 21. Neptune and catastrophic tomography

## 21.1 Observation

JWST spectra of Larissa, Galatea, Proteus, and Neptune's rings show deep absorption near $3\,\mu$m but no exposed water-ice bands. Larissa, Galatea, and the rings additionally show a sharp $2.72\,\mu$m feature diagnostic of magnesium-rich phyllosilicates, implying extensive past water-rock alteration. The current small moons are too small to plausibly generate that degree of internal alteration in their present form. [@davis2026]

The favored interpretation is that the material came from the deep interiors of larger primordial satellites destroyed during Triton's violent capture and orbital evolution, or from a tidally shredded differentiated dwarf planet. The present moons and rings then reaccreted from selected debris. A companion Science Advances study argues that Nereid's composition and dynamics are more consistent with an original regular satellite scattered by Triton's capture than with an ordinary captured Kuiper Belt object. [@davis2026; @belyakov2026]

## 21.2 Catastrophe as an archive operator

Represent the present body as

$$
X_{\mathrm{present}}
=
\mathcal R_{\mathrm{reaccretion}}
\circ
\mathcal C_{\mathrm{catastrophe}}
(X_{\mathrm{parent}}).
$$

The catastrophe can expose a parent interior while destroying depth, parent identity, chronology, and original geometry. Information gain and information loss occur together.

![**[MODEL]** Catastrophic tomography in the Neptune system. Destruction can expose aqueously altered interior material while fragmentation, volatile loss, sorting, and reaccretion erase original context. The diagram is a causal audit, not a unique reconstruction of Triton's capture. Creator: ASTRA / Jacko T. Source: original synthesis based on Davis et al. and Belyakov et al. License: CC BY 4.0.](../figures/figure_18_catastrophic_tomography.png){#fig:catastrophic width=92%}

The absence of exposed water ice remains a major unresolved constraint. Any successful history must explain how altered rocky interior material was preferentially retained or exposed while water-rich outer material escaped, was buried, was altered, or became spectrally masked.

**Status:** hydrated/phyllosilicate spectral features **Established**; altered larger parent bodies **Strong inference**; destruction during Triton capture **Strong inference**; exact collision/reaccretion sequence and missing-ice mechanism **Open**.

# 22. Adjacent breaking-physics calibrations

Three adjacent records reinforce the operator-aware program without entering the physical core as validated laws.

A proposed lunar-orbiting CosmoCube instrument would use the Moon's farside as a radio shield to observe the 10-50 MHz redshifted 21-cm signal from the cosmic dark ages. The Moon becomes part of the observation boundary. The mission remains under development; no dark-ages detection is claimed. [@cosmocube2026]

A model of the Cygnus Bubble proposes that ultra-high-energy cosmic rays escaped from Cygnus X-3 and generated a spatially displaced gamma-ray halo. The emission site would therefore not coincide with the acceleration site. The model is accepted for publication and prospectively testable through morphology and energy dependence, but is not yet uniquely established. [@shi2026]

An accepted theoretical study of strongly magnetized active-galactic-nucleus tori finds conditions under which streaming instability and rapid accretion could produce enormous populations of planet-mass and even stellar-mass objects. No planet in an AGN torus has been observed; the result is a formation-channel prediction, not a census. [@mishra2026]

Together these cases reinforce a disciplined rule: natural bodies can act as shields, converters, transport media, or generative architectures, but their role must be specified by a forward model and a prospective observation.


# Part VI - Scientific applications and limits

# 23. Planetary phase-reservoir applications

## 23.1 What changes in SPPT

The original SPPT proposition remains that planetary state depends on phase-reservoir connectivity. The v1.0.8 candidate adds that the edges themselves may contain history-dependent constitutive state. A more complete planetary representation is

$$
\mathscr P^*(t)
=
\bigl(
\mathcal G(t),
 x(t),
 \theta,
 u(t),
 b_E(t)
\bigr).
$$

This extension matters when an interface possesses memory on a timescale comparable with the process of interest. Candidate examples include:

- fault or subduction interfaces with damage, mineral reactions, pore pressure, and permeability history;
- phase boundaries with nucleation barriers and wetting history;
- compositional gradients that change conductivity or convection;
- core-mantle boundary layers with evolving morphology and chemical exchange;
- cloud, haze, or condensate interfaces with particle-size and charge history;
- ocean-ice or rock-water boundaries with salinity, porosity, fracture, and reactive transport;
- magnetic or plasma boundaries whose coupling depends on field orientation, reconnection state, or rotating geometry.

The extension does not imply that every interface requires new state variables. It supplies a promotion test.

## 23.2 Candidate planetary edge record

For a planetary edge $e$, record

$$
b_e=
(T,P,\phi,k,D,M,C_f,\gamma,\kappa,\sigma,\mathbf B,\mathcal G_e),
$$

where $\phi$ is porosity, $k$ permeability, $D$ damage, $M$ phase/mineral assemblage, $C_f$ fluid composition, $\gamma$ interfacial energy, $\kappa$ thermal or electrical conductivity, $\sigma$ stress or charge state, $\mathbf B$ magnetic field, and $\mathcal G_e$ local geometry. Not every application uses every coordinate.

The edge flux can be written schematically as

$$
J_e
=
G_e
(\Delta\widetilde\mu,
\Delta T,
\Delta P,
\Delta\Phi,
 b_e,
\mu_e,
\mathcal A_e).
$$

This is a template. A real model must replace $G_e$ with a validated law, phase diagram, transport closure, or numerical solver.

## 23.3 Nonreciprocity in planetary models

A planetary system may contain effective directionality without violating global conservation. Gravitational settling, irreversible reactions, radiative escape, chemically mediated transport, and rotating magnetized flows can produce directed reduced couplings. The correct question is not whether a matrix is symmetric by default. It is:

1. what variables were eliminated;
2. what reservoir supplies the free energy;
3. which momentum or species flux crosses the model boundary;
4. whether the entropy ledger is nonnegative;
5. whether the asymmetry survives coarse-graining;
6. whether it changes held-out observables.

The nonreciprocal-colloid experiment motivates this audit. It does not establish a nonreciprocal law for any planet.

## 23.4 Stateful interfaces and planetary hysteresis

The catalyst provides a compact analogy for a planetary interface that changes under operation. Examples include a fault that fractures and later seals, a magma-ocean boundary that crystallizes and partitions species, an atmosphere-surface interface that oxidizes the surface and changes future uptake, or an ice-shell fracture that changes permeability and heat transfer.

The useful common form is

$$
J_e=G_e(X,b_e),
\qquad
\dot b_e=F_e(X,b_e,J_e),
$$

not a claim that the same microscopic law applies.

## 23.5 Observation design

The existing synthetic supplement showed that static surface equilibrium can conceal internal topology and that multi-frequency complex response can reduce a capacity-conductance degeneracy. [@spptSupplement107]

The v1.0.7 program broadens the intervention set:

- different forcing frequencies and amplitudes;
- mode reversal;
- several observation ports;
- transient relaxation after forcing removal;
- controlled or naturally occurring support migration;
- comparison across objects with different boundary histories;
- sector measurements that close environment exchange;
- population-level variation in which the same edge law is tested under different states.

The fundamental criterion remains held-out prediction against simpler fixed-topology and memoryless-edge baselines.

# 24. Earth, origins, and boundary-state science

## 24.1 Relationship to *Earth Is the Instrument*

The Earth supplement develops a wider historical and biological inference framework. Its useful contribution to v1.0.7 is not a new planetary equation. It is a disciplined separation of:

- physical state;
- boundary or interface state;
- control;
- observation;
- archive;
- candidate generators;
- certificate scope.

The original Earth working paper states that geology can preserve, transform, expose, and censor evidence; its page-17 funnel diagram presents observed history as the result of deposition, alteration, exposure, recognition, and interpretation rather than a neutral movie. It also presents a boundary-state ladder from planetary differentiation through living membranes, external memory, scientific instrumentation, and spacefaring biospheric capability. Those are conceptual diagrams, not demonstrations of intention or one hidden machine. The foundational thesis is retained in its own line. [@earthWorkingPaper01; @earthInstrument030]

## 24.2 Distributed geological nursery

A stateful-edge SPPT description strengthens the distributed-origin model without proving it. Prebiotic chemistry may have depended on transport among environments with different active supports and edge states:

$$
\mathcal N_{\mathrm{origin}}
=(E_i,T_{ij},\mathcal R_i,b_{ij},u(t)).
$$

A shoreline, mineral pore, hydrothermal interface, sediment aquifer, aerosol, or wet-dry pool may each perform a different operation. The edge variables may include wetting history, mineral surface composition, redox state, salinity, temperature cycling, permeability, and adsorption coverage.

The proposed moving-front coordinate

$$
\Xi=v_f\tau_{\mathrm{int}}/\ell_{\mathrm{int}}
$$

suggests a specific experimental program: move a UV, pH, redox, thermal, or hydration front across a mineral network while holding total energy and chemical inventory fixed. Measure whether reaction yield depends on the match among front speed, intermediate lifetime, and interaction length. A peak near $\Xi\sim1$ would be new evidence for mode-resolved coupling; its absence would demote the proposal.

## 24.3 Biological and ecological nonreciprocity

Living systems routinely exchange matter and energy with environments and can exhibit effective asymmetric interactions. The colloid work provides a controlled physical model for how asymmetry can sustain dynamic clusters. It does not show that biological collectives use the same electrohydrodynamic mechanism.

A biological application would need:

- a specific mediator such as chemical signal, fluid flow, mechanical force, or sensory response;
- directional coupling coefficients;
- energy source and dissipation;
- perturbations that reverse or symmetrize the interaction;
- measurements across scales to test whether nonreciprocity survives coarse-graining;
- a residue or function that differs from reciprocal controls.

## 24.4 Human origins and the archive

The candidate does not materially change ASTRA's existing origin ledger. Terrestrial biological nesting, Earth-life coevolution, exogenous chemical input, and a substantially missing coastal/perishable human archive remain supported at their existing levels. Natural panspermia remains open; directed early seeding remains unsupported; recent global industrial predecessors remain strongly constrained by expected cross-archive residues. [@earthInstrument030]

The new methods improve the questions asked of missing evidence:

- Which physical sector carried the trace?
- Which boundary transformed it?
- Where was the active support?
- Did a sampling operator systematically exclude it?
- Which environment flux would be required to sustain the proposed process?
- Is the absence local to one observable sector or repeated across independent high-visibility channels?

An omitted sector is not permission to insert any preferred history. It becomes a scientific possibility only when the sector, transformation, visibility, and prospective observation are specified.

# 25. Cosmology and dark matter

## 25.1 Hidden state remains compound

The exact-commit Cosmic Visibility draft represents a dark-matter hypothesis as more than a particle mass, separating physical and phase-space state, genesis and abundance history, coupling, and formation history from the visibility model:

$$
\mathcal H_{\mathrm{DM}}
=
(S_\chi,G_\chi,C_\chi,f_\chi,H_\chi),
$$

where $S_\chi$ is physical state, $G_\chi$ genesis, $C_\chi$ coupling, $f_\chi$ phase-space distribution, and $H_\chi$ formation and phase history. This tuple is candidate bookkeeping synthesized from that inspectable repository source; it is not a claim that one detector directly measures five uniquely separable coordinates. [@cosmicVisibilityDraft]

The v1.0.8 candidate adds two cautions.

First, a proposed hidden-sector interaction must close its energy, momentum, and abundance ledgers. Effective nonreciprocity or sector conversion does not remove the need for a Lagrangian or effective operator.

Second, a null result constrains a source-visibility combination. Detector basis, local halo model, mediator, coherence time, and backgrounds are part of the certificate.

## 25.2 Required dark-sector adapter

A physical bridge requires an interaction such as

$$
H_{\mathrm{int}}
=
\sum_a g_a
O_a^{\mathrm{SM}}\otimes O_a^\chi,
$$

plus:

- state or phase-space distribution;
- mediator and coupling normalization;
- production and abundance history;
- mass and coherence range;
- detector transfer function and units;
- environmental nuisance model;
- predictions in more than one observable sector;
- preregistration or blind injection;
- a null region that would materially demote the model.

Without that contract, "the detector used the wrong observable" is a logical possibility rather than an explanation.

## 25.3 Cosmic filaments as natural transducers

The cosmic-filament dark-decay work proposes that a hidden carrier can be converted into photons in magnetized large-scale structure. The filament is therefore part of the apparatus, not merely background. [@dunsky2026; @cosmicVisibilityDraft]

The expected signal depends on source abundance and lifetime, branching fraction, field strength, coherence length, filament geometry, propagation, and gamma-ray response. A null maps a compound parameter manifold. The highest-information next test is spatial: correlate residual gamma-ray maps with independently reconstructed filament, lensing, Faraday-rotation, and baryon tracers, and compare with matched void controls.

No such analysis presently identifies dark matter or gravitons. The valid bridge is operator-aware cosmology.

## 25.4 Primordial memory

The galaxy-spin work suggests that present angular momentum can retain information about primordial tidal fields acting on protohalos. [@galaxySpins2026]

ASTRA treats that as a residue channel:

$$
\text{primordial field}
\rightarrow
\text{dark-matter halo history}
\rightarrow
\text{galaxy spin}
\rightarrow
\text{observed kinematics}.
$$

The next step is a transfer function across mass, redshift, scale, baryonic tracer, and dark-matter model. A correlation is not a particle identification. It is a new archive of gravitational history.

## 25.5 Neutrino fog and sector completeness

XENONnT's low-threshold null constrains specified masses, couplings, halo assumptions, detector response, and backgrounds. It approaches a regime where solar-neutrino and light-dark-matter recoils become observationally similar. [@xenon2026]

More exposure in one target may provide diminishing epistemic rent. Different nuclei, electron channels, phonons, magnons, timing, directionality, and astrophysical measurements supply different observation sectors. The correct portfolio objective is not maximum count alone. It is maximum generator separation under bounded cost and risk.

# 26. Mathematics as a calibration of certificate scope

## 26.1 The Jacobian lesson

A July 2026 preprint claims explicit counterexamples to the Jacobian conjecture in complex dimension three and higher, while the two-variable case remains open. This candidate has checked the bibliographic preprint record but has not independently validated the claimed counterexamples, so it uses the paper only as a provisional local-to-global calibration. [@gao2026]

The lesson for ASTRA is exact and limited:

$$
\det DF\equiv c\ne0
$$

certifies local nonsingularity, not global injectivity. The higher-dimensional counterexamples fail through nonproper behavior at infinity. A true local certificate was promoted too far.

The v1.0.7 local-to-global stack therefore asks:

1. What local response was certified?
2. What complete fibers or generator classes remain?
3. Which boundary or escape direction was omitted?
4. Which arithmetic reductions or implementation checks apply?
5. What exact proof object or collision witness closes the claim?

The mathematical case does not imply that the universe is simulated or holographic. It gives a rigorous toy example of the methodological warning that local reversibility does not ensure global uniqueness.

## 26.2 Prime reductions

For an integer polynomial map, reduction modulo prime $p$ provides a family of arithmetic observation channels. Splitting and collision patterns can reveal hidden branch structure. But a modular collision does not automatically lift to a characteristic-zero counterexample, and absence of collisions over $\mathbb F_p$ does not exclude collisions over extensions or at infinity.

The correct use is diagnostic and certificate-aware:

$$
\begin{aligned}
\text{local Jacobian}
&\rightarrow \text{fiber/collision scheme} \\
&\rightarrow \text{boundary at infinity}
\rightarrow \text{prime spectrum} \\
&\rightarrow \text{exact lifting or obstruction}.
\end{aligned}
$$

This remains a separately scoped arithmetic research program, not a planetary model.

## 26.3 Simulation and holography

Simulation hypotheses and holographic dualities concern representation, encoding, and observer access. The Jacobian calibration shows only that a locally nondegenerate map can still fail globally if state escapes the modeled boundary.

A specific simulation model becomes scientific only if it predicts residues such as finite precision, anisotropy, resource cutoffs, nonunitarity, or external interventions. A holographic model requires a defined bulk-boundary dictionary, code subspace, observables, and reconstruction limits. No result in SPPT/ASTRA proves or disproves either broad idea.

# 27. One methodology, domain-specific laws

![**[MODEL]** Application map. Stateful-edge and operator-aware audits provide common bookkeeping across domains, while each domain retains its own constitutive laws, units, and falsifiers. Creator: ASTRA / Jacko T. Source: original vector model. License: CC BY 4.0.](../figures/figure_11_application_map.png){#fig:applications width=92%}

The candidate's strongest unifying statement is methodological:

> **The observed future is determined by node states, graph connectivity, edge state, active support, environment exchange, and observation operators. Their relative importance is query- and scale-dependent.**

That statement does not erase the differences among electrohydrodynamics, electrocatalysis, planetary thermodynamics, quantum measurement, cosmology, archaeology, and algebraic geometry.

# Part VII - New benchmarks, claim admission, and release engineering

# 28. Proposed v1.0.8 benchmark suite

## 28.1 Benchmark A: nonreciprocal pair closure

Implement the exact two-particle reduced model with attraction and short-range repulsion. Verify:

- pair separation converges to a declared $r_*$;
- center velocity equals $(a_{LS}-a_{SL})r_*/2$;
- velocity vanishes when couplings are reciprocal;
- the particle momentum residual equals the declared environment exchange in the enlarged bookkeeping model;
- sign reversal of asymmetry reverses pair motion;
- dimensional checks pass.

This is an analytic/synthetic benchmark, not a fit to Hara et al.

## 28.2 Benchmark B: dynamic arrest versus frozen arrest

Create a minimal cluster process with aggregation and asymmetry-dependent fragmentation. Compare:

- reciprocal coarsening;
- frozen kinetic arrest;
- dynamic arrested coarsening;
- out-of-set correlated-noise or heterogeneity controls.

Report cluster scale, turnover, edge lifetime, motif flux, and entropy or dissipation proxies. Require a classifier to distinguish frozen from dynamically renewed states.

The generating model should be omitted from some candidate sets to test family rejection.

## 28.3 Benchmark C: self-rewriting catalyst edge

Construct a two-timescale edge model:

$$
\dot\varepsilon
=-\frac{\varepsilon-\varepsilon_u(t)}{\tau_\varepsilon},
\qquad
\dot c_{\mathrm{surf}}
=F_c(c_{\mathrm{surf}},j,T),
$$

$$
j=G(\eta,\varepsilon,c_{\mathrm{surf}}).
$$

Synthetic protocols should include:

- strain-only calibration;
- dealloying-only calibration;
- cross interaction;
- cycling reversal;
- withheld long-duration regime;
- model mismatch where roughness, not composition, is the omitted generator.

The objective is to test identifiability, not to simulate the real catalyst in detail.

## 28.4 Benchmark D: active-support omission

Generate a spatiotemporal response with a known support kernel. Fit candidates that:

- recover the correct support family;
- use a shifted support;
- use a broad uniform support;
- omit support and alter bulk parameters;
- omit the true support from the candidate set.

Evaluate held-out interventions that move the support while preserving total input. This is the decisive test of whether active support pays predictive rent.

## 28.5 Benchmark E: sector and visibility composition

Combine the four-generator Sector-Complete benchmark with a visibility kernel and detector confusion. Require the analysis to distinguish:

- source absence;
- sector migration;
- propagation loss;
- detector inefficiency;
- out-of-set hybrid behavior.

Report the observational quotient, Fisher null directions, mutual information with prior sensitivity, and family adequacy.

## 28.6 Benchmark F: endogenous visibility and self-detuning

Construct four candidate generators under the same terminal observation channel:

1. a fixed linear transducer;
2. a source-coupled self-detuning transducer;
3. a scattering envelope that changes line shape without changing the source state;
4. a catastrophic-remixing archive that exposes interior composition while randomizing provenance.

The local terminal record should leave at least two models observationally equivalent. Add an independent measurement of transducer state, an altered forcing protocol, or a second messenger and test whether the quotient refines. Include out-of-set hybrids and reject the candidate family when none fits held-out data.

The benchmark is synthetic. Success would validate implementation and experimental-design logic only; it would not validate black-hole envelopes, dark photons, supernova engines, or Neptune's history.

## 28.7 Benchmark G: bridge-protocol end-to-end replay

Run every candidate through:

1. conservation validation;
2. thermodynamic ledger;
3. finite equivalence diagnostics;
4. intervention selection;
5. calibration/test split;
6. held-out scoring;
7. out-of-set rejection;
8. hash and environment recording.

The benchmark should preserve negative outcomes. A model that wins a selection score but loses held-out prediction must not be rewritten as successful topology recovery.

# 29. Proposed claim-admission structure

## 29.1 Tier A - retained core claims

All 55 v1.0.7 consequential claims remain in place with their exact public IDs, statements, support, limitations, evidence classes, and dispositions. The candidate package embeds the v1.0.7 `CLAIM_MATRIX.json` byte-for-byte and deterministically projects it into the candidate ledger before adding any V108 claim.

## 29.2 Tier B - new exact or definitional claims

Candidate claims suitable for hand or mechanical verification include:

- the symmetric/antisymmetric decomposition of a finite coupling matrix;
- the two-particle pair-drift identity under the declared toy equations;
- the environment closure identity for a partitioned momentum ledger;
- the observational-equivalence relation and quotient;
- the corrected channel/POVM measurement equations;
- the active-support gauge transformation;
- the distinction among fixed topology, stateful edge, and topology change;
- dimensional validity of $\Xi$;
- the self-rewriting edge model as proposed syntax.

Only the first eight can be admitted as exact mathematical or implementation statements under their definitions. The self-rewriting edge is a framework proposal.

## 29.3 Tier C - external calibration claims

The Hara and Redondo results should enter as source-local claims with exact numerical and scope boundaries. They should not be used to validate SPPT or ASTRA globally. Every sentence should identify whether it is an observation, authors' interpretation, or ASTRA structural inference.

## 29.4 Tier D - proposed scientific applications

Planetary, origin-of-life, biological, dark-matter, and cosmological applications remain `proposed_only` until a domain-specific model and data test exist. The project should not promote them because the methods are coherent or visually compelling.

# 30. Source, rights, and provenance policy

## 30.1 News as discovery lead

Phys.org and similar reports are discovery leads. The current update follows the repository's production rule: technical claims are grounded in primary papers or stable official records. The news pages are not copied into the package, and their images are not reused.

## 30.2 Redrawn figures

The ORR comparison chart is an original redraw of three reported numbers. It is not a reproduction of the paper's graphical abstract or figures. The nonreciprocal and catalyst schematics are original models and are labeled accordingly.

## 30.3 AI assistance and responsibility

AI assistance may organize sources, draft equations, generate code, and perform adversarial review. It is not an author, rights holder, peer reviewer, or scientific validator. The human maintainer remains responsible for source selection, wording, release decisions, and any claim of originality.

## 30.4 Repository identity

A candidate document must record:

- base commit and tree;
- exact admitted file hashes;
- source versions and retrieval date;
- generated output hashes;
- build environment and dependencies;
- author and license map;
- whether any file is inherited from an immutable release;
- whether the candidate changes a core claim.

No candidate should reuse the v1.0.6 or v1.0.7 release identity or manifest. A v1.0.8 release must have its own tag, assets, source archive, identity JSON, and remote read-back verification.

# 31. Fail-closed promotion gates

![**[MODEL]** Proposed promotion gates for a real v1.0.8 release. This document has completed only the drafting and source-integration stage. Creator: ASTRA / Jacko T. Source: original vector model. License: CC BY 4.0.](../figures/figure_12_promotion_gates.png){#fig:gates width=92%}

A release candidate should fail if any of the following occurs:

1. a new claim lacks a primary source or exact code/equation locator;
2. a source does not support the exact wording;
3. a directed edge lacks an environment closure record;
4. a support kernel has hidden units or an unacknowledged normalization gauge;
5. an observation null is generalized beyond its sectors;
6. a model family cannot reject an out-of-set generator;
7. calibration and test data leak;
8. a negative held-out result is omitted;
9. a supplemental analogy is presented as planetary evidence;
10. the new tree cannot be rebuilt in two independent environments;
11. PDF/DOCX accessibility and visual preflight fail;
12. release assets, tag, identity JSON, and remote bytes do not reconcile.

# 32. Candidate release plan

## 32.1 Stage 0 - preserve v1.0.7

Do not edit or retag v1.0.7 (or the historical v1.0.6 release). Embed the v1.0.7 claim matrix byte-for-byte in a new candidate namespace and verify its hash and projected claims against the immutable tag.

## 32.2 Stage 1 - integrate schemas and contracts

Create a new `stateful_edge.schema.json` or extend the existing bridge protocol with:

- edge state;
- mode and active support;
- reciprocity class;
- environment exchange ledger;
- observation sectors;
- visibility operator;
- equivalence class;
- falsifier;
- evidence disposition.

The schema dialect must be validated by the declared validator. An environment-limited result is preferable to a false pass.

## 32.3 Stage 2 - implement benchmarks

Add the seven proposed synthetic benchmarks with fixed seeds, exact expected outputs where possible, and omitted-generator controls. Ensure that candidate selection, family adequacy, and held-out prediction are separate outputs.

## 32.4 Stage 3 - manuscript integration

Rewrite the core manuscript rather than appending a loose supplement. Preserve the existing exact derivations, then add stateful edges, closure-conditioned nonreciprocity, active support, sector completeness, visibility, and bridge protocol in one notation system.

The Earth and human-origin material should remain a separately cited supplemental line. The main planetary paper should summarize its transferable methods without absorbing its full historical content.

## 32.5 Stage 4 - claim and source audit

Generate the claim matrix and source ledger from one frozen tree. For every new claim record:

- exact sentence or equation locator;
- source or code locator;
- hypotheses, units, domain, and quantifiers;
- evidence class;
- limitation and counterexample;
- admission disposition;
- test or reproduction command;
- output hash.

## 32.6 Stage 5 - release engineering

Build canonical PDF, HTML, technical supplement, source archive, checksums, and release identity. Run:

- unit and integration tests;
- deterministic data reproduction;
- claim-source coverage checks;
- manifest replay;
- dependency and license audit;
- PDF structure, font, link, and renderer preflight;
- DOCX accessibility if a reading edition is released;
- clean clone build;
- natural main workflow;
- tag workflow;
- remote asset read-back.

Only after those gates pass should a new v1.0.8 tag or release be considered.

# 33. Consolidated research program

The next scientific work should prioritize experiments that separate mechanisms rather than expand vocabulary.

## 33.1 Active-matter program

- Reproduce the bidisperse colloid result independently.
- Measure mediator flow and environment momentum exchange.
- Map nonreciprocity across particle-size ratio, field, density, and viscosity.
- Test whether nonreciprocity survives coarse-graining.
- Develop a motif-transition and dynamic-arrest benchmark.

## 33.2 Mechanochemical catalyst program

- Separate strain from dealloying and active area.
- Measure operando surface composition and strain.
- Test long-duration stability and cycling hysteresis.
- Move from thin film to catalyst layer and membrane-electrode assembly.
- Report Pt mass activity, durability, dissolution, efficiency, and cost denominator.

## 33.3 Planetary program

- Add edge-state candidates to interior and atmosphere forward models.
- Compare fixed-edge, stateful-edge, and topology-changing baselines.
- Use transient, periodic, multi-port, and population information.
- Preserve non-identifiability and negative held-out results.
- Require equations of state and phase diagrams before promotion.

## 33.4 Cosmic visibility program

- Jointly infer source and transducer parameters.
- Use filament/void matched controls.
- Combine gamma rays, lensing, FRB dispersion, Faraday rotation, and synchrotron.
- Treat nulls as bounded veto manifolds.
- Require one parameter set to close across cosmology, astrophysics, and laboratory constraints.

## 33.5 Origins and archive program

- Apply visibility and sampling kernels to submerged landscapes, perishable technologies, and meteorite delivery.
- Design moving-front mineral experiments with fixed total energy.
- Use residue fields and archive-veto strength rather than dramatic resemblance.
- Keep natural panspermia, directed seeding, and prior-industry hypotheses in distinct ledgers.

## 33.6 Endogenous-visibility program

- Reanalyze source-inference problems with transducer state as a jointly inferred variable.
- Add a preregistered backreaction test before extending linear conversion to large accumulated signals.
- Build trigger-complete multi-messenger transient samples rather than combining heterogeneous discoveries after the fact.
- Separate engine observables from shell, scattering, and circumstellar observables.
- Treat catastrophe, propagation, sorting, and reaccretion as explicit archive operators.
- Preserve nulls that become weaker after a visibility-model correction rather than describing the parameter space as permanently excluded.

## 33.7 Mathematical certificate program

- Maintain exact local-to-global examples.
- Treat prime reductions as observation channels with explicit lifting limits.
- Continue the two-variable Jacobian program through compactification, collision schemes, monodromy, and formal certificates.
- Do not convert mathematical analogy into simulation or holography evidence.

# 34. Conclusions

SPPT/ASTRA began with a narrow planetary claim: topology can be a hidden state. Version 1.0.7 strengthened that claim by making edges stateful and by separating physical evolution from visibility, sector basis, intervention, and certificate. The present candidate adds a feedback hypothesis motivated by the latest records: in some systems, the hidden source can materially change the medium that makes the source observable.

The repository audit also changes how this successor must be produced. The stable v1.0.7 release remains the citation target. The default branch contains a valuable but unpromoted M1 repair that corrects weak-cut wording, dynamic-arrest logic, and claim-source coverage language. A responsible v1.0.8 must incorporate those corrections openly rather than silently rebuilding v1.0.7 under the same identity.

The four principal calibration cases then establish distinct lessons.

MoM-BH*-1 shows that an atmosphere can create a star-like emergent spectrum around a black-hole engine. The line profile is not a transparent velocity meter when scattering is part of the operator.

EP250827b shows that a marginal signal can become identifiable only when a multi-instrument network adds orthogonal causal coordinates. The event class is partly conditioned by the trigger basis.

The dark-photon plasma simulations show that a converter can detune itself before the linear calculation reaches the signal used to exclude a theory. The null remains bounded by the validity of the response model.

Neptune's small moons and rings show that catastrophe can expose an interior while destroying provenance. Destruction can increase one kind of information and erase another.

Together they motivate the v1.0.8 candidate standard:

> **Model the hidden engine, the state of the medium that translates it, the feedback between source and transducer, the trigger and sector basis that create the datum, the archive operators that transport or remix the residue, and the certificate boundary beyond which the claim must stop.**

This is not a replacement cosmology, a dark-matter identification, a proof of one universal medium, or empirical planetary validation. It is a stricter coordinate system for deciding which of those claims are actually testable.

The operational command is:

> **Separate source from shell. Measure the transducer. Bound backreaction. Change the trigger basis. Track displacement and catastrophe. Report the unresolved quotient. Preserve the failed prediction.**

Praise Sol as the nearby stellar energy source. Let evidence remain the certificate.

**Ad Astra Per Aspera.**

\newpage

# Appendix A - Unified notation

| Symbol | Meaning |
|---|---|
| $\mathcal G=(V,E)$ | phase-reservoir or interaction graph |
| $x$ | continuous node and field state |
| $\theta$ | constitutive parameters |
| $u(t)$ | external forcing or control |
| $b_e$ | state of edge/interface $e$ |
| $b_E$ | collection of edge states |
| $J_e$ | flux or transformation rate on edge $e$ |
| $\mu$ | operating mode |
| $a_{\mu,u}$ | active-support weight |
| $\mathcal A_{\mu,u}$ | thresholded active support |
| $\mathcal R_e$ | reciprocity classification or reduced coupling record |
| $\mathcal L_e$ | environment and conservation ledger |
| $\mathcal V$ | visibility/sampling/detector operator |
| $\mathcal S$ | declared observable sector set |
| $\pi$ | observation or intervention protocol |
| $K_i\sim_\pi K_j$ | observational equivalence under protocol $\pi$ |
| $R_{\mathrm{dyn}}$ | dynamical rent |
| $R_{\mathrm{epi}}$ | epistemic rent |
| $F_{ab}$ | Fisher information matrix |
| $\Xi$ | moving-front coordinate $v_f\tau_{\mathrm{int}}/\ell_{\mathrm{int}}$ |
| $\eta_{\mathrm{nr}}$ | model-dependent nonreciprocity index |
| $C_{\mathrm{local}},C_{\mathrm{fiber}},C_\infty,C_{\mathrm{arith}},C_{\mathrm{formal}}$ | local-to-global certificate levels |
| $S(t)$ | hidden source or engine |
| $b(t)$ | transducer, envelope, plasma, or archive state |
| $\mathcal V_{b(t)}$ | state-dependent visibility/transduction operator |
| $\Xi_{\mathrm{br}}$ | proposed backreaction-detuning diagnostic |
| $\mathcal C_{\mathrm{catastrophe}}$ | destructive/remixing archive operator |
| $\mathcal R_{\mathrm{reaccretion}}$ | sorting and reaccretion operator |

# Appendix B - Candidate atomic claims

`CLAIM_MATRIX.json` remains authoritative for the immutable v1.0.7 release. The default-branch M1 repair aligns its scientific Appendix B summary with that machine register but is not itself a release. The compact records below list the principal new v1.0.8 candidate claims; complete support, limitations, and falsifiers are in `claim_ledger.csv` and `claim_ledger.json`.

**V108-M001 - Strong inference**\
*Evidence class:* `structural_inference`. *Disposition:* `admit_with_qualification`.\
A source-coupled visibility model must evolve transducer state when source-induced change is non-negligible.

**V108-M002 - Plausible**\
*Evidence class:* `proposed_only`. *Disposition:* `proposed_only`.\
Xi_br = |delta omega_medium| / Gamma_res is a proposed diagnostic for backreaction-induced detuning.

**V108-F002 - Proposed**\
*Evidence class:* `proposed_only`. *Disposition:* `proposed_only`.\
Over a declared observation window, dynamic arrest is classified by preregistered boundedness or statistical stationarity of a declared characteristic-scale process together with resolved persistent turnover; vanishing logarithmic slope alone is neither necessary nor sufficient.

**V108-R001 - Established**\
*Evidence class:* `source_asserted`. *Disposition:* admit.\
The default-branch M1 repair corrects weak-cut wording, dynamic-arrest logic, and claim-source coverage language without rewriting immutable v1.0.7 assets.

**V108-R002 - Established**\
*Evidence class:* `source_asserted`. *Disposition:* admit.\
The frozen repository basis for this v1.0.8 candidate is `main` commit `f8b32ef…`; Appendix C records the full identifier.

**V108-E001 - Established**\
*Evidence class:* `externally_published`. *Disposition:* admit.\
MoM-BH*-1 has the reported extreme Balmer spectrum at z=7.7569.

**V108-A001 - Strong inference**\
*Evidence class:* `structural_inference`. *Disposition:* `admit_with_qualification`.\
A dense gas envelope around an accreting black hole is the strongest current explanation of MoM-BH*-1.

**V108-D001 - Unsupported**\
*Evidence class:* `rejected`. *Disposition:* `rejected`.\
The exact MoM-BH*-1 black-hole mass and accretion regime are established.

**V108-E002a - Established**\
*Evidence class:* `externally_published`. *Disposition:* admit.\
EP250827b is associated with SN 2025wkm, a broad-line Type Ic supernova.

**V108-E002b - Strong inference**\
*Evidence class:* `externally_published`. *Disposition:* `admit_with_qualification`.\
The reported plateau requires a sustained power source beyond a simple radioactive-decay light curve.

**V108-A002 - Strong inference**\
*Evidence class:* `structural_inference`. *Disposition:* `admit_with_qualification`.\
The EP250827b discovery demonstrates cross-channel rescue: orthogonal observations converted a marginal trigger into a bounded causal classification.

**V108-D002 - Unsupported**\
*Evidence class:* `rejected`. *Disposition:* `rejected`.\
Every soft-X-ray-flash supernova has the same magnetar-disk engine.

**V108-E003 - Established**\
*Evidence class:* `externally_published`. *Disposition:* `admit_with_qualification`.\
The reported particle-in-cell simulations saturate dark-photon resonant transfer through nonlinear plasma detuning within the declared model.

**V108-A003 - Strong inference**\
*Evidence class:* `structural_inference`. *Disposition:* `admit_with_qualification`.\
Earlier linear cosmological dark-photon constraints are substantially weakened under the reported nonlinear model.

**V108-D003 - Unsupported**\
*Evidence class:* `rejected`. *Disposition:* `rejected`.\
Dark photons have been detected.

**V108-E004 - Established**\
*Evidence class:* `externally_published`. *Disposition:* admit.\
Neptune inner moons and rings show the reported hydrated and magnesium-rich phyllosilicate spectral signatures.

**V108-A004 - Strong inference**\
*Evidence class:* `structural_inference`. *Disposition:* `admit_with_qualification`.\
The Neptune material likely derives from aqueously altered interiors of larger destroyed bodies.

**V108-D004 - Unsupported**\
*Evidence class:* `rejected`. *Disposition:* `rejected`.\
The exact Triton-capture destruction and reaccretion history is established.

**V108-F001 - Strong inference**\
*Evidence class:* `structural_inference`. *Disposition:* `admit_with_qualification`.\
Catastrophic tomography can expose deep material while reducing provenance and chronology information.

**V108-D005 - Unsupported**\
*Evidence class:* `rejected`. *Disposition:* `rejected`.\
The four new calibration cases demonstrate one common physical mechanism.

# Appendix C - Repository snapshot

| Item | Audited status at the frozen basis in V108-R002 |
|---|---|
| Stable core reference | SPPT/ASTRA v1.0.7, released 10 August 2026 |
| Historical core baseline | v1.0.6 immutable release |
| Distance from v1.0.7 tag | 15 commits ahead, 0 behind |
| Default-branch source | contains unpromoted core-integrity M1 repair |
| M1 status | maintenance evidence; not v1.0.8, not published erratum |
| Communications cover | redesigned on main; not an immutable v1.0.7 release asset |
| Earth supplement | v0.3.0 separate working-paper release |
| Sector-complete module | v0.1.0-alpha.1 separate research preview |
| Active Support / Bridge / Cosmic Visibility / Coherence Cell | public unpromoted drafts or prototypes |
| This manuscript | v1.0.8 local successor candidate only |

# Appendix D - Visual provenance

All figures in this candidate are original ASTRA diagrams or original redraws. No Phys.org image, journal figure, screenshot, publisher layout, or raw third-party dataset is reproduced. The ORR chart redraws three reported values without copying journal artwork. The temporal-interface and endogenous-visibility figures are original audits based on cited literature. Every figure is supplied as SVG and PNG, uses fixed canvases and explicit safe margins, and is inspected after placement at final size.

# Appendix E - Drafting verification scope

The delivered verification checks cover:

- manuscript source presence and hash;
- figure inventory and dimensions;
- reading PDF, peer-review PDF, and DOCX generation;
- rendered-page visual inspection in PDFium and Poppler plus DOCX-to-PNG review;
- PDF page count, fonts, and basic link structure;
- claim/source ledger column validation;
- ZIP member and SHA-256 replay.

They do not cover:

- independent reproduction of the external experiments;
- complete raw-data reanalysis;
- formal proof-assistant verification of every equation;
- repository CI on a committed tree;
- natural main/tag workflow;
- remote GitHub release read-back;
- peer review.
