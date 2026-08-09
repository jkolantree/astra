# SPPT Bridge Protocol — local successor prototype

Status: `local_unpromoted_successor_prototype`

This directory is a local, unpromoted prototype for the proposed bridge:

```text
ConservationContract
    -> ThermodynamicLedger
    -> ObservationalEquivalenceClass
    -> InterventionDesign
    -> CalibratedPredictionAudit
```

The prototype makes all five gates executable at contract level. It is
deliberately separate from the SPPT core and from the immutable v1.0.6
release. It does not claim planetary validation, a topology-recovery theorem,
thermodynamic completeness, or a new physical law.

## Scope

`bridge_contract.py` provides:

- strict directed-incidence and stoichiometric conservation validation;
- dynamic inventory and weighted-invariant residuals;
- an energy/entropy ledger with duplicate-ID, finite-value, balance, and
  nonnegative-production checks;
- finite Markov/transfer signatures and complete-linkage observational classes;
- pole/zero, controllability/observability-rank, and graph-label diagnostics;
- response-derived intervention separation, Fisher information, safety/budget
  filtering, and deterministic utility selection;
- calibration-only scale estimation followed by held-out Gaussian log score,
  CRPS, interval coverage, posterior-predictive checks, simulation-based
  calibration, and promotion/defer/demote decisions;
- deterministic fit/calibration/test splitting and a successor-only strict
  SPPT thermal-edge adapter that binds incidence orientation to entropy checks.

The identifiability signature is an explicit finite design diagnostic, not a
proof of rational transfer equality. Exact scientific promotion still needs a
canonical transfer/pole or independent rank argument. The scoring engine also
expects model means to be fit before the calibration split; it does not hide
training leakage or turn a convenient score into external validation.
Posterior-predictive and SBC outputs are diagnostics with declared sample
sizes; their local status labels do not replace preregistration or independent
replication.

The record types are intentionally conservative. A typed record is not evidence
that the corresponding scientific result has been established.

## Local check

From the repository root, run:

```powershell
& '.\tmp\python-3.12.10-embed\python.exe' -I -B '.\resources\sppt-bridge-protocol\draft-v0.1.0\test_bridge_contract.py'
```

The prototype is not registered in the public manifest or release machinery.
`BRIDGE_MANIFEST.sha256` binds this local prototype's own payload bytes; it is
not the root v1.0.6 release manifest. No commit, push, tag, Pages deployment,
DOI, or release is implied.

## Schema dialect gate

`bridge_protocol.schema.json` deliberately declares JSON Schema Draft 2020-12.
The locked v1.0.6 runtime carries `jsonschema==3.2.0` for an existing
transitive dependency; that version only ships Draft 3/4/6/7 validators.  A
Draft 7 fallback can make this example appear valid while failing to verify the
declared dialect.  Run `validate_schema.py` instead: it uses
`Draft202012Validator` when available and otherwise returns the explicit status
`environment_limited` (exit code 2), never a false pass.

To obtain `valid`, use a disposable external validation environment with a
current `jsonschema` 4.x release, record its interpreter/package identity, and
keep it separate from the root v1.0.6 lock.  Do not upgrade the root lock merely
to remove this warning; that would be a separate dependency/reproducibility
change requiring its own audit.
