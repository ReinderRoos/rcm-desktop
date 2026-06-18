"""Slice 107-B issue 01 — view-titel in layout-shell."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QMessageBox

from rcm_desktop import messages
from rcm_desktop.adapter.workspace_view_registry import SIDE_OUTPUT
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
from tests.test_desktop_results_workspace_window import _ensure_app


def _open_window(monkeypatch) -> ResultsWorkspaceWindow:
    apply = __import__(
        "rcm_desktop.theme.rcm2_theme", fromlist=["apply_rcm2_theme"]
    ).apply_rcm2_theme
    app = _ensure_app()
    apply(app)
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()
    return window


def test_view_title_above_detail_zone(monkeypatch) -> None:
    window = _open_window(monkeypatch)
    assert window.view_title_label.objectName() == "WorkspaceViewTitle"
    layout = window.center_column.layout()
    assert layout.indexOf(window.view_title_label) < layout.indexOf(window.detail_zone)


def test_view_title_shows_registry_label_on_view_switch(monkeypatch) -> None:
    window = _open_window(monkeypatch)
    window.workspace_state.set_workspace_side(SIDE_OUTPUT)
    window.workspace_state.set_active_view("output.fm_results")
    app = __import__("PySide6.QtWidgets", fromlist=["QApplication"]).QApplication.instance()
    app.processEvents()
    assert window.view_title_label.text() == messages.WORKSPACE_VIEW_TOP_BIJDRAGEN
    assert window.view_title_label.isVisible()


def test_footer_context_label_hidden(monkeypatch) -> None:
    window = _open_window(monkeypatch)
    assert window.chrome_footer_context_label.isVisible() is False
