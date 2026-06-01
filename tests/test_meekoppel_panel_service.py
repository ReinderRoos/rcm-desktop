"""Issue 2 — meekoppel_panel_service (TDD)."""

from __future__ import annotations

from rcm_core.config import RCMConfig
from rcm_core.models import Faalwijze, PBSItem, RCMProject, PMTask, TaskType

from rcm_desktop import messages
from rcm_desktop.adapter.loaded_project import LoadedProject
from rcm_desktop.adapter.meekoppel_panel_service import (
    MeekoppelPreviewGate,
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
            "PM-C": PMTask("PM-C", "FM-2", TaskType.REV, interval_jaar=7.0),
            "PM-D": PMTask("PM-D", "FM-2", TaskType.REV, interval_jaar=8.0),
        },
    )


def test_sync_meekoppel_panel_disabled_without_whatif() -> None:
    project = _project_with_rev_tasks()
    session = ProjectSession.from_parts(LoadedProject.from_core(project))
    ws = ResultsWorkspaceState()
    ws.set_modus(MODE_LCC)
    snapshot = ws.snapshot()

    panel = sync_meekoppel_panel(session, snapshot, window_years=2)
    assert panel.preview_enabled is False
    assert panel.rows == ()


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
        preview_gate=MeekoppelPreviewGate(pbs_id="P1", anchor="later"),
        selected_pbs_id="P1",
        current_anchor="later",
    )
    assert gated.apply_enabled is True


def test_sync_meekoppel_panel_scope_filter_empty_message() -> None:
    project = _project_with_rev_tasks()
    session = ProjectSession.from_parts(LoadedProject.from_core(project))
    ws = ResultsWorkspaceState()
    ws.set_modus(MODE_LCC)
    ws.set_scope("ROOT")
    ws.set_planning_overlay(ws.snapshot().planning_overlay.begin_what_if())
    snapshot = ws.snapshot()

    panel = sync_meekoppel_panel(session, snapshot, window_years=2)
    assert len(panel.rows) == 2

    ws.set_scope("P1")
    snapshot = ws.snapshot()
    panel = sync_meekoppel_panel(session, snapshot, window_years=2)
    assert len(panel.rows) == 1
    assert panel.rows[0].pbs_id == "P1"

    ws.set_scope("P2")
    snapshot = ws.snapshot()
    panel = sync_meekoppel_panel(session, snapshot, window_years=2)
    assert len(panel.rows) == 1
    assert panel.rows[0].pbs_id == "P2"
    assert panel.empty_label_text is None

