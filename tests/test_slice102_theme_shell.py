"""Slice 102-A — Delta Pi theme + werkruimte-shell."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QMessageBox

from rcm_desktop import messages
from rcm_desktop.adapter.results_workspace_state import MODE_BIJDRAGEN, MODE_FM_DETAIL, MODE_LCC
from rcm_desktop.theme.rcm2_theme import apply_rcm2_theme, load_rcm2_stylesheet
from rcm_desktop.theme.semantic_styles import semantic_status_color
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
from tests.test_desktop_results_workspace_window import _ensure_app


def test_rcm2_stylesheet_contains_delta_pi_tokens() -> None:
    qss = load_rcm2_stylesheet()
    assert "#232851" in qss
    assert "AppTopbar" in qss
    assert "StatusStrip" in qss
    assert "WorkspaceFooter" in qss
    assert "QHeaderView::section" in qss
    assert "WorkspaceSubNav" in qss
    assert "WorkspaceToolbar" in qss
    assert "QComboBox QLineEdit" in qss
    assert "QMenuBar" in qss


def test_apply_rcm2_theme_is_idempotent() -> None:
    app = _ensure_app()
    apply_rcm2_theme(app)
    first = app.styleSheet()
    apply_rcm2_theme(app)
    assert app.styleSheet() == first
    assert "AppTopbar" in first


def test_apply_rcm2_theme_sets_readable_palette() -> None:
    app = _ensure_app()
    apply_rcm2_theme(app)
    palette = app.palette()
    assert palette.color(QPalette.ColorRole.WindowText).name().upper() == "#212121"
    assert palette.color(QPalette.ColorRole.Text).name().upper() == "#212121"


def test_semantic_status_colors_use_readable_tokens() -> None:
    assert semantic_status_color("idle") == "#424242"
    assert semantic_status_color("valid_with_warnings") == "#B45309"
    assert semantic_status_color("valid") == "#1B5E20"


def test_shell_widgets_use_stylesheet_background(monkeypatch) -> None:
    app = _ensure_app()
    apply_rcm2_theme(app)
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    for widget in (window.app_topbar, window.status_strip, window.chrome_footer):
        assert widget.testAttribute(Qt.WA_StyledBackground)


def test_workspace_shell_widgets_present(monkeypatch) -> None:
    app = _ensure_app()
    apply_rcm2_theme(app)
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    assert window.app_topbar.objectName() == "AppTopbar"
    assert window.app_logo_org.text() == messages.WORKSPACE_APP_WORDMARK_ORG
    assert window.app_logo_product.text() == messages.WORKSPACE_APP_WORDMARK_PRODUCT
    assert window.status_strip.objectName() == "StatusStrip"
    assert window.status_strip.property("status") == "idle"
    assert window.validate_status_label.objectName() == "ValidateStatusLabel"
    assert window.statusBar() is not None
    assert window.statusBar().objectName() == "WorkspaceFooter"


def test_kpi_not_active_until_navigated(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    assert window.workspace_state.snapshot().active_view_id != "output.kpi_overview"
    assert window.detail_stack.currentWidget() is not window.kpi_overview_page


def test_workspace_footer_show_message(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    window.show_workspace_footer_message("Testmelding slice 102", 1000)
    app.processEvents()
    assert window.statusBar().currentMessage() == "Testmelding slice 102"
