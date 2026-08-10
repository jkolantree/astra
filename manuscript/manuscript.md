---
title: "SPPT / ASTRA v1.0.7: Stateful Edges and Operator-Aware Inference"
subtitle: "Stateful Edges, Active Supports, Nonreciprocal Effective Interactions, Sector-Complete Instruments, and Operator-Aware Visibility"
author: "Jacko T."
date: "10 August 2026"
version: "1.0.7"
lang: en-US
bibliography: references.bib
link-citations: true
reference-section-title: References
toc: true
toc-depth: 3
number-sections: true
geometry: margin=0.78in
fontsize: 10pt
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
    \setlength{\parskip}{0.46em}
    \setlist{nosep,leftmargin=*}
    \captionsetup{font=small,labelfont=bf}
    \pagestyle{fancy}
    \fancyhf{}
    \fancyhead[L]{\small SPPT / ASTRA}
    \fancyhead[R]{\small Reference edition v1.0.7}
    \fancyfoot[C]{\thepage}
    \renewcommand{\headrulewidth}{0.3pt}
---

**Reference edition v1.0.7 · perspective and mathematical framework · not peer reviewed · no empirical planetary validation**

**Repository basis.** This edition is the successor reference line on the post-taxonomy `main` tree. SPPT/ASTRA v1.0.6 remains preserved as an immutable historical release; this v1.0.7 edition has its own source, claim matrix, manifest, tag, and release identity. [@astraRepo2026; @astraRelease106]

**Scientific status.** This edition remains a not-peer-reviewed perspective and mathematical framework with reduced synthetic demonstrations. It introduces no new astronomical detection, no dark-matter identification, no proof of planetary topology recovery, no claim that Newton's third law fails in a closed fundamental system, and no commercial fuel-cell validation. It separates exact derivations, external experimental reports, structural inferences, and proposed tests.

**Correspondence:** [GitHub Issues for this repository](https://github.com/jkolantree/astra/issues)

**Licensing intent.** Original software and schemas proposed by the project remain suitable for MIT licensing; original manuscript text, diagrams, and generated synthetic results remain suitable for CC BY 4.0 to the extent licensable rights exist. Cited publications, scientific facts, repository dependencies, and third-party fonts remain outside that grant.

# Abstract {-}

SPPT/ASTRA v1.0.6 treats phase-reservoir topology as a hidden state: planetary behavior depends not only on total composition and continuous fields, but on which reservoirs exist, which are connected, and what transport or transformation process occupies each edge. The v1.0.7 reference edition extends that program without discarding its core. The principal advance is to distinguish **topology** from **edge state** and to connect physical evolution to the observation operators by which hidden states become inferable.

The proposed physical state is a phase-reservoir graph with continuous node variables and dynamically evolving edge variables. An edge can store strain, composition, damage, adsorbate coverage, permeability, coherence, or other domain-specific state. A mode-resolved **active support** specifies where and when a coupling is effective. A **reciprocity and closure record** distinguishes an effectively nonreciprocal reduced interaction from a failure of momentum or energy accounting in the enlarged system. A **visibility and sampling operator** records the transformations between source, archive, detector, and certificate. A **sector-complete instrument record** reports which plausible observable sectors are measured or bounded and which generator equivalence classes remain unresolved.

Two new experimental reports provide high-value calibration cases. Bidisperse colloids driven by alternating electric fields exhibit nonreciprocal electrohydrodynamic interactions: asymmetric particle pairs self-propel, and dense clusters repeatedly fragment and reorganize rather than coarsening into static aggregates. The result does not abolish action-reaction in the full particle-fluid-field-electrode system; it demonstrates that an open reduced particle subsystem can possess directed effective interactions whose environmental momentum flux must be included in the closure ledger. [@hara2026; @dinelli2023; @mohite2026]

A second study uses a NiTi shape-memory substrate to impose controlled strain on Cu3Pt thin films during the oxygen-reduction reaction. A compressed film reached a reported 855 mV at 1.0 mA cm^-2, compared with 856 mV for pure Pt in the same study conditions, while tensile strain reduced the value to 840 mV. Electrochemical cycling also selectively removed Cu and produced a 5-10 nm Pt-enriched surface. The strongest ASTRA reading is a **self-rewriting edge**: fast reversible strain and slower irreversible surface evolution jointly modify the constitutive response. The report establishes a controlled thin-film ORR result, not full-cell durability, manufacturability, or economy. [@redondo2026; @monclus2025; @martinez2025]

A 2026 news article also resurfaced a peer-reviewed 2023 Optica paper on waves whose effective speed varies with time. The paper proposes an accelerating-wave equation, an intrinsic-time parametrization, and a forward-time solution branch. This fits ASTRA as a **temporal-interface and reference-frame calibration case**, not as established proof of a universal microscopic arrow of time. The full physical audit must include the externally driven modulation, the medium, the field, the selected branch and initial conditions, and the global energy-momentum ledger. [@brighterSide2026; @koivurova2023; @galiffi2022; @moussa2023]

The v1.0.7 reference edition integrates the repository's current namespaced work: the dual-rent and local-to-global certificate methods from *Earth Is the Instrument* v0.3.0; the corrected quantum-instrument and observational-quotient logic of the Sector-Complete Instrument alpha; the mode-resolved active-support audit; the executable SPPT Bridge Protocol; the Cosmic Visibility and Sampling Framework; and the AEOF analogy-to-falsifier discipline of the Coherence-Cell Exploration. [@earthInstrument030; @sectorCompleteAlpha; @activeSupportDraft; @bridgeProtocolDraft; @cosmicVisibilityDraft; @coherenceCellDraft]

The resulting standard is narrower than a universal theory and stronger than a collage of analogies:

> **A proposed edge must state what it transports, how its constitutive law depends on local state and history, where and when it is active, how the enlarged system closes its ledgers, which observation sectors can detect it, which histories remain equivalent, and which held-out result would demote it.**

# Executive summary {-}

## What the repository currently contains

The current repository has a deliberately stratified architecture. SPPT/ASTRA v1.0.7 is the stable current core reference edition; v1.0.6 remains the immutable historical core release. *Earth Is the Instrument* v0.3.0 is a separately versioned supplemental working-paper release. The Sector-Complete Instrument is a public namespaced research preview. Active Support, the Bridge Protocol, Cosmic Visibility, and Coherence-Cell Exploration remain public but unpromoted drafts or prototypes. These resources contribute methods and calibration records only where the v1.0.7 claim matrix says so; none inherits the v1.0.7 release identity automatically. [@astraRepo2026]

![**[MODEL]** Current repository architecture and the v1.0.7 integration boundary. The arrows denote review and scoped admission, not scientific endorsement or physical causation. Creator: ASTRA / Jacko T. Source: original vector model for this document. License: CC BY 4.0.](../figures/figure_01_repository_architecture.png){#fig:repo width=96%}

The integration rule is not to concatenate every document. It is to identify the common typed objects that survived red-team review and admit them with precise scope while preserving domain-specific evidence boundaries.

## The new central object: a stateful edge

Version 1.0.6 makes the graph part of the physical state. The v1.0.7 reference edition proposes that, for many applications, a graph edge must also carry its own state:

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

## The new closure rule

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

If the reduced pair forces do not cancel, the residual must be assigned to fluid, field, electrode, substrate, controller, or another declared environment channel. The v1.0.7 edition therefore adds **closure-conditioned reciprocity**:

> A directed effective interaction is admissible only when the enlarged momentum, energy, charge, species, and entropy ledgers specify what entered, left, or was dissipated.

## The new observation rule

The instrument cannot be represented by one generic arrow. The v1.0.7 reference edition composes distinct operators:

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

Together, the studies motivate a new proposed rule:

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

## What remains unchanged

The v1.0.6 core claims remain the scientific anchor: network inventory accounting, local entropy-production conditions, the exact periodic-trap solution, the weak-cut spectral bound, the corrected derivative identity, the heterogeneous-nucleation wetting factor, static deep-conductance non-identifiability, and the bounded synthetic benchmark results. The v1.0.7 edition does not upgrade any of those from conditional mathematics or synthetic evidence to planetary validation. [@astraManuscript106; @astraClaims106; @spptSupplement106]

The v1.0.7 edition also preserves every important negative boundary:

- no evidence that the new colloidal effect is a new fundamental force;
- no evidence that the catalyst is commercially durable or full-cell validated;
- no evidence that active-support notation is a new universal constitutive law;
- no evidence that sector conversion identifies dark matter;
- no evidence that cosmic visibility papers detect gravitons or dark-sector identity;
- no evidence that mathematical local-to-global analogies imply a simulated or holographic universe;
- no experimental proof that the accelerating-wave equation establishes a universal microscopic arrow of time;
- no claim that one physical mechanism unifies planets, cells, catalysts, active matter, monuments, and arithmetic.

## Release status

This document is the **v1.0.7 stable current reference edition**. It has its own frozen source tree, claim/source coverage, generated documents, release identity, and main/tag workflow. “Stable” here describes the repository and artifact contract; the scientific classification remains a not-peer-reviewed perspective and mathematical framework with reduced synthetic demonstrations and no empirical planetary validation. The external studies and supplemental tracks are calibration inputs, not validations of SPPT or a common physical mechanism.

# Epistemic and implementation vocabulary {-}

Two vocabularies are retained because they answer different questions.

**Scientific status** describes what the world-facing evidence supports:

Table: Scientific-status labels used throughout the v1.0.7 reference edition.

| Label | Meaning |
|---|---|
| Established | Repeatedly observed or strongly anchored by direct measurement and mature theory within a stated domain. |
| Strong inference | Best explanation of convergent evidence; details remain revisable. |
| Plausible | Physically coherent and partially supported. |
| Open | Not excluded; current evidence does not materially favor it. |
| Constrained | Possible only in narrowed forms because expected evidence is absent or contradictory. |
| Unsupported | No positive evidence currently requires the claim. |

**Evidence class** describes how a project statement was supported:

Table: Evidence classes and their project-level meaning.

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

## 1.1 The immutable core

The repository's formal core remains SPPT/ASTRA v1.0.6, released on 2 August 2026. Its release specification identifies a seven-asset allowlist, a fixed build epoch, MIT licensing for software, CC BY 4.0 for manuscript, figures, and data, and a scientific classification of "not-peer-reviewed perspective and mathematical framework with reduced synthetic demonstrations; no empirical planetary validation." [@astraRelease106]

The v1.0.6 manuscript describes a planet as

$$
\mathscr P(t)=\bigl(\mathcal G(t),x(t),\theta,u(t)\bigr),
\qquad
\mathcal G(t)=(V(t),E(t)),
$$

where nodes are reservoirs or phases and edges are physically admissible transport or transformation pathways. It contains five admissibility axioms: inventory closure, energy closure, thermodynamic admissibility, topology legality, and inferential rent. [@astraManuscript106]

The core claim matrix admits exact or bounded claims rather than a single global verdict. Important examples include:

1. internal graph transport cancels in whole-network inventory accounting under the declared incidence convention;
2. a weighted inventory is conserved when the stoichiometric null-vector and external closure hypotheses hold;
3. a positive-semidefinite near-equilibrium phenomenological closure produces nonnegative local entropy production in its declared domain;
4. the periodic one-timescale trap has the displayed analytic solution and loop integrals;
5. a weak conductance cut gives an upper bound on the first nonzero generalized relaxation rate under positive capacities and connected positive-weight topology;
6. the corrected state-dependent derivative retains the upper-state dependence unless fixed explicitly;
7. the spherical-cap heterogeneous-nucleation barrier contains the substrate wetting factor only under its ideal assumptions;
8. a two-reservoir static surface temperature can be independent of deep conductance while the hidden deep temperature remains conductance dependent;
9. topology-change equations are syntax, not a general existence or non-Zeno theorem;
10. the frozen synthetic topology benchmark is regression evidence inside a favorable closed candidate set, not planetary topology recovery. [@astraClaims106]

The v1.0.7 edition keeps those claims intact. It does not change their hypotheses, evidence class, or disposition. For auditability, the retained theorem boundaries are stated explicitly: the weak-cut proposition requires **every node capacity be strictly positive**, the **positive-weight conductance graph be connected**, and a **nonempty proper node set**; the static closure uses a **fixed conductance $K>0$**; the corrected derivative is **injective on the declared physical temperature domain** only when that hypothesis is supplied; the periodic forcing **lies in the range of $L$** when a closed zero-mode solve is claimed; and the hybrid syntax remains conditional on **simultaneous-guard priority**, **reset-map closure**, and a condition excluding **Zeno accumulation**. Any calibrated inference record must declare a **symmetric positive-definite noise covariance** (or its explicitly typed generalization) before rank, likelihood, or prediction claims are admitted.

## 1.2 The separately versioned Earth line

*Earth Is the Instrument* v0.3.0 is a foundational supplemental framework. It develops boundary-state promotion, ASTRA-Layers typed relations, FOG audits, seam information, dual-rent seams, residue fields, archive-veto strength, local-to-global certificates, arithmetic reductions, and a comparative origin ledger. Its central proposition is that Earth can be modeled operationally as reactor, archive, censor, and instrument without implying consciousness or design. [@earthInstrument030; @earthWorkingPaper01]

The v1.0.7 integration uses several methods from this line but does not merge its historical, archaeological, religious, or human-origin claims into the planetary core. The reusable elements are the typed edge discipline, dual-rent promotion test, observation-equifinality analysis, and local-to-global certificate stack.

## 1.3 The namespaced modules and drafts

The repository now exposes four substantial successor methods lines and one exploratory scaffold.

**Sector-Complete Instrument alpha.** This module corrects an invalid trace-of-commutator measurement equation and replaces it with a channel/POVM or quantum-instrument formulation. It defines observational equivalence classes, a bounded meaning of sector completeness, and a four-generator synthetic benchmark in which local observations confuse absorption with string transmission while expanded defect/string observations resolve the candidates. [@sectorCompleteAlpha]

**Mode-Resolved Active-Support Audit.** This draft distinguishes parameter variation, forcing variation, boundary variation, topology variation, observation variation, and operating-mode variation. It introduces a candidate support kernel $a_{\mu,u}(\mathbf r,t,\nu)$ and the dimensionless moving-front coordinate $\Xi=v_f\tau_{\mathrm{int}}/\ell_{\mathrm{int}}$, while explicitly refusing to promote those objects into SPPT physical edges without units and constitutive laws. [@activeSupportDraft]

**SPPT Bridge Protocol.** This executable prototype implements a five-gate successor path:

$$
\text{Conservation Contract}
\rightarrow
\text{Thermodynamic Ledger}
\rightarrow
\text{Observational Equivalence}
\rightarrow
\text{Intervention Design}
\rightarrow
\text{Calibrated Prediction Audit}.
$$

It includes finite transfer signatures, controllability/observability diagnostics, intervention utility, calibration/test splitting, posterior predictive diagnostics, and a strict thermal-edge adapter. It also retains a deliberate JSON Schema dialect warning rather than falsely passing Draft 2020-12 through an older validator. [@bridgeProtocolDraft]

**Cosmic Visibility and Sampling Framework.** This draft writes the source-to-certificate chain as an operator composition. It treats magnetized cosmic filaments as conditional transducers in hidden-decay searches and Martian meteorite delivery as a selective archive. It defines a visibility kernel, source-versus-visibility equivalence classes, multi-messenger calibration, and matched controls. [@cosmicVisibilityDraft]

**Coherence-Cell Exploration.** This scaffold introduces the AEOF record - Analogy, established kernel, standard Equation, proposed term, Observable, and Falsifier. It uses that discipline to prevent the words wave, pressure, coherence, release, or support from silently becoming one physical substrate across unrelated domains. [@coherenceCellDraft]

## 1.4 Why the next version should integrate methods, not collapse domains

The repository has reached a useful but potentially unstable stage. Its core is narrow and tested. Its supplemental methods are richer but distributed. If they remain permanently separate, the project accumulates parallel vocabularies and duplicate audit logic. If they are merged indiscriminately, external calibration cases may be mistaken for planetary evidence or a new physical law.

The v1.0.7 reference edition therefore uses a layered admission strategy:

Table: Layered admission strategy for the v1.0.7 reference edition.

| Layer | Content | Candidate disposition |
|---|---|---|
| Core physical layer | v1.0.6 conservation, thermodynamics, topology, reduced models | retain unchanged |
| Edge-state layer | interface state, active support, reciprocity, environmental closure | admit as typed proposed extension |
| Observation layer | visibility, sector basis, sampling, equivalence classes | admit as ASTRA method |
| Bridge layer | conservation-to-held-out promotion protocol | admit as executable successor method after integration tests |
| External calibration layer | colloids, catalysts, lasers, birds, quantum optics, dark matter, meteorites | cite as domain-specific cases, not validation |
| Earth/human-origins line | archive, FOG, residue fields, comparative origins | retain separately versioned supplement |
| Mathematical calibration | Jacobian local/global failure, prime reductions | retain as analogy and certificate discipline, not planetary physics |

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

The v1.0.7 integration does not replace this matrix balance. Stateful edges modify how $J$ is calculated and how the model records omitted environment exchange. They do not create a new source term by rhetoric.

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

The weak-cut spectral result remains the simplest topological bottleneck calibration. For a connected positive conductance graph with positive capacities, a low-capacity cut or weak conductance cut produces a slow relaxation bound. A slow mode can therefore arise from topology even when local constitutive laws are ordinary.

The v1.0.7 edition adds another possibility: a slow mode can arise because an edge state evolves slowly, because its active support turns on intermittently, or because a directed effective coupling maintains dynamic reorganization. Those mechanisms must be separated by intervention.

The periodic-trap calibration preserves an important scale distinction. At fixed forcing amplitude and frequency, the **raw inventory-loop magnitude increases monotonically** with the release time, while the release-normalized loop is **maximal at $\omega\tau_r=1$**. The former measures retained inventory; the latter measures forcing--release phase mismatch. Likewise, the heterogeneous-nucleation result carries a **substrate-dependent wetting factor** only under its stated ideal assumptions. Electrochemical examples must use **supplied electrochemical free energy**, and the ledger must state that the input is **not latent heat**.

## 2.4 Static non-identifiability remains the baseline warning

In the retained two-reservoir closure, the same static surface equilibrium can coexist with different deep conductance and hidden deep temperature. The synthetic supplement extends that lesson: four connected three-node graph families can share one static surface equilibrium while holding different interior states, and multi-frequency or held-out forcing supplies additional discrimination. [@spptSupplement106]

This is the baseline against which the new methods should be judged. An edge-state variable is useful only if it explains data that fixed topology and fixed edge parameters cannot explain, and if the added variable remains identifiable under an improved observation protocol.

# 3. Integration axioms

The five v1.0.6 axioms are retained. The v1.0.7 edition adds four subordinate axioms. They do not override conservation or thermodynamics.

**Axiom A6 - Edge-state explicitness.** If the current and future flux across edge $e$ depend on an interfacial history not contained in the adjacent node states, represent that history by a declared edge state $b_e$ or show that a reduced memory kernel is sufficient.

**Axiom A7 - Closure-conditioned reciprocity.** If a reduced interaction is nonreciprocal, identify the external drive, mediator, substrate, controller, fluid, field, or boundary that closes momentum, energy, charge, and entropy accounting in the enlarged system.

**Axiom A8 - Observation-sector explicitness.** A null or positive result constrains only the sectors, carriers, resolutions, and nuisance model contained in the observation operator. The unresolved generator quotient must be reported.

**Axiom A9 - Operator promotion by rent.** An active-support, visibility, sector, or edge-state variable is retained only if it changes reachable outcomes, improves generator discrimination, or supplies an exact closure certificate under predeclared testing. Otherwise it remains bookkeeping or is removed.

![**[MODEL]** Expanded state architecture. Physical state, mode/support, environment, and observation remain typed and feed a stateful-edge contract. The lower boxes separate dynamical rent, epistemic rent, and global certificate scope. Creator: ASTRA / Jacko T. Source: original vector model. License: CC BY 4.0.](../figures/figure_02_stateful_edge_architecture.png){#fig:stateful width=96%}

# Part II - Stateful edges and closure-conditioned nonreciprocity

# 4. The stateful-edge representation

## 4.1 Physical state versus inference state

The v1.0.7 integration separates the world model from the inference record:

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

A physical edge admitted by this edition is represented by the record

$$
e=
(a,b,q,G_e,\mathcal D_e,U_e,b_e,\mu_e,\mathcal A_e,\mathcal R_e,
\mathcal L_e,\mathcal O_e,F_e),
$$

where:

Table: Required fields in the v1.0.7 typed edge contract.

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

![**[MODEL]** The v1.0.7 proposed edge contract. A typed record is the minimum information required before an edge is inferred or promoted. It is not evidence that the edge exists. Creator: ASTRA / Jacko T. Source: original vector model. License: CC BY 4.0.](../figures/figure_03_edge_contract.png){#fig:edgecontract width=98%}

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

The benchmark also preserves the original negative result: the **triangle also attains a smaller held-out RMSE** in a subset of runs even when the simpler graph wins the training criterion. This is why the result is neither blind nor external validation and is **not untouched, blinded, or external evaluation**; it is regression evidence for a declared synthetic protocol. A future edge-type substitution must therefore be tested against held-out noisy data and a calibrated equivalence class, not a favorable point estimate.

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

A static aggregate can stop changing because it reached an equilibrium, a glassy state, or a kinetic trap. A dynamically arrested cluster state is different: cluster size stops growing on average while mergers, fragmentation, exchange, and reorganization continue.

Let $\ell(t)$ be a declared characteristic cluster scale and $\Gamma_{\mathrm{turn}}(t)$ a turnover rate counting fragmentation, fusion, or membership exchange. A proposed operational criterion is

$$
\limsup_{t\to\infty}
\left|\frac{d\ln\ell}{d\ln t}\right|
\le\delta,
\qquad
\liminf_{t\to\infty}\Gamma_{\mathrm{turn}}(t)>\Gamma_{\min}>0.
$$

The thresholds $\delta$ and $\Gamma_{\min}$ must be preregistered relative to noise and finite-window uncertainty. The first condition indicates arrested scale growth; the second distinguishes dynamic renewal from a frozen aggregate.

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
\text{source}
\rightarrow
\text{waveform/control}
\rightarrow
\text{active support}
\rightarrow
\text{local state change}
\rightarrow
\text{system output}
\rightarrow
\text{residue}
\rightarrow
\text{prediction}.
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

The transformation $a\mapsto ca$, $R\mapsto R/c$ leaves $Y$ unchanged. That gauge freedom means an active-support map is not uniquely identified without a normalization convention or independent measurement.

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

is meaningless unless information, redundancy, cost, and safety are normalized and the utility weights are declared. The v1.0.7 protocol requires sensitivity analysis over $\lambda$, $\mu$, priors, cost units, and stopping rules.

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

The v1.0.7 integration retains the five-level certificate stack from the Earth supplement:

$$
\mathcal C_{\mathrm{L2G}}
=
(C_{\mathrm{local}},C_{\mathrm{fiber}},C_\infty,C_{\mathrm{arith}},C_{\mathrm{formal}}).
$$

Table: Local-to-global certificate stack and its limits.

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

**Scientific status:** Established within the reported driven colloidal platform.

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

**Scientific status:** Established for the thin-film electrochemical study.

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

Table: Calibration portfolio and the boundary of each case.

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

The v1.0.7 edition makes the **temporal-interface branch audit** explicit. The record asks:

- Is the propagation law spatially varying, temporally varying, or evaluated along a trajectory?
- Which external controller produces the prescribed $n(t)$ or wave-speed history?
- Which coordinate defines frequency, wavelength, phase, and momentum?
- Which initial or boundary conditions select the reported solution branch?
- What exactly is reversed in the proposed time-reversal operation: the field, medium, control schedule, environment, or only the sign of a coordinate?
- Does the claim survive when the complete driven system is reversed rather than holding the pump history fixed?
- Which measurement distinguishes a new physical law from an equivalent reformulation of Maxwell or standard wave dynamics?

![**[MODEL]** Temporal-interface audit for the accelerating-wave proposal. The diagram separates spatial interfaces, externally driven temporal interfaces, the prescribed time-varying speed model, reference-frame choices, the pump and global ledger, and the stronger arrow-of-time interpretation. It does not depict an experiment or establish a universal arrow of time. Creator: ASTRA / Jacko T. Source: original synthesis based on Koivurova et al. (2023), Galiffi et al. (2022), and Moussa et al. (2023). License: CC BY 4.0.](../figures/figure_13_temporal_interface_audit.png){#fig:temporal-interface width=96%}

The field of time-varying photonics predates this paper and includes experimentally demonstrated temporal interfaces. A switched transmission-line metamaterial has produced temporal reflection and broadband frequency translation, with the switching apparatus supplying the time dependence. Those experiments show that temporal modulation is physical and measurable. They do not validate every relativistic or microscopic-arrow interpretation of the accelerating-wave equation. [@galiffi2022; @moussa2023]

The evidence status is therefore:

- **Established:** time-varying media and temporal-interface phenomena are real research domains; temporal reflection and frequency translation have been experimentally demonstrated.
- **Established as published theory:** the 2023 paper derives and analyzes the displayed accelerating-wave equation.
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

Table: AEOF records for the nonreciprocal-colloid and Cu3Pt calibration cases.

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

Table: AEOF record for the accelerating-wave calibration.

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

# Part V - Scientific applications and limits

# 17. Planetary phase-reservoir applications

## 17.1 What changes in SPPT

The original SPPT proposition remains that planetary state depends on phase-reservoir connectivity. The v1.0.7 edition adds that the edges themselves may contain history-dependent constitutive state. A more complete planetary representation is

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

## 17.2 Candidate planetary edge record

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

## 17.3 Nonreciprocity in planetary models

A planetary system may contain effective directionality without violating global conservation. Gravitational settling, irreversible reactions, radiative escape, chemically mediated transport, and rotating magnetized flows can produce directed reduced couplings. The correct question is not whether a matrix is symmetric by default. It is:

1. what variables were eliminated;
2. what reservoir supplies the free energy;
3. which momentum or species flux crosses the model boundary;
4. whether the entropy ledger is nonnegative;
5. whether the asymmetry survives coarse-graining;
6. whether it changes held-out observables.

The nonreciprocal-colloid experiment motivates this audit. It does not establish a nonreciprocal law for any planet.

## 17.4 Stateful interfaces and planetary hysteresis

The catalyst provides a compact analogy for a planetary interface that changes under operation. Examples include a fault that fractures and later seals, a magma-ocean boundary that crystallizes and partitions species, an atmosphere-surface interface that oxidizes the surface and changes future uptake, or an ice-shell fracture that changes permeability and heat transfer.

The useful common form is

$$
J_e=G_e(X,b_e),
\qquad
\dot b_e=F_e(X,b_e,J_e),
$$

not a claim that the same microscopic law applies.

## 17.5 Observation design

The existing synthetic supplement showed that static surface equilibrium can conceal internal topology and that multi-frequency complex response can reduce a capacity-conductance degeneracy. [@spptSupplement106]

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

# 18. Earth, origins, and boundary-state science

## 18.1 Relationship to *Earth Is the Instrument*

The Earth supplement develops a wider historical and biological inference framework. Its useful contribution to v1.0.7 is not a new planetary equation. It is a disciplined separation of:

- physical state;
- boundary or interface state;
- control;
- observation;
- archive;
- candidate generators;
- certificate scope.

The original Earth working paper states that geology can preserve, transform, expose, and censor evidence; its page-17 funnel diagram presents observed history as the result of deposition, alteration, exposure, recognition, and interpretation rather than a neutral movie. It also presents a boundary-state ladder from planetary differentiation through living membranes, external memory, scientific instrumentation, and spacefaring biospheric capability. Those are conceptual diagrams, not demonstrations of intention or one hidden machine. The foundational thesis is retained in its own line. [@earthWorkingPaper01; @earthInstrument030]

## 18.2 Distributed geological nursery

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

## 18.3 Biological and ecological nonreciprocity

Living systems routinely exchange matter and energy with environments and can exhibit effective asymmetric interactions. The colloid work provides a controlled physical model for how asymmetry can sustain dynamic clusters. It does not show that biological collectives use the same electrohydrodynamic mechanism.

A biological application would need:

- a specific mediator such as chemical signal, fluid flow, mechanical force, or sensory response;
- directional coupling coefficients;
- energy source and dissipation;
- perturbations that reverse or symmetrize the interaction;
- measurements across scales to test whether nonreciprocity survives coarse-graining;
- a residue or function that differs from reciprocal controls.

## 18.4 Human origins and the archive

The v1.0.7 integration does not materially change ASTRA's existing origin ledger. Terrestrial biological nesting, Earth-life coevolution, exogenous chemical input, and a substantially missing coastal/perishable human archive remain supported at their existing levels. Natural panspermia remains open; directed early seeding remains unsupported; recent global industrial predecessors remain strongly constrained by expected cross-archive residues. [@earthInstrument030]

The new methods improve the questions asked of missing evidence:

- Which physical sector carried the trace?
- Which boundary transformed it?
- Where was the active support?
- Did a sampling operator systematically exclude it?
- Which environment flux would be required to sustain the proposed process?
- Is the absence local to one observable sector or repeated across independent high-visibility channels?

An omitted sector is not permission to insert any preferred history. It becomes a scientific possibility only when the sector, transformation, visibility, and prospective observation are specified.

# 19. Cosmology and dark matter

## 19.1 Hidden state remains compound

ASTRA's cosmic update represents a dark-matter hypothesis as more than a particle mass:

$$
\mathcal H_{\mathrm{DM}}
=
(S_\chi,G_\chi,C_\chi,f_\chi,H_\chi),
$$

where $S_\chi$ is physical state, $G_\chi$ genesis, $C_\chi$ coupling, $f_\chi$ phase-space distribution, and $H_\chi$ formation and phase history. No single detector measures all five coordinates. [@darkMatterCoherence2026]

The v1.0.7 edition adds two cautions.

First, a proposed hidden-sector interaction must close its energy, momentum, and abundance ledgers. Effective nonreciprocity or sector conversion does not remove the need for a Lagrangian or effective operator.

Second, a null result constrains a source-visibility combination. Detector basis, local halo model, mediator, coherence time, and backgrounds are part of the certificate.

## 19.2 Required dark-sector adapter

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

## 19.3 Cosmic filaments as natural transducers

The cosmic-filament dark-decay work proposes that a hidden carrier can be converted into photons in magnetized large-scale structure. The filament is therefore part of the apparatus, not merely background. [@dunsky2026; @cosmicVisibilityDraft]

The expected signal depends on source abundance and lifetime, branching fraction, field strength, coherence length, filament geometry, propagation, and gamma-ray response. A null maps a compound parameter manifold. The highest-information next test is spatial: correlate residual gamma-ray maps with independently reconstructed filament, lensing, Faraday-rotation, and baryon tracers, and compare with matched void controls.

No such analysis presently identifies dark matter or gravitons. The valid bridge is operator-aware cosmology. The four external calibration studies discussed in the integration outlook are useful constraints and test designs; **none of the four studies validates SPPT**.

## 19.4 Primordial memory

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

## 19.5 Neutrino fog and sector completeness

XENONnT's low-threshold null constrains specified masses, couplings, halo assumptions, detector response, and backgrounds. It approaches a regime where solar-neutrino and light-dark-matter recoils become observationally similar. [@xenon2026]

More exposure in one target may provide diminishing epistemic rent. Different nuclei, electron channels, phonons, magnons, timing, directionality, and astrophysical measurements supply different observation sectors. The correct portfolio objective is not maximum count alone. It is maximum generator separation under bounded cost and risk.

# 20. Mathematics as a calibration of certificate scope

## 20.1 The Jacobian lesson

Recent 2026 work supplies explicit counterexamples to the Jacobian conjecture in complex dimension three and higher, while the two-variable case remains open. [@gao2026]

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

## 20.2 Prime reductions

For an integer polynomial map, reduction modulo prime $p$ provides a family of arithmetic observation channels. Splitting and collision patterns can reveal hidden branch structure. But a modular collision does not automatically lift to a characteristic-zero counterexample, and absence of collisions over $\mathbb F_p$ does not exclude collisions over extensions or at infinity.

The correct use is diagnostic and certificate-aware:

$$
\text{local Jacobian}
\rightarrow
\text{fiber/collision scheme}
\rightarrow
\text{boundary at infinity}
\rightarrow
\text{prime spectrum}
\rightarrow
\text{exact lifting or obstruction}.
$$

This remains a separately scoped arithmetic research program, not a planetary model.

## 20.3 Simulation and holography

Simulation hypotheses and holographic dualities concern representation, encoding, and observer access. The Jacobian calibration shows only that a locally nondegenerate map can still fail globally if state escapes the modeled boundary.

A specific simulation model becomes scientific only if it predicts residues such as finite precision, anisotropy, resource cutoffs, nonunitarity, or external interventions. A holographic model requires a defined bulk-boundary dictionary, code subspace, observables, and reconstruction limits. No result in SPPT/ASTRA proves or disproves either broad idea.

# 21. One methodology, domain-specific laws

![**[MODEL]** Application map. Stateful-edge and operator-aware audits provide common bookkeeping across domains, while each domain retains its own constitutive laws, units, and falsifiers. Creator: ASTRA / Jacko T. Source: original vector model. License: CC BY 4.0.](../figures/figure_11_application_map.png){#fig:applications width=92%}

The edition's strongest unifying statement is methodological:

> **The observed future is determined by node states, graph connectivity, edge state, active support, environment exchange, and observation operators. Their relative importance is query- and scale-dependent.**

That statement does not erase the differences among electrohydrodynamics, electrocatalysis, planetary thermodynamics, quantum measurement, cosmology, archaeology, and algebraic geometry.

# Part VI - New benchmarks, claim admission, and release engineering

# 22. Proposed v1.0.7 benchmark suite

## 22.1 Benchmark A: nonreciprocal pair closure

Implement the exact two-particle reduced model with attraction and short-range repulsion. Verify:

- pair separation converges to a declared $r_*$;
- center velocity equals $(a_{LS}-a_{SL})r_*/2$;
- velocity vanishes when couplings are reciprocal;
- the particle momentum residual equals the declared environment exchange in the enlarged bookkeeping model;
- sign reversal of asymmetry reverses pair motion;
- dimensional checks pass.

This is an analytic/synthetic benchmark, not a fit to Hara et al.

## 22.2 Benchmark B: dynamic arrest versus frozen arrest

Create a minimal cluster process with aggregation and asymmetry-dependent fragmentation. Compare:

- reciprocal coarsening;
- frozen kinetic arrest;
- dynamic arrested coarsening;
- out-of-set correlated-noise or heterogeneity controls.

Report cluster scale, turnover, edge lifetime, motif flux, and entropy or dissipation proxies. Require a classifier to distinguish frozen from dynamically renewed states.

The generating model should be omitted from some candidate sets to test family rejection.

## 22.3 Benchmark C: self-rewriting catalyst edge

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

## 22.4 Benchmark D: active-support omission

Generate a spatiotemporal response with a known support kernel. Fit candidates that:

- recover the correct support family;
- use a shifted support;
- use a broad uniform support;
- omit support and alter bulk parameters;
- omit the true support from the candidate set.

Evaluate held-out interventions that move the support while preserving total input. This is the decisive test of whether active support pays predictive rent.

## 22.5 Benchmark E: sector and visibility composition

Combine the four-generator Sector-Complete benchmark with a visibility kernel and detector confusion. Require the analysis to distinguish:

- source absence;
- sector migration;
- propagation loss;
- detector inefficiency;
- out-of-set hybrid behavior.

Report the observational quotient, Fisher null directions, mutual information with prior sensitivity, and family adequacy.

## 22.6 Benchmark F: bridge-protocol end-to-end replay

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

# 23. Proposed claim-admission structure

## 23.1 Tier A - retained core claims

All v1.0.6 consequential claims remain in place with their existing wording and limitations. The v1.0.7 claim matrix records their retained dispositions alongside the new scoped method claims; any future claim addition must be diffed against the immutable v1.0.6 matrix before admission.

## 23.2 Tier B - new exact or definitional claims

The v1.0.7 claims suitable for hand or mechanical verification include:

- the symmetric/antisymmetric decomposition of a finite coupling matrix;
- the two-particle pair-drift identity under the declared toy equations;
- the environment closure identity for a partitioned momentum ledger;
- the observational-equivalence relation and quotient;
- the corrected channel/POVM measurement equations;
- the active-support gauge transformation;
- the distinction among fixed topology, stateful edge, and topology change;
- dimensional validity of $\Xi$;
- the self-rewriting edge model as proposed syntax.

Only the first seven can be admitted as exact mathematical or implementation statements under their definitions. The self-rewriting edge is a framework proposal.

## 23.3 Tier C - external calibration claims

The Hara and Redondo results should enter as source-local claims with exact numerical and scope boundaries. They should not be used to validate SPPT or ASTRA globally. Every sentence should identify whether it is an observation, authors' interpretation, or ASTRA structural inference.

## 23.4 Tier D - proposed scientific applications

Planetary, origin-of-life, biological, dark-matter, and cosmological applications remain `proposed_only` until a domain-specific model and data test exist. The project should not promote them because the methods are coherent or visually compelling.

# 24. Source, rights, and provenance policy

## 24.1 News as discovery lead

Phys.org and similar reports are discovery leads. The current update follows the repository's production rule: technical claims are grounded in primary papers or stable official records. The news pages are not copied into the package, and their images are not reused.

## 24.2 Redrawn figures

The ORR comparison chart is an original redraw of three reported numbers. It is not a reproduction of the paper's graphical abstract or figures. The nonreciprocal and catalyst schematics are original models and are labeled accordingly.

## 24.3 AI assistance and responsibility

AI assistance may organize sources, draft equations, generate code, and perform adversarial review. It is not an author, rights holder, peer reviewer, or scientific validator. The human maintainer remains responsible for source selection, wording, release decisions, and any claim of originality.

Primary sources, calculations, data, and tests---not model output---supply the evidence. **Neither the dream, the collage, nor model output is scientific evidence.**

## 24.4 Repository identity

A release document must record:

- base commit and tree;
- exact admitted file hashes;
- source versions and retrieval date;
- generated output hashes;
- build environment and dependencies;
- author and license map;
- whether any file is inherited from an immutable release;
- whether the release change alters a retained core claim.

The v1.0.7 edition does not reuse the v1.0.6 release identity or manifest. It has its own tag, assets, source archive, identity JSON, and remote read-back verification.

# 25. Fail-closed promotion gates

![**[MODEL]** Promotion gates used for the v1.0.7 release and retained for future corrections. Passing the gates establishes artifact and scope integrity, not peer review or empirical planetary validation. Creator: ASTRA / Jacko T. Source: original vector model. License: CC BY 4.0.](../figures/figure_12_promotion_gates.png){#fig:gates width=92%}

A proposed correction or successor should fail if any of the following occurs:

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

# 26. Maintenance and successor plan

## 26.1 Stage 0 - preserve v1.0.6

Do not edit or retag v1.0.6. The v1.0.7 claim matrix carries the retained claims forward under a new release identity and records every new extension separately.

## 26.2 Stage 1 - v1.0.7 integration result

The v1.0.7 integration records stateful-edge and bridge fields for:

- edge state;
- mode and active support;
- reciprocity class;
- environment exchange ledger;
- observation sectors;
- visibility operator;
- equivalence class;
- falsifier;
- evidence disposition.

The schema dialect is validated by the declared validator where the environment supplies its metaschema; an environment-limited result remains preferable to a false pass.

## 26.3 Stage 2 - future benchmark maintenance

Future maintenance should add the six proposed synthetic benchmarks with fixed seeds, exact expected outputs where possible, and omitted-generator controls. Candidate selection, family adequacy, and held-out prediction must remain separate outputs.

## 26.4 Stage 3 - completed manuscript integration

This edition rewrites the core manuscript rather than appending a loose supplement. It preserves the existing exact derivations, then adds stateful edges, closure-conditioned nonreciprocity, active support, sector completeness, visibility, and the bridge protocol in one notation system.

The Earth and human-origin material should remain a separately cited supplemental line. The main planetary paper should summarize its transferable methods without absorbing its full historical content.

## 26.5 Stage 4 - claim and source audit record

The v1.0.7 claim matrix and source ledger are generated from one frozen tree. For every new claim the release record includes:

- exact sentence or equation locator;
- source or code locator;
- hypotheses, units, domain, and quantifiers;
- evidence class;
- limitation and counterexample;
- admission disposition;
- test or reproduction command;
- output hash.

## 26.6 Stage 5 - release engineering record

The v1.0.7 release builds canonical PDF, HTML, technical supplement, source archive, checksums, and release identity. The maintenance checklist is:

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

Those gates define the maintenance standard for future v1.0.7.x corrections and any later successor; they are not a pending release instruction for this already identified v1.0.7 edition.

# 27. Consolidated research program

The next scientific work should prioritize experiments that separate mechanisms rather than expand vocabulary.

## 27.1 Active-matter program

- Reproduce the bidisperse colloid result independently.
- Measure mediator flow and environment momentum exchange.
- Map nonreciprocity across particle-size ratio, field, density, and viscosity.
- Test whether nonreciprocity survives coarse-graining.
- Develop a motif-transition and dynamic-arrest benchmark.

## 27.2 Mechanochemical catalyst program

- Separate strain from dealloying and active area.
- Measure operando surface composition and strain.
- Test long-duration stability and cycling hysteresis.
- Move from thin film to catalyst layer and membrane-electrode assembly.
- Report Pt mass activity, durability, dissolution, efficiency, and cost denominator.

## 27.3 Planetary program

- Add edge-state candidates to interior and atmosphere forward models.
- Compare fixed-edge, stateful-edge, and topology-changing baselines.
- Use transient, periodic, multi-port, and population information.
- Preserve non-identifiability and negative held-out results.
- Require equations of state and phase diagrams before promotion.

## 27.4 Cosmic visibility program

- Jointly infer source and transducer parameters.
- Use filament/void matched controls.
- Combine gamma rays, lensing, FRB dispersion, Faraday rotation, and synchrotron.
- Treat nulls as bounded veto manifolds.
- Require one parameter set to close across cosmology, astrophysics, and laboratory constraints.

## 27.5 Origins and archive program

- Apply visibility and sampling kernels to submerged landscapes, perishable technologies, and meteorite delivery.
- Design moving-front mineral experiments with fixed total energy.
- Use residue fields and archive-veto strength rather than dramatic resemblance.
- Keep natural panspermia, directed seeding, and prior-industry hypotheses in distinct ledgers.

## 27.6 Mathematical certificate program

- Maintain exact local-to-global examples.
- Treat prime reductions as observation channels with explicit lifting limits.
- Continue the two-variable Jacobian program through compactification, collision schemes, monodromy, and formal certificates.
- Do not convert mathematical analogy into simulation or holography evidence.

# 28. Conclusions

SPPT/ASTRA began with a narrow planetary claim: topology can be a hidden state. The current repository has accumulated enough disciplined successor work to justify the next conceptual step.

A graph is not fully specified by its nodes and adjacency. Its edges can contain state. They can store strain, composition, damage, adsorption, permeability, phase, or controller history. They can be active only on a moving support. Their reduced couplings can be directed because the subsystem exchanges momentum or energy with an environment. Their outputs can migrate into sectors outside a detector's basis. Their visibility can be amplified or suppressed by a cosmic, geological, biological, or instrumental operator. Their local success can fail to close globally.

The two new studies make the point concrete.

The colloidal system shows that effective nonreciprocity can sustain motion and prevent ordinary coarsening from completing. The correct lesson is not that conservation failed. It is that the particle subsystem was not closed and that directed edge weights can create a dynamically renewed graph ensemble.

The Cu3Pt system shows that a catalyst's constitutive law depends on both present mechanical strain and accumulated electrochemical history. The correct lesson is not that platinum has been commercially replaced. It is that an interface can be a self-rewriting state variable whose operation changes its future operation.

The repository's namespaced modules then supply the missing inference machinery: active support, sector completeness, visibility operators, observational quotients, dual rent, local-to-global certificates, and fail-closed bridge gates.

The resulting v1.0.7 reference edition can be stated in one sentence:

> **Model the physical graph, the state of its edges, the support on which each coupling is active, the environment that closes its ledgers, the sectors through which its outputs can be observed, and the certificate boundary beyond which the claim must stop.**

That is a real advancement. It does not solve planetary inference, identify dark matter, prove a universal active-matter law, commercialize a catalyst, or validate a hidden origin story. It makes those claims harder to state carelessly and easier to test honestly.

> **Find the edge. Measure its state. Locate its active support. Close the environment. Enumerate the observable sectors. Report the unresolved quotient. Intervene. Predict held-out data. Preserve the failure.**

**Ad Astra Per Aspera.**

\newpage

# Appendix A - Unified notation

Table: Unified notation used by the v1.0.7 reference edition.

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

# Appendix B - v1.0.7 atomic claims

The machine-readable claim ledger delivered with this manuscript contains the full records. The principal new atomic claims are summarized here.

Table: Principal v1.0.7 atomic claims and their dispositions.

| ID | Statement | Evidence class | Disposition |
|---|---|---|---|
| V107-M001 | A finite coupling matrix has unique symmetric and antisymmetric decomposition. | hand checked | admit |
| V107-M002 | The declared two-particle asymmetric-attraction model has center drift $(a_{LS}-a_{SL})r/2$. | hand checked | admit |
| V107-M003 | A nonzero reduced pair-force residual requires an environment/boundary term in the enlarged momentum ledger. | hand checked bookkeeping identity | admit with qualification |
| V107-M004 | The active-support aggregate has a multiplicative normalization gauge unless normalization is fixed. | hand checked | admit |
| V107-M005 | Observational equivalence under a protocol is an equivalence relation when equality of distributions is exact. | hand checked | admit |
| V107-M006 | The corrected POVM/channel equations replace the invalid trace-of-commutator measurement form. | hand checked | admit |
| V107-F001 | Stateful-edge syntax separates fixed topology, evolving edge state, and topology change. | proposed framework | proposed only |
| V107-F002 | Dynamic arrest should require scale saturation and nonzero turnover. | proposed operational definition | proposed only |
| V107-F003 | A self-rewriting edge contains fast reversible and slow irreversible state. | proposed framework | proposed only |
| V107-E001 | Hara et al. report persistent dynamic clusters from nonreciprocal EHD interactions in a large bidisperse colloid system. | externally published/source asserted | admit as calibration |
| V107-E002 | Redondo et al. report the stated strain-dependent ORR values and Pt-enriched surface. | externally published/source asserted | admit as calibration |
| V107-A001 | The colloid case supports a closure-conditioned reciprocity audit. | structural inference | admit with qualification |
| V107-A002 | The Cu3Pt case supports a self-rewriting mechanochemical edge audit. | structural inference | admit with qualification |
| V107-E006 | Koivurova et al. published the accelerating-wave equation and positive-time interpretation in 2023. | externally published/source asserted | admit as calibration |
| V107-A003 | The wave paper supports a temporal-interface, reference-frame, branch-selection, and global-ledger audit. | structural inference | admit with qualification |
| V107-D001 | These cases validate SPPT for a planet. | unsupported | reject |
| V107-D002 | The colloid paper establishes fundamental violation of momentum conservation. | unsupported | reject |
| V107-D003 | The Cu3Pt paper establishes commercial fuel-cell parity. | unsupported | reject |
| V107-D004 | The accelerating-wave equation experimentally proves a universal microscopic arrow of time. | unsupported | reject |

# Appendix C - Repository snapshot

Table: Repository snapshot and version boundary at the v1.0.7 reference edition.

| Item | Current status at audited main snapshot |
|---|---|
| Current core reference | SPPT/ASTRA v1.0.7 stable current edition |
| Immutable historical core | SPPT/ASTRA v1.0.6, released 2 August 2026 |
| v1.0.7 source tree | frozen at the tagged release commit and bound by the v1.0.7 manifest |
| Earth supplement | v0.3.0 supplemental working-paper release |
| Sector-complete module | v0.1.0-alpha.1 public namespaced research preview |
| Active-support audit | draft-v0.1.0 public unpromoted draft |
| Bridge protocol | draft-v0.1.0 public unpromoted executable prototype |
| Cosmic visibility | draft-v0.1.0 public unpromoted methods draft |
| Coherence-cell exploration | draft-v0.1.0 public unpromoted methods draft |
| This manuscript | v1.0.7 stable reference edition |

# Appendix D - Visual provenance

All figures in this edition are original ASTRA diagrams or original redraws. No Phys.org image, journal figure, screenshot, publisher layout, or raw third-party dataset is reproduced. Figure 7 redraws three values reported by Redondo et al.; Figure 13 is an original temporal-interface audit based on cited primary literature. Captions state the source and limitation. SVG and PNG sources are included in the release.

# Appendix E - Drafting verification scope

The delivered verification checks cover:

- manuscript source presence and hash;
- figure inventory and dimensions;
- DOCX and PDF generation;
- rendered-page visual inspection;
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
