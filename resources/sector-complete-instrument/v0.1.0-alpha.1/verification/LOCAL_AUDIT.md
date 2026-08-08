# Local integration audit

Date: 2026-08-07
Status: `GITHUB_NAMESPACED_ALPHA_RELEASE` for a namespaced synthetic methods
preview; this status does not promote any dark-matter interpretation or claim
peer review.

## Identity and scope

- Attached ZIP SHA-256: `b0b9606b3c64c91c97a92e18e4e4a5bdb7519ed4d15664a33f864e420f32c1b6`.
- Companion text SHA-256: `0dc731eaac8ffadfd9105afd7ac944a5a98274d8b26462547343bc16d30c3675`.
- The ZIP contains 70 members; unsafe path checks found no absolute, drive,
  traversal, or backslash paths. Four `.pytest_cache` members and bytecode
  members were excluded from the tracked resource.
- The resource is under `resources/sector-complete-instrument/v0.1.0-alpha.1`.
  It is not a core `v*` release, not an Earth v0.3.0 successor, and not a
  core or Earth-line release. The public tag is
  `sector-complete-instrument-v0.1.0-alpha.1`; no Pages, DOI, or Zenodo record
  is claimed.

## Repairs made

1. The typed record now emits JSON-compatible arrays, an object-valued
   conservation/exchange ledger, unresolved-sector bounds, and an
   identifiability object accepted by the schema.
2. The benchmark sets Matplotlib to `Agg`, writes LF-normalized UTF-8 JSON/CSV,
   and records finite/log survival information rather than serializing
   non-standard `-Infinity` JSON.
3. The out-of-set control now states that the best of four pure candidates was
   selected before the diagnostic and records a conservative selection-adjusted
   upper bound. The value underflows to zero for this toy case; this is not an
   exact globally calibrated p-value.
4. The source and claim ledgers add three typed magnet records: Amaral's
   published B-L null search, Ji's LeMaMa metrology, and Tian's accepted
   spin--spin--velocity record. They remain observation/certificate context,
   not SPPT transport edges or dark-matter identity evidence.

## Local execution

- Runtime identity used for the release replay: CPython 3.12.10 from the
  frozen repository runtime, with NumPy 2.3.5, SciPy 1.18.0, Matplotlib 3.11.1,
  pytest 9.1.1, and jsonschema 3.2.0.
- Resource test file: **29 passed**. The root integration contract adds five
  checks; together the focused command reports **34 passed**.
- Benchmark replay: mechanically replayed with the frozen CPython 3.12.10
  runtime and locked NumPy 2.3.5, SciPy 1.18.0, and Matplotlib 3.11.1. The
  output reports local Fisher rank 2, complete rank
  3, mutual information 1.343487321503841 versus 1.853974149791973 bits,
  classification accuracy 0.7525 versus 1.0, and a selection-adjusted
  diagnostic bound of 0.0 after underflow.
- Frozen regenerated JSON SHA-256:
  `c01673b4228173928acf90798644181ca6ca4dbfed6a8d6f05458db28a31b031`.
- Two consecutive benchmark runs produced identical SHA-256 values for the
  JSON, checksum, configuration, and four CSV outputs. The claim is limited
  to these text outputs in this runtime; plot bytes are not claimed portable
  across graphics stacks.
- The namespaced resource is registered in the repository allowlist; the
  repository contract passes for 176 public files and the root tracked manifest
  was regenerated mechanically. A final `git diff --check` is run before handoff.

## Document and source limitations

- The supplied canonical PDF, tagged PDF, and DOCX were inspected for text,
  metadata, and structure, but their original bytes are not part of this
  tracked resource and the original PDF/DOCX render context is not available
  for a release replay. Their producer reports claiming complete visual and
  accessibility passes are retained as producer assertions, not promoted to
  verified evidence.
- Current metadata/abstract checks were made against the primary records on
  2026-08-07. No raw experiment, instrument calibration, full likelihood, or
  source-data replay was performed. Tian's APS item is explicitly an accepted
  record, not a version-of-record verification.
- Synthetic agreement remains synthetic methods evidence. It is not evidence
  for real duality defects, hidden sectors, dark matter, planetary evolution,
  or an empirical ASTRA/SPPT validation.
- The 12 tracked PNG figures were inspected for embedded metadata; the eight
  regenerated plots contain only Matplotlib software/DPI fields, and no local
  path, email, or account identifier was observed.

## External state

No GitHub, GitHub Pages, GitHub Release, Zenodo, DOI, tag, branch, or other
external state was changed. Immutable SPPT/ASTRA v1.0.6 and *Earth Is the
Instrument* v0.3.0 artifacts remain untouched.
