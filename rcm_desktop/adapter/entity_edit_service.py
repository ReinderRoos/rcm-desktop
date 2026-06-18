"""Schema-gedreven entiteiten-bewerking via tabulaire editing-pipeline (slice 83)."""

from __future__ import annotations

import copy
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from rcm_core.editing.schemas import ENTITY_SCHEMAS
from rcm_core.editing.state import blocking_edit_error_count, edit_findings_count
from rcm_core.editing.validation import normalize_key
from rcm_core.models import RCMProject

from rcm_desktop.adapter.editing_session import EditingSession
from rcm_desktop.adapter.input_revalidation_service import revalidate_input_buffer
from rcm_desktop.adapter.entity_grid_config import (
    EntityGridViewConfig,
    entity_grid_config_for_view,
)
from rcm_desktop.adapter.tabular_edit_types import (
    BulkChangeResult,
    CellErrorView,
    MaterializeBlockedError,
)

FaalwijzenMaterializeBlockedError = MaterializeBlockedError


@dataclass(frozen=True)
class EntityRowView:
    row_key: str
    values: dict[str, Any]
    field_errors: dict[str, tuple[CellErrorView, ...]]
    editable_fields: frozenset[str]

    def editable(self, field: str) -> bool:
        return field in self.editable_fields


class EntityEditService:
    def __init__(self, config: EntityGridViewConfig, changed: Callable[[], None] | None = None) -> None:
        self._config = config
        self._entity = config.entity
        self._key_field = config.key_field
        schema = ENTITY_SCHEMAS[self._entity]
        self._field_types: dict[str, str] = schema["field_types"]
        self._editable = config.editable_columns
        self._editing = EditingSession()
        self._changed = changed
        self._rows_cache: list[EntityRowView] | None = None

    @classmethod
    def for_view(cls, view_id: str, changed: Callable[[], None] | None = None) -> EntityEditService:
        cfg = entity_grid_config_for_view(view_id)
        if cfg is None:
            raise ValueError(f"Geen entiteiten-grid config voor view {view_id!r}")
        return cls(cfg, changed=changed)

    @property
    def config(self) -> EntityGridViewConfig:
        return self._config

    @property
    def editing_session(self) -> EditingSession:
        return self._editing

    def attach_editing_session(self, session: EditingSession) -> None:
        self._editing = session
        self._invalidate_rows_cache()

    def bind_changed(self, callback: Callable[[], None] | None) -> None:
        self._changed = callback

    @property
    def _session(self) -> dict[str, Any]:
        return self._editing.session

    def is_active(self) -> bool:
        return self._editing.is_loaded

    def clear(self) -> None:
        self._editing = EditingSession()
        self._invalidate_rows_cache()

    def init(self, project: RCMProject) -> None:
        self.reset(project)

    def reset(self, project: RCMProject) -> None:
        self._editing = EditingSession()
        self._editing.load_project(project)
        self._invalidate_rows_cache()

    def discard_changes(self) -> None:
        if not self._editing.is_loaded:
            return
        original = copy.deepcopy(self._session.get("edit_original", {}).get(self._entity, []))
        self._editing.apply_entity_rows(self._entity, original)
        revalidate_input_buffer(self._editing)
        self._invalidate_rows_cache()
        if self._changed:
            self._changed()

    def rows(self) -> list[EntityRowView]:
        if not self._editing.is_loaded:
            return []
        if self._rows_cache is None:
            raw_rows = self._session.get("edit_current", {}).get(self._entity, [])
            sorted_rows = sorted(raw_rows, key=lambda r: normalize_key(r.get(self._key_field)))
            self._rows_cache = [_row_to_view(row, self._session, self._config) for row in sorted_rows]
        return self._rows_cache

    def _invalidate_rows_cache(self) -> None:
        self._rows_cache = None

    def refresh_rows(self) -> None:
        self._invalidate_rows_cache()

    def apply_change(self, row_key: str, field: str, raw_value: Any) -> None:
        if field not in self._editable:
            raise ValueError(f"Field '{field}' is not editable in {self._entity} grid")
        if not self._editing.is_loaded:
            raise RuntimeError("EntityEditService is not initialized")

        rows = copy.deepcopy(self._session["edit_current"][self._entity])
        target = normalize_key(row_key)
        idx = next(
            (i for i, r in enumerate(rows) if normalize_key(r.get(self._key_field)) == target),
            None,
        )
        if idx is None:
            return

        adapted = _adapt_raw_for_coerce(field, raw_value, self._field_types)
        rows[idx][field] = adapted

        self._editing.apply_entity_rows(self._entity, rows)
        revalidate_input_buffer(self._editing)
        self._invalidate_rows_cache()
        if self._changed:
            self._changed()

    def apply_bulk_change(
        self,
        row_keys: Sequence[str],
        field: str,
        raw_value: Any,
    ) -> BulkChangeResult:
        if field not in self._editable:
            raise ValueError(f"Field '{field}' is not editable in {self._entity} grid")
        if not self._editing.is_loaded:
            raise RuntimeError("EntityEditService is not initialized")
        if not row_keys:
            return BulkChangeResult(ok=True, errors=(), applied_count=0)

        adapted = _adapt_raw_for_coerce(field, raw_value, self._field_types)
        rows = copy.deepcopy(self._session["edit_current"][self._entity])
        targets = {normalize_key(rk) for rk in row_keys}
        touched = 0
        for row in rows:
            if normalize_key(row.get(self._key_field)) in targets:
                row[field] = adapted
                touched += 1

        if touched == 0:
            return BulkChangeResult(ok=True, errors=(), applied_count=0)

        original_rows = copy.deepcopy(self._session["edit_current"][self._entity])
        self._editing.apply_entity_rows(self._entity, rows)
        revalidate_input_buffer(self._editing)
        msgs: list[str] = []
        for rk in row_keys:
            key = normalize_key(rk)
            fe = _errors_for_row(self._session, self._entity, key)
            if field in fe:
                blocking = [e for e in fe[field] if e.severity == "error"]
                if blocking:
                    msgs.append(f"{key}/{field}: {blocking[0].message}")

        if msgs:
            self._editing.apply_entity_rows(self._entity, original_rows)
            revalidate_input_buffer(self._editing)
            return BulkChangeResult(ok=False, errors=tuple(msgs), applied_count=0)

        self._invalidate_rows_cache()
        if self._changed:
            self._changed()
        return BulkChangeResult(ok=True, errors=(), applied_count=touched)

    def has_errors(self) -> bool:
        return self.error_count() > 0

    def error_count(self) -> int:
        if not self._editing.is_loaded:
            return 0
        return blocking_edit_error_count(self._session)

    def findings_count(self) -> tuple[int, int]:
        """(fouten, waarschuwingen) voor deze entiteit over de volledige view."""
        if not self._editing.is_loaded:
            return (0, 0)
        errors = edit_findings_count(self._session, severity="error", entity=self._entity)
        warnings = edit_findings_count(self._session, severity="warning", entity=self._entity)
        return (errors, warnings)

    def columns_with_findings(self) -> frozenset[str]:
        """Kolomvelden met minstens één invoerbevinding (fout of waarschuwing)."""
        if not self._editing.is_loaded:
            return frozenset()
        cols: set[str] = set()
        for fields in self._session.get("edit_errors", {}).get(self._entity, {}).values():
            for field, arr in fields.items():
                if arr:
                    cols.add(field)
        return frozenset(cols)

    def column_findings_severity(self) -> dict[str, str]:
        """Per kolom de hoogste ernst: 'error' wint boven 'warning'."""
        if not self._editing.is_loaded:
            return {}
        severity_by_col: dict[str, str] = {}
        for fields in self._session.get("edit_errors", {}).get(self._entity, {}).values():
            for field, arr in fields.items():
                if not arr:
                    continue
                if any(e.get("severity", "error") == "error" for e in arr):
                    severity_by_col[field] = "error"
                elif field not in severity_by_col:
                    severity_by_col[field] = "warning"
        return severity_by_col

    def materialize_for_run(self) -> RCMProject:
        return self._materialize()

    def materialize_for_save(self) -> RCMProject:
        return self._materialize()

    def delete_row(self, row_key: str) -> None:
        if not self._editing.is_loaded:
            raise RuntimeError("EntityEditService is not initialized")
        target = normalize_key(row_key)
        rows = self._session["edit_current"][self._entity]
        filtered = [r for r in rows if normalize_key(r.get(self._key_field)) != target]
        if len(filtered) == len(rows):
            return
        self._editing.apply_entity_rows(self._entity, filtered)
        if self._entity == "faalwijzes":
            self._cascade_delete_faalwijze(target)
        revalidate_input_buffer(self._editing)
        self._invalidate_rows_cache()
        if self._changed:
            self._changed()

    def _cascade_delete_faalwijze(self, fm_id: str) -> None:
        current = self._session["edit_current"]
        pm_rows = current.get("pm_tasks", [])
        pm_for_fm = [r for r in pm_rows if normalize_key(r.get("fm_id")) == fm_id]
        pm_ids = {normalize_key(r.get("pm_id")) for r in pm_for_fm}
        remaining_pm = [r for r in pm_rows if normalize_key(r.get("fm_id")) != fm_id]
        if len(remaining_pm) != len(pm_rows):
            self._editing.apply_entity_rows("pm_tasks", remaining_pm)
        fm_links = current.get("fm_effect_links", [])
        remaining_fm_links = [
            r for r in fm_links if normalize_key(r.get("fm_id")) != fm_id
        ]
        if len(remaining_fm_links) != len(fm_links):
            self._editing.apply_entity_rows("fm_effect_links", remaining_fm_links)
        pm_links = current.get("pm_effect_links", [])
        remaining_pm_links = [
            r for r in pm_links if normalize_key(r.get("pm_id")) not in pm_ids
        ]
        if len(remaining_pm_links) != len(pm_links):
            self._editing.apply_entity_rows("pm_effect_links", remaining_pm_links)

    def _materialize(self) -> RCMProject:
        if not self._editing.is_loaded:
            raise RuntimeError("EntityEditService is not initialized")
        if blocking_edit_error_count(self._session) > 0:
            raise MaterializeBlockedError(
                "Los eerst de bewerkingsfouten op voordat je een analyse start."
            )
        return self._editing.build_project()


def _adapt_raw_for_coerce(field: str, raw_value: Any, field_types: dict[str, str]) -> Any:
    expected = field_types.get(field)
    if expected == "bool":
        if isinstance(raw_value, bool):
            return raw_value
        s = str(raw_value).strip().lower()
        if s in ("ja", "yes", "true", "1"):
            return True
        if s in ("nee", "no", "false", "0"):
            return False
        return bool(raw_value)
    if expected == "str" and field == "failure_type":
        return str(raw_value).strip().lower()
    if expected != "float" or not isinstance(raw_value, str):
        return raw_value
    s = raw_value.strip()
    if "," in s and "." not in s:
        return s.replace(",", ".")
    return raw_value


def _errors_for_row(
    session: dict[str, Any],
    entity: str,
    row_key: str,
) -> dict[str, tuple[CellErrorView, ...]]:
    raw_errors = session.get("edit_errors", {}).get(entity, {}).get(row_key, {})
    out: dict[str, tuple[CellErrorView, ...]] = {}
    for field, arr in raw_errors.items():
        out[field] = tuple(
            CellErrorView(
                code=e["code"],
                message=e["message"],
                severity=e.get("severity", "error"),
            )
            for e in arr
        )
    return out
def _row_to_view(
    row: dict[str, Any],
    session: dict[str, Any],
    config: EntityGridViewConfig,
) -> EntityRowView:
    row_key = normalize_key(row.get(config.key_field)) or ""
    fe = _errors_for_row(session, config.entity, row_key)
    return EntityRowView(
        row_key=row_key,
        values=dict(row),
        field_errors=fe,
        editable_fields=config.editable_columns,
    )
