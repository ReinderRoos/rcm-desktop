"""Globale tooltip-presentatie voor de desktop-app (slice 17–18)."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

# Donker neutraal palet: leesbaar op Windows/Qt zonder native tooltip-palet (slice 18).
TOOLTIP_BACKGROUND_COLOR = "#2d333b"
TOOLTIP_FOREGROUND_COLOR = "#f0f3f6"
TOOLTIP_BORDER_COLOR = "#4a5568"

_TOOLTIP_STYLESHEET_FRAGMENT = f"""
QToolTip {{
    padding: 8px;
    font-size: 11pt;
    border-radius: 4px;
    background-color: {TOOLTIP_BACKGROUND_COLOR};
    color: {TOOLTIP_FOREGROUND_COLOR};
    border: 1px solid {TOOLTIP_BORDER_COLOR};
}}
"""


def apply_desktop_tooltip_polish(app: QApplication) -> None:
    """Maakt tooltips sneller zichtbaar waar de Qt-versie dat ondersteunt, en verhoogt leesbaarheid."""
    hints = app.styleHints()
    show_setter = getattr(hints, "setToolTipShowDelay", None)
    if callable(show_setter):
        show_setter(200)
    hide_setter = getattr(hints, "setToolTipHideDelay", None)
    if callable(hide_setter):
        hide_setter(60000)

    merged = (app.styleSheet() + "\n" + _TOOLTIP_STYLESHEET_FRAGMENT).strip()
    app.setStyleSheet(merged)
