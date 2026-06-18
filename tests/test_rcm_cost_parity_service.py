"""Adapter tests — RCM-Cost parity view (slice 65)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rcm_core.engine import run_analytical
from rcm_core.models import RCMProject
from rcm_core.rcm_cost_benchmark import ParityVerdict
from rcm_desktop.adapter.isograph_import_service import build_from_workbook
from rcm_desktop.adapter.rcm_cost_parity_service import build_parity_view

CM_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "RCMCostdata export_CM.xlsx"


def test_build_parity_view_without_benchmarks() -> None:
    project = RCMProject()
    fm_results, _ = run_analytical(project, parallel=False)
    view = build_parity_view(project, fm_results)
    assert view.has_benchmarks is False
    assert view.summary.benchmark_fm_count == 0


@pytest.mark.skipif(not CM_FIXTURE.is_file(), reason="CM fixture ontbreekt")
def test_build_parity_view_on_cm_fixture() -> None:
    built = build_from_workbook(CM_FIXTURE, modeljaar=2026)
    fm_results, _ = run_analytical(built.project, parallel=False)
    view = build_parity_view(built.project, fm_results)
    assert view.has_benchmarks is True
    assert view.summary.benchmark_fm_count == len(fm_results)
    assert len(view.rows) == len(fm_results)
    assert any(row.verdict == ParityVerdict.FAIL for row in view.rows)
    assert view.rows[0].aw_total_cost.startswith("€")
    assert view.rows[0].aw_expected_failures != "—"
    assert view.rows[0].rev_moments != ""
