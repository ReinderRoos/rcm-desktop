from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication

from rcm_core.persistence import load_project
from rcm_desktop.adapter.presentation_cache_service import build_contribution_presentation
from rcm_desktop.adapter.run_runner import RunRunner
from rcm_desktop.adapter.run_service import RunMetrics, RunResult


@pytest.fixture(scope="module")
def qapp():
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app


def test_run_runner_post_run_builds_contribution_only(qapp, monkeypatch):
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    project = load_project(fixture)
    calls: dict[str, int] = {"contrib": 0, "lcc": 0, "nb": 0, "pm": 0}

    fake_result = RunResult(
        status="done",
        summary="klaar",
        metrics=RunMetrics(fm_result_count=0, total_lifecycle_faalmomenten=0.0, total_cost_eur=0.0),
        fm_core_results=(),
    )

    def fake_run(*_args, **_kwargs):
        return fake_result

    def spy_contrib(*_args, **_kwargs):
        calls["contrib"] += 1
        return build_contribution_presentation(project, fake_result)

    import rcm_desktop.adapter.lcc_chart_service as lcc_mod
    import rcm_desktop.adapter.pm_chart_service as pm_mod
    import rcm_desktop.adapter.run_service as run_service_mod
    import rcm_desktop.adapter.unavailability_chart_service as nb_mod

    monkeypatch.setattr(run_service_mod, "run", fake_run)
    monkeypatch.setattr(
        "rcm_desktop.adapter.run_runner.build_contribution_presentation",
        spy_contrib,
    )
    monkeypatch.setattr(lcc_mod, "build_single_run_lcc_input", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("LCC build in post-run")))
    monkeypatch.setattr(nb_mod, "build_unavailability_chart_input", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("NB build in post-run")))
    monkeypatch.setattr(pm_mod, "build_pm_chart_input", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("PM build in post-run")))

    runner = RunRunner()
    runner.start(project, fixture, force_recompute=False)

    while runner.busy:
        qapp.processEvents()

    assert calls["contrib"] == 1
