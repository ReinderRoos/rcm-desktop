"""Row-mappers voor FM-edit buffer (Qt-vrij)."""

from __future__ import annotations

from typing import Any


def downtime_hours_from_row(row: dict[str, Any]) -> float:
    raw = row.get("downtime_per_failure")
    if not isinstance(raw, dict):
        return 0.0
    from rcm_core.units import TimeDuration

    return TimeDuration.from_dict(raw).to_hours()


def downtime_dict_from_hours(hours: float) -> dict[str, Any]:
    return {"value": float(hours), "unit": "uur"}
