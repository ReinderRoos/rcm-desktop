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
from rcm_desktop.adapter.result_filter_service import collect_pbs_subtree_ids
from rcm_desktop.adapter.results_workspace_state import MODE_LCC, WorkspaceStateSnapshot


@dataclass(frozen=True)
class MeekoppelPreviewGate:
    """Rij+anker waarvoor preview is gezien en apply mag."""

    pbs_id: str
    anchor: MeekoppelAnchor


@dataclass(frozen=True)
class MeekoppelPanelView:
    panel_active: bool
    whatif_active: bool
    window_spin_enabled: bool
    table_visible: bool
    preview_enabled: bool
    apply_enabled: bool
    show_whatif_hint: bool
    empty_label_text: str | None
    rows: tuple[MeekoppelLocationGroup, ...]


def _filter_groups_by_scope(
    session: ProjectSession,
    rows: tuple[MeekoppelLocationGroup, ...],
    scope_id: str | None,
) -> tuple[tuple[MeekoppelLocationGroup, ...], str | None]:
    if scope_id is None:
        if not rows:
            return (), None
        return rows, None

    project = session.loaded.core()
    if scope_id not in project.pbs_items:
        return (), None

    subtree = collect_pbs_subtree_ids(project, scope_id)
    filtered = tuple(row for row in rows if row.pbs_id in subtree)
    if filtered:
        return filtered, None
    if rows:
        from rcm_desktop import messages

        return (), messages.WORKSPACE_MEEKOPPEL_EMPTY_SCOPE
    return (), None


def sync_meekoppel_panel(
    session: ProjectSession | None,
    snapshot: WorkspaceStateSnapshot,
    *,
    window_years: int,
    preview_gate: MeekoppelPreviewGate | None = None,
    selected_pbs_id: str | None = None,
    current_anchor: MeekoppelAnchor = "later",
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
            empty_label_text=None,
            rows=(),
        )

    all_rows = discover_meekoppel_locations(session.loaded.core(), window_years=window_years)
    rows, empty_label_text = _filter_groups_by_scope(session, all_rows, snapshot.scope_id)
    if not rows and empty_label_text is None and not all_rows:
        from rcm_desktop import messages

        empty_label_text = messages.WORKSPACE_MEEKOPPEL_EMPTY

    apply_enabled = (
        preview_gate is not None
        and selected_pbs_id is not None
        and preview_gate.pbs_id == selected_pbs_id
        and preview_gate.anchor == current_anchor
    )

    return MeekoppelPanelView(
        panel_active=True,
        whatif_active=True,
        window_spin_enabled=True,
        table_visible=bool(rows),
        preview_enabled=True,
        apply_enabled=apply_enabled,
        show_whatif_hint=False,
        empty_label_text=empty_label_text,
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
