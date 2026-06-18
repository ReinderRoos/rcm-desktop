"""Slice 53 issue 07 — gate voor legacy PR7-A cleanup in workspace-view."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_WINDOW = ROOT / "rcm_desktop" / "views" / "results_workspace_window.py"
VALIDATE_WINDOW = ROOT / "rcm_desktop" / "views" / "validate_window.py"


def test_issue07_workspace_view_has_no_scenario_split_legacy_references() -> None:
    source = WORKSPACE_WINDOW.read_text(encoding="utf-8").lower()
    assert "workspace_split_layout" not in source
    assert "scenario-run" not in source
    assert "scenario-slot" not in source


def test_issue07_compare_runner_stays_in_legacy_validate_window_only() -> None:
    workspace_source = WORKSPACE_WINDOW.read_text(encoding="utf-8")
    validate_source = VALIDATE_WINDOW.read_text(encoding="utf-8")
    assert "CompareRunner" not in workspace_source
    assert "CompareRunner" in validate_source


def test_issue07_workspace_has_slice56_ab_compare_path() -> None:
    """Slice 56 issue 06 — nieuw A/B-pad in werkruimte, geen legacy compare-runner."""
    workspace_source = WORKSPACE_WINDOW.read_text(encoding="utf-8")
    assert "_compare_slots" in workspace_source
    assert "CompareRunRunner" in workspace_source
    assert "CompareRunConfig" in workspace_source
    assert "compare_mode" in workspace_source
    assert "CompareRunner" not in workspace_source
