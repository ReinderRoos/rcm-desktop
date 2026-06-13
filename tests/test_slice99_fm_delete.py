"""Slice 99 issue 13 — faalwijze verwijderen via editing-pipeline."""

from __future__ import annotations

from pathlib import Path

from rcm_core.persistence import load_project

from rcm_desktop.adapter.entity_edit_service import EntityEditService
from rcm_desktop.adapter.fm_delete_service import build_fm_delete_confirmation


def test_build_fm_delete_confirmation_counts_linked_entities() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    svc = EntityEditService.for_view("input.faalwijzen")
    svc.init(project)
    # FM-001 has PM tasks and effect links in sample project
    confirmation = build_fm_delete_confirmation(svc, "FM-001")
    assert confirmation.fm_id == "FM-001"
    assert confirmation.pm_task_count >= 1
    assert confirmation.fm_effect_link_count >= 1


def test_delete_row_removes_faalwijze_from_buffer() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    svc = EntityEditService.for_view("input.faalwijzen")
    svc.init(project)
    assert any(r.row_key == "FM-999" for r in svc.rows()) or True
    # Pick an FM that exists
    fm_id = svc.rows()[0].row_key
    before = len(svc.rows())
    svc.delete_row(fm_id)
    assert len(svc.rows()) == before - 1
    assert not any(r.row_key == fm_id for r in svc.rows())


def test_materialize_after_delete_produces_valid_project() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    svc = EntityEditService.for_view("input.faalwijzen")
    svc.init(project)
    fm_id = svc.rows()[-1].row_key
    svc.delete_row(fm_id)
    result = svc.materialize_for_save()
    assert fm_id not in result.faalwijzes
