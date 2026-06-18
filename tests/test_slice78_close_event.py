"""Slice 78 issue 02 — closeEvent grid-dirty + busy-cancel."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QMessageBox

from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

from tests.test_desktop_results_workspace_window import _ensure_app


class _FakeCloseEvent(QCloseEvent):
    def __init__(self) -> None:
        super().__init__()
        self._accepted = False
        self._ignored = False

    def accept(self) -> None:
        self._accepted = True
        super().accept()

    def ignore(self) -> None:
        self._ignored = True
        super().ignore()


def test_close_event_proceeds_when_clean(monkeypatch) -> None:
    _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    monkeypatch.setattr(window._editing_host, "is_grid_dirty", lambda: False)
    monkeypatch.setattr(window, "_any_runner_busy", lambda: False)

    event = _FakeCloseEvent()
    window.closeEvent(event)
    assert event._accepted is True


def test_close_event_ignores_when_grid_dirty_cancelled(monkeypatch) -> None:
    _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    monkeypatch.setattr(window._editing_host, "is_grid_dirty", lambda: True)
    monkeypatch.setattr(
        "rcm_desktop.views.results_workspace_window.resolve_grid_dirty_before_editor",
        lambda *_a, **_k: "cancel",
    )

    event = _FakeCloseEvent()
    window.closeEvent(event)
    assert event._ignored is True


def test_close_event_cancels_runners_when_busy_confirmed(monkeypatch) -> None:
    _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    monkeypatch.setattr(window._editing_host, "is_grid_dirty", lambda: False)
    busy_state = {"busy": True}

    cancelled: list[str] = []

    def _fake_confirm() -> bool:
        return True

    def _fake_cancel() -> None:
        cancelled.append("yes")
        busy_state["busy"] = False

    monkeypatch.setattr(window, "_any_runner_busy", lambda: busy_state["busy"])
    monkeypatch.setattr(window, "_confirm_busy_shutdown", _fake_confirm)
    monkeypatch.setattr(window, "cancel_background_runners", _fake_cancel)

    event = _FakeCloseEvent()
    window.closeEvent(event)
    assert cancelled == ["yes"]
    assert event._accepted is True
