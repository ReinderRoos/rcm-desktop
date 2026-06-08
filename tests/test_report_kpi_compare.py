from __future__ import annotations

import json
from pathlib import Path

from rcm_desktop.adapter.kpi_table_service import (
    KPI_DELTA_KEY,
    KPI_KEY_LIFECYCLE_COSTS_EUR,
    KPI_KEY_UNAVAILABILITY_PCT,
    build_kpi_compare_table,
)
from rcm_desktop.adapter.run_service import run as run_single
from rcm_core.models import RCMProject


def _sample_project() -> RCMProject:
    raw = json.loads(Path("tests/fixtures/sample_project.rcm.json").read_text(encoding="utf-8"))
    return RCMProject.from_dict(raw)


def test_compare_kpi_table_has_delta_column() -> None:
    project = _sample_project()
    path = Path("tests/fixtures/sample_project.rcm.json")
    run = run_single(project, path)
    table = build_kpi_compare_table(
        project=project,
        scenarios=(("A", "Scenario A", run), ("B", "Scenario B", run)),
        scope_id=None,
    )
    assert KPI_DELTA_KEY in table.scenario_keys
    nb_row = next(r for r in table.rows if r.key == KPI_KEY_UNAVAILABILITY_PCT)
    assert len(nb_row.cells) == 3
    cost_row = next(r for r in table.rows if r.key == KPI_KEY_LIFECYCLE_COSTS_EUR)
    assert len(cost_row.cells) == 3
    assert nb_row.cells[-1].raw == 0.0
