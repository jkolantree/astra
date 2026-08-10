# Mode-resolved active-support audit

## 1. Executive conclusion

The three reports in the supplied synthesis do not reveal a common hidden
force. They do, however, expose a recurring experimental-design problem:
nominal input is often too coarse to identify the support through which a
mode-specific response is generated.

In the flying-focus accelerator, the useful control is a spatiotemporal
trajectory that keeps a wake phase matched to trapped electrons. In the bird
study, the behavioral output changes between radiofrequency waveforms that
share a carrier scale and nominal peak-field description, while the receptor
and causal pathway remain unresolved. In the silver/perovskite summary, the
reported oxygen-reduction and oxygen-evolution trends are associated with
different geometric measures in opposite operating directions, but the exact
primary record is not yet resolved here.

The conservative ASTRA contribution is therefore an audit layer:

    source -> waveform or control -> active support -> local state change
           -> system output -> residue -> prediction

The words "active support" mean a declared candidate region, time interval,
frequency band, trajectory, interface measure, or other operational support
for a particular mode. They do not mean a new field, a universal coupling, a
new material reservoir, or a discovered dark-matter sector.

This note is a local, unpromoted methods draft. It is not a peer-reviewed
paper, an empirical validation of SPPT, or an extension of the stable
SPPT/ASTRA v1.0.7 claim matrix. Its frozen audit baseline is the immutable
SPPT/ASTRA v1.0.6 release.

## 2. What was audited

The audit used four evidence layers.

1. The supplied synthesis was hashed and treated as a user input and
   provenance record.
2. The flying-focus Nature Physics version of record was checked directly.
3. The bird paper's DOI identity and consulted author-copy text were checked,
   and an independent arXiv preprint was used as a negative-control source for
   one induction architecture.
4. The SNU research-achievement URL was retained as a source lead, but the
   exact primary article, authors, DOI, version, and rights were not resolved.

The project repository was inspected at the fixed base commit recorded in
draft_metadata.json. Existing SPPT claims were read as the baseline, not
silently reinterpreted as evidence for the new cases.

The primary records are:

- Arrowsmith et al., "Dephasingless laser wakefield acceleration of electrons
  using a flying focus", Nature Physics (2026),
  https://www.nature.com/articles/s41567-026-03352-x
- Kavokin et al., "Disruption of magnetic orientation in migratory songbirds
  by radiofrequency magnetic fields is mediated by a specialized sensory
  system", Journal of the Royal Society Interface, DOI
  https://doi.org/10.1098/rsif.2026.0129
- Kattnig, "Signals too small to sense: Physical and information-theoretic
  limits to induction-based magnetoreception in birds", arXiv:2602.23485,
  https://arxiv.org/abs/2602.23485
- The unresolved SNU lead supplied in source_ledger.csv; it is not treated as
  a verified primary citation.

## 3. Evidence taxonomy

Every statement in this note is intended to carry one of the following
statuses.

- observed: directly present in a cited record or supplied file;
- externally_published: a result reported by an identifiable external record;
- hand_checked: an algebraic, dimensional, or boundary check performed on a
  declared statement;
- independently_reproduced: a result reproduced from disclosed inputs without
  relying on a saved transcript;
- mechanically_replayed: a deterministic project test or generator replay;
- structural_inference: a cross-case comparison that preserves domain
  differences;
- proposed_only: a notation, experiment, or prediction awaiting data;
- deferred: blocked by unresolved source, rights, units, or controls;
- rejected: a tempting interpretation ruled out by the present evidence.

The source and claim ledgers use the repository's existing evidence classes
where possible. "Externally published" describes the status of the source
record, not independent validation of ASTRA. Numerical agreement is not proof;
an article's future projection is not an achieved result; and a behavioral
output is not receptor identification.

## 4. Placement in ASTRA and SPPT

SPPT represents a physical system as a continuous state coupled to a directed
phase-reservoir graph. Nodes store declared quantities and edges carry declared
physical processes. ASTRA is the inference, admissibility, calibration, and
held-out-promotion layer around candidate graphs.

The active-support draft lives beside that core for four reasons.

1. The cases are not planetary phase-reservoir experiments.
2. The proposed notation is an interface for describing modes and support, not
   a replacement for SPPT's conserved inventories or transport laws.
3. The supplied SNU record is not yet source-complete.
4. Folding the analogy into the core claim matrix would make a structural
   comparison look like a new empirical result.

The correct relationship is:

    SPPT physical state and flux graph
                 |
                 v
    ASTRA inference and promotion rules
                 |
                 +--> optional mode/support audit (this draft)
                 |
                 +--> optional observation/archive/certificate records

An observation or certificate may inform ASTRA inference, but it cannot become
a physical matter-or-energy edge merely because it is predictive, useful, or
semantically related.

## 5. Baseline SPPT state and what may vary

Let a baseline SPPT candidate be

    M = (x, G, theta, u, b_Gamma, O, C).

Here x is the continuous state, G is the directed physical topology, theta is
the parameter vector, u is the declared control or forcing, b_Gamma is the
boundary state, O is the observation operator, and C is the admissibility and
calibration context. The exact components and units depend on the chosen
forward model.

The core theory admits several kinds of variation, but they are not
interchangeable.

### 5.1 Parameter variation

The topology G and state meaning stay fixed while theta changes. Examples
include capacities, conductances, release times, radiation coefficients,
wetting factors, and source amplitudes. A parameter scan does not demonstrate
topology recovery.

### 5.2 Forcing variation

The physical graph stays fixed while u(t), u(r,t), or a boundary schedule
changes. The periodic-trap result shows why forcing frequency and release time
must be kept dimensionally explicit. A new waveform can identify a response
surface without proving a new edge.

### 5.3 Boundary-condition variation

The graph and parameters stay fixed while boundary inputs, sinks, ports, or
radiation laws change. Static boundary observations can remain non-identifying
when hidden conductances differ. Boundary changes must not be described as
topology changes unless a physical connection itself is changed.

### 5.4 Topology variation

The edge set, node set, or guard state changes under a declared hybrid rule.
The existing SPPT syntax offers a proposed guard/reset language. It does not
yet provide a general existence, uniqueness, reset-map closure, simultaneous
guard, or non-Zeno theorem.

### 5.5 Observation variation

The physical graph is fixed while O changes: a second port, a different
frequency, a new sensor, or a controlled intervention may separate transfer
equivalence classes. Observation variation is not a physical transport edge.

### 5.6 Mode variation

The physical system is operated under a different task, direction, waveform,
or controller. A mode may change which region or interface contributes to a
response without changing the underlying material graph. This is the entry
point for the active-support draft.

## 6. Proposed mode-resolved interface

For a mode mu and control protocol u, define a bookkeeping record

    b_Gamma_star = (b_Gamma, mu, u, A_mu,u).

The tuple records a boundary or interface state, the operating mode, the
control, and a candidate active-support descriptor A_mu,u. It does not add a
physical reservoir. A physical instantiation must state which components are
measured, which are inferred, and which are merely hypothesized.

A mode-specific response may be written schematically as

    J_mu = G_mu(x_minus, x_plus, b_Gamma, u, du/dt, grad(u), A_mu,u).

This is an interface signature, not a closed constitutive equation. To become
an SPPT edge it would need:

- a state space and units for every argument and output;
- a declared domain and boundary condition;
- a causal or phenomenological law;
- calibration parameters and uncertainty;
- admissibility and entropy conditions where relevant;
- an observation operator;
- a null model and an intervention;
- a reproducible forward calculation.

Without those items, J_mu stays in the ASTRA observation or audit layer.

## 7. Active-support kernel and measure

Let

    a_mu,u(r,t,nu)

be a dimensionless support weight with 0 <= a <= 1. It can represent a
candidate fraction of local coupling, but it is not automatically a
probability, density, or material occupancy. Let R_mu,u be a local response
density with units declared for the selected measure. A schematic aggregate
response is

    Y_mu,u =
      integral_over_Omega_r integral_over_T integral_over_Omega_nu
      a_mu,u(r,t,nu) R_mu,u(X,b_Gamma;r,t,nu)
      dnu dt dr.

The formula is useful only after the following are fixed:

- the spatial domain and coordinate convention;
- the time window and initial condition;
- the frequency or spectral measure;
- whether r is one-, two-, or three-dimensional;
- the units of R and the normalization of a;
- threshold and uncertainty rules;
- boundary and censoring treatment.

The thresholded active set is

    A_mu,u(theta) = {(r,t,nu): a_mu,u(r,t,nu) > theta}.

Changing the scale of a and R inversely leaves Y unchanged. That bookkeeping
gauge is a warning: an active set cannot be treated as a unique discovered
object without an identification convention. A future schema should record
the normalization and threshold as data, not hide them in prose.

## 8. Case study A: flying-focus laser wakefield acceleration

### 8.1 What the record establishes

The Nature Physics version of record reports a 7 mm gas-cell experiment using
21 fs, 4 J laser pulses in a hydrogen-argon mixture. Near a plasma density of
5.0 x 10^18 cm^-3, the reported maximum electron energy is 396 +/- 14 MeV,
more than twice the quoted conventional dephasing-limited energy of about
185 +40/-39 MeV. The reported charge is about 0.9 +/- 0.2 pC and the average
divergence is about 3.4 +/- 1.3 mrad.

The experiment is a direct example of spatiotemporal control. The focus
trajectory and the plasma density determine the wake velocity. When the wake
velocity approaches the electron velocity, the dephasing length can exceed
the accelerator length. The article reports a narrow density window, charge
loss at lower density, dephasing and wake perturbation at higher density, and
sensitivity to pulse duration, energy, and focus position.

The article also gives a scaling projection for approximately 100 GeV
electrons in a sub-metre stage. That projection is not a 100 GeV observation.
Beam charge, divergence, energy spread, staging, laser delivery, diagnostics,
and repeatability remain engineering and physics obligations.

### 8.2 Active-support reading

The candidate active support is the moving wake/bunch overlap in z and t,
with a spectral and density context. The most informative control is not the
total laser energy alone. It is the relation among plasma density, focal
velocity, wake phase, and bunch position.

A safe audit chain is:

    density and optical timing
      -> focal trajectory and wake velocity
      -> bunch/wake overlap
      -> acceleration and trapping
      -> energy, charge, divergence, spread
      -> shot-to-shot residuals
      -> held-out density/focal-velocity prediction

The phrase "active support moves" is literal here because the focus is
programmed in spacetime. It still does not imply that the support is a new
reservoir in SPPT.

### 8.3 Proposed tests

The next experiment should measure wake velocity independently rather than
infer it only from the final energy. It should reconstruct the bunch position
along the cell, scan density and focal velocity under a preregistered plan,
and hold out a longer stage or a density band. It should report full beam
metrics: charge, energy distribution, divergence, energy spread, efficiency,
dark current, pointing, and stability.

A useful falsifier is a matched condition with the same laser energy and
plasma inventory but deliberately mismatched focal velocity. If the proposed
overlap metric does not predict the change in stalling, dephasing, or beam
quality after nuisance controls, the active-support interpretation is weakened.

## 9. Case study B: radiofrequency disturbance of songbird orientation

### 9.1 What the record establishes

The Journal of the Royal Society Interface paper studies pied flycatchers in
Emlen funnels. The reported conditions include 1.41 or 1.5 MHz carriers,
continuous fields, and a 500 Hz square-wave modulation with 50 percent duty
cycle. Across the reported seasons, the behavioral result depends on the
combination of field amplitude, carrier, and waveform. A continuous 30 nT
condition in one 2025 series was compatible with oriented behavior, while the
modulated condition was disorienting; earlier series included 47 nT
conditions, with year-to-year differences.

"Disorientation" here means that the group direction in the funnel was not
significantly different from random under the study's analysis. It is not a
direct free-flight route measurement, and it does not by itself locate a
receptor.

The paper argues that the result is not adequately explained by a direct
cryptochrome-decoherence account. It does not refute cryptochrome's ordinary
compass role. It proposes that a separate RF disturbance detector may exist,
possibly involving induction, but that mechanism remains open.

### 9.2 Active-support reading

The candidate support is not "the bird" or "the RF field" as a single scalar.
It may involve temporal envelope, sidebands, rise and fall times, crest factor,
RMS and mean power, field orientation, phase stability, and an unknown sensory
coordinate. The biological support may be retinal, vestibular, trigeminal,
cellular, or a combination; no localization is admitted by this draft.

The Kattnig preprint is a useful guardrail. It constrains one idealized
semicircular-canal induction architecture under its stated assumptions. It
does not eliminate every induction pathway, vestibular magnetic pathway, or
cryptochrome mechanism. The correct ASTRA use is a negative-control template:
state the architecture, calculate its signal and noise, and do not generalize
the failure to an entire mechanism family.

### 9.3 Proposed tests

Use a factorial response surface varying carrier frequency, envelope
frequency, duty cycle, peak field, RMS field, mean power, rise time, phase
coherence, sideband content, and orientation. Keep the field logger inside
the enclosure and expose sham conditions to the same switching artifacts.
Blind the treatment code. Replicate across sites and seasons.

Pair the behavioral endpoint with field and acoustic monitoring, retinal and
vestibular perturbations where ethically justified, neural or receptor
localization, and a free-flight follow-up. A robust waveform-specific effect
after these controls would support a mode-dependent sensor hypothesis; it
would not identify a receptor without localization.

## 10. Case study C: silver/perovskite electrode lead

The supplied synthesis describes a thin-film perovskite electrode with
controlled metal nanoparticle arrays, comparing Ag, Co, Pd, and Pt. It
associates oxygen-reduction activity with Ag-oxide interface length and
oxygen-evolution activity with exposed Ag area, using operando synchrotron
measurements and DFT. Hydrogen is produced at the opposite fuel electrode.

Those details are not promoted as a resolved external result here. The SNU
URL, exact primary article, author list, DOI, version, complete geometry, and
rights must be checked before the case can support a released citation.

If the summary is later confirmed, its methodological value would be a
directional and geometric audit:

    fuel-cell mode       -> candidate perimeter or interface support
    electrolysis mode   -> candidate exposed-surface support

The two rows should not be collapsed into one reversible edge without measuring
mass transfer, morphology, oxidation state, poisoning, sintering, migration,
temperature, current density, and aging. A reported correlation is not a
general rule that perimeter always controls reduction or area always controls
oxidation.

The high-value experiment is mass-held-constant geometry variation. Independently
vary interface perimeter and exposed area, randomize the array layout, measure
both directions under matched conditions, and preregister the response slopes
and failure criteria.

## 11. What SPPT can vary without changing its identity

The active-support perspective is useful because it clarifies which changes
are legal SPPT variations and which would be a new theory.

### Variation A: forcing schedule

Change u(t) or a boundary waveform while retaining the same graph and
constitutive laws. Predict changes in transient, periodic, or frequency-domain
outputs. This is a standard forward-model variation.

### Variation B: release and relaxation scales

Change tau, capacities, conductances, or release laws within their declared
positive domains. The periodic-trap calculation predicts the raw and
normalized loop responses; the weak-cut result predicts a slow mode bound.

### Variation C: observation operator

Add a second port, frequency, or intervention. This can reduce an
identifiability class without changing physical transport. The static
surface-star/deep-star equivalence is a standing warning against claiming
unique topology from one boundary trace.

### Variation D: typed mode

Record a mode and control protocol alongside a boundary or observation record.
This is the proposed active-support tuple. It becomes physical only if its
response law is specified and admitted.

### Variation E: topology guard

Allow an edge or node to appear, disappear, or switch under a declared guard.
This remains a proposed hybrid syntax. A future theorem would need a state
domain, event ordering, reset map, continuation rule, and non-Zeno condition.

### Variation F: external instrument layer

Attach an observation, archive, or certificate record to an ASTRA candidate.
This can help rank models and preserve provenance. It must not be treated as a
new matter or energy edge.

### Variation G: domain-specific constitutive bridge

To add an external mode such as a laser wake, bird sensor, electrode, or
dark-matter detector to SPPT, specify the physical state, coupling, units,
boundary conditions, response, nuisance terms, and test. A structural analogy
alone is insufficient.

## 12. Prediction taxonomy

SPPT predictions should be read in three tiers.

### Tier 1: core mathematical consequences

These are already part of the v1.0.6 reference claim matrix under their stated
hypotheses.

- Internal transport cancels in the declared inventory balance.
- Positive-semidefinite phenomenological closure gives nonnegative local
  entropy production on the declared force-flux domain.
- The periodic trap has the displayed solution and loop integrals.
- At fixed forcing frequency, raw loop magnitude increases with release time;
  release-normalized loop magnitude peaks at omega*tau = 1.
- A positive-capacity, connected conductance graph has the stated weak-cut
  relaxation bound.
- The complete state-dependent derivative includes K(1-dTu/dTd).
- Heterogeneous nucleation includes the substrate wetting factor in the ideal
  spherical-cap case.
- Static boundary temperature can be independent of deep conductance under
  K>0 and injective radiation, while the hidden temperature remains
  conductance-dependent.

These are conditional mathematical results, not predictions about every
planet or every material.

### Tier 2: ASTRA model-selection predictions

These are operational rules rather than universal laws.

- Promote a topology only when it is physically admissible, calibrated, and
  predictively superior on held-out information.
- Use more ports, frequencies, interventions, or priors to break an observed
  transfer equivalence rather than assuming identifiability.
- Preserve negative results and active-bound fits; do not convert a selected
  model into a family-wide recovery claim.

The synthetic benchmark is regression evidence for this workflow. It is not
blinded, external, or empirical validation.

### Tier 3: proposed active-support predictions

These are new hypotheses in this draft, not established SPPT results.

1. Matched total input with changed support geometry or waveform should change
   output if support is causal.
2. In flying-focus acceleration, phase-velocity mismatch should reduce
   effective overlap and produce measurable stalling or beam degradation.
3. In the bird case, a factorial waveform experiment would test whether the
   response depends on sideband, duty, rise-time, RMS, or mean-power
   coordinates rather than peak field alone, under an explicitly stated
   detector hypothesis.
4. In the electrode case, interface perimeter and exposed area should have
   distinguishable response slopes under mass-held-constant geometry controls.
5. In a moving-front experiment, a dimensionless overlap coordinate can be
   tested across independent changes in front speed, interaction time, and
   interaction length.

Each item needs an operational endpoint, units, nuisance model, null control,
replication plan, and predeclared falsifier. None is promoted by the existence
of this note.

## 13. The moving-front coordinate

For a proposed interface or microfluidic experiment, define

    Xi = v_f * tau_int / l_int.

Here v_f is a front speed, tau_int is an interaction time, and l_int is an
interaction length. Xi is dimensionless if the three quantities are positive
and expressed in compatible units.

A convenient interpretation is:

- Xi much less than one: the front moves little during the interaction;
- Xi near one: front motion and local interaction span are comparable;
- Xi much greater than one: the front traverses the interaction span rapidly.

The statement that yield peaks near Xi=1 is only a hypothesis. It cannot be
made true by tuning the interaction length after seeing the response. A
credible test varies v_f, tau_int, and l_int independently, holds chemical
inventory and average energy fixed, measures temperature and mass transfer,
and uses a held-out geometry or front speed.

The coordinate is an experimental design variable, not a new SPPT state
variable. The three scales must be independently controlled or independently
measured as effective scales; a physical relation such as a diffusion law may
couple them and must be modeled rather than assumed away. Xi could become an
SPPT variable only if a domain-specific constitutive model shows that it
controls a declared reservoir flux.

## 14. Multi-objective selection without hidden units

The synthesis suggests selecting experiments by information gain, cost,
redundancy, and risk. A score such as

    Score = (Information - lambda * Redundancy) / (Cost + mu * Risk)

is not meaningful until every term is normalized. Information may be measured
in bits, cost in time or money, and risk in a dimensionless governance score;
they cannot be added without explicit scales. A future audit should record:

- admissible experiment set;
- priors and utility;
- information estimator;
- cost units;
- risk definition;
- lambda and mu;
- sensitivity to normalization;
- stopping rule.

Without those declarations the expression remains a design sketch.

## 15. Cross-case matrix

| Case | Mode/control | Candidate support | Measurement | Supported result | Main unknown |
| --- | --- | --- | --- | --- | --- |
| Flying focus | density and focal trajectory | wake/bunch overlap in z,t | electron energy spectrum and beam metrics | beyond conventional dephasing in a 7 mm experiment | independent phase trace, scaling quality |
| Flycatchers | carrier plus RF envelope | waveform, sidebands, field orientation, unknown sensory coordinate | Emlen-funnel group direction | selected disorientation conditions | receptor and causal pathway |
| Silver/perovskite | fuel-cell versus electrolysis | interface length versus exposed Ag area | ORR/OER and operando structure | source-summary correlation only in this audit | primary record, aging, geometry controls |
| SPPT core | forcing, release, topology, observation | physical phase-reservoir graph | boundary and internal declared observables | conditional equations and model-selection rules | domain-specific planetary validation |

The table is a comparison of audit questions, not a claim that the systems are
physically isomorphic.

## 16. Relevance to dark-matter searches

The mode-resolved idea could improve the design of a dark-matter experiment,
but it does not itself create a dark-matter connection.

A valid dark-matter adapter would need at least:

1. a Lagrangian or effective interaction operator;
2. coupling normalization and mediator or mass convention;
3. local density, velocity distribution, and coherence assumptions;
4. detector transfer function and calibration in SI units;
5. magnetic, thermal, mechanical, electrical, and environmental nuisance
   models;
6. an analysis window, trial-factor treatment, and preregistered null;
7. independent source reversal, off-resonance, and blind-injection controls;
8. predictions in more than one sector or detector channel;
9. a likelihood or confidence construction whose coverage is declared;
10. a result that distinguishes a null bound, an excess, and particle
    identification.

The three audited reports supply no such common operator. The accelerator is a
control example, the bird paper is a biological sensing example, and the
electrode item is an unresolved electrochemistry lead. None establishes dark
matter's identity, origin, purpose, abundance, or planetary role.

The honest connection is therefore procedural: active-support audits may help
prevent a dark-matter search from confusing total drive power, nominal
frequency, or sensor label with the actual response channel. That is a
proposed experimental-design use, not a dark-matter result.

## 17. What would count as an SPPT advancement

The following would be material advances rather than analogies.

- A unit-consistent constitutive map from a mode-specific support variable to
  a planetary phase-reservoir flux.
- A theorem with stated domains for a mode-dependent edge or active support.
- A reproducible numerical forward model with independent parameters,
  calibration, and negative controls.
- A new observation operator that breaks a documented transfer equivalence.
- A pre-registered laboratory or planetary dataset with held-out prediction
  against fixed-topology baselines.
- A validated hybrid topology rule with guard, reset, existence, and
  non-Zeno conditions.

Until one of these is supplied, the active-support layer is an ASTRA methods
perspective, not a core SPPT revision.

## 18. Failure modes this draft is designed to prevent

1. Calling the 100 GeV flying-focus projection a demonstrated accelerator.
2. Treating Emlen-funnel disorientation as free-flight route failure.
3. Claiming that direct cryptochrome decoherence is disproved or that an
   induction receptor is located.
4. Treating an unresolved institutional summary as a verified primary paper.
5. Equating interface perimeter, surface area, or a moving front with a
   universal chemical law.
6. Promoting a support kernel to a material state without units or a
   constitutive bridge.
7. Calling a structural analogy evidence for SPPT or dark matter.
8. Counting the supplied synthesis and its cited papers as independent
   evidence.
9. Letting a dynamic repository HEAD determine a deterministic source identity.
10. Reusing the v1.0.6 manifest, tag, release, or claim matrix for this draft.

## 19. Required implementation before promotion

A future candidate should implement a versioned schema with fields for:

- claim ID and exact paragraph, equation, table, or figure locator;
- source ID and canonical record version;
- supplied input hash and admitted-release hash;
- retrieval date and rights status;
- entailment decision and quoted or paraphrased support scope;
- reproduction command, runtime, seed, and output hash;
- hypotheses, units, domain, boundary conditions, and quantifiers;
- limitation, counterexample, and falsifier;
- evidence class and disposition.

The source ledger and claim ledger must be generated from one frozen candidate
tree. Alias sources must be deduplicated by hash or canonical record, and a
saved transcript must never count as execution.

For an active-support implementation, add:

- a schema validator for mode, control, support measure, and normalization;
- dimension checks for kernels and aggregate responses;
- null records for support-scramble and waveform-scramble controls;
- a calibration model and nuisance covariates;
- synthetic tests where the true support is omitted from the candidate set;
- negative tests for observation-to-physical-edge substitution;
- deterministic output checks that do not read mutable HEAD.

## 20. Residual unknowns

- The SNU primary article and exact rights remain unresolved.
- The bird receptor and causal mechanism remain unresolved.
- The generality of a support-weight representation across nonlinear,
  stochastic, and hybrid systems is unproved.
- No posterior calibration, global search guarantee, or cross-domain transfer
  result is supplied.
- No case in this draft is an empirical planetary test of SPPT.
- No case in this draft is a dark-matter detection or particle-identification
  result.

These are not defects to hide. They are the work list for a possible successor.

## 21. Final disposition

The methodological bridge is useful enough to preserve as a named ASTRA draft,
but not strong enough to promote into the core reference line. The correct
scientific sentence is:

> The audited studies motivate a proposed mode-resolved active-support audit
> for separating control, geometry, observation, and physical transport. They
> do not establish a common mechanism, change SPPT's physical equations, or
> provide dark-matter evidence.

Any later release must repeat source, rights, claim, numerical, accessibility,
privacy, and release-identity checks from a new frozen candidate. The
immutable v1.0.6 assets remain the reference for the existing SPPT claims.

## 22. Provenance and responsibility

The draft was prepared with AI-assisted literature organization, comparison,
equation drafting, and adversarial review. The model is not an author,
scientific validator, peer reviewer, or rights holder. The human project
operator remains responsible for source selection, interpretation, wording,
rights, and any future publication decision. The supplied synthesis is kept as
an identified input and is not silently upgraded to external evidence.
