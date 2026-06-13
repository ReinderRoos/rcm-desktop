"""Slice 91 issue 01 — NB-effectfilter refresh na run-complete."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from rcm_core.persistence import load_project
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
from tests.test_desktop_results_workspace_window import _done_run_for_fixture


def _ensure_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _selectable_klasse_count(combo) -> int:
    model = combo.model()
    count = 0
    for row in range(model.rowCount()):
        item = model.item(row)
        if item is not None and item.flags() & Qt.ItemFlag.ItemIsEnabled:
            count += 1
    return count


def test_nb_effect_filter_becomes_selectable_after_run_complete(monkeypatch) -> None:
    """Na project-load zonder run zijn klassen disabled; na done-run minstens één selecteerbaar."""
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))

    window._state.set_last_project(project)
    app.processEvents()

    assert _selectable_klasse_count(window.nb_effect_filter_combo) == 0

    window._state.set_last_run(_done_run_for_fixture())
    app.processEvents()

    assert _selectable_klasse_count(window.nb_effect_filter_combo) >= 1
