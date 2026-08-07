# Public-Package Audit for ASTRA Framework v0.3.0

Audit date: 6 August 2026
Scope: normalized pre-publication package tree
Series: *Earth Is the Instrument* framework series, separate from core SPPT/ASTRA v1.x

## Publication status

The normalized content is suitable for a bounded public release only after the final package manifest, checksums, archive, and outer sidecars are regenerated and the full fail-closed verifier passes against those exact bytes.

Use a namespaced immutable tag such as `earth-instrument-framework-v0.3.0`. Do not use the bare tag `v0.3.0`, replace the core SPPT/ASTRA v1.x latest release, or describe this package as superseding that series.

## Preserved authored artifacts

This public normalization does not revise the authored manuscript text or the released PDFs. It preserves:

- `source/main.tex` and the modular manuscript sources;
- `source/ASTRA_Framework_v0.3.0_Earth_Is_The_Instrument.md`;
- the main working-paper PDF;
- the public ground-reading PDF;
- the static audit-form PDF;
- the producer-generated verification report and its historical logs.

Changes are limited to release metadata, public identifiers and mappings, documentation, validation code, and tests.

## Naming and AI provenance

The authored main paper already records language-model assistance and Jacko T.'s
responsibility for the work. The public release metadata now names OpenAI's
ChatGPT as the assisting product and records the author's stated naming
inspirations: the Kansas motto *Ad Astra Per Aspera* and OpenAI's 1 August 2026
public description of an internal version of Astra as "our next major model."
These are provenance disclosures, not scientific evidence, independent review,
or endorsement by OpenAI or the State of Kansas.

The preserved authored PDFs and manuscript sources are not rewritten to add
this release-level wording. Their existing model-assistance disclosure remains
in place, while the resource guide, Pages landing page, release notes, and
offline package README carry the fuller naming and independence statement. The
"ASTRA Coherence Cell" is the author's role-based review architecture, not a
separate institution, employer, committee, or roster of external reviewers.

## Verified strengths

- The supplied archive was structurally safe: no path traversal, absolute members, symlinks, encryption, filename collisions, CRC errors, or duplicate members were found.
- The supplied internal manifest and checksum rows matched the original supplied package before normalization.
- Independent exact algebra reproduced the constant Keller-map determinant, the declared three-point rational collision, the released finite-field profiles, the sixth-cyclotomic multiplicity pattern, and the declared bounded perfect-power search result.
- The claim, source, and visual CSV/JSON pairs are machine-readable and have stable unique identifiers.
- Every released visual has a declared class, creator, source, license, dimensions, crop status, modifications, caption, and alternative text.
- The scientific prose consistently distinguishes calibration examples from proof of a shared mechanism and finite computation from an unrestricted theorem.

## Required corrections incorporated in the normalized tree

- stale v0.2 license attribution was corrected to v0.3.0;
- public series/version identity was separated from core SPPT/ASTRA v1.x;
- drafting-library identifiers were replaced by package-relative paths or explicit public aliases;
- source-to-claim mappings were regenerated from claim-side source keys;
- arithmetic prime-domain validation now rejects booleans, nonintegers, composites, nonpositive values, and the bad even reduction where applicable;
- benchmark worker help now matches the actual multiprocessing implementation;
- runtime, dependency, font-license, accessibility, and publication-gate records were added.
- container-specific absolute build paths were replaced by package-relative/configurable script roots and neutral `<build-root>` markers in retained text preflight records; substantive results were unchanged.

## Verification authority

`verification/verify_v030.py` and `ASTRA_v0.3.0_Verification_Report.*` are retained as producer-generated historical records. The original verifier contains fixed verdict language and does not derive every gate from a current failing process, so it is not the public release gate.

`verification/verify_publication_v030.py` is the public fail-closed gate. It:

- exits nonzero on every required failed check;
- checks version and release metadata;
- compares each CSV ledger with its JSON twin;
- enforces unique identifiers and exact bidirectional claim/source mappings;
- validates required visual metadata and referenced visual assets;
- runs the package tests in a subprocess and requires a zero exit status;
- inspects required PDFs without claiming semantic mathematical accessibility;
- checks the final manifest and SHA-256 inventory unless explicitly invoked with `--content-only`.

The `--content-only` option exists solely for pre-manifest staging. It is not a release pass.

## Accessibility findings and limits

Positive features include document language, tagged structure, bookmarks, internal and external links, embedded fonts, and alternative text on the released figures.

The PDFs are not claimed to conform to PDF/UA or WCAG:

- mathematical expressions do not have complete semantic Formula tagging or MathML-equivalent alternate text;
- the retained main LaTeX log contains structure warnings;
- the bundled main-PDF text extraction contains replacement characters in several equations;
- the one-page audit form has no AcroForm fields and is a printable/static worksheet;
- the original report's broad accessibility PASS is a producer conclusion, not independent certification.

Readers needing exact mathematical extraction should use the authored Markdown/TeX sources alongside the PDF.

## Scientific and source-validation limits

- Source-ledger completeness is not independent replication of 85 external sources.
- A `source_support_verdict` value is release metadata, not proof that a citation entails a claim.
- External URLs and publication status can change after release.
- The synthetic benchmark is favorable by design and does not estimate a general planetary false-positive rate.
- The exact arithmetic counterexample is a calibration of local-versus-global reasoning; it does not make physical systems number-theoretic.
- Finite-field reductions and bounded searches do not prove unrestricted characteristic-zero or Diophantine claims.

## Final release sequence

1. Run `python -m pytest` and require all tests to pass.
2. Run `python verification/verify_publication_v030.py --content-only` and require success.
3. Regenerate `RELEASE_MANIFEST.txt` and `SHA256SUMS.txt` from the final normalized tree.
4. Run `python verification/verify_publication_v030.py` and require success.
5. Build the archive from that same tree, generate outer SHA-256 and verification sidecars, and independently verify the extracted archive.
6. Publish once under the namespaced immutable v0.3.0 tag and versioned reading-room path.

Any content change after step 3 begins a new candidate and requires steps 1–5 again.

## Public-normalization validation result

- Package-isolated regression tests: **29 passed**.
- Fail-closed content gate: **83 of 83 checks passed** with status `CONTENT_GATE_PASS_NOT_RELEASE_PASS`.
- Full release gate before manifest regeneration: **expected failure** on exactly three release-integrity checks—manifest inventory, checksum inventory, and stale checksum values.
- Authored PDF and manuscript-source hashes matched the frozen pre-normalization values.
- No opaque drafting-library file identifier, user-profile path, or container-specific absolute build-root prefix remains in the public text surface.

This is a successful pre-manifest result, not authorization to publish stale release bytes.

## Final normalized release result

The publication controller then regenerated the package identity files and
ran the default fail-closed gate against the final tree: **90 of 90 checks
passed** with status `RELEASE_GATE_PASS`. A second deterministic archive build
produced the same bytes.

- Archive: `ASTRA_Framework_v0.3.0_Dual_Rent_Arithmetic_Seams.zip`
- Bytes: `35,343,563`
- Members: `341`
- Uncompressed bytes: `43,018,712`
- SHA-256: `b2a1072c14f1afff43a161b57620cdd2f6ad19b03884e7b5d8fbdd023333e09d`
- Inner manifest rows: `339`
- Inner checksum rows: `340`
- Independent extraction replay: no missing or extra files, no hash mismatches,
  and exact manifest coverage

This outer publication record can name the completed archive identity without
creating a self-reference inside that archive. Publication remains scoped to the
namespaced supplemental tag and does not alter SPPT/ASTRA v1.0.6.
