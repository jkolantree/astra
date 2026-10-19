# Inactive namespaced publication design

The adjacent `.yml.disabled` file is a review scaffold, not an executable publication implementation. It is outside `.github/workflows`, its only job has `if: false`, permissions are empty, the runner label is deliberately unapproved, and its only command exits with failure. There are no action references, installation commands, secrets, publishing calls, dispatch triggers or Pages deployment steps. Copying it into an active location would not implement release publication.

The proposed namespace `astra-integrated-research-v*` requires owner selection. It cannot match the core `v*` trigger. The earlier `sppt-scm-research-companion-v0.1.0-draft.1` provisional identity addresses the bounded companion, not this new integrated edition. Root RELEASE_SPEC.json, CITATION.cff, v1.0.7 authority, the existing four workflows, published Atlas prerelease and ancestral/unpromoted v1.0.8 candidate remain unchanged.

The existing Atlas workflow establishes a useful separate publication-line pattern. A later implementation must independently establish the following checks, without replacing the historical core gate:

1. Owner-selected package-local release spec, exact new annotated tag identity, reviewed commit/tree, main ancestry and explicit prerelease/non-Latest policy. Reject existing tags/releases, mutable tag identity and all core tags.
2. An admitted final source inventory, exact rights/asset allowlist and citations, approved split runtime/provider inputs, complete test accounting, unchanged historical authority and32 original SCM payload hashes. Never convert a diagnostic failure or not-tested check to PASS by excluding it from the report.
3. Two independent complete builds from initially empty output trees under the selected final runtime. Bind all inputs, outputs, notices and privacy checks; explicitly distinguish reproduced outputs from retained originals. Current019/020 partial families do not establish a complete69-output run.
4. Deterministic source/asset archives, safe regular members, exact checksums and detached identity. Detached digest identity is not a signature or independent attestation. Use existing supported signing only if separately available and approved; create no keys.
5. Repository immutable-release configuration verified through an already authorized read mechanism; absence of the intended release rechecked immediately before publication. Keep write permission confined to a future approved publication job. Do not change account or repository settings to satisfy the check.
6. Explicit final publication approval, then exact asset upload and post-publication identity/hash/immutable/prerelease/non-Latest verification. No overwrite or replacement of existing public assets. Pages admission and explorer navigation remain a separate reviewed action.

Unresolved implementation choices include the selected release identity, final asset names, runner/provider provisioning, authenticated read permission, final-source test results, comprehensive fresh build, source/runtime/Pages admission and asset appearance/rights decisions. This scaffold intentionally does not pretend those choices are settled.

GitHub recognizes workflow files with `.yml` or `.yaml` extensions in `.github/workflows`; job conditions and permissions are defined by its [official workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax). This file is a proposal under that contract, not a way around it.
