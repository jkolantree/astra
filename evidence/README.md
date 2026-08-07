# Evidence boundary

This directory belongs to the current SPPT/ASTRA **v1.0.6 reference package**.
Separately versioned resources under `resources/` retain their own evidence and
verification records and do not inherit this release's status.

`source_test_results.txt` is the 99-byte transcript supplied with the source candidate. It states that 15 tests passed, but a saved transcript is not execution evidence and is not counted as an independent verification run.

Current core verification is produced by executing `python -I -B tools/verify.py --all --workers 4` from a clean, hash-locked environment. The CSV and JSON ensemble files are alternate serializations of the same 64 realizations, not independent evidence.
