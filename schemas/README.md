# Public data schemas

These Draft 7 JSON Schemas describe the machine-readable records shipped by
the SPPT/ASTRA reference-release line, currently **v1.0.7**. Their canonical
URLs are served by the project reading site at
`https://jkolantree.github.io/astra/schemas/`.

Supplemental resources use the namespaced release schemas
`supplemental-release-spec-v1.schema.json` and
`supplemental-release-identity-v1.schema.json`; they do not change the core
SPPT/ASTRA release contract.

The separately versioned
`supplemental-release-spec-v2.schema.json` and
`supplemental-release-identity-v2.schema.json` contracts admit a stable
resource version such as `0.1.0` while still requiring its GitHub object to be
a prerelease that cannot displace the stable core line. Existing v1 schemas
and their consumers remain unchanged.

The maintenance `claim-source-coverage-v1.schema.json` describes the
immutable v1.0.7 claim/source audit under `evidence/`. It is an audit-layer schema,
not a replacement for `claim-matrix-v1.schema.json`, and it does not promote
source-asserted or structurally linked material to independently verified
evidence. The schema is available through the versioned Pages build when the
v1.0.7 release-bound deployment completes.

The unpromoted core-integrity M1 overlay declares the distinct candidate schema
`claim-source-coverage-overlay-m1.schema.json`. That new filename preserves the
published v1 schema bytes and makes the local candidate contract explicit. Its
canonical Pages URL is reserved but is not claimed live until a separately
authorized publication promotes that schema; local validation uses the shipped
candidate file.

The historical Dark-Medium Response Atlas admission record uses
`dark-medium-response-atlas-successor-overlay-s1.schema.json`. The live
publication-successor record uses the distinct
`dark-medium-response-atlas-publication-successor-overlay-s2.schema.json` and
owns only the exact Atlas package and Pages admission it names. The two
contracts deliberately do not transfer authority between older and current
repository bases.

Schema names carry an independent revision (`v1`). A scientific release may
therefore update from, for example, v1.0.6 to v1.0.7 without changing a schema
whose contract is unchanged. Published schema revisions are immutable; a
breaking schema change requires a new schema filename.

The release verifier validates each schema-declaring tracked metadata or audit
record against its declared schema and verifies that the public URL maps to a
shipped schema file. Scientific data serializations retain their separate
project-specific invariant checks.
