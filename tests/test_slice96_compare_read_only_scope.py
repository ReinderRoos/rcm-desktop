"""Slice 96 issue 01 — read-only compare scope (no uniformeren UI)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from rcm_desktop.adapter.compare_session_service import load_compare_session
from rcm_desktop.adapter.compare_workspace_presentation_service import (
    build_compare_workspace_view_state,
)
from rcm_desktop.views.compare_models_window import CompareModelsWindow


@pytest.fixture
def sample_pair(tmp_path: Path) -> tuple[Path, Path]:
    src = Path("tests/fixtures/sample_project.rcm.json")
    path_a = tmp_path / "a.rcm.json"
    path_b = tmp_path / "b.rcm.json"
    shutil.copy(src, path_a)
    shutil.copy(src, path_b)
    return path_a, path_b


def test_compare_session_unchanged_after_read_only_scope(sample_pair) -> None:
    path_a, path_b = sample_pair
    session = load_compare_session(path_a, path_b)
    assert session.project_a is not None
    assert session.project_b is not None


def test_build_compare_workspace_view_state_after_read_only_scope(sample_pair) -> None:
    path_a, path_b = sample_pair
    session = load_compare_session(path_a, path_b)
    state = build_compare_workspace_view_state(session)
    assert len(state.rows) >= 1


def test_compare_models_window_hides_normalization_widgets(qtbot, sample_pair) -> None:
    _ = QApplication.instance()
    path_a, path_b = sample_pair
    window = CompareModelsWindow()
    qtbot.addWidget(window)
    window.load_paths(path_a, path_b)

    assert not hasattr(window, "_normalization_table") or not window._normalization_table.isVisible()
    assert not hasattr(window, "_normalization_apply_button") or not window._normalization_apply_button.isVisible()
    assert not hasattr(window, "_normalization_rollback_button") or not window._normalization_rollback_button.isVisible()
    assert window.table_model().rowCount() >= 1
