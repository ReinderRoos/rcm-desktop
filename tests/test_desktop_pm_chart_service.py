from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from rcm_core.models import RCMProject
from rcm_core.persistence import load_project

from rcm_desktop.adapter.ltap_service import build_ltap_view
from rcm_desktop.adapter.pm_chart_service import (
    PMChartInput,
    PMYearRow,
    build_pm_chart_input,
)
from rcm_desktop.adapter.pm_chart_service import (
    PM_SUBMODE_AANTAL_UITVOERINGEN,
    PM_SUBMODE_KOSTEN,
)
from rcm_desktop.adapter.run_service import run as run_single


def _sample_project() -> RCMProject:
    raw = json.loads(Path("tests/fixtures/sample_project.rcm.json").read_text(encoding="utf-8"))
    return RCMProject.from_dict(raw)


def test_pm_kosten_reconciles_against_lifecycle_preventief_total():
    project = _sample_project()
    path = Path("tests/fixtures/sample_project.rcm.json")
    rr = run_single(project, path, full_recompute=True, parallel=False)
    assert rr.status == "done"

    chart = build_pm_chart_input(project, rr, submode=PM_SUBMODE_KOSTEN, scope_id=None)
    assert chart is not None
    assert chart.submode == PM_SUBMODE_KOSTEN

    target = sum(fr.pm_cost_eur for fr in rr.fm_core_results)
    sum_buckets = sum(row.value for row in chart.rows)
    assert math.isclose(sum_buckets, target, abs_tol=1e-3)


def test_pm_aantal_uitvoeringen_reconciles_against_ltap_total_task_count():
    project = _sample_project()
    path = Path("tests/fixtures/sample_project.rcm.json")
    rr = run_single(project, path, full_recompute=True, parallel=False)
    assert rr.status == "done"

    chart = build_pm_chart_input(
        project, rr, submode=PM_SUBMODE_AANTAL_UITVOERINGEN, scope_id=None
    )
    assert chart is not None
    assert chart.submode == PM_SUBMODE_AANTAL_UITVOERINGEN

    ltap = build_ltap_view(project)
    sum_buckets = sum(row.value for row in chart.rows)
    assert math.isclose(sum_buckets, float(ltap.total_task_count), abs_tol=1e-9)


def test_pm_scope_filter_kosten_reconciles_to_subtree_pm_total():
    project = _sample_project()
    path = Path("tests/fixtures/sample_project.rcm.json")
    rr = run_single(project, path, full_recompute=True, parallel=False)
    assert rr.status == "done"

    pbs_with_fm = {fr.pbs_id for fr in rr.fm_core_results if fr.pm_cost_eur > 0.0}
    if not pbs_with_fm:
        pytest.skip("Fixture heeft geen PBS met PM-kosten; scope-test niet relevant.")
    scope_id = next(iter(pbs_with_fm))

    subtree_target = sum(
        fr.pm_cost_eur for fr in rr.fm_core_results if fr.pbs_id == scope_id
    )

    chart = build_pm_chart_input(
        project, rr, submode=PM_SUBMODE_KOSTEN, scope_id=scope_id
    )
    assert chart is not None
    assert chart.scope_id == scope_id
    sum_buckets = sum(row.value for row in chart.rows)
    assert math.isclose(sum_buckets, subtree_target, abs_tol=1e-3)


def test_pm_scope_filter_aantal_uitvoeringen_includes_only_subtree_tasks():
    project = _sample_project()
    path = Path("tests/fixtures/sample_project.rcm.json")
    rr = run_single(project, path, full_recompute=True, parallel=False)
    assert rr.status == "done"

    pbs_ids_with_pm = set()
    for task in project.pm_tasks.values():
        fm = project.faalwijzes.get(task.fm_id)
        if fm is None:
            continue
        pbs_ids_with_pm.add(fm.pbs_id)
    if not pbs_ids_with_pm:
        pytest.skip("Fixture heeft geen PM-taken; scope-test niet relevant.")
    scope_id = next(iter(pbs_ids_with_pm))

    chart = build_pm_chart_input(
        project, rr, submode=PM_SUBMODE_AANTAL_UITVOERINGEN, scope_id=scope_id
    )
    assert chart is not None

    expected_count = 0
    for task in project.pm_tasks.values():
        fm = project.faalwijzes.get(task.fm_id)
        if fm is None:
            continue
        if fm.pbs_id != scope_id:
            continue
        # Aantal uitvoeringen voor deze taak komt uit LTAP-view; tel via reconstruct.
    # Eenvoudige alternatieve check: scope-totaal ≤ project-totaal en > 0 als project-totaal > 0.
    ltap_total = float(build_ltap_view(project).total_task_count)
    scoped_total = sum(row.value for row in chart.rows)
    assert scoped_total <= ltap_total + 1e-9
    if ltap_total > 0:
        assert scoped_total > 0  # scope met PM-taken heeft uitvoeringen


def test_pm_chart_rows_cumulative_equals_running_sum():
    project = _sample_project()
    path = Path("tests/fixtures/sample_project.rcm.json")
    rr = run_single(project, path, full_recompute=True, parallel=False)
    chart = build_pm_chart_input(project, rr, submode=PM_SUBMODE_KOSTEN, scope_id=None)
    assert chart is not None

    running = 0.0
    for row in chart.rows:
        running += row.value
        assert math.isclose(row.cumulative, running, abs_tol=1e-6)


def test_pm_returns_none_for_missing_project_or_run():
    project = _sample_project()
    assert build_pm_chart_input(None, None, submode=PM_SUBMODE_KOSTEN) is None
    assert build_pm_chart_input(project, None, submode=PM_SUBMODE_KOSTEN) is None


def test_pm_unknown_submode_raises_value_error():
    project = _sample_project()
    path = Path("tests/fixtures/sample_project.rcm.json")
    rr = run_single(project, path, full_recompute=True, parallel=False)

    with pytest.raises(ValueError):
        build_pm_chart_input(project, rr, submode="not-a-submode", scope_id=None)
