"""Slice 106 issue 02 — FaalwijzePresentationBundle in RenderPlan."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from rcm_desktop.adapter.compare_slot_state import CompareSlotState
from rcm_desktop.adapter.loaded_project import LoadedProject
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.results_workspace_orchestrator import (
    ResultsWorkspaceOrchestrator,
    WorkspaceRenderContext,
)
from rcm_desktop.adapter.results_workspace_state import MODE_FM_DETAIL, ResultsWorkspaceState
from rcm_desktop.adapter.workspace_render_index import WorkspaceRenderIndex

from tests.test_desktop_results_workspace_window import _done_run_for_fixture, _three_level_project

RCM_DESKTOP = Path(__file__).resolve().parent.parent / "rcm_desktop"


def test_orchestrator_fm_single_run_includes_bundle() -> None:
    project = _three_level_project()
    run = _done_run_for_fixture()
    session = ProjectSession.from_parts(LoadedProject.from_core(project), run=run)
    state = ResultsWorkspaceState()
    snapshot = replace(state.snapshot(), modus=MODE_FM_DETAIL, compare_mode=False)
    ctx = WorkspaceRenderContext(
        session=session,
        compare_slots=CompareSlotState(),
        project_total_presentation=None,
        render_index=WorkspaceRenderIndex(),
        prev_lcc_snapshot=None,
    )
    plan = ResultsWorkspaceOrchestrator.plan_render(snapshot, ctx)
    assert plan.kind == "fm"
    assert plan.faalwijze_bundle is not None
    assert plan.faalwijze_bundle.single_run is not None
    assert plan.faalwijze_bundle.chart_presentation() is not None


def test_views_do_not_import_faalwijze_builders() -> None:
    views_root = RCM_DESKTOP / "views"
    offenders: list[str] = []
    for path in views_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "build_faalwijze_" in text:
            offenders.append(str(path.relative_to(RCM_DESKTOP.parent)))
    assert offenders == []
