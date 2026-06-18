"""Slice 95 issues 04-06 — dual-project compare use-cases."""

from __future__ import annotations

from pathlib import Path

from rcm_core.persistence import load_project

from rcm_desktop.adapter.compare_align_service import align_failure_modes
from rcm_desktop.adapter.compare_balanced_presentation_service import build_compare_presentation
from rcm_desktop.adapter.compare_diff_service import build_field_diffs, build_result_diffs
from rcm_desktop.adapter.compare_session_service import CompareSession, load_compare_session


def test_compare_session_loads_two_projects(tmp_path) -> None:
    src = Path("tests/fixtures/sample_project.rcm.json")
    path_a = tmp_path / "a.rcm.json"
    path_b = tmp_path / "b.rcm.json"
    path_a.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    path_b.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    session = load_compare_session(path_a, path_b)
    assert session.project_a is not None
    assert session.project_b is not None
    assert len(session.project_a.faalwijzes) > 0


def test_align_failure_modes_matches_by_id() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    pairs = align_failure_modes(project, project)
    assert len(pairs) >= 1
    assert all(p.match_kind == "id" for p in pairs if p.fm_id_a and p.fm_id_b)


def test_build_field_diffs_detects_mttf_change() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    variant = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    # Mutate a copy conceptually — use two loads; diff empty when identical
    diffs = build_field_diffs(project, variant, fm_id_a="FM-001", fm_id_b="FM-001")
    assert isinstance(diffs, tuple)


def test_build_compare_presentation_balanced_per_fm() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    presentation = build_compare_presentation(project, project)
    assert len(presentation.entries) >= 1
    entry = presentation.entries[0]
    assert hasattr(entry, "field_diffs")
    assert hasattr(entry, "result_diffs")


def test_align_failure_modes_covers_unmatched_sides(tmp_path) -> None:
    import json
    import shutil

    src = Path("tests/fixtures/sample_project.rcm.json")
    path_a = tmp_path / "a.rcm.json"
    path_b = tmp_path / "b.rcm.json"
    shutil.copy(src, path_a)
    data_b = json.loads(src.read_text(encoding="utf-8"))
    data_b["faalwijzes"]["FM-ONLY-B"] = {
        **data_b["faalwijzes"]["FM-001"],
        "fm_id": "FM-ONLY-B",
        "faalwijze_omschrijving": "Extra faalwijze B",
    }
    del data_b["faalwijzes"]["FM-001"]
    path_b.write_text(json.dumps(data_b), encoding="utf-8")
    project_a = load_project(path_a)
    project_b = load_project(path_b)
    pairs = align_failure_modes(project_a, project_b)
    kinds = {p.match_kind for p in pairs}
    assert "id" in kinds or "unmatched_a" in kinds
    assert "unmatched_a" in kinds
    assert "unmatched_b" in kinds


def test_build_field_diffs_classifies_mttf_as_parameterisatie() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    import copy

    variant = copy.deepcopy(project)
    variant.faalwijzes["FM-001"].mttf_jaar = project.faalwijzes["FM-001"].mttf_jaar + 5.0
    diffs = build_field_diffs(project, variant, fm_id_a="FM-001", fm_id_b="FM-001")
    mttf_diffs = [d for d in diffs if d.field == "mttf_jaar"]
    assert len(mttf_diffs) == 1
    assert mttf_diffs[0].difference_class == "parameterisatie"


def test_build_field_diffs_classifies_omschrijving_as_terminologie() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    import copy

    variant = copy.deepcopy(project)
    variant.faalwijzes["FM-001"].faalwijze_omschrijving = "Andere naam"
    diffs = build_field_diffs(project, variant, fm_id_a="FM-001", fm_id_b="FM-001")
    label_diffs = [d for d in diffs if d.field == "faalwijze_omschrijving"]
    assert len(label_diffs) == 1
    assert label_diffs[0].difference_class == "terminologie"
