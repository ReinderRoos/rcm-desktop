"""View-titel boven detail_zone (slice 107-B, ADR-0021)."""

from __future__ import annotations

from typing import Any


def apply_view_title(window: Any, title: str) -> None:
    if not hasattr(window, "view_title_label"):
        return
    window.view_title_label.setText(title)
    window.view_title_label.setVisible(bool(title))
