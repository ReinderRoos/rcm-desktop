"""Tests voor library_explorer_dialog (slice 64 issue 04)."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from rcm_core.models import BibliotheekItem, RCMProject
from rcm_desktop.views.library_explorer_dialog import LibraryExplorerDialog


def _ensure_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_library_explorer_shows_provenance_badge() -> None:
    _ensure_app()
    project = RCMProject(
        bibliotheek={
            "DIST-x": BibliotheekItem(
                bibliotheek_id="DIST-x",
                categorie="faalmodel",
                omschrijving="Lekkage",
                waarde="MTTF=10",
                bron="3 bron(nen)",
                provenance=[
                    {"source_id": "a", "netwerkschakel": "H", "fm_id": "FM-1", "relative_path": "a"},
                    {"source_id": "b", "netwerkschakel": "R", "fm_id": "FM-2", "relative_path": "b"},
                    {"source_id": "c", "netwerkschakel": "G", "fm_id": "FM-3", "relative_path": "c"},
                ],
            )
        }
    )
    dialog = LibraryExplorerDialog(project)
    assert dialog.row_count() == 1
    assert "3 bronnen" in dialog.bron_badge_at(0)
