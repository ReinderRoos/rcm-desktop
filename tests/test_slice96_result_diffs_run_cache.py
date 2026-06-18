"""Slice 96 issue 04 — cache hydrate, run A/B/both, US16 result diffs."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from rcm_core.models import FMResult
from rcm_core.persistence import load_project

from rcm_desktop.adapter.compare_balanced_presentation_service import build_compare_presentation
from rcm_desktop.adapter.compare_diff_service import build_result_diffs
from rcm_desktop.adapter.compare_results_service import (
    hydrate_compare_results,
    run_compare_analytical,
)
from rcm_desktop.adapter.compare_session_service import load_compare_session
from rcm_desktop.adapter.compare_workspace_presentation_service import (
    build_compare_workspace_view_state,
)
from rcm_desktop.adapter.run_service import run as run_analytical


def _fm_result(fm_id: str, *, cost: float = 100.0, downtime: float = 10.0, risk: float = 0.5) -> FMResult:
    return FMResult(
        fm_id=fm_id,
        pbs_id="PBS-1",
        p_failure_lifecycle=0.1,
        expected_failures=1.0,
        expected_raw_downtime_hr=downtime,
        expected_detection_delay_hr=0.0,
        expected_total_downtime_hr=downtime,
        expected_pm_downtime_hr=0.0,
        expected_cm_cost_eur=cost * 0.6,
        pm_cost_eur=cost * 0.4,
        total_cost_eur=cost,
        risk_contribution=risk,
    )


@pytest.fixture
def sample_pair(tmp_path: Path) -> tuple[Path, Path]:
    src = Path("tests/fixtures/sample_project.rcm.json")
    path_a = tmp_path / "a.rcm.json"
    path_b = tmp_path / "b.rcm.json"
    shutil.copy(src, path_a)
    shutil.copy(src, path_b)
    return path_a, path_b


def test_hydrate_compare_results_from_cache_after_run(sample_pair) -> None:
    path_a, path_b = sample_pair
    project_a = load_project(path_a)
    project_b = load_project(path_b)
    assert run_analytical(project_a, path_a).status == "done"
    assert run_analytical(project_b, path_b).status == "done"

    session = load_compare_session(path_a, path_b)
    bundle = hydrate_compare_results(session)
    assert bundle.status_a.source == "cache"
    assert bundle.status_b.source == "cache"
    assert len(bundle.results_a) >= 1
    assert len(bundle.results_b) >= 1


def test_hydrate_returns_none_source_without_cache(sample_pair) -> None:
    path_a, path_b = sample_pair
    session = load_compare_session(path_a, path_b)
    bundle = hydrate_compare_results(session)
    assert bundle.status_a.source == "none"
    assert bundle.status_b.source == "none"


def test_run_compare_analytical_side_a(sample_pair) -> None:
    path_a, path_b = sample_pair
    session = load_compare_session(path_a, path_b)
    bundle = run_compare_analytical(session, side="a")
    assert bundle.status_a.source == "run"
    assert len(bundle.results_a) >= 1


def test_run_compare_analytical_both(sample_pair) -> None:
    path_a, path_b = sample_pair
    session = load_compare_session(path_a, path_b)
    bundle = run_compare_analytical(session, side="both")
    assert bundle.status_a.source == "run"
    assert bundle.status_b.source == "run"


def test_build_result_diffs_us16_side_by_side_when_equal() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    fm_id = "FM-001"
    results = {fm_id: _fm_result(fm_id)}
    diffs = build_result_diffs(
        project,
        project,
        fm_id_a=fm_id,
        fm_id_b=fm_id,
        results_a=results,
        results_b=results,
    )
    metrics = {d.metric for d in diffs}
    assert metrics == {"total_cost_eur", "expected_total_downtime_hr", "risk_contribution"}
    for diff in diffs:
        assert diff.value_a == diff.value_b
        assert diff.is_different is False


def test_build_result_diffs_us16_marks_difference() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    fm_id = "FM-001"
    results_a = {fm_id: _fm_result(fm_id, cost=100.0)}
    results_b = {fm_id: _fm_result(fm_id, cost=200.0)}
    diffs = build_result_diffs(
        project,
        project,
        fm_id_a=fm_id,
        fm_id_b=fm_id,
        results_a=results_a,
        results_b=results_b,
    )
    cost_diff = next(d for d in diffs if d.metric == "total_cost_eur")
    assert cost_diff.is_different is True


def test_workspace_view_state_includes_run_status(sample_pair) -> None:
    path_a, path_b = sample_pair
    session = load_compare_session(path_a, path_b)
    project_a = session.project_a
    run_analytical(project_a, path_a)
    bundle = hydrate_compare_results(session)
    state = build_compare_workspace_view_state(session, results_bundle=bundle)
    assert state.run_source_a == "cache"
    assert state.run_source_b == "none"


def test_presentation_includes_result_diffs_with_cache(sample_pair) -> None:
    path_a, path_b = sample_pair
    project_a = load_project(path_a)
    run_analytical(project_a, path_a)
    session = load_compare_session(path_a, path_b)
    bundle = hydrate_compare_results(session)
    presentation = build_compare_presentation(
        session.project_a,
        session.project_b,
        results_a=bundle.results_a,
        results_b=bundle.results_b,
    )
    entry = next(e for e in presentation.entries if e.pair.match_kind == "id")
    assert len(entry.result_diffs) >= 3
