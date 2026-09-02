# Dark-Medium Response Atlas v0.1.0 release notes

## Publication identity

- Title: *Dark-Medium Response Atlas v0.1.0 - Path, Compensation, Memory, and
  Observation*
- Publication line: supplemental working paper and methods proposal
- Version: `0.1.0`
- Tag: `dark-medium-response-atlas-v0.1.0`
- Versioned route:
  <https://jkolantree.github.io/astra/resources/dark-medium-response-atlas/v0.1.0/>
- GitHub object: immutable prerelease, not GitHub Latest

## What this edition contributes

The Atlas begins with response rather than ontology. It asks how a hidden
sector would store path history, compensate parameters, cross a phase
boundary, and appear through a finite observation operator. Its central
analytic benchmark shows how charge-conjugation symmetry removes mixed
stress-current response at linear order and how an ideal neutral equal-pair
fluid separates into Jeans-like and Langmuir-like branches under additional
declared assumptions.

Three cases sharpen the inference method without claiming a shared physical
mechanism: particle creation after a restored cosmological control,
barrier-prefactor compensation in microwave synthesis, and delayed cometary
activity after a model-supported orbital perturbation.

## Status and nonclaims

This work is not peer reviewed. It does not detect dark matter, identify dark
matter with plasma or aether, establish a preferred frame, promote an ASTRA
core claim, validate an empirical hidden-sector model, publish a DOI, or claim
priority. Proposed methods remain proposed until independent comparison and
held-out testing.

## Canonical document commands

Run these only from the repository root under the exact runtime in
`RUNTIME.json`:

```text
python -I -B tools/build_dark_medium_response_atlas_documents.py
python -I -B tools/check_dark_medium_response_atlas_html.py
python -I -B tools/inspect_dark_medium_response_atlas_pdf.py
python -I -B tools/render_dark_medium_response_atlas_pdf.py
```

The first document-generation command must follow the applicable artifact
operation marker in the publication environment. The renderer command writes
only to `tmp/` and produces page images for complete visual inspection.

## Release assets

The release controller admits exactly five assets:

1. `dark-medium-response-atlas-v0.1.0.html`
2. `dark-medium-response-atlas-v0.1.0.pdf`
3. `dark-medium-response-atlas-v0.1.0-source.tar.gz`
4. `SHA256SUMS`
5. `dark-medium-response-atlas-v0.1.0-release-identity.json`

The package-local ledgers, citation metadata, rights map, and release
specification travel inside the deterministic source archive.
