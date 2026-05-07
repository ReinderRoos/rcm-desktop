from __future__ import annotations

import time
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtTest import QSignalSpy
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from rcm_desktop import messages
from rcm_desktop.adapter.faalwijzen_edit_service import SLICE_FIELD_KEYS
from rcm_desktop.adapter.project_paths import resolve_default_fixture_path
from rcm_desktop.adapter.preview_service import ProjectPreview, TopFaalwijze
from rcm_desktop.adapter.run_runner import RunRunner
from rcm_desktop.adapter.run_service import RunMetrics, RunResult
from rcm_desktop.adapter.result_view_service import FMResultRow, PBSResultRow
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


def _spy_count(spy: QSignalSpy) -> int:
    count_fn = getattr(spy, "count", None)
    if callable(count_fn):
        return int(count_fn())
    return len(spy)


def _spy_wait_min(app: QApplication, spy: QSignalSpy, minimum: int = 1, timeout_s: float = 3.0) -> None:
    deadline = time.time() + timeout_s
    while _spy_count(spy) < minimum and time.time() < deadline:
        app.processEvents()
        time.sleep(0.01)


def _spy_emission_args(spy: QSignalSpy, emission_index: int = 0) -> tuple:
    at = getattr(spy, "at", None)
    if callable(at):
        args = at(emission_index)
        try:
            return tuple(args[i] for i in range(len(args)))  # type: ignore[arg-type]
        except Exception:
            pass
        try:
            return tuple(args)
        except TypeError:
            return (args,)
    return tuple(spy[emission_index])


def _align_project_path_then_validate_state(window: ValidateWindow, fixture: Path, app: QApplication) -> None:
    """Match path field to fixture before setting validated project (avoids stale AWZI default path only)."""
    window.path_input.setText(str(fixture.resolve()))
    app.processEvents()


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
    assert _spy_count(spy) == 1


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
    assert _spy_count(spy) == 1


def test_app_state_keeps_last_project_and_emits_signal():
    app = _ensure_app()
    state = AppState()
    spy = QSignalSpy(state.project_changed)
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    project = load_project(fixture)

    state.set_last_project(project)
    app.processEvents()

    assert state.last_project == project
    assert _spy_count(spy) == 1


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
    assert _spy_count(spy) == 1


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
    _spy_wait_min(app, results)
    _spy_wait_min(app, previews)

    deadline = time.time() + 2
    while _spy_count(states) < 3 and time.time() < deadline:
        app.processEvents()
        time.sleep(0.01)

    assert _spy_count(results) == 1
    assert _spy_count(previews) == 1
    assert _spy_count(projects) == 1
    assert _spy_emission_args(previews, 0)[0] == preview
    assert _spy_emission_args(projects, 0)[0] is not None
    state_values = [_spy_emission_args(states, i)[0] for i in range(_spy_count(states))]
    assert "busy" in state_values
    assert "idle" in state_values


def test_validate_runner_emits_empty_preview_for_invalid(monkeypatch):
    app = _ensure_app()
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
    _spy_wait_min(app, previews)
    _spy_wait_min(app, projects)

    assert build_calls["count"] == 0
    assert _spy_emission_args(previews, 0)[0] is None
    assert _spy_emission_args(projects, 0)[0] is None


def test_validate_runner_emits_empty_preview_when_project_missing(monkeypatch):
    app = _ensure_app()
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
    _spy_wait_min(app, previews)

    assert build_calls["count"] == 0
    assert _spy_emission_args(previews, 0)[0] is None


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
    _spy_wait_min(app, results)

    deadline = time.time() + 2
    while _spy_count(states) < 3 and time.time() < deadline:
        app.processEvents()
        time.sleep(0.01)

    assert _spy_count(results) == 1
    assert _spy_emission_args(results, 0)[0] == result
    state_values = [_spy_emission_args(states, i)[0] for i in range(_spy_count(states))]
    assert "busy" in state_values
    assert "idle" in state_values


def test_validate_window_run_button_and_panel_flow(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: QMessageBox.Ok)
    window = ValidateWindow()
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    _align_project_path_then_validate_state(window, fixture, app)
    window.show()

    assert window.run_button.isEnabled() is False
    window._state.set_last_result(ValidateResult(status="valid", summary="ok", details=[]))
    window._state.set_last_project(load_project(fixture))
    app.processEvents()
    assert window.run_button.isEnabled() is True
    assert window.faalwijzen_group.isVisible() is True
    assert window.faalwijzen_table.model() is not None

    done_result = RunResult(
        status="done",
        summary="klaar",
        metrics=RunMetrics(fm_result_count=7, total_lifecycle_faalmomenten=9.5, total_cost_eur=1200.0),
        rows=[
            FMResultRow(
                fm_id="FM-1",
                faalwijze_omschrijving="omschrijving",
                pbs_id="PBS-1",
                bouwdeel_naam="Bouwdeel A",
                expected_failures=7.0,
                expected_total_downtime_hr=9.5,
                total_cost_eur=1200.0,
            )
        ],
        pbs_rows=[
            PBSResultRow(
                pbs_id="PBS-ROOT",
                bouwdeel_naam="Root",
                parent_pbs_id=None,
                level=0,
                sort_path=("PBS-ROOT",),
                expected_failures_self=0.0,
                total_downtime_hr_self=0.0,
                total_cost_eur_self=0.0,
                expected_failures_total=7.0,
                total_downtime_hr_total=9.5,
                total_cost_eur_total=1200.0,
                unavailability_pct_total=1.0,
            )
        ],
    )
    window._state.set_last_run(done_result)
    app.processEvents()

    assert window.run_group.isVisible() is True
    assert window.run_fm_result_count_value.text() == "7"
    assert window.run_total_faalmomenten_value.text() == "9,50"
    assert window.run_total_cost_value.text() == "€ 1.200,00"
    assert window.result_table_group.isVisible() is True
    assert window.pbs_table_group.isVisible() is True
    assert window.pbs_table.horizontalHeader().sortIndicatorSection() == -1
    assert window.pbs_tree.model() is not None

    window.path_input.setText("nieuw-pad.rcm.json")
    app.processEvents()
    assert window.run_group.isVisible() is False
    assert window.faalwijzen_group.isVisible() is False
    assert window.faalwijzen_table.model() is None
    assert window.result_table_group.isVisible() is False
    assert window.pbs_table_group.isVisible() is False
    assert window.pbs_tree.model() is None
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
        rows=[],
        pbs_rows=[],
        error=UserFacingError(code="RUN_INTERNAL_ERROR", message="Analyse intern mislukt"),
    )

    window._state.set_last_run(error_result)
    app.processEvents()

    assert window.run_status_value.text() == "Fout"
    assert window.result_table_group.isVisible() is False
    assert window.pbs_table_group.isVisible() is False
    assert captured["title"] == messages.RUN_ERROR_DIALOG_TITLE
    assert captured["message"] == "Analyse intern mislukt"


def test_validate_window_hides_results_table_for_empty_rows(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: QMessageBox.Ok)
    window = ValidateWindow()
    done_result = RunResult(
        status="done",
        summary="klaar",
        metrics=RunMetrics(fm_result_count=0, total_lifecycle_faalmomenten=0.0, total_cost_eur=0.0),
        rows=[],
        pbs_rows=[],
    )

    window._state.set_last_run(done_result)
    app.processEvents()

    assert window.result_table_group.isVisible() is False
    assert window.pbs_table_group.isVisible() is False


def test_validate_window_hides_pbs_table_for_empty_pbs_rows(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: QMessageBox.Ok)
    window = ValidateWindow()
    window.show()
    done_result = RunResult(
        status="done",
        summary="klaar",
        metrics=RunMetrics(fm_result_count=1, total_lifecycle_faalmomenten=1.0, total_cost_eur=2.0),
        rows=[
            FMResultRow(
                fm_id="FM-1",
                faalwijze_omschrijving="omschrijving",
                pbs_id="PBS-1",
                bouwdeel_naam="Bouwdeel A",
                expected_failures=1.0,
                expected_total_downtime_hr=1.0,
                total_cost_eur=2.0,
            )
        ],
        pbs_rows=[],
    )

    window._state.set_last_run(done_result)
    app.processEvents()

    assert window.result_table_group.isVisible() is True
    assert window.pbs_table_group.isVisible() is False
    assert window.pbs_tree.model() is None


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
    window.show()
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
    window.show()

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


def _fm_row(model, fm_id: str) -> int:
    for r in range(model.rowCount()):
        if model.data(model.index(r, 0), Qt.DisplayRole) == fm_id:
            return r
    raise AssertionError(f"missing {fm_id}")


def test_validate_window_run_disabled_when_faalwijzen_edit_has_errors(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: QMessageBox.Ok)
    window = ValidateWindow()
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    _align_project_path_then_validate_state(window, fixture, app)
    window.show()
    window._state.set_last_result(ValidateResult(status="valid", summary="ok", details=[]))
    window._state.set_last_project(load_project(fixture))
    app.processEvents()
    assert window.faalwijzen_group.isVisible() is True
    model = window.faalwijzen_table.model()
    row = _fm_row(model, "FM-001")
    ix = model.index(row, SLICE_FIELD_KEYS.index("mttf_jaar"))
    model.setData(ix, "0", Qt.EditRole)
    model.emit_grid_refresh()
    assert window.run_button.isEnabled() is False


def test_validate_window_run_materializes_edited_project(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: QMessageBox.Ok)
    window = ValidateWindow()
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    _align_project_path_then_validate_state(window, fixture, app)
    window.show()
    window._state.set_last_result(ValidateResult(status="valid", summary="ok", details=[]))
    window._state.set_last_project(load_project(fixture))
    app.processEvents()

    model = window.faalwijzen_table.model()
    row = _fm_row(model, "FM-001")
    ix = model.index(row, SLICE_FIELD_KEYS.index("mttf_jaar"))
    model.setData(ix, "77", Qt.EditRole)
    model.emit_grid_refresh()

    captured: dict[str, object] = {}

    def fake_start(proj: object, path: str) -> bool:
        captured["project"] = proj
        captured["path"] = path
        return True

    monkeypatch.setattr(window._run_runner, "start", fake_start)
    window._start_run()
    assert "project" in captured
    proj = captured["project"]
    assert proj.faalwijzes["FM-001"].mttf_jaar == pytest.approx(77.0)


def test_validate_window_materialize_blocked_shows_modal_and_skips_runner(monkeypatch):
    app = _ensure_app()
    msgs: list[str] = []

    def fake_critical(_p, _t, message: str) -> int:
        msgs.append(message)
        return QMessageBox.Ok

    monkeypatch.setattr(QMessageBox, "critical", fake_critical)
    window = ValidateWindow()
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    _align_project_path_then_validate_state(window, fixture, app)
    window.show()
    window._state.set_last_result(ValidateResult(status="valid", summary="ok", details=[]))
    window._state.set_last_project(load_project(fixture))
    app.processEvents()

    model = window.faalwijzen_table.model()
    row = _fm_row(model, "FM-001")
    ix = model.index(row, SLICE_FIELD_KEYS.index("mttf_jaar"))
    model.setData(ix, "0", Qt.EditRole)
    model.emit_grid_refresh()

    started: list[int] = []

    def fake_start(*_a, **_k) -> bool:
        started.append(1)
        return True

    monkeypatch.setattr(window._run_runner, "start", fake_start)
    window._start_run()

    assert started == []
    assert msgs
