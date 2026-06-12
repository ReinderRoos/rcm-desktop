"""LTAP PM-uitvoeringsschema — adapter-re-export van ``rcm_core.pm_schedule``."""

from __future__ import annotations

from rcm_core.pm_schedule import pm_executions_by_horizon_year as ltap_executions_by_year

__all__ = ["ltap_executions_by_year"]
