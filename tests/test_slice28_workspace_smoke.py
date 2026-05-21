"""Optionele pytest-qt smoke voor slice 28 werkruimte-LCC."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PySide6.QtCore import Qt

from rcm_core.models import RCMProject
from rcm_desktop.adapter.results_workspace_state import MODE_LCC
from rcm_desktop.adapter.run_service import run as run_single
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow


pytest.importorskip("pytestqt")


@pytest.fixture
def workspace(qtbot):
    window = ResultsWorkspaceWindow()
    qtbot.addWidget(window)
    window.show()
    return window


def test_lcc_whatif_toggle_and_reset_smoke(workspace, qtbot):
    path = Path("tests/fixtures/one_fm_planning.rcm.json")
    project = RCMProject.from_dict(json.loads(path.read_text(encoding="utf-8")))
    rr = run_single(project, path, full_recompute=True, parallel=False)
    assert rr.status == "done"
    workspace._state.set_last_project(project)
    workspace._state.set_last_run(rr)
    workspace.workspace_state.set_modus(MODE_LCC)
    qtbot.wait(50)
    assert workspace.lcc_chart_widget.buckets()
    workspace.lcc_whatif_button.setChecked(True)
    qtbot.wait(50)
    assert workspace.workspace_state.snapshot().planning_overlay.active
    workspace.lcc_reset_overlay_button.click()
    qtbot.wait(50)
    assert not workspace.workspace_state.snapshot().planning_overlay.active
