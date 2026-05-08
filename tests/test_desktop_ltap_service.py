from __future__ import annotations

from pathlib import Path

from rcm_core.models import PMTask, TaskType
from rcm_core.persistence import load_project
from rcm_desktop.adapter.ltap_service import build_ltap_view, format_ltap_pm_label


def test_build_ltap_view_baseline_has_year_aggregates_and_details():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    view = build_ltap_view(project)
    assert len(view.years) == int(project.config.lifecycle_years)
    year0 = view.years[0]
    assert year0.task_count > 0
    assert year0.pm_cost_eur >= 0.0
    assert year0.details


def test_build_ltap_view_overlay_shifts_task_to_another_year():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    baseline = build_ltap_view(project)
    shifted = build_ltap_view(project, overlay_anchor_years={"PM-002": 1.0})
    baseline_year0_ids = {d.pm_id for d in baseline.years[0].details}
    shifted_year0_ids = {d.pm_id for d in shifted.years[0].details}
    shifted_year1_ids = {d.pm_id for d in shifted.years[1].details}
    assert "PM-002" in baseline_year0_ids
    assert "PM-002" not in shifted_year0_ids
    assert "PM-002" in shifted_year1_ids


def test_build_ltap_view_marks_svo_and_wet_as_non_shiftable():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    project.pm_tasks["PM-WET"] = PMTask(
        pm_id="PM-WET",
        fm_id="FM-001",
        taak_type=TaskType.IN,
        taak_omschrijving="WET inspectie",
        interval_jaar=1.0,
        cost_eur=100.0,
    )
    view = build_ltap_view(project)
    details = [d for row in view.years for d in row.details if d.pm_id in {"PM-001", "PM-WET"}]
    assert details
    by_id = {d.pm_id: d for d in details}
    assert by_id["PM-001"].shiftable is False
    assert by_id["PM-WET"].shiftable is False


def test_build_ltap_view_can_filter_to_rev_only():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    view = build_ltap_view(project, taak_type_filter="REV")
    details = [detail for row in view.years for detail in row.details]
    assert details
    assert {detail.taak_type for detail in details} == {"REV"}


def test_format_ltap_pm_label_contains_type_group_and_wet_status():
    task = PMTask(
        pm_id="PM-REV",
        fm_id="FM-001",
        taak_type=TaskType.REV,
        taak_omschrijving="WET revisie",
        interval_jaar=1.0,
        cost_eur=100.0,
        task_group_id="TG-01",
    )
    assert format_ltap_pm_label(task) == "PM-REV [REV] [TG] [WET]"
