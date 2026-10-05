# Quantum recurrence: three different evolutions

**Publication status: Draft companion. Scientific status: source-attributed
interpretation; proposed comparisons unexecuted.**

Dong et al., *Quantum many-body mixed phase space revealed by hybrid feedback
control*, Nature Physics (23 September 2026),
[DOI: 10.1038/s41567-026-03431-z](https://doi.org/10.1038/s41567-026-03431-z),
provides a useful comparison between conventional quantum dynamics, evolution
projected onto a variational manifold, and feedback stabilization. It does not
establish fundamental nonlinear quantum mechanics or validate SCM.

## Keep the protocols separate

1. **Uncontrolled evolution:** a prepared quantum state evolves under U(t).
2. **Projected TDVP:** evolution is projected onto a specified variational
   manifold, giving effective equations for its parameters. The variational
   circuit produces entangled states; this is not simply a product-state model.
3. **Hybrid feedback:** measurement, classical optimization and repreparation
   occur every 80 ns. The objective uses a central four-qubit subsystem, while
   the displayed imbalance uses the central twelve qubits. Finite feedback
   cycles are not continuous TDVP or an uninterrupted trajectory of the device.

The experiment uses 24 qubits; the first-revival exact-diagonalization comparison
uses 16 qubits. Neither is reproduced by this explorer. A future browser model
must state its actual size, initial state, boundaries and observable convention.

## Which return is being measured?

A fixed-reference imbalance compares to a fixed reference, whereas a co-moving
imbalance changes its decoding frame. Final article equation 3 averages
parity-weighted decoded sigma-z expectations with normalization 1/|A| over the
selected subsystem A. These are not interchangeable with global pure-state
fidelity, |⟨ψ(0)|ψ(t)⟩|², or with decoded subsystem return probability.
A perfect local imbalance does not establish global return. Subsystem return
probability is not generally Uhlmann fidelity.

A small first revival alone does not establish chaos. Supplement S10 also
recommends examining the maximum revival after the first minimum over a declared
later time window. Any implementation must declare that window before comparing
outcomes.

## Source data and reproduction limits

[Ren's Leeds deposit](https://archive.researchdata.leeds.ac.uk/1577/) provides
processed figure tables and documentation. It does not supply raw shots or a
pinned end-to-end plotting/processing pipeline. The article names EDKit.jl and
InfiniteTEBD.jl; this is not a claim that no code exists. The article also offers
source-data workbooks. The deposit identifies its dataset as CC BY 4.0; this
explorer links to it and does not redistribute the archives or article images.

The scientific integration review identifies the following unresolved points:

- A co-moving phi2 convention, documentation referring to 300 shots per delay
  versus a final caption referring to 1,200, and undocumented readout/peak
  processing. Do not invent error bars to fill these gaps.
- Figure 3b experimental sine coordinates do not uniquely determine angles.
  Applying arcsin does not reconstruct the original trajectory. The numerical
  stable-orbit file contains spline control points, not a time-indexed solution.
- Figure 1c unqualified angles are radians; `_pi` columns are multiples of pi.
- The first-revival ED map uses 16 qubits, periodic boundaries, half filling,
  ramp t0 = 1.5/Jo and a 241 × 161 grid. Co-moving maps omit the ramp and use T = pi.
- The main Hamiltonian and supplement S37 use opposite exchange signs; that
  convention must be resolved before asserting reproduction.
- Jo/(2pi) = 5 MHz gives 1/Jo ≈ 31.8 ns; 200 ns corresponds to 2pi/Jo.
  Keep projected calculations dimensionless unless conversion is explicit.

Consult the [final supplement](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41567-026-03431-z/MediaObjects/41567_2026_3431_MOESM1_ESM.pdf)
and the [earlier arXiv version](https://arxiv.org/abs/2607.14223) with their version
differences retained. Do not silently substitute the preprint normalization for
the final article.

## Proposed tests — none executed here

- Replay deposited values without fitting; call this data replay, not an
  independent experiment.
- Independently check final equation 5 before implementing it. Test the limit
  je = j3 = 0: theta is constant and both phi derivatives equal jo. Then test
  step-size convergence and event-detected phi1 = 0 mod 2pi Poincare crossings.
- Compare quantum, projected and controlled dynamics only with matched initial
  states, Hamiltonians, boundaries and observables.
- Require SCM to specify an evolution law, preparation/state map, observable
  map, parameter constraints and held-out prediction before comparison.
- For ensemble consistency, compare decompositions of the same density matrix
  under identical accessible preparation information and control. A controller
  that knows decomposition labels implements a different protocol.

These are proposed reproducibility and discrimination tests, not results or
claims added to the stable ASTRA claim matrix.
