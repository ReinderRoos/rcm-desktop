from __future__ import annotations

import copy
from typing import Any

import pandas as pd

from rcm_core.editing.session import get_session_state
from rcm_core.editing.schemas import ENTITY_SCHEMAS
from rcm_core.editing.validation import validate_entity_rows
from rcm_core.models import RCMProject


def _resolve_session(session: dict[str, Any] | None) -> dict[str, Any]:
    return get_session_state() if session is None else session


def init_edit_state(project: RCMProject, session: dict[str, Any] | None = None) -> None:
    session_state = _resolve_session(session)
    edit_original: dict[str, list[dict[str, Any]]] = {}
    edit_current: dict[str, list[dict[str, Any]]] = {}
    edit_errors: dict[str, dict[str, dict[str, list[dict[str, Any]]]]] = {}
    edit_dirty: dict[str, bool] = {}
    for entity, schema in ENTITY_SCHEMAS.items():
        store_key = schema["store_key"]
        values = getattr(project, store_key).values()
        rows = [v.to_dict() for v in values]
        edit_original[entity] = copy.deepcopy(rows)
        edit_current[entity] = copy.deepcopy(rows)
        edit_errors[entity] = {}
        edit_dirty[entity] = False
    session_state["edit_original"] = edit_original
    session_state["edit_current"] = edit_current
    session_state["edit_errors"] = edit_errors
    session_state["edit_dirty"] = edit_dirty
    session_state["edit_dirty_global"] = False


def set_dirty_flags(session: dict[str, Any] | None = None) -> None:
    session_state = _resolve_session(session)
    edit_original = session_state.get("edit_original", {})
    edit_current = session_state.get("edit_current", {})
    edit_dirty: dict[str, bool] = {}
    for entity in ENTITY_SCHEMAS:
        original_df = pd.DataFrame(edit_original.get(entity, []))
        current_df = pd.DataFrame(edit_current.get(entity, []))
        edit_dirty[entity] = not original_df.equals(current_df)
    session_state["edit_dirty"] = edit_dirty
    session_state["edit_dirty_global"] = any(edit_dirty.values())


def errors_count(entity: str, session: dict[str, Any] | None = None) -> int:
    errors = _resolve_session(session).get("edit_errors", {}).get(entity, {})
    return sum(len(arr) for row in errors.values() for arr in row.values())


def add_error_summary_column(entity: str, rows: list[dict[str, Any]], session: dict[str, Any] | None = None) -> pd.DataFrame:
    session_state = _resolve_session(session)
    schema = ENTITY_SCHEMAS[entity]
    key_field = schema["key_field"]
    errors = session_state.get("edit_errors", {}).get(entity, {})
    out_rows: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        row2 = dict(row)
        row_key = str(row2.get(key_field, "")).strip() or f"row-{idx+1}"
        per_row = errors.get(row_key, {})
        row2["_errors"] = sum(len(v) for v in per_row.values())
        out_rows.append(row2)
    return pd.DataFrame(out_rows)


def parse_bulk_text_for_entity(entity: str, text: str) -> list[dict[str, Any]]:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return []
    delimiter = "\t" if "\t" in lines[0] else ";"
    first_cols = [col.strip() for col in lines[0].split(delimiter)]
    known_fields = set(ENTITY_SCHEMAS[entity]["field_types"].keys())
    key_field = ENTITY_SCHEMAS[entity]["key_field"]

    has_header = key_field in first_cols or all(col in known_fields for col in first_cols if col)
    if has_header:
        headers = first_cols
        data_lines = lines[1:]
    else:
        headers = list(ENTITY_SCHEMAS[entity]["field_types"].keys())
        data_lines = lines

    rows: list[dict[str, Any]] = []
    for line in data_lines:
        cols = [c.strip() for c in line.split(delimiter)]
        rows.append(dict(zip(headers, cols)))
    return rows


def merge_rows_by_key(entity: str, current_rows: list[dict[str, Any]], new_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    key_field = ENTITY_SCHEMAS[entity]["key_field"]
    by_key: dict[str, dict[str, Any]] = {}
    for row in current_rows:
        key = str(row.get(key_field, "")).strip()
        if key:
            by_key[key] = dict(row)
    for row in new_rows:
        key = str(row.get(key_field, "")).strip()
        if not key:
            continue
        if key in by_key:
            by_key[key].update(row)
        else:
            by_key[key] = dict(row)
    return list(by_key.values())


def apply_rows(
    entity: str,
    rows: list[dict[str, Any]],
    project: RCMProject,
    session: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, list[dict[str, Any]]]]]:
    session_state = _resolve_session(session)
    edit_current = session_state.get("edit_current", {})
    coerced, errors = validate_entity_rows(entity, rows, project, edit_current)
    session_state["edit_current"][entity] = coerced
    session_state["edit_errors"][entity] = errors
    set_dirty_flags(session=session_state)
    return coerced, errors


def restore_entity(entity: str, session: dict[str, Any] | None = None) -> None:
    session_state = _resolve_session(session)
    session_state["edit_current"][entity] = copy.deepcopy(session_state["edit_original"][entity])
    session_state["edit_errors"][entity] = {}
    set_dirty_flags(session=session_state)


def validate_all_entities(project: RCMProject, session: dict[str, Any] | None = None) -> int:
    session_state = _resolve_session(session)
    total = 0
    for entity in ENTITY_SCHEMAS:
        rows = session_state.get("edit_current", {}).get(entity, [])
        _, errors = apply_rows(entity, rows, project, session=session_state)
        total += sum(len(arr) for row in errors.values() for arr in row.values())
    return total

