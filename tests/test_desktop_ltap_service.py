from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from rcm_core.models import PMTask, TaskType
from rcm_core.persistence import load_project
from rcm_desktop.adapter.ltap_service import (
    PM_COST_DISPLAY_NORMAL,
    PM_COST_DISPLAY_ZERO_EXPECTED,
    PM_COST_DISPLAY_ZERO_MISSING,
    build_ltap_pm_display_seq_map,
    build_ltap_view,
    classify_pm_cost_display,
    format_ltap_pm_label,
    resolve_ltap_fm_cell,
)


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


def test_format_ltap_pm_label_pattern_with_optional_suffixes():
    task = PMTask(
        pm_id="PM-REV",
        fm_id="FM-001",
        taak_type=TaskType.REV,
        taak_omschrijving="WET revisie",
        interval_jaar=1.0,
        cost_eur=100.0,
        task_group_id="TG-01",
    )
    assert format_ltap_pm_label(task, 7) == "PM_REV_WET_TG_07"


def test_format_ltap_pm_label_without_wet_or_tg():
    task = PMTask(
        pm_id="z",
        fm_id="FM-001",
        taak_type=TaskType.IN,
        taak_omschrijving="routine",
        interval_jaar=1.0,
        cost_eur=1.0,
    )
    assert format_ltap_pm_label(task, 3) == "PM_IN_03"


def test_pm_display_sequence_is_global_sorted_pm_id():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    seq = build_ltap_pm_display_seq_map(project)
    assert seq["PM-001"] == 1
    assert seq["PM-002"] == 2
    assert seq["PM-008"] == len(project.pm_tasks)


def test_rev_filter_keeps_same_display_sequence_as_full_project():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    full = build_ltap_view(project)
    rev_only = build_ltap_view(project, taak_type_filter="REV")
    full_pm002 = next(d for row in full.years for d in row.details if d.pm_id == "PM-002")
    rev_pm002 = next(d for row in rev_only.years for d in row.details if d.pm_id == "PM-002")
    assert full_pm002.pm_label == rev_pm002.pm_label == "PM_REV_02"


def test_fixture_mixed_task_types_get_distinct_compact_labels():
    """SVO, IN+TG, REV etc. share one global sequence map (sorted pm_id)."""
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    view = build_ltap_view(project)
    by_pm = {d.pm_id: d.pm_label for row in view.years for d in row.details}
    assert by_pm["PM-001"] == "PM_SVO_01"
    assert by_pm["PM-002"] == "PM_REV_02"
    assert by_pm["PM-003"] == "PM_IN_TG_03"
    assert by_pm["PM-006"] == "PM_TST_06"


def test_task_group_member_zero_cost_marked_expected():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    task = project.pm_tasks["PM-004"]
    assert float(task.cost_eur) == 0.0
    assert task.task_group_id == "TG-001"
    assert classify_pm_cost_display(task, project) == PM_COST_DISPLAY_ZERO_EXPECTED


def test_standalone_zero_cost_without_rationale_marked_missing():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    task = PMTask(
        pm_id="PM-ZERO",
        fm_id="FM-001",
        taak_type=TaskType.IN,
        taak_omschrijving="missende kosten",
        interval_jaar=1.0,
        cost_eur=0.0,
    )
    project.pm_tasks["PM-ZERO"] = task
    assert classify_pm_cost_display(task, project) == PM_COST_DISPLAY_ZERO_MISSING


def test_zero_cost_with_aanname_marked_expected():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    task = PMTask(
        pm_id="PM-AANN",
        fm_id="FM-001",
        taak_type=TaskType.IN,
        taak_omschrijving="",
        interval_jaar=1.0,
        cost_eur=0.0,
        aanname_kosten="nul door afspraak X",
    )
    project.pm_tasks["PM-AANN"] = task
    assert classify_pm_cost_display(task, project) == PM_COST_DISPLAY_ZERO_EXPECTED


def test_positive_cost_always_normal():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    task = project.pm_tasks["PM-001"]
    assert classify_pm_cost_display(task, project) == PM_COST_DISPLAY_NORMAL


def test_detail_rows_carry_cost_display_metadata():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    view = build_ltap_view(project)
    pm004 = next(d for row in view.years for d in row.details if d.pm_id == "PM-004")
    assert pm004.pm_cost_display == PM_COST_DISPLAY_ZERO_EXPECTED


def test_resolve_ltap_fm_cell_shows_description_and_id_tooltip():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    display, tip = resolve_ltap_fm_cell(fm_id="FM-001", project=project)
    assert display == "Impellerslijtage"
    assert "FM-001" in tip


def test_resolve_ltap_fm_cell_unknown_fm():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    display, tip = resolve_ltap_fm_cell(fm_id="FM-UNKNOWN", project=project)
    assert display == "FM-UNKNOWN"
    assert "Onbekende faalwijze" in tip


def test_resolve_ltap_fm_cell_empty_description_fallback():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    base = project.faalwijzes["FM-001"]
    project.faalwijzes["FM-EMPTY"] = replace(base, fm_id="FM-EMPTY", faalwijze_omschrijving="  ")
    display, tip = resolve_ltap_fm_cell(fm_id="FM-EMPTY", project=project)
    assert display == "FM-EMPTY"
    assert "Geen omschrijving" in tip


def test_ltap_detail_carries_fm_display_fields():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    view = build_ltap_view(project)
    d = next(det for row in view.years for det in row.details if det.pm_id == "PM-001")
    assert d.fm_display == "Impellerslijtage"
    assert "FM-001" in d.fm_tooltip
