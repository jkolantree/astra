# Coherence-cell exploration: methods note

## 1. Disposition

This is a local, unpromoted ASTRA supplemental research draft. It is not a
peer-reviewed paper, an empirical discovery, a replacement for Lambda-CDM,
SPPT, QED, or general relativity, or evidence for a particulate ether.

The supplied proposal is treated as a source of questions, not as scientific
authority. The draft deliberately keeps the following labels distinct:

- `observed`: present in a primary record or supplied artifact;
- `source_asserted`: reported by a source but not independently reproduced;
- `hand_checked`: checked algebraically, dimensionally, or against a declared
  boundary;
- `proposed_only`: a new notation, analogy, model term, or test;
- `deferred`: blocked by unresolved source identity, rights, or controls;
- `rejected`: incompatible with the current benchmark evidence.

## 2. The research question

The proposal repeatedly uses the words wave, pressure, coherence, support,
collapse, release, and information across atoms, molecules, magnets, BECs,
white dwarfs, black holes, and cosmology. The first question is not whether
these systems are made of one hidden substance. It is:

> Is there a quantitative invariant that survives translation between any of
> these domains and improves prediction over the domain-specific baseline?

If no such invariant exists, the similarities remain pedagogical analogies.
That is a useful result, not a failure of the audit.

## 3. AEOF record

Every proposed bridge should be represented by:

    AEOF = (analogy, kernel, standard_equation, proposed_term,
            domain_units, observable, null_model, falsifier, prior_art,
            evidence_status)

The record prevents an analogy from silently becoming a physical edge.

### 3.1 Analogy

State the intuitive resemblance in ordinary language. Examples include “a
wave crest deposits more momentum at a dock” or “a compressed system releases
stored energy.” The analogy is not evidence.

### 3.2 Established kernel

State only what is measured or already derived. For a hydrogen transition this
could be a frequency and uncertainty. For a BEC it could be a controlled
interaction quench and atom-loss trace. For a white dwarf it could be a
mass-radius estimate and gravitational redshift.

### 3.3 Standard equation

Write the current domain equation before adding a new term. This prevents a
pressure metaphor from replacing Maxwell stress, a Born-Oppenheimer energy
surface, the Gross-Pitaevskii equation, a degenerate equation of state, or the
Einstein equations.

### 3.4 Proposed term

Name exactly what is new: a field, coupling, constitutive coefficient,
dispersion correction, intervention, or scaling law. A new name for an old
quantity is not a new term.

### 3.5 Observable and falsifier

Specify a measured quantity, baseline, nuisance model, effect-size threshold,
and a result that would count against the proposal. “It explains everything”
is not an endpoint.

## 4. Atomic bridge: from crest language to wave packets

For an energy eigenstate,

    psi_n(r,t) = psi_n(r) exp(-i E_n t / hbar),

and therefore `|psi_n(r,t)|^2` is stationary. A ground-state hydrogen atom is
not a classical sphere that pulses through an electron radius.

For a prepared superposition,

    Psi(r,t) = sum_n c_n R_nl(r) Y_lm(theta,phi) exp(-i E_n t / hbar),

and the radial probability observable is

    P(r,t) = r^2 integral dOmega |Psi(r,t)|^2.

the radial probability contains cross-terms at

    omega_nm = (E_n - E_m) / hbar.

Those cross-terms can make a localized Rydberg wave packet move, dephase, and
revive. This is the scientifically correct version of the pulsing intuition.
It does not introduce an ether, an electron surface, or a universal radial
frequency.

### 4.1 Atomic benchmark

The first executable research milestone should be a hydrogenic wave-packet
calculation with disclosed coefficients, basis truncation, time step, and
error tolerance. The output should include:

- radial density and current;
- revival time and fractional revival structure;
- pump-probe ionization proxy;
- sensitivity to basis truncation and dephasing;
- comparison with a stationary eigenstate null.

Any substrate term must then predict a residual shift, extra dephasing, or
new transition rule. If it predicts no residual, it is operationally
equivalent to standard quantum mechanics in this test.

### 4.2 Hard atomic gates

An electron-like substrate must eventually reproduce charge quantization,
spin one-half, Fermi statistics, antimatter/CPT, the magnetic moment, atomic
spectra, and scattering. A spherical scalar bubble does not supply these by
itself. The electron magnetic moment and hydrogen/antihydrogen spectroscopy
are precision constraints, not optional later checks.

## 5. Stress-flux translation

Replace the unqualified word “pressure” with a measurable stress or momentum
flux. For a spatial stress tensor `T^ij` and surface normal `n_i`, define

    P_n = n_i T^ij n_j,
    P_iso = (1/3) T^i_i,
    A^ij = T^ij - P_iso delta^ij.

`P_n` is directional normal momentum flux, `P_iso` is its isotropic part, and
`A^ij` is anisotropic stress. They are not interchangeable with density,
probability, or material occupancy. These are local orthonormal-frame
shorthand; a curved-coordinate implementation must carry the spatial metric,
index placement, and surface measure explicitly.

### 5.1 Domain mappings

| Domain | Standard object | What the proposed bridge must reproduce |
|---|---|---|
| Electromagnetism | Maxwell stress tensor | force and torque maps for arbitrary fields and magnet geometries |
| Molecules | Born-Oppenheimer energy surface | bond length, dissociation energy, vibrational spectrum |
| BEC | interaction and quantum-pressure terms | collapse threshold, atom burst, remnant dynamics |
| White dwarf | degenerate-electron equation of state | mass-radius relation, cooling, gravitational redshift |
| Gravity | stress-energy tensor and metric | free fall, clock redshift, lensing, orbital and wave tests |

The proposed common field is admissible only if one constitutive law maps to
these domain observables without breaking gauge invariance, Lorentz symmetry,
quantum statistics, or the equivalence principle.

## 6. Coherence-support-release hypothesis

Across BEC collapse, compact-star support, magnetic reconnection, AGN feedback,
and relativistic collapse, a broad pattern may be useful:

    stored order or energy -> support loss -> instability -> release -> relaxation

For a comparative phase diagram, define only dimensionless quantities:

    Pi = E_support / |E_binding|,
    chi = tau_relax / tau_dyn,
    C = declared coherence statistic.

The definition of each quantity must be domain-specific. A density, quantum
purity, magnetic correlation, or phase-space order parameter must not be
silently treated as the same `C`.

The hypothesis is testable only if it predicts a common boundary, exponent, or
out-of-sample scaling law. A visual similarity or a post-hoc collapse of plots
does not establish universality. BEC critical-scaling literature is prior art;
the proposed contribution must state its exact delta from that literature.

## 7. Discrete-substrate / foam branch

“Planck bubbles” are treated here as a parameterized hypothesis, not a fact.
A simple local lattice normally produces anisotropy and modified dispersion.
A candidate effective correction could be written schematically as

    E^2 = p^2 c^2 + m^2 c^4
          + eta_n p^2 c^2 (E / (M_star c^2))^n.

The model must calculate photon arrival-time differences, birefringence,
interferometer noise, atomic shifts, and gravitational-wave propagation. A
mechanical rest frame is a high-priority failure mode. Existing Lorentz tests
already constrain simple linear Planck-scale dispersion.

If the proposed substrate is exactly Lorentz invariant and adds no observable
degree of freedom, the substrate is not experimentally distinguishable from
ordinary fields or spacetime. That is an identifiability result, not a
refutation of metaphysical speculation.

## 8. Redshift discriminator

The static/tired-light branch must be compared jointly against the expanding
metric model. A candidate record should predict:

    redshift,
    source-clock stretch,
    spectral-line broadening,
    image blur or angular diffusion,
    surface-brightness evolution,
    CMB temperature evolution,
    BAO scale,
    gravitational lensing.

Matching the distance-redshift relation alone is insufficient. The observed
supernova time-dilation relation is a hard gate for non-time-dilating models.
JWST early-galaxy tension is a galaxy-formation question unless a replacement
model also fits the CMB, BAO, lensing, and time-dilation network.

## 9. Black holes, wormholes, and information

AGN jets inflating X-ray cavities demonstrate energy transfer from accretion
systems into surrounding plasma. They do not establish that a black hole
explodes, reboots, or acts as a literal data node.

The Einstein-Rosen bridge and later traversable-wormhole constructions are
mathematical spacetime solutions with stringent causal and stress-energy
conditions. A “missing bubble” interpretation must specify a metric, source,
stability analysis, and observable. A black-hole reset claim must specify an
entropy law and a signal such as a ringdown deviation or echo waveform.

## 10. Prior-art and novelty boundary

The following families overlap the proposal and must be searched before any
priority language is used:

- thermodynamic and emergent gravity;
- causal sets, causal dynamical triangulations, and loop/spinfoam models;
- quantum cellular automata and digital physics;
- analogue and superfluid gravity;
- Einstein-aether and Lorentz-violating effective theories;
- oscillons, Q-balls, and topological defects;
- quantum wave-packet collapse and revival;
- BEC critical scaling and nonequilibrium universality;
- tired-light and static cosmology tests.

The current claim is therefore “proposed ASTRA integration and audit pattern,”
not “new universal mechanism” or “first theory.” Novelty remains `unknown`
until a novelty ledger records the exact delta from canonical prior art.

## 11. Promotion gates

Before a future public research version, require:

1. a frozen candidate tree and input hashes;
2. claim-local source and equation locators;
3. an explicit novelty ledger and search log;
4. a unit-consistent constitutive bridge or a clearly labeled methods-only
   result;
5. an independent replay with held-out regimes and preserved failures;
6. precision atomic, Lorentz, equivalence-principle, gravitational-wave, and
   cosmological null checks;
7. rights, privacy, and source-status review;
8. a separate release identity if and only if the user later authorizes it.

Until those gates pass, this folder remains a local supplemental draft and
does not alter SPPT or any immutable ASTRA release.
