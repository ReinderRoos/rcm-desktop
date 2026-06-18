"""Slice 109 issue 08 — Top bijdragen editor-paden."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QModelIndex
from PySide6.QtWidgets import QMessageBox

from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
from tests.test_desktop_results_workspace_window import _ensure_app, _inject_run, _three_level_project
from tests.workspace_test_helpers import switch_workspace_modus


def test_topx_double_click_opens_inspector_not_editor(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    _inject_run(window, project)
    switch_workspace_modus(window, "fm_detail", app)
    app.processEvents()

    editor_calls: list[str] = []
    monkeypatch.setattr(window, "_open_fm_editor", lambda fm_id: editor_calls.append(fm_id))

    sel = window.fm_table_view.selectionModel()
    assert sel is not None
    idx = window.fm_table_view.model().index(0, 0)
    window.fm_table_view.doubleClicked.emit(idx)
    app.processEvents()

    assert editor_calls == []
    assert window.workspace_state.snapshot().fm_inspector_mode is True


def test_inspector_bewerken_opens_editor(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = _three_level_project()
    window._state.set_last_project(project)
    _inject_run(window, project)
    switch_workspace_modus(window, "fm_detail", app)
    app.processEvents()

    editor_calls: list[str] = []
    monkeypatch.setattr(window, "_open_fm_editor", lambda fm_id: editor_calls.append(fm_id))

    model = window.fm_table_view.model()
    assert model is not None and model.rowCount() >= 1
    fm_id = str(model.data(model.index(0, 0), __import__(
        "rcm_desktop.adapter.fm_results_table_model", fromlist=["RAW_ROLE"]
    ).RAW_ROLE))
    window.workspace_state.open_fm_inspector_mode(fm_id)
    window._refresh_fm_inspector(fm_id)
    app.processEvents()
    window.fm_inspector_edit_button.click()
    app.processEvents()

    assert editor_calls == [fm_id]
