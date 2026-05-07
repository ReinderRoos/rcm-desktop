from __future__ import annotations

from pathlib import Path

from rcm_core.incremental_run import IncrementalRunResult
from rcm_core.models import FMResult
from rcm_core.persistence import load_project
from rcm_desktop.adapter import run_service


def _fm_result(fm_id: str, expected_failures: float, total_cost_eur: float) -> FMResult:
    return FMResult(
        fm_id=fm_id,
        pbs_id="PBS-1",
        p_failure_lifecycle=0.1,
        expected_failures=expected_failures,
        expected_raw_downtime_hr=1.0,
        expected_detection_delay_hr=0.5,
        expected_total_downtime_hr=1.5,
        expected_pm_downtime_hr=0.2,
        expected_cm_cost_eur=25.0,
        pm_cost_eur=10.0,
        total_cost_eur=total_cost_eur,
        risk_contribution=0.01,
        effect_bijdragen={},
    )


def test_run_service_happy_path_maps_metrics_and_status(monkeypatch):
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    project = load_project(fixture)
    fake_result = IncrementalRunResult(
        fm_results={
            "FM-1": _fm_result("FM-1", expected_failures=1.25, total_cost_eur=100.0),
            "FM-2": _fm_result("FM-2", expected_failures=2.75, total_cost_eur=60.5),
        },
        pbs_results={},
        cache_only=False,
        affected_fm_ids=[],
        recalculated_fm_count=2,
        parallel_retried_sequential=False,
    )

    monkeypatch.setattr(run_service, "run_incremental_analysis", lambda *_args, **_kwargs: fake_result)

    result = run_service.run(project, fixture)

    assert result.status == "done"
    assert result.error is None
    assert result.metrics.fm_result_count == 2
    assert result.metrics.total_lifecycle_faalmomenten == 4.0
    assert result.metrics.total_cost_eur == 160.5
    assert len(result.rows) == 2
    assert result.rows[0].fm_id == "FM-1"
    assert result.rows[0].expected_total_downtime_hr == 1.5


def test_run_service_missing_project_returns_precondition_error():
    result = run_service.run(None, "tests/fixtures/sample_project.rcm.json")

    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "RUN_PRECONDITION_NOT_MET"
    assert result.metrics.fm_result_count == 0
    assert result.rows == []


def test_run_service_maps_unexpected_core_error(monkeypatch):
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    project = load_project(fixture)

    def fake_raise(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(run_service, "run_incremental_analysis", fake_raise)

    result = run_service.run(project, fixture)

    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "RUN_INTERNAL_ERROR"
    assert result.metrics.total_lifecycle_faalmomenten == 0.0
    assert result.metrics.total_cost_eur == 0.0
    assert result.rows == []


def test_run_service_passes_full_recompute_kwarg(monkeypatch):
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    project = load_project(fixture)
    captured: dict[str, object] = {}
    fake_result = IncrementalRunResult(
        fm_results={},
        pbs_results={},
        cache_only=False,
        affected_fm_ids=[],
        recalculated_fm_count=0,
        parallel_retried_sequential=False,
    )

    def fake_run(project_arg, project_path_arg, **kwargs):
        captured["project"] = project_arg
        captured["project_path"] = project_path_arg
        captured["kwargs"] = kwargs
        return fake_result

    monkeypatch.setattr(run_service, "run_incremental_analysis", fake_run)

    result = run_service.run(project, fixture, full_recompute=True, parallel=False)

    assert result.status == "done"
    assert captured["project"] == project
    assert captured["project_path"] == fixture
    assert captured["kwargs"] == {"full_recompute": True, "parallel": False}
