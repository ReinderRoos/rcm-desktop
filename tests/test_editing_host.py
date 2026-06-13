"""Slice 46-08 — gedeelde EditingSession + commit-orchestratie via EditingHost."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QApplication

from rcm_core.incremental_run import IncrementalRunResult
from rcm_core.persistence import load_project
from rcm_desktop.adapter.editing_host import EditingHost
from rcm_desktop.adapter.fm_edit_scope_loader import load_fm_edit_scope
from rcm_desktop.views.fm_editor_dialog import FmEditorDialog


@pytest.fixture
def sample_project():
    return load_project(Path("tests/fixtures/sample_project.rcm.json"))


@pytest.fixture(autouse=True)
def _isolate_editing_host():
    from rcm_desktop.adapter.editing_host import reset_editing_host_for_tests

    reset_editing_host_for_tests()
    yield
    reset_editing_host_for_tests()


def test_editing_host_grid_edit_visible_in_fm_scope(sample_project) -> None:
    host = EditingHost()
    grid = host.ensure_grid(sample_project)
    grid.apply_change("FM-001", "failure_type", "aging")
    bundle = load_fm_edit_scope(host.editing_session, "FM-001")
    assert bundle.faalwijze_row["failure_type"] == "aging"


def test_editing_host_commit_grid_triggers_incremental_run(
    sample_project, tmp_path, monkeypatch
) -> None:
    path = tmp_path / "proj.rcm.json"
    path.write_text(Path("tests/fixtures/sample_project.rcm.json").read_text(encoding="utf-8"))

    host = EditingHost()
    grid = host.ensure_grid(sample_project)
    grid.apply_change("FM-001", "mttf_jaar", 44.0)

    mock_inc = MagicMock(
        return_value=IncrementalRunResult(
            fm_results={},
            pbs_results={},
            cache_only=False,
            affected_fm_ids=["FM-001"],
            recalculated_fm_count=1,
        )
    )
    monkeypatch.setattr(
        "rcm_desktop.adapter.fm_edit_commit_service.run_incremental_analysis",
        mock_inc,
    )

    result = host.commit_grid_edits(path=path, save_to_disk=False)
    assert result.ok is True
    assert result.project is not None
    assert result.project.faalwijzes["FM-001"].mttf_jaar == pytest.approx(44.0)
    mock_inc.assert_called_once()
    assert not host.is_grid_dirty()


def test_fm_editor_dialog_reflects_shared_grid_failure_type(
    sample_project, qtbot
) -> None:
    _ = qtbot
    app = QApplication.instance() or QApplication([])
    host = EditingHost()
    grid = host.ensure_grid(sample_project)
    grid.apply_change("FM-001", "failure_type", "aging")

    dialog = FmEditorDialog(
        None,
        project=sample_project,
        fm_id="FM-001",
        editing_session=host.editing_session,
    )
    assert dialog._failure_type.currentData() == "aging"
    dialog.close()
    app.processEvents()
