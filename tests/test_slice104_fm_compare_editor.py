"""Slice 104 issue 06 — FM-editor opent via dubbelklik in compare-kolommen."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from rcm_desktop.adapter.compare_slot_state import COMPARE_SLOT_A, COMPARE_SLOT_B
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

from tests.test_desktop_results_workspace_window import (
    _ensure_app,
    _inject_run,
    _three_level_project,
)
from tests.workspace_test_helpers import switch_workspace_modus


def _enter_fm_compare(window: ResultsWorkspaceWindow, app: QApplication) -> None:
    from rcm_desktop.adapter.validate_service import ValidateResult

    project = _three_level_project()
    window._state.set_last_project(project)
    window._state.set_last_result(ValidateResult(status="valid", summary="ok", details=[]))
    _inject_run(window, project)
    window.extra_scenario_button.click()
    app.processEvents()
    _inject_run(window, project)
    app.processEvents()
    window.compare_toggle_button.setChecked(True)
    app.processEvents()
    switch_workspace_modus(window, "fm_detail", app)
    app.processEvents()
    assert window.workspace_state.snapshot().compare_mode is True
    assert window._compare_slots.has(COMPARE_SLOT_A)
    assert window._compare_slots.has(COMPARE_SLOT_B)


def test_fm_compare_double_click_opens_editor(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "warning", lambda *_a, **_k: QMessageBox.Ok)
    opened: list[str] = []

    class _FakeDialog:
        DialogCode = QDialog.DialogCode

        def __init__(self, _parent, **kwargs) -> None:
            self.commit_result = None
            self._fm_id = kwargs.get("fm_id", "")

        def exec(self):
            opened.append(self._fm_id)
            return QDialog.DialogCode.Rejected

    monkeypatch.setattr(
        "rcm_desktop.views.results_workspace_window.FmEditorDialog",
        _FakeDialog,
    )

    window = ResultsWorkspaceWindow()
    window.show()
    _enter_fm_compare(window, app)

    table = window._fm_compare_col_a["table"]
    model = table.model()
    assert model is not None and model.rowCount() >= 1
    idx = model.index(0, 1)
    expected_fm_id = str(model.data(model.index(0, 0), Qt.DisplayRole))
    table.doubleClicked.emit(idx)
    app.processEvents()
    assert opened == [expected_fm_id]


def test_fm_compare_double_click_uses_fm_id_column_not_clicked_column(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "warning", lambda *_a, **_k: QMessageBox.Ok)
    opened: list[str] = []

    class _FakeDialog:
        DialogCode = QDialog.DialogCode

        def __init__(self, _parent, **kwargs) -> None:
            self.commit_result = None
            self._fm_id = kwargs.get("fm_id", "")

        def exec(self):
            opened.append(self._fm_id)
            return QDialog.DialogCode.Rejected

    monkeypatch.setattr(
        "rcm_desktop.views.results_workspace_window.FmEditorDialog",
        _FakeDialog,
    )

    window = ResultsWorkspaceWindow()
    window.show()
    _enter_fm_compare(window, app)

    table = window._fm_compare_col_b["table"]
    model = table.model()
    assert model is not None and model.rowCount() >= 1
    metric_col = max(0, model.columnCount() - 1)
    idx = model.index(0, metric_col)
    expected_fm_id = str(model.data(model.index(0, 0), Qt.DisplayRole))
    table.doubleClicked.emit(idx)
    app.processEvents()
    assert opened == [expected_fm_id]
