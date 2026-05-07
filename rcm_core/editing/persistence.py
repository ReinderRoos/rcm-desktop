from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from typing import Any

import pandas as pd

from rcm_core.editing.schemas import ENTITY_SCHEMAS
from rcm_core.editing.session import get_session_state
from rcm_core.models import RCMProject
from rcm_core.persistence import load_project, save_project


def _simple_dict_from_row(row: dict[str, Any], allowed_fields: set[str]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in row.items():
        if key in allowed_fields:
            if isinstance(value, float) and pd.isna(value):
                cleaned[key] = None
            else:
                cleaned[key] = value
    return cleaned


def _write_back_simple(edited_df: pd.DataFrame, cls: type, key_field: str) -> dict[str, Any]:
    allowed_fields = {f.name for f in fields(cls)}
    result: dict[str, Any] = {}
    for row in edited_df.to_dict(orient="records"):
        row_clean = _simple_dict_from_row(row, allowed_fields)
        key = str(row_clean.get(key_field, "")).strip()
        if not key:
            continue
        row_clean[key_field] = key
        result[key] = cls.from_dict(row_clean)
    return result


def build_project_from_state(project: RCMProject, session: dict[str, Any] | None = None) -> RCMProject:
    session_state = get_session_state() if session is None else session
    new_project = RCMProject.from_dict(project.to_dict())
    for entity, schema in ENTITY_SCHEMAS.items():
        rows = session_state.get("edit_current", {}).get(entity, [])
        df = pd.DataFrame(rows)
        klass = schema["class"]
        key_field = schema["key_field"]
        parsed = _write_back_simple(df, klass, key_field)
        setattr(new_project, schema["store_key"], parsed)
    return new_project


def reload_from_disk(path_obj: Path) -> RCMProject:
    return load_project(path_obj)


def save_to_disk(project: RCMProject, path_obj: Path) -> None:
    save_project(project, path_obj)

