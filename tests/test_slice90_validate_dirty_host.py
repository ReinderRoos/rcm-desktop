"""Slice 90 issue 06 — Validate-venster dirty via EditingHost."""

from __future__ import annotations

from pathlib import Path

import pytest

from rcm_core.persistence import load_project
from rcm_desktop.adapter.editing_host import EditingHost
from rcm_desktop.adapter.entity_edit_service import EntityEditService


@pytest.fixture
def sample_project():
    return load_project(Path("tests/fixtures/sample_project.rcm.json"))


def test_editing_host_dirty_after_non_faalwijzen_edit(sample_project) -> None:
    host = EditingHost()
    grid = host.ensure_grid(sample_project)
    rev = EntityEditService.for_view("input.rev_tasks")
    rev.init(sample_project)
    rev.attach_editing_session(grid.editing_session)
    row = rev.rows()[0]
    field = next(f for f in row.editable_fields if f != rev.config.key_field)
    rev.apply_change(row.row_key, field, "999")
    assert host.is_grid_dirty() is True


def test_editing_host_clean_after_reset(sample_project) -> None:
    host = EditingHost()
    grid = host.ensure_grid(sample_project)
    grid.apply_change("FM-001", "mttf_jaar", "99")
    assert host.is_grid_dirty() is True
    grid.reset(sample_project)
    assert host.is_grid_dirty() is False
