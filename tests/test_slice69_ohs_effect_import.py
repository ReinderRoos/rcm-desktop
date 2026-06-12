"""Slice 69 — OHS cause–effect import alignment (golden + regressie)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rcm_core.incremental_run import run_incremental_analysis
from rcm_core.isograph_pm_import_rules import (
    CauseEffectAssignmentRow,
    ScheduledTaskRow,
    audit_effect_ids_vs_fm_links,
    parse_effect_ids,
    pm_effect_fractie,
    resolve_pm_tasks,
    resolve_pm_tasks_for_scope,
)
from rcm_desktop.adapter.fm_verification_service import build_fm_verification_view
from rcm_desktop.adapter.isograph_import_service import build_from_sheets, build_from_workbook

CM_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "RCMCostdata export_CM.xlsx"
GOLDEN_CAUSE = "06H-350.1.1.1.1.1.A.1"
HOURS_PER_YEAR = 8760.0


def test_parse_effect_ids_nl_decimal_and_multiple() -> None:
    parsed = parse_effect_ids(
        "VGM - Effect 3 [RF=0,1], VGM - Effect 2 [RF=0,9], Schutten 0-20% functieverlies"
    )
    assert len(parsed) == 3
    assert parsed[0].effect_id == "VGM - Effect 3"
    assert parsed[0].redundancy_factor == pytest.approx(0.1)
    assert parsed[1].redundancy_factor == pytest.approx(0.9)
    assert parsed[2].redundancy_factor is None


def test_parse_effect_ids_empty() -> None:
    assert parse_effect_ids("") == []
    assert parse_effect_ids(None) == []


def test_pm_effect_fractie_uses_redundancy_factor() -> None:
    row = CauseEffectAssignmentRow(
        cause_id="FM-1",
        effect_id="E1",
        c_enable="True",
        p_enable="True",
        i_enable="False",
        redundancy_factor="0,5",
    )
    assert pm_effect_fractie(row) == pytest.approx(0.5)


def test_subindex_fallback_resolves_single_planned_task() -> None:
    row = CauseEffectAssignmentRow(
        cause_id="FM-1",
        effect_id="E1",
        c_enable="False",
        p_enable="True",
        i_enable="False",
        redundancy_factor=1,
        sub_index=2,
    )
    tasks = [
        ScheduledTaskRow("FM-1", 0, "REV", "Planned", "True"),
    ]
    resolved, warnings = resolve_pm_tasks_for_scope(row, tasks, "planned")
    assert len(resolved) == 1
    assert resolved[0].pm_id == "FM-1|REV|0"
    assert any("SubIndex-fallback" in w for w in warnings)


def test_dual_scope_p_and_i_create_two_pm_links() -> None:
    row = CauseEffectAssignmentRow(
        cause_id="FM-1",
        effect_id="E1",
        c_enable="False",
        p_enable="True",
        i_enable="True",
        redundancy_factor=0.5,
        sub_index=0,
    )
    tasks = [
        ScheduledTaskRow("FM-1", 0, "REV", "Planned", "True"),
        ScheduledTaskRow("FM-1", 1, "IN", "Inspection", "True"),
    ]
    resolved, _ = resolve_pm_tasks(row, tasks)
    assert {r.pm_id for r in resolved} == {"FM-1|REV|0", "FM-1|IN|1"}


def test_ambiguous_planned_tasks_no_fallback_link() -> None:
    row = CauseEffectAssignmentRow(
        cause_id="FM-1",
        effect_id="E1",
        c_enable="False",
        p_enable="True",
        i_enable="False",
        redundancy_factor=1,
        sub_index=0,
    )
    tasks = [
        ScheduledTaskRow("FM-1", 0, "A", "Planned", "True"),
        ScheduledTaskRow("FM-1", 0, "B", "Planned", "True"),
    ]
    resolved, warnings = resolve_pm_tasks(row, tasks)
    assert resolved == []
    assert not any("SubIndex-fallback" in w for w in warnings)


def test_audit_effect_ids_mismatch_detected() -> None:
    msg = audit_effect_ids_vs_fm_links(
        "E-missing [RF=0,5]",
        [("E1", 1.0)],
    )
    assert msg is not None
    assert "ontbrekend" in msg


def test_synthetic_effect_ids_mismatch_warning() -> None:
    sheets = {
        "RcmLocations": [{"Id": "L1", "Parent": "", "Description": "Loc"}],
        "RcmFunctions": [{"Id": "F1", "Parent": "L1", "Description": "Functie"}],
        "RcmFunctionalFailures": [{"Id": "FF1", "Parent": "F1", "Description": "FF"}],
        "RcmCauses": [
            {
                "Id": "FM-A",
                "Parent": "FF1",
                "Description": "FM",
                "LocationId": "L1",
                "FmMttf": 87600,
                "InitialAge": 0,
                "Mttr": 8,
                "EffectIds": "E-missing [RF=0,5]",
            },
        ],
        "RcmEffects": [{"Id": "E1", "Description": "Effect"}],
        "RcmCauseEffectAssignments": [
            {
                "Cause": "FM-A",
                "Effect": "E1",
                "CEnable": "True",
                "PEnable": "False",
                "IEnable": "False",
                "RedundancyFactor": 1,
            },
        ],
        "RcmCorrectiveTasks": [{"Cause": "FM-A", "TaskDuration": 8, "OperationalCost": 100}],
        "RcmScheduledTasks": [],
        "TaskGroups": [],
        "Project": [{"LifeTime": 876000}],
    }
    result = build_from_sheets(sheets, modeljaar=2026)
    assert any("EffectIds-mismatch" in w for w in result.warnings)
    assert result.warning_summary.get("effect_ids_mismatch", 0) >= 1


@pytest.mark.skipif(not CM_FIXTURE.is_file(), reason="CM fixture ontbreekt")
def test_golden_cause_fm_and_pm_effect_links() -> None:
    result = build_from_workbook(CM_FIXTURE, modeljaar=2026)
    project = result.project
    fm_links = [l for l in project.fm_effect_links.values() if l.fm_id == GOLDEN_CAUSE]
    assert len(fm_links) == 4
    fracties = sorted(l.fractie for l in fm_links)
    assert fracties == pytest.approx([0.1, 0.5, 0.9, 1.0])
    pm_links = [
        l
        for l in project.pm_effect_links.values()
        if l.pm_id.startswith(f"{GOLDEN_CAUSE}|")
    ]
    assert len(pm_links) >= 1
    schutten = [
        l
        for l in pm_links
        if l.klasse_id == "Schutten 0-20% functieverlies"
    ]
    assert len(schutten) == 1
    assert schutten[0].pm_id == f"{GOLDEN_CAUSE}|REV|0"
    assert schutten[0].fractie == pytest.approx(1.0)
    parsed = result.import_settings["isograph_causes"][GOLDEN_CAUSE].get(
        "effect_ids_parsed"
    )
    assert parsed is not None
    assert len(parsed) >= 4
    assert not any("EffectIds-mismatch" in w and GOLDEN_CAUSE in w for w in result.warnings)


@pytest.mark.skipif(not CM_FIXTURE.is_file(), reason="CM fixture ontbreekt")
def test_cm_fixture_pm_warnings_reduced_and_fm_stable() -> None:
    result = build_from_workbook(CM_FIXTURE, modeljaar=2026)
    assert len(result.project.fm_effect_links) == 224
    unresolved = [w for w in result.warnings if "PM-effect niet geïmporteerd" in w]
    assert len(unresolved) <= 12
    assert len(result.project.pm_effect_links) > 54
    assert result.warning_summary["unresolved_pm"] == len(unresolved)


@pytest.mark.skipif(not CM_FIXTURE.is_file(), reason="CM fixture ontbreekt")
def test_cm_import_motor_smoke_pm_effect_bijdragen() -> None:
    result = build_from_workbook(CM_FIXTURE, modeljaar=2026)
    run = run_incremental_analysis(
        result.project,
        CM_FIXTURE.with_suffix(".rcm.cache.json"),
        full_recompute=True,
        parallel=False,
    )
    fmr = run.fm_results[GOLDEN_CAUSE]
    pm_effect_total = sum(
        v for k, v in fmr.effect_bijdragen.items() if k.startswith("pm:")
    )
    if pm_effect_total == 0:
        pm_effect_total = sum(
            v
            for k, v in fmr.effect_bijdragen.items()
            if any(
                l.klasse_id == k
                for l in result.project.pm_effect_links.values()
                if l.pm_id.startswith(GOLDEN_CAUSE)
            )
        )
    assert fmr.expected_pm_downtime_hr >= 0.0
    pm_links = [
        l
        for l in result.project.pm_effect_links.values()
        if l.pm_id.startswith(f"{GOLDEN_CAUSE}|")
    ]
    if pm_links:
        assert fmr.expected_pm_downtime_hr > 0.0 or pm_effect_total > 0.0


@pytest.mark.skipif(not CM_FIXTURE.is_file(), reason="CM fixture ontbreekt")
def test_fm_verification_shows_pm_effect_links_for_golden_cause() -> None:
    result = build_from_workbook(CM_FIXTURE, modeljaar=2026)
    run = run_incremental_analysis(
        result.project,
        CM_FIXTURE.with_suffix(".rcm.cache.json"),
        full_recompute=True,
        parallel=False,
    )
    view = build_fm_verification_view(result.project, run.fm_results[GOLDEN_CAUSE])
    assert view.inputs is not None
    assert len(view.inputs.pm_effect_links) >= 1
