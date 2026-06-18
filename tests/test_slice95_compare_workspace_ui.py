"""Slice 95 issue 07 — vergelijkingswerkruimte UI (adapter + smoke)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from rcm_desktop.adapter.compare_session_service import load_compare_session
from rcm_desktop.adapter.compare_workspace_presentation_service import (
    build_compare_workspace_view_state,
)
from rcm_desktop.adapter.compare_workspace_table_model import CompareWorkspaceTableModel, ROW_ROLE
from rcm_desktop.views.compare_models_window import CompareModelsWindow


@pytest.fixture
def sample_pair(tmp_path: Path) -> tuple[Path, Path]:
    src = Path("tests/fixtures/sample_project.rcm.json")
    path_a = tmp_path / "a.rcm.json"
    path_b = tmp_path / "b.rcm.json"
    shutil.copy(src, path_a)
    shutil.copy(src, path_b)
    return path_a, path_b


def test_build_compare_workspace_view_state_lists_fm_pairs(sample_pair) -> None:
    path_a, path_b = sample_pair
    session = load_compare_session(path_a, path_b)
    state = build_compare_workspace_view_state(session)
    assert state.label_a == path_a.name
    assert state.label_b == path_b.name
    assert len(state.rows) >= 1
    row = state.rows[0]
    assert row.match_kind == "id"
    assert row.fm_id_a == row.fm_id_b
    assert row.status_label == "beide"


def test_compare_workspace_table_model_exposes_balanced_columns(sample_pair) -> None:
    path_a, path_b = sample_pair
    session = load_compare_session(path_a, path_b)
    state = build_compare_workspace_view_state(session)
    model = CompareWorkspaceTableModel(state.rows)
    assert model.rowCount() == len(state.rows)
    assert model.columnCount() >= 5
    idx = model.index(0, 0)
    assert model.data(idx, Qt.DisplayRole) == "beide"


@pytest.fixture
def unmatched_pair(tmp_path: Path) -> tuple[Path, Path, str]:
    src = Path("tests/fixtures/sample_project.rcm.json")
    data_a = json.loads(src.read_text(encoding="utf-8"))
    data_b = json.loads(src.read_text(encoding="utf-8"))
    only_a_fm_id = "FM-006"
    del data_b["faalwijzes"][only_a_fm_id]
    path_a = tmp_path / "a.rcm.json"
    path_b = tmp_path / "b.rcm.json"
    path_a.write_text(json.dumps(data_a), encoding="utf-8")
    path_b.write_text(json.dumps(data_b), encoding="utf-8")
    return path_a, path_b, only_a_fm_id


def test_unmatched_fm_row_has_detail_values_but_zero_diff_counts(unmatched_pair) -> None:
    path_a, path_b, only_a_fm_id = unmatched_pair
    session = load_compare_session(path_a, path_b)
    state = build_compare_workspace_view_state(session)
    unmatched = next(row for row in state.rows if row.match_kind == "unmatched_a")
    assert unmatched.fm_id_a == only_a_fm_id
    assert unmatched.fm_id_b is None
    assert unmatched.field_diff_count == 0
    assert unmatched.result_diff_count == 0
    assert len(unmatched.field_diffs) >= 1
    assert unmatched.field_diffs[0].value_a is not None
    assert unmatched.field_diffs[0].value_b is None
    assert len(unmatched.result_diffs) >= 1


def test_compare_models_window_populates_detail_for_unmatched_fm(qtbot, unmatched_pair) -> None:
    _ = QApplication.instance()
    path_a, path_b, only_a_fm_id = unmatched_pair
    window = CompareModelsWindow()
    qtbot.addWidget(window)
    window.load_paths(path_a, path_b)

    model = window.table_model()
    unmatched_row_index = next(
        i for i in range(model.rowCount()) if model.data(model.index(i, 0), ROW_ROLE).match_kind == "unmatched_a"
    )
    window._fm_table.selectRow(unmatched_row_index)
    qtbot.wait(10)

    field_model = window._field_table.model()
    result_model = window._result_table.model()
    assert field_model.rowCount() >= 1
    assert result_model.rowCount() >= 1
    assert field_model.data(field_model.index(0, 0), Qt.DisplayRole) == "mttf_jaar"
    assert field_model.data(field_model.index(0, 1), Qt.DisplayRole) not in ("", None)
    assert field_model.data(field_model.index(0, 2), Qt.DisplayRole) == "—"
    assert only_a_fm_id in window._detail_title.text()


def test_compare_models_window_loads_two_projects(qtbot, sample_pair) -> None:

    _ = QApplication.instance()
    path_a, path_b = sample_pair
    window = CompareModelsWindow()
    qtbot.addWidget(window)
    window.load_paths(path_a, path_b)
    assert window.table_model().rowCount() >= 1
    assert window.path_a_label() == path_a.name
    assert window.path_b_label() == path_b.name


def test_workspace_menu_opens_compare_models_window(qtbot) -> None:
    from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

    window = ResultsWorkspaceWindow()
    qtbot.addWidget(window)
    action = window._workspace_menu.actions_by_id["analysis.compare_models"]
    assert action.shortcut().toString() == "Ctrl+Shift+L"
    action.trigger()
    assert window._compare_models_window is not None
    assert window._compare_models_window.isVisible()
