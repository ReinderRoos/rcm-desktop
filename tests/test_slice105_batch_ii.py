"""Slice 105 issues 30–33 — AFK batch II tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from rcm_core.persistence import load_project
from rcm_desktop import messages
from rcm_desktop.adapter.fm_edit_commit_service import create_edit_session
from rcm_desktop.adapter.fm_library_fill_service import (
    apply_effect_klassen_from_library,
    apply_rev_tasks_from_library,
    effect_klasse_library_choices,
    rev_task_library_choices,
)

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from rcm_desktop.views.fm_editor_dialog import FmEditorDialog
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow


@pytest.fixture
def sample_project():
    return load_project(Path("tests/fixtures/sample_project.rcm.json"))


@pytest.fixture
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app
    app.processEvents()


def test_effect_klasse_library_choices_lists_project_klassen(sample_project) -> None:
    session = create_edit_session(sample_project)
    edit_current = session.session["edit_current"]
    choices = effect_klasse_library_choices(edit_current)
    assert choices
    assert all("EK-SYS" in label for label, _ in choices)


def test_apply_effect_klassen_from_library_creates_fm_links(sample_project) -> None:
    session = create_edit_session(sample_project)
    edit_current = session.session["edit_current"]
    copied = apply_effect_klassen_from_library(
        edit_current,
        target_fm_id="FM-002",
        selected_klasse_ids=("EK-SYS-01", "EK-SYS-02"),
        existing_link_ids=set(),
    )
    assert len(copied.fm_effect_rows) == 2
    assert all(row["fm_id"] == "FM-002" for row in copied.fm_effect_rows)
    assert copied.pm_effect_rows == ()


def test_apply_rev_tasks_from_library_clones_with_new_pm_ids(sample_project) -> None:
    session = create_edit_session(sample_project)
    edit_current = session.session["edit_current"]
    copied = apply_rev_tasks_from_library(
        edit_current,
        target_fm_id="FM-002",
        selected_pm_ids=("PM-001",),
        existing_pm_ids={"PM-001", "PM-002"},
    )
    assert len(copied.pm_task_rows) == 1
    row = copied.pm_task_rows[0]
    assert row["fm_id"] == "FM-002"
    assert row["pm_id"] not in {"PM-001", "PM-002"}
    assert row["task_group_id"] is None


def test_fill_from_effecten_uses_effect_klasse_library_picker(sample_project, qt_app) -> None:
    _ = qt_app
    dialog = FmEditorDialog(None, project=sample_project, fm_id="FM-002")
    captured: dict[str, str] = {}

    def _capture_pick(_self, *, choices, title, label):
        captured["title"] = title
        captured["label"] = label
        captured["choices"] = choices
        return ["EK-SYS-01"]

    with patch.object(FmEditorDialog, "_pick_library_ids", _capture_pick):
        with patch.object(FmEditorDialog, "_confirm_fill_overwrite", return_value=False):
            dialog._on_fill_from_effecten()

    assert captured["title"] == messages.FM_EDITOR_FILL_FROM_EFFECTEN_TITLE
    assert captured["label"] == messages.FM_EDITOR_FILL_FROM_PICKER_EFFECT_KLASSEN
    assert captured["choices"]
    assert "FM-00" not in captured["choices"][0][0]


def test_fill_from_preventief_uses_rev_library_picker(sample_project, qt_app) -> None:
    _ = qt_app
    dialog = FmEditorDialog(None, project=sample_project, fm_id="FM-002")
    captured: dict[str, str] = {}

    def _capture_pick(_self, *, choices, title, label):
        captured["title"] = title
        captured["label"] = label
        return ["PM-001"]

    with patch.object(FmEditorDialog, "_pick_library_ids", _capture_pick):
        with patch.object(FmEditorDialog, "_confirm_fill_overwrite", return_value=False):
            dialog._on_fill_from_preventief()

    assert captured["title"] == messages.FM_EDITOR_FILL_FROM_PREVENTIEF_TITLE
    assert captured["label"] == messages.FM_EDITOR_FILL_FROM_PICKER_REV_TAKEN


def test_workspace_has_view_tabs_not_dropdown(monkeypatch, qt_app, tmp_path) -> None:
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QMessageBox

    from rcm_desktop.adapter.workspace_view_registry import SIDE_INPUT, SIDE_OUTPUT

    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path))
    QSettings("rcm2", "desktop").clear()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    qt_app.processEvents()

    nav = window._workspace_navigation
    assert not hasattr(nav, "view_combo")
    assert len(nav.view_tab_buttons) == 3
    assert set(nav.side_buttons.keys()) == {SIDE_INPUT, SIDE_OUTPUT}
    assert nav.side_buttons[SIDE_OUTPUT].isChecked() is True
    QSettings("rcm2", "desktop").clear()


def test_view_tabs_switch_detail_page(monkeypatch, qt_app, tmp_path) -> None:
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QMessageBox

    from rcm_desktop.adapter.results_workspace_state import MODE_FM_DETAIL, MODE_LCC

    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path))
    QSettings("rcm2", "desktop").clear()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    qt_app.processEvents()

    nav = window._workspace_navigation
    nav.view_tab_buttons["output.fm_results"].click()
    qt_app.processEvents()
    assert window.workspace_state.snapshot().modus == MODE_FM_DETAIL
    assert window.detail_stack.currentWidget() is window.fm_detail_page

    nav.view_tab_buttons["output.lcc_plot"].click()
    qt_app.processEvents()
    assert window.workspace_state.snapshot().modus == MODE_LCC
    assert window.detail_stack.currentWidget() is window.lcc_page
    QSettings("rcm2", "desktop").clear()
