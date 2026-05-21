from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt

from rcm_core.models import RCMProject

from rcm_desktop.adapter.kpi_table_model import KPITableModel
from rcm_desktop.adapter.kpi_table_service import CURRENT_ANALYSIS_LABEL, build_kpi_table
from rcm_desktop.adapter.run_service import run as run_single


def _project() -> RCMProject:
    raw = json.loads(Path("tests/fixtures/sample_project.rcm.json").read_text(encoding="utf-8"))
    return RCMProject.from_dict(raw)


def test_kpi_model_exposes_label_column_and_one_data_column():
    project = _project()
    path = Path("tests/fixtures/sample_project.rcm.json")
    run_result = run_single(project, path)
    table = build_kpi_table(project=project, run_result=run_result, scope_id=None)
    model = KPITableModel(table)

    assert model.rowCount() == 4
    assert model.columnCount() == 2
    headers = [model.headerData(c, Qt.Horizontal, Qt.DisplayRole) for c in range(2)]
    assert headers[0] == "KPI"
    assert headers[1] == CURRENT_ANALYSIS_LABEL


def test_kpi_model_renders_em_dash_without_run():
    project = _project()
    table = build_kpi_table(project=project, run_result=None, scope_id=None)
    model = KPITableModel(table)

    for r in range(model.rowCount()):
        assert model.data(model.index(r, 1), Qt.DisplayRole) == "—"


def test_kpi_model_renders_real_values_for_done_run():
    project = _project()
    path = Path("tests/fixtures/sample_project.rcm.json")
    run_result = run_single(project, path)
    table = build_kpi_table(project=project, run_result=run_result, scope_id=None)
    model = KPITableModel(table)

    text_failures = model.data(model.index(0, 1), Qt.DisplayRole)
    text_cost = model.data(model.index(2, 1), Qt.DisplayRole)
    assert text_failures != "—"
    assert "€" in text_cost
