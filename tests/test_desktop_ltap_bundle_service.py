from __future__ import annotations

from pathlib import Path

from rcm_core.models import PMTask, TaskType
from rcm_core.persistence import load_project
from rcm_desktop.adapter.ltap_bundle_service import apply_bundle_shift


def test_apply_bundle_shift_updates_overlay_anchor():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    result = apply_bundle_shift(
        project,
        current_overlay_anchor_years={},
        pm_ids=["PM-002"],
        shift_years=2,
    )
    assert result.ok is True
    assert result.overlay_anchor_years["PM-002"] == 2.0


def test_apply_bundle_shift_is_all_or_nothing_for_unknown_pm_id():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    result = apply_bundle_shift(
        project,
        current_overlay_anchor_years={"PM-002": 1.0},
        pm_ids=["PM-002", "PM-NOPE"],
        shift_years=2,
    )
    assert result.ok is False
    assert result.overlay_anchor_years == {"PM-002": 1.0}
    assert "onbekende PM-taak" in (result.error or "")


def test_apply_bundle_shift_blocks_svo_and_wet():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    project.pm_tasks["PM-WET"] = PMTask(
        pm_id="PM-WET",
        fm_id="FM-001",
        taak_type=TaskType.IN,
        taak_omschrijving="WET inspectie",
        interval_jaar=1.0,
        cost_eur=100.0,
    )
    svo_result = apply_bundle_shift(
        project,
        current_overlay_anchor_years={},
        pm_ids=["PM-001"],
        shift_years=1,
    )
    wet_result = apply_bundle_shift(
        project,
        current_overlay_anchor_years={},
        pm_ids=["PM-WET"],
        shift_years=1,
    )
    assert svo_result.ok is False
    assert wet_result.ok is False


def test_apply_bundle_shift_rejects_all_when_one_selected_task_not_shiftable():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    result = apply_bundle_shift(
        project,
        current_overlay_anchor_years={"PM-002": 0.0},
        pm_ids=["PM-002", "PM-001"],
        shift_years=1,
    )
    assert result.ok is False
    assert result.overlay_anchor_years == {"PM-002": 0.0}
