"""Smalle kopie tussen faalwijze-rijen en editor-secties (slice 59.3 / 105.23)."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Literal

from rcm_desktop.adapter.fm_edit_bundle_service import FmEditBundle

CopySection = Literal["basis", "correctief"]

_BASIS_FIELDS = (
    "failure_type",
    "mttf_jaar",
    "sigma_jaar",
    "aging_distribution",
    "beta_jaar",
    "is_evident",
    "repair_quality",
    "faalwijze_omschrijving",
    "p_ongewenste_gebeurtenis",
    "eindgevolg",
)

_CORRECTIEF_FIELDS = (
    "cost_cm_eur",
    "downtime_per_failure",
    "notes",
    "aanname_cm_kosten",
    "aanname_downtime",
)


def copy_fields(
    source_row: dict[str, Any],
    target_row: dict[str, Any],
    *,
    sections: tuple[CopySection, ...] = ("basis", "correctief"),
) -> dict[str, Any]:
    """Kopieer geselecteerde secties; ids en FK's in ``target_row`` blijven intact."""
    out = dict(target_row)
    fields: list[str] = []
    if "basis" in sections:
        fields.extend(_BASIS_FIELDS)
    if "correctief" in sections:
        fields.extend(_CORRECTIEF_FIELDS)
    for field in fields:
        if field in source_row:
            value = source_row[field]
            if field == "downtime_per_failure" and isinstance(value, dict):
                out[field] = dict(value)
            else:
                out[field] = value
    return out


def _next_id(prefix: str, existing: set[str]) -> str:
    n = 1
    while True:
        candidate = f"{prefix}-{n:03d}"
        if candidate not in existing:
            return candidate
        n += 1


@dataclass(frozen=True)
class EffectScopeCopy:
    fm_effect_rows: tuple[dict[str, Any], ...]
    pm_effect_rows: tuple[dict[str, Any], ...]
    effect_klasse_rows: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class PreventiefScopeCopy:
    pm_task_rows: tuple[dict[str, Any], ...]


def copy_effect_scope(
    source: FmEditBundle,
    *,
    target_fm_id: str,
    existing_link_ids: set[str],
) -> EffectScopeCopy:
    """Kopieer effecten-tab: FM-links + effectklassen; PM-links worden geleegd."""
    link_ids = set(existing_link_ids)
    fm_rows: list[dict[str, Any]] = []
    for row in source.fm_effect_rows:
        copied = copy.deepcopy(row)
        copied["fm_id"] = target_fm_id
        copied["link_id"] = _next_id("FMEL", link_ids)
        link_ids.add(str(copied["link_id"]))
        fm_rows.append(copied)
    klasse_ids = {str(r.get("klasse_id")) for r in fm_rows if r.get("klasse_id")}
    merged_klassen: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in source.effect_klasse_rows:
        kid = str(row.get("klasse_id") or "")
        if kid in klasse_ids and kid not in seen:
            merged_klassen.append(copy.deepcopy(row))
            seen.add(kid)
    return EffectScopeCopy(
        fm_effect_rows=tuple(fm_rows),
        pm_effect_rows=(),
        effect_klasse_rows=tuple(merged_klassen),
    )


def copy_preventief_scope(
    source: FmEditBundle,
    *,
    target_fm_id: str,
    existing_pm_ids: set[str],
) -> PreventiefScopeCopy:
    """Kopieer PM-taken; nieuwe pm_id's, geen taakgroep-koppeling."""
    pm_ids = set(existing_pm_ids)
    rows: list[dict[str, Any]] = []
    for row in source.pm_task_rows:
        copied = copy.deepcopy(row)
        copied["fm_id"] = target_fm_id
        copied["pm_id"] = _next_id("PM", pm_ids)
        pm_ids.add(str(copied["pm_id"]))
        copied["task_group_id"] = None
        rows.append(copied)
    return PreventiefScopeCopy(pm_task_rows=tuple(rows))
