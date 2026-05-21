from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from rcm_desktop.desktop_tooltip import (
    TOOLTIP_BACKGROUND_COLOR,
    TOOLTIP_BORDER_COLOR,
    TOOLTIP_FOREGROUND_COLOR,
    apply_desktop_tooltip_polish,
)


def test_apply_desktop_tooltip_polish_appends_tooltip_stylesheet():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    apply_desktop_tooltip_polish(app)
    sheet = app.styleSheet()
    assert "QToolTip" in sheet
    assert "background-color" in sheet
    assert "border:" in sheet or "border :" in sheet
    assert TOOLTIP_BACKGROUND_COLOR in sheet
    assert TOOLTIP_FOREGROUND_COLOR in sheet
    assert TOOLTIP_BORDER_COLOR in sheet
