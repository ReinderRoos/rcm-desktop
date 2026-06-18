"""Slice 105 issue 26 — PBS-sidebar zonder Componenten-titel."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QLabel, QMessageBox

from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
from tests.test_desktop_results_workspace_window import _ensure_app


def test_pbs_sidebar_has_no_componenten_title(monkeypatch) -> None:
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    label_texts = {label.text() for label in window.pbs_sidebar.findChildren(QLabel)}
    assert "Componenten" not in label_texts
    assert window.pbs_filter_input.isVisible() is True
