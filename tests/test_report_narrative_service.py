from __future__ import annotations

import json
from pathlib import Path

from rcm_desktop import messages
from rcm_desktop.adapter.kpi_table_service import build_kpi_compare_table
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.report_narrative_service import build_kpi_narrative
from rcm_desktop.adapter.report_run_source_service import ReportRunBundle, ReportScenarioRun
from rcm_desktop.adapter.run_service import run as run_single
from rcm_core.models import RCMProject


def _sample_project() -> RCMProject:
    raw = json.loads(Path("tests/fixtures/sample_project.rcm.json").read_text(encoding="utf-8"))
    return RCMProject.from_dict(raw)


def test_kpi_narrative_warns_on_different_scenario_keys() -> None:
    project = _sample_project()
    run = run_single(project, Path("tests/fixtures/sample_project.rcm.json"))
    bundle = ReportRunBundle(
        mode="compare",
        scenarios=(
            ReportScenarioRun("A", "A", run, PlanningOverlayState.inactive(), None),
            ReportScenarioRun("B", "B", run, PlanningOverlayState.inactive(), "cm"),
        ),
    )
    table = build_kpi_compare_table(
        project=project,
        scenarios=(("A", "A", run), ("B", "B", run)),
        scope_id=None,
    )
    text = " ".join(build_kpi_narrative(bundle, table))
    assert messages.REPORT_NARRATIVE_SCENARIO_MISMATCH.split(".")[0] in text
