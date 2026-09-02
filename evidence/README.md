# Evidence boundary

This directory belongs to the current SPPT/ASTRA **v1.0.7 reference package**.
Separately versioned resources under `resources/` retain their own evidence and
verification records and do not inherit this release's status.

`source_test_results.txt` is the 99-byte transcript supplied with the source candidate. It states that 15 tests passed, but a saved transcript is not execution evidence and is not counted as an independent verification run.

Current core verification is produced by executing `python -I -B tools/verify.py --all --workers 4` from a clean, hash-locked environment. The CSV and JSON ensemble files are alternate serializations of the same 64 realizations, not independent evidence.

`claim_source_coverage_v1.0.7.json` is the immutable deterministic maintenance
record shipped with v1.0.7. The historical
`claim_source_coverage_v1.0.6_draft.json` remains available as v1.0.6 provenance.

`claim_source_coverage_v1.0.7_maintenance_overlay_m1.json` is a separate,
unpromoted core-integrity M1 source-repair overlay. It binds the candidate source
projection while excluding its manifest and its own bytes to avoid self-reference;
tracked-manifest and Git-archive checks close those two identities after commit.
Its distinct candidate schema is
`schemas/claim-source-coverage-overlay-m1.schema.json`. The overlay does not amend
the v1.0.7 record, release assets, Pages editions, tag, or citation identity.

`dark_medium_response_atlas_successor_overlay_s1.json` preserves the exact
historical source-admission candidate created against an earlier repository
base. Its bytes and the admitted `resources/dark-medium-response-atlas/draft-v0.1.0/`
package are historical evidence and are not regenerated against the live tree.

`dark_medium_response_atlas_publication_successor_overlay_s2.json` is the
separately named publication-successor record for the final Atlas v0.1.0
package on the current repository line. It binds the exact source projection,
package roster, publication outputs, and Pages admission without amending the
historical S1 record, the core M1 overlay, stable v1.0.7, or the separate
v1.0.8 candidate. Its authority is limited to this supplemental publication;
it carries no peer-review, empirical-validation, priority, DOI, core-claim, or
core-release authority.

These records add machine-readable path hashes, source-link kinds, locator
precision, and explicit unknown fields without promoting structural links to
verified entailment. External entailment, source-record versions, retrieval
dates, and claim-specific execution identities remain unknown until independently
entered and verified; neither record is a sentence-level completeness proof or
independent peer review.
