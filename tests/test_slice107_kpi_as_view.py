"""Slice 107 issue 02 — KPI als Output-view."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QMessageBox

from rcm_desktop.adapter.results_workspace_state import MODE_KPI_OVERVIEW, SIDE_OUTPUT
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
from tests.test_desktop_results_workspace_window import _ensure_app


def _open_window(monkeypatch) -> ResultsWorkspaceWindow:
    from rcm_desktop.theme.rcm2_theme import apply_rcm2_theme

    app = _ensure_app()
    apply_rcm2_theme(app)
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()
    return window


def test_ctrl_k_navigates_to_kpi_view(monkeypatch) -> None:
    window = _open_window(monkeypatch)
    action = window._workspace_menu.actions_by_id["view.output.kpi_overview"]
    action.trigger()
    QApplication.instance().processEvents()
    snap = window.workspace_state.snapshot()
    assert snap.active_view_id == "output.kpi_overview"
    assert snap.workspace_side == SIDE_OUTPUT
    assert snap.modus == MODE_KPI_OVERVIEW
    assert window.detail_stack.currentWidget() is window.kpi_overview_page


def test_no_kpi_collapsed_state_in_snapshot() -> None:
    from rcm_desktop.adapter.results_workspace_state import WorkspaceStateSnapshot

    assert "kpi_collapsed_in_lcc" not in WorkspaceStateSnapshot.__dataclass_fields__
