"""Slice 28 — LCC-planning, overlay, FM NMF-filter."""

from __future__ import annotations

import json
from pathlib import Path

from rcm_core.models import RCMProject

from rcm_desktop.adapter.fm_evident_filter import filter_fm_rows_by_evident
from rcm_desktop.adapter.lcc_chart_service import LCCScenarioCurve, sum_correctief_preventief
from rcm_desktop.adapter.lcc_planning_service import (
    build_lcc_planning_curve_reconciled,
    build_lcc_year_detail,
    horizon_index_for_calendar_year,
)
from rcm_desktop.adapter.lcc_type_filter import LCCTypeFilterSet
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.planning_whatif_service import apply_overlay_shift
from rcm_desktop.adapter.run_service import run as run_single


FIXTURE = Path("tests/fixtures/one_fm_planning.rcm.json")


def _project() -> RCMProject:
    return RCMProject.from_dict(json.loads(FIXTURE.read_text(encoding="utf-8")))


def _run(project: RCMProject):
    rr = run_single(project, FIXTURE, full_recompute=True, parallel=False)
    assert rr.status == "done"
    return rr


def _curve(buckets) -> LCCScenarioCurve:
    return LCCScenarioCurve(scenario_key="T", label="T", buckets=buckets)


def test_golden_fixture_loads_and_runs():
    project = _project()
    rr = _run(project)
    assert len(rr.fm_core_results) >= 1


def test_lcc_type_filter_cm_off_zeros_correctief():
    project = _project()
    rr = _run(project)
    curve = build_lcc_planning_curve_reconciled(
        project,
        rr,
        type_filters=LCCTypeFilterSet(
            cm=False, rev=True, in_task=True, tst=True, svo=True, wet=True
        ),
    )
    assert curve is not None
    assert all(b.correctief_eur == 0.0 for b in curve.display_buckets)


def test_lcc_rev_only_preventief_lte_total():
    project = _project()
    rr = _run(project)
    all_on = build_lcc_planning_curve_reconciled(
        project, rr, type_filters=LCCTypeFilterSet.all_on()
    )
    rev_only = build_lcc_planning_curve_reconciled(
        project,
        rr,
        type_filters=LCCTypeFilterSet(
            cm=True, rev=True, in_task=False, tst=False, svo=False, wet=False
        ),
    )
    assert all_on is not None and rev_only is not None
    _, prev_all, _ = sum_correctief_preventief(_curve(all_on.display_buckets))
    _, prev_rev, _ = sum_correctief_preventief(_curve(rev_only.display_buckets))
    assert prev_rev <= prev_all + 1e-3
    assert prev_rev > 0.0


def test_overlay_rev_passive_drops_preventief():
    project = _project()
    rr = _run(project)
    baseline = build_lcc_planning_curve_reconciled(project, rr)
    overlay = PlanningOverlayState.inactive().begin_what_if().bulk_all_rev_passive(project)
    whatif = build_lcc_planning_curve_reconciled(project, rr, overlay=overlay)
    assert baseline is not None and whatif is not None
    _, prev_base, _ = sum_correctief_preventief(_curve(baseline.display_buckets))
    _, prev_whatif, _ = sum_correctief_preventief(_curve(whatif.display_buckets))
    assert prev_whatif < prev_base - 1.0


def test_overlay_shift_changes_year_detail():
    project = _project()
    rr = _run(project)
    mj = int(project.config.modeljaar)
    year = mj + 15
    assert horizon_index_for_calendar_year(project, year) is not None
    overlay = PlanningOverlayState.inactive().begin_what_if()
    before = build_lcc_year_detail(project, rr, year, overlay=overlay)
    shifted = apply_overlay_shift(
        project, overlay, pm_ids=["PM-002"], shift_years=5
    )
    assert shifted.error is None
    after = build_lcc_year_detail(
        project, rr, year + 5, overlay=shifted.overlay, type_filters=LCCTypeFilterSet.all_on()
    )
    assert before is not None and after is not None
    assert any(r.pm_id == "PM-002" for r in after.rows)


def test_year_detail_cm_only_has_no_pm_rows():
    project = _project()
    rr = _run(project)
    year = int(project.config.modeljaar)
    detail = build_lcc_year_detail(
        project,
        rr,
        year,
        type_filters=LCCTypeFilterSet(
            cm=True, rev=False, in_task=False, tst=False, svo=False, wet=False
        ),
    )
    assert detail is not None
    assert detail.cm_only
    assert detail.rows == ()


def test_fm_evident_filter_nmf_only():
    project = _project()
    rr = _run(project)
    nmf = filter_fm_rows_by_evident(rr.rows, project, "nmf_only")
    assert all(project.faalwijzes[r.fm_id].is_evident is False for r in nmf)
    assert any(r.fm_id == "FM-003" for r in nmf)


def test_planning_overlay_reset_clears_changes():
    project = _project()
    o = PlanningOverlayState.inactive().begin_what_if().bulk_all_rev_passive(project)
    assert o.change_count() > 0
    assert o.reset_overlay().change_count() == 0
