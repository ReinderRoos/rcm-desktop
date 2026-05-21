"""PM jaargrafiek-input (presentatie, Qt-vrij)."""
from __future__ import annotations

import math
from dataclasses import dataclass

from rcm_core.lcc_profile import ltap_horizon_bucket_count
from rcm_core.models import RCMProject

from rcm_desktop.adapter.calendar_year import calendar_year_for_horizon_index
from rcm_desktop.adapter.lcc_chart_service import _pm_eur_per_bucket_ltap
from rcm_desktop.adapter.ltap_service import build_ltap_view
from rcm_desktop.adapter.result_filter_service import collect_pbs_subtree_ids
from rcm_desktop.adapter.run_service import RunResult

PM_SUBMODE_KOSTEN = "kosten"
PM_SUBMODE_AANTAL_UITVOERINGEN = "aantal_uitvoeringen"
ALL_PM_SUBMODES: tuple[str, ...] = (
    PM_SUBMODE_KOSTEN,
    PM_SUBMODE_AANTAL_UITVOERINGEN,
)


@dataclass(frozen=True)
class PMYearRow:
    calendar_year: int
    value: float
    cumulative: float


@dataclass(frozen=True)
class PMChartInput:
    submode: str
    scope_id: str | None
    rows: tuple[PMYearRow, ...]


def build_pm_chart_input(
    project: RCMProject | None,
    run: RunResult | None,
    *,
    submode: str,
    scope_id: str | None = None,
) -> PMChartInput | None:
    if project is None or run is None or run.status != "done":
        return None
    if submode not in ALL_PM_SUBMODES:
        raise ValueError(f"Onbekende PM-submode: {submode!r}")

    if scope_id is None:
        fm_subset = run.fm_core_results
        pbs_filter = None
    elif scope_id not in project.pbs_items:
        return PMChartInput(submode=submode, scope_id=scope_id, rows=())
    else:
        subtree = collect_pbs_subtree_ids(project, scope_id)
        fm_subset = tuple(fr for fr in run.fm_core_results if fr.pbs_id in subtree)
        pbs_filter = subtree

    num = ltap_horizon_bucket_count(float(project.config.lifecycle_years))
    if num <= 0:
        return PMChartInput(submode=submode, scope_id=scope_id, rows=())

    if submode == PM_SUBMODE_KOSTEN:
        target = sum(float(fr.pm_cost_eur) for fr in fm_subset)
        per_year = _pm_eur_per_bucket_ltap(project, target)
    else:
        view = build_ltap_view(project, fm_pbs_ids=pbs_filter)
        target = float(view.total_task_count)
        per_year = [float(y.task_count) for y in view.years]

    if len(per_year) < num:
        per_year = per_year + [0.0] * (num - len(per_year))
    per_year = per_year[:num]

    if submode == PM_SUBMODE_KOSTEN:
        got = float(sum(per_year))
        if got > 0.0 and not math.isclose(got, target, rel_tol=0, abs_tol=1e-3):
            scale = target / got
            per_year = [v * scale for v in per_year]

    modeljaar = int(project.config.modeljaar)
    rows: list[PMYearRow] = []
    cumulative = 0.0
    for h, value in enumerate(per_year):
        cumulative += float(value)
        rows.append(
            PMYearRow(
                calendar_year=calendar_year_for_horizon_index(modeljaar, h),
                value=float(value),
                cumulative=cumulative,
            )
        )
    return PMChartInput(submode=submode, scope_id=scope_id, rows=tuple(rows))
