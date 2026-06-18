"""Slice 79 issue 02 — Beeld-menu view-navigatie (pytest-qt)."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QMessageBox

from rcm_desktop.adapter.results_workspace_state import MODE_LCC
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

from tests.test_desktop_results_workspace_window import _ensure_app


@pytest.fixture
def isolated_navigation_settings(tmp_path):
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path))
    QSettings("rcm2", "desktop").clear()
    yield
    QSettings("rcm2", "desktop").clear()


def _action(window: ResultsWorkspaceWindow, action_id: str):
    return window._workspace_menu.actions_by_id[action_id]


def test_beeld_menu_contains_view_submenus(monkeypatch, isolated_navigation_settings) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    assert "view.output.top_10" not in window._workspace_menu.actions_by_id
    assert "view.input.faalwijzen" in window._workspace_menu.actions_by_id
    assert _action(window, "view.side.input") is not None
    assert _action(window, "view.side.output") is not None


def test_menu_view_action_switches_active_view(monkeypatch, isolated_navigation_settings) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    _action(window, "view.output.lcc_plot").trigger()
    app.processEvents()

    assert window.workspace_state.snapshot().active_view_id == "output.lcc_plot"
    assert _action(window, "view.output.lcc_plot").isChecked() is True


def test_ctrl_2_side_shortcut_keeps_sticky_output_view(
    monkeypatch, qtbot, isolated_navigation_settings
) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    qtbot.addWidget(window)
    window.show()
    app.processEvents()

    window.workspace_state.set_active_view("output.lcc_plot")
    app.processEvents()
    window.workspace_state.set_workspace_side("input")
    app.processEvents()

    qtbot.keyClick(window, Qt.Key.Key_2, Qt.KeyboardModifier.ControlModifier)
    app.processEvents()

    assert window.workspace_state.snapshot().active_view_id == "output.lcc_plot"
    assert window.workspace_state.snapshot().modus == MODE_LCC
