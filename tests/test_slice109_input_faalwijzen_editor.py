"""Slice 109 issue 07 — Input Faalwijzen dubbelklik → editor."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QModelIndex
from PySide6.QtWidgets import QMessageBox

from rcm_desktop.adapter.workspace_navigation_policy import INPUT_FAALWIJZEN_VIEW
from rcm_desktop.views.panels.input_entity_grid_binding import handle_entity_grid_double_click
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
from tests.test_desktop_results_workspace_window import _ensure_app, _inject_run, _three_level_project


def test_input_faalwijzen_double_click_opens_editor(monkeypatch) -> None:
    _ensure_app()
    opened: list[str] = []
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)

    window = ResultsWorkspaceWindow()
    project = _three_level_project()
    window._state.set_last_project(project)
    _inject_run(window, project)
    window.workspace_state.set_active_view(INPUT_FAALWIJZEN_VIEW)
    window._refresh_entity_grid(INPUT_FAALWIJZEN_VIEW)
    monkeypatch.setattr(window, "_open_fm_editor", lambda fm_id: opened.append(fm_id))

    panel = window._entity_grid_panel
    model = panel.table_model()
    assert model is not None
    fm_id = model.row_key_at(0)
    proxy_index = panel._proxy.index(0, 0)
    handle_entity_grid_double_click(window, proxy_index)
    assert opened == [fm_id]
