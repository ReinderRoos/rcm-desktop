"""Slice 95 issue 01 — chrome-profiel in view-registry."""

from __future__ import annotations

from rcm_desktop.adapter.results_workspace_orchestrator import ResultsWorkspaceOrchestrator
from rcm_desktop.adapter.results_workspace_state import (
    MODE_FM_DETAIL,
    ResultsWorkspaceState,
    WorkspaceStateSnapshot,
)
from rcm_desktop.adapter.workspace_view_registry import (
    SIDE_INPUT,
    SIDE_OUTPUT,
    WORKSPACE_VIEW_REGISTRY,
    chrome_for_view,
)


def _snap(**kwargs) -> WorkspaceStateSnapshot:
    base = ResultsWorkspaceState().snapshot()
    data = {f.name: getattr(base, f.name) for f in base.__dataclass_fields__.values()}
    data.update(kwargs)
    return WorkspaceStateSnapshot(**data)


def test_input_faalwijzen_chrome_allows_new_fm() -> None:
    profile = chrome_for_view(WORKSPACE_VIEW_REGISTRY, "input.faalwijzen")
    assert profile is not None
    assert profile.allows_new_fm is True
    assert profile.shows_batch_faalwijzen is True
    assert profile.toolbar_family == "fm"


def test_output_fm_results_chrome_disallows_new_fm() -> None:
    profile = chrome_for_view(WORKSPACE_VIEW_REGISTRY, "output.fm_results")
    assert profile is not None
    assert profile.allows_new_fm is False
    assert profile.shows_column_crop is True
    assert profile.toolbar_family == "fm"


def test_orchestrator_fm_toolbar_matches_registry_on_input_faalwijzen() -> None:
    snap = _snap(
        workspace_side=SIDE_INPUT,
        active_view_id="input.faalwijzen",
        modus=MODE_FM_DETAIL,
    )
    profile = chrome_for_view(WORKSPACE_VIEW_REGISTRY, "input.faalwijzen")
    plan = ResultsWorkspaceOrchestrator.plan_ui_sync(None, snap)
    assert plan.fm_toolbar is not None
    assert plan.fm_toolbar.new_fm_visible is profile.allows_new_fm
    assert plan.fm_toolbar.batch_faalwijzen_visible is profile.shows_batch_faalwijzen


def test_orchestrator_fm_toolbar_matches_registry_on_output_fm_results() -> None:
    snap = _snap(
        workspace_side=SIDE_OUTPUT,
        active_view_id="output.fm_results",
        modus=MODE_FM_DETAIL,
    )
    profile = chrome_for_view(WORKSPACE_VIEW_REGISTRY, "output.fm_results")
    plan = ResultsWorkspaceOrchestrator.plan_ui_sync(None, snap)
    assert plan.fm_toolbar is not None
    assert plan.fm_toolbar.new_fm_visible is profile.allows_new_fm
    assert plan.fm_toolbar.column_crop_visible is profile.shows_column_crop
