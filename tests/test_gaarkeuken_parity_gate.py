"""Slice 66/67 — Gaarkeuken parity-gate regressie."""

from __future__ import annotations

from pathlib import Path

import pytest

from rcm_core.cm_overlay import materialize_cm_overlay_project
from rcm_core.engine import run_analytical
from rcm_core.persistence import load_project
from rcm_core.rcm_cost_benchmark import build_parity_report

GAARKEUKEN = Path(__file__).resolve().parent / "fixtures" / "RCMCostdata export_Gaarkeuken.rcm.json"
ANCHOR_FM_ID = "06H-350.2.12.2.1.A.1"

# Baseline: 128 parity-fails op 135 benchmark-FM's. Slice 67 (repair_quality + CM-overlay)
# verbetert # falen-validatie; cost-parity blijft 128 door A1/A2/A4 residu.
_REV_SURVIVAL_EXPLOSION_EF = 10_000.0
_FAIL_COUNT_CEILING = 128


def _gaarkeuken_parity_report():
    project = load_project(GAARKEUKEN)
    aligned = materialize_cm_overlay_project(project)
    fm_results, _ = run_analytical(aligned, parallel=False)
    return project, build_parity_report(project, fm_results)


def _has_rev_survival_explosion(row) -> bool:
    return (
        row.expected_failures_rcm is not None
        and row.expected_failures_rcm > _REV_SURVIVAL_EXPLOSION_EF
    )


@pytest.mark.skipif(not GAARKEUKEN.is_file(), reason="Gaarkeuken fixture ontbreekt")
def test_gaarkeuken_parity_has_no_rev_survival_explosion() -> None:
    """REV-survival bug gaf ~8 FMs expected_failures > 10⁴; na fix geen explosies meer."""
    _project, report = _gaarkeuken_parity_report()
    explosive = [row.fm_id for row in report.rows if _has_rev_survival_explosion(row)]
    assert explosive == []


@pytest.mark.skipif(not GAARKEUKEN.is_file(), reason="Gaarkeuken fixture ontbreekt")
def test_gaarkeuken_anchor_fm_not_rev_survival_explosion() -> None:
    """Anker-FM 06H-350.2.12.2.1.A.1: geen ×10⁵ faalmomenten meer (was ~4,5·10⁵)."""
    _project, report = _gaarkeuken_parity_report()
    anchor = next(row for row in report.rows if row.fm_id == ANCHOR_FM_ID)
    assert anchor.expected_failures_rcm is not None
    assert anchor.expected_failures_rcm < 50.0
    assert anchor.total_cost_aw is not None and anchor.total_cost_rcm is not None
    assert anchor.total_cost_rcm / anchor.total_cost_aw < 1_000.0


@pytest.mark.skipif(not GAARKEUKEN.is_file(), reason="Gaarkeuken fixture ontbreekt")
def test_gaarkeuken_parity_summary_within_fail_ceiling() -> None:
    """Parity-summary: fail-count ≤ 128 (finetune issue-02; explosies apart bewaakt)."""
    project, report = _gaarkeuken_parity_report()
    assert project.config.aw_mc_lifecycle_horizon is True
    summary = report.summary
    assert summary.benchmark_fm_count == 135
    assert summary.pass_count >= 0
    assert summary.fail_count <= _FAIL_COUNT_CEILING
    assert summary.informative_count >= 0
    assert summary.missing_benchmark_count == 0
    assert (
        summary.pass_count + summary.fail_count + summary.informative_count
        == summary.benchmark_fm_count
    )

