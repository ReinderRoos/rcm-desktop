from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_WINDOW = ROOT / "rcm_desktop" / "views" / "results_workspace_window.py"
VALIDATE_WINDOW = ROOT / "rcm_desktop" / "views" / "validate_window.py"


def test_workspace_view_has_no_scenario_split_legacy_references() -> None:
    source = WORKSPACE_WINDOW.read_text(encoding="utf-8").lower()
    assert "workspace_split_layout" not in source
    assert "scenario-run" not in source
    assert "scenario-slot" not in source


def test_compare_runner_stays_in_legacy_validate_window_only() -> None:
    workspace_source = WORKSPACE_WINDOW.read_text(encoding="utf-8")
    validate_source = VALIDATE_WINDOW.read_text(encoding="utf-8")
    assert "CompareRunner" not in workspace_source
    assert "CompareRunner" in validate_source
