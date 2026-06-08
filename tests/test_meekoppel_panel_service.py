"""Issue 2 — meekoppel_panel_service (TDD)."""

from __future__ import annotations

from rcm_core.config import RCMConfig
from rcm_core.models import Faalwijze, PBSItem, RCMProject, PMTask, TaskType

from rcm_desktop import messages
from rcm_desktop.adapter.loaded_project import LoadedProject
from rcm_desktop.adapter.meekoppel_panel_service import (
    MeekoppelPreviewGate,
    build_meekoppel_panel_row,
    meekoppel_panel_columns,
    sync_meekoppel_panel,
)
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.results_workspace_state import MODE_LCC, ResultsWorkspaceState


def _project_with_rev_tasks() -> RCMProject:
    return RCMProject(
        config=RCMConfig(lifecycle_years=40.0, modeljaar=2026),
        pbs_items={
            "P1": PBSItem("P1", "obj", "el", "Pump", parent_pbs_id="ROOT"),
            "P2": PBSItem("P2", "obj", "el", "Valve", parent_pbs_id="ROOT"),
            "ROOT": PBSItem("ROOT", "obj", "el", "Site"),
        },
        faalwijzes={
            "FM-1": Faalwijze("FM-1", "P1", "F1", "Leak"),
            "FM-2": Faalwijze("FM-2", "P2", "F1", "Wear"),
        },
        pm_tasks={
            "PM-A": PMTask("PM-A", "FM-1", TaskType.REV, interval_jaar=5.0),
            "PM-B": PMTask("PM-B", "FM-1", TaskType.REV, interval_jaar=6.0),
            "PM-C": PMTask("PM-C", "FM-2", TaskType.REV, interval_jaar=6.0),
            "PM-D": PMTask("PM-D", "FM-2", TaskType.REV, interval_jaar=7.0),
        },
    )


def test_meekoppel_panel_columns_match_messages() -> None:
    cols = meekoppel_panel_columns()
    assert tuple(c.header for c in cols) == (
        messages.WORKSPACE_MEEKOPPEL_HEADER_PATH,
        messages.WORKSPACE_MEEKOPPEL_HEADER_REV_COUNT,
        messages.WORKSPACE_MEEKOPPEL_HEADER_DUE_RANGE,
        messages.WORKSPACE_MEEKOPPEL_HEADER_SPAN,
    )


def test_build_meekoppel_panel_row_includes_tooltip() -> None:
    from rcm_desktop.adapter.meekoppelkansen_discovery_service import (
        discover_meekoppel_locations,
    )

    project = _project_with_rev_tasks()
    group = discover_meekoppel_locations(project, window_years=2)[0]
    row = build_meekoppel_panel_row(project, group)
    assert row.pbs_id == group.pbs_id
    assert row.path_label == group.path_label
    assert row.due_range_text == group.due_range_label()
    assert "PBS-id:" in row.path_tooltip
    assert group.pbs_id in row.path_tooltip


def test_sync_meekoppel_panel_disabled_without_whatif() -> None:
    project = _project_with_rev_tasks()
    session = ProjectSession.from_parts(LoadedProject.from_core(project))
    ws = ResultsWorkspaceState()
    ws.set_modus(MODE_LCC)
    snapshot = ws.snapshot()

    panel = sync_meekoppel_panel(session, snapshot, window_years=2)
    assert panel.preview_enabled is False
    assert panel.rows == ()
    assert len(panel.columns) == 4


def test_sync_meekoppel_panel_apply_requires_preview_gate() -> None:
    project = _project_with_rev_tasks()
    session = ProjectSession.from_parts(LoadedProject.from_core(project))
    ws = ResultsWorkspaceState()
    ws.set_modus(MODE_LCC)
    ws.set_planning_overlay(ws.snapshot().planning_overlay.begin_what_if())
    snapshot = ws.snapshot()

    panel = sync_meekoppel_panel(session, snapshot, window_years=2)
    assert panel.apply_enabled is False

    gated = sync_meekoppel_panel(
        session,
        snapshot,
        window_years=2,
        preview_gate=MeekoppelPreviewGate(pbs_ids=frozenset({"P1"}), anchor="later"),
        selected_pbs_ids=frozenset({"P1"}),
        current_anchor="later",
    )
    assert gated.apply_enabled is True


def test_collect_rev_tasks_for_multi_pbs_selection() -> None:
    from rcm_desktop.adapter.meekoppelkansen_discovery_service import (
        collect_rev_tasks_for_pbs_selection,
    )

    project = _project_with_rev_tasks()
    tasks = collect_rev_tasks_for_pbs_selection(project, frozenset({"P1", "P2"}))
    assert len(tasks) == 4
    assert {t.pm_id for t in tasks} == {"PM-A", "PM-B", "PM-C", "PM-D"}


def test_preview_meekoppel_multi_pbs_selection() -> None:
    from rcm_desktop.adapter.meekoppel_panel_service import preview_meekoppel

    project = _project_with_rev_tasks()
    session = ProjectSession.from_parts(LoadedProject.from_core(project))
    ws = ResultsWorkspaceState()
    ws.set_planning_overlay(ws.snapshot().planning_overlay.begin_what_if())
    overlay = ws.snapshot().planning_overlay

    prev = preview_meekoppel(
        session,
        overlay,
        frozenset({"P1", "P2"}),
        anchor="later",
    )
    assert prev.blocked_reason is None
    assert len(prev.moves) == 3
    assert prev.target_year == 7


def test_scope_filter_shows_parent_group_when_only_leaf_in_subtree() -> None:
    from rcm_desktop.adapter.meekoppelkansen_discovery_service import (
        discover_meekoppel_locations,
    )

    project = _project_with_rev_tasks()
    groups = discover_meekoppel_locations(project, window_years=2)
    assert len(groups) == 1
    assert groups[0].pbs_id == "ROOT"

    session = ProjectSession.from_parts(LoadedProject.from_core(project))
    ws = ResultsWorkspaceState()
    ws.set_modus(MODE_LCC)
    ws.set_scope("P1")
    ws.set_planning_overlay(ws.snapshot().planning_overlay.begin_what_if())
    panel = sync_meekoppel_panel(session, ws.snapshot(), window_years=2)
    assert len(panel.rows) == 1
    assert panel.rows[0].pbs_id == "ROOT"


def test_sync_meekoppel_panel_scope_filter_empty_message() -> None:
    project = _project_with_rev_tasks()
    session = ProjectSession.from_parts(LoadedProject.from_core(project))
    ws = ResultsWorkspaceState()
    ws.set_modus(MODE_LCC)
    ws.set_scope("ROOT")
    ws.set_planning_overlay(ws.snapshot().planning_overlay.begin_what_if())
    snapshot = ws.snapshot()

    panel = sync_meekoppel_panel(session, snapshot, window_years=2)
    assert len(panel.rows) == 1
    assert panel.rows[0].pbs_id == "ROOT"

    ws.set_scope("P1")
    snapshot = ws.snapshot()
    panel = sync_meekoppel_panel(session, snapshot, window_years=2)
    assert len(panel.rows) == 1
    assert panel.rows[0].pbs_id == "ROOT"

    ws.set_scope("P2")
    snapshot = ws.snapshot()
    panel = sync_meekoppel_panel(session, snapshot, window_years=2)
    assert len(panel.rows) == 1
    assert panel.rows[0].pbs_id == "ROOT"
    assert panel.empty_label_text is None
