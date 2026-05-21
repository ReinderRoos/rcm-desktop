from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from rcm_desktop.app_state import AppState


def _ensure_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_set_last_project_and_run_emits_single_project_run_signal() -> None:
    _ensure_app()
    state = AppState()
    pr_count: list[int] = []
    pc_count: list[int] = []
    rc_count: list[int] = []

    state.project_run_view_changed.connect(lambda: pr_count.append(1))
    state.project_changed.connect(lambda _p: pc_count.append(1))
    state.run_changed.connect(lambda _r: rc_count.append(1))

    state.set_last_project_and_run(None, None)

    assert len(pr_count) == 1
    assert len(pc_count) == 0
    assert len(rc_count) == 0
