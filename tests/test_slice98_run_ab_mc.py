"""Slice 98 — Run A/B MC dispatch and Start-analyse visibility."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QMessageBox

from rcm_core.simulation_engine import MetricBand
from rcm_desktop.adapter.compare_mc_slot_state import CompareMcSlotState
from rcm_desktop.adapter.compare_slot_state import COMPARE_SLOT_A
from rcm_desktop.adapter.loaded_project import LoadedProject
from rcm_desktop.adapter.simulation_engine_service import FMMCResultRow, MCRunResult
from rcm_desktop.adapter.simulation_job_service import RunMode
from rcm_desktop.views.panels.simulation_run_binding import (
    _on_mc_result_ready,
    dispatch_compare_slot_run,
)
from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow
from tests.test_desktop_results_workspace_window import _ensure_app, _three_level_project


def test_run_analyse_hidden_in_mc_mode(monkeypatch):
    app = _ensure_app()
    monkeypatch.setattr(QMessageBox, "critical", lambda *_a, **_k: QMessageBox.Ok)
    window = ResultsWorkspaceWindow()
    window.show()
    app.processEvents()

    assert window.run_analyse_button.isVisible() is True

    combo = window.simulation_run_mode_combo
    combo.setCurrentIndex(combo.findData(RunMode.MONTE_CARLO))
    app.processEvents()

    assert window.run_analyse_button.isVisible() is False

    combo.setCurrentIndex(combo.findData(RunMode.ANALYTICAL))
    app.processEvents()

    assert window.run_analyse_button.isVisible() is True


def test_dispatch_compare_slot_run_targets_mc_slot(monkeypatch):
    project = _three_level_project()
    started: list[str] = []

    class _Window:
        def __init__(self) -> None:
            self._pending_mc_compare_slot = None
            self.simulation_run_mode_combo = type(
                "Combo",
                (),
                {"currentData": lambda _self: RunMode.MONTE_CARLO},
            )()
            self._compare_mc_slots = CompareMcSlotState()
            self._state = type("State", (), {"set_last_mc_run": lambda *_a, **_k: None})()
            self._simulation_result_store = None
            self._simulation_job = None

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
            started.append(window._pending_mc_compare_slot)
            return True

    import rcm_desktop.views.panels.simulation_run_binding as binding_mod

    monkeypatch.setattr(binding_mod, "ensure_simulation_runner", lambda _w: _Runner())

    assert dispatch_compare_slot_run(window, COMPARE_SLOT_A) is True
    assert started == [COMPARE_SLOT_A]


def test_on_mc_result_ready_populates_mc_compare_slot():
    result = MCRunResult(
        status="done",
        seed=7,
        n_completed=100,
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
    stored: list[object] = []

    class _State:
        def set_last_mc_run(self, mc):
            stored.append(mc)

    class _Window:
        _pending_mc_compare_slot = COMPARE_SLOT_A
        _compare_mc_slots = CompareMcSlotState()
        _state = _State()
        _simulation_result_store = None

        def _rerender_detail_for_current_scope(self) -> None:
            pass

    window = _Window()
    _on_mc_result_ready(window, result)

    assert stored == [result]
    snap = window._compare_mc_slots.get(COMPARE_SLOT_A)
    assert snap is not None
    assert snap.mc_run is result
    assert "seed 7" in snap.label
    assert window._pending_mc_compare_slot is None
