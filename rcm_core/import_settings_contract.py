"""Top-level import_settings contract for Isograph bootstrap import (ADR-0004)."""

from __future__ import annotations

from typing import Any, Mapping

IMPORT_SETTINGS_SCHEMA_VERSION = 1
SOURCE_WORKBOOK_PATH_KEY = "source_workbook_path"


def normalize_import_settings(
    raw: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Ensure schema version; pass through all other keys unchanged."""
    if not raw:
        return {"import_settings_schema_version": IMPORT_SETTINGS_SCHEMA_VERSION}
    out = dict(raw)
    out["import_settings_schema_version"] = IMPORT_SETTINGS_SCHEMA_VERSION
    return out


def merge_import_settings(
    base: Mapping[str, Any],
    overlay: Mapping[str, Any],
) -> dict[str, Any]:
    """Shallow merge with overlay winning; re-normalize version field."""
    merged = dict(base)
    merged.update(overlay)
    return normalize_import_settings(merged)
