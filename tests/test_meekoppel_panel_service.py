"""Issue 2 — meekoppel_panel_service (TDD)."""

from __future__ import annotations

from rcm_core.config import RCMConfig
from rcm_core.models import Faalwijze, PBSItem, RCMProject, PMTask, TaskType

from rcm_desktop.adapter.loaded_project import LoadedProject
from rcm_desktop.adapter.meekoppel_panel_service import sync_meekoppel_panel
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.results_workspace_state import MODE_LCC, ResultsWorkspaceState


def _project_with_rev_tasks() -> RCMProject:
    return RCMProject(
        config=RCMConfig(lifecycle_years=40.0, modeljaar=2026),
        pbs_items={"P1": PBSItem("P1", "obj", "el", "Pump")},
        faalwijzes={"FM-1": Faalwijze("FM-1", "P1", "F1", "Leak")},
        pm_tasks={
            "PM-A": PMTask("PM-A", "FM-1", TaskType.REV, interval_jaar=5.0),
            "PM-B": PMTask("PM-B", "FM-1", TaskType.REV, interval_jaar=6.0),
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
