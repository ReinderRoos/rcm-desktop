"""Slice 78 issue 03 — aboutToQuit runner-vangnet."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

from tests.test_desktop_results_workspace_window import _ensure_app


def test_about_to_quit_cancels_background_runners(monkeypatch) -> None:
    _ensure_app()
    app = QApplication.instance()
    assert app is not None

    window = ResultsWorkspaceWindow()
    cancelled: list[str] = []

    def _fake_cancel() -> None:
        cancelled.append("yes")

    monkeypatch.setattr(window, "cancel_background_runners", _fake_cancel)
    app.aboutToQuit.connect(window.cancel_background_runners)

    app.aboutToQuit.emit()
    assert cancelled == ["yes"]


def test_about_to_quit_cancel_is_idempotent_with_close_event(monkeypatch) -> None:
    _ensure_app()
    app = QApplication.instance()
    assert app is not None

    window = ResultsWorkspaceWindow()
    calls = 0

    def _counting_cancel() -> None:
        nonlocal calls
        calls += 1

    monkeypatch.setattr(window, "cancel_background_runners", _counting_cancel)
    app.aboutToQuit.connect(window.cancel_background_runners)

    window.cancel_background_runners()
    app.aboutToQuit.emit()
    assert calls == 2
