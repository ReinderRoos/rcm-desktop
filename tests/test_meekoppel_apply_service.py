"""Unit tests — meekoppel apply bridge (slice 39/40)."""

from __future__ import annotations

from dataclasses import replace

from rcm_core.models import RCMProject, TaskType

from rcm_desktop.adapter.meekoppel_apply_service import (
    apply_meekoppel_location,
    preview_meekoppel_location,
)
from rcm_desktop.adapter.meekoppelkansen_discovery_service import discover_meekoppel_locations
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState


def _pair_project() -> RCMProject:
    return RCMProject.from_dict(
        {
            "config": {"lifecycle_years": 40.0, "modeljaar": 2026},
            "pbs_items": {
                "PBS-A": {
                    "pbs_id": "PBS-A",
                    "object_naam": "X",
                    "element_naam": "Pomp",
                    "bouwdeel_naam": "Locatie A",
                    "component_naam": "",
                    "multiplicity": 1,
                    "bouwjaar": 2000,
                },
            },
            "functies": {},
            "faalwijzes": {
                "FM-A": {
                    "fm_id": "FM-A",
                    "pbs_id": "PBS-A",
                    "functie_id": "F1",
                    "faalwijze_omschrijving": "A",
                    "failure_type": "random",
                    "mttf_jaar": 10.0,
                    "downtime_per_failure": {"value": 1.0, "unit": "uur"},
                },
            },
            "pm_tasks": {
                "PM-10": {
                    "pm_id": "PM-10",
                    "fm_id": "FM-A",
                    "taak_type": "REV",
                    "interval_jaar": 10.0,
                },
                "PM-14": {
                    "pm_id": "PM-14",
                    "fm_id": "FM-A",
                    "taak_type": "REV",
                    "interval_jaar": 14.0,
                },
            },
            "task_groups": {},
            "effect_klassen": {},
            "fm_effect_links": {},
            "pm_effect_links": {},
            "bibliotheek": {},
        }
    )


def _location_group(project: RCMProject):
    groups = discover_meekoppel_locations(project, window_years=5)
    assert len(groups) == 1
    return groups[0]


def test_preview_default_later_shifts_earlier_task():
    project = _pair_project()
    overlay = PlanningOverlayState.inactive().begin_what_if()
    group = _location_group(project)
    prev = preview_meekoppel_location(project, overlay, group)
    assert prev.blocked_reason is None
    assert prev.target_year == 14
    assert len(prev.moves) == 1
    assert prev.moves[0].pm_id == "PM-10"
    assert prev.moves[0].shift_years == 4


def test_preview_earlier_anchor_shifts_later_task():
    project = _pair_project()
    overlay = PlanningOverlayState.inactive().begin_what_if()
    group = _location_group(project)
    prev = preview_meekoppel_location(project, overlay, group, anchor="earlier")
    assert prev.target_year == 10
    assert prev.moves[0].pm_id == "PM-14"
    assert prev.moves[0].shift_years == -4


def test_preview_respects_existing_anchor_offset():
    project = _pair_project()
    overlay = (
        PlanningOverlayState.inactive()
        .begin_what_if()
        .with_anchor_years({"PM-14": 2.0})
    )
    group = _location_group(project)
    prev = preview_meekoppel_location(project, overlay, group, anchor="earlier")
    assert prev.moves[0].from_year == 16
    assert prev.moves[0].shift_years == -6
    assert prev.moves[0].to_year == 10


def test_apply_default_later_updates_overlay():
    project = _pair_project()
    overlay = PlanningOverlayState.inactive().begin_what_if()
    group = _location_group(project)
    result = apply_meekoppel_location(project, overlay, group)
    assert result.error is None
    assert result.overlay.anchor_years_dict().get("PM-10") == 4.0
    assert result.overlay.change_count() == 1


def test_apply_earlier_anchor_shifts_all():
    project = _pair_project()
    overlay = PlanningOverlayState.inactive().begin_what_if()
    group = _location_group(project)
    result = apply_meekoppel_location(project, overlay, group, anchor="earlier")
    assert result.error is None
    assert result.overlay.anchor_years_dict().get("PM-14") == -4.0


def test_apply_blocked_for_svo():
    project = _pair_project()
    overlay = PlanningOverlayState.inactive().begin_what_if()
    group = _location_group(project)
    project.pm_tasks["PM-10"] = replace(
        project.pm_tasks["PM-10"],
        taak_type=TaskType.SVO,
    )
    prev = preview_meekoppel_location(project, overlay, group)
    assert prev.blocked_reason is not None
    applied = apply_meekoppel_location(project, overlay, group)
    assert applied.error is not None
    assert applied.overlay == overlay
