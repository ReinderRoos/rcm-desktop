"""Slice 105 issue 23/25/32/33 — Vul van… per sectie-tab in FM-editor."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from rcm_core.persistence import load_project
from rcm_desktop import messages
from rcm_desktop.adapter.fm_edit_commit_service import create_edit_session
from rcm_desktop.adapter.fm_edit_scope_loader import load_fm_edit_scope
from rcm_desktop.adapter.fm_field_copy_service import (
    copy_effect_scope,
    copy_preventief_scope,
)

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QPushButton

from rcm_desktop.views.fm_editor_dialog import FmEditorDialog

@pytest.fixture
def sample_project():
    return load_project(Path("tests/fixtures/sample_project.rcm.json"))


@pytest.fixture
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app
    app.processEvents()


def _tab_index(dialog: FmEditorDialog, label: str) -> int:
    return next(
        i for i in range(dialog._tabs.count()) if dialog._tabs.tabText(i) == label
    )


def _buttons_in_tab(dialog: FmEditorDialog, tab_label: str) -> list[QPushButton]:
    dialog._tabs.setCurrentIndex(_tab_index(dialog, tab_label))
    page = dialog._tabs._stack.currentWidget()
    assert page is not None
    inner = page.widget() if hasattr(page, "widget") else page
    return inner.findChildren(QPushButton)


def test_fm_editor_fill_from_buttons_per_section_only(sample_project, qt_app) -> None:
    _ = qt_app
    dialog = FmEditorDialog(None, project=sample_project, fm_id="FM-002")
    dialog.show()
    qt_app.processEvents()

    assert not hasattr(dialog, "_fill_from_btn")

    basis_labels = {
        b.text() for b in _buttons_in_tab(dialog, messages.FM_EDITOR_TAB_BASIS)
    }
    assert messages.FM_EDITOR_FILL_FROM in basis_labels

    effecten_labels = {
        b.text() for b in _buttons_in_tab(dialog, messages.FM_EDITOR_TAB_EFFECTEN)
    }
    assert messages.FM_EDITOR_FILL_FROM_EFFECTEN in effecten_labels

    preventief_labels = {
        b.text() for b in _buttons_in_tab(dialog, messages.FM_EDITOR_TAB_PREVENTIEF)
    }
    assert messages.FM_EDITOR_FILL_FROM_PREVENTIEF in preventief_labels

    correctief_labels = {
        b.text() for b in _buttons_in_tab(dialog, messages.FM_EDITOR_TAB_CORRECTIEF)
    }
    assert messages.FM_EDITOR_FILL_FROM not in correctief_labels

    resultaten_labels = {
        b.text() for b in _buttons_in_tab(dialog, messages.FM_EDITOR_TAB_RESULTATEN)
    }
    assert messages.FM_EDITOR_FILL_FROM not in resultaten_labels

    dialog.close()


def test_fill_from_effecten_uses_effect_klasse_library_picker(sample_project, qt_app) -> None:
    _ = qt_app
    dialog = FmEditorDialog(None, project=sample_project, fm_id="FM-002")
    captured: dict[str, str] = {}

    def _capture_pick(_self, *, choices, title, label):
        captured["title"] = title
        captured["label"] = label
        return []

    with patch.object(FmEditorDialog, "_pick_library_ids", _capture_pick):
        dialog._on_fill_from_effecten()

    assert captured["title"] == messages.FM_EDITOR_FILL_FROM_EFFECTEN_TITLE
    assert captured["label"] == messages.FM_EDITOR_FILL_FROM_PICKER_EFFECT_KLASSEN
    assert "Bron-faalwijze" != captured["label"]


def test_fill_from_preventief_uses_rev_library_picker(sample_project, qt_app) -> None:
    _ = qt_app
    dialog = FmEditorDialog(None, project=sample_project, fm_id="FM-002")
    captured: dict[str, str] = {}

    def _capture_pick(_self, *, choices, title, label):
        captured["title"] = title
        captured["label"] = label
        return []

    with patch.object(FmEditorDialog, "_pick_library_ids", _capture_pick):
        dialog._on_fill_from_preventief()

    assert captured["title"] == messages.FM_EDITOR_FILL_FROM_PREVENTIEF_TITLE
    assert captured["label"] == messages.FM_EDITOR_FILL_FROM_PICKER_REV_TAKEN
    assert "Bron-faalwijze" != captured["label"]


def test_copy_effect_scope_remaps_fm_id_and_link_ids(sample_project) -> None:
    session = create_edit_session(sample_project)
    source = load_fm_edit_scope(session, "FM-001")
    copied = copy_effect_scope(
        source,
        target_fm_id="FM-002",
        existing_link_ids=set(),
    )
    assert copied.fm_effect_rows
    assert all(row["fm_id"] == "FM-002" for row in copied.fm_effect_rows)
    assert copied.pm_effect_rows == ()


def test_copy_preventief_scope_assigns_new_pm_ids(sample_project) -> None:
    session = create_edit_session(sample_project)
    source = load_fm_edit_scope(session, "FM-001")
    copied = copy_preventief_scope(
        source,
        target_fm_id="FM-002",
        existing_pm_ids={"PM-001", "PM-002"},
    )
    assert copied.pm_task_rows
    for row in copied.pm_task_rows:
        assert row["fm_id"] == "FM-002"
        assert row["task_group_id"] is None
        assert str(row["pm_id"]).startswith("PM-")
