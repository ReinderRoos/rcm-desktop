"""Slice 96 issue 02 — FM alignment with fingerprint fallback."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from rcm_core.persistence import load_project

from rcm_desktop.adapter.compare_align_service import align_failure_modes
from rcm_desktop.adapter.compare_balanced_presentation_service import build_compare_presentation


def test_id_match_has_priority_over_fingerprint() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    pairs = align_failure_modes(project, project)
    matched = [p for p in pairs if p.fm_id_a and p.fm_id_b]
    assert matched
    assert all(p.match_kind == "id" for p in matched)


def test_fingerprint_pairs_when_ids_differ_but_content_matches(tmp_path) -> None:
    src = Path("tests/fixtures/sample_project.rcm.json")
    data_a = json.loads(src.read_text(encoding="utf-8"))
    data_b = json.loads(src.read_text(encoding="utf-8"))
    fm_template = copy.deepcopy(data_a["faalwijzes"]["FM-001"])
    fm_template["fm_id"] = "FM-FP-B"
    data_b["faalwijzes"]["FM-FP-B"] = fm_template
    del data_b["faalwijzes"]["FM-001"]
    path_a = tmp_path / "a.rcm.json"
    path_b = tmp_path / "b.rcm.json"
    path_a.write_text(json.dumps(data_a), encoding="utf-8")
    path_b.write_text(json.dumps(data_b), encoding="utf-8")
    project_a = load_project(path_a)
    project_b = load_project(path_b)

    pairs = align_failure_modes(project_a, project_b)
    fp_pairs = [p for p in pairs if p.match_kind == "fingerprint"]
    assert len(fp_pairs) == 1
    assert fp_pairs[0].fm_id_a == "FM-001"
    assert fp_pairs[0].fm_id_b == "FM-FP-B"


def test_fingerprint_pairing_is_stable_sorted_greedy(tmp_path) -> None:
    """When multiple B candidates share a fingerprint, pick lowest sorted fm_id_b."""
    src = Path("tests/fixtures/sample_project.rcm.json")
    data_a = json.loads(src.read_text(encoding="utf-8"))
    data_b = json.loads(src.read_text(encoding="utf-8"))
    template = copy.deepcopy(data_a["faalwijzes"]["FM-001"])
    for new_id in ("FM-FP-Z", "FM-FP-A"):
        entry = copy.deepcopy(template)
        entry["fm_id"] = new_id
        data_b["faalwijzes"][new_id] = entry
    del data_b["faalwijzes"]["FM-001"]
    path_a = tmp_path / "a.rcm.json"
    path_b = tmp_path / "b.rcm.json"
    path_a.write_text(json.dumps(data_a), encoding="utf-8")
    path_b.write_text(json.dumps(data_b), encoding="utf-8")
    project_a = load_project(path_a)
    project_b = load_project(path_b)

    pairs = align_failure_modes(project_a, project_b)
    fp_pairs = [p for p in pairs if p.match_kind == "fingerprint"]
    assert len(fp_pairs) == 1
    assert fp_pairs[0].fm_id_b == "FM-FP-A"


def test_unmatched_a_and_b_when_no_id_or_fingerprint_match(tmp_path) -> None:
    src = Path("tests/fixtures/sample_project.rcm.json")
    data_a = json.loads(src.read_text(encoding="utf-8"))
    data_b = json.loads(src.read_text(encoding="utf-8"))
    data_b["faalwijzes"]["FM-ONLY-B"] = {
        **data_b["faalwijzes"]["FM-001"],
        "fm_id": "FM-ONLY-B",
        "faalwijze_omschrijving": "Unieke faalwijze B",
        "mttf_jaar": 999.0,
    }
    del data_b["faalwijzes"]["FM-001"]
    path_a = tmp_path / "a.rcm.json"
    path_b = tmp_path / "b.rcm.json"
    path_a.write_text(json.dumps(data_a), encoding="utf-8")
    path_b.write_text(json.dumps(data_b), encoding="utf-8")
    project_a = load_project(path_a)
    project_b = load_project(path_b)

    pairs = align_failure_modes(project_a, project_b)
    kinds = {p.match_kind for p in pairs}
    assert "unmatched_a" in kinds
    assert "unmatched_b" in kinds


def test_match_kind_exposed_in_compare_presentation(tmp_path) -> None:
    src = Path("tests/fixtures/sample_project.rcm.json")
    data_a = json.loads(src.read_text(encoding="utf-8"))
    data_b = json.loads(src.read_text(encoding="utf-8"))
    fm_template = copy.deepcopy(data_a["faalwijzes"]["FM-001"])
    fm_template["fm_id"] = "FM-FP-B"
    data_b["faalwijzes"]["FM-FP-B"] = fm_template
    del data_b["faalwijzes"]["FM-001"]
    path_a = tmp_path / "a.rcm.json"
    path_b = tmp_path / "b.rcm.json"
    path_a.write_text(json.dumps(data_a), encoding="utf-8")
    path_b.write_text(json.dumps(data_b), encoding="utf-8")
    project_a = load_project(path_a)
    project_b = load_project(path_b)

    presentation = build_compare_presentation(project_a, project_b)
    kinds = {entry.pair.match_kind for entry in presentation.entries}
    assert "fingerprint" in kinds
