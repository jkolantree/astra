"""Strict Draft 2020-12 validation for the local bridge protocol.

The repository's v1.0.6 runtime intentionally locks ``jsonschema==3.2.0``
for an existing dependency.  That package does not contain the Draft 2020-12
metaschema.  This helper therefore refuses the old ``validator_for`` fallback:
it either runs a real Draft 2020-12 validator or reports an explicit,
machine-readable environment limitation.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version as distribution_version
import json
from pathlib import Path
from typing import Any, Literal


ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = ROOT / "bridge_protocol.schema.json"
INSTANCE_PATH = ROOT / "example_protocol.json"
DRAFT_2020_12_SCHEMA = "https://json-schema.org/draft/2020-12/schema"
ValidationStatus = Literal["valid", "invalid", "environment_limited"]


@dataclass(frozen=True, slots=True)
class SchemaValidationResult:
    """A strict validation result that never conflates a missing validator with pass."""

    status: ValidationStatus
    schema_path: str
    instance_path: str
    declared_schema: str | None
    validator: str | None
    errors: tuple[str, ...] = ()
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "schema_path": self.schema_path,
            "instance_path": self.instance_path,
            "declared_schema": self.declared_schema,
            "validator": self.validator,
            "errors": list(self.errors),
            "reason": self.reason,
        }


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not load JSON from {path}: {exc}") from exc


def validate_protocol_schema(
    schema_path: Path = SCHEMA_PATH,
    instance_path: Path = INSTANCE_PATH,
) -> SchemaValidationResult:
    """Validate an instance only with a genuine Draft 2020-12 implementation.

    ``environment_limited`` is deliberately distinct from ``invalid`` and
    ``valid``.  In particular, this function never invokes ``validator_for``
    when the installed package lacks ``Draft202012Validator``.
    """

    schema = _load_json(schema_path)
    instance = _load_json(instance_path)
    declared_schema = schema.get("$schema") if isinstance(schema, dict) else None
    if declared_schema != DRAFT_2020_12_SCHEMA:
        return SchemaValidationResult(
            status="invalid",
            schema_path=str(schema_path),
            instance_path=str(instance_path),
            declared_schema=declared_schema if isinstance(declared_schema, str) else None,
            validator=None,
            errors=(
                f"schema must declare {DRAFT_2020_12_SCHEMA!r}; "
                f"found {declared_schema!r}",
            ),
            reason="schema dialect mismatch",
        )

    try:
        import jsonschema
        from jsonschema import Draft202012Validator, FormatChecker
    except (ImportError, AttributeError) as exc:
        return SchemaValidationResult(
            status="environment_limited",
            schema_path=str(schema_path),
            instance_path=str(instance_path),
            declared_schema=declared_schema,
            validator=None,
            reason=(
                "The active jsonschema package has no Draft202012Validator; "
                "use a disposable validator environment with jsonschema>=4.x "
                f"(import error: {exc})"
            ),
        )

    try:
        version = distribution_version("jsonschema")
    except PackageNotFoundError:
        version = "unknown"
    validator_name = f"jsonschema {version}; Draft202012Validator"
    try:
        Draft202012Validator.check_schema(schema)
        validation_errors = sorted(
            Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(instance),
            key=lambda error: tuple(str(part) for part in error.absolute_path),
        )
    except Exception as exc:  # schema/validator failures are reported, never treated as pass
        return SchemaValidationResult(
            status="invalid",
            schema_path=str(schema_path),
            instance_path=str(instance_path),
            declared_schema=declared_schema,
            validator=validator_name,
            errors=(str(exc),),
            reason="validator or schema error",
        )

    if validation_errors:
        return SchemaValidationResult(
            status="invalid",
            schema_path=str(schema_path),
            instance_path=str(instance_path),
            declared_schema=declared_schema,
            validator=validator_name,
            errors=tuple(
                f"{getattr(error, 'json_path', '$')}: {error.message}"
                for error in validation_errors
            ),
            reason="instance does not satisfy the Draft 2020-12 schema",
        )
    return SchemaValidationResult(
        status="valid",
        schema_path=str(schema_path),
        instance_path=str(instance_path),
        declared_schema=declared_schema,
        validator=validator_name,
        reason="schema and example validated with Draft 2020-12",
    )


def main() -> int:
    result = validate_protocol_schema()
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return {"valid": 0, "invalid": 1, "environment_limited": 2}[result.status]


if __name__ == "__main__":
    raise SystemExit(main())
