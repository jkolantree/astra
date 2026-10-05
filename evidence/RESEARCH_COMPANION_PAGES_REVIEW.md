# Research companion Pages review

The research companion is an unpromoted draft. Admission v2 lists the exact
40 companion files and three supporting notices. The preserved v1 admission
record and schema describe the preceding Pages boundary; the current builder
and checker use v2. Core v1.0.7, historical editions and the four existing
release-route contracts are unchanged.

The manual, main-only Pages workflow retains its release identity checks. It
adds the admitted companion at
`resources/sppt-scm-research-companion/draft-v0.1.0/` and an `/explore/` redirect.
The assembler rejects extra companion files, changed bytes, links, collisions
and changes to pre-existing site files. Identical existing license notices may
be reused. The original 32-file research payload is copied byte for byte.

## Current review boundary

The executor's browser navigation received `ERR_BLOCKED_BY_ADMINISTRATOR`.
No alternate host, scheme, browser, page-content injection, policy flag or
security-setting change was attempted for the explorer. The repository already
has pinned Chromium checks for existing reading-room cover geometry and narrow
layouts, but those checks do not review this explorer or provide its screenshot
evidence. Their existence does not authorize rerouting the denied target.

To complete visual review, the platform administrator must explicitly permit a
browser surface for this candidate, or the owner must inspect the candidate on
an already permitted browser and supply the review evidence. Document the
permitted surface before using it. Do not change browser policy or add a CI
browser route to evade the denial.

The required review covers desktop and mobile layout, all slider/select/reset
controls, keyboard focus and ordering, reduced-motion preference, native video
play/pause and posters, console and network behavior, and an assistive-technology
pass. Inspect the reading-room links and both the `/explore/` entry point and
versioned destination. Record observed limitations and fixes. Static source,
Node callbacks and standalone media inspection do not satisfy this gate.

## Exact-candidate gate

[The review record](research_companion_pages_review_v1.json) is pending. The
production command refuses it. It must not be marked approved until actual
review and final publication approval have occurred.

After source changes, regenerate admission with:

```text
python -I -B tools/build_pages_admission.py
python -I -B tools/assemble_research_companion_pages.py --candidate-digest
```

The digest covers admission (which pins the shell, companion and notices),
assembly/admission/link-checking code, workflow and applicable schemas. The
review record and root manifest are excluded to avoid a self-reference cycle.
A changed candidate invalidates an earlier review.

Use `tools/check_pages_admission.py --copy-to ARTIFACT_DIRECTORY` followed by
`tools/assemble_research_companion_pages.py --site ARTIFACT_DIRECTORY` to prepare
an isolated source review artifact. This does not reconstruct the historical
release editions; the full Pages workflow obtains and verifies those releases.
No review or deployment authorization is conferred by this diagnostic command.

After permitted inspection, keep privacy-reviewed PNG screenshots and a written
Markdown review under `evidence/research-companion-browser-review/`. Record each
file's path, byte count and SHA-256 in the review record, identify the permitted
surface, record completed checks and the final publication decision, and bind
them to the candidate digest. The production command uses `--require-reviewed`;
it checks the exact digest and evidence bytes, requires screenshots and a
written report, and requires every review check to pass. This records a human
review; it is not a claim that software can prove visual quality or consent.

Only after parent review of the final candidate may the existing manual Pages
workflow be dispatched through its normal main-branch process. No merge,
workflow run, release, deployment or security-setting change has been performed
by preparing this integration.

## Scientific limits

The reservoir display browses retained synthetic samples; it is not a live ODE
solver. Pattern/tracer motion and filament geometry are prescribed. Supplied
animations remain paused until activated. Quantum recurrence remains a prose
chapter: final-source equations and conventions have not been independently
verified here, so no numerical chapter or experimental replay is claimed.
