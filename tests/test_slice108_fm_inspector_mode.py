"""Slice 108 issue 03 — FM-inspectiemodus state + orchestrator."""

from __future__ import annotations

from rcm_desktop.adapter.faalwijze_analyse_service import FM_COMPARE_VIEW_DIAGRAM, FM_COMPARE_VIEW_TABLE
from rcm_desktop.adapter.results_workspace_orchestrator import ResultsWorkspaceOrchestrator
from rcm_desktop.adapter.results_workspace_state import (
    FM_VIEW_MODE_DIAGRAM,
    FM_VIEW_MODE_TABLE,
    MODE_FM_DETAIL,
    ResultsWorkspaceState,
    WorkspaceStateSnapshot,
)
from rcm_desktop.adapter.workspace_view_registry import SIDE_OUTPUT


def _snap(**kwargs) -> WorkspaceStateSnapshot:
    base = ResultsWorkspaceState().snapshot()
    data = {f.name: getattr(base, f.name) for f in base.__dataclass_fields__.values()}
    data.update(kwargs)
    return WorkspaceStateSnapshot(**data)


def test_open_fm_inspector_mode_sets_snapshot() -> None:
    state = ResultsWorkspaceState()
    state.open_fm_inspector_mode("FM-1")
    snap = state.snapshot()
    assert snap.fm_inspector_mode is True
    assert snap.fm_inspector_fm_id == "FM-1"


def test_close_fm_inspector_mode_clears_snapshot() -> None:
    state = ResultsWorkspaceState()
    state.open_fm_inspector_mode("FM-1")
    state.close_fm_inspector_mode()
    snap = state.snapshot()
    assert snap.fm_inspector_mode is False
    assert snap.fm_inspector_fm_id is None


def test_set_fm_view_mode_diagram_closes_inspector() -> None:
    state = ResultsWorkspaceState()
    state.open_fm_inspector_mode("FM-1")
    state.set_fm_view_mode(FM_VIEW_MODE_DIAGRAM)
    snap = state.snapshot()
    assert snap.fm_inspector_mode is False
    assert snap.fm_view_mode == FM_VIEW_MODE_DIAGRAM


def test_orchestrator_inspector_visible_only_in_table_mode() -> None:
    snap = _snap(
        workspace_side=SIDE_OUTPUT,
        active_view_id="output.fm_results",
        modus=MODE_FM_DETAIL,
        fm_inspector_mode=True,
        fm_inspector_fm_id="FM-1",
        fm_view_mode=FM_VIEW_MODE_TABLE,
    )
    plan = ResultsWorkspaceOrchestrator.plan_ui_sync(None, snap)
    assert plan.fm_toolbar is not None
    assert plan.fm_toolbar.fm_inspector_visible is True


def test_orchestrator_inspector_hidden_in_diagram_mode() -> None:
    snap = _snap(
        workspace_side=SIDE_OUTPUT,
        active_view_id="output.fm_results",
        modus=MODE_FM_DETAIL,
        fm_inspector_mode=True,
        fm_inspector_fm_id="FM-1",
        fm_view_mode=FM_VIEW_MODE_DIAGRAM,
    )
    plan = ResultsWorkspaceOrchestrator.plan_ui_sync(None, snap)
    assert plan.fm_toolbar is not None
    assert plan.fm_toolbar.fm_inspector_visible is False


def test_orchestrator_inspector_hidden_when_mode_off() -> None:
    snap = _snap(
        workspace_side=SIDE_OUTPUT,
        active_view_id="output.fm_results",
        modus=MODE_FM_DETAIL,
        fm_inspector_mode=False,
        fm_view_mode=FM_VIEW_MODE_TABLE,
    )
    plan = ResultsWorkspaceOrchestrator.plan_ui_sync(None, snap)
    assert plan.fm_toolbar is not None
    assert plan.fm_toolbar.fm_inspector_visible is False
