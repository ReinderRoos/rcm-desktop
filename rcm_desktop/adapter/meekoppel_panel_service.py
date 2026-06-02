"""Meekoppel panel orchestrator — Qt-vrije sync/preview/apply (slice 41)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_core.models import RCMProject

from rcm_desktop.adapter.meekoppel_apply_service import (
    MeekoppelAnchor,
    MeekoppelLocationPreview,
    apply_meekoppel_rev_tasks,
    preview_meekoppel_rev_tasks,
)
from rcm_desktop.adapter.meekoppel_display_service import location_group_tooltip
from rcm_desktop.adapter.meekoppelkansen_discovery_service import (
    MeekoppelLocationGroup,
    MeekoppelRevTask,
    covered_pbs_for_selection,
    collect_rev_tasks_for_pbs_selection,
    discover_meekoppel_locations,
    pbs_selection_path_label,
)
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.planning_whatif_service import WhatIfActionResult
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.result_filter_service import collect_pbs_subtree_ids
from rcm_desktop.adapter.results_workspace_state import MODE_LCC, WorkspaceStateSnapshot


@dataclass(frozen=True)
class MeekoppelPreviewGate:
    """PBS-selectie+anker waarvoor preview is gezien en apply mag."""

    pbs_ids: frozenset[str]
    anchor: MeekoppelAnchor


@dataclass(frozen=True)
class MeekoppelPanelColumn:
    header: str


@dataclass(frozen=True)
class MeekoppelPanelRow:
    """Display-DTO voor één meekoppelkans-rij (view bindt alleen strings)."""

    pbs_id: str
    path_label: str
    rev_count_text: str
    due_range_text: str
    span_text: str
    path_tooltip: str


@dataclass(frozen=True)
class MeekoppelPanelView:
    panel_active: bool
    whatif_active: bool
    window_spin_enabled: bool
    table_visible: bool
    preview_enabled: bool
    apply_enabled: bool
    show_whatif_hint: bool
    selection_summary_text: str | None
    empty_label_text: str | None
    columns: tuple[MeekoppelPanelColumn, ...]
    rows: tuple[MeekoppelPanelRow, ...]
    location_groups: tuple[MeekoppelLocationGroup, ...] = ()


def meekoppel_panel_columns() -> tuple[MeekoppelPanelColumn, ...]:
    from rcm_desktop import messages

    return (
        MeekoppelPanelColumn(messages.WORKSPACE_MEEKOPPEL_HEADER_PATH),
        MeekoppelPanelColumn(messages.WORKSPACE_MEEKOPPEL_HEADER_REV_COUNT),
        MeekoppelPanelColumn(messages.WORKSPACE_MEEKOPPEL_HEADER_DUE_RANGE),
        MeekoppelPanelColumn(messages.WORKSPACE_MEEKOPPEL_HEADER_SPAN),
    )


def build_meekoppel_panel_row(
    project: RCMProject,
    group: MeekoppelLocationGroup,
    *,
    overlay: PlanningOverlayState | None = None,
) -> MeekoppelPanelRow:
    return MeekoppelPanelRow(
        pbs_id=group.pbs_id,
        path_label=group.path_label,
        rev_count_text=str(group.rev_count),
        due_range_text=group.due_range_label(),
        span_text=str(group.span_jaar),
        path_tooltip=location_group_tooltip(project, group, overlay=overlay),
    )


def _group_visible_in_covered(
    row: MeekoppelLocationGroup, covered: frozenset[str]
) -> bool:
    return any(task.pbs_id in covered for task in row.tasks)


def _filter_groups_by_scope(
    session: ProjectSession,
    rows: tuple[MeekoppelLocationGroup, ...],
    scope_id: str | None,
    *,
    selected_pbs_ids: frozenset[str] | None = None,
) -> tuple[tuple[MeekoppelLocationGroup, ...], str | None]:
    project = session.loaded.core()
    if selected_pbs_ids:
        covered = covered_pbs_for_selection(project, selected_pbs_ids)
        if not covered:
            return (), None
        filtered = tuple(
            row for row in rows if _group_visible_in_covered(row, covered)
        )
        if filtered:
            return filtered, None
        if rows:
            from rcm_desktop import messages

            return (), messages.WORKSPACE_MEEKOPPEL_EMPTY_SCOPE
        return (), None

    if scope_id is None:
        if not rows:
            return (), None
        return rows, None

    if scope_id not in project.pbs_items:
        return (), None

    subtree = frozenset(collect_pbs_subtree_ids(project, scope_id))
    filtered = tuple(row for row in rows if _group_visible_in_covered(row, subtree))
    if filtered:
        return filtered, None
    if rows:
        from rcm_desktop import messages

        return (), messages.WORKSPACE_MEEKOPPEL_EMPTY_SCOPE
    return (), None


def _selection_summary_text(
    session: ProjectSession,
    selected_pbs_ids: frozenset[str] | None,
) -> str | None:
    if not selected_pbs_ids:
        return None
    from rcm_desktop import messages

    project = session.loaded.core()
    tasks = collect_rev_tasks_for_pbs_selection(project, selected_pbs_ids)
    if not tasks:
        return messages.WORKSPACE_MEEKOPPEL_SELECTION_NONE
    path = pbs_selection_path_label(project, selected_pbs_ids)
    return messages.WORKSPACE_MEEKOPPEL_SELECTION_COUNT.format(
        count=len(tasks),
        path=path,
    )


def _pbs_ids_label(pbs_ids: frozenset[str]) -> str:
    return ", ".join(sorted(pbs_ids))


def _resolve_pbs_selection_bundle(
    session: ProjectSession,
    pbs_ids: frozenset[str],
) -> tuple[str, str, tuple[MeekoppelRevTask, ...]] | None:
    if not pbs_ids:
        return None
    project = session.loaded.core()
    tasks = collect_rev_tasks_for_pbs_selection(project, pbs_ids)
    if not tasks:
        return None
    return (
        _pbs_ids_label(pbs_ids),
        pbs_selection_path_label(project, pbs_ids),
        tasks,
    )


def sync_meekoppel_panel(
    session: ProjectSession | None,
    snapshot: WorkspaceStateSnapshot,
    *,
    window_years: int,
    preview_gate: MeekoppelPreviewGate | None = None,
    selected_pbs_ids: frozenset[str] | None = None,
    current_anchor: MeekoppelAnchor = "later",
) -> MeekoppelPanelView:
    columns = meekoppel_panel_columns()
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
            selection_summary_text=None,
            empty_label_text=None,
            columns=columns,
            rows=(),
            location_groups=(),
        )

    project = session.loaded.core()
    all_rows = discover_meekoppel_locations(project, window_years=window_years)
    groups, empty_label_text = _filter_groups_by_scope(
        session,
        all_rows,
        snapshot.scope_id,
        selected_pbs_ids=selected_pbs_ids,
    )
    selection_summary_text = _selection_summary_text(session, selected_pbs_ids)
    if not groups and empty_label_text is None and not all_rows:
        from rcm_desktop import messages

        empty_label_text = messages.WORKSPACE_MEEKOPPEL_EMPTY

    panel_rows = tuple(
        build_meekoppel_panel_row(project, g, overlay=overlay) for g in groups
    )

    apply_enabled = (
        preview_gate is not None
        and selected_pbs_ids is not None
        and preview_gate.pbs_ids == selected_pbs_ids
        and preview_gate.anchor == current_anchor
    )

    return MeekoppelPanelView(
        panel_active=True,
        whatif_active=True,
        window_spin_enabled=True,
        table_visible=bool(panel_rows),
        preview_enabled=True,
        apply_enabled=apply_enabled,
        show_whatif_hint=False,
        selection_summary_text=selection_summary_text,
        empty_label_text=empty_label_text,
        columns=columns,
        rows=panel_rows,
        location_groups=groups,
    )


def preview_meekoppel(
    session: ProjectSession,
    overlay: PlanningOverlayState,
    pbs_ids: frozenset[str],
    *,
    anchor: MeekoppelAnchor,
) -> MeekoppelLocationPreview:
    bundle = _resolve_pbs_selection_bundle(session, pbs_ids)
    if bundle is None:
        from rcm_desktop import messages

        return MeekoppelLocationPreview(
            pbs_id="",
            path_label="",
            target_year=0,
            moves=(),
            blocked_reason=messages.WORKSPACE_MEEKOPPEL_SELECT_PBS,
        )
    pbs_id_label, path_label, tasks = bundle
    return preview_meekoppel_rev_tasks(
        session.loaded.core(),
        overlay,
        pbs_id_label=pbs_id_label,
        path_label=path_label,
        tasks=tasks,
        anchor=anchor,
    )


def apply_meekoppel(
    session: ProjectSession,
    overlay: PlanningOverlayState,
    pbs_ids: frozenset[str],
    *,
    anchor: MeekoppelAnchor,
) -> WhatIfActionResult:
    bundle = _resolve_pbs_selection_bundle(session, pbs_ids)
    if bundle is None:
        from rcm_desktop import messages

        return WhatIfActionResult(
            overlay=overlay,
            error=messages.WORKSPACE_MEEKOPPEL_SELECT_PBS,
        )
    pbs_id_label, path_label, tasks = bundle
    return apply_meekoppel_rev_tasks(
        session.loaded.core(),
        overlay,
        pbs_id_label=pbs_id_label,
        path_label=path_label,
        tasks=tasks,
        anchor=anchor,
    )
