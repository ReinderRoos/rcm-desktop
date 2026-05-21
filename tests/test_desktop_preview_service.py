from __future__ import annotations

from pathlib import Path

from rcm_core.persistence import load_project
from rcm_desktop.adapter import preview_service


def test_build_preview_happy_path_counts_and_top5():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))

    preview = preview_service.build(project)

    assert preview.pbs_items == len(project.pbs_items)
    assert preview.functies == len(project.functies)
    assert preview.faalwijzes == len(project.faalwijzes)
    assert preview.pm_tasks == len(project.pm_tasks)
    assert len(preview.top_faalwijzes) <= 5
    if preview.top_faalwijzes:
        first = preview.top_faalwijzes[0]
        assert first.fm_id
        assert first.faalwijze_omschrijving


def test_build_preview_zero_faalwijzes_returns_empty_top_list():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    project.faalwijzes.clear()

    preview = preview_service.build(project)

    assert preview.faalwijzes == 0
    assert preview.top_faalwijzes == []


def test_build_preview_limits_top5_and_keeps_input_order():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    existing = list(project.faalwijzes.values())
    source = existing[0]
    for idx in range(6):
        clone = type(source)(**{**source.__dict__, "fm_id": f"FM-EXTRA-{idx}", "faalwijze_omschrijving": f"Extra {idx}"})
        project.faalwijzes[clone.fm_id] = clone

    preview = preview_service.build(project)

    expected_ids = list(project.faalwijzes.keys())[:5]
    assert [item.fm_id for item in preview.top_faalwijzes] == expected_ids
    assert len(preview.top_faalwijzes) == 5


def test_build_preview_maps_exact_fm_fields():
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    first = next(iter(project.faalwijzes.values()))

    preview = preview_service.build(project)

    assert preview.top_faalwijzes
    assert preview.top_faalwijzes[0].fm_id == first.fm_id
    assert preview.top_faalwijzes[0].faalwijze_omschrijving == first.faalwijze_omschrijving
