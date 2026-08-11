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

These records add machine-readable path hashes, source-link kinds, locator
precision, and explicit unknown fields without promoting structural links to
verified entailment. External entailment, source-record versions, retrieval
dates, and claim-specific execution identities remain unknown until independently
entered and verified; neither record is a sentence-level completeness proof or
independent peer review.
