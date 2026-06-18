"""FM-niveau LCC-plot presentatie voor inspector (slice 108, ADR-0021)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_desktop.adapter.fm_verification_service import FMVerificationView
from rcm_desktop.adapter.lcc_chart_service import LCCYearBucket
from rcm_desktop.adapter.results_workspace_state import (
    METRIC_FAALMOMENTEN,
    METRIC_KOSTEN,
    METRIC_NIET_BESCHIKBAARHEID,
)


@dataclass(frozen=True)
class FmInspectorPlotView:
    buckets: tuple[LCCYearBucket, ...]
    y_axis_label: str


def build_fm_inspector_plot_view(
    view: FMVerificationView,
    *,
    metric: str,
) -> FmInspectorPlotView | None:
    if view.profile_missing or not view.year_rows:
        return None
    if metric == METRIC_KOSTEN:
        pm_total = float(view.lifecycle.pm_cost_eur)
        faal_sum = float(sum(r.faalmomenten for r in view.year_rows)) or 1.0
        buckets = tuple(
            LCCYearBucket(
                calendar_year=r.calendar_year,
                correctief_eur=float(r.cor_eur),
                preventief_eur=pm_total * (float(r.faalmomenten) / faal_sum),
            )
            for r in view.year_rows
        )
        return FmInspectorPlotView(buckets=buckets, y_axis_label="EUR")
    if metric == METRIC_FAALMOMENTEN:
        buckets = tuple(
            LCCYearBucket(
                calendar_year=r.calendar_year,
                correctief_eur=float(r.faalmomenten),
                preventief_eur=0.0,
            )
            for r in view.year_rows
        )
        return FmInspectorPlotView(buckets=buckets, y_axis_label="Faalmomenten")
    if metric == METRIC_NIET_BESCHIKBAARHEID:
        buckets = tuple(
            LCCYearBucket(
                calendar_year=r.calendar_year,
                correctief_eur=float(r.nb_downtime_hr),
                preventief_eur=0.0,
            )
            for r in view.year_rows
        )
        return FmInspectorPlotView(buckets=buckets, y_axis_label="NB (uur)")
    raise ValueError(f"Onbekende metric: {metric!r}")
