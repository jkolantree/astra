# Public data schemas

These Draft 7 JSON Schemas describe the machine-readable records shipped by
SPPT/ASTRA. Their canonical URLs are served by the project reading site at
`https://jkolantree.github.io/astra/schemas/`.

Schema names carry an independent revision (`v1`). A scientific release may
therefore update from, for example, v1.0.6 to v1.0.7 without changing a schema
whose contract is unchanged. Published schema revisions are immutable; a
breaking schema change requires a new schema filename.

The release verifier validates each schema-declaring tracked metadata or audit
record against its declared schema and verifies that the public URL maps to a
shipped schema file. Scientific data serializations retain their separate
project-specific invariant checks.
