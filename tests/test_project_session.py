"""Issue 1 — ProjectSession on AppState (TDD)."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from rcm_core.config import RCMConfig
from rcm_core.models import RCMProject
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.run_service import RunMetrics, RunResult
from rcm_desktop.app_state import AppState


def _ensure_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _project() -> RCMProject:
    return RCMProject(config=RCMConfig(lifecycle_years=40.0, modeljaar=2026))


def _run() -> RunResult:
    return RunResult(
        status="done",
        summary="ok",
        metrics=RunMetrics(
            fm_result_count=0,
            total_lifecycle_faalmomenten=0.0,
            total_cost_eur=0.0,
            total_downtime_hr=0.0,
            lifecycle_years=40.0,
        ),
    )


def test_set_last_project_populates_project_session() -> None:
    _ensure_app()
    state = AppState()
    project = _project()
    state.set_last_project(project, path=Path("/tmp/demo.rcm.json"))

    session = state.project_session
    assert isinstance(session, ProjectSession)
    assert session.path == Path("/tmp/demo.rcm.json")
    assert session.loaded.modeljaar == 2026
    assert session.run is None


def test_set_last_run_updates_project_session_run() -> None:
    _ensure_app()
    state = AppState()
    project = _project()
    state.set_last_project(project)
    run = _run()
    state.set_last_run(run)

    session = state.project_session
    assert session is not None
    assert session.run is run


def test_set_last_project_and_run_keeps_session_in_sync() -> None:
    _ensure_app()
    state = AppState()
    project = _project()
    run = _run()
    state.set_last_project_and_run(project, run, path=Path("/data/proj.rcm.json"))

    session = state.project_session
    assert session is not None
    assert session.path == Path("/data/proj.rcm.json")
    assert session.run is run
    assert state.last_project is project
    assert state.loaded_project is session.loaded


def test_clearing_project_clears_project_session() -> None:
    _ensure_app()
    state = AppState()
    state.set_last_project(_project())
    state.set_last_project(None)

    assert state.project_session is None
