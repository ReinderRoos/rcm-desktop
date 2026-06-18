"""Slice 105 issue 01 — FM-editor tabs robuust op smalle vensters."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from rcm_core.persistence import load_project
from rcm_desktop import messages
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


def test_fm_editor_all_tab_labels_visible_in_tab_bar(sample_project, qt_app) -> None:
    _ = qt_app
    dialog = FmEditorDialog(None, project=sample_project, fm_id="FM-001")
    dialog.resize(720, 480)
    dialog.show()
    qt_app.processEvents()

    tab_bar = dialog._tabs.tabBar()
    assert not tab_bar.usesScrollButtons()
    for label in (
        messages.FM_EDITOR_TAB_BASIS,
        messages.FM_EDITOR_TAB_EFFECTEN,
        messages.FM_EDITOR_TAB_CORRECTIEF,
        messages.FM_EDITOR_TAB_PREVENTIEF,
        messages.FM_EDITOR_TAB_RESULTATEN,
    ):
        index = _tab_index(dialog, label)
        rect = tab_bar.tabRect(index)
        assert rect.width() > 0, label
        assert rect.height() > 0, label
        assert dialog._tabs.tabText(index) == label

    dialog.close()


def test_fm_editor_all_tabs_reachable_at_minimum_height(sample_project, qt_app) -> None:
    _ = qt_app
    dialog = FmEditorDialog(None, project=sample_project, fm_id="FM-001")
    dialog.resize(720, 480)
    dialog.show()
    qt_app.processEvents()

    tab_bar = dialog._tabs.tabBar()
    assert tab_bar.isVisible()
    assert dialog._tabs.count() >= 3

    for label in (
        messages.FM_EDITOR_TAB_BASIS,
        messages.FM_EDITOR_TAB_EFFECTEN,
        messages.FM_EDITOR_TAB_PREVENTIEF,
    ):
        index = _tab_index(dialog, label)
        assert tab_bar.tabRect(index).height() > 0
        dialog._tabs.setCurrentIndex(index)
        qt_app.processEvents()
        assert dialog._tabs.currentIndex() == index

    dialog.close()


def test_fm_editor_effecten_and_preventief_tables_visible_after_resize(
    sample_project, qt_app
) -> None:
    _ = qt_app
    dialog = FmEditorDialog(None, project=sample_project, fm_id="FM-001")
    dialog.resize(720, 480)
    dialog.show()
    qt_app.processEvents()

    dialog._tabs.setCurrentIndex(_tab_index(dialog, messages.FM_EDITOR_TAB_EFFECTEN))
    qt_app.processEvents()
    assert dialog._fm_links_table.isVisible()
    assert dialog._effect_table.isVisible()

    dialog._tabs.setCurrentIndex(_tab_index(dialog, messages.FM_EDITOR_TAB_PREVENTIEF))
    qt_app.processEvents()
    assert dialog._pm_tasks_table.isVisible()

    dialog.close()
