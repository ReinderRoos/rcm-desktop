"""Centraal RCM2 Qt-thema (slice 102-A)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QWidget

from rcm_desktop.theme.dp_tokens import (
    DP_BORDER,
    DP_NAVY,
    DP_ROW_ALT,
    DP_SURFACE,
    DP_TEXT_BODY,
    DP_TEXT_MUTED,
    DP_TEXT_ON_NAVY,
    DP_TEXT_SUBTLE,
    DP_WARNING_BG,
    FONT_BODY,
    FONT_DISPLAY,
)

_THEME_FLAG = "_rcm2_theme_applied"


def enable_stylesheet_background(widget: QWidget) -> None:
    """QWidget achtergrond uit QSS vereist WA_StyledBackground (Qt Windows)."""
    widget.setAttribute(Qt.WA_StyledBackground, True)


def apply_rcm2_palette(app: QApplication) -> None:
    """Leesbaar default-palet voor widgets buiten expliciete QSS-regels."""
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(DP_TEXT_BODY))
    palette.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(DP_ROW_ALT))
    palette.setColor(QPalette.ColorRole.Text, QColor(DP_TEXT_BODY))
    palette.setColor(QPalette.ColorRole.Button, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(DP_TEXT_BODY))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#D6E4F0"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(DP_TEXT_BODY))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(DP_TEXT_SUBTLE))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(DP_TEXT_SUBTLE))
    palette.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(DP_TEXT_SUBTLE)
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(DP_TEXT_SUBTLE)
    )
    app.setPalette(palette)


def load_rcm2_stylesheet() -> str:
    from pathlib import Path

    template = Path(__file__).with_name("rcm2.qss").read_text(encoding="utf-8")
    return template.format(
        dp_navy=DP_NAVY,
        dp_surface=DP_SURFACE,
        dp_text_on_navy=DP_TEXT_ON_NAVY,
        dp_text_body=DP_TEXT_BODY,
        dp_text_muted=DP_TEXT_MUTED,
        dp_text_subtle=DP_TEXT_SUBTLE,
        dp_row_alt=DP_ROW_ALT,
        dp_border=DP_BORDER,
        dp_warning_bg=DP_WARNING_BG,
        font_display=FONT_DISPLAY,
        font_body=FONT_BODY,
    )


def apply_rcm2_theme(app: QApplication) -> None:
    """Voeg RCM2 palet + QSS toe aan app (idempotent)."""
    if getattr(app, _THEME_FLAG, False):
        return
    apply_rcm2_palette(app)
    merged = (app.styleSheet() + "\n" + load_rcm2_stylesheet()).strip()
    app.setStyleSheet(merged)
    setattr(app, _THEME_FLAG, True)


def ensure_rcm2_theme(app: QApplication | None) -> None:
    if app is not None:
        apply_rcm2_theme(app)
