"""LTAP preset-view helpers (slice 82)."""

from __future__ import annotations

from dataclasses import replace

from rcm_desktop.adapter.lcc_type_filter import LCCTypeFilterSet
from rcm_desktop.adapter.results_workspace_state import WorkspaceStateSnapshot
from rcm_desktop.adapter.workspace_view_registry import (
    WORKSPACE_VIEW_REGISTRY,
    view_by_id,
)


def lcc_preset_for_view(view_id: str):
    entry = view_by_id(WORKSPACE_VIEW_REGISTRY, view_id)
    if entry is None:
        return None
    return entry.lcc_preset


def effective_lcc_filters(snapshot: WorkspaceStateSnapshot) -> LCCTypeFilterSet:
    """Presentatiefilters: preset forceert CM uit zonder snapshot.lcc_filters te wijzigen."""
    preset = lcc_preset_for_view(snapshot.active_view_id)
    if preset is None or preset.cm_enabled:
        return snapshot.lcc_filters
    return replace(snapshot.lcc_filters, cm=False)
