"""Slice 79 issue 01 — venster navigatie end-to-end (pytest-qt)."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QMessageBox

from rcm_desktop import messages
from rcm_desktop.adapter.results_workspace_state import MODE_BIJDRAGEN, MODE_FM_DETAIL, MODE_LCC
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


def test_workspace_has_side_switcher_and_view_dropdown_not_modus_buttons(
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
    assert nav.view_combo.count() == 4


def test_view_dropdown_switches_detail_page(monkeypatch, isolated_navigation_settings):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    combo = window._workspace_navigation.view_combo
    combo.setCurrentIndex(combo.findData("output.fm_results"))
    app.processEvents()
    assert window.workspace_state.snapshot().modus == MODE_FM_DETAIL
    assert window.detail_stack.currentWidget() is window.fm_detail_page

    combo.setCurrentIndex(combo.findData("output.lcc_plot"))
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


def test_ltap_item_enabled_in_dropdown(monkeypatch, isolated_navigation_settings):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    combo = window._workspace_navigation.view_combo
    ltap_index = combo.findText(messages.WORKSPACE_VIEW_LTAP)
    assert ltap_index >= 0
    model_item = combo.model().item(ltap_index)
    assert model_item is not None
    assert model_item.isEnabled() is True


def test_switching_back_to_output_restores_sticky_view(
    monkeypatch, isolated_navigation_settings
):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    combo = window._workspace_navigation.view_combo
    combo.setCurrentIndex(combo.findData("output.lcc_plot"))
    app.processEvents()
    window._workspace_navigation.side_buttons[SIDE_INPUT].click()
    app.processEvents()
    window._workspace_navigation.side_buttons[SIDE_OUTPUT].click()
    app.processEvents()

    assert window.workspace_state.snapshot().active_view_id == "output.lcc_plot"
    assert window.workspace_state.snapshot().modus == MODE_LCC
    assert window.detail_stack.currentWidget() is window.lcc_page
