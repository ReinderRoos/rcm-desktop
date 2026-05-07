from __future__ import annotations

from pathlib import Path

import pytest

from rcm_core.config import RCMConfig
from rcm_core.models import FMResult, PBSItem, PBSResult, RCMProject
from rcm_core.persistence import load_project
from rcm_desktop.adapter.result_view_service import build_pbs_rows, build_rows


def _fm_result(fm_id: str, pbs_id: str, expected_failures: float, downtime: float, cost: float) -> FMResult:
    return FMResult(
        fm_id=fm_id,
        pbs_id=pbs_id,
        p_failure_lifecycle=0.1,
        expected_failures=expected_failures,
        expected_raw_downtime_hr=1.0,
        expected_detection_delay_hr=0.5,
        expected_total_downtime_hr=downtime,
        expected_pm_downtime_hr=0.2,
        expected_cm_cost_eur=25.0,
        pm_cost_eur=10.0,
        total_cost_eur=cost,
        risk_contribution=0.01,
        effect_bijdragen={},
    )


def test_build_rows_maps_join_fields_and_metrics():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    fm = next(iter(project.faalwijzes.values()))
    fm_result = _fm_result(
        fm_id=fm.fm_id,
        pbs_id=fm.pbs_id,
        expected_failures=2.5,
        downtime=4.0,
        cost=300.0,
    )

    rows = build_rows(project, [fm_result])

    assert len(rows) == 1
    row = rows[0]
    assert row.fm_id == fm.fm_id
    assert row.faalwijze_omschrijving == fm.faalwijze_omschrijving
    assert row.pbs_id == fm.pbs_id
    assert row.bouwdeel_naam == project.pbs_items[fm.pbs_id].bouwdeel_naam
    assert row.expected_failures == 2.5
    assert row.expected_total_downtime_hr == 4.0
    assert row.total_cost_eur == 300.0


def test_build_rows_keeps_running_with_unknown_pbs():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    fm = next(iter(project.faalwijzes.values()))
    fm_result = _fm_result(
        fm_id=fm.fm_id,
        pbs_id="PBS-DOES-NOT-EXIST",
        expected_failures=1.0,
        downtime=2.0,
        cost=10.0,
    )

    rows = build_rows(project, [fm_result])

    assert len(rows) == 1
    assert rows[0].bouwdeel_naam == ""


def test_build_rows_returns_empty_for_empty_input():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))

    assert build_rows(project, []) == []


def _pbs_project() -> RCMProject:
    return RCMProject(
        config=RCMConfig(lifecycle_years=80.0),
        pbs_items={
            "A": PBSItem("A", "o", "e", "Root A"),
            "B": PBSItem("B", "o", "e", "Child B", parent_pbs_id="A"),
            "C": PBSItem("C", "o", "e", "Child C", parent_pbs_id="A"),
            "D": PBSItem("D", "o", "e", "Leaf D", parent_pbs_id="B"),
            "E": PBSItem("E", "o", "e", "Orphan E", parent_pbs_id="MISSING"),
        },
    )


def _pbs_result(pbs_id: str, failures: float, downtime: float, cost: float, unavailability_pct: float = 0.0) -> PBSResult:
    return PBSResult(
        pbs_id=pbs_id,
        bouwdeel_naam=f"Result {pbs_id}",
        total_expected_failures=failures,
        total_downtime_hr=downtime,
        total_cm_cost_eur=0.0,
        total_pm_cost_eur=0.0,
        total_cost_eur=cost,
        unavailability_pct=unavailability_pct,
        total_risk_contribution=0.0,
    )


def test_build_pbs_rows_returns_empty_for_empty_input():
    project = _pbs_project()
    assert build_pbs_rows(project, {}) == []


def test_build_pbs_rows_builds_dfs_and_aggregates_totals():
    project = _pbs_project()
    pbs_results = {
        "A": _pbs_result("A", failures=1.0, downtime=10.0, cost=100.0),
        "B": _pbs_result("B", failures=2.0, downtime=20.0, cost=200.0),
        "C": _pbs_result("C", failures=3.0, downtime=30.0, cost=300.0),
        "D": _pbs_result("D", failures=4.0, downtime=40.0, cost=400.0),
    }

    rows = build_pbs_rows(project, pbs_results)

    assert [row.pbs_id for row in rows] == ["A", "B", "D", "C", "E"]
    row_a = next(row for row in rows if row.pbs_id == "A")
    row_b = next(row for row in rows if row.pbs_id == "B")
    row_e = next(row for row in rows if row.pbs_id == "E")
    assert row_a.expected_failures_total == 10.0
    assert row_a.total_downtime_hr_total == 100.0
    assert row_a.total_cost_eur_total == 1000.0
    assert row_b.level == 1
    assert row_b.sort_path == ("A", "B")
    assert row_e.level == 0
    assert row_e.expected_failures_self == 0.0
    assert row_e.total_cost_eur_total == 0.0


def test_build_pbs_rows_uses_pbsitem_bouwdeel_naam_as_single_source_of_truth():
    project = _pbs_project()
    pbs_results = {"A": _pbs_result("A", failures=1.0, downtime=2.0, cost=3.0)}

    row = build_pbs_rows(project, pbs_results)[0]
    assert row.bouwdeel_naam == "Root A"


def test_build_pbs_rows_recomputes_unavailability_parity_for_leaf():
    project = RCMProject(
        config=RCMConfig(lifecycle_years=80.0),
        pbs_items={"LEAF": PBSItem("LEAF", "o", "e", "Leaf")},
    )
    expected_pct = (876.0 / (80.0 * 8760.0)) * 100.0
    pbs_results = {
        "LEAF": _pbs_result(
            "LEAF", failures=1.0, downtime=876.0, cost=5.0, unavailability_pct=expected_pct
        )
    }

    row = build_pbs_rows(project, pbs_results)[0]
    assert row.unavailability_pct_total == pytest.approx(expected_pct)


def test_build_pbs_rows_handles_cycle_defensively():
    project = RCMProject(
        config=RCMConfig(lifecycle_years=80.0),
        pbs_items={
            "A": PBSItem("A", "o", "e", "A", parent_pbs_id="B"),
            "B": PBSItem("B", "o", "e", "B", parent_pbs_id="A"),
        },
    )
    pbs_results = {
        "A": _pbs_result("A", failures=1.0, downtime=1.0, cost=1.0),
        "B": _pbs_result("B", failures=2.0, downtime=2.0, cost=2.0),
    }

    rows = build_pbs_rows(project, pbs_results)
    assert len(rows) == 2
    assert any(row.level == 0 for row in rows)
