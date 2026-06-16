"""Semantische statuskleuren voor StatusStrip (slice 102-A contrast)."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QWidget

from rcm_desktop.theme.dp_tokens import (
    DP_BUSY_TEXT,
    DP_ERROR_TEXT,
    DP_SUCCESS_TEXT,
    DP_TEXT_MUTED,
    DP_WARNING_TEXT,
)

_STATUS_LABEL_COLORS: dict[str, str] = {
    "valid": DP_SUCCESS_TEXT,
    "valid_with_warnings": DP_WARNING_TEXT,
    "invalid": DP_ERROR_TEXT,
    "error": DP_ERROR_TEXT,
    "busy": DP_BUSY_TEXT,
    "idle": DP_TEXT_MUTED,
    "done": DP_SUCCESS_TEXT,
}


def semantic_status_color(status: str) -> str:
    return _STATUS_LABEL_COLORS.get(status, DP_TEXT_MUTED)


def semantic_status_label_stylesheet(status: str) -> str:
    color = semantic_status_color(status)
    return f"color: {color}; font-weight: 600;"


def apply_semantic_status_label(label: QLabel, status: str) -> None:
    label.setStyleSheet(semantic_status_label_stylesheet(status))


def apply_status_strip_semantic(status_strip: QWidget, status: str) -> None:
    """Zet dynamische QSS-property voor waarschuwingsachtergrond e.d."""
    status_strip.setProperty("status", status)
    style = status_strip.style()
    if style is not None:
        style.unpolish(status_strip)
        style.polish(status_strip)
    status_strip.update()
