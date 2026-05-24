"""In-memory faalwijzen editing via rcm_core editing pipeline (no Qt)."""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from rcm_core.editing.schemas import ENTITY_SCHEMAS
from rcm_core.editing.validation import normalize_key
from rcm_core.models import RCMProject

from rcm_desktop.adapter.editing_session import EditingSession

_ENTITY = "faalwijzes"
_SCHEMA = ENTITY_SCHEMAS[_ENTITY]
_FIELD_TYPES: dict[str, str] = _SCHEMA["field_types"]

READONLY_FIELDS = frozenset({"fm_id", "pbs_id"})
EDITABLE_FIELDS = frozenset(
    {
        "faalwijze_omschrijving",
        "functie_id",
        "mttf_jaar",
        "sigma_jaar",
        "cost_cm_eur",
        "p_ongewenste_gebeurtenis",
    }
)
SLICE_FIELD_KEYS: tuple[str, ...] = (
    "fm_id",
    "pbs_id",
    "faalwijze_omschrijving",
    "functie_id",
    "mttf_jaar",
    "sigma_jaar",
    "cost_cm_eur",
    "p_ongewenste_gebeurtenis",
)


@dataclass(frozen=True)
class CellErrorView:
    code: str
    message: str


@dataclass(frozen=True)
class FaalwijzenRowView:
    fm_id: str
    pbs_id: str
    faalwijze_omschrijving: str
    functie_id: str
    mttf_jaar: Any
    sigma_jaar: Any
    cost_cm_eur: Any
    p_ongewenste_gebeurtenis: Any
    field_errors: dict[str, tuple[CellErrorView, ...]]

    def editable(self, field: str) -> bool:
        return field in EDITABLE_FIELDS


class FaalwijzenMaterializeBlockedError(RuntimeError):
    """Raised when ``materialize_for_run`` is called while validation errors exist."""


def _adapt_raw_for_coerce(field: str, raw_value: Any) -> Any:
    expected = _FIELD_TYPES.get(field)
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


class FaalwijzenEditService:
    def __init__(self, changed: Callable[[], None] | None = None) -> None:
        self._editing = EditingSession()
        self._changed = changed
        self._saved_digest = ""

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

    def rows(self) -> list[FaalwijzenRowView]:
        if not self._editing.is_loaded:
            return []
        raw_rows = self._session.get("edit_current", {}).get(_ENTITY, [])
        sorted_rows = sorted(raw_rows, key=lambda r: normalize_key(r.get("fm_id")))
        views: list[FaalwijzenRowView] = []
        for row in sorted_rows:
            fm_id = normalize_key(row.get("fm_id")) or ""
            fe = _errors_for_row(self._session, fm_id)
            views.append(
                FaalwijzenRowView(
                    fm_id=fm_id,
                    pbs_id=str(row.get("pbs_id") or ""),
                    faalwijze_omschrijving=str(row.get("faalwijze_omschrijving") or ""),
                    functie_id=str(row.get("functie_id") or ""),
                    mttf_jaar=row.get("mttf_jaar"),
                    sigma_jaar=row.get("sigma_jaar"),
                    cost_cm_eur=row.get("cost_cm_eur"),
                    p_ongewenste_gebeurtenis=row.get("p_ongewenste_gebeurtenis"),
                    field_errors=fe,
                )
            )
        return views

    def apply_change(self, fm_id: str, field: str, raw_value: Any) -> None:
        if field not in EDITABLE_FIELDS:
            raise ValueError(f"Field '{field}' is not editable in slice 7")
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

    def has_errors(self) -> bool:
        return self.error_count() > 0

    def error_count(self) -> int:
        if not self._editing.is_loaded:
            return 0
        return _session_error_total(self._session)

    def materialize_for_run(self) -> RCMProject:
        if not self._editing.is_loaded:
            raise RuntimeError("FaalwijzenEditService is not initialized")
        total_errors = self._editing.validate()
        if total_errors > 0:
            raise FaalwijzenMaterializeBlockedError(
                "Los eerst de bewerkingsfouten op voordat je een analyse start."
            )
        built = self._editing.build_project()
        return built
