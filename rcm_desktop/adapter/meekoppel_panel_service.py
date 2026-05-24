"""Meekoppel panel orchestrator — Qt-vrije sync/preview/apply (slice 41)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_desktop.adapter.meekoppel_apply_service import (
    MeekoppelAnchor,
    MeekoppelLocationPreview,
    apply_meekoppel_location,
    preview_meekoppel_location,
)
from rcm_desktop.adapter.meekoppelkansen_discovery_service import (
    MeekoppelLocationGroup,
    discover_meekoppel_locations,
)
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.planning_whatif_service import WhatIfActionResult
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.results_workspace_state import MODE_LCC, WorkspaceStateSnapshot


@dataclass(frozen=True)
class MeekoppelPanelView:
  panel_active: bool
  whatif_active: bool
  window_spin_enabled: bool
  table_visible: bool
  preview_enabled: bool
  apply_enabled: bool
  show_whatif_hint: bool
  show_empty_label: bool
  rows: tuple[MeekoppelLocationGroup, ...]


def sync_meekoppel_panel(
    session: ProjectSession | None,
    snapshot: WorkspaceStateSnapshot,
    *,
    window_years: int,
) -> MeekoppelPanelView:
    overlay = snapshot.planning_overlay
    whatif = overlay.active
    if session is None or not whatif:
        return MeekoppelPanelView(
            panel_active=snapshot.modus == MODE_LCC,
            whatif_active=False,
            window_spin_enabled=False,
            table_visible=False,
            preview_enabled=False,
            apply_enabled=False,
            show_whatif_hint=True,
            show_empty_label=False,
            rows=(),
        )
    rows = discover_meekoppel_locations(session.loaded.core(), window_years=window_years)
    empty = len(rows) == 0
    return MeekoppelPanelView(
        panel_active=True,
        whatif_active=True,
        window_spin_enabled=True,
        table_visible=not empty,
        preview_enabled=True,
        apply_enabled=True,
        show_whatif_hint=False,
        show_empty_label=empty,
        rows=rows,
    )


def preview_meekoppel(
    session: ProjectSession,
    overlay: PlanningOverlayState,
    group: MeekoppelLocationGroup,
    *,
    anchor: MeekoppelAnchor,
) -> MeekoppelLocationPreview:
    return preview_meekoppel_location(
        session.loaded.core(), overlay, group, anchor=anchor
    )


def apply_meekoppel(
    session: ProjectSession,
    overlay: PlanningOverlayState,
    group: MeekoppelLocationGroup,
    *,
    anchor: MeekoppelAnchor,
) -> WhatIfActionResult:
    return apply_meekoppel_location(
        session.loaded.core(), overlay, group, anchor=anchor
    )
