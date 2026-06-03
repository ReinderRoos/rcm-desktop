"""PNG-grafieken voor rapportexport zonder Qt (slice 57)."""

from __future__ import annotations

import io

from rcm_core.models import RCMProject

from rcm_desktop.adapter.lcc_planning_service import LCCPlanningCurve, build_lcc_planning_curve
from rcm_desktop.adapter.lcc_type_filter import LCCTypeFilterSet
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.run_service import RunResult
from rcm_desktop.adapter.unavailability_chart_service import (
    UnavailabilityChartInput,
    build_unavailability_chart_input,
)


def render_unavailability_chart_png(chart: UnavailabilityChartInput) -> bytes:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    years = [row.calendar_year for row in chart.rows]
    values = [row.unavailability_pct for row in chart.rows]
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.bar(years, values, color="#1565c0")
    ax.set_ylabel("Niet-beschikbaarheid %")
    ax.set_xlabel("Kalenderjaar")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120)
    plt.close(fig)
    return buf.getvalue()


def render_lcc_chart_png(curve: LCCPlanningCurve) -> bytes:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    buckets = curve.display_buckets
    years = [b.calendar_year for b in buckets]
    totals = [float(b.correctief_eur) + float(b.preventief_eur) for b in buckets]
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.bar(years, totals, color="#2e7d32")
    ax.set_ylabel("Kosten (EUR)")
    ax.set_xlabel("Kalenderjaar")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120)
    plt.close(fig)
    return buf.getvalue()


def build_project_lcc_curve(
    project: RCMProject,
    run: RunResult,
    overlay: PlanningOverlayState,
) -> LCCPlanningCurve | None:
    return build_lcc_planning_curve(
        project,
        run,
        scope_id=None,
        overlay=overlay,
        type_filters=LCCTypeFilterSet.all_on(),
    )


def build_project_unavailability_chart(
    project: RCMProject,
    run: RunResult,
) -> UnavailabilityChartInput | None:
    return build_unavailability_chart_input(project, run, scope_id=None)
