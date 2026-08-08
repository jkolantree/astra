---
title: "ASTRA Sector-Complete Instrument Module"
subtitle: "Typed Quantum Transduction, Observable Closure, Identifiability, and a Frozen Four-Generator Benchmark"
author: "ASTRA Coherence Cell / Jacko T."
date: "7 August 2026"
version: "v0.1.0-alpha.1"
status: "Local research preview - synthetic methods only - not peer reviewed"
lang: en-US
geometry: margin=0.8in
fontsize: 11pt
colorlinks: true
linkcolor: blue
urlcolor: blue
toc: true
toc-depth: 3
header-includes:
  - |
    \usepackage{booktabs}
  - |
    \usepackage{longtable}
  - |
    \usepackage{microtype}
  - |
    \usepackage{float}
  - |
    \usepackage{caption}
  - |
    \captionsetup{font=small,labelfont=bf}
  - |
    \usepackage{xcolor}
  - |
    \definecolor{astranavy}{HTML}{0B1F2A}
  - |
    \definecolor{astragold}{HTML}{B89A2D}
---

# Document status

This document is the first local implementation milestone for a proposed ASTRA **sector-complete instrument** module. It responds directly to the supplied read-only methods audit and preserves its strongest correction: the prior observation equation was mathematically invalid because it used the trace of a commutator.

The companion methods input was supplied as a local text artifact with SHA-256

`0DC731EAAC8FFADFD9105AFD7AC944A5A98274D8B26462547343BC16D30C3675`.

That hash was independently recomputed from the attached text. The attached implementation archive was also independently hashed as `B0B9606B3C64C91C97A92E18E4E4A5BDB7519ED4D15664A33F864E420F32C1B6`. No repository, publication, tag, release, GitHub, Zenodo, or DOI action was taken. The package is a namespaced local research preview; it does not create an ASTRA v0.3.2 release or modify the immutable v1.0.6/v0.3.0 lines.

The benchmark in this package is entirely synthetic. It does **not** validate a real duality defect, a topological hidden sector, dark matter, mirror matter, or any physical ontology. It tests one narrow inference principle:

> A detector restricted to local observables can correctly report a null while leaving two physically different generators observationally equivalent. Expanding the declared observable basis can resolve that equivalence when the missing sectors are correctly specified.

# Abstract

ASTRA currently distinguishes physical evolution, boundary state, control, observation, archive, and certificate. The quantum-transduction reports considered in the supplied audit require a sharper treatment of carrier migration and observable incompleteness. This module corrects the measurement formalism, defines a typed transduction schema, gives a bounded definition of sector completeness, and implements a frozen synthetic benchmark with four candidate generators: reflection, absorption, local transmission, and string-sector transmission.

The corrected unconditioned measurement equation is

\[
p(d\mid \rho,\Gamma,u)
=
\operatorname{Tr}\!\left[M_d\,\mathcal E_{\Gamma,u}(\rho)\right],
\qquad
\sum_d M_d=I,
\]

where \(\mathcal E_{\Gamma,u}\) is completely positive and trace preserving when no branch is selected. A postselected branch is represented by a completely positive trace-nonincreasing quantum instrument, not by an additive-noise expectation equation.

In the frozen benchmark, local outcomes are left, right, and no-local-signal. Absorption and string transmission therefore produce identical local records. The exact local equivalence classes are

\[
\{\mathrm{reflect}\},\quad
\{\mathrm{absorb},\mathrm{string}\},\quad
\{\mathrm{local\ transmit}\}.
\]

A declared sector-complete measurement adds string- and environment-sector outcomes and an interface-state observable. All four benchmark generators then become singleton equivalence classes. With a 2% symmetric detector-confusion model, the local Fisher information has rank 2 while the sector-complete Fisher information has rank 3 on the three-dimensional mixture simplex. Uniform-prior mutual information rises from 1.343487 to 1.853974 bits. In 400 frozen classification replicates at 600 samples per generator, local accuracy is 0.7525 and sector-complete accuracy is 1.0. An out-of-set hybrid is decisively rejected by the four-pure-generator model, preventing apparent resolution from being mistaken for candidate-set completeness.

The module also includes broken-duality, detector-noise, finite-boundary, and model-mismatch controls; a JSON Schema; a conservation/exchange ledger; 29 local automated tests (27 supplied tests plus schema and text-output guards); frozen outputs; and a dark-matter firewall that keeps all ontological interpretations `proposed_only` until a concrete interaction and detector-response chain exists.

# Executive result

The supplied audit was correct on the blocking point. The expression

\[
D_j=\operatorname{Tr}\left[O_j,\mathcal E_{\Gamma,u}(\rho)\right]+\epsilon_j
\]

cannot serve as the intended observation equation under ordinary finite-dimensional conditions because

\[
\operatorname{Tr}[A,B]=0.
\]

The equation would reduce to its noise term. The local implementation therefore removes it entirely.

The strongest defensible ASTRA advance is not a new claim about dark matter. It is a stricter instrument criterion:

\[
\boxed{
\text{carrier}
\rightarrow
\text{sector}
\rightarrow
\text{interface/control map}
\rightarrow
\text{output sectors}
\rightarrow
\text{observable basis}
\rightarrow
\text{equivalence class}
\rightarrow
\text{rejection test}
}
\]

A protocol is not permitted to certify a generator more finely than the quotient induced by its observable basis.

![**Figure 1. [MODEL]** Sector-complete workflow. A restricted local POVM yields an explicit absorb/string equivalence. The expanded protocol resolves the frozen four-generator benchmark and then applies an out-of-set rejection test. **Limitation:** synthetic methods diagram; not evidence for a real topological sector. Creator: ASTRA Coherence Cell / Jacko T. Source: original diagram for this module. License: CC BY 4.0.](../figures/figure_00_sector_complete_workflow.png){width=100%}

# 1. Source map and evidential boundary

The supplied source audit distinguishes four primary cases and three adjacent metrology records. This milestone preserves those distinctions and does not upgrade any paper beyond the supplied record.

| Case | Primary record cited in supplied audit | Safe ASTRA use | Current milestone status |
|---|---|---|---|
| Sunlight-pumped SPDC | arXiv:2602.15655 | Degree-of-freedom selection and nonlinear transduction | Source map carried forward; experiment not reproduced |
| Duality defects | arXiv:2510.26780 | Sector conversion and observable incompleteness in specified models | Source map carried forward; no real defect simulated |
| Clavina | arXiv:2602.06544 | Routing and controller state are part of the physical system | Source map carried forward; hardware not reproduced |
| Fermium-255 | arXiv:2511.20921 | Proxy measurement and uncertainty propagation | Source map carried forward; spectra not reanalyzed |
| Levitated-magnet null search | arXiv:2409.03814 | Model-specific null-result record | Kept separate from dark-matter detection claims |
| Room-temperature magnetometry | arXiv:2504.21524 | Metrology record | Kept separate from dark-matter signal claims |
| Spin-spin-velocity bounds | APS accepted record 35c1-ylnx | Model-dependent interaction bounds | Kept separate from particle identification |

The four central reports support four observational-failure modes:

1. **Degree-of-freedom blindness:** a source is labeled globally incoherent although the relevant degree of freedom can be selected and controlled.
2. **Sector blindness:** a local observable is monitored after the excitation has moved into a specified nonlocal, collective, or interface-supported sector.
3. **Architecture blindness:** hardware is listed while route, timing, feedforward, controller history, and loop occupancy are omitted.
4. **Proxy blindness:** a hidden state is treated as inaccessible even though a calibrated outer system carries its signature.

These are methodological bridges. They are not evidence that the four systems share one hidden mechanism.

# 2. Corrected measurement formalism

## 2.1 Unconditioned channel and POVM

Let \(\rho\) be the input density operator, \(\Gamma\) the interface specification, and \(u\) the active control route. For an unconditioned experiment, the physical transformation is represented by a completely positive trace-preserving map

\[
\mathcal E_{\Gamma,u}:\rho\mapsto \rho_{\mathrm{out}}.
\]

A detector with outcomes \(d\) is represented by a positive-operator-valued measure \(\{M_d\}\):

\[
M_d\succeq0,
\qquad
\sum_d M_d=I.
\]

The observation law is

\[
\boxed{
p(d\mid\rho,\Gamma,u)
=
\operatorname{Tr}\!\left[M_d\mathcal E_{\Gamma,u}(\rho)\right].
}
\]

An expectation value is

\[
\langle O_j\rangle
=
\operatorname{Tr}\!\left[O_j\mathcal E_{\Gamma,u}(\rho)\right].
\]

The product is essential. A commutator belongs in dynamical or response equations when physically justified; its trace is not a generic detector signal.

## 2.2 Selected branches and quantum instruments

If outcome \(d\) selects a physical branch, use a quantum instrument \(\{\mathcal E_d\}\), where every \(\mathcal E_d\) is completely positive and trace nonincreasing and

\[
\sum_d\mathcal E_d
\]

is trace preserving. Then

\[
p(d\mid\rho)=\operatorname{Tr}[\mathcal E_d(\rho)],
\]

and, when \(p(d\mid\rho)>0\),

\[
\rho_d
=
\frac{\mathcal E_d(\rho)}{p(d\mid\rho)}.
\]

This distinction matters for heralding, filtering, postselection, discarded trials, and selected optical branches. An apparent performance number without the branch probability and denominator leaves system-boundary fog.

## 2.3 Counts, intensities, and continuous estimates

There is no universal additive \(\epsilon_j\) model. The likelihood must match the reported quantity.

For categorical counts,

\[
(n_1,\ldots,n_m)
\sim
\operatorname{Multinomial}(N,p_1,\ldots,p_m).
\]

For photon counts, a Poisson or overdispersed count model may be appropriate. For voltages, force estimates, frequencies, line centers, or tomography parameters, use a likelihood with declared units, calibration, covariance, censoring, drift, and nuisance parameters.

The ASTRA record must therefore state not only the observable but also the data type and units.

# 3. Typed transduction schema

The proposed module represents a transduction claim as

\[
\mathcal T
=
(\rho_{\mathrm{in}},s_{\mathrm{in}},\Gamma,b_\Gamma,u,
\mathcal E,\mathcal S_{\mathrm{out}},\mathcal M,\mathcal C,\mathcal I,\mathcal R),
\]

where:

- \(\rho_{\mathrm{in}}\): input physical state;
- \(s_{\mathrm{in}}\): input carrier/sector label;
- \(\Gamma\): interface identity and geometry;
- \(b_\Gamma\): interface state or Hilbert-space contribution;
- \(u\): routing, timing, feedforward, and control history;
- \(\mathcal E\): channel or instrument;
- \(\mathcal S_{\mathrm{out}}\): plausible output sectors;
- \(\mathcal M\): observable basis and detector model;
- \(\mathcal C\): calibration, units, and exchange ledger;
- \(\mathcal I\): identifiability result;
- \(\mathcal R\): rejection or demotion test.

The machine-readable schema requires the following fields:

1. input carrier;
2. input sector;
3. output carriers;
4. output sectors;
5. selection and conditioning;
6. interface state or Hilbert space;
7. active control route;
8. observable basis;
9. calibration and units;
10. conservation/exchange ledger;
11. unresolved-sector bounds;
12. model-mediated inversion;
13. identifiability quotient and null directions;
14. predeclared rejection test;
15. interpretation status.

The schema is designed to extend ASTRA-Layers rather than create one generic arrow. Physical transport, interface-state change, control, observation, and certificate remain separate typed relations.

# 4. What sector-complete means

“Sector-complete” must not mean measuring every mathematically imaginable state. That is impossible and would make the term useless.

Let \(\mathcal K=\{K_1,\ldots,K_m\}\) be the declared candidate generators and \(\pi\) the measurement protocol. Define

\[
K_i\sim_\pi K_j
\quad\Longleftrightarrow\quad
P(D\mid K_i,\pi)=P(D\mid K_j,\pi).
\]

For noisy or finite data, exact equality can be replaced by a declared operational threshold based on total variation, likelihood ratio, Bayes factor, expected error, or another calibrated separation criterion.

The protocol certifies only the quotient

\[
\mathcal K/\!\sim_\pi.
\]

A protocol is **sector-complete relative to a declared candidate set** when:

1. the plausible output sectors for those candidates are enumerated;
2. every listed sector has a measurement or a quantitative bound;
3. detector response and cross-talk are included;
4. remaining equivalence classes are reported explicitly;
5. the claim is no more specific than those classes;
6. an out-of-set goodness-of-fit or model-discrepancy test is retained.

This definition allows a sector-complete audit to conclude that two generators remain equivalent. Completeness refers to honest closure of the declared sector ledger, not guaranteed uniqueness.

# 5. Identifiability and information diagnostics

## 5.1 Fisher information

For parameters \(\theta\) and likelihood \(p(D\mid\theta)\), the Fisher information is

\[
F_{ab}
=
\mathbb E\!\left[
\partial_a\log p(D\mid\theta)
\partial_b\log p(D\mid\theta)
\right].
\]

A null direction identifies a local parameter combination that the declared protocol cannot estimate. Fisher rank is local and model dependent. It does not establish global uniqueness, candidate-set completeness, or physical truth.

## 5.2 Mutual information

For candidate generator \(K\) and data \(D\),

\[
I(K;D)
=
\sum_{k,d}p(k,d)
\log_2\frac{p(k,d)}{p(k)p(d)}.
\]

Mutual information is useful for comparing frozen protocols under a declared prior. It is not itself a certificate because it changes with the prior, candidate set, likelihood, and nuisance model.

## 5.3 Pairwise distinguishability

For two candidate response distributions, this benchmark also records total variation:

\[
\operatorname{TV}(P_i,P_j)
=
\frac12\sum_d|P_i(d)-P_j(d)|.
\]

A zero distance means exact observational equivalence for the declared protocol. A nonzero value does not automatically imply practical discrimination at finite sample size.

# 6. Conservation and exchange ledger

Probability normalization, energy, charge, entropy, and accessible information are different quantities. The module therefore forbids a generic statement that “information is conserved” unless the system boundary and quantity are defined.

For each declared quantity \(Q\), use an enlarged-system ledger of the form

\[
\Delta\langle Q\rangle_{\mathrm{bulk}}
+
\Delta\langle Q\rangle_{\mathrm{interface}}
+
\Delta\langle Q\rangle_{\mathrm{controller/environment}}
-
\Phi_Q
=
R_Q,
\]

where \(\Phi_Q\) is declared flux through the outer boundary and \(R_Q\) is the closure residual.

In the frozen benchmark:

- density-matrix trace is one;
- one global excitation is preserved in the enlarged basis;
- the defect occupation changes only for string transmission;
- energy is not modeled;
- charge is not modeled;
- subsystem entropy is not asserted to be conserved;
- accessible information changes with the observable basis.

That is a deliberately narrow ledger. It prevents the model from claiming conservation laws it does not implement.

# 7. Frozen synthetic benchmark

## 7.1 Enlarged basis

The benchmark uses a ten-dimensional computational basis:

\[
\begin{aligned}
&|\mathrm{vac},d0\rangle,
|L,d0\rangle,
|R,d0\rangle,
|S,d0\rangle,
|E,d0\rangle,\\
&|\mathrm{vac},d1\rangle,
|L,d1\rangle,
|R,d1\rangle,
|S,d1\rangle,
|E,d1\rangle.
\end{aligned}
\]

Here \(L\) and \(R\) are local sectors, \(S\) is a string-labelled sector, \(E\) is an environment/absorption sector, and \(d0,d1\) are binary interface-state labels. These names are synthetic bookkeeping. They are not asserted to reproduce the Hilbert space of a physical duality defect.

The input is

\[
\rho_{\mathrm{in}}
=|L,d0\rangle\langle L,d0|.
\]

## 7.2 Four generators

The four ideal global transformations are represented by permutation unitaries on the enlarged basis:

\[
\begin{aligned}
K_R &: |L,d0\rangle\mapsto|L,d0\rangle,\\
K_A &: |L,d0\rangle\mapsto|E,d0\rangle,\\
K_T &: |L,d0\rangle\mapsto|R,d0\rangle,\\
K_S &: |L,d0\rangle\mapsto|S,d1\rangle.
\end{aligned}
\]

Absorption is globally unitary only because the environment-labelled sector is inside the model boundary. A reduced local subsystem would see a nonunitary loss channel.

![**Figure 2. [MODEL]** The frozen four-generator state flow. Absorption and string transmission produce the same local null even though the enlarged states differ. **Limitation:** synthetic basis and generator maps; not a physical duality-defect Hamiltonian. Creator: ASTRA Coherence Cell / Jacko T. Source: original diagram. License: CC BY 4.0.](../figures/figure_09_four_generator_state_flow.png){width=92%}

## 7.3 Local measurement

The local POVM has three outcomes:

\[
M_L=P_L,
\qquad
M_R=P_R,
\qquad
M_0=I-P_L-P_R.
\]

Absorption and string transmission both yield \(M_0\) with probability one before detector noise. The local detector therefore cannot distinguish them, regardless of exposure.

![**Figure 3. [MODEL]** Noisy local response matrix with 2% symmetric outcome confusion. Absorption and string transmission remain identical columns. **Limitation:** frozen detector-noise model; not a general detector law. Creator: ASTRA Coherence Cell / Jacko T. Source: benchmark output. License: CC BY 4.0.](../figures/figure_01_local_response_matrix.png){width=82%}

## 7.4 Sector-complete measurement

The expanded POVM adds string and environment outcomes:

\[
\{P_L,P_R,P_S,P_E,I-P_L-P_R-P_S-P_E\}.
\]

The defect occupation is recorded as a separate commuting diagnostic. Under the frozen ideal generators, every response column is distinct.

![**Figure 4. [MODEL]** Noisy sector-complete response matrix with the same 2% confusion model. The four generator columns are distinct. **Limitation:** resolution follows from the declared synthetic basis; it does not validate real string or environment detectors. Creator: ASTRA Coherence Cell / Jacko T. Source: benchmark output. License: CC BY 4.0.](../figures/figure_02_sector_complete_response_matrix.png){width=82%}

# 8. Benchmark results

## 8.1 Equivalence classes

The exact ideal local classes are

\[
\{K_R\},\quad
\{K_A,K_S\},\quad
\{K_T\}.
\]

The sector-complete classes are

\[
\{K_R\},\quad
\{K_A\},\quad
\{K_T\},\quad
\{K_S\}.
\]

The correct local conclusion is not “the excitation disappeared.” It is:

> The local record is compatible with at least absorption and string-sector transmission under the declared candidate set.

## 8.2 Fisher-rank result

Using a uniform interior mixture and 1,000 nominal samples, the frozen local Fisher eigenvalues are

\[
0,
\quad3726.3366,
\quad7527.9528.
\]

The sector-complete eigenvalues are

\[
3821.6080,
\quad3821.6080,
\quad15286.4322.
\]

The zero local eigenvalue is the absorb-versus-string mixture direction.

![**Figure 5. [MODEL]** Fisher eigenvalues for local and sector-complete protocols. The local zero eigenvalue is an exact identifiability failure under the frozen model. **Limitation:** Fisher information is local and candidate-model dependent. Creator: ASTRA Coherence Cell / Jacko T. Source: benchmark output. License: CC BY 4.0.](../figures/figure_03_fisher_eigenvalues.png){width=78%}

## 8.3 Mutual-information result

With a uniform prior over the four generators:

| Protocol | Ideal \(I(K;D)\) | With 2% detector confusion |
|---|---:|---:|
| Local | 1.500000 bits | 1.343487 bits |
| Sector-complete | 2.000000 bits | 1.853974 bits |

The complete protocol pays positive epistemic rent in this benchmark. The result is a frozen design diagnostic, not a universal certificate.

![**Figure 6. [MODEL]** Mutual information versus symmetric detector error. Both protocols lose information as noise grows; the expanded basis retains more discrimination across the declared range. **Limitation:** uniform prior and symmetric confusion are modeling choices. Creator: ASTRA Coherence Cell / Jacko T. Source: benchmark output. License: CC BY 4.0.](../figures/figure_04_information_vs_detector_noise.png){width=78%}

## 8.4 Finite-sample classification

The frozen simulation uses 600 samples per true generator and 400 replicates. Ties under the local absorb/string equivalence are broken randomly.

- Local accuracy: **0.7525**.
- Sector-complete accuracy: **1.0000**.

The local result is not a failure of the classifier. It is the expected ceiling imposed by the observation quotient.

![**Figure 7. [MODEL]** Local classification confusion. Absorb and string transmission split approximately evenly because their likelihoods are identical. **Limitation:** frozen seed, sample size, pure candidates, and symmetric noise. Creator: ASTRA Coherence Cell / Jacko T. Source: benchmark output. License: CC BY 4.0.](../figures/figure_07_local_classification_confusion.png){width=72%}

![**Figure 8. [MODEL]** Sector-complete classification confusion. The synthetic generators are perfectly classified under the frozen conditions. **Limitation:** favorable closed candidate set; not a general error-rate estimate. Creator: ASTRA Coherence Cell / Jacko T. Source: benchmark output. License: CC BY 4.0.](../figures/figure_08_sector_complete_classification_confusion.png){width=72%}

# 9. Required controls

## 9.1 Broken-duality control

The benchmark represents imperfect matching as a random-unitary mixture:

\[
\mathcal E_{\delta}
=
(1-\delta)\mathcal U_S
+
\delta\mathcal U_R.
\]

Increasing \(\delta\) restores reflection. This is not derived from the duality-defect paper; it is a falsification control showing that the ideal no-reflection result should disappear when the matching condition is deliberately broken.

![**Figure 9. [MODEL]** Broken-matching control. Reflection rises linearly as the declared reflected admixture increases. **Limitation:** random-unitary toy closure, not a physical defect law. Creator: ASTRA Coherence Cell / Jacko T. Source: benchmark output. License: CC BY 4.0.](../figures/figure_06_broken_duality_control.png){width=78%}

## 9.2 Finite-boundary control

The toy finite-boundary closure assumes

\[
s(L)=1-e^{-L/\xi},
\]

with unresolved weight deposited in the environment sector. As \(L/\xi\) grows, the response approaches ideal string transmission. Local observations remain unable to distinguish the mixture from absorption when both produce no local signal.

![**Figure 10. [MODEL]** Finite-boundary control. String-sector weight and total-variation distance from pure absorption approach one with increasing \(L/\xi\). **Limitation:** synthetic exponential closure; no real finite-size scaling is claimed. Creator: ASTRA Coherence Cell / Jacko T. Source: benchmark output. License: CC BY 4.0.](../figures/figure_05_finite_boundary_control.png){width=78%}

## 9.3 Detector-noise control

The frozen detector model is a symmetric column-stochastic confusion matrix. It is intentionally simple. A real implementation must include efficiency, loss, false positives, time dependence, correlated noise, drift, thresholding, and calibration uncertainty.

The important audit rule is:

> Observable closure must be evaluated after the detector response, not only in the ideal Hilbert-space basis.

## 9.4 Out-of-set model mismatch

A closed candidate set can produce confident but false classification. The benchmark therefore generates a hybrid response with weights

\[
(0.10,0.20,0.25,0.45)
\]

in generator order \((K_R,K_A,K_T,K_S)\), then compares it with the four pure candidates. The best pure candidate is string transmission, but the multinomial deviance is 16828.035 with four degrees of freedom. The nominal chi-square tail is below floating-point resolution. Because the best of four candidates was selected before this diagnostic, the result is reported with a conservative four-candidate selection-adjusted upper bound; it rejects the declared pure candidate set under the predeclared 0.001 rule. This is a diagnostic for the frozen synthetic case, not a calibrated universal p-value.

This control is as important as the sector-complete success. It prevents “we measured more sectors” from becoming “our candidate list must be complete.”

# 10. Relation to the ASTRA framework

ASTRA’s existing complete-instrument chain is

\[
\text{source}
\rightarrow
\text{coupling}
\rightarrow
\text{state change}
\rightarrow
\text{output}
\rightarrow
\text{residue}
\rightarrow
\text{prospective prediction}.
\]

The proposed sector-complete module adds a second line beneath the observation and certificate stages:

\[
\text{input carrier/sector}
\rightarrow
\text{interface/control map}
\rightarrow
\text{output carriers/sectors}
\rightarrow
\text{observable basis}
\rightarrow
\text{equivalence class}
\rightarrow
\text{rejection test}.
\]

This directly extends several existing ASTRA principles:

- **Boundary-state promotion:** the interface receives explicit state when it stores or transforms predictive information.
- **Dual rent:** a seam may change physical futures, identifiability, or both.
- **FOG discipline:** observation and system-boundary fog are audited by the sector ledger.
- **Bounded nulls:** a null constrains only the generators and sectors to which the protocol is sensitive.
- **Public failure memory:** broken matching and out-of-set rejection remain visible.
- **Local-to-global certificates:** a local null cannot certify global absence when the state space was not closed.

The earlier ASTRA synthetic reservoir work demonstrated that identical static boundary equilibria can conceal different internal graphs and that richer forcing can improve topology recovery. This module addresses a different failure mode: more local data do not help when the relevant distinction lies in an unmeasured sector. The correction is a changed observable basis, not merely a longer time series.

# 11. Dark-matter firewall

The valid bridge to dark matter is methodological, not ontological.

A hidden-sector proposal must specify an interaction such as

\[
H_{\mathrm{int}}
=
\sum_a g_a O_a^{\mathrm{SM}}\otimes O_a^\chi,
\]

and must then declare:

- the dark-sector state or phase-space distribution;
- mediator and coupling normalization;
- production and abundance assumptions;
- mass range and coherence time;
- detector response function;
- background and nuisance model;
- predicted signals in more than one observable sector;
- a blind or preregistered analysis;
- a falsifiable null region.

Without those items, “the detector used the wrong observable” is only a possibility. It is not an explanation.

## 11.1 Levitated-magnet bridge: observation and certificate only

Three magnet-related primary records are kept separate because they answer
different questions:

1. Amaral et al. report a superconducting-trap search with a measured force
   sensitivity near (0.2\,\mathrm{fN}/\sqrt{\mathrm{Hz}}), no anticipated signal,
   and a model-specific (B-L) upper limit over a narrow ultralight-mass band.
   This is a published null search, not particle identification or a universal
   dark-matter exclusion.
2. Ji et al. report the room-temperature LeMaMa metrology result, approximately
   (32\,\mathrm{fT}/\sqrt{\mathrm{Hz}}) near its stated resonance. It is a
   field-sensitivity demonstration; it reports neither a dark-matter signal nor
   a dark-matter limit.
3. Tian et al.'s APS record is explicitly an accepted paper, not yet treated
   here as a verified version of record. It reports model-dependent 95%-CL
   bounds on (V_6/V_{14}) spin--spin--velocity potentials and no positive
   exotic signal.

These results provide a useful **certificate-layer template**: a null or bound
must carry its observable, calibration, confidence convention, coupling
normalization, searched mass/range, nuisance model, and detector controls. They
do not provide a physical edge in ASTRA's SPPT transport graph. A future
dark-sector adapter remains `proposed_only` until it supplies a Hamiltonian or
effective operator, a distribution/abundance model, a detector-response map
from the operator to force or field units, multi-sector predictions, blind or
preregistered analysis, and an independently replayable null region. In
particular, force sensitivity cannot be relabeled as field sensitivity, and
neither can be relabeled as latent heat, planetary sequestration, or evidence
of a dark-matter origin.

![**Figure 11. [MODEL]** Dark-matter interpretation firewall. A methods analogy cannot be promoted into ontology without a complete interaction, abundance, response, nuisance, and rejection chain. **Limitation:** governance diagram, not a dark-matter model. Creator: ASTRA Coherence Cell / Jacko T. Source: original diagram. License: CC BY 4.0.](../figures/figure_10_dark_matter_firewall.png){width=88%}

The machine-readable template therefore fixes

`interpretation_status = proposed_only`.

No current record in this module may be promoted by analogy alone.

# 12. Specialist responsibility matrix

This module requires bounded review rather than one person certifying the entire chain.

| Perspective | Responsibility | Cannot certify alone |
|---|---|---|
| Mathematical physics | Channel, POVM, instrument, defect-sector formalism | Physical realization or detector calibration |
| Quantum information | Identifiability, Fisher rank, likelihood, tomography | Material Hamiltonian or experimental noise completeness |
| Condensed matter / tensor networks | Plausible sector and interface-state structure | Cosmological hidden-sector identity |
| Quantum optics | Degree-of-freedom selection, loss, heralding, postselection | General topological-sector claims |
| Experimental metrology | Units, response, drift, efficiency, cross-talk | Candidate ontology |
| Statistics | Equivalence classes, nuisance models, model mismatch | Physical completeness of candidates |
| Systems engineering | Routing, controller state, denominators, full boundary | Microscopic theory |
| Nuclear spectroscopy | Proxy inversion and theory covariance | Quantum-computing architecture or dark matter |
| Particle/cosmology theory | Interaction and abundance consistency | Detector evidence without response model |
| Red team | Alternative generators, broken controls, failure memory | Positive mechanism by criticism alone |
| Research software | Frozen outputs, tests, hashes, schema validation | Empirical validity of equations |

This matrix is a design responsibility map. It is not a claim that external specialists reviewed or endorsed the module.

# 13. Limitations

The benchmark is intentionally favorable and narrow.

1. The candidate set is known and contains the four ideal generators.
2. The ideal outputs are orthogonal basis states.
3. The detector confusion model is symmetric and stationary.
4. The global maps are simple permutation or random-unitary channels.
5. The finite-boundary law is a declared toy closure.
6. The broken-duality law is not derived from a microscopic Hamiltonian.
7. No coherent superposition between output sectors is inferred from data.
8. No real string/Wilson observable is implemented.
9. No finite-size many-body simulation is included.
10. No raw data from the four cited reports are reproduced.
11. Current primary-record checks cover the three magnet sources listed in Appendix D, but no raw experimental data or full likelihood replay is included; the Tian record remains accepted rather than version-of-record verified here.
12. No energy, charge, or physical entropy scale is modeled.
13. Classification uses pure candidates; real systems may require hierarchical mixtures and discrepancy processes.
14. Fisher information is evaluated at one interior point.
15. The model-mismatch test detects one declared hybrid; it is not a universal out-of-distribution guarantee.
16. Dark-matter interpretations remain proposed only.

# 14. Next implementation milestones

The next milestone should replace the favorable basis-state benchmark with a blinded suite containing:

1. coherent and incoherent partial sector conversion;
2. nonorthogonal detector responses;
3. unknown detector confusion and calibration drift;
4. candidate sets that sometimes omit the generator;
5. finite-size and boundary-condition sweeps;
6. correlated noise and missing outcomes;
7. explicit postselection and denominator accounting;
8. likelihood-free or simulation-based calibration where analytic likelihoods fail;
9. held-out protocols chosen by expected discrimination;
10. a programmable many-body demonstration of local versus string observables, if a defensible model can be implemented;
11. external replication of the source/version audit;
12. sentence-to-claim coverage before integration into ASTRA v0.3.2 or later.

The promotion gate for a real physical case should be:

\[
\boxed{
\text{specified sector map}
+
\text{calibrated detector}
+
\text{held-out prediction}
+
\text{broken-control response}
+
\text{model-mismatch survival}
}
\]

# 15. Reproducibility

From the package root (use a Python environment containing NumPy, SciPy,
Matplotlib, and pytest):

```bash
python scripts/run_sector_complete_benchmark.py
pytest -q
```

The benchmark selects the non-interactive Matplotlib `Agg` backend and writes
UTF-8 LF-normalized JSON/CSV. Re-running it twice in the same declared runtime
must produce byte-identical JSON, CSV, and checksum files; PNG/PDF rendering
bytes are not claimed deterministic across all graphics stacks.

The benchmark produces:

- `data/sector_complete_benchmark.json`;
- response-matrix CSV files;
- detector-noise, finite-boundary, and broken-duality control CSV files;
- eight benchmark plots in PNG and PDF;
- a frozen result SHA-256;
- a validated example sector-complete record;
- 27 automated tests.

Frozen result hash:

`ad7b450635e06410fe4a8e5f9227bc38f6a12eb1878fa2e1ada58cde3a65971a`

The automated test result is:

`27 passed`.

# 16. Conclusion

The strongest update is a correction in scientific grammar.

A local null is not automatically evidence of nonexistence. It may identify an equivalence class. But that possibility earns no explanatory weight until the missing sectors are specified, their observables are defined, their detector responses are calibrated, and the enlarged model survives broken controls and out-of-set rejection tests.

The ASTRA command should therefore be:

> Identify the carrier. Enumerate the plausible sectors. Model the interface and route. Measure or bound each declared sector. Report the observational quotient. Reject the candidate set when the data do not fit. Keep ontology behind the evidence.

**Ad Astra Per Aspera.**

# Appendix A. Compact field specification

| Field | Required content |
|---|---|
| `model_id` | Stable identifier and version |
| `input_carrier` | Physical carrier entering the interface |
| `input_sector` | Local, collective, topological, environmental, or other declared sector |
| `output_carriers` | All plausible carriers under the candidate set |
| `output_sectors` | All plausible output sectors under the candidate set |
| `selection_conditioning` | Filters, postselection, heralding, discarded trials, branch probabilities |
| `interface_state` | State variables or Hilbert-space contribution of the seam |
| `active_control_route` | Timing, switching, feedforward, loop occupancy, controller history |
| `observable_basis` | POVM, operators, proxy signals, and detector basis |
| `calibration_and_units` | Units, response matrix, uncertainty, drift, thresholds |
| `conservation_exchange_ledger` | Separate probability, energy, charge, entropy, and information statements |
| `unresolved_sector_bounds` | What remains unmeasured and the quantitative bound |
| `model_mediated_inversion` | Forward model and inverse procedure |
| `identifiability` | Equivalence classes, rank, null directions, practical separation |
| `rejection_test` | Prospective result that rejects or demotes the model |
| `interpretation_status` | `synthetic_methods_only`, `proposed_only`, `empirical_calibration`, or `empirical_test` |

# Appendix B. Frozen benchmark configuration

| Item | Value |
|---|---:|
| Seed | 20260807 |
| Samples per generator | 600 |
| Classification replicates | 400 |
| Symmetric detector confusion | 0.02 |
| Fisher nominal samples | 1000 |
| Model-mismatch samples | 5000 |
| Pure candidate count | 4 |
| Local outcome count | 3 |
| Sector-complete outcome count | 5 |

# Appendix C. Evidence labels

- **Established:** exact mathematical result, direct implementation result under frozen assumptions, or repeatedly measured empirical result.
- **Strong inference:** best methodological interpretation of convergent evidence; details remain revisable.
- **Plausible:** coherent with partial support.
- **Open:** not excluded and not materially favored.
- **Constrained:** possible only in narrowed forms.
- **Unsupported:** no positive evidence presently requires the claim.

The benchmark results are Established only as synthetic implementation results. They do not inherit empirical status from the cited physical papers.

# Appendix D. Primary records carried from the supplied audit

1. Sunlight-pumped SPDC: https://arxiv.org/abs/2602.15655
2. Duality defects: https://arxiv.org/abs/2510.26780
3. Clavina: https://arxiv.org/abs/2602.06544
4. Fermium-255: https://arxiv.org/abs/2511.20921
5. Levitated-magnet null search (Amaral et al.; published PRL 134, 251001,
   DOI 10.1103/PhysRevLett.134.251001): https://arxiv.org/abs/2409.03814
6. Room-temperature magnetometry (Ji et al.; arXiv preprint):
   https://arxiv.org/abs/2504.21524
7. Spin--spin--velocity bounds (Tian et al.; APS accepted record, DOI
   10.1103/35c1-ylnx): https://journals.aps.org/prl/accepted/10.1103/35c1-ylnx

The record metadata and abstracts were checked against the linked primary
records on 2026-08-07. This is source-level verification only: no raw data,
instrument calibration, or experiment was independently reproduced. The
LeMaMa and Amaral records remain separate; neither supplies evidence for the
other's units or dark-matter status.
