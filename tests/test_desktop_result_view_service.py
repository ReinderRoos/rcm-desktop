from __future__ import annotations

from pathlib import Path

from rcm_core.models import FMResult
from rcm_core.persistence import load_project
from rcm_desktop.adapter.result_view_service import build_rows


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
