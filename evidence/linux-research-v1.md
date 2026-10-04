# ASTRA Linux research baseline v1

Linux research v1 is a separately versioned local development baseline. It does
not reissue a publication, replace Windows evidence, or claim Windows numerical
equivalence. The owner authorized establishing this baseline after reviewing the
portability diagnosis. Public release, merge, and remote publication remain outside
that authorization.

The machine-readable contract is [linux-research-v1.json](linux-research-v1.json).
It pins 46 source/configuration files and 57 output hashes before a fresh two-pass
refit and rendering run. The runtime is the exact executable, numerical-library,
font and browser contract in [RUNTIME-linux.json](../RUNTIME-linux.json), with the
unchanged hash-locked dependencies. The whole OS image and every system shared
library are not frozen; differing output bytes fail rather than being accepted.

## Method review and experimental scope

V1 retains the existing scientific methods, seeds, noise, observations, objectives,
20-start optimizer, parameter bounds, stopping tolerances and acceptance rules.
The single fit uses RK45 with forward sensitivities; the ensemble uses four-substep
zero-order-hold matrix exponentials with Frechet sensitivities, 64 seeds beginning
at 20260801, and four workers. Replaying the generators performs fresh fits; v1 does
not copy historical expected results into the generated outputs. Fixing these
methods gives a reproducible starting point for future method comparisons.

The [portability review](linux-migration.md) and
[numerical diagnostic](linux-portability-diagnosis.json) remain part of its evidence.
The single-fit solver has measured integration noise up to 3.742e-7 against two
independent references, exceeding its optimizer stopping scale. The ensemble uses
a different integration method and its platform drift is not explained solely by
that issue. These limitations are accepted for a *documented exploratory baseline*,
not as evidence that the fitted parameters have that many accurate digits.
No solver improvement is silently mixed into v1. Discontinuity-aware integration,
validated closed-form sensitivities, error-consistent stopping criteria, and refits
belong in an explicitly compared successor baseline.

Stable headline classifications (64/64 chain training selections, 23/64 triangle
held-out improvements, 29/64 shortcut-boundary fits) do not establish family-wide
identifiability, uniqueness of the interior, physical discovery or empirical
validation. Parameter sensitivity, noise/model robustness and independent data
remain meaningful next research constraints.

## Verification contract

```sh
.venv/bin/python -I -B tools/verify_linux_baseline.py --all --workers 4
```

The command verifies source hashes, the existing runtime and development gates,
then generates science and the Atlas twice in an isolated copy. It requires:

- no source-checkout mutation;
- exact equality between all 57 outputs in both runs;
- exact equality to every v1 output hash, with no missing or extra outputs;
- byte-identical historical Atlas HTML;
- successful existing HTML/PDF structural, font, formula and accessibility checks.

The verifier has no record/update-baseline mode. New bytes require a reviewed
successor; the expected record must not be regenerated to make a failure green.
Negative controls reject changed/missing/extra outputs and nonrepeatable replay.

Historical numerical comparison still runs at rtol=atol=1e-12 and exact discrete
outcomes. Its **FAIL** is recorded explicitly and separately from the Linux byte
verdict in `tmp/linux-baseline-verification.json`. The original strict route,
`tools/verify.py --all --workers 4`, still fails on that drift. No tolerance changed.
The Linux CI definition now invokes the v1 gate; GitHub CI itself remains unexercised.

## PDF layout revision

The Linux-only `--linux-layout --no-identity` print path removes nested multi-column
contents and starts all 16 references on a dedicated final page with their rights
paragraph. The flag cannot generate a publication identity. Default historical
rendering behavior and checked-in HTML, stylesheet, manuscript and PDF are retained.
All 27 Linux pages were visually reviewed. The existing PDF inspector passes;
PDFium found no glyph outside physical page bounds. With the exact leading page
number removed, pypdf extracts the same 43,526 non-whitespace body-character
inventory from Linux and Windows, with none missing or extra. This differs from
the earlier PDFium character total because the extractors represent math differently;
the comparisons are always between documents using the same extractor.

The contents page is readable at body-text size. The final page has its heading,
all references and rights together; no isolated rights page remains. Scientific
text is unchanged and HTML bytes are identical. Page count remains 27 versus the
historical 28. These are local unpromoted review artifacts.

## Provenance and privacy

Source hashes, output hashes, runtime identity and the Git commit/manifest together
identify the candidate. Task commits use the owner-approved public noreply identity;
original authorship, citations and licenses are retained. The local old-identity
backup is not part of the branch and must not be shared via an all-refs/mirror push.
OpenAI Codex assisted with implementation, diagnostics and review; this is not
independent peer review. No credentials, security settings or publication records
were changed. The previously documented scanner-hardening and optional provenance
minimization proposals remain separate from this numerical baseline.
