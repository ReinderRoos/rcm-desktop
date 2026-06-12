"""Slice 76 issue 02 — QMenuBar-binding, knop-migratie en state-sync (pytest-qt)."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from rcm_desktop import messages
from rcm_desktop.adapter.results_workspace_state import MODE_LCC
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

from tests.test_desktop_results_workspace_window import _ensure_app


def _menu_labels(window: ResultsWorkspaceWindow) -> list[str]:
    return [action.text() for action in window.menuBar().actions()]


def _action(window: ResultsWorkspaceWindow, action_id: str):
    return window._workspace_menu.actions_by_id[action_id]


def test_workspace_menu_bar_has_top_level_menus(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()
    assert _menu_labels(window) == [
        messages.WORKSPACE_MENU_FILE,
        messages.WORKSPACE_MENU_VIEW,
        messages.WORKSPACE_MENU_RUN,
        messages.WORKSPACE_MENU_ANALYSIS,
    ]


def test_migrated_toolbar_buttons_removed(monkeypatch) -> None:
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    for attr in (
        "pbs_toggle_button",
        "kpi_collapse_button",
        "batch_faalwijzen_button",
        "model_settings_button",
        "generate_report_button",
        "open_isograph_button",
    ):
        assert not hasattr(window, attr), attr


def test_pbs_menu_toggle_hides_sidebar(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    pbs_action = _action(window, "view.pbs_tree_visible")
    assert pbs_action.isChecked() is True
    assert window.pbs_sidebar.isVisible() is True

    pbs_action.setChecked(False)
    app.processEvents()
    assert window.pbs_sidebar.isVisible() is False
    assert pbs_action.isChecked() is False

    pbs_action.setChecked(True)
    app.processEvents()
    assert window.pbs_sidebar.isVisible() is True


def test_kpi_menu_toggle_collapses_panel(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    window.workspace_state.set_modus(MODE_LCC)
    app.processEvents()

    kpi_action = _action(window, "view.kpi_overview_visible")
    assert kpi_action.isChecked() is False
    assert window.workspace_state.snapshot().kpi_collapsed_in_lcc is True
    assert window.kpi_table_view.isVisible() is False

    kpi_action.setChecked(True)
    app.processEvents()
    assert window.workspace_state.snapshot().kpi_collapsed_in_lcc is False
    assert window.kpi_table_view.isVisible() is True


def test_ctrl_b_shortcut_toggles_pbs_sidebar(monkeypatch, qtbot) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    qtbot.addWidget(window)
    window.show()
    app.processEvents()

    assert window.pbs_sidebar.isVisible() is True
    qtbot.keyClick(window, Qt.Key.Key_B, Qt.KeyboardModifier.ControlModifier)
    app.processEvents()
    assert window.pbs_sidebar.isVisible() is False
