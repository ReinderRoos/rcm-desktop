"""Slice 24 issue 06 — scenario-runner parallel + cache-hergebruik."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from rcm_core.incremental_run import run_incremental_analysis
from rcm_core.persistence import load_project
from rcm_desktop.adapter.run_service import RunResult, run as run_single
from rcm_desktop.adapter.scenario_run_service import (
    SCENARIO_CM,
    SCENARIO_PM,
    build_project_for_scenario,
    run_cm,
    run_pm,
)


@pytest.fixture
def sample_path(tmp_path) -> Path:
    src = Path("tests/fixtures/sample_project.rcm.json")
    dst = tmp_path / "sample.rcm.json"
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return dst


@pytest.fixture
def sample_project(sample_path):
    return load_project(sample_path)


def test_scenario_run_uses_parallel_incremental_defaults(monkeypatch, sample_project, sample_path):
    captured: dict = {}

    def fake_run(project, path, **kwargs):
        captured.update(kwargs)
        return RunResult(
            status="done",
            summary="ok",
            metrics=__import__(
                "rcm_desktop.adapter.run_service", fromlist=["RunMetrics"]
            ).RunMetrics(0, 0.0, 0.0),
        )

    monkeypatch.setattr(
        "rcm_desktop.adapter.scenario_run_service.run_single",
        fake_run,
    )
    run_cm(sample_project, sample_path)
    assert captured["parallel"] is True
    assert captured["full_recompute"] is False


def test_repeat_cm_run_is_cache_only(sample_project, sample_path):
    cm_project = build_project_for_scenario(sample_project, SCENARIO_CM)
    first = run_incremental_analysis(
        cm_project, sample_path, full_recompute=False, parallel=True, scenario_key=SCENARIO_CM
    )
    assert first.cache_only is False
    assert first.recalculated_fm_count > 0

    second = run_incremental_analysis(
        cm_project, sample_path, full_recompute=False, parallel=True, scenario_key=SCENARIO_CM
    )
    assert second.cache_only is True
    assert second.recalculated_fm_count == 0


def test_repeat_pm_run_is_cache_only(sample_project, sample_path):
    pm_project = build_project_for_scenario(sample_project, SCENARIO_PM)
    run_incremental_analysis(
        pm_project, sample_path, full_recompute=False, parallel=True, scenario_key=SCENARIO_PM
    )
    second = run_incremental_analysis(
        pm_project, sample_path, full_recompute=False, parallel=True, scenario_key=SCENARIO_PM
    )
    assert second.cache_only is True
    assert second.recalculated_fm_count == 0


def test_cm_after_pm_uses_cm_cache_not_pm_cache(sample_project, sample_path):
    cm_project = build_project_for_scenario(sample_project, SCENARIO_CM)
    pm_project = build_project_for_scenario(sample_project, SCENARIO_PM)

    run_incremental_analysis(
        cm_project, sample_path, full_recompute=False, parallel=True, scenario_key=SCENARIO_CM
    )
    run_incremental_analysis(
        pm_project, sample_path, full_recompute=False, parallel=True, scenario_key=SCENARIO_PM
    )

    only_pm_then_cm = run_incremental_analysis(
        cm_project, sample_path, full_recompute=False, parallel=True, scenario_key=SCENARIO_CM
    )
    assert only_pm_then_cm.cache_only is True
    assert only_pm_then_cm.recalculated_fm_count == 0

    pm_only = run_incremental_analysis(
        pm_project, sample_path, full_recompute=False, parallel=True, scenario_key=SCENARIO_PM
    )
    assert pm_only.cache_only is True


def test_repeat_scenario_run_is_under_300ms(sample_project, sample_path):
    cm_project = build_project_for_scenario(sample_project, SCENARIO_CM)
    run_incremental_analysis(
        cm_project, sample_path, full_recompute=False, parallel=True, scenario_key=SCENARIO_CM
    )
    t0 = time.perf_counter()
    run_incremental_analysis(
        cm_project, sample_path, full_recompute=False, parallel=True, scenario_key=SCENARIO_CM
    )
    elapsed = time.perf_counter() - t0
    assert elapsed < 0.3
