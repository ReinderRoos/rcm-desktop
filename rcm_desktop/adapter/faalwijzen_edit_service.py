"""In-memory faalwijzen editing via rcm_core editing pipeline (no Qt)."""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from rcm_core.editing.schemas import ENTITY_SCHEMAS
from rcm_core.editing.validation import normalize_key
from rcm_core.models import RCMProject

from rcm_desktop.adapter.editing_session import EditingSession
from rcm_desktop.adapter.faalwijzen_grid_contract import (
    EDITABLE_FIELDS,
    READONLY_FIELDS,
    SLICE_FIELD_KEYS,
    grid_column_keys,
    grid_editable_fields,
)

_ENTITY = "faalwijzes"
_SCHEMA = ENTITY_SCHEMAS[_ENTITY]
_FIELD_TYPES: dict[str, str] = _SCHEMA["field_types"]


@dataclass(frozen=True)
class CellErrorView:
    code: str
    message: str


@dataclass(frozen=True)
class BulkChangeResult:
    ok: bool
    errors: tuple[str, ...]
    applied_count: int


@dataclass(frozen=True)
class FaalwijzenRowView:
    fm_id: str
    pbs_id: str
    failure_type: str
    is_evident: bool
    faalwijze_omschrijving: str
    functie_id: str
    mttf_jaar: Any
    sigma_jaar: Any
    repair_quality: Any
    cost_cm_eur: Any
    p_ongewenste_gebeurtenis: Any
    field_errors: dict[str, tuple[CellErrorView, ...]]

    def editable(self, field: str) -> bool:
        return field in EDITABLE_FIELDS


class FaalwijzenMaterializeBlockedError(RuntimeError):
    """Raised when ``materialize_for_run`` is called while validation errors exist."""


def _adapt_raw_for_coerce(field: str, raw_value: Any) -> Any:
    expected = _FIELD_TYPES.get(field)
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


def _errors_for_row(session: dict[str, Any], fm_id: str) -> dict[str, tuple[CellErrorView, ...]]:
    raw_errors = session.get("edit_errors", {}).get(_ENTITY, {}).get(fm_id, {})
    out: dict[str, tuple[CellErrorView, ...]] = {}
    for field, arr in raw_errors.items():
        out[field] = tuple(CellErrorView(code=e["code"], message=e["message"]) for e in arr)
    return out


def _session_error_total(session: dict[str, Any]) -> int:
    total = 0
    for _entity, rows_e in session.get("edit_errors", {}).items():
        for _rk, fields in rows_e.items():
            for _f, arr in fields.items():
                total += len(arr)
    return total


def _session_content_digest(session: dict[str, Any]) -> str:
    rows = session.get("edit_current", {}).get(_ENTITY, [])
    payload = json.dumps(rows, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def _row_to_view(row: dict[str, Any], session: dict[str, Any]) -> FaalwijzenRowView:
    fm_id = normalize_key(row.get("fm_id")) or ""
    fe = _errors_for_row(session, fm_id)
    return FaalwijzenRowView(
        fm_id=fm_id,
        pbs_id=str(row.get("pbs_id") or ""),
        failure_type=str(row.get("failure_type") or "random"),
        is_evident=bool(row.get("is_evident", True)),
        faalwijze_omschrijving=str(row.get("faalwijze_omschrijving") or ""),
        functie_id=str(row.get("functie_id") or ""),
        mttf_jaar=row.get("mttf_jaar"),
        sigma_jaar=row.get("sigma_jaar"),
        repair_quality=row.get("repair_quality"),
        cost_cm_eur=row.get("cost_cm_eur"),
        p_ongewenste_gebeurtenis=row.get("p_ongewenste_gebeurtenis"),
        field_errors=fe,
    )


class FaalwijzenEditService:
    def __init__(self, changed: Callable[[], None] | None = None) -> None:
        self._editing = EditingSession()
        self._changed = changed
        self._saved_digest = ""

    @property
    def editing_session(self) -> EditingSession:
        return self._editing

    def attach_editing_session(self, session: EditingSession) -> None:
        """Gedeelde project-sessie (slice 48) — grid en editor gebruiken dezelfde buffer."""
        self._editing = session
        self._saved_digest = _session_content_digest(self._session)

    @property
    def _session(self) -> dict[str, Any]:
        return self._editing.session

    def bind_changed(self, callback: Callable[[], None] | None) -> None:
        self._changed = callback

    def is_active(self) -> bool:
        return self._editing.is_loaded

    def clear(self) -> None:
        self._editing = EditingSession()
        self._saved_digest = ""

    def init(self, project: RCMProject) -> None:
        self.reset(project)

    def reset(self, project: RCMProject) -> None:
        self._editing = EditingSession()
        self._editing.load_project(project)
        self._saved_digest = _session_content_digest(self._session)

    def is_dirty(self) -> bool:
        if not self._editing.is_loaded:
            return False
        return _session_content_digest(self._session) != self._saved_digest

    def mark_saved(self) -> None:
        if not self._editing.is_loaded:
            return
        self._saved_digest = _session_content_digest(self._session)

    def discard_changes(self) -> None:
        if not self._editing.is_loaded:
            return
        original = copy.deepcopy(self._session.get("edit_original", {}).get(_ENTITY, []))
        self._editing.apply_entity_rows(_ENTITY, original)
        self._editing.validate()
        self._saved_digest = _session_content_digest(self._session)
        if self._changed:
            self._changed()

    def rows(self) -> list[FaalwijzenRowView]:
        if not self._editing.is_loaded:
            return []
        raw_rows = self._session.get("edit_current", {}).get(_ENTITY, [])
        sorted_rows = sorted(raw_rows, key=lambda r: normalize_key(r.get("fm_id")))
        return [_row_to_view(row, self._session) for row in sorted_rows]

    def apply_change(self, fm_id: str, field: str, raw_value: Any) -> None:
        if field not in EDITABLE_FIELDS:
            raise ValueError(f"Field '{field}' is not editable in faalwijzen grid")
        if not self._editing.is_loaded:
            raise RuntimeError("FaalwijzenEditService is not initialized")

        rows = copy.deepcopy(self._session["edit_current"][_ENTITY])
        target = normalize_key(fm_id)
        idx = next((i for i, r in enumerate(rows) if normalize_key(r.get("fm_id")) == target), None)
        if idx is None:
            return

        adapted = _adapt_raw_for_coerce(field, raw_value)
        rows[idx][field] = adapted

        self._editing.apply_entity_rows(_ENTITY, rows)
        if self._changed:
            self._changed()

    def apply_bulk_change(
        self,
        fm_ids: Sequence[str],
        field: str,
        raw_value: Any,
    ) -> BulkChangeResult:
        if field not in EDITABLE_FIELDS:
            raise ValueError(f"Field '{field}' is not editable in faalwijzen grid")
        if not self._editing.is_loaded:
            raise RuntimeError("FaalwijzenEditService is not initialized")
        if not fm_ids:
            return BulkChangeResult(ok=True, errors=(), applied_count=0)

        adapted = _adapt_raw_for_coerce(field, raw_value)
        rows = copy.deepcopy(self._session["edit_current"][_ENTITY])
        targets = {normalize_key(fid) for fid in fm_ids}
        touched = 0
        for row in rows:
            if normalize_key(row.get("fm_id")) in targets:
                row[field] = adapted
                touched += 1

        if touched == 0:
            return BulkChangeResult(ok=True, errors=(), applied_count=0)

        original_rows = copy.deepcopy(self._session["edit_current"][_ENTITY])
        self._editing.apply_entity_rows(_ENTITY, rows)
        self._editing.validate()
        msgs: list[str] = []
        for fm_id in fm_ids:
            fid = normalize_key(fm_id)
            fe = _errors_for_row(self._session, fid)
            if field in fe:
                msgs.append(f"{fid}/{field}: {fe[field][0].message}")

        if msgs:
            self._editing.apply_entity_rows(_ENTITY, original_rows)
            self._editing.validate()
            return BulkChangeResult(ok=False, errors=tuple(msgs), applied_count=0)

        if self._changed:
            self._changed()
        return BulkChangeResult(ok=True, errors=(), applied_count=touched)

    def has_errors(self) -> bool:
        return self.error_count() > 0

    def error_count(self) -> int:
        if not self._editing.is_loaded:
            return 0
        return _session_error_total(self._session)

    def materialize_for_run(self) -> RCMProject:
        return self._materialize()

    def materialize_for_save(self) -> RCMProject:
        return self._materialize()

    def _materialize(self) -> RCMProject:
        if not self._editing.is_loaded:
            raise RuntimeError("FaalwijzenEditService is not initialized")
        total_errors = self._editing.validate()
        if total_errors > 0:
            raise FaalwijzenMaterializeBlockedError(
                "Los eerst de bewerkingsfouten op voordat je een analyse start."
            )
        built = self._editing.build_project()
        return built


__all__ = [
    "BulkChangeResult",
    "EDITABLE_FIELDS",
    "READONLY_FIELDS",
    "SLICE_FIELD_KEYS",
    "grid_column_keys",
    "grid_editable_fields",
    "CellErrorView",
    "FaalwijzenEditService",
    "FaalwijzenMaterializeBlockedError",
    "FaalwijzenRowView",
]
