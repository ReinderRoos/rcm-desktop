"""Unit tests — meekoppel display helpers (UX v2)."""

from __future__ import annotations

from rcm_core.config import RCMConfig
from rcm_core.models import Faalwijze, PBSItem, RCMProject, PMTask, TaskType

from rcm_desktop.adapter.meekoppel_apply_service import MeekoppelShiftMove
from rcm_desktop.adapter.meekoppel_display_service import (
    due_calendar_year,
    format_preview_move_line,
    location_group_tooltip,
    pm_task_label,
    rev_task_tooltip_line,
)
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop import messages
from rcm_desktop.adapter.meekoppelkansen_discovery_service import discover_meekoppel_locations


def _project() -> RCMProject:
    return RCMProject(
        config=RCMConfig(lifecycle_years=40.0, modeljaar=2026),
        pbs_items={"P1": PBSItem("P1", "obj", "el", "Pump")},
        faalwijzes={"FM-1": Faalwijze("FM-1", "P1", "F1", "Leak")},
        pm_tasks={
            "PM-A": PMTask(
                "PM-A",
                "FM-1",
                TaskType.REV,
                interval_jaar=5.0,
                taak_omschrijving="Vervang pakking",
            ),
            "PM-B": PMTask("PM-B", "FM-1", TaskType.REV, interval_jaar=6.0),
        },
    )


def test_due_calendar_year_uses_modeljaar():
    assert due_calendar_year(2026, 5) == 2031


def test_pm_task_label_prefers_omschrijving():
    project = _project()
    assert pm_task_label(project, "PM-A") == "Vervang pakking"
    assert pm_task_label(project, "PM-B") == "PM-B"


def test_location_group_tooltip_lists_tasks_baseline_only_without_overlay():
    project = _project()
    group = discover_meekoppel_locations(project, window_years=2)[0]
    tip = location_group_tooltip(project, group, overlay=None)
    assert "PBS-id: P1" in tip
    assert "baseline jaar 5" in tip
    assert "effectief" not in tip


def test_location_group_tooltip_shows_baseline_and_effective_when_overlay_active():
    project = _project()
    group = discover_meekoppel_locations(project, window_years=2)[0]
    overlay = (
        PlanningOverlayState.inactive()
        .begin_what_if()
        .with_anchor_years({"PM-A": 3.0})
    )
    tip = location_group_tooltip(project, group, overlay=overlay)
    assert "baseline jaar 5" in tip
    assert "effectief jaar 8" in tip


def test_rev_task_tooltip_line_baseline_only():
    project = _project()
    from rcm_desktop.adapter.meekoppelkansen_discovery_service import MeekoppelRevTask

    line = rev_task_tooltip_line(
        project,
        MeekoppelRevTask(pm_id="PM-A", pbs_id="P1", due_jaar=5),
        overlay=None,
    )
    assert "baseline jaar 5" in line
    assert "effectief" not in line


def test_format_preview_move_line_includes_calendar_years():
    project = _project()
    line = format_preview_move_line(
        project,
        2026,
        MeekoppelShiftMove(pm_id="PM-A", from_year=5, to_year=6, shift_years=1),
    )
    assert "Vervang pakking" in line
    assert "2031" in line
    assert "2032" in line
