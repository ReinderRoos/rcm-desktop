"""Slice 31 — Preventief-modus aligned met LCC planning curve."""

from __future__ import annotations

import json
import math
from pathlib import Path

from rcm_core.models import RCMProject

from rcm_desktop.adapter.lcc_planning_service import build_lcc_planning_curve_reconciled
from rcm_desktop.adapter.lcc_type_filter import LCCTypeFilterSet
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.pm_chart_service import build_pm_chart_input
from rcm_desktop.adapter.ltap_service import build_ltap_view
from rcm_desktop.adapter.pm_chart_service import (
    PM_SUBMODE_AANTAL_UITVOERINGEN,
    PM_SUBMODE_KOSTEN,
)
from rcm_desktop.adapter.run_service import run as run_single

FIXTURE = Path("tests/fixtures/one_fm_planning.rcm.json")
SAMPLE = Path("tests/fixtures/sample_project.rcm.json")


def _project(path: Path = FIXTURE) -> RCMProject:
    return RCMProject.from_dict(json.loads(path.read_text(encoding="utf-8")))


def _run(project: RCMProject, path: Path = FIXTURE):
    rr = run_single(project, path, full_recompute=True, parallel=False)
    assert rr.status == "done"
    return rr


def _lcc_preventief_sum(project, rr, **kwargs) -> float:
    curve = build_lcc_planning_curve_reconciled(project, rr, **kwargs)
    assert curve is not None
    return sum(b.preventief_eur for b in curve.display_buckets)


def test_pm_kosten_overlay_passive_lower_than_baseline():
    project = _project()
    rr = _run(project)
    baseline = build_pm_chart_input(project, rr, submode=PM_SUBMODE_KOSTEN)
    overlay = PlanningOverlayState.inactive().begin_what_if().bulk_all_rev_passive(project)
    whatif = build_pm_chart_input(
        project, rr, submode=PM_SUBMODE_KOSTEN, overlay=overlay
    )
    assert baseline is not None and whatif is not None
    base_sum = sum(r.value for r in baseline.rows)
    whatif_sum = sum(r.value for r in whatif.rows)
    assert whatif_sum < base_sum - 1.0
    assert math.isclose(whatif_sum, _lcc_preventief_sum(project, rr, overlay=overlay), abs_tol=1e-3)


def test_pm_kosten_rev_filter_matches_lcc():
    project = _project()
    rr = _run(project)
    filters = LCCTypeFilterSet(
        cm=True, rev=True, in_task=False, tst=False, svo=False, wet=False
    )
    chart = build_pm_chart_input(
        project, rr, submode=PM_SUBMODE_KOSTEN, type_filters=filters
    )
    assert chart is not None
    assert math.isclose(
        sum(r.value for r in chart.rows),
        _lcc_preventief_sum(project, rr, type_filters=filters),
        abs_tol=1e-3,
    )


def test_pm_kosten_inactive_overlay_reconciles_lifecycle_preventief():
    project = _project(SAMPLE)
    rr = _run(project, SAMPLE)
    chart = build_pm_chart_input(project, rr, submode=PM_SUBMODE_KOSTEN)
    assert chart is not None
    target = sum(fr.pm_cost_eur for fr in rr.fm_core_results)
    assert math.isclose(sum(r.value for r in chart.rows), target, abs_tol=1e-3)


def test_pm_kosten_scoped_subtree_reconciles():
    project = _project(SAMPLE)
    rr = _run(project, SAMPLE)
    pbs_with_fm = {fr.pbs_id for fr in rr.fm_core_results if fr.pm_cost_eur > 0.0}
    if not pbs_with_fm:
        return
    scope_id = next(iter(pbs_with_fm))
    subtree_target = sum(
        fr.pm_cost_eur for fr in rr.fm_core_results if fr.pbs_id == scope_id
    )
    chart = build_pm_chart_input(
        project, rr, submode=PM_SUBMODE_KOSTEN, scope_id=scope_id
    )
    assert chart is not None
    assert math.isclose(sum(r.value for r in chart.rows), subtree_target, abs_tol=1e-3)


def test_pm_aantal_rev_filter_counts_only_rev_executions():
    project = _project()
    rr = _run(project)
    filters = LCCTypeFilterSet(
        cm=True, rev=True, in_task=False, tst=False, svo=False, wet=False
    )
    chart = build_pm_chart_input(
        project,
        rr,
        submode=PM_SUBMODE_AANTAL_UITVOERINGEN,
        type_filters=filters,
    )
    assert chart is not None
    expected = 0.0
    for task in project.pm_tasks.values():
        from rcm_core.models import TaskType

        if task.taak_type != TaskType.REV:
            continue
        fm = project.faalwijzes.get(task.fm_id)
        if fm is None:
            continue
        for year_row in build_ltap_view(project).years:
            for detail in year_row.details:
                if detail.pm_id == task.pm_id:
                    expected += float(detail.executions)
    assert math.isclose(sum(r.value for r in chart.rows), expected, abs_tol=1e-9)
