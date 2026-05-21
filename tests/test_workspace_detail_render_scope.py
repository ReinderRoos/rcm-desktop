"""Slice 36 issue 04 — modus-gescopeerde rerender tests."""
from __future__ import annotations

from rcm_desktop.adapter.results_workspace_state import (
    MODE_BIJDRAGEN,
    MODE_FM_DETAIL,
    MODE_LCC,
    ResultsWorkspaceState,
    WorkspaceStateSnapshot,
)
from rcm_desktop.adapter.workspace_detail_render_scope import (
    required_detail_builders,
    should_refresh_kpi_for_render_depth,
    workspace_detail_split_render_depth,
)


def _snap(**kwargs) -> WorkspaceStateSnapshot:
    base = ResultsWorkspaceState().snapshot()
    data = {f.name: getattr(base, f.name) for f in base.__dataclass_fields__.values()}
    data.update(kwargs)
    return WorkspaceStateSnapshot(**data)


def test_scope_change_yields_all_splits():
    prev = _snap(scope_id=None)
    curr = _snap(scope_id="PBS-1")
    assert workspace_detail_split_render_depth(prev, curr) == "all_splits"


def test_metric_toggle_yields_active_modus_only():
    prev = _snap(metric="kosten")
    curr = _snap(metric="niet_beschikbaarheid")
    assert workspace_detail_split_render_depth(prev, curr) == "active_modus_only"


def test_required_builders_active_modus_only_excludes_lcc_in_bijdragen():
    snap = _snap(modus=MODE_BIJDRAGEN)
    required = required_detail_builders(snap, "active_modus_only")
    assert required == frozenset({MODE_BIJDRAGEN})
    assert MODE_LCC not in required


def test_required_builders_all_splits_includes_all_modi():
    snap = _snap(modus=MODE_BIJDRAGEN)
    required = required_detail_builders(snap, "all_splits")
    assert required == frozenset({MODE_FM_DETAIL, MODE_BIJDRAGEN, MODE_LCC})


def test_kpi_refresh_only_on_all_splits():
    assert should_refresh_kpi_for_render_depth("all_splits") is True
    assert should_refresh_kpi_for_render_depth("active_modus_only") is False
