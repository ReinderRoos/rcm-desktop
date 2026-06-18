from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("matplotlib")

from rcm_desktop import messages
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.report_materialization_service import materialize_report
from rcm_desktop.adapter.report_options import ReportOptions
from rcm_desktop.adapter.report_run_source_service import ReportRunBundle, ReportScenarioRun
from rcm_desktop.adapter.run_service import run as run_single
from rcm_core.models import RCMProject


def _sample_project() -> RCMProject:
    raw = json.loads(Path("tests/fixtures/sample_project.rcm.json").read_text(encoding="utf-8"))
    return RCMProject.from_dict(raw)


def _single_bundle(project, run) -> ReportRunBundle:
    return ReportRunBundle(
        mode="single",
        scenarios=(
            ReportScenarioRun(
                key="current",
                label="Test",
                run_result=run,
                overlay_at_run=PlanningOverlayState.inactive(),
                scenario_key=None,
            ),
        ),
    )


def test_materialize_report_has_cover_and_kpi_first(tmp_path: Path) -> None:
    project = _sample_project()
    path = Path("tests/fixtures/sample_project.rcm.json")
    run = run_single(project, path)
    options = ReportOptions(output_docx_path=tmp_path / "out.docx")
    doc = materialize_report(project, _single_bundle(project, run), options)
    titles = doc.section_titles()
    assert titles[0] == messages.REPORT_SECTION_COVER
    assert messages.REPORT_SECTION_KPI in titles


def test_materialize_includes_project_chart_sections() -> None:
    project = _sample_project()
    run = run_single(project, Path("tests/fixtures/sample_project.rcm.json"))
    options = ReportOptions(output_docx_path=Path("x.docx"))
    doc = materialize_report(project, _single_bundle(project, run), options)
    joined = " ".join(doc.section_titles())
    assert messages.REPORT_SECTION_PROJECT_NB.split(" —")[0] in joined or "Project" in joined
