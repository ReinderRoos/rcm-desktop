"""Regression: Top-10-subbar label mag geen los top-level venster worden (slice 105)."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QMessageBox

from rcm_desktop.adapter.results_workspace_state import METRIC_KOSTEN, MODE_LCC
from rcm_desktop.views.panels.workspace_toolbar_sync import relocate_fm_metric_chrome
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
from tests.test_desktop_results_workspace_window import _ensure_app


def test_top10_subbar_label_stays_parented_after_metric_chrome_relocate(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    label = window.top10_subbar_label
    assert label.parent() is window.top10_subbar
    assert label.isWindow() is False

    relocate_fm_metric_chrome(window, target="top10")
    app.processEvents()
    assert label.parent() is window.top10_subbar
    assert label.isWindow() is False

    relocate_fm_metric_chrome(window, target="fm")
    app.processEvents()
    assert label.isWindow() is False


def test_whatif_toggle_expands_bar_and_switches_to_kosten(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    window.workspace_state.set_active_view("output.lcc_plot")
    app.processEvents()

    window.lcc_whatif_button.setChecked(True)
    app.processEvents()
    snap = window.workspace_state.snapshot()
    assert snap.planning_overlay.active is True
    assert snap.lcc_whatif_collapsed_in_lcc is False
    assert snap.metric == METRIC_KOSTEN
    assert window.lcc_whatif_content.isVisible() is True
    assert window._lcc_filter_checks["rev"].isVisible() is True
