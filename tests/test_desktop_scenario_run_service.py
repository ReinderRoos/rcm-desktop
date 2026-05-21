from __future__ import annotations

from pathlib import Path

from rcm_core.persistence import load_project
from rcm_core.models import PMTask, TaskType
from rcm_desktop.adapter.scenario_run_service import (
    SCENARIO_CM,
    SCENARIO_PM,
    build_project_for_scenario,
    run_cm,
    run_compare,
    run_pm,
)


def test_build_project_for_scenario_pm_keeps_tasks():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    out = build_project_for_scenario(project, SCENARIO_PM)
    assert len(out.pm_tasks) == len(project.pm_tasks)


def test_build_project_for_scenario_cm_keeps_only_svo_or_wet():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    project.pm_tasks["PM-WET"] = PMTask(
        pm_id="PM-WET",
        fm_id="FM-001",
        taak_type=TaskType.IN,
        taak_omschrijving="Wettelijke inspectie",
        interval_jaar=1.0,
        cost_eur=100.0,
        is_wettelijk_verplicht=True,
    )
    out = build_project_for_scenario(project, SCENARIO_CM)
    kept = set(out.pm_tasks)
    assert "PM-001" in kept  # sample fixture SVO
    assert "PM-WET" in kept
    for task in out.pm_tasks.values():
        if task.taak_type == TaskType.SVO or task.is_wettelijk_verplicht:
            continue
        fm = project.faalwijzes.get(task.fm_id)
        assert fm is not None and not fm.is_evident
        assert task.taak_type in (TaskType.IN, TaskType.TST)


def test_run_cm_produces_same_aggregates_as_compare_cm_branch():
    import math

    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    path = Path("tests/fixtures/sample_project.rcm.json")

    single = run_cm(project, path)
    pair = run_compare(project, path)

    assert single.status == "done"
    assert pair.status == "done"
    assert single.run_result is not None
    assert pair.cm_result is not None

    a = single.run_result.metrics
    b = pair.cm_result.metrics
    assert math.isclose(
        a.total_lifecycle_faalmomenten, b.total_lifecycle_faalmomenten, abs_tol=1e-6
    )
    assert math.isclose(a.total_downtime_hr, b.total_downtime_hr, abs_tol=1e-3)
    assert math.isclose(a.total_cost_eur, b.total_cost_eur, abs_tol=1e-3)


def test_run_pm_produces_same_aggregates_as_compare_pm_branch():
    import math

    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    path = Path("tests/fixtures/sample_project.rcm.json")

    single = run_pm(project, path)
    pair = run_compare(project, path)

    assert single.status == "done"
    assert pair.status == "done"
    a = single.run_result.metrics
    b = pair.pm_result.metrics
    assert math.isclose(
        a.total_lifecycle_faalmomenten, b.total_lifecycle_faalmomenten, abs_tol=1e-6
    )
    assert math.isclose(a.total_downtime_hr, b.total_downtime_hr, abs_tol=1e-3)
    assert math.isclose(a.total_cost_eur, b.total_cost_eur, abs_tol=1e-3)


def test_run_cm_without_project_returns_error_status():
    single = run_cm(None, Path("tests/fixtures/sample_project.rcm.json"))
    assert single.status == "error"
    assert single.scenario_project is None


def test_run_pm_without_project_returns_error_status():
    single = run_pm(None, Path("tests/fixtures/sample_project.rcm.json"))
    assert single.status == "error"
    assert single.scenario_project is None


def test_run_compare_remains_callable_as_internal_pipeline():
    """Issue 08 — `run_compare` blijft beschikbaar als interne functie en geeft
    dezelfde aggregaten als de combinatie van `run_cm` + `run_pm`.

    De UI-laag triggert `run_compare` niet meer direct (de
    `Vergelijk scenario's (CM/PM)`-knop is verwijderd), maar de helper blijft
    bestaan om hergebruik door `run_cm`/`run_pm` via één materialisatie-helper
    te garanderen.
    """
    import math

    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    path = Path("tests/fixtures/sample_project.rcm.json")

    pair = run_compare(project, path)
    single_cm = run_cm(project, path)
    single_pm = run_pm(project, path)

    assert pair.status == "done"
    assert pair.cm_result is not None and pair.pm_result is not None
    for a, b in (
        (single_cm.run_result.metrics, pair.cm_result.metrics),
        (single_pm.run_result.metrics, pair.pm_result.metrics),
    ):
        assert math.isclose(
            a.total_lifecycle_faalmomenten, b.total_lifecycle_faalmomenten, abs_tol=1e-6
        )
        assert math.isclose(a.total_downtime_hr, b.total_downtime_hr, abs_tol=1e-3)
        assert math.isclose(a.total_cost_eur, b.total_cost_eur, abs_tol=1e-3)


def test_cm_and_pm_scenarios_share_materialization_with_run_compare():
    """Issue 07 — geen drift: scenario-projecten zijn identiek tussen
    `run_compare` en `run_cm`/`run_pm` (zelfde materialisatie-helper).
    """
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    path = Path("tests/fixtures/sample_project.rcm.json")

    single_cm = run_cm(project, path)
    single_pm = run_pm(project, path)
    pair = run_compare(project, path)

    assert single_cm.scenario_project is not None
    assert single_pm.scenario_project is not None
    assert pair.cm_project is not None
    assert pair.pm_project is not None

    assert single_cm.scenario_project.to_dict() == pair.cm_project.to_dict()
    assert single_pm.scenario_project.to_dict() == pair.pm_project.to_dict()

