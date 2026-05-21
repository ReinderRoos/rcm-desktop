from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from rcm_core.models import RCMProject

from rcm_desktop.adapter.kpi_table_service import (
    CURRENT_ANALYSIS_KEY,
    CURRENT_ANALYSIS_LABEL,
    KPI_KEY_LIFECYCLE_COSTS_EUR,
    KPI_KEY_LIFECYCLE_FAILURES,
    KPI_KEY_PM_TASKS_ACTIVE,
    KPI_KEY_UNAVAILABILITY_PCT,
    build_kpi_table,
)
from rcm_desktop.adapter.run_service import run as run_single


def _sample_project() -> RCMProject:
    raw = json.loads(Path("tests/fixtures/sample_project.rcm.json").read_text(encoding="utf-8"))
    return RCMProject.from_dict(raw)


def test_kpi_table_has_four_rows_with_known_keys():
    project = _sample_project()
    path = Path("tests/fixtures/sample_project.rcm.json")
    run_result = run_single(project, path)
    table = build_kpi_table(project=project, run_result=run_result, scope_id=None)

    keys = tuple(row.key for row in table.rows)
    assert keys == (
        KPI_KEY_LIFECYCLE_FAILURES,
        KPI_KEY_UNAVAILABILITY_PCT,
        KPI_KEY_LIFECYCLE_COSTS_EUR,
        KPI_KEY_PM_TASKS_ACTIVE,
    )


def test_kpi_table_has_single_current_analysis_column():
    project = _sample_project()
    path = Path("tests/fixtures/sample_project.rcm.json")
    run_result = run_single(project, path)
    table = build_kpi_table(project=project, run_result=run_result, scope_id=None)

    assert table.scenario_keys == (CURRENT_ANALYSIS_KEY,)
    assert table.scenario_labels == (CURRENT_ANALYSIS_LABEL,)


def test_kpi_table_without_run_renders_em_dash():
    project = _sample_project()
    table = build_kpi_table(project=project, run_result=None, scope_id=None)

    for row in table.rows:
        assert len(row.cells) == 1
        assert row.cells[0].raw is None
        assert row.cells[0].display == "—"


def test_kpi_table_values_match_run_metrics_when_scope_none():
    project = _sample_project()
    path = Path("tests/fixtures/sample_project.rcm.json")
    run_result = run_single(project, path)
    table = build_kpi_table(project=project, run_result=run_result, scope_id=None)

    by_key = {row.key: row.cells[0] for row in table.rows}
    metrics = run_result.metrics
    assert math.isclose(
        by_key[KPI_KEY_LIFECYCLE_FAILURES].raw,
        metrics.total_lifecycle_faalmomenten,
        abs_tol=1e-6,
    )
    assert math.isclose(
        by_key[KPI_KEY_LIFECYCLE_COSTS_EUR].raw, metrics.total_cost_eur, abs_tol=1e-3
    )


def test_kpi_row_4_pm_tasks_active_ignores_scope_id():
    project = _sample_project()
    path = Path("tests/fixtures/sample_project.rcm.json")
    run_result = run_single(project, path)
    expected = len(project.pm_tasks)

    table_full = build_kpi_table(project=project, run_result=run_result, scope_id=None)
    scoped_scope_id = next(iter(project.pbs_items))
    table_scoped = build_kpi_table(
        project=project, run_result=run_result, scope_id=scoped_scope_id
    )

    pm_row_full = next(r for r in table_full.rows if r.key == KPI_KEY_PM_TASKS_ACTIVE)
    pm_row_scoped = next(r for r in table_scoped.rows if r.key == KPI_KEY_PM_TASKS_ACTIVE)
    assert pm_row_full.cells[0].raw == expected
    assert pm_row_scoped.cells[0].raw == expected


def test_kpi_rows_1_to_3_respect_subtree_scope():
    project = _sample_project()
    path = Path("tests/fixtures/sample_project.rcm.json")
    run_result = run_single(project, path)
    pbs_with_fm = {fr.pbs_id for fr in run_result.fm_core_results}
    scope_id = next(iter(pbs_with_fm))

    subtree_failures = sum(
        fr.expected_failures
        for fr in run_result.fm_core_results
        if fr.pbs_id == scope_id
    )
    subtree_cost = sum(
        fr.total_cost_eur for fr in run_result.fm_core_results if fr.pbs_id == scope_id
    )

    table = build_kpi_table(project=project, run_result=run_result, scope_id=scope_id)
    by_key = {row.key: row.cells[0] for row in table.rows}

    assert math.isclose(
        by_key[KPI_KEY_LIFECYCLE_FAILURES].raw, subtree_failures, abs_tol=1e-6
    )
    assert math.isclose(
        by_key[KPI_KEY_LIFECYCLE_COSTS_EUR].raw, subtree_cost, abs_tol=1e-3
    )
