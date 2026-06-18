"""Slice 105 issue 10 — Faalwijze-analyse view-state in snapshot."""

from __future__ import annotations

from rcm_desktop.adapter.faalwijze_analyse_service import (
    FM_COMPARE_VIEW_DIAGRAM,
    FM_COMPARE_VIEW_TABLE,
)
from rcm_desktop.adapter.results_workspace_orchestrator import ResultsWorkspaceOrchestrator
from rcm_desktop.adapter.results_workspace_state import (
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


def test_default_snapshot_has_fm_view_state() -> None:
    snap = ResultsWorkspaceState().snapshot()
    assert snap.fm_view_mode == FM_COMPARE_VIEW_TABLE
    assert snap.fm_show_nmf_rf is False


def test_set_fm_view_mode_updates_snapshot() -> None:
    state = ResultsWorkspaceState()
    seen: list[WorkspaceStateSnapshot] = []
    state.subscribe(seen.append)

    state.set_fm_view_mode(FM_COMPARE_VIEW_DIAGRAM)

    assert state.snapshot().fm_view_mode == FM_COMPARE_VIEW_DIAGRAM
    assert len(seen) == 1
    assert seen[0].fm_view_mode == FM_COMPARE_VIEW_DIAGRAM


def test_set_fm_show_nmf_rf_updates_snapshot() -> None:
    state = ResultsWorkspaceState()
    state.set_fm_show_nmf_rf(True)
    assert state.snapshot().fm_show_nmf_rf is True


def test_orchestrator_fm_toolbar_reflects_view_mode_from_snapshot() -> None:
    snap = _snap(
        workspace_side=SIDE_OUTPUT,
        active_view_id="output.fm_results",
        modus=MODE_FM_DETAIL,
        fm_view_mode=FM_COMPARE_VIEW_DIAGRAM,
        fm_show_nmf_rf=True,
    )
    plan = ResultsWorkspaceOrchestrator.plan_ui_sync(None, snap)
    assert plan.fm_toolbar is not None
    assert plan.fm_toolbar.fm_view_mode == FM_COMPARE_VIEW_DIAGRAM
    assert plan.fm_toolbar.fm_show_nmf_rf is True


def test_orchestrator_fm_toolbar_uses_snapshot_not_compare_mode_for_view_mode() -> None:
    snap = _snap(
        workspace_side=SIDE_OUTPUT,
        active_view_id="output.fm_results",
        modus=MODE_FM_DETAIL,
        compare_mode=True,
        fm_view_mode=FM_COMPARE_VIEW_DIAGRAM,
    )
    plan = ResultsWorkspaceOrchestrator.plan_ui_sync(None, snap)
    assert plan.fm_toolbar is not None
    assert plan.fm_toolbar.fm_view_mode == FM_COMPARE_VIEW_DIAGRAM
