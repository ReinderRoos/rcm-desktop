"""Slice 77 issues 02–03 — isograph export-service (Qt-free)."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from rcm_core.models import RCMProject
from rcm_desktop.adapter.isograph_excel_reader import read_workbook_sheets
from rcm_desktop.adapter.isograph_export_service import export_project_to_workbook
from rcm_desktop.adapter.isograph_import_service import build_from_workbook

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "RCMCostdata export_leeg.xlsx"
CAUSE_ID = "06H-350.1.1.1.1.1.A.1"
HOURS_PER_YEAR = 8760.0


def _import_fixture() -> RCMProject:
    return build_from_workbook(FIXTURE, modeljaar=2026).project


def test_export_noop_preserves_must_v1_sheets(tmp_path: Path) -> None:
    project = _import_fixture()
    output = tmp_path / "export.xlsx"
    result = export_project_to_workbook(project, FIXTURE, output)

    assert output.is_file()
    assert result.total_patched >= 0
    before = read_workbook_sheets(FIXTURE)
    after = read_workbook_sheets(output)
    assert set(after) == set(before)
    for sheet in before:
        assert len(after[sheet]) == len(before[sheet])


def test_export_patch_fm_mttf_round_trips(tmp_path: Path) -> None:
    project = deepcopy(_import_fixture())
    fm = project.faalwijzes[CAUSE_ID]
    project.faalwijzes[CAUSE_ID] = replace(fm, mttf_jaar=fm.mttf_jaar + 1.0)
    output = tmp_path / "patched.xlsx"
    export_project_to_workbook(project, FIXTURE, output)

    reimport = build_from_workbook(output, modeljaar=2026).project
    assert reimport.faalwijzes[CAUSE_ID].mttf_jaar == pytest.approx(
        project.faalwijzes[CAUSE_ID].mttf_jaar
    )


def test_export_warns_on_missing_cause_in_project(tmp_path: Path) -> None:
    project = _import_fixture()
    fm_id = next(iter(project.faalwijzes))
    trimmed = deepcopy(project)
    del trimmed.faalwijzes[fm_id]

    output = tmp_path / "warn.xlsx"
    result = export_project_to_workbook(trimmed, FIXTURE, output)

    assert result.total_warned >= 1
    assert any(fm_id in w for w in result.warnings)
    after = read_workbook_sheets(output)
    assert any(r.get("Id") == fm_id for r in after["RcmCauses"])
