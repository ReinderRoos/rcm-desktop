"""CM vs PM KPI compare view (legacy scenario-vergelijker)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_desktop.adapter.result_view_service import FMResultRow
from rcm_desktop.adapter.run_service import RunResult


@dataclass(frozen=True)
class CompareKpi:
    key: str
    label: str
    cm_value: float
    pm_value: float
    delta_display: str
    cm_drivers: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScenarioCompareView:
    status: str
    kpis: tuple[CompareKpi, ...]


def _fmt_delta(cm_value: float, pm_value: float) -> str:
    delta = pm_value - cm_value
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta:.2f}"


def _unavailability_pct(run: RunResult) -> float:
    m = run.metrics
    years = float(m.lifecycle_years or 0.0)
    if years <= 0:
        return 0.0
    return float(m.total_downtime_hr) / years


def _cost_drivers(rows: list[FMResultRow]) -> tuple[str, ...]:
    ordered = sorted(rows, key=lambda r: (-abs(r.total_cost_eur), r.fm_id))
    return tuple(f"{row.fm_id}" for row in ordered[:5])


def build_compare_view(
    cm: RunResult | None,
    pm: RunResult | None,
) -> ScenarioCompareView:
    if cm is None or pm is None or cm.status != "done" or pm.status != "done":
        return ScenarioCompareView(status="error", kpis=())

    cm_m = cm.metrics
    pm_m = pm.metrics
    kpis = (
        CompareKpi(
            key="expected_failures",
            label="Faalmomenten",
            cm_value=cm_m.total_lifecycle_faalmomenten,
            pm_value=pm_m.total_lifecycle_faalmomenten,
            delta_display=_fmt_delta(
                cm_m.total_lifecycle_faalmomenten,
                pm_m.total_lifecycle_faalmomenten,
            ),
        ),
        CompareKpi(
            key="total_cost_eur",
            label="Kosten",
            cm_value=cm_m.total_cost_eur,
            pm_value=pm_m.total_cost_eur,
            delta_display=_fmt_delta(cm_m.total_cost_eur, pm_m.total_cost_eur),
            cm_drivers=_cost_drivers(cm.rows),
        ),
        CompareKpi(
            key="unavailability_pct",
            label="Niet-beschikbaarheid",
            cm_value=_unavailability_pct(cm),
            pm_value=_unavailability_pct(pm),
            delta_display=_fmt_delta(_unavailability_pct(cm), _unavailability_pct(pm)),
        ),
    )
    return ScenarioCompareView(status="done", kpis=kpis)
