"""Slice 107-B issue 01 — view-titel plan + footer zonder context."""

from __future__ import annotations

from rcm_desktop import messages
from rcm_desktop.adapter.results_workspace_orchestrator import (
    ResultsWorkspaceOrchestrator,
    plan_chrome_footer,
)
from rcm_desktop.adapter.results_workspace_state import (
    MODE_FM_DETAIL,
    MODE_LCC,
    ResultsWorkspaceState,
    WorkspaceStateSnapshot,
)
from rcm_desktop.adapter.workspace_view_registry import SIDE_OUTPUT


def _snap(**kwargs) -> WorkspaceStateSnapshot:
    base = ResultsWorkspaceState().snapshot()
    data = {f.name: getattr(base, f.name) for f in base.__dataclass_fields__.values()}
    data.update(kwargs)
    return WorkspaceStateSnapshot(**data)


def test_footer_plan_has_no_context_label() -> None:
    snap = _snap(
        workspace_side=SIDE_OUTPUT,
        active_view_id="output.fm_results",
        modus=MODE_FM_DETAIL,
    )
    plan = plan_chrome_footer(snap)
    assert plan.context_label == ""


def test_ui_sync_plan_view_title_from_registry() -> None:
    snap = _snap(
        workspace_side=SIDE_OUTPUT,
        active_view_id="output.fm_results",
        modus=MODE_FM_DETAIL,
    )
    ui = ResultsWorkspaceOrchestrator.plan_ui_sync(None, snap)
    assert ui.view_title == messages.WORKSPACE_VIEW_TOP_BIJDRAGEN


def test_ui_sync_plan_view_title_updates_per_view() -> None:
    snap = _snap(
        workspace_side=SIDE_OUTPUT,
        active_view_id="output.lcc_plot",
        modus=MODE_LCC,
    )
    ui = ResultsWorkspaceOrchestrator.plan_ui_sync(None, snap)
    assert ui.view_title == messages.WORKSPACE_VIEW_LCC_PLOT
