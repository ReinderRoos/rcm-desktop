"""Issue 04 — import_settings round-trip on RCMProject."""

from __future__ import annotations

import json

from rcm_core.import_settings_contract import IMPORT_SETTINGS_SCHEMA_VERSION
from rcm_core.models import RCMProject


def test_round_trip_preserves_nested_import_settings() -> None:
    nested = {
        "import_settings_schema_version": IMPORT_SETTINGS_SCHEMA_VERSION,
        "isograph_project": {"AvsimAvailabilityPreference": False, "FileName": "x.awb"},
        "isograph_causes": {"06H-350.1.1.1.1.1.A.1": {"TotalCostErrPc": 5.0}},
    }
    project = RCMProject(import_settings=nested)
    raw = json.loads(json.dumps(project.to_dict()))
    restored = RCMProject.from_dict(raw)
    assert restored.import_settings == nested


def test_legacy_fixture_without_import_settings_loads() -> None:
    project = RCMProject.from_dict({"config": {"modeljaar": 2026}})
    assert project.import_settings == {}


def test_empty_import_settings_omitted_from_json_dict() -> None:
    project = RCMProject()
    assert "import_settings" not in project.to_dict()
