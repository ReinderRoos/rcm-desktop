"""PM-uitvoeringsschema — pure planningslogica gedeeld door motor en UI (slice 84)."""

from __future__ import annotations

import math

from rcm_core.models import PMTask


def pm_execution_years(
    interval_years: float,
    *,
    lifecycle_years: float,
    anchor_year: float = 0.0,
) -> tuple[float, ...]:
    """Horizon-relatieve uitvoeringstijden binnen de LCC-periode."""
    interval = float(interval_years)
    if interval <= 0:
        return ()
    first_k = math.ceil((0.0 - float(anchor_year)) / interval)
    last_k = math.floor(((float(lifecycle_years) - 1e-9) - float(anchor_year)) / interval)
    if last_k < first_k:
        return ()
    return tuple(float(anchor_year) + k * interval for k in range(first_k, last_k + 1))


def pm_execution_count(
    interval_years: float,
    *,
    lifecycle_years: float,
    anchor_year: float = 0.0,
) -> int:
    """Aantal PM-uitvoeringen binnen de LCC-periode."""
    return len(pm_execution_years(interval_years, lifecycle_years=lifecycle_years, anchor_year=anchor_year))


def pm_first_execution_year(
    interval_years: float,
    *,
    lifecycle_years: float,
    anchor_year: float = 0.0,
) -> float | None:
    """Eerste horizon-relatieve uitvoeringstijd, of None bij geen uitvoeringen."""
    years = pm_execution_years(interval_years, lifecycle_years=lifecycle_years, anchor_year=anchor_year)
    return years[0] if years else None


def pm_executions_by_horizon_year(
    task: PMTask,
    *,
    lifecycle_years: float,
    anchor_year: float = 0.0,
) -> dict[int, int]:
    """Aantal PM-uitvoeringen per horizon-index (LTAP-raster)."""
    interval = float(task.interval_jaar)
    if interval <= 0:
        return {}
    out: dict[int, int] = {}
    for t in pm_execution_years(interval, lifecycle_years=lifecycle_years, anchor_year=anchor_year):
        year = int(math.floor(t))
        out[year] = out.get(year, 0) + 1
    return out
