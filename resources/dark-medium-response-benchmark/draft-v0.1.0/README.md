# Dark-Medium Response Benchmark -- Draft v0.1.0

**Status: Draft; experimental; unpromoted.** This is a separate synthetic
algebra, response and null experiment. It is not an Atlas publication or
published Atlas evidence. Comparative utility is **UNESTABLISHED**: the
comparator and response formulation use the same finite-library weighted least
squares (WLS) with primitive-species versus modal forward solvers. A change of
coordinates supplies no distinct inference method.

The question is whether the Atlas's declared longitudinal fluid response
predicts reproducible observable equivalence classes, and which additional
measurements can resolve those classes. The benchmark checks that organization
against an independently assembled primitive calculation; it does not test a
general advantage of Causal Residual Spectroscopy. The experiment and synthetic
results belong to this directory alone. Atlas v0.1.0, its historical draft,
S1/S2 evidence, and the SPPT/ASTRA core retain their independent identities.
This Draft has no Pages route, tag, GitHub Release, DOI or Zenodo record.

## Model and independently checked algebra

The source is [Atlas v0.1.0, sections 4-6](../../dark-medium-response-atlas/v0.1.0/dark-medium-response-atlas-v0.1.0.md).
It assumes homogeneous neutral, unmagnetized, nonstreaming species with charges
`+q` and `-q`, number density `n`, Newtonian local Jeans gravity, a massless
unbroken gauge field, and barotropic specific pressure responses `c+^2,c-^2`.
Only the longitudinal linear fluid closure is exercised. The transverse,
kinetic, condensate and preferred-frame claims are outside this calculation.

Write `g = 4piG`. Direct elimination of continuity, momentum, Poisson and Gauss
equations gives the primitive density operator

```text
D = [[k^2 c+^2 - g n m+ + n q^2/m+,  -g n m- - n q^2/m+],
     [-g n m+ - n q^2/m-,          k^2 c-^2 - g n m- + n q^2/m-]].
T = [[m+, m-], [1, -1]],     [R,Q]^T = T [deltan+,deltan-]^T.
```

Exact rational arithmetic independently verifies `T D T^-1` against the Atlas's
generic unequal-mass matrix and eigenvalue discriminant in 15 cases, including
unequal pressure, unequal mass with equal pressure, the cold limit, and zero
gravity or charge. Thus the algebra controls cover the displayed generic
matrix, while the statistical experiment uses only its equal-mass restriction.
For `M=m++m-`, the off-diagonal entries are
`k^2(m+m-/M)(c+^2-c-^2)` and `k^2(c+^2-c-^2)/M`: unequal mass alone does not create
mixing when the specific pressure responses agree. The exact frequency ratio
`Omegap^2/omegaJ^2 = q^2/(g m^2)` for an equal pair is also density independent.

For dimensionless `m+=m-=n=1`, let `c=(c+^2+c-^2)/2`, `d=(c+^2-c-^2)/2`,
`J^2=2gn`, and `P^2=2nq^2`. The evaluation model is

```text
x_ddot + gammax_dot + A(k)x = f,        x = [R,Q]^T,
A(k) = [[c k^2 - J^2, d k^2], [d k^2, c k^2 + P^2]],
chi(k,omega) = [A(k) - omega^2 I - igammaomega I]^-1   for exp(-iomegat).
```

The positive scalar damping `gamma=0.15` is an added phenomenological,
symmetry-preserving benchmark closure; it is not derived from the Atlas's
undamped equations. All sampled modes are stable under the fixed configuration.
`d=0` preserves pair symmetry and decouples mass and charge. `d=+/-0.2` breaks
the equality of pressure responses and produces mixed response. This is a
declared closure/symmetry break, not evidence of microscopic charge-conjugation
violation.

The modal solver uses the explicit two-by-two inverse. The independent forward
solver assembles four Fourier continuity/momentum equations for `deltan+/-,v+/-` and
solves by pivoted elimination after substituting Poisson/Gauss fields. The
primitive solver generates synthetic means. Neither solver calls the other.

## Observation, nuisance parameters and exact nulls

`mass_only` measures only `chiMM`: one calibrated mass drive and one mass
readout. `full_response` measures all four entries: two independently calibrated
drive columns and two readouts. At each split there are ten `(k,omega)` points,
so these operators receive respectively 10 and 40 complex observations.
Acquisition cost and information are **not matched across operators**. Only the
two forward formulations within each operator have matched observations and
budgets. Any recovery difference across operators is a bounded effect of
additional measurements, with no claim of acquisition efficiency.

Each real and imaginary component has independent Gaussian noise with known
standard deviation `0.04`; filtering is the identity. Sensor gain, drive
amplitude, damping, `c`, `J^2` and noise scale are fixed known quantities in the
scored experiment. There is no fitted noise scale, adaptive filtering, hidden
intervention, or unreported nuisance optimization.

The controls make limits visible:

- At `d=0`, mass-only response is independent of `P^2` at every frequency and
  wave number. The charge scale is genuinely unidentifiable in this operator.
- At any `d`, `chiMM` depends on `d^2`, so `d` and `-d` have exactly identical
  mass-only response. Full response changes the sign of its mixed entries.
- At a single `k0`, replacing `(c,J^2,P^2)` with
  `(c+epsilon,J^2+epsilon k0^2,P^2-epsilon k0^2)` preserves the entire response. A second wave number
  breaks this compensation when the other model assumptions are retained.
- Unknown sensor gain and unknown drive amplitude enter as their product.
  The measurement function exercises compensated pairs. A separate noiseless
  known unit-drive calibration recovers gain, illustrating the additional
  information required; that algebra control is not a noisy calibration study.
- Zero drive produces zero signal for every candidate through the same
  primitive forward/measurement path. Noiseless full response uniquely
  recovers all six grid candidates.

## Frozen evaluation contract

[evaluation.json](evaluation.json) fixes every choice before held-out scoring.
The six equally available candidate hypotheses are `P^2 in {0.8,1.6}` and
`d in {-0.2,0,0.2}`, with `c=1` and `J^2=0.2`. Every grid member is used as a
fixed synthetic truth. This is exact-library recovery with known nuisance
parameters, not continuous-parameter identifiability or an off-grid robustness
test. Conventional Gaussian WLS enumerates all six candidates; the tuning
budget is zero. The ordinary squared-residual objective is also documented by
[SciPy's primary least-squares reference](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html);
this tiny finite library requires no optimizer or new dependency.

Training uses `k={0.8,1.2}`, `omega={0.25,0.65,1.05,1.45,1.85}`. Held-out scoring
uses disjoint `k={1.0,1.4}`, `omega={0.45,0.85,1.25,1.65,2.05}`. Each operator and
fixed truth has 64 independent repetitions, with separate training and
held-out noise streams derived by SHA-256 from the recorded seed, repetition,
truth, operator and split. Development tests use a separate seed. The fitter
accepts only training observations and fixed training predictions; it receives
neither truth identifiers nor held-out data.

The primary score is held-out squared residual divided by known noise
variance, averaged over real components. For each repetition, scores first
average the six fixed truths. The paired relative advantage is
`(baseline-response)/baseline`; its reported approximate two-sided 95%
interval is the mean plus/minus `1.99834` sample standard errors over 64
independent repetition aggregates. The predeclared practical criterion is a
lower interval bound above 5% relative improvement. No such method advantage
is expected for equivalent solvers.

All cost minimizers within absolute tolerance `1e-9` are retained. These are
numerical tie classes, **not statistical parameter confidence regions**. The
first index is used only to make predictions deterministic; arbitrary tie
breaking is never credited as unique parameter recovery. Recovery counts and
Wilson 95% intervals refer to Monte Carlo repetition over each fixed truth,
and are reported separately from the score uncertainty.

Unresolved classes, recovery errors and lack of improvement are acceptable
scientific outcomes. Source/runtime mismatch, singular or nonfinite responses,
overlapping splits, algebra-control failure, or disagreement between equivalent
formulations are harness failures and do not produce a completed experiment.
Changing the substantive contract after viewing scores requires a new
candidate/run; reused cases then count as regression evidence.

## Reproduction and evidence identity

The retained first run, `response-null-candidate-1`, completed 384 paired
trials per operator (64 repetitions of six fixed truths). Both formulations
returned the same fitted classes in all 768 paired trials. Their maximum
absolute score difference was `5.70e-14`, well inside the declared `1e-9`
solver-equivalence tolerance. Tiny nonzero paired intervals in the JSON are
floating-point roundoff, not evidence of a method advantage. Neither operator
met the predeclared 5% practical-improvement criterion.

| Operator | Held-out response score (approximate 95% interval) | Unique truth recovery for each fixed truth |
|---|---|---|
| Mass-only | 0.976435 (0.949662, 1.003207) | 0/64; two indistinguishable candidates always retained |
| Full response | 0.989098 (0.972994, 1.005203) | 64/64 |

Every retained class contained the generating truth. Per fixed truth, the
Wilson 95% interval is `[0, 0.0566]` for mass-only unique recovery and
`[0.9434, 1]` for full-response unique recovery. All 15 exact rational algebra
cases and the declared controls passed. The larger observation operator
resolved this small, calibrated candidate library; comparative inference
utility remains **UNESTABLISHED**.

Use the exact CPython 3.12.10 environment and dependency contract in
[RUNTIME.json](../../../RUNTIME.json). The producer itself uses only standard
library complex arithmetic, `Fraction`, and seeded `random.Random.gauss`.
It does not call NumPy, SciPy or a BLAS kernel. These results therefore add no
cross-platform floating-point identity claim to the existing runtime contract.

From the repository root, with that interpreter selected:

```text
python -I -B resources/dark-medium-response-benchmark/draft-v0.1.0/benchmark.py --controls
python -I -B resources/dark-medium-response-benchmark/draft-v0.1.0/benchmark.py --check
python -I -B -m pytest tests/test_dark_medium_response_benchmark.py
```

The initial sequence is source/configuration and development checks, then
`--freeze`, then the no-argument producer. The frozen record binds the producer,
configuration, tests, Atlas source, runtime contract and dependency lock before
scoring. [frozen-evaluation.json](frozen-evaluation.json) excludes itself and
results from its input hashes; [results.json](results.json) binds that frozen
record. The outer repository manifest and commit bind the complete payload.
There is no circular output hash. Existing differing frozen records or results
are never overwritten by the producer. `--check` recomputes in memory and
compares canonical result bytes without replacing the retained record.

Only the generated frozen record and results are canonical producer outputs.
The results retain actual controls, paired scores and their uncertainty,
per-truth recovery and negative outcomes. Successful replay establishes this
declared experiment only. It cannot establish dark-matter detection, empirical
validation, a cosmic ontology, general CRS superiority, peer review, priority,
novelty, or ASTRA-core authority. Gravitational role, collective charge response,
preferred-frame claims and condensate/superfluid phase assumptions remain
distinct.

Original code and tests are MIT under the root [LICENSE](../../../LICENSE).
Original documentation, configuration and generated synthetic results are
CC BY 4.0 under [the repository license](../../../licenses/CC-BY-4.0.txt), to the
extent the author holds the relevant rights. External sources and dependencies
retain their own terms; no external source data or third-party source bytes are
redistributed here.
