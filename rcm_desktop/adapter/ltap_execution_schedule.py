"""LTAP PM-uitvoeringsschema per horizon-index (geen adapter-afhankelijkheden)."""

from __future__ import annotations

import math

from rcm_core.models import PMTask


def ltap_executions_by_year(
    task: PMTask,
    *,
    lifecycle_years: float,
    anchor_year: float,
) -> dict[int, int]:
    """Aantal PM-uitvoeringen per horizon-index onder LTAP-semantiek."""
    interval = float(task.interval_jaar)
    if interval <= 0:
        return {}
    first_k = math.ceil((0.0 - anchor_year) / interval)
    last_k = math.floor(((lifecycle_years - 1e-9) - anchor_year) / interval)
    out: dict[int, int] = {}
    if last_k < first_k:
        return out
    for k in range(first_k, last_k + 1):
        t = anchor_year + k * interval
        year = int(math.floor(t))
        out[year] = out.get(year, 0) + 1
    return out
