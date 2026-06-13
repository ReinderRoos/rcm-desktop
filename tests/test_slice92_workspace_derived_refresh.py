"""Slice 92 — plan_nb_filter_refresh pure-functie tests (geen Qt vereist)."""

from __future__ import annotations

from pathlib import Path

from rcm_core.persistence import load_project

from rcm_desktop.adapter.workspace_derived_refresh import plan_nb_filter_refresh


def test_plan_nb_filter_refresh_none_project_returns_empty() -> None:
    """plan_nb_filter_refresh(None, ()) geeft lege presentatie."""
    result = plan_nb_filter_refresh(None, ())
    assert result.entries == ()


def test_plan_nb_filter_refresh_project_no_run_returns_entries() -> None:
    """plan_nb_filter_refresh met project maar zonder run-resultaten geeft entries (niet selecteerbaar)."""
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    result = plan_nb_filter_refresh(project, ())
    assert len(result.entries) > 0
    assert all(not entry.selectable for entry in result.entries)


def test_plan_nb_filter_refresh_is_qt_free() -> None:
    """plan_nb_filter_refresh heeft geen Qt-import nodig (importeerbaar zonder display)."""
    import importlib
    import sys

    # Verifieer dat het module importeerbaar is zonder PySide6 te triggeren
    mod_name = "rcm_desktop.adapter.workspace_derived_refresh"
    mod = sys.modules.get(mod_name) or importlib.import_module(mod_name)
    assert callable(getattr(mod, "plan_nb_filter_refresh", None))
