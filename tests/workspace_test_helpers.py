"""Testhelpers voor legacy modus → view-id navigatie (slice 79)."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

LEGACY_MODUS_VIEW_ID = {
    "bijdragen": "output.top_10",
    "lcc": "output.lcc_plot",
    "fm_detail": "output.fm_results",
}


def switch_workspace_modus(
    window: ResultsWorkspaceWindow,
    modus: str,
    app: QApplication,
) -> None:
    view_id = LEGACY_MODUS_VIEW_ID[modus]
    window.workspace_state.set_active_view(view_id)
    app.processEvents()
