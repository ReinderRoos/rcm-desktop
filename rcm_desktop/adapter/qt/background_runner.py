"""Shared QThread worker lifecycle for adapter runners (slice 41)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QThread, Slot


class BackgroundRunner:
    """Encapsulates QThread start/cleanup; composed by adapter *Runner classes."""

    def __init__(self, owner: QObject, state_changed: Callable[[str], None]) -> None:
        self._owner = owner
        self._state_changed = state_changed
        self._thread: QThread | None = None
        self._worker: QObject | None = None
        self._busy = False

    @property
    def busy(self) -> bool:
        return self._busy

    def start(
        self,
        worker: QObject,
        *,
        on_finished: Callable[..., None],
        finished_signal: str = "finished",
    ) -> bool:
        if self._busy:
            return False

        self._busy = True
        self._state_changed("busy")

        self._thread = QThread()
        self._worker = worker
        worker.moveToThread(self._thread)
        self._thread.started.connect(worker.run)  # type: ignore[attr-defined]
        signal = getattr(worker, finished_signal)
        signal.connect(on_finished)
        signal.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup)
        self._thread.start()
        return True

    @Slot()
    def _cleanup(self) -> None:
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None
        if self._thread is not None:
            self._thread.deleteLater()
            self._thread = None
        self._busy = False
        self._state_changed("idle")

    def cancel(self) -> None:
        if self._thread is not None and self._thread.isRunning():
            self._thread.quit()
