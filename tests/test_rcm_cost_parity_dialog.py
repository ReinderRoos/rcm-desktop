"""Dialog tests — RCM-Cost parity (slice 65)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from rcm_core.engine import run_analytical
from rcm_core.rcm_cost_benchmark import ParityVerdict
from rcm_desktop.adapter.isograph_import_service import build_from_workbook
from rcm_desktop.adapter.rcm_cost_parity_service import build_parity_view
from rcm_desktop.views.rcm_cost_parity_dialog import RcmCostParityDialog

CM_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "RCMCostdata export_CM.xlsx"


@pytest.mark.skipif(not CM_FIXTURE.is_file(), reason="CM fixture ontbreekt")
def test_parity_dialog_shows_fail_rows(qtbot) -> None:
    if QApplication.instance() is None:
        QApplication([])
    built = build_from_workbook(CM_FIXTURE, modeljaar=2026)
    fm_results, _ = run_analytical(built.project, parallel=False)
    view = build_parity_view(built.project, fm_results)
    dialog = RcmCostParityDialog(
        view,
        project=built.project,
        fm_results=fm_results,
    )
    qtbot.addWidget(dialog)
    assert dialog.visible_row_count() == len(view.rows)
    dialog._filter_combo.setCurrentText("Alleen afwijkingen")
    fail_count = sum(1 for row in view.rows if row.verdict == ParityVerdict.FAIL)
    assert dialog.visible_row_count() == fail_count
