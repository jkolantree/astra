# SPPT/ASTRA v1.0.3

This is the publishable successor to the audited v1.0.2 candidate. The public v1.0.2 tag is retained unchanged as negative release-process evidence, but no v1.0.2 GitHub Release was created. Version 1.0.3 carries forward its scientific corrections and frozen numerical results, adds the repaired publication controller, and supersedes v1.0.1 for current use without rewriting or replacing the immutable v1.0.1 tag or assets.

## Publication-controller correction

The natural v1.0.2 tag run exposed a deterministic checkout-controller defect before scientific replay. The pinned checkout action initially fetched the authoritative annotated tag, then compared its tag-object identifier with GitHub's peeled event commit and replaced only the runner-local tag ref with that commit. The release verifier correctly rejected the resulting lightweight local ref. The remote annotated tag and candidate commit were not altered, and the failed run remains preserved as a controller-invalid trial rather than a candidate failure.

The v1.0.3 workflow binds both the declared repository name and immutable GitHub repository ID, then restores the declared remote tag ref through a validated argument-array Git invocation after checkout and exact-Git installation. It requires a non-forced new-ref creation payload with an absent prior ref, and then requires the restored object to be an annotated tag that directly targets `HEAD` and GitHub's event commit before any scientific or archive gate runs. A regression test reproduces the runner-local annotated-tag-to-commit transition, defeats a decoy `origin`, and proves exact restoration while the authoritative remote tag object remains unchanged.

A single creation payload cannot distinguish a first tag creation from deletion followed by later recreation. The release process therefore also requires a separately observed pre-tag absence check and exact remote read-back; historical delete-then-create activity remains a registry-level residual risk until the GitHub Release becomes immutable.

## Scope and evidence

The package remains a not-peer-reviewed perspective and mathematical framework with reduced synthetic demonstrations. It contains no empirical planetary validation, general topology-recovery theorem, or claim that numerical agreement constitutes proof.

## Scientific corrections

The v1.0.1 Figure 5 transient computation applied its unit source to the lossy surface reservoir, while the accompanying equilibrium panel and discussion described deep internal heating. This release places the source at the deep reservoir consistently and derives both displayed equilibria from the implemented model. The analytic static-boundary-degeneracy proposition remains valid.

An algebraic-statistical fiber analysis now supplies an exact structural-identifiability limit on the three-reservoir benchmark. For capacities \(C=(8,3,1)\), surface loss \(1.2\), and node 2 as the only forcing and observation port, the surface star

\[
(k_{02},k_{12})=(5,6)
\]

and the deep star

\[
(k_{01},k_{02})=(30/11,11)
\]

have the same rational surface transfer function for every surface forcing from equilibrium, despite different labeled supports and hidden states. Strictly positive triangle realizations can likewise occur in globally two-to-one transfer-equivalent pairs, and a singular balance locus contains an unobservable hidden mode. More samples, a different surface waveform, or a BIC penalty cannot distinguish exactly equivalent realizations under the same input-output design.

The released generating chain \((k_{01},k_{12},k_{02})=(0.22,1.40,0)\) remains distinguishable in the declared nonnegative candidate domain: its algebraic partner requires a negative conductance. The benchmark therefore remains evidence for pointwise selection of that released generating representation, not family-wide identification of physical topology.

The two-reservoir frequency demonstration is also stated more precisely. Its one-frequency objective uses amplitude alone. One exact nonzero complex response can generically provide two real constraints on two unknown parameters; multiple frequencies can provide redundancy, while the released noiseless calculation demonstrates improved conditioning and finite-grid localization rather than noise resistance or a minimal-data theorem.

## Preserved frozen benchmark results

The corrected interpretation does not alter the frozen ensemble outcomes:

- Training BIC selects the released generating chain in 64/64 realizations.
- The overconnected triangle has lower post-selection held-out RMSE in 23/64 realizations.
- The triangle shortcut reaches its declared lower bound in 29/64 realizations.
- The 20-start design remains post-audit regression evidence rather than untouched, blinded, or external evaluation.

The CSV and JSON remain duplicate serializations of the same synthetic evidence, not independent confirmations.

## Numerical implementation corrections

The numerical routines now:

- preserve representable slow poles and small positive relaxation modes instead of erasing them with absolute thresholds or cancellation;
- avoid avoidable overflow and underflow in trap-response, equilibrium, weak-cut, pole, frequency-response, and Fisher-information calculations;
- scale steady-state solves, refine them against separately accumulated transport and loss terms, and fail closed when the physical balance remains numerically unresolved;
- assemble Laplacian entries with order-independent accurate summation and fail closed when an incident conductance contribution cannot be retained in binary64;
- reject non-finite conductances, parameters, forcing, time, and covariance inputs;
- reject materially asymmetric loss and covariance matrices using scale-relative tests;
- require finite strictly monotonic benchmark time grids and exact observation-vector shapes.

These changes improve finite binary64 behavior but do not promise arbitrary dynamic range. Inputs whose incident conductance ratios cannot be represented reliably during Laplacian assembly are rejected rather than silently erasing a weak edge.

## Verification and release-integrity hardening

Canonical verification now requires:

```powershell
py -3.12 -I -B tools\verify.py --all --workers 4
```

The controller rejects unsafe startup before shadowable imports, removes inherited Python, Pytest, and Git selector state, disables external Pytest plugin autoload, and binds Git operations to the intended repository configuration.

Release checks additionally:

- reject symbolic-link or junction redirection of disposable output roots;
- use atomic archive writes that do not mutate an external hardlink target;
- reject skip-worktree and assume-unchanged index flags;
- use NUL-delimited tracked-path inventories;
- validate portable release-asset basenames and bind every versioned name to the release specification;
- require release documents to equal the tagged manuscript bytes;
- require the source archive to equal the canonical tagged archive bytes;
- bind tag-event verification to GitHub's repository, ref type, and event commit without shell-interpolating the tag name;
- build and verify the complete asset roster in a temporary directory before replacing an admitted prior `dist` roster, with rollback on failed final verification;
- verify the tracked manifest inventory; and
- run scientific generation twice to detect consecutive replay nondeterminism.

## Remaining limitations

Ordinary BIC cannot identify the physical source of two exactly equivalent input-output laws and does not have regular asymptotics on the documented boundary and singular strata. Another spatially distinct input or output, an intervention, or independently justified structural constraints may separate those equivalence classes, but structural identifiability must be recomputed for the particular augmented design.

The identifiability and model-selection benchmarks remain reduced, linear, synthetic, and deliberately favorable. Capacities, sink structure, forcing, noise law, and the closed candidate set are supplied rather than inferred. Other conceptual figures include explicitly labeled nonlinear constitutive examples; none provides astronomical or population validation.

## Licensing and preservation

Licensing and conceptual-provenance boundaries are unchanged. Original software remains MIT licensed; original manuscript text, documentation, figures, and generated results remain CC BY 4.0.

v1.0.1 remains immutable. The public, unreleased v1.0.2 tag remains unchanged and has no GitHub Release. The v1.0.3 release uses a new tag and new release assets. This repository's established publication scope is GitHub-only; no Zenodo ingestion or DOI is claimed.
