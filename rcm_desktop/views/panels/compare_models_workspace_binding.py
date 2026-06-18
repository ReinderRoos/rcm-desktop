"""Vergelijkingswerkruimte openen vanuit de resultatenwerkruimte (slice 95)."""

from __future__ import annotations

from typing import Any

from rcm_desktop.views.compare_models_window import CompareModelsWindow


def open_compare_models_window(window: Any) -> None:
    compare_window = getattr(window, "_compare_models_window", None)
    if compare_window is None:
        compare_window = CompareModelsWindow(window)
        window._compare_models_window = compare_window
    compare_window.show()
    compare_window.raise_()
    compare_window.activateWindow()
