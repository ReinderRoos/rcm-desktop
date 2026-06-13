"""Slice 94 — plan_contribution_year_refresh pure-functie tests."""

from __future__ import annotations

from pathlib import Path

from rcm_core.persistence import load_project

from rcm_desktop.adapter.workspace_derived_refresh import plan_contribution_year_refresh


def test_plan_contribution_year_refresh_none_project_returns_empty() -> None:
    assert plan_contribution_year_refresh(None) == ()


def test_plan_contribution_year_refresh_sample_project_returns_years() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    years = plan_contribution_year_refresh(project)
    assert len(years) > 0
    assert years == tuple(sorted(years))
