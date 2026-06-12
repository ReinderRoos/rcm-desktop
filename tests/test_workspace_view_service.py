"""Issue 1 — workspace_view_service modus builders (TDD)."""

from __future__ import annotations

from rcm_core.config import RCMConfig
from rcm_core.models import Faalwijze, FMResult, PBSItem, RCMProject

from rcm_desktop.adapter.loaded_project import LoadedProject
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.results_workspace_state import (
    MODE_BIJDRAGEN,
    MODE_FM_DETAIL,
    ResultsWorkspaceState,
)
from rcm_desktop.adapter.run_service import build_run_result
from rcm_desktop.adapter.workspace_render_index import WorkspaceRenderIndex
from rcm_desktop.adapter.workspace_view_service import (
    build_bijdragen_view,
    build_fm_detail_view,
    build_workspace_cache_modus_key,
)


def _project_with_fm() -> RCMProject:
    return RCMProject(
        config=RCMConfig(lifecycle_years=40.0, modeljaar=2026),
        pbs_items={
            "P1": PBSItem("P1", "obj", "el", "Pump"),
        },
        faalwijzes={
            "FM-1": Faalwijze("FM-1", "P1", "F1", "Leak", is_evident=True),
            "FM-2": Faalwijze("FM-2", "P1", "F1", "Hidden", is_evident=False),
        },
    )


def _fm_result(fm_id: str, pbs_id: str = "P1") -> FMResult:
    return FMResult(
        fm_id=fm_id,
        pbs_id=pbs_id,
        p_failure_lifecycle=0.1,
        expected_failures=1.0,
        expected_raw_downtime_hr=1.0,
        expected_detection_delay_hr=0.0,
        expected_total_downtime_hr=1.0,
        expected_pm_downtime_hr=0.0,
        expected_cm_cost_eur=50.0,
        pm_cost_eur=0.0,
        total_cost_eur=50.0,
        risk_contribution=0.01,
        effect_bijdragen={},
    )


def _session(project: RCMProject, fm_results: list[FMResult]) -> ProjectSession:
    run = build_run_result(project, fm_results)
    loaded = LoadedProject.from_core(project)
    return ProjectSession.from_parts(loaded, run=run)


def test_build_fm_detail_view_returns_all_fm_rows() -> None:
    project = _project_with_fm()
    session = _session(project, [_fm_result("FM-1"), _fm_result("FM-2")])
    ws = ResultsWorkspaceState()
    ws.set_modus(MODE_FM_DETAIL)
    snapshot = ws.snapshot()

    view = build_fm_detail_view(session, snapshot)
    assert view is not None
    assert [r.fm_id for r in view.fm_rows] == ["FM-1", "FM-2"]


def test_build_fm_detail_view_returns_none_without_completed_run() -> None:
    project = _project_with_fm()
    loaded = LoadedProject.from_core(project)
    session = ProjectSession.from_parts(loaded, run=None)
    snapshot = ResultsWorkspaceState().snapshot()

    assert build_fm_detail_view(session, snapshot) is None


def test_build_bijdragen_view_builds_contribution_rows() -> None:
    project = _project_with_fm()
    session = _session(project, [_fm_result("FM-1")])
    ws = ResultsWorkspaceState()
    ws.set_modus(MODE_BIJDRAGEN)
    snapshot = ws.snapshot()
    render_index = WorkspaceRenderIndex()

    view = build_bijdragen_view(
        session,
        snapshot,
        render_index=render_index,
        project_total_presentation=None,
    )
    assert view is not None
    assert len(view.contribution_rows) >= 1
    assert view.cache_modus_key == build_workspace_cache_modus_key(snapshot)
    assert view.from_presentation_cache is False
