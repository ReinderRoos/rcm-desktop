"""Slice 65 — RCM-Cost benchmark parity (Qt-free core)."""

from __future__ import annotations

from rcm_core.models import FMResult, RCMProject
from rcm_core.rcm_cost_benchmark import (
    ParityVerdict,
    aw_tolerance_eur,
    build_parity_report,
    has_aw_benchmarks,
    metric_within_aw_band,
)


def _fm_result(
    fm_id: str,
    *,
    total_cost: float = 100.0,
    downtime_hr: float = 10.0,
) -> FMResult:
    return FMResult(
        fm_id=fm_id,
        pbs_id="P1",
        p_failure_lifecycle=0.5,
        expected_failures=1.0,
        expected_raw_downtime_hr=downtime_hr,
        expected_detection_delay_hr=0.0,
        expected_total_downtime_hr=downtime_hr,
        expected_pm_downtime_hr=0.0,
        expected_cm_cost_eur=total_cost,
        pm_cost_eur=0.0,
        total_cost_eur=total_cost,
        risk_contribution=0.0,
    )


def test_aw_tolerance_uses_max_of_abs_and_percent() -> None:
    assert aw_tolerance_eur(1000.0, err_pc=5.0, err_abs=10.0) == 50.0
    assert aw_tolerance_eur(1000.0, err_pc=None, err_abs=25.0) == 25.0
    assert aw_tolerance_eur(1000.0, err_pc=2.0, err_abs=None) == 20.0


def test_metric_within_band_pass_and_fail() -> None:
    assert metric_within_aw_band(
        actual=104.0,
        aw_value=100.0,
        err_pc=5.0,
        err_abs=None,
    )
    assert not metric_within_aw_band(
        actual=106.0,
        aw_value=100.0,
        err_pc=5.0,
        err_abs=None,
    )


def test_has_aw_benchmarks_requires_total_cost() -> None:
    project = RCMProject(
        import_settings={
            "isograph_causes": {
                "FM-1": {"TotalCostErrPc": 1.0},
            }
        }
    )
    assert not has_aw_benchmarks(project)

    project.import_settings["isograph_causes"]["FM-1"]["TotalCost"] = 1000.0
    assert has_aw_benchmarks(project)


def test_build_parity_report_pass_fail_and_missing() -> None:
    project = RCMProject(
        faalwijzes={},
        import_settings={
            "isograph_causes": {
                "FM-PASS": {
                    "TotalCost": 100.0,
                    "TotalCostErrPc": 5.0,
                },
                "FM-FAIL": {
                    "TotalCost": 200.0,
                    "TotalCostErrPc": 1.0,
                },
                "FM-NO-BENCH": {
                    "TotalCostErrPc": 1.0,
                },
            }
        },
    )
    fm_results = {
        "FM-PASS": _fm_result("FM-PASS", total_cost=102.0),
        "FM-FAIL": _fm_result("FM-FAIL", total_cost=250.0),
        "FM-NO-BENCH": _fm_result("FM-NO-BENCH", total_cost=50.0),
    }
    report = build_parity_report(project, fm_results)

    by_id = {row.fm_id: row for row in report.rows}
    assert by_id["FM-PASS"].verdict == ParityVerdict.PASS
    assert by_id["FM-FAIL"].verdict == ParityVerdict.FAIL
    assert by_id["FM-NO-BENCH"].verdict == ParityVerdict.MISSING_BENCHMARK

    assert report.summary.pass_count == 1
    assert report.summary.fail_count == 1
    assert report.summary.missing_benchmark_count == 1


def test_build_parity_report_includes_diagnostics() -> None:
    project = RCMProject(
        import_settings={
            "isograph_causes": {
                "FM-1": {
                    "TotalCost": 100.0,
                    "TotalCostErrPc": 10.0,
                    "TotalW": 2.5,
                    "CTdt": 10.0,
                    "PTdt": 5.0,
                    "ITdt": 1.0,
                },
            }
        },
    )
    fm_results = {
        "FM-1": _fm_result("FM-1", total_cost=100.0, downtime_hr=12.0),
    }
    row = build_parity_report(project, fm_results).rows[0]
    assert row.expected_failures_aw == 2.5
    assert row.expected_failures_rcm == 1.0
    assert row.cm_downtime_aw == 10.0
    assert row.cm_downtime_rcm == 12.0
    assert row.insp_downtime_aw == 1.0


def test_build_parity_report_total_tdt_gates_when_err_present() -> None:
    project = RCMProject(
        import_settings={
            "isograph_causes": {
                "FM-1": {
                    "TotalCost": 100.0,
                    "TotalCostErrPc": 10.0,
                    "TotalTdt": 50.0,
                    "TotalTdtErr": 1.0,
                },
            }
        },
    )
    fm_results = {
        "FM-1": _fm_result("FM-1", total_cost=100.0, downtime_hr=60.0),
    }
    report = build_parity_report(project, fm_results)
    row = report.rows[0]
    assert row.verdict == ParityVerdict.FAIL
    assert row.total_tdt_aw == 50.0
    assert row.total_tdt_rcm == 60.0
