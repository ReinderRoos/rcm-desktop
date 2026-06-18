"""QSettings-seam voor entiteiten-grid kolomzichtbaarheid (slice 83)."""

from __future__ import annotations

from typing import Protocol

from rcm_desktop.adapter.entity_grid_config import (
    entity_grid_config_for_view,
    schema_columns_for_view,
)


class _SettingsLike(Protocol):
    def value(self, key: str, default: object = None, type: type | None = None) -> object: ...
    def setValue(self, key: str, value: object) -> None: ...


def _settings_key(view_id: str) -> str:
    return f"workspace/entity_grid/{view_id}/hidden_columns"


def available_column_ids(view_id: str) -> frozenset[str]:
    return frozenset(schema_columns_for_view(view_id))


def default_hidden_columns(view_id: str) -> frozenset[str]:
    cfg = entity_grid_config_for_view(view_id)
    if cfg is None:
        return frozenset()
    return cfg.optional_columns


def read_hidden_entity_columns(settings: _SettingsLike, view_id: str) -> frozenset[str]:
    key = _settings_key(view_id)
    key_present = settings.value(key) is not None
    if not key_present:
        return default_hidden_columns(view_id)
    stored = settings.value(key, "")
    if not isinstance(stored, str) or not stored.strip():
        return frozenset()
    allowed = available_column_ids(view_id)
    ids = frozenset(part.strip() for part in stored.split(",") if part.strip())
    return frozenset(col_id for col_id in ids if col_id in allowed)


def write_hidden_entity_columns(
    settings: _SettingsLike,
    view_id: str,
    hidden_ids: frozenset[str],
) -> None:
    allowed = available_column_ids(view_id)
    valid = frozenset(col_id for col_id in hidden_ids if col_id in allowed)
    settings.setValue(_settings_key(view_id), ",".join(sorted(valid)))


def resolve_visible_columns(
    view_id: str,
    hidden_ids: frozenset[str],
) -> tuple[str, ...]:
    cfg = entity_grid_config_for_view(view_id)
    if cfg is None:
        return ()
    order = schema_columns_for_view(view_id)
    return tuple(col for col in order if col not in hidden_ids)
