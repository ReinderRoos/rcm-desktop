"""Allocate FM-id en default rijen voor create-modus (slice 59.1, Qt-vrij)."""

from __future__ import annotations

import re
from typing import Any

from rcm_core.editing.validation import normalize_key
from rcm_core.models import RCMProject

from rcm_desktop.adapter.editing_session import EditingSession
from rcm_desktop.adapter.fm_edit_bundle_service import _edit_current

_FM_ID_PATTERN = re.compile(r"^FM-(\d+)$", re.IGNORECASE)


def _existing_fm_ids(source: RCMProject | EditingSession) -> set[str]:
    if isinstance(source, EditingSession):
        rows = _edit_current(source).get("faalwijzes", [])
        return {normalize_key(r.get("fm_id")) for r in rows if normalize_key(r.get("fm_id"))}
    return {normalize_key(k) for k in source.faalwijzes.keys()}


def allocate_fm_id(source: RCMProject | EditingSession) -> str:
    """Ken uniek ``FM-###`` toe dat nog niet in project of sessie voorkomt."""
    used = _existing_fm_ids(source)
    max_num = 0
    for fm_id in used:
        match = _FM_ID_PATTERN.match(fm_id)
        if match:
            max_num = max(max_num, int(match.group(1)))
    candidate_num = max_num + 1
    while True:
        candidate = f"FM-{candidate_num:03d}"
        if candidate not in used:
            return candidate
        candidate_num += 1


def default_functie_id_for_pbs(source: RCMProject | EditingSession, pbs_id: str) -> str:
    """Eerste functie van sibling-FM op PBS, anders eerste projectfunctie."""
    target_pbs = normalize_key(pbs_id)
    if isinstance(source, EditingSession):
        rows = _edit_current(source).get("faalwijzes", [])
        for row in rows:
            if normalize_key(row.get("pbs_id")) == target_pbs:
                functie_id = normalize_key(row.get("functie_id"))
                if functie_id:
                    return functie_id
        functies = sorted(_edit_current(source).get("functies", []), key=lambda r: normalize_key(r.get("functie_id")))
        if functies:
            return normalize_key(functies[0].get("functie_id"))
        return ""
    for fm in source.faalwijzes.values():
        if normalize_key(fm.pbs_id) == target_pbs and normalize_key(fm.functie_id):
            return normalize_key(fm.functie_id)
    if source.functies:
        return normalize_key(next(iter(sorted(source.functies.keys()))))
    return ""


def default_faalwijze_row(*, fm_id: str, pbs_id: str, functie_id: str) -> dict[str, Any]:
    """Schema-default rij voor nieuwe faalwijze in create-modus."""
    return {
        "fm_id": normalize_key(fm_id),
        "pbs_id": normalize_key(pbs_id),
        "functie_id": normalize_key(functie_id),
        "faalwijze_omschrijving": "",
        "failure_type": "random",
        "mttf_jaar": 10.0,
        "sigma_jaar": 0.0,
        "aging_distribution": "normal",
        "beta_jaar": 0.0,
        "repair_quality": 1.0,
        "is_evident": True,
        "p_ongewenste_gebeurtenis": 1.0,
        "eindgevolg": "",
        "downtime_per_failure": {"value": 0.0, "unit": "uur"},
        "cost_cm_eur": 0.0,
        "library_ref": "",
        "notes": "",
        "aanname_faalmodel": "",
        "aanname_cm_kosten": "",
        "aanname_downtime": "",
        "aanname_effectklasse": "",
    }


def is_leaf_pbs(source: RCMProject | EditingSession, pbs_id: str) -> bool:
    """True wanneer PBS bestaat en geen kinderen heeft in de boom."""
    target = normalize_key(pbs_id)
    if isinstance(source, EditingSession):
        pbs_rows = _edit_current(source).get("pbs", [])
        if not any(normalize_key(r.get("pbs_id")) == target for r in pbs_rows):
            return False
        for row in pbs_rows:
            parent = normalize_key(row.get("parent_pbs_id"))
            if parent == target:
                return False
        return True
    if target not in source.pbs_items:
        return False
    for item in source.pbs_items.values():
        parent = item.parent_pbs_id
        if parent is not None and normalize_key(parent) == target:
            return False
    return True


def validate_fm_minimum(faalwijze_row: dict[str, Any]) -> tuple[str, ...]:
    """Minimumvalidatie voor create/edit vóór commit."""
    errors: list[str] = []
    if not str(faalwijze_row.get("faalwijze_omschrijving") or "").strip():
        from rcm_desktop import messages

        errors.append(messages.FM_EDITOR_CREATE_OMSCHRIJVING_REQUIRED)
    if not normalize_key(faalwijze_row.get("functie_id")):
        from rcm_desktop import messages

        errors.append(messages.FM_EDITOR_CREATE_FUNCTIE_REQUIRED)
    mttf = faalwijze_row.get("mttf_jaar")
    if not isinstance(mttf, (int, float)) or float(mttf) <= 0:
        errors.append("MTTF moet groter zijn dan 0.")
    return tuple(errors)
