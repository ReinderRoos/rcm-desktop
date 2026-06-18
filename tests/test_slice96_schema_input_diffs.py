"""Slice 96 issue 03 — schema-driven input diffs."""

from __future__ import annotations

import copy
from pathlib import Path

from rcm_core.editing.schemas import ENTITY_SCHEMAS
from rcm_core.persistence import load_project

from rcm_desktop.adapter.compare_diff_service import (
    build_field_diffs,
    compare_field_names,
)


def test_compare_fields_derived_from_editing_registry() -> None:
    schema_fields = set(ENTITY_SCHEMAS["faalwijzes"]["field_types"])
    excluded = {"fm_id", "library_ref", "notes", "downtime_per_failure"}
    expected = {
        name
        for name in schema_fields
        if name not in excluded and not name.startswith("aanname_")
    }
    assert set(compare_field_names()) == expected


def test_excluded_fields_not_in_field_diffs() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    variant = copy.deepcopy(project)
    fm = variant.faalwijzes["FM-001"]
    fm.library_ref = "changed-ref"
    fm.notes = "changed notes"
    fm.aanname_faalmodel = "changed aanname"
    diffs = build_field_diffs(project, variant, fm_id_a="FM-001", fm_id_b="FM-001")
    diff_fields = {d.field for d in diffs}
    assert "library_ref" not in diff_fields
    assert "notes" not in diff_fields
    assert "fm_id" not in diff_fields
    assert not any(f.startswith("aanname_") for f in diff_fields)
    assert "downtime_per_failure" not in diff_fields


def test_terminologie_vs_parameterisatie_classification() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    variant = copy.deepcopy(project)
    variant.faalwijzes["FM-001"].faalwijze_omschrijving = "Andere naam"
    term_diffs = build_field_diffs(project, variant, fm_id_a="FM-001", fm_id_b="FM-001")
    assert any(d.field == "faalwijze_omschrijving" and d.difference_class == "terminologie" for d in term_diffs)

    variant2 = copy.deepcopy(project)
    variant2.faalwijzes["FM-001"].mttf_jaar = project.faalwijzes["FM-001"].mttf_jaar + 5.0
    param_diffs = build_field_diffs(project, variant2, fm_id_a="FM-001", fm_id_b="FM-001")
    assert any(d.field == "mttf_jaar" and d.difference_class == "parameterisatie" for d in param_diffs)


def test_schema_field_sigma_jaar_included_when_different() -> None:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    variant = copy.deepcopy(project)
    variant.faalwijzes["FM-001"].sigma_jaar = 12.0
    diffs = build_field_diffs(project, variant, fm_id_a="FM-001", fm_id_b="FM-001")
    assert any(d.field == "sigma_jaar" for d in diffs)
