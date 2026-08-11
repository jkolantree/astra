# ASTRA repository instructions

This file supplements the general agent charter. Versions, hashes, incidents, and milestone-specific findings belong in release records, evidence ledgers, or runbooks.

## Preserve repository and publication identity

- Inspect repository identity, HEAD/tree, status, remotes, and registered worktrees before consequential work.
- Treat unexplained state as user-owned. Do not reset, clean, stash, overwrite, prune, or delete merely to obtain a pass.
- Tagged, released, versioned, or checksum-bound artifacts are immutable history. Correct them through visible errata or new identities; never move tags or replace release assets.
- Commits, pushes, tags, Releases, Pages changes, archive changes, and DOI/Zenodo actions require explicit authorization.

## Scientific and evidentiary discipline

- Distinguish VERIFIED, OBSERVED, INFERRED, PROPOSED_ONLY, UNKNOWN, DEFERRED, and REJECTED.
- Preserve negative results, rejected claims, limitations, and harness/environment failures.
- CLAIM_MATRIX.json is the core consequential-claim register. Claim IDs are public identifiers and must not be reused, silently renumbered, or assigned different meanings across consumers.
- Manuscripts, claim ledgers, evidence records, captions, code, and tests must agree.
- Do not claim “all,” “every,” “exact,” “complete,” or “reproducible” without machine-checkable coverage from the authoritative source.

## Runtime and generated artifacts

- RUNTIME.json defines the release-authoritative environment. Mismatched-runtime results are diagnostic or ENVIRONMENT_LIMITED.
- Sanitize inherited test controls, including PYTEST_ADDOPTS, only for the invoked process and report that action.
- Run document, data, and figure generators only in an isolated worktree or disposable copy unless primary-checkout generation is explicitly authorized.
- Identify canonical sources and producers before editing. Do not hand-edit generated derivatives.
- Adding a public file requires explicit allowlist admission, license mapping, and mechanical manifest regeneration.
- Derive hashes and manifests from final bytes; serialize identity artifacts last.
- A green root suite is not a complete-repository result unless all applicable namespaced suites and consumers were also checked.

## Document changes

- Verify scientific/editorial changes with semantic review, applicable tests, and deterministic rebuild evidence.
- For any rebuilt PDF, render and inspect every page and review suspect pages at readable resolution.
- Check corresponding HTML at desktop, mobile, and print widths.
- Report an unavailable visual surface as NOT_CHECKED rather than inferring a pass.

## Completion

- Report changed/generated files, runtime, commands, checks, skips, limitations, residual risks, and final Git status.
- Stop before promotion if immutable bytes would change, a claim would be upgraded without evidence, or a required gate remains unresolved.
- Change AGENTS.md only with explicit user authorization. Keep evolving procedures and incident history elsewhere.
