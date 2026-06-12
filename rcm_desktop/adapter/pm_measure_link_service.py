"""Koppel PM-rij aan bestaande taakgroep (slice 59.4)."""

from __future__ import annotations

from typing import Any

from rcm_core.editing.validation import normalize_key
from rcm_core.models import RCMProject

from rcm_desktop.adapter.editing_session import EditingSession
from rcm_desktop.adapter.task_group_catalog_service import TaskGroupCatalogEntry, list_task_groups


def _find_group(
    source: RCMProject | EditingSession, group_id: str
) -> TaskGroupCatalogEntry | None:
    target = normalize_key(group_id)
    for entry in list_task_groups(source):
        if entry.group_id == target:
            return entry
    return None


def apply_task_group_link(
    pm_row: dict[str, Any],
    group_id: str,
    source: RCMProject | EditingSession,
) -> dict[str, Any]:
    """Stel ``task_group_id`` in en erf gedeelde velden uit taakgroep."""
    entry = _find_group(source, group_id)
    if entry is None:
        raise KeyError(f"Onbekende taakgroep: {group_id}")
    out = dict(pm_row)
    out["task_group_id"] = entry.group_id
    if entry.interval_jaar > 0:
        out["interval_jaar"] = entry.interval_jaar
    if entry.cost_eur > 0:
        out["cost_eur"] = entry.cost_eur
    return out
