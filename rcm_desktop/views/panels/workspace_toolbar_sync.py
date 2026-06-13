"""Orchestrator-toolbar-plannen toepassen op werkruimte-widgets (slice 62 follow-up)."""

from __future__ import annotations

from typing import Any

from rcm_desktop.adapter.results_workspace_orchestrator import (
    BijdragenToolbarPlan,
    CollapsePanelPlan,
    CollapsePanelsPlan,
    CompareChromePlan,
    FmToolbarPlan,
    LccToolbarVisibilityPlan,
    MeekoppelCollapsePlan,
)
from rcm_desktop.adapter.results_workspace_state import (
    METRIC_NIET_BESCHIKBAARHEID,
    MODE_LCC,
    WorkspaceStateSnapshot,
)


def apply_bijdragen_toolbar(
    window: Any,
    toolbar: BijdragenToolbarPlan | None,
) -> None:
    in_lcc = window.workspace_state.snapshot().modus == MODE_LCC
    if toolbar is None and not in_lcc:
        window.top10_subbar.setVisible(False)
        return
    window.top10_subbar.setVisible(True)
    window.metric_combo.setVisible(True)
    if toolbar is None:
        window.horizon_lifecycle_button.setVisible(False)
        window.horizon_per_year_button.setVisible(False)
        window.contribution_year_combo.setVisible(False)
        window.nb_hours_button.setVisible(False)
        window.nb_percent_button.setVisible(False)
        lcc_toolbar = window._last_lcc_toolbar_plan
        if lcc_toolbar is not None:
            window.nb_effect_filter_combo.setVisible(lcc_toolbar.effect_nb_filter_visible)
        return
    window.horizon_lifecycle_button.setVisible(toolbar.horizon_lifecycle_visible)
    window.horizon_per_year_button.setVisible(toolbar.horizon_per_year_visible)
    window.contribution_year_combo.setVisible(toolbar.year_combo_visible)
    window.nb_hours_button.setVisible(toolbar.nb_hours_visible)
    window.nb_percent_button.setVisible(toolbar.nb_percent_visible)
    window.nb_effect_filter_combo.setVisible(toolbar.effect_nb_filter_visible)
    if toolbar.effect_nb_filter_visible:
        window.nb_effect_filter_combo.set_filter(
            window.workspace_state.snapshot().effect_nb_filter
        )
    if toolbar.horizon_lifecycle_visible:
        if toolbar.horizon_lifecycle_checked and not window.horizon_lifecycle_button.isChecked():
            window.horizon_lifecycle_button.setChecked(True)
        elif toolbar.horizon_per_year_checked and not window.horizon_per_year_button.isChecked():
            window.horizon_per_year_button.setChecked(True)
    if toolbar.nb_hours_visible:
        if toolbar.nb_hours_checked and not window.nb_hours_button.isChecked():
            window.nb_hours_button.setChecked(True)
        elif toolbar.nb_percent_checked and not window.nb_percent_button.isChecked():
            window.nb_percent_button.setChecked(True)
    if toolbar.year_combo_visible:
        idx = window.contribution_year_combo.findData(toolbar.year_choice)
        if idx >= 0 and idx != window.contribution_year_combo.currentIndex():
            blocker = window.contribution_year_combo.blockSignals(True)
            window.contribution_year_combo.setCurrentIndex(idx)
            window.contribution_year_combo.blockSignals(blocker)


def apply_lcc_toolbar(
    window: Any,
    toolbar: LccToolbarVisibilityPlan | None,
    snapshot: WorkspaceStateSnapshot,
) -> None:
    window._last_lcc_toolbar_plan = toolbar
    if toolbar is None:
        window.lcc_filter_bar.setVisible(False)
        window.lcc_show_all_years_button.setVisible(False)
        window.lcc_year_summary_label.setVisible(False)
        window.meekoppel_panel.setVisible(False)
        return
    window.lcc_filter_bar.setVisible(toolbar.filter_bar_visible)
    pm_visible = toolbar.pm_type_filters_visible
    for key, box in window._lcc_filter_checks.items():
        if key == "cm":
            box.setVisible(pm_visible and toolbar.cm_filter_visible)
            box.setEnabled(toolbar.cm_filter_visible)
        else:
            box.setVisible(pm_visible)
    window.lcc_cm_preset_button.setVisible(toolbar.cm_preset_button_visible)
    window.lcc_show_all_years_button.setVisible(toolbar.show_all_years_visible)
    window.lcc_year_summary_label.setVisible(toolbar.year_summary_label_visible)
    window.meekoppel_panel.setVisible(toolbar.meekoppel_panel_visible)
    window.metric_combo.setVisible(toolbar.metric_combo_visible)
    window.nb_effect_filter_combo.setVisible(toolbar.effect_nb_filter_visible)
    if toolbar.effect_nb_filter_visible:
        window.nb_effect_filter_combo.set_filter(snapshot.effect_nb_filter)
    if snapshot.modus == MODE_LCC:
        window.top10_subbar.setVisible(True)
        window.horizon_lifecycle_button.setVisible(False)
        window.horizon_per_year_button.setVisible(False)
        window.contribution_year_combo.setVisible(False)
        nb = snapshot.metric == METRIC_NIET_BESCHIKBAARHEID
        window.nb_hours_button.setVisible(nb)
        window.nb_percent_button.setVisible(nb)
    window._sync_lcc_filter_checks(toolbar.lcc_filters)
    from rcm_desktop.views.panels.meekoppel_workspace_binding import bind_meekoppel_panel

    bind_meekoppel_panel(window, snapshot)
    window._sync_lcc_axis_labels(snapshot)


def apply_fm_toolbar(window: Any, toolbar: FmToolbarPlan) -> None:
    faalwijzen_action = window._workspace_menu.actions_by_id.get("analysis.faalwijzen_grid")
    if faalwijzen_action is not None:
        faalwijzen_action.setVisible(toolbar.batch_faalwijzen_visible)
    crop_action = window._workspace_menu.actions_by_id.get("view.column_crop")
    if crop_action is not None:
        crop_action.setVisible(toolbar.column_crop_visible)
    if hasattr(window, "column_crop_button"):
        window.column_crop_button.setVisible(toolbar.column_crop_visible)
    if hasattr(window, "new_fm_button"):
        window.new_fm_button.setVisible(toolbar.new_fm_visible)
        if toolbar.new_fm_visible:
            window._sync_new_fm_button_enabled()
    if hasattr(window, "fm_inspector_container"):
        window.fm_inspector_container.setVisible(toolbar.fm_inspector_visible)
        if toolbar.clear_fm_inspector:
            from rcm_desktop.views.panels.fm_inspector_binding import refresh_fm_inspector

            refresh_fm_inspector(window, None)
    if toolbar.effect_nb_filter_visible:
        window.top10_subbar.setVisible(True)
        window.metric_combo.setVisible(toolbar.metric_combo_visible)
        window.horizon_lifecycle_button.setVisible(toolbar.horizon_lifecycle_visible)
        window.horizon_per_year_button.setVisible(toolbar.horizon_per_year_visible)
        window.contribution_year_combo.setVisible(toolbar.year_combo_visible)
        window.horizon_lifecycle_button.setChecked(toolbar.horizon_lifecycle_checked)
        window.horizon_per_year_button.setChecked(toolbar.horizon_per_year_checked)
        if toolbar.year_combo_visible:
            idx = window.contribution_year_combo.findData(toolbar.year_choice)
            if idx >= 0 and idx != window.contribution_year_combo.currentIndex():
                blocker = window.contribution_year_combo.blockSignals(True)
                window.contribution_year_combo.setCurrentIndex(idx)
                window.contribution_year_combo.blockSignals(blocker)
        window.nb_hours_button.setVisible(False)
        window.horizon_per_year_button.setVisible(False)
        window.contribution_year_combo.setVisible(False)
        window.nb_hours_button.setVisible(False)
        window.nb_percent_button.setVisible(False)
        window.nb_effect_filter_combo.setVisible(True)
        window.nb_effect_filter_combo.set_filter(
            window.workspace_state.snapshot().effect_nb_filter
        )


def apply_compare_chrome(window: Any, compare: CompareChromePlan) -> None:
    if hasattr(window, "compare_toggle_button"):
        if window.compare_toggle_button.isChecked() != compare.compare_mode_checked:
            blocker = window.compare_toggle_button.blockSignals(True)
            window.compare_toggle_button.setChecked(compare.compare_mode_checked)
            window.compare_toggle_button.blockSignals(blocker)
    if hasattr(window, "bijdragen_single_slot_pane"):
        window.bijdragen_single_slot_pane.setVisible(compare.bijdragen_single_visible)
        window.bijdragen_compare_pane.setVisible(compare.bijdragen_compare_visible)
        window.bijdragen_chart_label.setVisible(compare.bijdragen_chart_label_visible)
    if hasattr(window, "lcc_single_slot_pane"):
        window.lcc_single_slot_pane.setVisible(compare.lcc_single_visible)
        window.lcc_compare_pane.setVisible(compare.lcc_compare_visible)
        if compare.lcc_empty_state_visible:
            window.lcc_empty_state_label.setVisible(True)


def apply_collapse_panels(window: Any, collapse: CollapsePanelsPlan) -> None:
    apply_collapse_panel(
        collapse.kpi,
        chrome_button=None,
        title=getattr(window, "kpi_panel_title", None),
        content=getattr(window, "kpi_table_view", None),
    )
    apply_collapse_panel(
        collapse.lcc_whatif,
        chrome_button=getattr(window, "lcc_whatif_collapse_button", None),
        title=getattr(window, "lcc_whatif_bar_title", None),
        content=getattr(window, "lcc_whatif_content", None),
    )
    apply_meekoppel_collapse(window, collapse.meekoppel)


def apply_collapse_panel(
    panel: CollapsePanelPlan | None,
    *,
    chrome_button,
    title,
    content,
) -> None:
    if panel is None:
        if chrome_button is not None:
            chrome_button.setVisible(False)
        if title is not None:
            title.setVisible(False)
        if content is not None:
            content.setVisible(True)
        return
    if chrome_button is not None:
        chrome_button.setVisible(panel.chrome_visible)
        chrome_button.setText(panel.collapse_glyph)
        chrome_button.setEnabled(panel.chrome_enabled)
    if title is not None:
        title.setVisible(panel.chrome_visible if chrome_button is not None else True)
    if content is not None:
        content.setVisible(panel.content_visible)


def apply_meekoppel_collapse(window: Any, panel: MeekoppelCollapsePlan | None) -> None:
    if not hasattr(window, "meekoppel_collapse_button"):
        return
    if panel is None:
        window.meekoppel_collapse_button.setVisible(False)
        window.meekoppel_content.setVisible(False)
        return
    if panel.ensure_whatif_if_expanding:
        from rcm_desktop.views.panels.meekoppel_workspace_binding import (
            ensure_whatif_for_meekoppel,
        )

        ensure_whatif_for_meekoppel(window)
    window.meekoppel_collapse_button.setVisible(panel.chrome_visible)
    window.meekoppel_content.setVisible(panel.content_visible)
    window.meekoppel_collapse_button.setText(panel.collapse_glyph)
    window.meekoppel_collapse_button.setEnabled(panel.chrome_enabled)
