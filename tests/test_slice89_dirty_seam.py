"""Slice 89 — buffer-brede dirty-seam op EditingHost (edit_dirty_global)."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from rcm_core.persistence import load_project
from rcm_desktop.adapter.editing_host import EditingHost


@pytest.fixture
def sample_project():
    return load_project(Path("tests/fixtures/sample_project.rcm.json"))


def _edit_first_row(host: EditingHost, entity: str, field: str, value) -> list[dict]:
    """Pas één veld aan in de eerste rij van een entiteit; geeft originele rijen terug."""
    session = host.editing_session
    original = copy.deepcopy(session.session["edit_current"][entity])
    rows = copy.deepcopy(original)
    assert rows, f"fixture heeft geen rijen voor entiteit {entity!r}"
    rows[0][field] = value
    session.apply_entity_rows(entity, rows)
    return original


def test_is_grid_dirty_detects_non_faalwijzen_entity(sample_project) -> None:
    host = EditingHost()
    host.ensure_grid(sample_project)
    assert host.is_grid_dirty() is False

    _edit_first_row(host, "pm_tasks", "taak_omschrijving", "aangepaste REV-taak")
    assert host.is_grid_dirty() is True


def test_is_grid_dirty_false_after_revert_to_original(sample_project) -> None:
    host = EditingHost()
    host.ensure_grid(sample_project)

    original = _edit_first_row(host, "pm_tasks", "taak_omschrijving", "tijdelijk")
    assert host.is_grid_dirty() is True

    host.editing_session.apply_entity_rows("pm_tasks", original)
    assert host.is_grid_dirty() is False


def test_is_grid_dirty_false_without_active_session() -> None:
    assert EditingHost().is_grid_dirty() is False


def test_is_grid_dirty_false_after_successful_commit(sample_project) -> None:
    host = EditingHost()
    host.ensure_grid(sample_project)
    _edit_first_row(host, "pm_tasks", "taak_omschrijving", "gecommitte wijziging")
    assert host.is_grid_dirty() is True

    result = host.commit_grid_edits()
    assert result.ok is True
    assert host.is_grid_dirty() is False


def test_dirty_non_faalwijzen_entity_reaches_shutdown_plan(sample_project) -> None:
    from rcm_desktop.adapter.shutdown_planner import ShutdownStep, plan_shutdown

    host = EditingHost()
    host.ensure_grid(sample_project)
    _edit_first_row(host, "effect_klassen", "omschrijving", "aangepast effect")

    plan = plan_shutdown(grid_dirty=host.is_grid_dirty(), busy=False)
    assert ShutdownStep.RESOLVE_GRID_DIRTY in plan.steps


def test_discard_restores_all_dirty_entities(sample_project) -> None:
    from rcm_desktop.adapter.dirty_guard_policy import resolve_dirty_choice

    host = EditingHost()
    host.ensure_grid(sample_project)
    original_pm = _edit_first_row(host, "pm_tasks", "taak_omschrijving", "weg ermee")
    original_fw = _edit_first_row(host, "faalwijzes", "faalwijze_omschrijving", "ook weg")
    assert host.is_grid_dirty() is True

    assert resolve_dirty_choice(host, "discard") == "proceed"
    assert host.is_grid_dirty() is False

    session = host.editing_session.session
    assert session["edit_current"]["pm_tasks"] == original_pm
    assert session["edit_current"]["faalwijzes"] == original_fw


def test_save_commits_all_dirty_entities(sample_project) -> None:
    from rcm_desktop.adapter.dirty_guard_policy import resolve_dirty_choice

    host = EditingHost()
    host.ensure_grid(sample_project)
    _edit_first_row(host, "pm_tasks", "taak_omschrijving", "blijvende wijziging")
    assert host.is_grid_dirty() is True

    assert resolve_dirty_choice(host, "save") == "proceed"
    assert host.is_grid_dirty() is False

    rows = host.editing_session.session["edit_current"]["pm_tasks"]
    assert rows[0]["taak_omschrijving"] == "blijvende wijziging"


def test_save_with_blocking_error_warns_and_keeps_buffer(sample_project) -> None:
    from rcm_desktop.adapter.dirty_guard_policy import resolve_dirty_choice

    host = EditingHost()
    host.ensure_grid(sample_project)
    _edit_first_row(host, "pm_tasks", "interval_jaar", "geen-getal")
    assert host.is_grid_dirty() is True

    assert resolve_dirty_choice(host, "save") == "warn_save_failed"
    assert host.is_grid_dirty() is True


def test_clean_buffer_proceeds_without_dialog(sample_project) -> None:
    from rcm_desktop.adapter.dirty_guard_policy import resolve_dirty_choice

    host = EditingHost()
    host.ensure_grid(sample_project)
    assert resolve_dirty_choice(host, "cancel") == "proceed"
