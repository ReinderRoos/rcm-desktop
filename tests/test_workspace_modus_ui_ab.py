"""Slice A/B: batch-knop alleen in FM-detail; Tijdsplot start met ingeklapte panelen."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QMessageBox

from rcm_desktop.adapter.results_workspace_state import (
    MODE_BIJDRAGEN,
    MODE_FM_DETAIL,
    MODE_LCC,
    ResultsWorkspaceState,
)
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

from tests.test_desktop_results_workspace_window import _ensure_app


def test_batch_faalwijzen_button_only_visible_in_fm_detail(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    assert window.batch_faalwijzen_button.isVisible() is False

    window.modus_buttons[MODE_FM_DETAIL].click()
    app.processEvents()
    assert window.batch_faalwijzen_button.isVisible() is True

    window.modus_buttons[MODE_LCC].click()
    app.processEvents()
    assert window.batch_faalwijzen_button.isVisible() is False

    window.modus_buttons[MODE_BIJDRAGEN].click()
    app.processEvents()
    assert window.batch_faalwijzen_button.isVisible() is False


def test_entering_lcc_modus_collapses_kpi_meekoppel_and_whatif():
    state = ResultsWorkspaceState()
    state.set_kpi_collapsed_in_lcc(False)
    state.set_meekoppel_collapsed_in_lcc(False)
    state.set_lcc_whatif_collapsed_in_lcc(False)

    state.set_modus(MODE_LCC)
    snap = state.snapshot()

    assert snap.modus == MODE_LCC
    assert snap.kpi_collapsed_in_lcc is True
    assert snap.meekoppel_collapsed_in_lcc is True
    assert snap.lcc_whatif_collapsed_in_lcc is True


def test_lcc_modus_starts_with_collapsed_panels(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    window.modus_buttons[MODE_LCC].click()
    app.processEvents()

    assert window.kpi_table_view.isVisible() is False
    assert window.lcc_whatif_content.isVisible() is False
    assert window.meekoppel_content.isVisible() is False
