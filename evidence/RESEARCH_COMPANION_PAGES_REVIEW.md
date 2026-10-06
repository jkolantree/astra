# Research companion Pages review

The research companion is an unpromoted draft. Admission v2 lists the exact
40 companion files and three supporting notices. Historical admission v1, its
schema, core v1.0.7 and all four existing release-route contracts are unchanged.
The refinement below affects only the new, still-unpublished companion review
gate introduced in this draft PR; it does not remove an existing repository
security or release-integrity gate.

The manual, main-only Pages workflow retains its release identity checks. The
assembler rejects extra companion files, changed bytes, links, collisions and
changes to pre-existing site files. Identical existing notices may be reused.
All 32 supplied research payload files remain byte-identical.

## Actual review and coverage

The owner inspected the delivered preview in their own browser on their own
device and accepted its general appearance. Missing images were traced to
extracting the two ZIPs into separate folders; combining the contents fixed
them. No image-path or image-byte change was needed.

[The public review record](research_companion_pages_review_v1.json) records
that limited, owner-reported acceptance. It contains no private screenshot,
conversation quotation, conversation identifier, device identifier or personal
metadata. Screenshots are not a publication requirement and must not be added
merely to satisfy this gate.

Detailed coverage is recorded separately as `passed`, `failed` or `not-tested`:
layout at desktop/mobile sizes, keyboard/focus, reduced motion, media playback,
console/network behavior and assistive technology. Here `not-tested` means no
specific result is documented; general positive feedback does not establish
those results. These fields are currently all `not-tested`. They do not demand
that the owner personally certify accessibility conformance. Additional formal
audits beyond this recorded coverage are not an implicit publication checklist.

The executor's earlier navigation was blocked by administrator policy. No
alternate host, browser, content injection or security-setting change was used.
The owner's separate manual inspection does not authorize an executor bypass.

## Mandatory publication conditions

Production assembly still requires:

1. Exact admitted source and asset bytes, safe paths, preserved existing files
   and the unchanged release-integrity checks.
2. Explicit manual visual acceptance bound to the rendered content reviewed.
3. Explicit final publication approval bound to the current assembly candidate.

Unperformed specialist checks remain disclosed and do not become false passes.
A declared failed check blocks publication until addressed. The production
command returns coverage statuses in its result, so its success is not presented
as an all-green accessibility or browser-testing certification.

Owner authorization for Pages publication is **recorded**, based on the
publication request and acceptance of the unchanged delivered preview. This is
separate from general visual acceptance and does not invent specialist results.
The command with `--require-reviewed` can admit this exact candidate after its
integrity and review checks pass. A successful exact-head CI result and the
owner's merge remain independent requirements before deployment; this record
does not authorize an autonomous merge or workflow dispatch.

## Two byte identities

The final-publication candidate digest covers admission (all shell, companion
and notice bytes), assembly/admission/link-checking code, workflow and applicable
schemas. The review record and root manifest are excluded to avoid cycles.
Changing the candidate requires a fresh final publication decision.

The separate visual-content digest covers the admitted HTML, CSS, SVG, images,
animations, PDF/DOCX downloads and generated explorer redirect. Inline explorer
JavaScript and fixtures are covered by the HTML bytes. Operational Markdown and
gate code are excluded from this narrower digest but remain covered by admission
and the final-publication candidate digest. Thus the owner's actual acceptance
can remain valid through a gate/documentation-only refinement when the rendered
content is proven unchanged. A rendered-content change invalidates it.

The record also identifies the delivered preview's original candidate digest.
The recorded visual-content digest was compared against the exact delivered
preview inventory, not inferred from feedback about a different rendering.

After source changes, regenerate admission and inspect both identities:

```text
python -I -B tools/build_pages_admission.py
python -I -B tools/assemble_research_companion_pages.py --candidate-digest
python -I -B tools/assemble_research_companion_pages.py --visual-content-digest
```

Do not copy old approval to changed bytes or mark unperformed coverage passed.
The JSON record is an explicit human-review statement, not software proof of
consent or quality. No screenshot upload is needed to complete that statement.

## Remaining production steps

Review the exact final diff and its local checks, obtain a successful exact-head
CI result, and present the final PR for the owner's merge through the normal
process. Publication authorization is already recorded; it must not be treated
as a completed CI run or a substitute for the owner's merge. The existing manual
Pages workflow remains a separate deployment action. No autonomous merge,
workflow dispatch or deployment is performed by this gate refinement.

Source-only assembly is available for inspection. It does not reconstruct the
historical release editions; the full workflow obtains and verifies those
release assets independently. The new schema endpoints are reserved repository
contracts and are not published by this bounded companion assembly.

## Scientific limits

The reservoir display browses retained synthetic samples; it is not a live ODE
solver. Pattern/tracer motion and filament geometry are prescribed. Quantum
recurrence remains prose only because final-source equations and conventions
have not been independently verified here. No empirical validation is claimed.
