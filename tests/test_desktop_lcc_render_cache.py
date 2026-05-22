"""Slice 38 issue 01 — LCC curve-cache key gescheiden van jaarselectie."""
from __future__ import annotations

from dataclasses import replace

from rcm_desktop.adapter.lcc_render_cache_service import (
    build_lcc_curve_cache_key,
    lcc_render_scope,
)
from rcm_desktop.adapter.lcc_type_filter import LCCTypeFilterSet
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.results_workspace_state import (
    MODE_LCC,
    WorkspaceStateSnapshot,
)


def _lcc_snapshot(**kwargs) -> WorkspaceStateSnapshot:
    base = WorkspaceStateSnapshot(
        modus=MODE_LCC,
        source="pbs",
        metric="nb",
        top_n=10,
        scope_id=None,
        filter_text="",
        lcc_filters=LCCTypeFilterSet.all_on(),
        lcc_calendar_year=None,
        planning_overlay=PlanningOverlayState.inactive(),
    )
    return replace(base, **kwargs)


def test_calendar_year_change_does_not_change_curve_key():
    snap_a = _lcc_snapshot(lcc_calendar_year=None)
    snap_b = _lcc_snapshot(lcc_calendar_year=2030)
    assert build_lcc_curve_cache_key(snap_a) == build_lcc_curve_cache_key(snap_b)


def test_filter_toggle_changes_curve_key():
    snap_a = _lcc_snapshot(lcc_filters=LCCTypeFilterSet.all_on())
    snap_b = _lcc_snapshot(lcc_filters=replace(LCCTypeFilterSet.all_on(), rev=False))
    assert build_lcc_curve_cache_key(snap_a) != build_lcc_curve_cache_key(snap_b)


def test_overlay_change_changes_curve_key():
    snap_a = _lcc_snapshot(planning_overlay=PlanningOverlayState.inactive())
    overlay = PlanningOverlayState.inactive().begin_what_if()
    snap_b = _lcc_snapshot(planning_overlay=overlay)
    assert build_lcc_curve_cache_key(snap_a) != build_lcc_curve_cache_key(snap_b)


def test_scope_change_changes_curve_key():
    snap_a = _lcc_snapshot(scope_id=None)
    snap_b = _lcc_snapshot(scope_id="PBS-001")
    assert build_lcc_curve_cache_key(snap_a) != build_lcc_curve_cache_key(snap_b)


def test_year_only_change_is_detail_scope():
    prev = _lcc_snapshot(lcc_calendar_year=None)
    curr = _lcc_snapshot(lcc_calendar_year=2030)
    assert lcc_render_scope(prev, curr) == "detail_only"


def test_filter_change_is_full_scope():
    prev = _lcc_snapshot()
    curr = _lcc_snapshot(lcc_filters=replace(LCCTypeFilterSet.all_on(), cm=False))
    assert lcc_render_scope(prev, curr) == "full"
