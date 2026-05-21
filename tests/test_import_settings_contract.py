"""Contract tests for top-level import_settings on .rcm.json (phase 0 / ADR-0004)."""

from __future__ import annotations

from rcm_core.import_settings_contract import (
    IMPORT_SETTINGS_SCHEMA_VERSION,
    merge_import_settings,
    normalize_import_settings,
)


def test_schema_version_is_fixed_at_one() -> None:
    assert IMPORT_SETTINGS_SCHEMA_VERSION == 1


def test_normalize_empty_returns_version_only() -> None:
    assert normalize_import_settings(None) == {
        "import_settings_schema_version": 1,
    }
    assert normalize_import_settings({}) == {
        "import_settings_schema_version": 1,
    }


def test_unknown_keys_preserved_on_round_trip() -> None:
    raw = {
        "import_settings_schema_version": 1,
        "isograph_project": {"RcmNoSimulations": 1000},
        "custom_future_key": {"x": 1},
    }
    normalized = normalize_import_settings(raw)
    assert normalized["custom_future_key"] == {"x": 1}
    merged = merge_import_settings(normalized, {"extra": True})
    assert merged["custom_future_key"] == {"x": 1}
    assert merged["extra"] is True
    assert merged["import_settings_schema_version"] == 1
