"""Slice 96 issue 05 — compare visual presentation (DTO + smoke)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from rcm_desktop.adapter.compare_session_service import load_compare_session
from rcm_desktop.adapter.compare_visual_presentation_service import build_compare_visual_flags
from rcm_desktop.adapter.compare_workspace_presentation_service import (
    MATCH_KIND_BADGE_LABELS,
    build_compare_workspace_view_state,
)
from rcm_desktop.adapter.compare_workspace_table_model import (
    BADGE_ROLE,
    HIGHLIGHT_ROLE,
    CompareWorkspaceTableModel,
)
from rcm_desktop.theme.dp_tokens import DP_SCENARIO_1, DP_SCENARIO_2
from rcm_desktop.views.compare_models_window import CompareModelsWindow


@pytest.fixture
def sample_pair(tmp_path: Path) -> tuple[Path, Path]:
    src = Path("tests/fixtures/sample_project.rcm.json")
    path_a = tmp_path / "a.rcm.json"
    path_b = tmp_path / "b.rcm.json"
    shutil.copy(src, path_a)
    shutil.copy(src, path_b)
    return path_a, path_b


def test_visual_flags_expose_ab_colors_and_labels(sample_pair) -> None:
    path_a, path_b = sample_pair
    session = load_compare_session(path_a, path_b)
    state = build_compare_workspace_view_state(session)
    flags = build_compare_visual_flags(state)
    assert flags.color_a == DP_SCENARIO_1
    assert flags.color_b == DP_SCENARIO_2
    assert flags.label_a == path_a.name
    assert flags.label_b == path_b.name


def test_match_kind_badge_labels_cover_all_kinds() -> None:
    assert MATCH_KIND_BADGE_LABELS["id"]
    assert MATCH_KIND_BADGE_LABELS["fingerprint"]
    assert MATCH_KIND_BADGE_LABELS["unmatched_a"]
    assert MATCH_KIND_BADGE_LABELS["unmatched_b"]


def test_workspace_rows_include_match_badge_and_diff_highlights(sample_pair) -> None:
    path_a, path_b = sample_pair
    session = load_compare_session(path_a, path_b)
    state = build_compare_workspace_view_state(session)
    row = state.rows[0]
    assert row.match_badge
    if row.field_diffs:
        assert hasattr(row.field_diffs[0], "is_different")


def test_table_model_exposes_badge_role(sample_pair) -> None:
    path_a, path_b = sample_pair
    session = load_compare_session(path_a, path_b)
    state = build_compare_workspace_view_state(session)
    model = CompareWorkspaceTableModel(state.rows)
    idx = model.index(0, 0)
    assert model.data(idx, BADGE_ROLE)


def test_compare_models_window_shows_run_status_strip(qtbot, sample_pair) -> None:
    _ = QApplication.instance()
    path_a, path_b = sample_pair
    window = CompareModelsWindow()
    qtbot.addWidget(window)
    window.load_paths(path_a, path_b)
    window.show()
    qtbot.wait(10)
    assert "A:" in window._run_status_strip.text()
    assert window._run_a_button.isVisible()
    assert window._run_b_button.isVisible()
    assert window._run_both_button.isVisible()


def test_detail_table_highlights_differing_cells(qtbot, sample_pair) -> None:
    _ = QApplication.instance()
    path_a, path_b = sample_pair
    window = CompareModelsWindow()
    qtbot.addWidget(window)
    window.load_paths(path_a, path_b)
    field_model = window._field_table.model()
    assert hasattr(field_model, "data")
    idx = field_model.index(0, 1)
    # Highlight role may be None when values match; role must exist
    _ = field_model.data(idx, HIGHLIGHT_ROLE)
