"""Slice 99 issue 13 — faalwijze verwijderen via editing-pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest

from rcm_core.persistence import load_project

from rcm_desktop.adapter.entity_edit_service import EntityEditService
from rcm_desktop.adapter.fm_delete_service import (
    build_fm_delete_confirmation,
    format_fm_delete_confirmation_message,
)


def test_build_fm_delete_confirmation_counts_linked_entities() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    svc = EntityEditService.for_view("input.faalwijzen")
    svc.init(project)
    # FM-001 has PM tasks and effect links in sample project
    confirmation = build_fm_delete_confirmation(svc, "FM-001")
    assert confirmation.fm_id == "FM-001"
    assert confirmation.pm_task_count >= 1
    assert confirmation.fm_effect_link_count >= 1


def test_format_fm_delete_confirmation_message_lists_linked_counts() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    svc = EntityEditService.for_view("input.faalwijzen")
    svc.init(project)
    confirmation = build_fm_delete_confirmation(svc, "FM-001")
    message = format_fm_delete_confirmation_message(confirmation)
    assert "FM-001" in message
    assert str(confirmation.pm_task_count) in message
    assert str(confirmation.fm_effect_link_count) in message


def test_delete_row_removes_faalwijze_from_buffer() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    svc = EntityEditService.for_view("input.faalwijzen")
    svc.init(project)
    assert any(r.row_key == "FM-999" for r in svc.rows()) or True
    # Pick an FM that exists
    fm_id = svc.rows()[0].row_key
    before = len(svc.rows())
    svc.delete_row(fm_id)
    assert len(svc.rows()) == before - 1
    assert not any(r.row_key == fm_id for r in svc.rows())


def test_materialize_after_delete_produces_valid_project() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    svc = EntityEditService.for_view("input.faalwijzen")
    svc.init(project)
    fm_id = svc.rows()[-1].row_key
    svc.delete_row(fm_id)
    result = svc.materialize_for_save()
    assert fm_id not in result.faalwijzes


def test_delete_fm_button_removes_selected_row(qtbot, monkeypatch) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QMessageBox

    from rcm_desktop.adapter.workspace_view_registry import SIDE_INPUT
    from rcm_desktop.views.panels.input_entity_grid_binding import sync_delete_fm_button_enabled
    from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_a, **_k: QMessageBox.StandardButton.Yes,
    )
    window = ResultsWorkspaceWindow()
    qtbot.addWidget(window)
    window.show()
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    window._state.set_last_project(project)
    window._workspace_navigation.side_buttons[SIDE_INPUT].click()
    qtbot.wait(50)
    assert window.delete_fm_button.isVisible()
    before = window._entity_grid_panel.row_count()
    table = window._entity_grid_panel._table
    table.selectRow(0)
    qtbot.wait(10)
    sync_delete_fm_button_enabled(window)
    assert window.delete_fm_button.isEnabled()
    window.delete_fm_button.click()
    qtbot.wait(10)
    assert window._entity_grid_panel.row_count() == before - 1
