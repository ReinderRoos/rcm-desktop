"""LCC what-if bar visibility + run-menu shortcuts (pytest-qt)."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from rcm_desktop.adapter.results_workspace_state import (
    METRIC_NIET_BESCHIKBAARHEID,
    MODE_LCC,
)
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

from tests.test_desktop_results_workspace_window import _ensure_app
from tests.workspace_test_helpers import switch_workspace_modus


def _action(window: ResultsWorkspaceWindow, action_id: str):
    return window._workspace_menu.actions_by_id[action_id]


def test_whatif_bar_visible_at_nb_metric_without_pm_filters(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    switch_workspace_modus(window, MODE_LCC, app)
    app.processEvents()
    window.workspace_state.set_lcc_whatif_collapsed_in_lcc(False)
    app.processEvents()
    assert window.workspace_state.snapshot().metric == METRIC_NIET_BESCHIKBAARHEID
    assert window.lcc_filter_bar.isVisible() is True
    assert window.lcc_whatif_button.isVisible() is True
    assert window._lcc_filter_checks["cm"].isVisible() is False
    assert window.meekoppel_panel.isVisible() is False


def test_meekoppel_visible_after_whatif_activated(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    switch_workspace_modus(window, MODE_LCC, app)
    app.processEvents()
    window.lcc_whatif_button.setChecked(True)
    app.processEvents()
    assert window.meekoppel_panel.isVisible() is True


def test_whatif_menu_toggle_from_top_level(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    switch_workspace_modus(window, MODE_LCC, app)
    app.processEvents()
    whatif_action = _action(window, "whatif.toggle")
    assert whatif_action.shortcut().toString() == "Ctrl+Shift+W"
    assert window.lcc_whatif_button.isChecked() is False
    whatif_action.trigger()
    app.processEvents()
    assert window.lcc_whatif_button.isChecked() is True
