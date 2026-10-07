# SPPT/ASTRA Integrated Core 1.1.0-alpha.1

This is an unpublished local successor candidate. Its proposed tag is
`astra-integrated-core-v1.1.0-alpha.1`. Source, runtime, Pages and publication
admission remain false. Historical root version, citation, release specification
and workflows retain their separate v1.0.7 authority. The root Python package is
not relabeled; `version.py` is this candidate's explicit version entrypoint.

`RELEASE_SPEC.json` defines 69 fresh outputs: 61 scientific/report/diagram outputs
and eight reading outputs. Two input-only productions must match all 69 bytes and
both 194-file Pages trees. The Pages plan has 143 retained routes and 51 versioned
integrated-core routes. The library override changes links to those versioned
assets. The old 57-output source gate still rejects this successor tree; it is
not silently weakened or treated as successor acceptance.

Run the following from this package directory, substituting explicit approved
paths and the externally supplied source-record digest. These commands create no
tag, commit, release or admission. No installer runs. The work directory must not
exist, and must be outside the source tree.

```sh
"$SCIENCE_PYTHON" -I -B version.py
"$SCIENCE_PYTHON" -I -B produce.py \
  --source-record "$SOURCE_RECORD" --record-sha256 "$SOURCE_RECORD_SHA256" \
  --science-python "$SCIENCE_PYTHON" --wki-python "$WKI_PYTHON" \
  --browser "$BROWSER" --work "$NEW_WORK_DIRECTORY" \
  --retained-preview "$RETAINED_PREVIEW"
"$SCIENCE_PYTHON" -I -B verify_successor.py \
  --source "$SOURCE_DIRECTORY" --record "$SOURCE_RECORD" \
  --record-sha256 "$SOURCE_RECORD_SHA256" \
  --science-python "$SCIENCE_PYTHON" --wki-python "$WKI_PYTHON" \
  --browser "$BROWSER" --production-root "$NEW_WORK_DIRECTORY" \
  --production-receipt "$PRODUCTION_RECEIPT" \
  --production-receipt-sha256 "$PRODUCTION_RECEIPT_SHA256"
```

The verifier checks exact source scope, original payload and claim bindings,
Python executables/libraries, full installed environments (including native
libraries and fonts), the approved Chromium tree, both productions and every
Pages destination. The source and production records are detached local evidence,
not signatures or proof of author identity. No signing key is created.

For a future publication, first obtain explicit owner approval of the final
source/runtime/Pages successor contracts, exact assets, appearance and file-level
rights. Then a separate reviewed workflow for `astra-integrated-core-v*` must bind
the final committed source and those approvals. The disabled workflow sketch in
`../../integrated-edition-proposal/review-024/` remains a proposal. Do not route
this candidate through historical `v*` gates or repurpose the companion tag.

See [release notes](RELEASE_NOTES.md), [citation](CITATION.cff),
[rights boundary](LICENSE_BOUNDARIES.md), and the versioned
[reading source](../../../manuscript/integrated-core-v1.1.0-alpha.1/README.md).
