"""Slice 101 — live Top10/LCC after MC-only run (no analytical session.run)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from rcm_core.persistence import load_project

from rcm_core.engine import compute_all_fm_results

from rcm_desktop.adapter.loaded_project import LoadedProject
from rcm_desktop.adapter.presentation_cache_service import (
    PresentationProjectTotal,
    build_project_total_presentation,
)
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.run_service import build_run_result
from rcm_desktop.adapter.results_workspace_state import (
    MODE_BIJDRAGEN,
    MODE_LCC,
    METRIC_KOSTEN,
    _DEFAULT_SNAPSHOT,
)
from rcm_desktop.adapter.simulation_engine_service import run_monte_carlo
from rcm_desktop.adapter.simulation_job_service import RunMode
from rcm_desktop.adapter.workspace_render_index import WorkspaceRenderIndex
from rcm_desktop.adapter.workspace_view_service import build_bijdragen_view, build_lcc_view


def _mc_only_session() -> ProjectSession:
    project = load_project(Path("tests/fixtures/sample_project.rcm.json"))
    mc = run_monte_carlo(project, n=200, seed=99)
    return ProjectSession.from_parts(LoadedProject.from_core(project), run=None, mc_run=mc)


def test_build_bijdragen_view_mc_skips_analytical_presentation_cache() -> None:
    session = _mc_only_session()
    project = session.loaded.core()
    anal_run = build_run_result(project, list(compute_all_fm_results(project).values()))
    anal_presentation = build_project_total_presentation(project, anal_run)
    assert isinstance(anal_presentation, PresentationProjectTotal)
    snapshot = replace(_DEFAULT_SNAPSHOT, modus=MODE_BIJDRAGEN)
    render_index = WorkspaceRenderIndex()

    view = build_bijdragen_view(
        session,
        snapshot,
        render_index=render_index,
        project_total_presentation=anal_presentation,
        run_mode=RunMode.MONTE_CARLO,
    )

    assert view is not None
    assert not view.from_presentation_cache
    assert len(view.contribution_rows) > 0


def test_build_lcc_view_mc_only_without_analytical_run() -> None:
    session = _mc_only_session()
    snapshot = replace(_DEFAULT_SNAPSHOT, modus=MODE_LCC, metric=METRIC_KOSTEN)

    view = build_lcc_view(
        session,
        snapshot,
        render_index=WorkspaceRenderIndex(),
        prev_snapshot=None,
        run_mode=RunMode.MONTE_CARLO,
    )

    assert view is not None
    assert view.curve is not None
    assert view.curve.display_buckets
