"""Qt-vrije builder voor de gedeelde KPI-tabel boven de grafiek-zone.

Bouwt één kolom "Huidige analyse" met vier KPI-rijen:
1. Lifecycle faalmomenten;
2. Niet-beschikbaarheid (% van bedrijfstijd);
3. Lifecycle kosten (EUR);
4. PM-taken actief (count).

Rijen 1-3 respecteren de actieve `scope_id`. Rij 4 is projectniveau.
"""
from __future__ import annotations

from dataclasses import dataclass

from rcm_core.models import RCMProject

from rcm_desktop.adapter.run_service import RunResult
from rcm_desktop.formatting import format_eur, format_float, format_int

EM_DASH = "—"

KPI_KEY_LIFECYCLE_FAILURES = "lifecycle_failures"
KPI_KEY_UNAVAILABILITY_PCT = "unavailability_pct"
KPI_KEY_LIFECYCLE_COSTS_EUR = "lifecycle_costs_eur"
KPI_KEY_PM_TASKS_ACTIVE = "pm_tasks_active"

CURRENT_ANALYSIS_KEY = "current"
CURRENT_ANALYSIS_LABEL = "Huidige analyse"

KPI_DELTA_KEY = "delta"
KPI_DELTA_LABEL = "Δ (abs.)"

_DELTA_KEYS = frozenset({KPI_KEY_UNAVAILABILITY_PCT, KPI_KEY_LIFECYCLE_COSTS_EUR})

_HOURS_PER_YEAR = 8760.0


@dataclass(frozen=True)
class KPICell:
    raw: float | int | None
    display: str


@dataclass(frozen=True)
class KPIRow:
    key: str
    label: str
    cells: tuple[KPICell, ...]


@dataclass(frozen=True)
class KPITable:
    scenario_keys: tuple[str, ...]
    scenario_labels: tuple[str, ...]
    rows: tuple[KPIRow, ...]


def build_kpi_table(
    *,
    project: RCMProject | None,
    run_result: RunResult | None,
    scope_id: str | None,
) -> KPITable:
    """Bouw de KPI-tabel voor de actieve analyse."""
    subtree: frozenset[str] | None
    if scope_id is not None and project is not None and scope_id in project.pbs_items:
        subtree = _collect_subtree_ids(project, scope_id)
    else:
        subtree = None

    aggregate = _aggregate_run(run_result, project=project, subtree=subtree)
    rows = (
        _build_row(
            KPI_KEY_LIFECYCLE_FAILURES,
            "Lifecycle faalmomenten",
            aggregate,
            formatter=_format_failures,
        ),
        _build_row(
            KPI_KEY_UNAVAILABILITY_PCT,
            "Niet-beschikbaarheid (%)",
            aggregate,
            formatter=_format_pct,
        ),
        _build_row(
            KPI_KEY_LIFECYCLE_COSTS_EUR,
            "Lifecycle kosten (EUR)",
            aggregate,
            formatter=_format_eur,
        ),
        _build_row(
            KPI_KEY_PM_TASKS_ACTIVE,
            "PM-taken actief",
            aggregate,
            formatter=_format_int,
        ),
    )
    return KPITable(
        scenario_keys=(CURRENT_ANALYSIS_KEY,),
        scenario_labels=(CURRENT_ANALYSIS_LABEL,),
        rows=rows,
    )


def build_kpi_compare_table(
    *,
    project: RCMProject | None,
    scenarios: tuple[tuple[str, str, RunResult], ...],
    scope_id: str | None,
) -> KPITable:
    """KPI-tabel voor rapport of compare met optionele Δ-kolom."""
    if not scenarios:
        return build_kpi_table(project=project, run_result=None, scope_id=scope_id)

    subtree: frozenset[str] | None
    if scope_id is not None and project is not None and scope_id in project.pbs_items:
        subtree = _collect_subtree_ids(project, scope_id)
    else:
        subtree = None

    aggregates = [
        _aggregate_run(run, project=project, subtree=subtree) for _key, _label, run in scenarios
    ]
    keys = tuple(key for key, _label, _run in scenarios)
    labels = tuple(label for _key, label, _run in scenarios)
    scenario_keys: tuple[str, ...]
    scenario_labels: tuple[str, ...]
    if len(scenarios) >= 2:
        scenario_keys = keys + (KPI_DELTA_KEY,)
        scenario_labels = labels + (KPI_DELTA_LABEL,)
    else:
        scenario_keys = keys
        scenario_labels = labels

    row_defs = (
        (KPI_KEY_LIFECYCLE_FAILURES, "Lifecycle faalmomenten", _format_failures),
        (KPI_KEY_UNAVAILABILITY_PCT, "Niet-beschikbaarheid (%)", _format_pct),
        (KPI_KEY_LIFECYCLE_COSTS_EUR, "Lifecycle kosten (EUR)", _format_eur),
        (KPI_KEY_PM_TASKS_ACTIVE, "PM-taken actief", _format_int),
    )
    rows: list[KPIRow] = []
    for row_key, row_label, formatter in row_defs:
        cells: list[KPICell] = []
        for agg in aggregates:
            value = agg.get(row_key)
            if value is None:
                cells.append(KPICell(raw=None, display=EM_DASH))
            else:
                cells.append(KPICell(raw=value, display=formatter(value)))
        if len(scenarios) >= 2 and row_key in _DELTA_KEYS:
            left = aggregates[0].get(row_key)
            right = aggregates[1].get(row_key)
            if left is None or right is None:
                cells.append(KPICell(raw=None, display=EM_DASH))
            else:
                delta = float(right) - float(left)
                cells.append(KPICell(raw=delta, display=formatter(delta)))
        rows.append(KPIRow(key=row_key, label=row_label, cells=tuple(cells)))

    return KPITable(
        scenario_keys=scenario_keys,
        scenario_labels=scenario_labels,
        rows=tuple(rows),
    )


def _aggregate_run(
    run_result: RunResult | None,
    *,
    project: RCMProject | None,
    subtree: frozenset[str] | None,
) -> dict[str, float | int | None]:
    if run_result is None or run_result.status != "done":
        return {
            KPI_KEY_LIFECYCLE_FAILURES: None,
            KPI_KEY_UNAVAILABILITY_PCT: None,
            KPI_KEY_LIFECYCLE_COSTS_EUR: None,
            KPI_KEY_PM_TASKS_ACTIVE: None,
        }
    if subtree is None:
        failures = float(run_result.metrics.total_lifecycle_faalmomenten)
        cost = float(run_result.metrics.total_cost_eur)
        downtime_hr = float(run_result.metrics.total_downtime_hr)
        lifecycle_years = float(run_result.metrics.lifecycle_years) or _project_lifecycle_years(
            project
        )
    else:
        failures = 0.0
        cost = 0.0
        downtime_hr = 0.0
        for fr in run_result.fm_core_results:
            if fr.pbs_id in subtree:
                failures += float(fr.expected_failures)
                cost += float(fr.total_cost_eur)
                downtime_hr += float(fr.expected_total_downtime_hr) + float(
                    fr.expected_pm_downtime_hr
                )
        lifecycle_years = float(run_result.metrics.lifecycle_years) or _project_lifecycle_years(
            project
        )
    pct = (
        (downtime_hr / (_HOURS_PER_YEAR * lifecycle_years)) * 100.0
        if lifecycle_years > 0
        else 0.0
    )
    pm_active = len(project.pm_tasks) if project is not None else None
    return {
        KPI_KEY_LIFECYCLE_FAILURES: failures,
        KPI_KEY_UNAVAILABILITY_PCT: pct,
        KPI_KEY_LIFECYCLE_COSTS_EUR: cost,
        KPI_KEY_PM_TASKS_ACTIVE: pm_active,
    }


def _project_lifecycle_years(project: RCMProject | None) -> float:
    if project is None:
        return 0.0
    return float(project.config.lifecycle_years)


def _build_row(
    key: str,
    label: str,
    aggregate: dict[str, float | int | None],
    *,
    formatter,
) -> KPIRow:
    value = aggregate.get(key)
    if value is None:
        cell = KPICell(raw=None, display=EM_DASH)
    else:
        cell = KPICell(raw=value, display=formatter(value))
    return KPIRow(key=key, label=label, cells=(cell,))


def _format_failures(value: float) -> str:
    return format_float(value)


def _format_pct(value: float) -> str:
    return f"{format_float(value, decimals=4)} %"


def _format_eur(value: float) -> str:
    return format_eur(value)


def _format_int(value: float | int) -> str:
    return format_int(int(round(value)))


def _collect_subtree_ids(project: RCMProject, scope_id: str) -> frozenset[str]:
    children: dict[str, list[str]] = {}
    for pid, item in project.pbs_items.items():
        if item.parent_pbs_id is None:
            continue
        if item.parent_pbs_id not in project.pbs_items:
            continue
        children.setdefault(item.parent_pbs_id, []).append(pid)
    collected: set[str] = set()
    stack: list[str] = [scope_id]
    while stack:
        current = stack.pop()
        if current in collected:
            continue
        collected.add(current)
        for child_id in children.get(current, ()):
            if child_id not in collected:
                stack.append(child_id)
    return frozenset(collected)
