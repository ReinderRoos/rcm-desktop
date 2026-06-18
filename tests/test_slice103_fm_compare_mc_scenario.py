"""Slice 103 issue 06 — FM compare panels reflecteren slot-specifieke MC P50 (regressietest).

HILT103 B4: na Extra scenario + wijziging + MC-run scenario 2 toonde FM compare
exact dezelfde waarden voor beide slots, ook al hadden de MC runs verschillende
failures.p50. Oorzaak: _faalmomenten_scalar berekende de jaargemiddelde via de
analytische motor van het live project (zelfde voor beide slots), in plaats van via
fmr.expected_failures (slot-specifiek MC P50 totaal).
"""
from __future__ import annotations

from rcm_core.simulation_engine import FMMCResult, MetricBand

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
from rcm_desktop.adapter.simulation_engine_service import (
    FMMCResultRow,
    MCRunResult,
    build_run_result_from_mc_p50,
)

from tests.test_desktop_results_workspace_window import _three_level_project


def _make_mc_run(fm_id: str, pbs_id: str, failures_p50: float) -> MCRunResult:
    mc_fm = FMMCResult(
        fm_id=fm_id,
        pbs_id=pbs_id,
        failures=MetricBand(
            p10=failures_p50 * 0.5,
            p50=failures_p50,
            p90=failures_p50 * 1.5,
        ),
        downtime_hr=MetricBand(p10=10.0, p50=20.0, p90=30.0),
        total_cost_eur=MetricBand(p10=500.0, p50=1000.0, p90=1500.0),
        n_completed=500,
        seed=42,
    )
    row = FMMCResultRow(
        fm_id=fm_id,
        faalwijze_omschrijving="Testfaalwijze",
        bouwdeel_naam="BD-test",
        failures_band=MetricBand(
            p10=failures_p50 * 0.5,
            p50=failures_p50,
            p90=failures_p50 * 1.5,
        ),
        downtime_band=MetricBand(p10=10.0, p50=20.0, p90=30.0),
        cost_band=MetricBand(p10=500.0, p50=1000.0, p90=1500.0),
        is_nmf=False,
        rf=0.0,
    )
    return MCRunResult(
        status="done",
        seed=42,
        n_completed=500,
        fm_results={fm_id: mc_fm},
        rows=(row,),
    )


def test_fm_compare_panels_mc_slots_reflect_slot_specific_p50():
    """FM compare panels moeten slot-specifieke failures_band.p50 tonen vanuit MC resultaten.

    Regressie voor HILT103 B4: met per_year+average presentatie berekende
    _faalmomenten_scalar de buckets via de analytische motor van het live project
    (identiek voor beide slots), waardoor display_failures voor beide panels gelijk was.
    Fix: schaal analytische buckets met fmr.expected_failures / sum(buckets).
    """
    project = _three_level_project()
    fm_id = next(iter(project.faalwijzes))
    pbs_id = project.faalwijzes[fm_id].pbs_id

    # Twee MC-runs met 5× verschillende failures P50
    mc_low = _make_mc_run(fm_id, pbs_id, failures_p50=2.0)
    mc_high = _make_mc_run(fm_id, pbs_id, failures_p50=10.0)

    session = ProjectSession.from_parts(LoadedProject.from_core(project))
    overlay = PlanningOverlayState.inactive()
    run_low = build_run_result_from_mc_p50(project, mc_low)
    run_high = build_run_result_from_mc_p50(project, mc_high)

    slots = CompareSlotState()
    slots.put(
        COMPARE_SLOT_A,
        CompareSlotSnapshot.from_mc_run(
            mc_run=mc_low,
            run_result=run_low,
            presentation=None,
            scenario_key=None,
            overlay_at_run=overlay,
            label="S1 low",
        ),
    )
    slots.put(
        COMPARE_SLOT_B,
        CompareSlotSnapshot.from_mc_run(
            mc_run=mc_high,
            run_result=run_high,
            presentation=None,
            scenario_key=None,
            overlay_at_run=overlay,
            label="S2 high",
        ),
    )

    # _DEFAULT_SNAPSHOT uses ContributionPresentation(horizon="per_year", year_choice="average")
    # — the exact presentation that triggered the bug
    panels = build_fm_compare_panels(session, _DEFAULT_SNAPSHOT, slots=slots)
    assert len(panels) == 2
    assert panels[0].fm is not None and panels[0].fm.is_mc_mode
    assert panels[1].fm is not None and panels[1].fm.is_mc_mode
    assert panels[0].fm.mc_rows, "Slot A moet mc_rows hebben"
    assert panels[1].fm.mc_rows, "Slot B moet mc_rows hebben"

    p50_a = panels[0].fm.mc_rows[0].failures_band.p50
    p50_b = panels[1].fm.mc_rows[0].failures_band.p50
    assert p50_a != p50_b, (
        f"FM compare panels moeten slot-specifieke MC P50 reflecteren, "
        f"maar beide tonen {p50_a:.4f}. "
        f"Bug: analytisch model van live project in _faalmomenten_scalar gebruikt "
        f"in plaats van fmr.expected_failures (slot-specifiek MC totaal)."
    )
    assert p50_b > p50_a, (
        f"S2 high ({p50_b:.4f}) moet groter zijn dan S1 low ({p50_a:.4f})"
    )
