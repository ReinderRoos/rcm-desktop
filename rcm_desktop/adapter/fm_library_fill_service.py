"""FM-editor: vul secties vanuit projectbrede libraries (slice 105.32/33)."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from rcm_desktop.adapter.fm_field_copy_service import (
    EffectScopeCopy,
    PreventiefScopeCopy,
    _next_id,
)


def effect_klasse_library_choices(
    edit_current: dict[str, Any],
) -> list[tuple[str, str]]:
    """Label + klasse_id voor effectklassen-library picker."""
    rows = edit_current.get("effect_klassen", [])
    choices: list[tuple[str, str]] = []
    for row in rows:
        klasse_id = str(row.get("klasse_id") or "")
        if not klasse_id:
            continue
        omschrijving = str(row.get("omschrijving") or "")
        categorie = str(row.get("categorie") or "")
        label = f"{klasse_id} — {omschrijving}"
        if categorie:
            label = f"{label} ({categorie})"
        choices.append((label, klasse_id))
    choices.sort(key=lambda pair: pair[0])
    return choices


def rev_task_library_choices(
    edit_current: dict[str, Any],
) -> list[tuple[str, str]]:
    """Label + pm_id voor REV-taken-library picker."""
    rows = edit_current.get("pm_tasks", [])
    choices: list[tuple[str, str]] = []
    for row in rows:
        pm_id = str(row.get("pm_id") or "")
        if not pm_id:
            continue
        omschrijving = str(row.get("taak_omschrijving") or "")
        taak_type = str(row.get("taak_type") or "")
        fm_id = str(row.get("fm_id") or "")
        label = f"{pm_id} — {omschrijving}"
        if taak_type:
            label = f"{label} [{taak_type}]"
        if fm_id:
            label = f"{label} (FM {fm_id})"
        choices.append((label, pm_id))
    choices.sort(key=lambda pair: pair[0])
    return choices


def _effect_klasse_by_id(edit_current: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in edit_current.get("effect_klassen", []):
        kid = str(row.get("klasse_id") or "")
        if kid:
            out[kid] = row
    return out


def apply_effect_klassen_from_library(
    edit_current: dict[str, Any],
    *,
    target_fm_id: str,
    selected_klasse_ids: tuple[str, ...],
    existing_link_ids: set[str],
) -> EffectScopeCopy:
    """Vervang FM-effectlinks door links naar gekozen effectklassen."""
    klasse_by_id = _effect_klasse_by_id(edit_current)
    link_ids = set(existing_link_ids)
    fm_rows: list[dict[str, Any]] = []
    for klasse_id in selected_klasse_ids:
        if klasse_id not in klasse_by_id:
            continue
        fm_rows.append(
            {
                "link_id": _next_id("FMEL", link_ids),
                "fm_id": target_fm_id,
                "klasse_id": klasse_id,
                "fractie": 1.0,
                "aanname_fractie": "",
            }
        )
        link_ids.add(str(fm_rows[-1]["link_id"]))
    merged_klassen: list[dict[str, Any]] = []
    seen: set[str] = set()
    for klasse_id in selected_klasse_ids:
        row = klasse_by_id.get(klasse_id)
        if row is not None and klasse_id not in seen:
            merged_klassen.append(copy.deepcopy(row))
            seen.add(klasse_id)
    return EffectScopeCopy(
        fm_effect_rows=tuple(fm_rows),
        pm_effect_rows=(),
        effect_klasse_rows=tuple(merged_klassen),
    )


def apply_rev_tasks_from_library(
    edit_current: dict[str, Any],
    *,
    target_fm_id: str,
    selected_pm_ids: tuple[str, ...],
    existing_pm_ids: set[str],
) -> PreventiefScopeCopy:
    """Kloon gekozen REV-taken naar doel-FM met nieuwe pm_id's."""
    pm_by_id = {
        str(row.get("pm_id")): row
        for row in edit_current.get("pm_tasks", [])
        if row.get("pm_id")
    }
    pm_ids = set(existing_pm_ids)
    rows: list[dict[str, Any]] = []
    for source_pm_id in selected_pm_ids:
        source = pm_by_id.get(source_pm_id)
        if source is None:
            continue
        copied = copy.deepcopy(source)
        copied["fm_id"] = target_fm_id
        copied["pm_id"] = _next_id("PM", pm_ids)
        pm_ids.add(str(copied["pm_id"]))
        copied["task_group_id"] = None
        rows.append(copied)
    return PreventiefScopeCopy(pm_task_rows=tuple(rows))
