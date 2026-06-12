"""Qt-vrije zoektekst voor Input entiteiten-grid (slice 87)."""

from __future__ import annotations

from typing import Any

from rcm_core.models import RCMProject

from rcm_desktop.adapter.entity_cell_display import display_faalwijze_field
from rcm_desktop.adapter.entity_grid_config import EntityGridViewConfig
from rcm_desktop.adapter.entity_grid_derived_values import entity_derived_value


def _raw_search_part(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _display_part(
    config: EntityGridViewConfig,
    project: RCMProject,
    field: str,
    row_values: dict[str, Any],
) -> str:
    if field in config.derived_columns:
        val = entity_derived_value(config.view_id, field, project, row_values)
        if val is None:
            return ""
        return str(val)
    value = row_values.get(field)
    if config.entity == "faalwijzes":
        return display_faalwijze_field(project, field, value)
    if value is None:
        return ""
    return str(value)


def build_row_search_haystack(
    config: EntityGridViewConfig,
    project: RCMProject,
    row_values: dict[str, Any],
    visible_columns: tuple[str, ...],
) -> str:
    parts: list[str] = []
    key_field = config.key_field
    key_val = row_values.get(key_field)
    if key_val is not None:
        parts.append(_raw_search_part(key_val))
        if config.entity == "faalwijzes":
            parts.append(display_faalwijze_field(project, key_field, key_val))
        else:
            parts.append(str(key_val))

    for field in visible_columns:
        if field == key_field:
            continue
        if field in config.derived_columns:
            val = entity_derived_value(config.view_id, field, project, row_values)
            parts.append(_raw_search_part(val))
            if val is not None:
                parts.append(str(val))
            continue
        raw = row_values.get(field)
        parts.append(_raw_search_part(raw))
        parts.append(_display_part(config, project, field, row_values))

    return " ".join(p for p in parts if p).lower()
