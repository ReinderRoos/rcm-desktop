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
from rcm_desktop.adapter.scenario_compare_service import KPIValue, ScenarioCompareView
from rcm_desktop.adapter.result_view_service import FMResultRow, PBSResultRow
from rcm_desktop.adapter.validate_runner import ValidateRunner
from rcm_desktop.adapter.validate_service import DetailItem, UserFacingError, ValidateResult
from rcm_desktop.app_state import AppState
from rcm_core.persistence import load_project
import rcm_desktop.views.validate_window as validate_window_module
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
    window.show()
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

    assert window.strip_run_face.isVisible() is True
    assert window.run_fm_result_count_value.text() == "7"
    assert window.run_total_faalmomenten_value.text() == "9,50"
    assert window.run_total_cost_value.text() == "€ 1.200,00"
    assert window.result_table_group.isVisible() is True
    assert window.pbs_table_group.isVisible() is False
    assert window.pbs_tree.model() is not None

    window.path_input.setText("nieuw-pad.rcm.json")
    app.processEvents()
    assert window.strip_run_face.isVisible() is False
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


def test_validate_window_dirty_indicator_and_save_gating(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: QMessageBox.Ok)
    window = ValidateWindow()
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    _align_project_path_then_validate_state(window, fixture, app)
    window._state.set_last_result(ValidateResult(status="valid", summary="ok", details=[]))
    window._state.set_last_project(load_project(fixture))
    app.processEvents()

    assert window.save_button.isEnabled() is False
    assert window.windowTitle().endswith("*") is False

    model = window.faalwijzen_table.model()
    row = _fm_row(model, "FM-001")
    ix = model.index(row, SLICE_FIELD_KEYS.index("mttf_jaar"))
    model.setData(ix, "33", Qt.EditRole)
    model.emit_grid_refresh()
    app.processEvents()

    assert window.save_button.isEnabled() is True
    assert window.save_as_button.isEnabled() is True
    assert window.windowTitle().endswith("*") is True


def test_validate_window_save_disabled_while_run_busy(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: QMessageBox.Ok)
    window = ValidateWindow()
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    _align_project_path_then_validate_state(window, fixture, app)
    window._state.set_last_result(ValidateResult(status="valid", summary="ok", details=[]))
    window._state.set_last_project(load_project(fixture))
    model = window.faalwijzen_table.model()
    row = _fm_row(model, "FM-001")
    ix = model.index(row, SLICE_FIELD_KEYS.index("mttf_jaar"))
    model.setData(ix, "42", Qt.EditRole)
    model.emit_grid_refresh()
    app.processEvents()
    assert window.save_button.isEnabled() is True

    window._run_runner._busy = True
    window._on_run_state_changed("busy")
    app.processEvents()
    assert window.save_button.isEnabled() is False


def test_validate_window_unsaved_flow_aborts_validate_when_save_fails(monkeypatch):
    app = _ensure_app()
    window = ValidateWindow()
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    _align_project_path_then_validate_state(window, fixture, app)
    window._state.set_last_result(ValidateResult(status="valid", summary="ok", details=[]))
    window._state.set_last_project(load_project(fixture))
    model = window.faalwijzen_table.model()
    row = _fm_row(model, "FM-001")
    ix = model.index(row, SLICE_FIELD_KEYS.index("mttf_jaar"))
    model.setData(ix, "88", Qt.EditRole)
    model.emit_grid_refresh()
    app.processEvents()

    monkeypatch.setattr(window, "_show_unsaved_dialog", lambda: "save")
    monkeypatch.setattr(window, "_save_current", lambda: False)
    starts: list[str] = []
    monkeypatch.setattr(window._runner, "start", lambda _path: starts.append(_path) or True)

    window._start_validate()
    app.processEvents()

    assert starts == []


def test_validate_window_compare_flow_renders_panel(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: QMessageBox.Ok)
    window = ValidateWindow()
    window.show()
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    _align_project_path_then_validate_state(window, fixture, app)
    window._state.set_last_result(ValidateResult(status="valid", summary="ok", details=[]))
    window._state.set_last_project(load_project(fixture))
    app.processEvents()

    assert window.compare_button.isEnabled() is True

    compare = ScenarioCompareView(
        status="done",
        summary="CM/PM-vergelijking beschikbaar.",
        kpis=(
            KPIValue(
                key="expected_failures",
                label="Verwachte falingen",
                cm_display="10,00",
                pm_display="8,00",
                delta_display="-2,00",
                trend="better",
                cm_drivers=("FM-001 — omsch (10,00)",),
                pm_drivers=("FM-002 — omsch (8,00)",),
            ),
        ),
    )

    monkeypatch.setattr(window._compare_runner, "start", lambda _p, _path: True)
    window._on_compare_result_ready(compare)
    app.processEvents()

    assert window.compare_group.isVisible() is True
    assert window.compare_kpi_list.count() >= 1


def test_validate_window_compare_panel_hidden_on_error(monkeypatch):
    app = _ensure_app()
    captured: dict[str, str] = {}

    def fake_critical(_parent, title: str, message: str):
        captured["title"] = title
        captured["message"] = message
        return QMessageBox.Ok

    monkeypatch.setattr(QMessageBox, "critical", fake_critical)
    window = ValidateWindow()
    view = ScenarioCompareView(status="error", summary="mislukt", kpis=tuple())

    window._on_compare_result_ready(view)
    app.processEvents()

    assert window.compare_group.isVisible() is False
    assert captured["title"] == messages.COMPARE_ERROR_DIALOG_TITLE


def test_validate_window_ltap_shift_impact_and_reset(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: QMessageBox.Ok)
    window = ValidateWindow()
    window.show()
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    _align_project_path_then_validate_state(window, fixture, app)
    window._state.set_last_result(ValidateResult(status="valid", summary="ok", details=[]))
    window._state.set_last_project(load_project(fixture))
    app.processEvents()

    assert window.ltap_group.isVisible() is True
    assert window.ltap_year_summary_label.text() == messages.LTAP_YEAR_SUMMARY_EMPTY
    assert window.ltap_detail_table.rowCount() >= 1
    window.ltap_shift_spin.setValue(1)
    window.ltap_year_list.setCurrentRow(1)
    selected_year_before = window.ltap_year_list.currentRow()
    selected_any = False
    for row_idx in range(window.ltap_detail_table.rowCount()):
        item = window.ltap_detail_table.item(row_idx, 0)
        task_item = window.ltap_detail_table.item(row_idx, 2)
        if (
            item is not None
            and task_item is not None
            and messages.LTAP_DETAIL_NON_SHIFTABLE_TAG not in task_item.text()
        ):
            window.ltap_detail_table.selectRow(row_idx)
            selected_any = True
            break
    assert selected_any is True
    window._apply_ltap_bundle()
    app.processEvents()

    assert "Δ PM-kosten" in window.ltap_impact_label.text()
    assert window.ltap_year_list.currentRow() == selected_year_before
    assert "Jaar " in window.ltap_year_summary_label.text()
    assert window._ltap_overlay_anchor_years

    window._reset_ltap_bundle()
    app.processEvents()
    assert window.ltap_impact_label.text() == messages.LTAP_IMPACT_LABEL_EMPTY
    assert not window._ltap_overlay_anchor_years
    assert window.ltap_year_summary_label.text() == messages.LTAP_YEAR_SUMMARY_EMPTY


def test_validate_window_ltap_rev_toggle_filters_chart_and_details(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: QMessageBox.Ok)
    window = ValidateWindow()
    window.show()
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    _align_project_path_then_validate_state(window, fixture, app)
    window._state.set_last_result(ValidateResult(status="valid", summary="ok", details=[]))
    window._state.set_last_project(load_project(fixture))
    app.processEvents()

    assert window.ltap_filter_button.text() == messages.LTAP_FILTER_REV_ONLY_BUTTON
    window.ltap_filter_button.click()
    app.processEvents()
    assert window.ltap_filter_button.text() == messages.LTAP_FILTER_SHOW_ALL_BUTTON
    assert window._ltap_current_view is not None
    filtered_types = {d.taak_type for y in window._ltap_current_view.years for d in y.details}
    assert filtered_types == {"REV"}
    assert window.ltap_detail_table.rowCount() >= 1
    first_label = window.ltap_detail_table.item(0, 0).text()
    assert " [REV] " in first_label


def test_validate_window_ltap_bundle_requires_table_selection(monkeypatch):
    app = _ensure_app()
    captured: dict[str, str] = {}

    def fake_critical(_parent, title: str, message: str):
        captured["title"] = title
        captured["message"] = message
        return QMessageBox.Ok

    monkeypatch.setattr(QMessageBox, "critical", fake_critical)
    window = ValidateWindow()
    window.show()
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    _align_project_path_then_validate_state(window, fixture, app)
    window._state.set_last_result(ValidateResult(status="valid", summary="ok", details=[]))
    window._state.set_last_project(load_project(fixture))
    app.processEvents()

    window.ltap_detail_table.clearSelection()
    window._apply_ltap_bundle()
    app.processEvents()

    assert captured["title"] == messages.LTAP_ERROR_DIALOG_TITLE
    assert captured["message"] == messages.LTAP_SELECTION_REQUIRED_ERROR


def test_validate_window_ltap_pm_label_contract(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: QMessageBox.Ok)
    window = ValidateWindow()
    window.show()
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    _align_project_path_then_validate_state(window, fixture, app)
    window._state.set_last_result(ValidateResult(status="valid", summary="ok", details=[]))
    window._state.set_last_project(load_project(fixture))
    app.processEvents()

    label = window.ltap_detail_table.item(0, 0).text()
    assert label.startswith("PM-")
    assert " [" in label and label.count("[") == 3


def test_validate_window_uses_harmonized_action_labels(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: QMessageBox.Ok)
    window = ValidateWindow()
    window.show()
    app.processEvents()

    assert window.validate_button.text() == messages.VALIDATE_BUTTON_LABEL
    assert window.run_button.text() == messages.RUN_BUTTON_LABEL
    assert window.compare_button.text() == messages.COMPARE_BUTTON_LABEL
    assert window.reset_layout_button.text() == messages.PANEL_RESET_LAYOUT_BUTTON
    assert window.ltap_reset_button.text() == messages.LTAP_RESET_BUTTON


def test_validate_window_ltap_apply_button_requires_selection(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: QMessageBox.Ok)
    window = ValidateWindow()
    window.show()
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    _align_project_path_then_validate_state(window, fixture, app)
    window._state.set_last_result(ValidateResult(status="valid", summary="ok", details=[]))
    window._state.set_last_project(load_project(fixture))
    app.processEvents()

    window.ltap_detail_table.clearSelection()
    window._sync_ltap_buttons()
    app.processEvents()
    assert window.ltap_apply_button.isEnabled() is False

    window.ltap_detail_table.selectRow(0)
    app.processEvents()
    assert window.ltap_apply_button.isEnabled() is True


def test_validate_window_ltap_context_label_tracks_filter_year_and_selection(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: QMessageBox.Ok)
    window = ValidateWindow()
    window.show()
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    _align_project_path_then_validate_state(window, fixture, app)
    window._state.set_last_result(ValidateResult(status="valid", summary="ok", details=[]))
    window._state.set_last_project(load_project(fixture))
    app.processEvents()

    assert "filter alle taken" in window.ltap_context_label.text()
    window.ltap_detail_table.selectRow(0)
    app.processEvents()
    assert "geselecteerd" in window.ltap_context_label.text()
    window.ltap_filter_button.click()
    app.processEvents()
    assert "filter REV" in window.ltap_context_label.text()
    window.ltap_year_list.setCurrentRow(1)
    app.processEvents()
    assert "jaar " in window.ltap_context_label.text()


def test_validate_window_applies_semantic_status_styles(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: QMessageBox.Ok)
    window = ValidateWindow()
    window.show()
    app.processEvents()

    window._render_result(ValidateResult(status="valid", summary="ok", details=[]))
    app.processEvents()
    assert "2E7D32" in window.status_label.styleSheet()

    window._render_result(ValidateResult(status="error", summary="fout", details=[]))
    app.processEvents()
    assert "D32F2F" in window.status_label.styleSheet()


def test_validate_window_ltap_table_has_readability_contract(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: QMessageBox.Ok)
    window = ValidateWindow()
    window.show()
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    _align_project_path_then_validate_state(window, fixture, app)
    window._state.set_last_result(ValidateResult(status="valid", summary="ok", details=[]))
    window._state.set_last_project(load_project(fixture))
    app.processEvents()

    assert window.ltap_detail_table.alternatingRowColors() is True
    assert window.ltap_detail_table.verticalHeader().defaultSectionSize() >= 24
    assert window.ltap_detail_table.horizontalHeaderItem(0).toolTip() != ""
    assert (
        window.ltap_detail_table.item(0, 4).textAlignment() & Qt.AlignRight
    ) == Qt.AlignRight


def test_validate_window_ltap_year_selection_updates_detail_table(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: QMessageBox.Ok)
    window = ValidateWindow()
    window.show()
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    _align_project_path_then_validate_state(window, fixture, app)
    window._state.set_last_result(ValidateResult(status="valid", summary="ok", details=[]))
    window._state.set_last_project(load_project(fixture))
    app.processEvents()

    assert window.ltap_year_list.count() > 1
    window.ltap_year_list.setCurrentRow(1)
    app.processEvents()

    assert window.ltap_detail_table.rowCount() >= 1
    assert window.ltap_detail_table.item(0, 0) is not None
    assert "Jaar " in window.ltap_year_summary_label.text()


def test_validate_window_ltap_show_all_years_resets_selection(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: QMessageBox.Ok)
    window = ValidateWindow()
    window.show()
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    _align_project_path_then_validate_state(window, fixture, app)
    window._state.set_last_result(ValidateResult(status="valid", summary="ok", details=[]))
    window._state.set_last_project(load_project(fixture))
    app.processEvents()

    window.ltap_year_list.setCurrentRow(2)
    app.processEvents()
    assert "Jaar " in window.ltap_year_summary_label.text()

    window.ltap_show_all_button.click()
    app.processEvents()

    assert window.ltap_year_list.currentRow() == -1
    assert window.ltap_year_summary_label.text() == messages.LTAP_YEAR_SUMMARY_EMPTY


def test_validate_window_ltap_chart_shows_baseline_and_what_if(monkeypatch):
    if not validate_window_module.HAS_QT_CHARTS:
        pytest.skip("QtCharts not available in test environment")
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: QMessageBox.Ok)
    window = ValidateWindow()
    window.show()
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    _align_project_path_then_validate_state(window, fixture, app)
    window._state.set_last_result(ValidateResult(status="valid", summary="ok", details=[]))
    window._state.set_last_project(load_project(fixture))
    app.processEvents()

    chart = window.ltap_chart_view.chart()
    assert chart is not None
    assert len(chart.series()) == 1
    series = chart.series()[0]
    assert len(series.barSets()) == 2


def test_validate_window_ltap_fallback_without_qtcharts(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: QMessageBox.Ok)
    monkeypatch.setattr(validate_window_module, "HAS_QT_CHARTS", False)
    window = validate_window_module.ValidateWindow()
    window.show()
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    _align_project_path_then_validate_state(window, fixture, app)
    window._state.set_last_result(ValidateResult(status="valid", summary="ok", details=[]))
    window._state.set_last_project(load_project(fixture))
    app.processEvents()

    assert window.ltap_chart_view is None
    window.ltap_year_list.setCurrentRow(1)
    app.processEvents()
    assert window.ltap_detail_table.rowCount() >= 1


def test_validate_window_on_demand_panel_toggles(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: QMessageBox.Ok)
    window = ValidateWindow()
    window.show()
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    _align_project_path_then_validate_state(window, fixture, app)
    window._state.set_last_result(ValidateResult(status="valid", summary="ok", details=[]))
    window._state.set_last_project(load_project(fixture))
    app.processEvents()

    window.toggle_compare_button.setChecked(True)
    app.processEvents()
    assert window.compare_group.isVisible() is True

    window.toggle_compare_button.setChecked(False)
    app.processEvents()
    assert window.compare_group.isVisible() is False


def test_validate_window_result_panel_manual_override_sticky(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: QMessageBox.Ok)
    window = ValidateWindow()
    window.show()
    fixture = Path("tests/fixtures/sample_project.rcm.json")
    _align_project_path_then_validate_state(window, fixture, app)
    window._state.set_last_result(ValidateResult(status="valid", summary="ok", details=[]))
    window._state.set_last_project(load_project(fixture))
    app.processEvents()

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
                expected_failures_total=1.0,
                total_downtime_hr_total=1.0,
                total_cost_eur_total=2.0,
                unavailability_pct_total=1.0,
            )
        ],
    )
    window._state.set_last_run(done_result)
    app.processEvents()
    assert window.result_table_group.isVisible() is True
    assert window.pbs_table_group.isVisible() is False

    window.result_focus_pbs_button.click()
    app.processEvents()
    assert window.pbs_table_group.isVisible() is True
    assert window.result_table_group.isVisible() is False

    window._state.set_last_run(done_result)
    app.processEvents()
    assert window.pbs_table_group.isVisible() is True


def test_validate_window_reset_layout_restores_balanced(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: QMessageBox.Ok)
    window = ValidateWindow()
    window.show()

    window.toggle_preview_button.setChecked(False)
    window.toggle_compare_button.setChecked(True)
    app.processEvents()
    assert window.preview_group.isVisible() is False
    assert window.compare_group.isVisible() is True

    window._reset_layout_defaults()
    app.processEvents()
    assert window.preview_group.isVisible() is True
    assert window.compare_group.isVisible() is False


def test_validate_window_layout_preferences_restore(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: QMessageBox.Ok)

    class FakeSettings:
        _store: dict[str, object] = {}

        def __init__(self, *_args, **_kwargs):
            pass

        def value(self, key: str, default=None, type=None):
            value = self._store.get(key, default)
            if type is bool:
                return bool(value)
            if type is str:
                return str(value)
            return value

        def setValue(self, key: str, value):
            self._store[key] = value

    monkeypatch.setattr(validate_window_module, "QSettings", FakeSettings)
    first = validate_window_module.ValidateWindow()
    first.show()
    first.toggle_compare_button.setChecked(True)
    first._save_layout_preferences()

    second = validate_window_module.ValidateWindow()
    second.show()
    second._restore_layout_preferences()
    app.processEvents()
    assert second.compare_group.isVisible() is True
