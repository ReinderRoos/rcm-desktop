"""Afgeleide kolomwaarden voor entiteiten-grid (presentatie, geen schema-velden)."""

from __future__ import annotations

import math
from typing import Any

from rcm_core.models import RCMProject
from rcm_core.pm_schedule import pm_execution_count, pm_first_execution_year

from rcm_desktop.adapter.calendar_year import calendar_year_for_horizon_index
from rcm_desktop.adapter.entity_grid_config import entity_grid_config_for_view
from rcm_desktop import messages


def entity_derived_column_ids(view_id: str) -> frozenset[str]:
    cfg = entity_grid_config_for_view(view_id)
    if cfg is None:
        return frozenset()
    return cfg.derived_columns


def entity_derived_header(view_id: str, column_id: str) -> str:
    if column_id == "pm_first_execution_year":
        return messages.ENTITY_GRID_PM_FIRST_EXECUTION_YEAR
    if column_id == "pm_execution_count_lcc":
        return messages.ENTITY_GRID_PM_EXECUTION_COUNT_LCC
    if column_id == "pm_downtime_oh":
        return messages.ENTITY_GRID_PM_DOWNTIME_OH
    if column_id == "pm_repair_quality":
        return messages.ENTITY_GRID_PM_REPAIR_QUALITY
    if column_id == "pm_herstelduur":
        return messages.ENTITY_GRID_PM_HERSTELDUUR
    return column_id


def entity_derived_value(
    view_id: str,
    column_id: str,
    project: RCMProject,
    row_values: dict[str, Any],
) -> Any:
    if column_id in ("pm_first_execution_year", "pm_execution_count_lcc"):
        return _pm_schedule_derived(view_id, column_id, project, row_values)
    if column_id == "pm_downtime_oh":
        return _pm_downtime_oh_display(project, row_values)
    if column_id == "pm_repair_quality":
        return _pm_repair_quality_display(project, row_values)
    if column_id == "pm_herstelduur":
        return _pm_herstelduur_display(row_values)
    return None


def _pm_schedule_derived(
    view_id: str,
    column_id: str,
    project: RCMProject,
    row_values: dict[str, Any],
) -> Any:
    if view_id != "input.rev_tasks":
        return None
    interval = float(row_values.get("interval_jaar") or 0.0)
    lifecycle = float(project.config.lifecycle_years)
    anchor = 0.0
    if column_id == "pm_first_execution_year":
        first = pm_first_execution_year(interval, lifecycle_years=lifecycle, anchor_year=anchor)
        if first is None:
            return None
        horizon = int(math.floor(first))
        return calendar_year_for_horizon_index(int(project.config.modeljaar), horizon)
    if column_id == "pm_execution_count_lcc":
        return pm_execution_count(interval, lifecycle_years=lifecycle, anchor_year=anchor)
    return None


def _pm_downtime_oh_display(project: RCMProject, row_values: dict[str, Any]) -> str:
    pm_id = str(row_values.get("pm_id") or "")
    if not pm_id:
        return ""
    parts: list[str] = []
    for link in project.get_pm_effect_links_for_pm(pm_id):
        klasse = project.effect_klassen.get(link.klasse_id)
        label = link.klasse_id
        if klasse is not None and klasse.omschrijving:
            label = f"{link.klasse_id}: {klasse.omschrijving}"
        parts.append(f"{label} RF={link.fractie:g}")
    return "; ".join(parts)


def _pm_repair_quality_display(project: RCMProject, row_values: dict[str, Any]) -> str:
    fm_id = str(row_values.get("fm_id") or "")
    fm = project.faalwijzes.get(fm_id)
    if fm is None:
        return ""
    return f"{fm.repair_quality:g}"


def _pm_herstelduur_display(row_values: dict[str, Any]) -> str:
    duration = row_values.get("duration")
    if duration is None:
        return ""
    if hasattr(duration, "to_hours"):
        hours = duration.to_hours()
    elif isinstance(duration, dict):
        from rcm_core.models import TimeDuration

        hours = TimeDuration.from_dict(duration).to_hours()
    else:
        return str(duration)
    return f"{hours:g} uur"
