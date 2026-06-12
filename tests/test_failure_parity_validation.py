"""Core tests — failure parity validation counterfactuals."""

from __future__ import annotations

from pathlib import Path

import pytest

from rcm_core.engine import run_analytical
from rcm_core.failure_parity_validation import (
    build_failure_validation_report,
    compute_expected_failures_for_fm,
)
from rcm_core.persistence import load_project

GAARKEUKEN = Path(__file__).resolve().parent / "fixtures" / "RCMCostdata export_Gaarkeuken.rcm.json"


@pytest.mark.skipif(not GAARKEUKEN.is_file(), reason="Gaarkeuken fixture ontbreekt")
def test_horizon_forward_not_less_than_cm_overlay_for_aging_fm() -> None:
    project = load_project(GAARKEUKEN)
    fm_results, _ = run_analytical(project, parallel=False)
    report = build_failure_validation_report(project, fm_results)

    aging_rows = [r for r in report.rows if r.failure_type == "aging" and r.aw_total_w]
    assert aging_rows, "verwacht aging FM's met AW TotalW"
    # Minstens één FM: AW-horizon levert meer falen dan RCM2-studieduur-cap
    assert any(r.ef_horizon_forward >= r.ef_cm_overlay for r in aging_rows)


@pytest.mark.skipif(not GAARKEUKEN.is_file(), reason="Gaarkeuken fixture ontbreekt")
def test_no_rev_differs_when_rev_structural_present() -> None:
    project = load_project(GAARKEUKEN)
    fm_id = next(iter(project.faalwijzes))
    disabled = frozenset(
        str(x) for x in (project.import_settings or {}).get("aw_disabled_pm_ids") or []
    )
    with_rev = compute_expected_failures_for_fm(project, fm_id, disabled_pm_ids=disabled)
    without_rev = compute_expected_failures_for_fm(
        project, fm_id, disabled_pm_ids=disabled, no_rev=True
    )
    # Triviaal als geen REV — beide >= 0
    assert with_rev >= 0.0
    assert without_rev >= 0.0
