# SPPT/ASTRA v1.0.4

This is the publishable successor to the audited v1.0.2 and v1.0.3 candidates. Their public tags are retained unchanged as negative release-process evidence, but neither has a GitHub Release. Version 1.0.4 carries forward the scientific corrections and frozen numerical results from those candidates, repairs the remaining annotated-tag event controller, and supersedes v1.0.1 for current use without rewriting or replacing the immutable v1.0.1 tag or assets.

## Publication-controller correction

The v1.0.3 commit passed the complete natural `main` verification run. Its natural tag run then stopped before dependency installation or scientific replay because the controller equated two different Git object identities that share the same 40-hex representation: the push payload's raw post-update tag-ref object and GitHub Actions' peeled commit. The remote v1.0.3 annotated tag, its commit and tree, and the locally preserved unpublished asset build were not altered. No v1.0.3 GitHub Release was created and no assets were uploaded.

The v1.0.4 controller models the event as a typed chain

```text
tag ref -> annotated tag object -> direct commit target
```

and binds each identity separately. It requires the creation payload's canonical `after` object to equal the annotated tag object fetched from the exact declared repository, while independently requiring the tag's direct commit target to equal `GITHUB_SHA` and `HEAD`. A frozen named event record prevents the tag-object and commit fields from being silently transposed. Regression tests use deliberately distinct object and commit identifiers, reproduce checkout's runner-local annotated-tag-to-commit transition, defeat a decoy `origin`, reject a tag changed between event and fetch even when it targets the same commit, and prove that the authoritative remote object is not modified by restoration.

The controller also retains the v1.0.3 repository-name and immutable repository-ID binding, exact ref and tag-name checks, non-forced new-ref creation requirement, zero prior-ref requirement, argument-array fetch, restore-before-dependencies order, and independent post-installation re-verification.

A single creation payload cannot distinguish a first tag creation from deletion followed by later recreation. The release process therefore also requires a separately observed pre-tag absence check and exact remote read-back; historical delete-then-create activity remains a registry-level residual risk until the GitHub Release becomes immutable.

## Scope and evidence

The package remains a not-peer-reviewed perspective and mathematical framework with reduced synthetic demonstrations. It contains no empirical planetary validation, general topology-recovery theorem, or claim that numerical agreement constitutes proof.

## Scientific corrections carried forward

The v1.0.1 Figure 5 transient computation applied its unit source to the lossy surface reservoir, while the accompanying equilibrium panel and discussion described deep internal heating. This release places the source at the deep reservoir consistently and derives both displayed equilibria from the implemented model. The analytic static-boundary-degeneracy proposition remains valid.

An algebraic-statistical fiber analysis supplies an exact structural-identifiability limit on the three-reservoir benchmark. For capacities \(C=(8,3,1)\), surface loss \(1.2\), and node 2 as the only forcing and observation port, the surface star

\[
(k_{02},k_{12})=(5,6)
\]

and the deep star

\[
(k_{01},k_{02})=(30/11,11)
\]

have the same rational surface transfer function for every surface forcing from equilibrium, despite different labeled supports and hidden states. Strictly positive triangle realizations can likewise occur in globally two-to-one transfer-equivalent pairs, and a singular balance locus contains an unobservable hidden mode. More samples, a different surface waveform, or a BIC penalty cannot distinguish exactly equivalent realizations under the same input-output design.

The released generating chain \((k_{01},k_{12},k_{02})=(0.22,1.40,0)\) remains distinguishable in the declared nonnegative candidate domain: its algebraic partner requires a negative conductance. The benchmark therefore remains evidence for pointwise selection of that released generating representation, not family-wide identification of physical topology.

The two-reservoir frequency demonstration is also stated precisely. Its one-frequency objective uses amplitude alone. One exact nonzero complex response can generically provide two real constraints on two unknown parameters; multiple frequencies can provide redundancy, while the released noiseless calculation demonstrates improved conditioning and finite-grid localization rather than noise resistance or a minimal-data theorem.

## Preserved frozen benchmark results

The corrected interpretation does not alter the frozen ensemble outcomes:

- Training BIC selects the released generating chain in 64/64 realizations.
- The overconnected triangle has lower post-selection held-out RMSE in 23/64 realizations.
- The triangle shortcut reaches its declared lower bound in 29/64 realizations.
- The 20-start design remains post-audit regression evidence rather than untouched, blinded, or external evaluation.

The CSV and JSON remain duplicate serializations of the same synthetic evidence, not independent confirmations.

## Numerical implementation corrections carried forward

The numerical routines:

- preserve representable slow poles and small positive relaxation modes instead of erasing them with absolute thresholds or cancellation;
- avoid avoidable overflow and underflow in trap-response, equilibrium, weak-cut, pole, frequency-response, and Fisher-information calculations;
- scale steady-state solves, refine them against separately accumulated transport and loss terms, and fail closed when the physical balance remains numerically unresolved;
- assemble Laplacian entries with order-independent accurate summation and fail closed when an incident conductance contribution cannot be retained in binary64;
- reject non-finite conductances, parameters, forcing, time, and covariance inputs;
- reject materially asymmetric loss and covariance matrices using scale-relative tests; and
- require finite strictly monotonic benchmark time grids and exact observation-vector shapes.

These changes improve finite binary64 behavior but do not promise arbitrary dynamic range. Inputs whose incident conductance ratios cannot be represented reliably during Laplacian assembly are rejected rather than silently erasing a weak edge.

## Verification and release-integrity hardening

Canonical verification requires:

```powershell
py -3.12 -I -B tools\verify.py --all --workers 4
```

The controller rejects unsafe startup before shadowable imports, removes inherited Python, Pytest, and Git selector state, disables external Pytest plugin autoload, and binds Git operations to the intended repository configuration. Release checks additionally reject redirected output roots, external hardlink mutation, hidden index flags, unsafe or stale asset names, archive divergence, manifest drift, and consecutive scientific or document replay nondeterminism.

## Remaining limitations

Ordinary BIC cannot identify the physical source of two exactly equivalent input-output laws and does not have regular asymptotics on the documented boundary and singular strata. Another spatially distinct input or output, an intervention, or independently justified structural constraints may separate those equivalence classes, but structural identifiability must be recomputed for the particular augmented design.

The identifiability and model-selection benchmarks remain reduced, linear, synthetic, and deliberately favorable. Capacities, sink structure, forcing, noise law, and the closed candidate set are supplied rather than inferred. Other conceptual figures include explicitly labeled nonlinear constitutive examples; none provides astronomical or population validation.

## Licensing and preservation

Licensing and conceptual-provenance boundaries are unchanged. Original software remains MIT licensed; original manuscript text, documentation, figures, and generated results remain CC BY 4.0.

v1.0.1 remains immutable. The public, unreleased v1.0.2 and v1.0.3 tags remain unchanged and have no GitHub Releases. The v1.0.4 release uses a new tag and new release assets. This repository's established publication scope is GitHub-only; no Zenodo ingestion or DOI is claimed.
