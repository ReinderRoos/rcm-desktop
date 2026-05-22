"""Unit tests — meekoppel apply bridge (slice 39)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from rcm_core.models import RCMProject, TaskType

from rcm_desktop.adapter.meekoppel_apply_service import (
    apply_meekoppel_suggestion,
    preview_meekoppel_suggestion,
)
from rcm_desktop.adapter.meekoppelkansen_discovery_service import (
    MeekoppelSuggestion,
    discover_meekoppelkansen,
)
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
                    "bouwdeel_naam": "",
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


def _suggestion(project: RCMProject) -> MeekoppelSuggestion:
    rows = discover_meekoppelkansen(project, window_years=5)
    assert len(rows) == 1
    return rows[0]


def test_preview_default_shifts_later_task_to_earlier_year():
    project = _pair_project()
    overlay = PlanningOverlayState.inactive().begin_what_if()
    sug = _suggestion(project)
    prev = preview_meekoppel_suggestion(project, overlay, sug, anchor="earlier")
    assert prev.blocked_reason is None
    assert prev.shifted_pm_id == "PM-14"
    assert prev.shift_years == -4
    assert prev.from_year == 14
    assert prev.to_year == 10


def test_preview_later_anchor_shifts_earlier_task():
    project = _pair_project()
    overlay = PlanningOverlayState.inactive().begin_what_if()
    sug = _suggestion(project)
    prev = preview_meekoppel_suggestion(project, overlay, sug, anchor="later")
    assert prev.shifted_pm_id == "PM-10"
    assert prev.shift_years == 4
    assert prev.to_year == 14


def test_preview_respects_existing_anchor_offset():
    project = _pair_project()
    overlay = (
        PlanningOverlayState.inactive()
        .begin_what_if()
        .with_anchor_years({"PM-14": 2.0})
    )
    sug = _suggestion(project)
    prev = preview_meekoppel_suggestion(project, overlay, sug, anchor="earlier")
    assert prev.from_year == 16
    assert prev.shift_years == -6
    assert prev.to_year == 10


def test_apply_success_updates_overlay():
    project = _pair_project()
    overlay = PlanningOverlayState.inactive().begin_what_if()
    sug = _suggestion(project)
    result = apply_meekoppel_suggestion(project, overlay, sug, anchor="earlier")
    assert result.error is None
    assert result.overlay.anchor_years_dict().get("PM-14") == -4.0
    assert result.overlay.change_count() == 1


def test_apply_blocked_for_svo():
    project = _pair_project()
    project.pm_tasks["PM-SVO"] = replace(
        project.pm_tasks["PM-10"],
        pm_id="PM-SVO",
        taak_type=TaskType.SVO,
        interval_jaar=10.0,
    )
    overlay = PlanningOverlayState.inactive().begin_what_if()
    sug = MeekoppelSuggestion(
        element_naam="Pomp",
        pm_a="PM-10",
        pm_b="PM-SVO",
        pbs_a="PBS-A",
        pbs_b="PBS-A",
        jaar_a=10,
        jaar_b=10,
        jaar_delta=0,
        reden="test",
    )
    prev = preview_meekoppel_suggestion(project, overlay, sug)
    assert prev.blocked_reason is not None
    applied = apply_meekoppel_suggestion(project, overlay, sug)
    assert applied.error is not None
    assert applied.overlay == overlay
