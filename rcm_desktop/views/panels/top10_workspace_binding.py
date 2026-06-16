"""Top10-subbar wiring voor de resultatenwerkruimte (slice 90 extractie)."""

from __future__ import annotations

from typing import Any

from rcm_desktop import messages
from rcm_desktop.adapter.view_core_facade import EffectNbFilterSet, RCMProject
from rcm_desktop.adapter.workspace_derived_refresh import (
    plan_contribution_year_refresh,
    plan_nb_filter_refresh,
)
from rcm_desktop.views.panels.top10_subbar_panel import build_top10_subbar_panel


def build_and_wire_top10_subbar(window: Any) -> None:
    panel = build_top10_subbar_panel()
    window.top10_subbar = getattr(panel, "widget")
    window.metric_combo = panel.metric_combo
    window.nb_effect_filter_combo = panel.nb_effect_filter_combo
    window.horizon_button_group = panel.horizon_button_group
    window.horizon_lifecycle_button = panel.horizon_lifecycle_button
    window.horizon_per_year_button = panel.horizon_per_year_button
    window.contribution_year_combo = panel.contribution_year_combo
    window.nb_display_button_group = panel.nb_display_button_group
    window.nb_hours_button = panel.nb_hours_button
    window.nb_percent_button = panel.nb_percent_button
    window.metric_combo.currentIndexChanged.connect(
        lambda idx: on_metric_combo_changed(window, idx)
    )
    window.nb_effect_filter_combo.filter_changed.connect(
        lambda filt: on_nb_effect_filter_changed(window, filt)
    )
    window.horizon_lifecycle_button.clicked.connect(
        lambda _c=False: window.workspace_state.set_contribution_horizon("lifecycle")
    )
    window.horizon_per_year_button.clicked.connect(
        lambda _c=False: window.workspace_state.set_contribution_horizon("per_year")
    )
    window.contribution_year_combo.currentIndexChanged.connect(
        lambda idx: on_contribution_year_combo_changed(window, idx)
    )
    window.nb_hours_button.clicked.connect(
        lambda _c=False: window.workspace_state.set_unavailability_display("hours")
    )
    window.nb_percent_button.clicked.connect(
        lambda _c=False: window.workspace_state.set_unavailability_display("percent")
    )


def on_metric_combo_changed(window: Any, _idx: int) -> None:
    metric = window.metric_combo.currentData()
    if isinstance(metric, str):
        window.workspace_state.set_metric(metric)


def on_nb_effect_filter_changed(window: Any, filt: EffectNbFilterSet) -> None:
    window.workspace_state.set_effect_nb_filter(filt)


def refresh_nb_effect_filter_combo(window: Any, project: object) -> None:
    rcm_project = project if isinstance(project, RCMProject) else None
    session = window._project_session()
    fm_results: tuple = ()
    if session is not None:
        from rcm_desktop.adapter.simulation_job_service import RunMode
        from rcm_desktop.adapter.simulation_workspace_service import resolve_live_run_result
        from rcm_desktop.views.panels.simulation_workspace_binding import current_run_mode

        run = resolve_live_run_result(session, current_run_mode(window))
        if run is not None and run.fm_core_results:
            fm_results = tuple(run.fm_core_results)
    presentation = plan_nb_filter_refresh(rcm_project, fm_results)
    if not presentation.entries:
        window.nb_effect_filter_combo.set_klassen(())
        return
    window.nb_effect_filter_combo.set_presentation(presentation)
    window.nb_effect_filter_combo.set_filter(
        window.workspace_state.snapshot().effect_nb_filter
    )


def on_contribution_year_combo_changed(window: Any, _idx: int) -> None:
    data = window.contribution_year_combo.currentData()
    if data == "average":
        window.workspace_state.set_contribution_year_choice("average")
    elif isinstance(data, int):
        window.workspace_state.set_contribution_year_choice(data)


def refresh_contribution_year_combo(window: Any, project) -> None:
    blocker = window.contribution_year_combo.blockSignals(True)
    current = window.contribution_year_combo.currentData()
    window.contribution_year_combo.clear()
    window.contribution_year_combo.addItem(
        messages.WORKSPACE_CONTRIBUTION_YEAR_AVERAGE,
        userData="average",
    )
    rcm_project = project if isinstance(project, RCMProject) else None
    for year in plan_contribution_year_refresh(rcm_project):
        window.contribution_year_combo.addItem(str(year), userData=year)
    if current is not None:
        idx = window.contribution_year_combo.findData(current)
        if idx >= 0:
            window.contribution_year_combo.setCurrentIndex(idx)
    window.contribution_year_combo.blockSignals(blocker)
