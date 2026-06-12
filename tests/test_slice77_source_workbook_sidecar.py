"""Slice 77 issue 01 — AW-bron-sidecar bij import + source_workbook_path."""

from __future__ import annotations

import shutil
from pathlib import Path

from openpyxl import Workbook
from rcm_core.persistence import load_project

from rcm_desktop.adapter.isograph_open_flow_service import persist_import_wizard_result

from tests.test_isograph_open_flow_service import _minimal_wizard_result


def _write_minimal_workbook(path: Path) -> None:
    wb = Workbook()
    wb.save(path)


def test_persist_import_writes_source_workbook_sidecar(tmp_path: Path) -> None:
    source = tmp_path / "bron.xlsx"
    _write_minimal_workbook(source)
    target = tmp_path / "imported.rcm.json"
    wizard = _minimal_wizard_result()

    outcome = persist_import_wizard_result(
        wizard,
        target,
        source_workbook_path=source,
    )

    sidecar = target.with_suffix("").with_suffix(".rcm.source.xlsx")
    assert sidecar.is_file()
    assert outcome.project.import_settings["source_workbook_path"] == sidecar.name
    restored = load_project(target)
    assert restored.import_settings["source_workbook_path"] == sidecar.name


def test_persist_import_sidecar_is_copy_not_move(tmp_path: Path) -> None:
    source = tmp_path / "bron.xlsx"
    _write_minimal_workbook(source)
    original_bytes = source.read_bytes()
    target = tmp_path / "imported.rcm.json"

    persist_import_wizard_result(
        _minimal_wizard_result(),
        target,
        source_workbook_path=source,
    )

    assert source.read_bytes() == original_bytes
