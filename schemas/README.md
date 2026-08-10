# Public data schemas

These Draft 7 JSON Schemas describe the machine-readable records shipped by
the SPPT/ASTRA reference-release line, currently **v1.0.7**. Their canonical
URLs are served by the project reading site at
`https://jkolantree.github.io/astra/schemas/`.

Supplemental resources use the namespaced release schemas
`supplemental-release-spec-v1.schema.json` and
`supplemental-release-identity-v1.schema.json`; they do not change the core
SPPT/ASTRA release contract.

The maintenance `claim-source-coverage-v1.schema.json` describes the
structured claim/source audit under `evidence/`. It is an audit-layer schema,
not a replacement for `claim-matrix-v1.schema.json`, and it does not promote
source-asserted or structurally linked material to independently verified
evidence. The schema is available through the versioned Pages build when the
v1.0.7 release-bound deployment completes.

Schema names carry an independent revision (`v1`). A scientific release may
therefore update from, for example, v1.0.6 to v1.0.7 without changing a schema
whose contract is unchanged. Published schema revisions are immutable; a
breaking schema change requires a new schema filename.

The release verifier validates each schema-declaring tracked metadata or audit
record against its declared schema and verifies that the public URL maps to a
shipped schema file. Scientific data serializations retain their separate
project-specific invariant checks.
