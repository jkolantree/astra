# Evidence boundary

This directory belongs to the current SPPT/ASTRA **v1.0.7 reference package**.
Separately versioned resources under `resources/` retain their own evidence and
verification records and do not inherit this release's status.

`source_test_results.txt` is the 99-byte transcript supplied with the source candidate. It states that 15 tests passed, but a saved transcript is not execution evidence and is not counted as an independent verification run.

Current core verification is produced by executing `python -I -B tools/verify.py --all --workers 4` from a clean, hash-locked environment. The CSV and JSON ensemble files are alternate serializations of the same 64 realizations, not independent evidence.

`claim_source_coverage_v1.0.7.json` is the current deterministic maintenance
record for the v1.0.7 claim and source ledgers. The historical
`claim_source_coverage_v1.0.6_draft.json` remains available as v1.0.6 provenance.
The current record adds machine-readable path hashes, source-link kinds, locator
precision, and explicit unknown fields without changing immutable historical
assets. External entailment, source-record versions, retrieval dates, and
claim-specific execution identities remain unknown until independently entered
and verified; this record is maintenance evidence, not a sentence-level
completeness proof or independent peer review.
