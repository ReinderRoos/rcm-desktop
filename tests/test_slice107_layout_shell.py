"""Slice 107 issue 01 — layout-shell + navigatierail."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QMessageBox

from rcm_desktop.adapter.workspace_view_registry import (
    SIDE_OUTPUT,
    WORKSPACE_VIEW_REGISTRY,
    enabled_views_for_side,
    view_by_id,
)
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


def test_main_splitter_has_pbs_center_column_and_nav_rail(monkeypatch) -> None:
    window = _open_window(monkeypatch)
    assert window.main_splitter.count() == 3
    assert window.pbs_sidebar is window.main_splitter.widget(0)
    assert window.center_column is window.main_splitter.widget(1)
    assert window.nav_rail.objectName() == "WorkspaceNavRail"


def test_chrome_footer_under_center_column_not_pbs_or_rail(monkeypatch) -> None:
    window = _open_window(monkeypatch)
    assert window.chrome_footer.objectName() == "WorkspaceChromeFooter"
    assert window.chrome_footer.parentWidget() is window.center_column


def test_nav_rail_shows_rail_labels_for_output_views(monkeypatch) -> None:
    window = _open_window(monkeypatch)
    window.workspace_state.set_workspace_side(SIDE_OUTPUT)
    app = QApplication.instance()
    app.processEvents()
    for entry in enabled_views_for_side(WORKSPACE_VIEW_REGISTRY, SIDE_OUTPUT):
        button = window._workspace_navigation.view_tab_buttons[entry.view_id]
        expected = entry.rail_label or entry.label
        assert button.text() == expected


def test_nav_rail_side_tabs_stacked_vertically(monkeypatch) -> None:
    window = _open_window(monkeypatch)
    side_buttons = list(window._workspace_navigation.side_buttons.values())
    if len(side_buttons) < 2:
        pytest.skip("need Input and Output side buttons")
    first_y = side_buttons[0].mapTo(window.nav_rail, side_buttons[0].rect().center()).y()
    second_y = side_buttons[1].mapTo(window.nav_rail, side_buttons[1].rect().center()).y()
    assert second_y > first_y
