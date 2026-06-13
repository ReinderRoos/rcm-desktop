"""Slice 95 issue 02 — plan_kpi_refresh en plan_pbs_tree_refresh."""

from __future__ import annotations

from pathlib import Path

from rcm_core.persistence import load_project

from rcm_desktop.adapter.loaded_project import LoadedProject
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.workspace_derived_refresh import (
    plan_kpi_refresh,
    plan_pbs_tree_refresh,
)


def test_plan_kpi_refresh_none_session_returns_placeholder_rows() -> None:
    table = plan_kpi_refresh(None, run_result=None, scope_id=None)
    assert len(table.rows) == 4
    assert all(cell.raw is None for row in table.rows for cell in row.cells)


def test_plan_kpi_refresh_sample_project_returns_rows() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    loaded = LoadedProject.from_core(project)
    session = ProjectSession.from_parts(loaded, path=Path("tests/fixtures/sample_project.rcm.json"))
    table = plan_kpi_refresh(session, run_result=None, scope_id=None)
    assert len(table.rows) == 4


def test_plan_pbs_tree_refresh_none_session_returns_empty() -> None:
    plan = plan_pbs_tree_refresh(None, run_result=None)
    assert plan.kind == "empty"
    assert plan.roots == ()


def test_plan_pbs_tree_refresh_structure_without_run() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    loaded = LoadedProject.from_core(project)
    session = ProjectSession.from_parts(loaded, path=Path("tests/fixtures/sample_project.rcm.json"))
    plan = plan_pbs_tree_refresh(session, run_result=None)
    assert plan.kind in ("structure", "navigation")
    if plan.kind == "structure":
        assert len(plan.roots) > 0
    assert plan.show_totals is False
