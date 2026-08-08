# Proposed integration bridge for a future ASTRA supplemental release

**Status:** draft bridge; not applied to the immutable SPPT/ASTRA v1.0.6 core or
the *Earth Is the Instrument* v0.3.0 release. The current repository copy is a
local namespaced candidate only; no ASTRA v0.3.2 release exists.

## 1. Replace the invalid observation equation

Remove any instance of

\[
D_j=\operatorname{Tr}[O_j,\mathcal E_{\Gamma,u}(\rho)]+\epsilon_j.
\]

Insert the product form with no commutator punctuation:

\[
p(d\mid\rho,\Gamma,u)
=
\operatorname{Tr}\!\left[M_d\,\mathcal E_{\Gamma,u}(\rho)\right],
\qquad
\sum_dM_d=I.
\]

For a selected branch, insert:

\[
p(d\mid\rho)=\operatorname{Tr}[\mathcal E_d(\rho)],
\qquad
\rho_d=\mathcal E_d(\rho)/p(d\mid\rho),
\]

with \(\{\mathcal E_d\}\) a completely positive trace-nonincreasing quantum instrument whose sum is trace preserving.

Add the guardrail:

> Counts, intensities, line centers, voltages, force estimates, and continuous reconstructions require their own units and likelihoods. Additive noise is not a universal observation model.

## 2. Add a new method subsection: Sector-Complete Instrument Criterion

### Proposed text

A physical quantity can remain present or causally effective while changing carrier, locality, or observable sector. ASTRA therefore distinguishes the state transformation from the detector basis.

Let \(\mathcal K\) be a declared generator set and \(\pi\) an observation protocol. Define

\[
K_i\sim_\pi K_j
\Longleftrightarrow
P(D\mid K_i,\pi)=P(D\mid K_j,\pi).
\]

The protocol certifies only \(\mathcal K/\!\sim_\pi\). A sector-complete audit must enumerate the plausible output sectors under the candidate set, assign each a measurement or bound, include detector response and cross-talk, report unresolved equivalence classes, and retain an out-of-set goodness-of-fit test. “Sector-complete” does not mean measuring every imaginable sector and does not guarantee a unique generator.

Required fields:

- input and output carriers;
- input and output sectors;
- selection and conditioning;
- interface state or Hilbert space;
- active control route;
- detector observable basis;
- calibration and units;
- conservation/exchange ledger;
- unresolved-sector bounds;
- model-mediated inversion;
- Fisher rank or another identifiability audit;
- predeclared rejection test.

## 3. Add conservation wording

Replace unqualified “information is conserved” language with a quantity-specific ledger:

\[
\Delta\langle Q\rangle_{\rm bulk}
+
\Delta\langle Q\rangle_{\rm interface}
+
\Delta\langle Q\rangle_{\rm controller/environment}
-
\Phi_Q
=R_Q.
\]

Probability normalization, energy, charge, entropy, and accessible information must be stated separately.

## 4. Add identifiability language

Insert:

\[
F_{ab}
=
\mathbb E[\partial_a\log p(D\mid\theta)\partial_b\log p(D\mid\theta)].
\]

A Fisher null direction identifies a locally unidentifiable parameter combination under the declared model. Mutual information is permitted as a frozen design diagnostic, but it is prior- and model-dependent and is not itself a certificate.

## 5. Add a benchmark section

Reference the local package `ASTRA_Sector_Complete_Instrument_Module_v0.1.0-alpha.1` and state:

- local observables identify the exact equivalence class `{absorb, string_transmit}`;
- the expanded synthetic basis resolves all four frozen generators;
- local Fisher rank is 2 and expanded rank is 3;
- the model includes broken-duality, detector-noise, finite-boundary, and out-of-set controls;
- the out-of-set diagnostic selects the best of four pure candidates before
  computing a conservative selection-adjusted upper bound; it is not a raw
  unadjusted p-value or universal goodness-of-fit guarantee;
- results are synthetic methods evidence only.

## 6. Add dark-matter firewall

Insert:

> A wrong-observable calibration case is not evidence for a hidden-sector ontology. A dark-matter bridge remains `proposed_only` until it specifies an interaction Hamiltonian or effective operator, state/distribution, mediator and coupling normalization, abundance history, coherence scale, detector response, nuisance model, multi-sector predictions, preregistration, and a falsifiable null region.

For levitated-magnet literature, keep three records typed separately:

- Amaral et al., a published narrow-band (B-L) ultralight-dark-matter null
  search and upper limit (DOI 10.1103/PhysRevLett.134.251001);
- Ji et al., a room-temperature LeMaMa field-sensitivity result (arXiv:2504.21524)
  with no dark-matter signal or limit;
- Tian et al., an APS accepted record for model-dependent spin--spin--velocity
  bounds (DOI 10.1103/35c1-ylnx), not yet treated as version-of-record verified.

None of these records supplies a planetary transport edge, latent-heat term, or
dark-matter identity. A future adapter must preserve force-versus-field units,
confidence semantics, calibration, nuisance controls, and the exact searched
mass/coupling domain.

## 7. Add acceptance gates

The framework fails the sector-complete audit if:

- the detector basis is left implicit;
- postselection is reported without its denominator;
- a local null is inflated into global absence despite an unresolved sector equivalence;
- “information conservation” is asserted without naming the quantity and enlarged boundary;
- a hidden sector is added after failure without a prospective observable;
- candidate-set completeness is assumed because one expanded model fits;
- a dark-matter identity claim is promoted by analogy alone.

## 8. Add public failure records

Record:

- rejected trace-of-commutator observation equation;
- exact local absorb/string equivalence in the frozen benchmark;
- conditions under which broken matching restores reflection;
- detector-noise degradation of discrimination;
- rejection of the out-of-set hybrid by the pure candidate set.
