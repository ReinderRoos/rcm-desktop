"""Slice 105 issue 04 — werkruimte content-marges."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QMessageBox

from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
from tests.test_desktop_results_workspace_window import _ensure_app


def test_detail_zone_has_content_margins(monkeypatch) -> None:
    _ = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    layout = window.detail_zone.layout()
    assert layout is not None
    left, top, right, bottom = (
        layout.contentsMargins().left(),
        layout.contentsMargins().top(),
        layout.contentsMargins().right(),
        layout.contentsMargins().bottom(),
    )
    assert left >= 12
    assert top >= 8
    assert right >= 12
    assert bottom >= 12
