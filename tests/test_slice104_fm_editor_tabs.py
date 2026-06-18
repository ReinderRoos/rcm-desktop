"""Slice 104 issue 03 — FM-editor Effecten + Preventief tabs commit."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QTableWidgetItem

from rcm_core.incremental_run import IncrementalRunResult
from rcm_core.persistence import load_project
from rcm_desktop.adapter.fm_edit_commit_service import create_edit_session
from rcm_desktop.adapter.fm_edit_scope_loader import load_fm_edit_scope
from rcm_desktop.views.fm_editor_dialog import FmEditorDialog


@pytest.fixture
def sample_project():
    return load_project(Path("tests/fixtures/sample_project.rcm.json"))


@pytest.fixture
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app
    app.processEvents()


def _mock_incremental(monkeypatch) -> None:
    monkeypatch.setattr(
        "rcm_desktop.adapter.fm_edit_commit_service.run_incremental_analysis",
        MagicMock(
            return_value=IncrementalRunResult(
                fm_results={},
                pbs_results={},
                cache_only=False,
                affected_fm_ids=["FM-001"],
                recalculated_fm_count=1,
            )
        ),
    )


def test_fm_editor_add_effect_link_commits(sample_project, qt_app, monkeypatch) -> None:
    _ = qt_app
    _mock_incremental(monkeypatch)
    session = create_edit_session(sample_project)
    dialog = FmEditorDialog(
        None,
        project=sample_project,
        fm_id="FM-001",
        editing_session=session,
    )
    before = len(load_fm_edit_scope(session, "FM-001").fm_effect_rows)
    dialog._add_link_row(dialog._fm_links_table, "FMEL", "FM-001")
    row = dialog._fm_links_table.rowCount() - 1
    dialog._fm_links_table.setItem(row, 1, QTableWidgetItem("EK-SYS-01"))
    dialog._fm_links_table.setItem(row, 2, QTableWidgetItem("0.5"))
    dialog._commit(stay_open=True)
    assert dialog.commit_result is not None
    assert dialog.commit_result.ok is True
    after = load_fm_edit_scope(session, "FM-001").fm_effect_rows
    assert len(after) == before + 1
    dialog.close()


def test_fm_editor_add_pm_task_commits(sample_project, qt_app, monkeypatch) -> None:
    _ = qt_app
    _mock_incremental(monkeypatch)
    session = create_edit_session(sample_project)
    dialog = FmEditorDialog(
        None,
        project=sample_project,
        fm_id="FM-001",
        editing_session=session,
    )
    before = len(load_fm_edit_scope(session, "FM-001").pm_task_rows)
    dialog._add_pm_task_row()
    row = dialog._pm_tasks_table.rowCount() - 1
    dialog._pm_tasks_table.setItem(row, 2, QTableWidgetItem("Slice104 testtaak"))
    dialog._pm_tasks_table.setItem(row, 3, QTableWidgetItem("2.0"))
    dialog._pm_tasks_table.setItem(row, 4, QTableWidgetItem("1500.0"))
    dialog._commit(stay_open=True)
    assert dialog.commit_result is not None
    assert dialog.commit_result.ok is True
    after = load_fm_edit_scope(session, "FM-001").pm_task_rows
    assert len(after) == before + 1
    added = next(r for r in after if r.get("taak_omschrijving") == "Slice104 testtaak")
    assert float(added.get("interval_jaar") or 0) == pytest.approx(2.0)
    dialog.close()


def test_fm_editor_effecten_tab_is_visible_and_has_links_table(
    sample_project, qt_app
) -> None:
    from rcm_desktop import messages

    _ = qt_app
    dialog = FmEditorDialog(None, project=sample_project, fm_id="FM-001")
    effecten_index = next(
        i
        for i in range(dialog._tabs.count())
        if dialog._tabs.tabText(i) == messages.FM_EDITOR_TAB_EFFECTEN
    )
    dialog._tabs.setCurrentIndex(effecten_index)
    dialog.show()
    qt_app.processEvents()
    assert dialog._fm_links_table.isVisible()
    assert dialog._fm_links_table.rowCount() >= 0
    assert dialog._pm_links_table.isVisible()
    assert dialog._effect_table.isVisible()
    dialog.close()


def test_fm_editor_preventief_tab_is_visible_and_has_pm_table(
    sample_project, qt_app
) -> None:
    from rcm_desktop import messages

    _ = qt_app
    dialog = FmEditorDialog(None, project=sample_project, fm_id="FM-001")
    preventief_index = next(
        i
        for i in range(dialog._tabs.count())
        if dialog._tabs.tabText(i) == messages.FM_EDITOR_TAB_PREVENTIEF
    )
    dialog._tabs.setCurrentIndex(preventief_index)
    dialog.show()
    qt_app.processEvents()
    assert dialog._pm_tasks_table.isVisible()
    assert dialog._pm_tasks_table.rowCount() >= 0
    dialog.close()


def test_fm_editor_effect_table_edit_marks_dirty(sample_project, qt_app) -> None:
    _ = qt_app
    dialog = FmEditorDialog(None, project=sample_project, fm_id="FM-001")
    assert dialog._dirty is False
    item = dialog._fm_links_table.item(0, 2)
    assert item is not None
    item.setText("0.99")
    assert dialog._dirty is True
    dialog.close()
