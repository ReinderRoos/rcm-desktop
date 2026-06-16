"""Slice 101 issue 06 — lifecycle / per-year MC FM parity with analytical presentation."""

from __future__ import annotations

from pathlib import Path

import pytest

from rcm_core.engine import compute_all_fm_results
from rcm_core.persistence import load_project

from rcm_desktop.adapter.result_view_service import (
    apply_presentation_scale_to_fm_rows,
    apply_presentation_scale_to_mc_rows,
    build_rows,
)
from rcm_desktop.adapter.results_workspace_state import ContributionPresentation
from rcm_desktop.adapter.simulation_engine_service import run_monte_carlo


def test_per_year_cost_matches_analytical_when_mc_p50_equals_engine() -> None:
    project = load_project(Path("tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json"))
    mc = run_monte_carlo(project, n=500, seed=42)
    pres = ContributionPresentation(horizon="per_year", year_choice="average")
    fm_anal = list(compute_all_fm_results(project).values())
    anal_rows = apply_presentation_scale_to_fm_rows(
        project,
        fm_anal,
        build_rows(project, fm_anal),
        presentation=pres,
        nb_filter=None,
    )
    mc_rows = apply_presentation_scale_to_mc_rows(
        project, mc, mc.rows, presentation=pres, nb_filter=None
    )
    anal_by_id = {r.fm_id: r for r in anal_rows}
    mc_by_id = {r.fm_id: r for r in mc_rows}
    a = anal_by_id["FM-016"]
    m = mc_by_id["FM-016"]
    assert m.cost_band.p50 == pytest.approx(a.total_cost_eur, rel=0.05)


def test_lifecycle_mixed_compare_cost_ratio_plausible_on_haarlem() -> None:
    from dataclasses import replace

    from rcm_desktop.adapter.compare_slot_state import (
        COMPARE_SLOT_A,
        COMPARE_SLOT_B,
        CompareSlotSnapshot,
        CompareSlotState,
    )
    from rcm_desktop.adapter.compare_view_service import build_fm_compare_panels
    from rcm_desktop.adapter.loaded_project import LoadedProject
    from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
    from rcm_desktop.adapter.project_session import ProjectSession
    from rcm_desktop.adapter.results_workspace_state import _DEFAULT_SNAPSHOT
    from rcm_desktop.adapter.run_service import build_run_result
    from rcm_desktop.adapter.simulation_engine_service import build_run_result_from_mc_p50

    project = load_project(Path("tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json"))
    mc = run_monte_carlo(project, n=500, seed=42)
    mc_run = build_run_result_from_mc_p50(project, mc)
    anal_run = build_run_result(project, list(compute_all_fm_results(project).values()))
    slots = CompareSlotState()
    overlay = PlanningOverlayState.inactive()
    slots.put(
        COMPARE_SLOT_A,
        CompareSlotSnapshot.from_motor_run(
            run_result=anal_run,
            presentation=None,
            scenario_key=None,
            overlay_at_run=overlay,
            label="Analytical",
        ),
    )
    slots.put(
        COMPARE_SLOT_B,
        CompareSlotSnapshot.from_mc_run(
            mc_run=mc,
            run_result=mc_run,
            presentation=None,
            scenario_key=None,
            overlay_at_run=overlay,
            label="MC",
        ),
    )
    session = ProjectSession.from_parts(
        LoadedProject.from_core(project), run=anal_run, mc_run=mc
    )
    ws = replace(
        _DEFAULT_SNAPSHOT,
        contribution_presentation=ContributionPresentation(horizon="lifecycle"),
    )
    panels = build_fm_compare_panels(session, ws, slots=slots)
    anal_by_id = {r.fm_id: r for r in panels[0].fm.fm_rows}
    mc_by_id = {r.fm_id: r for r in panels[1].fm.mc_rows}
    worst = 0.0
    for fm_id, a in anal_by_id.items():
        m = mc_by_id.get(fm_id)
        if m is None or a.total_cost_eur <= 100.0:
            continue
        ratio = m.cost_band.p50 / a.total_cost_eur
        worst = max(worst, ratio, 1.0 / ratio if ratio > 0 else 0.0)
    assert worst < 3.0, f"lifecycle FM cost ratio {worst} suggests presentation mismatch"
