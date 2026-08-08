from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

from jsonschema.validators import validator_for

ROOT = Path(__file__).resolve().parents[1]
RESOURCE = ROOT / "resources" / "sector-complete-instrument" / "v0.1.0-alpha.1"


def load_module():
    path = RESOURCE / "src" / "astra_sector_complete.py"
    spec = importlib.util.spec_from_file_location("astra_sector_complete_candidate", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_sector_candidate_is_namespaced_and_public_alpha() -> None:
    metadata = json.loads((RESOURCE / "package_metadata.json").read_text(encoding="utf-8"))
    assert metadata["namespace"] == "resources/sector-complete-instrument/v0.1.0-alpha.1"
    assert metadata["publication_changes"] is True
    assert metadata["tag"] == "sector-complete-instrument-v0.1.0-alpha.1"
    assert metadata["dark_matter_interpretation_status"] == "proposed_only"


def test_default_transduction_record_matches_candidate_schema() -> None:
    module = load_module()
    schema = json.loads(
        (RESOURCE / "schema" / "sector_complete_instrument.schema.json").read_text(
            encoding="utf-8"
        )
    )
    validator_type = validator_for(schema)
    validator_type.check_schema(schema)
    errors = list(validator_type(schema).iter_errors(module.default_transduction_record().to_dict()))
    assert not errors


def test_source_map_is_declared_alias_of_source_ledger() -> None:
    ledger = (RESOURCE / "source_ledger.csv").read_bytes()
    source_map = (RESOURCE / "source" / "source_map.csv").read_bytes()
    assert ledger == source_map
    assert hashlib.sha256(ledger).hexdigest()


def test_generated_text_outputs_are_lf_only() -> None:
    for path in (RESOURCE / "data").glob("*.json"):
        assert b"\r" not in path.read_bytes(), path
    for path in (RESOURCE / "data").glob("*.csv"):
        assert b"\r" not in path.read_bytes(), path


def test_magnet_bridge_does_not_promote_dark_matter() -> None:
    readme = (RESOURCE / "README.md").read_text(encoding="utf-8")
    source = (RESOURCE / "source" / "ASTRA_Sector_Complete_Instrument_Module_v0.1.0-alpha.1.md").read_text(
        encoding="utf-8"
    )
    assert "proposed_only" in readme
    assert "not a dark-matter observation or limit" in readme
    assert "do not provide a physical edge in ASTRA's SPPT transport graph" in source
