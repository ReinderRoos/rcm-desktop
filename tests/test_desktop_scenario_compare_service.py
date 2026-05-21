from __future__ import annotations

from rcm_desktop.adapter.result_view_service import FMResultRow
from rcm_desktop.adapter.run_service import RunMetrics, RunResult
from rcm_desktop.adapter.scenario_compare_service import build_compare_view


def _run_result(
    *,
    failures: float,
    cost: float,
    downtime: float,
    lifecycle_years: float = 100.0,
    risk: float | None = None,
) -> RunResult:
    return RunResult(
        status="done",
        summary="ok",
        metrics=RunMetrics(
            fm_result_count=2,
            total_lifecycle_faalmomenten=failures,
            total_cost_eur=cost,
            total_downtime_hr=downtime,
            lifecycle_years=lifecycle_years,
            total_risk_contribution=risk,
        ),
        rows=[
            FMResultRow(
                fm_id="FM-001",
                faalwijze_omschrijving="a",
                pbs_id="PBS-1",
                bouwdeel_naam="B1",
                expected_failures=10.0,
                expected_total_downtime_hr=4.0,
                total_cost_eur=300.0,
            ),
            FMResultRow(
                fm_id="FM-002",
                faalwijze_omschrijving="b",
                pbs_id="PBS-1",
                bouwdeel_naam="B1",
                expected_failures=3.0,
                expected_total_downtime_hr=9.0,
                total_cost_eur=120.0,
            ),
        ],
    )


def test_build_compare_view_returns_error_when_missing_inputs():
    view = build_compare_view(None, None)
    assert view.status == "error"
    assert view.kpis == tuple()


def test_build_compare_view_uses_pm_minus_cm_and_stable_kpi_order():
    cm = _run_result(failures=10.0, cost=1000.0, downtime=100.0, risk=20.0)
    pm = _run_result(failures=8.0, cost=1200.0, downtime=80.0, risk=18.0)
    view = build_compare_view(cm, pm)
    assert view.status == "done"
    assert [k.key for k in view.kpis] == [
        "expected_failures",
        "total_cost_eur",
        "unavailability_pct",
    ]
    failures = view.kpis[0]
    assert failures.delta_display.startswith("-")
    cost = view.kpis[1]
    assert cost.delta_display.startswith("+")


def test_build_compare_view_driver_tie_breaks_on_fm_id():
    cm = _run_result(failures=10.0, cost=1000.0, downtime=100.0, risk=20.0)
    pm = _run_result(failures=10.0, cost=1000.0, downtime=100.0, risk=20.0)
    # equal costs after abs() -> FM-001 first by id
    cm.rows[0] = FMResultRow(**{**cm.rows[0].__dict__, "total_cost_eur": 50.0})
    cm.rows[1] = FMResultRow(**{**cm.rows[1].__dict__, "total_cost_eur": 50.0})
    view = build_compare_view(cm, pm)
    kpi = next(k for k in view.kpis if k.key == "total_cost_eur")
    assert kpi.cm_drivers[0].startswith("FM-001")

