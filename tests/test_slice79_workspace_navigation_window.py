"""Slice 79 issue 01 — venster navigatie end-to-end (pytest-qt)."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QMessageBox

from rcm_desktop import messages
from rcm_desktop.adapter.results_workspace_state import MODE_FM_DETAIL, MODE_LCC
from rcm_desktop.adapter.workspace_view_registry import SIDE_INPUT, SIDE_OUTPUT
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow


def _ensure_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def isolated_navigation_settings(tmp_path):
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path))
    QSettings("rcm2", "desktop").clear()
    yield
    QSettings("rcm2", "desktop").clear()


def test_workspace_has_side_switcher_and_view_tabs_not_modus_buttons(
    monkeypatch, isolated_navigation_settings
):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    assert not hasattr(window, "modus_buttons")
    nav = window._workspace_navigation
    assert set(nav.side_buttons.keys()) == {SIDE_INPUT, SIDE_OUTPUT}
    assert nav.side_buttons[SIDE_OUTPUT].isChecked() is True
    assert len(nav.view_tab_buttons) == 3


def test_view_tabs_switch_detail_page(monkeypatch, isolated_navigation_settings):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    nav = window._workspace_navigation
    nav.view_tab_buttons["output.fm_results"].click()
    app.processEvents()
    assert window.workspace_state.snapshot().modus == MODE_FM_DETAIL
    assert window.detail_stack.currentWidget() is window.fm_detail_page

    nav.view_tab_buttons["output.lcc_plot"].click()
    app.processEvents()
    assert window.workspace_state.snapshot().modus == MODE_LCC
    assert window.detail_stack.currentWidget() is window.lcc_page


def test_input_side_shows_entity_grid_page(monkeypatch, isolated_navigation_settings):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    window._workspace_navigation.side_buttons[SIDE_INPUT].click()
    app.processEvents()

    assert window.workspace_state.snapshot().workspace_side == SIDE_INPUT
    assert window.workspace_state.snapshot().active_view_id == "input.faalwijzen"
    assert window.detail_stack.currentWidget() is window.input_entity_grid_page


def test_ltap_tab_enabled(monkeypatch, isolated_navigation_settings):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    ltap_button = window._workspace_navigation.view_tab_buttons["output.ltap"]
    assert ltap_button.text() == messages.WORKSPACE_VIEW_LTAP
    assert ltap_button.isEnabled() is True


def test_switching_back_to_output_restores_sticky_view(
    monkeypatch, isolated_navigation_settings
):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    nav = window._workspace_navigation
    nav.view_tab_buttons["output.lcc_plot"].click()
    app.processEvents()
    window._workspace_navigation.side_buttons[SIDE_INPUT].click()
    app.processEvents()
    window._workspace_navigation.side_buttons[SIDE_OUTPUT].click()
    app.processEvents()

    assert window.workspace_state.snapshot().active_view_id == "output.lcc_plot"
    assert window.workspace_state.snapshot().modus == MODE_LCC
    assert window.detail_stack.currentWidget() is window.lcc_page
