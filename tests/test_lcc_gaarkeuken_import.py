"""LCC tijdsplot op geïmporteerd Gaarkeuken-project (regressie AttributeError WET)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rcm_core.persistence import load_project
from rcm_desktop.adapter.lcc_planning_service import build_lcc_planning_curve_reconciled
from rcm_desktop.adapter.run_service import run

GAARKEUKEN = Path(__file__).resolve().parent / "fixtures" / "RCMCostdata export_Gaarkeuken.rcm.json"


@pytest.mark.skipif(not GAARKEUKEN.is_file(), reason="Gaarkeuken fixture ontbreekt")
def test_lcc_planning_curve_builds_for_imported_gaarkeuken() -> None:
    project = load_project(GAARKEUKEN)
    rr = run(project, GAARKEUKEN, full_recompute=False)
    assert rr.status == "done"
    curve = build_lcc_planning_curve_reconciled(project, rr)
    assert curve is not None
    assert len(curve.display_buckets) > 0
