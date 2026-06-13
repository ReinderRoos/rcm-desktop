"""Slice 93 — view-aware input chrome (Nieuwe faalwijze op input.faalwijzen)."""

from __future__ import annotations

from rcm_desktop.adapter.results_workspace_orchestrator import ResultsWorkspaceOrchestrator
from rcm_desktop.adapter.results_workspace_state import (
    MODE_FM_DETAIL,
    ResultsWorkspaceState,
    WorkspaceStateSnapshot,
)
from rcm_desktop.adapter.workspace_view_registry import SIDE_INPUT, SIDE_OUTPUT


def _snap(**kwargs) -> WorkspaceStateSnapshot:
    base = ResultsWorkspaceState().snapshot()
    data = {f.name: getattr(base, f.name) for f in base.__dataclass_fields__.values()}
    data.update(kwargs)
    return WorkspaceStateSnapshot(**data)


def test_new_fm_visible_only_on_input_faalwijzen() -> None:
    input_snap = _snap(
        workspace_side=SIDE_INPUT,
        active_view_id="input.faalwijzen",
        modus=MODE_FM_DETAIL,
    )
    plan = ResultsWorkspaceOrchestrator.plan_ui_sync(None, input_snap)
    assert plan.fm_toolbar is not None
    assert plan.fm_toolbar.new_fm_visible is True
    assert plan.fm_toolbar.batch_faalwijzen_visible is True
    assert plan.fm_toolbar.column_crop_visible is False


def test_new_fm_hidden_on_output_fm_results() -> None:
    output_snap = _snap(
        workspace_side=SIDE_OUTPUT,
        active_view_id="output.fm_results",
        modus=MODE_FM_DETAIL,
    )
    plan = ResultsWorkspaceOrchestrator.plan_ui_sync(None, output_snap)
    assert plan.fm_toolbar is not None
    assert plan.fm_toolbar.new_fm_visible is False
    assert plan.fm_toolbar.batch_faalwijzen_visible is False
    assert plan.fm_toolbar.column_crop_visible is True
    assert plan.fm_toolbar.fm_inspector_visible is True
