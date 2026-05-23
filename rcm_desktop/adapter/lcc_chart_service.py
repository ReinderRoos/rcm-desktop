"""LCC-presentatie: bouw `LCCChartInput` uit project + `RunResult` (slice 21)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from rcm_core.lcc_profile import build_cm_eur_per_bucket, ltap_horizon_bucket_count
from rcm_core.models import RCMProject

from rcm_desktop.adapter.calendar_year import calendar_year_for_horizon_index
from rcm_desktop.adapter.ltap_service import build_ltap_view
from rcm_desktop.adapter.run_service import RunResult


@dataclass(frozen=True)
class LCCYearBucket:
    calendar_year: int
    correctief_eur: float  # faalgebonden (expected_cm_cost verdeeld over jaren)
    preventief_eur: float  # PM-taken (pm_cost verdeeld over jaren)


@dataclass(frozen=True)
class LCCScenarioCurve:
    scenario_key: str
    label: str
    buckets: tuple[LCCYearBucket, ...]


@dataclass(frozen=True)
class LCCChartInput:
    mode: Literal["compare", "single_run"]
    cm_curve: LCCScenarioCurve | None
    pm_curve: LCCScenarioCurve | None
    single_curve: LCCScenarioCurve | None


def _pm_eur_per_bucket_ltap(project: RCMProject, target_pm_total: float) -> list[float]:
    from rcm_desktop.adapter.ltap_pm_cost_series import pm_eur_per_bucket_scaled

    return pm_eur_per_bucket_scaled(project, target_pm_total)


def _curve_from_project_run(
    *,
    project: RCMProject,
    run: RunResult,
    scenario_key: str,
    label: str,
) -> LCCScenarioCurve | None:
    if run.status != "done" or not run.fm_core_results:
        return None
    cm = build_cm_eur_per_bucket(project, run.fm_core_results)
    target_pm = sum(float(r.pm_cost_eur) for r in run.fm_core_results)
    pm = _pm_eur_per_bucket_ltap(project, target_pm)
    n = ltap_horizon_bucket_count(float(project.config.lifecycle_years))
    if len(cm) < n:
        cm = cm + [0.0] * (n - len(cm))
    if len(pm) < n:
        pm = pm + [0.0] * (n - len(pm))
    cm = cm[:n]
    pm = pm[:n]
    mj = int(project.config.modeljaar)
    built: list[LCCYearBucket] = []
    for h in range(n):
        cy = calendar_year_for_horizon_index(mj, h)
        built.append(
            LCCYearBucket(calendar_year=cy, correctief_eur=cm[h], preventief_eur=pm[h]),
        )

    target_cm = sum(float(r.expected_cm_cost_eur) for r in run.fm_core_results)
    cm_sum = sum(b.correctief_eur for b in built)
    pm_sum = sum(b.preventief_eur for b in built)
    if cm_sum > 0 and not math.isclose(cm_sum, target_cm, rel_tol=0, abs_tol=1e-4):
        cf = target_cm / cm_sum
        built = [
            LCCYearBucket(
                calendar_year=b.calendar_year,
                correctief_eur=b.correctief_eur * cf,
                preventief_eur=b.preventief_eur,
            )
            for b in built
        ]
    if pm_sum > 0 and not math.isclose(pm_sum, target_pm, rel_tol=0, abs_tol=1e-4):
        pf = target_pm / pm_sum
        built = [
            LCCYearBucket(
                calendar_year=b.calendar_year,
                correctief_eur=b.correctief_eur,
                preventief_eur=b.preventief_eur * pf,
            )
            for b in built
        ]

    return LCCScenarioCurve(scenario_key=scenario_key, label=label, buckets=tuple(built))


def build_single_run_lcc_input(project: RCMProject | None, run: RunResult | None) -> LCCChartInput | None:
    if project is None or run is None or run.status != "done" or not run.fm_core_results:
        return None
    curve = _curve_from_project_run(
        project=project,
        run=run,
        scenario_key="CURRENT_PROJECT",
        label="Huidig project",
    )
    if curve is None:
        return None
    return LCCChartInput(mode="single_run", cm_curve=None, pm_curve=None, single_curve=curve)


def build_compare_lcc_input(
    *,
    cm_project: RCMProject | None,
    cm_run: RunResult | None,
    pm_project: RCMProject | None,
    pm_run: RunResult | None,
) -> LCCChartInput | None:
    if (
        cm_project is None
        or pm_project is None
        or cm_run is None
        or pm_run is None
        or cm_run.status != "done"
        or pm_run.status != "done"
        or not cm_run.fm_core_results
        or not pm_run.fm_core_results
    ):
        return None
    cm_curve = _curve_from_project_run(
        project=cm_project,
        run=cm_run,
        scenario_key="CM",
        label="CM-scenario",
    )
    pm_curve = _curve_from_project_run(
        project=pm_project,
        run=pm_run,
        scenario_key="PM",
        label="PM-scenario",
    )
    if cm_curve is None or pm_curve is None:
        return None
    return LCCChartInput(mode="compare", cm_curve=cm_curve, pm_curve=pm_curve, single_curve=None)


def sum_correctief_preventief(curve: LCCScenarioCurve | None) -> tuple[float, float, float]:
    """Som over buckets: (correctief, preventief, totaal)."""
    if curve is None:
        return 0.0, 0.0, 0.0
    sc = sum(b.correctief_eur for b in curve.buckets)
    sp = sum(b.preventief_eur for b in curve.buckets)
    return sc, sp, sc + sp


def sum_cm_pm(curve: LCCScenarioCurve | None) -> tuple[float, float, float]:
    """Deprecated alias voor `sum_correctief_preventief` (semantiek: correctief/preventief)."""
    return sum_correctief_preventief(curve)
