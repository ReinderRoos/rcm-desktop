"""Slice 89 issue 03 — generieke dirty-dialoogteksten + contextafhankelijke annuleerknop."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QMessageBox

from rcm_core.persistence import load_project
from rcm_desktop import messages
from rcm_desktop.adapter.editing_host import EditingHost
from rcm_desktop.views.grid_dirty_guard import resolve_grid_dirty_before_editor

from tests.test_desktop_results_workspace_window import _ensure_app


@pytest.fixture
def dirty_host():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    host = EditingHost()
    host.ensure_grid(project)
    session = host.editing_session
    rows = copy.deepcopy(session.session["edit_current"]["pm_tasks"])
    rows[0]["taak_omschrijving"] = "dirty voor dialoogtest"
    session.apply_entity_rows("pm_tasks", rows)
    assert host.is_grid_dirty() is True
    return host


def _capture_dialog(monkeypatch) -> dict:
    captured: dict = {}

    def fake_exec(self):
        captured["title"] = self.windowTitle()
        captured["text"] = self.text()
        captured["buttons"] = [b.text() for b in self.buttons()]
        return 0

    monkeypatch.setattr(QMessageBox, "exec", fake_exec)
    return captured


def test_dialog_uses_generic_input_change_texts(dirty_host, monkeypatch) -> None:
    _ensure_app()
    captured = _capture_dialog(monkeypatch)

    outcome = resolve_grid_dirty_before_editor(None, dirty_host)
    assert outcome == "cancel"

    assert captured["title"] == "Onopgeslagen invoerwijzigingen"
    assert "faalwijzen-grid" not in captured["text"]
    assert "invoerwijzigingen" in captured["text"]
    assert "Invoer opslaan" in captured["buttons"]
    assert "Invoer verwerpen" in captured["buttons"]


def test_cancel_button_label_for_editor_context(dirty_host, monkeypatch) -> None:
    _ensure_app()
    captured = _capture_dialog(monkeypatch)

    resolve_grid_dirty_before_editor(None, dirty_host, context="editor")
    assert "Editor annuleren" in captured["buttons"]
    assert "Niet afsluiten" not in captured["buttons"]


def test_cancel_button_label_for_shutdown_context(dirty_host, monkeypatch) -> None:
    _ensure_app()
    captured = _capture_dialog(monkeypatch)

    resolve_grid_dirty_before_editor(None, dirty_host, context="shutdown")
    assert "Niet afsluiten" in captured["buttons"]
    assert "Editor annuleren" not in captured["buttons"]


def test_dialog_texts_come_from_message_catalog() -> None:
    assert messages.GRID_DIRTY_GUARD_TITLE == "Onopgeslagen invoerwijzigingen"
    assert messages.GRID_DIRTY_SAVE == "Invoer opslaan"
    assert messages.GRID_DIRTY_DISCARD == "Invoer verwerpen"
    assert messages.GRID_DIRTY_CANCEL_EDITOR == "Editor annuleren"
    assert messages.GRID_DIRTY_CANCEL_SHUTDOWN == "Niet afsluiten"
