"""Issue 5 — BackgroundRunner (TDD)."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QApplication

from rcm_desktop.adapter.qt.background_runner import BackgroundRunner


def _ensure_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class _EchoWorker(QObject):
    finished = Signal(str)

    @Slot()
    def run(self) -> None:
        self.finished.emit("ok")


def test_background_runner_emits_idle_after_finish(qtbot) -> None:
    _ensure_app()
    owner = QObject()
    states: list[str] = []
    runner = BackgroundRunner(owner, states.append)
    results: list[str] = []

    assert runner.start(_EchoWorker(), on_finished=results.append) is True
    qtbot.waitUntil(lambda: results == ["ok"] and runner.busy is False, timeout=5000)
    assert "busy" in states
    assert states[-1] == "idle"
