from __future__ import annotations

import time
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication, QMessageBox

from rcm_desktop import messages
from rcm_desktop.adapter.project_paths import resolve_default_fixture_path
from rcm_desktop.adapter.preview_service import ProjectPreview, TopFaalwijze
from rcm_desktop.adapter.run_runner import RunRunner
from rcm_desktop.adapter.run_service import RunMetrics, RunResult
from rcm_desktop.adapter.validate_runner import ValidateRunner
from rcm_desktop.adapter.validate_service import DetailItem, UserFacingError, ValidateResult
from rcm_desktop.app_state import AppState
from rcm_core.persistence import load_project
from rcm_desktop.views.validate_window import ValidateWindow


def _ensure_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_resolve_default_fixture_path_finds_repo_fixture():
    fixture = resolve_default_fixture_path(Path.cwd())
    assert fixture is not None
    assert fixture.name == "awzi_haarlem_waarderpolder_demo.rcm.json"


def test_resolve_default_fixture_path_returns_none_when_missing(tmp_path: Path):
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    assert resolve_default_fixture_path(nested) is None


def test_app_state_keeps_last_result_and_emits_signal():
    app = _ensure_app()
    state = AppState()
    spy = QSignalSpy(state.result_changed)
    result = ValidateResult(status="valid", summary="ok", details=[])

    state.set_last_result(result)
    app.processEvents()

    assert state.last_result == result
    assert len(spy) == 1


def test_app_state_keeps_last_preview_and_emits_signal():
    app = _ensure_app()
    state = AppState()
    spy = QSignalSpy(state.preview_changed)
    preview = ProjectPreview(
        pbs_items=1,
        functies=2,
        faalwijzes=3,
        pm_tasks=4,
        top_faalwijzes=[TopFaalwijze(fm_id="FM-1", faalwijze_omschrijving="omschrijving")],
    )

    state.set_last_preview(preview)
    app.processEvents()

    assert state.last_preview == preview
    assert len(spy) == 1


def test_app_state_keeps_last_project_and_emits_signal():
    app = _ensure_app()
    state = AppState()
    spy = QSignalSpy(state.project_changed)
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    project = load_project(fixture)

    state.set_last_project(project)
    app.processEvents()

    assert state.last_project == project
    assert len(spy) == 1


def test_app_state_keeps_last_run_and_emits_signal():
    app = _ensure_app()
    state = AppState()
    spy = QSignalSpy(state.run_changed)
    run_result = RunResult(
        status="done",
        summary="klaar",
        metrics=RunMetrics(
            fm_result_count=2,
            total_lifecycle_faalmomenten=3.5,
            total_cost_eur=120.0,
        ),
    )

    state.set_last_run(run_result)
    app.processEvents()

    assert state.last_run == run_result
    assert len(spy) == 1


def test_validate_runner_emits_result_and_rejects_reentry(monkeypatch):
    app = _ensure_app()
    runner = ValidateRunner()
    result = ValidateResult(status="valid", summary="ok", details=[])
    preview = ProjectPreview(pbs_items=1, functies=2, faalwijzes=3, pm_tasks=4, top_faalwijzes=[])

    def fake_run(_path: str) -> tuple[ValidateResult, object]:
        time.sleep(0.05)
        return result, object()

    monkeypatch.setattr("rcm_desktop.adapter.validate_service.run", fake_run)
    monkeypatch.setattr("rcm_desktop.adapter.preview_service.build", lambda _project: preview)

    states = QSignalSpy(runner.state_changed)
    results = QSignalSpy(runner.result_ready)
    previews = QSignalSpy(runner.preview_ready)
    projects = QSignalSpy(runner.project_ready)

    assert runner.start("x.rcm.json") is True
    assert runner.start("x.rcm.json") is False
    assert results.wait(2000)
    assert previews.wait(2000)

    deadline = time.time() + 2
    while len(states) < 3 and time.time() < deadline:
        app.processEvents()
        time.sleep(0.01)

    assert len(results) == 1
    assert len(previews) == 1
    assert len(projects) == 1
    assert previews[0][0] == preview
    assert projects[0][0] is not None
    state_values = [entry[0] for entry in states]
    assert "busy" in state_values
    assert "idle" in state_values


def test_validate_runner_emits_empty_preview_for_invalid(monkeypatch):
    runner = ValidateRunner()
    result = ValidateResult(status="invalid", summary="bad", details=[])

    monkeypatch.setattr("rcm_desktop.adapter.validate_service.run", lambda _path: (result, object()))
    build_calls = {"count": 0}

    def fake_build(_project):
        build_calls["count"] += 1
        return ProjectPreview(0, 0, 0, 0, [])

    monkeypatch.setattr("rcm_desktop.adapter.preview_service.build", fake_build)

    previews = QSignalSpy(runner.preview_ready)
    projects = QSignalSpy(runner.project_ready)
    assert runner.start("x.rcm.json") is True
    assert previews.wait(2000)

    assert build_calls["count"] == 0
    assert previews[0][0] is None
    assert projects[0][0] is None


def test_validate_runner_emits_empty_preview_when_project_missing(monkeypatch):
    runner = ValidateRunner()
    result = ValidateResult(status="valid", summary="ok", details=[])

    monkeypatch.setattr("rcm_desktop.adapter.validate_service.run", lambda _path: (result, None))
    build_calls = {"count": 0}

    def fake_build(_project):
        build_calls["count"] += 1
        return ProjectPreview(0, 0, 0, 0, [])

    monkeypatch.setattr("rcm_desktop.adapter.preview_service.build", fake_build)

    previews = QSignalSpy(runner.preview_ready)
    assert runner.start("x.rcm.json") is True
    assert previews.wait(2000)

    assert build_calls["count"] == 0
    assert previews[0][0] is None


def test_run_runner_emits_result_and_rejects_reentry(monkeypatch):
    app = _ensure_app()
    runner = RunRunner()
    result = RunResult(
        status="done",
        summary="ok",
        metrics=RunMetrics(fm_result_count=2, total_lifecycle_faalmomenten=3.0, total_cost_eur=10.0),
    )

    def fake_run(*_args, **_kwargs):
        time.sleep(0.05)
        return result

    monkeypatch.setattr("rcm_desktop.adapter.run_service.run", fake_run)

    states = QSignalSpy(runner.state_changed)
    results = QSignalSpy(runner.result_ready)

    assert runner.start(object(), "x.rcm.json") is True
    assert runner.start(object(), "x.rcm.json") is False
    assert results.wait(2000)

    deadline = time.time() + 2
    while len(states) < 3 and time.time() < deadline:
        app.processEvents()
        time.sleep(0.01)

    assert len(results) == 1
    assert results[0][0] == result
    state_values = [entry[0] for entry in states]
    assert "busy" in state_values
    assert "idle" in state_values


def test_validate_window_run_button_and_panel_flow(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: QMessageBox.Ok)
    window = ValidateWindow()

    assert window.run_button.isEnabled() is False
    window._state.set_last_result(ValidateResult(status="valid", summary="ok", details=[]))
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    window._state.set_last_project(load_project(fixture))
    app.processEvents()
    assert window.run_button.isEnabled() is True

    done_result = RunResult(
        status="done",
        summary="klaar",
        metrics=RunMetrics(fm_result_count=7, total_lifecycle_faalmomenten=9.5, total_cost_eur=1200.0),
    )
    window._state.set_last_run(done_result)
    app.processEvents()

    assert window.run_group.isVisible() is True
    assert window.run_fm_result_count_value.text() == "7"
    assert window.run_total_faalmomenten_value.text() == "9.5"
    assert window.run_total_cost_value.text() == "1200.0"

    window.path_input.setText("nieuw-pad.rcm.json")
    app.processEvents()
    assert window.run_group.isVisible() is False
    assert window._state.last_run is None


def test_validate_window_shows_run_error_inline_and_modal(monkeypatch):
    app = _ensure_app()
    captured: dict[str, str] = {}

    def fake_critical(_parent, title: str, message: str):
        captured["title"] = title
        captured["message"] = message
        return QMessageBox.Ok

    monkeypatch.setattr(QMessageBox, "critical", fake_critical)
    window = ValidateWindow()
    error_result = RunResult(
        status="error",
        summary="kapot",
        metrics=RunMetrics(fm_result_count=0, total_lifecycle_faalmomenten=0.0, total_cost_eur=0.0),
        error=UserFacingError(code="RUN_INTERNAL_ERROR", message="Analyse intern mislukt"),
    )

    window._state.set_last_run(error_result)
    app.processEvents()

    assert window.run_status_value.text() == "Fout"
    assert captured["title"] == messages.RUN_ERROR_DIALOG_TITLE
    assert captured["message"] == "Analyse intern mislukt"


def test_validate_window_replaces_previous_result(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: QMessageBox.Ok)
    window = ValidateWindow()

    first = ValidateResult(
        status="invalid",
        summary="eerste run",
        details=[DetailItem(severity="error", code="E1", message="m1")],
    )
    second = ValidateResult(
        status="valid",
        summary="tweede run",
        details=[],
    )

    window._render_result(first)
    window._render_result(second)
    app.processEvents()

    assert window.summary_label.text() == "tweede run"
    assert window.details_text.toPlainText() == ""


def test_validate_window_shows_modal_and_inline_on_error(monkeypatch):
    app = _ensure_app()
    captured: dict[str, str] = {}

    def fake_critical(_parent, title: str, message: str):
        captured["title"] = title
        captured["message"] = message
        return QMessageBox.Ok

    monkeypatch.setattr(QMessageBox, "critical", fake_critical)
    window = ValidateWindow()
    result = ValidateResult(
        status="error",
        summary="io fout",
        details=[],
        error=UserFacingError(code="FILE_NOT_FOUND", message="bestaat niet"),
    )

    window._render_result(result)
    app.processEvents()

    assert window.status_label.text() == "Fout"
    assert captured["message"] == "bestaat niet"


def test_validate_window_renders_preview_and_clears_on_new_run(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: QMessageBox.Ok)
    window = ValidateWindow()
    window.path_input.setText("tests/fixtures/sample_project.rcm.json")

    preview = ProjectPreview(
        pbs_items=11,
        functies=12,
        faalwijzes=0,
        pm_tasks=13,
        top_faalwijzes=[],
    )
    window._on_preview_ready(preview)
    app.processEvents()

    assert window.preview_group.isVisible()
    assert window.preview_pbs_value.text() == "11"
    assert window.preview_top5_list.count() == 1
    assert window.preview_top5_list.item(0).text() == messages.PREVIEW_EMPTY_TOP5

    monkeypatch.setattr(window._runner, "start", lambda _path: True)
    window._start_validate()
    app.processEvents()

    assert window.preview_group.isVisible() is False
    assert window.preview_top5_list.count() == 0


def test_validate_window_hides_existing_preview_on_error_result(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: QMessageBox.Ok)
    window = ValidateWindow()

    preview = ProjectPreview(
        pbs_items=2,
        functies=3,
        faalwijzes=1,
        pm_tasks=4,
        top_faalwijzes=[TopFaalwijze(fm_id="FM-1", faalwijze_omschrijving="omschrijving")],
    )
    window._on_preview_ready(preview)
    app.processEvents()
    assert window.preview_group.isVisible()

    error_result = ValidateResult(
        status="error",
        summary="fout",
        details=[],
        error=UserFacingError(code="UNEXPECTED_ERROR", message="kapot"),
    )
    window._render_result(error_result)
    window._on_preview_ready(None)
    app.processEvents()

    assert window.preview_group.isVisible() is False
    assert window.preview_top5_list.count() == 0
