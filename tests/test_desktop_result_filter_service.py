from __future__ import annotations

from pathlib import Path

import pytest

from rcm_core.config import RCMConfig
from rcm_core.models import FMResult, PBSItem, RCMProject
from rcm_core.persistence import load_project
from rcm_desktop.adapter.result_filter_service import (
    FilteredRunView,
    ScopedKPITotals,
    filter_run_result,
)
from rcm_desktop.adapter.result_view_service import (
    FMResultRow,
    PBSResultRow,
    PBSTreeNode,
    build_pbs_rows,
    build_rows,
)
from rcm_desktop.adapter.run_service import RunMetrics, RunResult


def _fm_result(
    fm_id: str,
    pbs_id: str,
    *,
    expected_failures: float = 1.0,
    downtime: float = 10.0,
    cost: float = 100.0,
) -> FMResult:
    return FMResult(
        fm_id=fm_id,
        pbs_id=pbs_id,
        p_failure_lifecycle=0.1,
        expected_failures=expected_failures,
        expected_raw_downtime_hr=downtime - 0.5,
        expected_detection_delay_hr=0.5,
        expected_total_downtime_hr=downtime,
        expected_pm_downtime_hr=0.0,
        expected_cm_cost_eur=cost * 0.6,
        pm_cost_eur=cost * 0.4,
        total_cost_eur=cost,
        risk_contribution=0.01,
        effect_bijdragen={},
    )


def _project_three_levels() -> RCMProject:
    """Project: ROOT -> CHILD_A -> LEAF_A1, CHILD_B (leaf)."""
    return RCMProject(
        config=RCMConfig(lifecycle_years=80.0),
        pbs_items={
            "ROOT": PBSItem("ROOT", "obj", "el", "Root"),
            "CHILD_A": PBSItem("CHILD_A", "obj", "el", "Child A", parent_pbs_id="ROOT"),
            "LEAF_A1": PBSItem("LEAF_A1", "obj", "el", "Leaf A1", parent_pbs_id="CHILD_A"),
            "CHILD_B": PBSItem("CHILD_B", "obj", "el", "Child B", parent_pbs_id="ROOT"),
        },
    )


def _build_run_result(
    project: RCMProject,
    fm_results: list[FMResult],
    *,
    pbs_results: dict | None = None,
) -> RunResult:
    rows = build_rows(project, fm_results)
    if pbs_results is None:
        pbs_results = {}
    pbs_rows = build_pbs_rows(project, pbs_results)
    metrics = RunMetrics(
        fm_result_count=len(fm_results),
        total_lifecycle_faalmomenten=sum(r.expected_failures for r in fm_results),
        total_cost_eur=sum(r.total_cost_eur for r in fm_results),
        total_downtime_hr=sum(
            r.expected_total_downtime_hr + r.expected_pm_downtime_hr for r in fm_results
        ),
        lifecycle_years=float(project.config.lifecycle_years),
        total_risk_contribution=sum(r.risk_contribution for r in fm_results),
    )
    return RunResult(
        status="done",
        summary="ok",
        metrics=metrics,
        rows=rows,
        pbs_rows=pbs_rows,
        fm_core_results=tuple(fm_results),
    )


def test_filter_run_result_scope_none_returns_all_rows_and_unscoped_totals():
    project = _project_three_levels()
    fm_results = [
        _fm_result("FM-1", "LEAF_A1", expected_failures=2.0, downtime=10.0, cost=200.0),
        _fm_result("FM-2", "CHILD_B", expected_failures=3.0, downtime=15.0, cost=300.0),
    ]
    run = _build_run_result(project, fm_results)

    view = filter_run_result(project, run, scope_id=None)

    assert view.scope_id is None
    assert len(view.fm_rows) == 2
    assert {row.fm_id for row in view.fm_rows} == {"FM-1", "FM-2"}
    assert view.kpi_totals.total_faalmomenten == pytest.approx(5.0)
    assert view.kpi_totals.total_cost_eur == pytest.approx(500.0)
    assert view.kpi_totals.total_downtime_hr == pytest.approx(25.0)
    # Unavailability = (25 / (80 * 8760)) * 100
    expected_pct = (25.0 / (80.0 * 8760.0)) * 100.0
    assert view.kpi_totals.unavailability_pct == pytest.approx(expected_pct, abs=1e-6)


def test_filter_run_result_scope_leaf_keeps_only_fm_rows_in_subtree():
    project = _project_three_levels()
    fm_results = [
        _fm_result("FM-LEAF", "LEAF_A1", expected_failures=2.0, cost=200.0, downtime=20.0),
        _fm_result("FM-OTHER", "CHILD_B", expected_failures=4.0, cost=400.0, downtime=40.0),
    ]
    run = _build_run_result(project, fm_results)

    view = filter_run_result(project, run, scope_id="LEAF_A1")

    assert view.scope_id == "LEAF_A1"
    assert [row.fm_id for row in view.fm_rows] == ["FM-LEAF"]
    assert view.kpi_totals.total_faalmomenten == pytest.approx(2.0)
    assert view.kpi_totals.total_cost_eur == pytest.approx(200.0)
    assert view.kpi_totals.total_downtime_hr == pytest.approx(20.0)


def test_filter_run_result_scope_subtree_includes_descendants():
    project = _project_three_levels()
    fm_results = [
        _fm_result("FM-LEAF", "LEAF_A1", expected_failures=2.0, cost=200.0, downtime=20.0),
        _fm_result("FM-MID", "CHILD_A", expected_failures=1.0, cost=100.0, downtime=10.0),
        _fm_result("FM-OUT", "CHILD_B", expected_failures=4.0, cost=400.0, downtime=40.0),
    ]
    run = _build_run_result(project, fm_results)

    view = filter_run_result(project, run, scope_id="CHILD_A")

    assert view.scope_id == "CHILD_A"
    fm_ids = {row.fm_id for row in view.fm_rows}
    assert fm_ids == {"FM-LEAF", "FM-MID"}
    assert view.kpi_totals.total_faalmomenten == pytest.approx(3.0)
    assert view.kpi_totals.total_cost_eur == pytest.approx(300.0)
    assert view.kpi_totals.total_downtime_hr == pytest.approx(30.0)


def test_filter_run_result_scope_unknown_returns_empty_view():
    project = _project_three_levels()
    fm_results = [
        _fm_result("FM-1", "LEAF_A1", expected_failures=2.0, cost=200.0, downtime=20.0),
    ]
    run = _build_run_result(project, fm_results)

    view = filter_run_result(project, run, scope_id="DOES-NOT-EXIST")

    assert view.scope_id == "DOES-NOT-EXIST"
    assert view.fm_rows == ()
    assert view.pbs_rows == ()
    assert view.pbs_tree_roots == ()
    assert view.kpi_totals.total_faalmomenten == pytest.approx(0.0)
    assert view.kpi_totals.total_cost_eur == pytest.approx(0.0)
    assert view.kpi_totals.total_downtime_hr == pytest.approx(0.0)
    assert view.kpi_totals.unavailability_pct == pytest.approx(0.0)


def test_filter_run_result_scope_none_tree_returns_all_roots():
    project = _project_three_levels()
    fm_results = [_fm_result("FM-1", "LEAF_A1", expected_failures=1.0, cost=50.0, downtime=5.0)]
    pbs_results = {
        "ROOT": _pbs_dummy_result("ROOT", 0.0, 0.0, 0.0),
        "CHILD_A": _pbs_dummy_result("CHILD_A", 0.0, 0.0, 0.0),
        "LEAF_A1": _pbs_dummy_result("LEAF_A1", 1.0, 5.0, 50.0),
        "CHILD_B": _pbs_dummy_result("CHILD_B", 0.0, 0.0, 0.0),
    }
    run = _build_run_result(project, fm_results, pbs_results=pbs_results)

    view = filter_run_result(project, run, scope_id=None)

    assert isinstance(view.pbs_tree_roots, tuple)
    assert len(view.pbs_tree_roots) == 1
    assert view.pbs_tree_roots[0].pbs_id == "ROOT"


def test_filter_run_result_scope_subtree_returns_subtree_root_only():
    project = _project_three_levels()
    fm_results = [
        _fm_result("FM-A1", "LEAF_A1", expected_failures=1.0, cost=10.0, downtime=1.0),
        _fm_result("FM-B", "CHILD_B", expected_failures=1.0, cost=20.0, downtime=2.0),
    ]
    pbs_results = {
        "ROOT": _pbs_dummy_result("ROOT", 0.0, 0.0, 0.0),
        "CHILD_A": _pbs_dummy_result("CHILD_A", 0.0, 0.0, 0.0),
        "LEAF_A1": _pbs_dummy_result("LEAF_A1", 1.0, 1.0, 10.0),
        "CHILD_B": _pbs_dummy_result("CHILD_B", 1.0, 2.0, 20.0),
    }
    run = _build_run_result(project, fm_results, pbs_results=pbs_results)

    view = filter_run_result(project, run, scope_id="CHILD_A")

    assert len(view.pbs_tree_roots) == 1
    root_node = view.pbs_tree_roots[0]
    assert root_node.pbs_id == "CHILD_A"
    descendant_ids = {root_node.pbs_id} | {c.pbs_id for c in root_node.children}
    assert descendant_ids == {"CHILD_A", "LEAF_A1"}


def test_filter_run_result_reconciles_to_run_metrics_for_scope_none_on_real_fixture():
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    project = load_project(fixture)
    from rcm_desktop.adapter import run_service

    run = run_service.run(project, fixture, full_recompute=True, parallel=False)
    assert run.status == "done"

    view = filter_run_result(project, run, scope_id=None)

    assert view.kpi_totals.total_faalmomenten == pytest.approx(
        run.metrics.total_lifecycle_faalmomenten, abs=1e-3
    )
    assert view.kpi_totals.total_cost_eur == pytest.approx(
        run.metrics.total_cost_eur, abs=1e-3
    )
    assert view.kpi_totals.total_downtime_hr == pytest.approx(
        run.metrics.total_downtime_hr, abs=1e-3
    )


def test_filter_run_result_subtree_sums_match_pbs_aggregate_on_real_fixture():
    """For any non-root PBS node, FM-rows in subtree must sum to the aggregate of that subtree."""
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    project = load_project(fixture)
    from rcm_desktop.adapter import run_service

    run = run_service.run(project, fixture, full_recompute=True, parallel=False)
    assert run.status == "done"

    # Pick a non-root subtree that has at least one FM-row underneath.
    candidate_id: str | None = None
    pbs_by_id = {row.pbs_id: row for row in run.pbs_rows}
    for row in run.pbs_rows:
        if row.parent_pbs_id is not None and row.expected_failures_total > 0:
            candidate_id = row.pbs_id
            break
    assert candidate_id is not None, "fixture should have a non-root subtree with failures"

    view = filter_run_result(project, run, scope_id=candidate_id)
    expected = pbs_by_id[candidate_id]

    assert sum(r.expected_failures for r in view.fm_rows) == pytest.approx(
        expected.expected_failures_total, abs=1e-3
    )
    assert sum(r.total_cost_eur for r in view.fm_rows) == pytest.approx(
        expected.total_cost_eur_total, abs=1e-3
    )


def _pbs_dummy_result(pbs_id: str, failures: float, downtime: float, cost: float):
    from rcm_core.models import PBSResult

    return PBSResult(
        pbs_id=pbs_id,
        bouwdeel_naam=f"Result {pbs_id}",
        total_expected_failures=failures,
        total_downtime_hr=downtime,
        total_cm_cost_eur=0.0,
        total_pm_cost_eur=0.0,
        total_cost_eur=cost,
        unavailability_pct=0.0,
        total_risk_contribution=0.0,
    )
