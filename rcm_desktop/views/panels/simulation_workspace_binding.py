"""Monte Carlo status-stub in de resultatenwerkruimte (slice 95 issue 12)."""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel

from rcm_desktop import messages
from rcm_desktop.adapter.simulation_job_service import (
    RunMode,
    SimulationPresentation,
    SimulationResultStore,
    build_simulation_presentation,
    create_simulation_job,
)


def build_simulation_status_widgets(parent: Any) -> tuple[QComboBox, QLabel]:
    run_mode_combo = QComboBox(parent)
    run_mode_combo.addItem(messages.SIMULATION_RUN_MODE_ANALYTICAL, RunMode.ANALYTICAL)
    run_mode_combo.addItem(messages.SIMULATION_RUN_MODE_MONTE_CARLO, RunMode.MONTE_CARLO)
    status_label = QLabel(parent)
    status_label.setVisible(False)
    return run_mode_combo, status_label


def apply_simulation_presentation(window: Any, presentation: SimulationPresentation) -> None:
    if not hasattr(window, "simulation_status_label"):
        return
    label = window.simulation_status_label
    combo = window.simulation_run_mode_combo
    mc_mode = presentation.run_mode is RunMode.MONTE_CARLO
    label.setText(presentation.status_label)
    label.setVisible(mc_mode)
    idx = combo.findData(presentation.run_mode)
    if idx >= 0 and combo.currentIndex() != idx:
        blocker = combo.blockSignals(True)
        combo.setCurrentIndex(idx)
        combo.blockSignals(blocker)


def refresh_simulation_status_stub(window: Any) -> None:
    run_mode = RunMode.ANALYTICAL
    if hasattr(window, "simulation_run_mode_combo"):
        data = window.simulation_run_mode_combo.currentData()
        if isinstance(data, RunMode):
            run_mode = data
    store = getattr(window, "_simulation_result_store", None)
    job = getattr(window, "_simulation_job", None)
    if run_mode is RunMode.MONTE_CARLO and job is None:
        job = create_simulation_job(seed=42, iterations=100)
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
    combo, label = build_simulation_status_widgets(window)
    window.simulation_run_mode_combo = combo
    window.simulation_status_label = label
    combo.currentIndexChanged.connect(lambda _idx: refresh_simulation_status_stub(window))
    ensure_simulation_store(window)
    refresh_simulation_status_stub(window)


def add_simulation_widgets_to_validate_row(validate_row: QHBoxLayout, window: Any) -> None:
    validate_row.addWidget(QLabel(messages.SIMULATION_RUN_MODE_LABEL))
    validate_row.addWidget(window.simulation_run_mode_combo)
    validate_row.addWidget(window.simulation_status_label)
