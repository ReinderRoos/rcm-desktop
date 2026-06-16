"""Slice 100 issue 03 — unified Start analyse (live run only, TDD)."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QMessageBox

from rcm_desktop.adapter.simulation_job_service import RunMode
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
from tests.test_desktop_results_workspace_window import _ensure_app


def test_start_analyse_button_visible_in_mc_mode(monkeypatch):
    """Start analyse stays visible in Monte Carlo modus (no slice-98 HILT hide)."""
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    assert window.run_analyse_button.isVisible() is True

    combo = window.simulation_run_mode_combo
    combo.setCurrentIndex(combo.findData(RunMode.MONTE_CARLO))
    app.processEvents()

    assert window.run_analyse_button.isVisible() is True


def test_dispatch_start_analyse_runs_mc_not_compare_slot(monkeypatch):
    """MC-modus: Start analyse dispatches live MC run, not Run A/B slot path."""
    from rcm_desktop.adapter.loaded_project import LoadedProject
    from rcm_desktop.views.panels.simulation_run_binding import dispatch_start_analyse
    import rcm_desktop.views.panels.simulation_run_binding as binding_mod
    from tests.test_desktop_results_workspace_window import _three_level_project

    project = _three_level_project()
    pending: list[str | None] = []

    class _Window:
        def __init__(self) -> None:
            self._pending_mc_compare_slot = None
            self.simulation_run_mode_combo = type(
                "Combo",
                (),
                {"currentData": lambda _self: RunMode.MONTE_CARLO},
            )()
            self._state = type("State", (), {"set_last_mc_run": lambda *_a, **_k: None})()
            self._simulation_result_store = None
            self._simulation_job = None
            self._run_runner = type("RR", (), {"start": lambda *_a, **_k: False, "busy": False})()

        def _project_session(self):
            from rcm_desktop.adapter.project_session import ProjectSession

            return ProjectSession.from_parts(LoadedProject.from_core(project))

        def _rerender_detail_for_current_scope(self) -> None:
            pass

        def _update_run_buttons_enabled(self) -> None:
            pass

        def _update_run_button_label(self) -> None:
            pass

    window = _Window()

    class _Runner:
        def start(self, *_a, **_k):
            pending.append(window._pending_mc_compare_slot)
            return True

    monkeypatch.setattr(binding_mod, "ensure_simulation_runner", lambda _w: _Runner())

    assert dispatch_start_analyse(window) is True
    assert pending == [None]


def test_mc_live_run_does_not_modify_frozen_compare_slots():
    """Geslaagde MC live run (Start analyse) laat bevroren compare-slots intact."""
    from rcm_core.simulation_engine import MetricBand
    from rcm_desktop.adapter.compare_slot_state import (
        COMPARE_SLOT_A,
        COMPARE_SLOT_B,
        CompareSlotSnapshot,
        CompareSlotState,
    )
    from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
    from rcm_desktop.adapter.run_service import RunMetrics, RunResult
    from rcm_desktop.adapter.simulation_engine_service import FMMCResultRow, MCRunResult
    from rcm_desktop.views.panels.simulation_run_binding import _on_mc_result_ready

    overlay = PlanningOverlayState.inactive()

    def _run(tag: str) -> RunResult:
        return RunResult(
            status="done",
            summary=tag,
            metrics=RunMetrics(
                fm_result_count=0,
                total_lifecycle_faalmomenten=0.0,
                total_cost_eur=0.0,
            ),
        )

    slots = CompareSlotState()
    snap_a = CompareSlotSnapshot.from_motor_run(
        run_result=_run("frozen-a"),
        presentation=None,
        scenario_key=None,
        overlay_at_run=overlay,
        label="frozen-a-label",
    )
    snap_b = CompareSlotSnapshot.from_motor_run(
        run_result=_run("frozen-b"),
        presentation=None,
        scenario_key="pm",
        overlay_at_run=overlay,
        label="frozen-b-label",
    )
    slots.put(COMPARE_SLOT_A, snap_a)
    slots.put(COMPARE_SLOT_B, snap_b)

    result = MCRunResult(
        status="done",
        seed=3,
        n_completed=50,
        rows=(
            FMMCResultRow(
                fm_id="FM-1",
                faalwijze_omschrijving="x",
                bouwdeel_naam="BD",
                failures_band=MetricBand(p10=1.0, p50=2.0, p90=3.0),
                downtime_band=MetricBand(p10=1.0, p50=2.0, p90=3.0),
                cost_band=MetricBand(p10=1.0, p50=2.0, p90=3.0),
                is_nmf=False,
                rf=0.0,
            ),
        ),
    )

    class _State:
        def set_last_mc_run(self, _mc):
            pass

    class _Window:
        _pending_mc_compare_slot = None
        _compare_mc_slots = None
        _state = _State()
        _simulation_result_store = None
        _compare_slots = slots

        def _rerender_detail_for_current_scope(self) -> None:
            pass

    _on_mc_result_ready(_Window(), result)

    assert slots.get(COMPARE_SLOT_A) is snap_a
    assert slots.get(COMPARE_SLOT_B) is snap_b


def test_cancelled_mc_run_leaves_live_views_empty():
    """Geannuleerde MC-run: live presentatiebron leeg, geen partial persist."""
    from rcm_core.config import RCMConfig
    from rcm_core.models import FailureType, Faalwijze, Functie, PBSItem, RCMProject
    from rcm_desktop.adapter.loaded_project import LoadedProject
    from rcm_desktop.adapter.project_session import ProjectSession
    from rcm_desktop.adapter.simulation_engine_service import MCRunResult
    from rcm_desktop.adapter.simulation_workspace_service import (
        fm_detail_source_for_run_mode,
        live_run_available,
        resolve_live_run_result,
    )

    cfg = RCMConfig(lifecycle_years=80.0, modeljaar=2026, monte_carlo_n=500)
    pbs = PBSItem("PBS-1", "Obj", "El", "BD", bouwjaar=2000)
    func = Functie("F-1", "PBS-1", "Functie")
    fm = Faalwijze(
        "FM-R",
        "PBS-1",
        "F-1",
        "Random",
        failure_type=FailureType.RANDOM,
        mttf_jaar=10.0,
        cost_cm_eur=500.0,
    )
    project = RCMProject(
        config=cfg,
        pbs_items={"PBS-1": pbs},
        functies={"F-1": func},
        faalwijzes={"FM-R": fm},
    )
    cancelled = MCRunResult(status="cancelled", seed=1, n_completed=10, rows=())
    session = ProjectSession.from_parts(
        LoadedProject.from_core(project),
        run=None,
        mc_run=cancelled,
    )

    assert not live_run_available(session, RunMode.MONTE_CARLO)
    assert resolve_live_run_result(session, RunMode.MONTE_CARLO) is None
    assert fm_detail_source_for_run_mode(RunMode.MONTE_CARLO, session) == "mc_cancelled"


def test_run_slot_ab_buttons_hidden(monkeypatch):
    """Slice 100: Run → A/B vervangen door unified Start analyse (knoppen verborgen)."""
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    assert window.run_slot_a_button.isVisible() is False
    assert window.run_slot_b_button.isVisible() is False
