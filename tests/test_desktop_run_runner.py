from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication

from rcm_core.incremental_run import IncrementalRunResult
from rcm_core.persistence import load_project
from rcm_desktop.adapter import run_service
from rcm_desktop.adapter.run_runner import RunRunner


@pytest.fixture(scope="module")
def qapp():
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app


def test_run_runner_start_analyse_uses_incremental_run(qapp, monkeypatch):
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    project = load_project(fixture)
    captured: dict[str, object] = {}
    fake_result = IncrementalRunResult(
        fm_results={},
        pbs_results={},
        cache_only=True,
        affected_fm_ids=[],
        recalculated_fm_count=0,
        parallel_retried_sequential=False,
    )

    def fake_run(*_args, **kwargs):
        captured["kwargs"] = kwargs
        return fake_result

    monkeypatch.setattr(run_service, "run_incremental_analysis", fake_run)

    runner = RunRunner()
    runner.start(project, fixture, force_recompute=False)

    while runner.busy:
        qapp.processEvents()

    assert captured["kwargs"] == {
        "full_recompute": False,
        "parallel": True,
        "scenario_key": None,
    }


def test_run_runner_force_recompute_uses_full_run(qapp, monkeypatch):
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

    def fake_run(*_args, **kwargs):
        captured["kwargs"] = kwargs
        return fake_result

    monkeypatch.setattr(run_service, "run_incremental_analysis", fake_run)

    runner = RunRunner()
    runner.start(project, fixture, force_recompute=True)

    while runner.busy:
        qapp.processEvents()

    assert captured["kwargs"] == {
        "full_recompute": True,
        "parallel": True,
        "scenario_key": None,
    }
