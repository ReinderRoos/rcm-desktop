"""Monte Carlo status strip in de resultatenwerkruimte (slice 95/98)."""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton

from rcm_desktop import messages
from rcm_desktop.adapter.simulation_job_service import (
    RunMode,
    SimulationPresentation,
    SimulationResultStore,
    build_simulation_presentation,
)
from rcm_desktop.adapter.simulation_workspace_service import resolve_run_mode


def current_run_mode(window: Any) -> RunMode:
    if hasattr(window, "simulation_run_mode_combo"):
        return resolve_run_mode(window.simulation_run_mode_combo.currentData())
    return RunMode.ANALYTICAL


def cancel_active_simulation(window: Any) -> None:
    runner = getattr(window, "_simulation_runner", None)
    if runner is not None and hasattr(runner, "cancel"):
        runner.cancel()


def build_simulation_status_widgets(parent: Any) -> tuple[QComboBox, QLabel, QPushButton]:
    run_mode_combo = QComboBox(parent)
    run_mode_combo.addItem(messages.SIMULATION_RUN_MODE_ANALYTICAL, RunMode.ANALYTICAL)
    run_mode_combo.addItem(messages.SIMULATION_RUN_MODE_MONTE_CARLO, RunMode.MONTE_CARLO)
    run_mode_combo.setToolTip(messages.SIMULATION_RUN_MODE_ONBOARDING)
    status_label = QLabel(parent)
    status_label.setVisible(False)
    cancel_button = QPushButton(messages.SIMULATION_CANCEL_BUTTON_LABEL, parent)
    cancel_button.setVisible(False)
    cancel_button.clicked.connect(lambda: cancel_active_simulation(parent))
    return run_mode_combo, status_label, cancel_button


def apply_simulation_presentation(window: Any, presentation: SimulationPresentation) -> None:
    if not hasattr(window, "simulation_status_label"):
        return
    label = window.simulation_status_label
    combo = window.simulation_run_mode_combo
    cancel_button = getattr(window, "simulation_cancel_button", None)
    mc_mode = presentation.run_mode is RunMode.MONTE_CARLO
    label.setText(presentation.status_label)
    label.setVisible(mc_mode)
    if cancel_button is not None:
        busy = presentation.status == "running"
        cancel_button.setVisible(mc_mode and busy)
    idx = combo.findData(presentation.run_mode)
    if idx >= 0 and combo.currentIndex() != idx:
        blocker = combo.blockSignals(True)
        combo.setCurrentIndex(idx)
        combo.blockSignals(blocker)


def refresh_simulation_status(window: Any) -> None:
    run_mode = current_run_mode(window)
    store = getattr(window, "_simulation_result_store", None)
    job = getattr(window, "_simulation_job", None)
    presentation = build_simulation_presentation(
        run_mode=run_mode,
        job=job,
        store=store if isinstance(store, SimulationResultStore) else None,
    )
    apply_simulation_presentation(window, presentation)


def ensure_simulation_store(window: Any) -> SimulationResultStore:
    store = getattr(window, "_simulation_result_store", None)
    if not isinstance(store, SimulationResultStore):
        store = SimulationResultStore()
        window._simulation_result_store = store
    return store


def wire_simulation_status_strip(window: Any) -> None:
    combo, label, cancel_button = build_simulation_status_widgets(window)
    window.simulation_run_mode_combo = combo
    window.simulation_status_label = label
    window.simulation_cancel_button = cancel_button
    ensure_simulation_store(window)
    refresh_simulation_status(window)


def add_simulation_widgets_to_validate_row(validate_row: QHBoxLayout, window: Any) -> None:
    validate_row.addWidget(QLabel(messages.SIMULATION_RUN_MODE_LABEL))
    validate_row.addWidget(window.simulation_run_mode_combo)
    validate_row.addWidget(window.simulation_status_label)
    validate_row.addWidget(window.simulation_cancel_button)
