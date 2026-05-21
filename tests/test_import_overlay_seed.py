"""Planning overlay seed from import_settings (slice 35 follow-up)."""

from __future__ import annotations

from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.planning_run_materializer import materialize_project_for_overlay


def test_from_import_settings_inactive_when_empty() -> None:
    assert PlanningOverlayState.from_import_settings({}) == PlanningOverlayState.inactive()
    assert PlanningOverlayState.from_import_settings(None) == PlanningOverlayState.inactive()


def test_from_import_settings_active_with_disabled_ids() -> None:
    overlay = PlanningOverlayState.from_import_settings(
        {"aw_disabled_pm_ids": ["FM-A|REV|0", "FM-B|TST|1"]}
    )
    assert overlay.active is True
    assert overlay.disabled_pm_ids == frozenset({"FM-A|REV|0", "FM-B|TST|1"})


def test_materialize_removes_disabled_pm_tasks() -> None:
    from pathlib import Path

    from rcm_core.persistence import load_project

    fixture = Path("tests/fixtures/sample_project.rcm.json")
    project = load_project(fixture)
    if not project.pm_tasks:
        return
    pm_id = next(iter(project.pm_tasks))
    overlay = PlanningOverlayState(
        active=True,
        anchor_years=(),
        disabled_pm_ids=frozenset({pm_id}),
    )
    clone = materialize_project_for_overlay(project, overlay)
    assert pm_id not in clone.pm_tasks
    assert pm_id in project.pm_tasks
