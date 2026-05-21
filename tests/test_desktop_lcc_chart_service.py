"""Adapter: LCCChartInput bouwen uit RunResult + project."""

from __future__ import annotations

import json
from pathlib import Path

from rcm_core.models import RCMProject

from rcm_desktop.adapter.lcc_chart_service import (
    build_compare_lcc_input,
    build_single_run_lcc_input,
    sum_correctief_preventief,
)
from rcm_desktop.adapter.run_service import run as run_single
from rcm_desktop.adapter.scenario_run_service import run_compare


def _sample() -> RCMProject:
    raw = json.loads(Path("tests/fixtures/sample_project.rcm.json").read_text(encoding="utf-8"))
    return RCMProject.from_dict(raw)


def test_single_run_lcc_reconciles_correctief_and_preventief_totals():
    project = _sample()
    path = Path("tests/fixtures/sample_project.rcm.json")
    rr = run_single(project, path, full_recompute=True, parallel=False)
    assert rr.status == "done"
    inp = build_single_run_lcc_input(project, rr)
    assert inp is not None
    assert inp.mode == "single_run"
    assert inp.single_curve is not None
    sc, sp, _tot = sum_correctief_preventief(inp.single_curve)
    target_corr = sum(r.expected_cm_cost_eur for r in rr.fm_core_results)
    target_prev = sum(r.pm_cost_eur for r in rr.fm_core_results)
    assert abs(sc - target_corr) < 1e-3
    assert abs(sp - target_prev) < 1e-3


def test_compare_lcc_both_scenarios_present():
    project = _sample()
    path = Path("tests/fixtures/sample_project.rcm.json")
    pair = run_compare(project, path)
    assert pair.status == "done"
    assert pair.cm_project is not None and pair.pm_project is not None
    inp = build_compare_lcc_input(
        cm_project=pair.cm_project,
        cm_run=pair.cm_result,
        pm_project=pair.pm_project,
        pm_run=pair.pm_result,
    )
    assert inp is not None
    assert inp.mode == "compare"
    assert inp.cm_curve is not None and inp.pm_curve is not None
    c_corr, c_prev, _ = sum_correctief_preventief(inp.cm_curve)
    p_corr, p_prev, _ = sum_correctief_preventief(inp.pm_curve)
    assert pair.cm_result is not None and pair.pm_result is not None
    t_cm_corr = sum(r.expected_cm_cost_eur for r in pair.cm_result.fm_core_results)
    t_cm_prev = sum(r.pm_cost_eur for r in pair.cm_result.fm_core_results)
    t_pm_corr = sum(r.expected_cm_cost_eur for r in pair.pm_result.fm_core_results)
    t_pm_prev = sum(r.pm_cost_eur for r in pair.pm_result.fm_core_results)
    assert abs(c_corr - t_cm_corr) < 1e-3
    assert abs(c_prev - t_cm_prev) < 1e-3
    assert abs(p_corr - t_pm_corr) < 1e-3
    assert abs(p_prev - t_pm_prev) < 1e-3
