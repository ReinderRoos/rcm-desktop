"""Slice 71 issue 00 — CM-overlay lifecycle-kosten diagnose (Gaarkeuken)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rcm_core.cm_overlay import aw_disabled_pm_ids, materialize_cm_overlay_project
from rcm_core.engine import run_analytical
from rcm_core.persistence import load_project
from rcm_desktop.adapter import run_service

GAARKEUKEN = Path(__file__).resolve().parent / "fixtures" / "RCMCostdata export_Gaarkeuken.rcm.json"

# Gemeten 2026-06-05 (50j lifecycle, aw_mc_lifecycle_horizon=True).
_OVERLAY_COST_EUR = 154_434_970.0
_RAW_COST_EUR = 172_296_932.0
_AW_DISABLED_PM_COUNT = 235


@pytest.mark.skipif(not GAARKEUKEN.is_file(), reason="Gaarkeuken fixture ontbreekt")
def test_gaarkeuken_import_has_cm_overlay_pm_set() -> None:
    project = load_project(GAARKEUKEN)
    disabled = aw_disabled_pm_ids(project)
    assert len(disabled) == _AW_DISABLED_PM_COUNT


@pytest.mark.skipif(not GAARKEUKEN.is_file(), reason="Gaarkeuken fixture ontbreekt")
def test_run_service_total_cost_uses_cm_overlay_materialization() -> None:
    """run_service default pad moet overlay-kosten geven, niet raw-project (~172 M)."""
    project = load_project(GAARKEUKEN)
    result = run_service.run(project, GAARKEUKEN, full_recompute=True)
    assert result.status == "done"
    assert result.metrics.total_cost_eur == pytest.approx(_OVERLAY_COST_EUR, rel=1e-4)


@pytest.mark.skipif(not GAARKEUKEN.is_file(), reason="Gaarkeuken fixture ontbreekt")
def test_cm_overlay_lowers_total_cost_vs_raw_project() -> None:
    project = load_project(GAARKEUKEN)
    fm_raw, _ = run_analytical(project, parallel=False)
    cost_raw = sum(r.total_cost_eur for r in fm_raw.values())

    aligned = materialize_cm_overlay_project(project)
    fm_overlay, _ = run_analytical(aligned, parallel=False)
    cost_overlay = sum(r.total_cost_eur for r in fm_overlay.values())

    assert cost_raw == pytest.approx(_RAW_COST_EUR, rel=1e-4)
    assert cost_overlay == pytest.approx(_OVERLAY_COST_EUR, rel=1e-4)
    assert cost_overlay < cost_raw
