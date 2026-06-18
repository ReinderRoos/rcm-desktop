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
from rcm_desktop.views.panels.input_entity_grid_binding import (
    sync_delete_fm_button_enabled,
    sync_new_fm_button_enabled,
)
from rcm_desktop.adapter.faalwijze_analyse_service import FM_COMPARE_VIEW_TABLE
from rcm_desktop.adapter.results_workspace_state import WorkspaceStateSnapshot


def apply_status_strip_visibility(window: Any, visible: bool) -> None:
    """Gele validatiestrip verbergen op Input; bron = invoertabel (slice 105.24)."""
    if not hasattr(window, "status_strip"):
        return
    window.status_strip.setVisible(visible)
    if visible:
        window.status_strip.setMaximumHeight(16777215)
        window.status_strip.setMinimumHeight(0)
    else:
        window.status_strip.setFixedHeight(0)


_FM_METRIC_CHROME_WIDGET_ATTRS: tuple[str, ...] = (
    "metric_combo",
    "nb_effect_filter_combo",
    "horizon_lifecycle_button",
    "horizon_per_year_button",
    "contribution_year_combo",
    "nb_hours_button",
    "nb_percent_button",
)


def _clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.setParent(None)


def _detach_widgets(widgets: tuple) -> None:
    for widget in widgets:
        if widget is not None:
            widget.setParent(None)


def _clear_layout_except(layout, keep: set) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None and widget not in keep:
            widget.setParent(None)


def relocate_fm_metric_chrome(window: Any, *, target: str) -> None:
    """Verplaats gedeelde metric-widgets tussen Top-10-subbar en FM-toolbar (105.27)."""
    if not hasattr(window, "fm_metric_chrome_layout"):
        return
    widgets = tuple(getattr(window, name) for name in _FM_METRIC_CHROME_WIDGET_ATTRS)
    label = getattr(window, "top10_subbar_label", None)
    _detach_widgets(widgets)

    if target == "fm":
        if label is not None:
            label.setVisible(False)
        layout = window.fm_metric_chrome_layout
        _clear_layout(layout)
        for widget in widgets:
            layout.addWidget(widget)
        layout.addStretch(1)
        return

    if target == "top10":
        layout = window._top10_subbar_layout
        keep = {label} if label is not None else set()
        _clear_layout_except(layout, keep)
        if label is not None:
            label.setVisible(True)
            if layout.indexOf(label) < 0:
                layout.insertWidget(0, label)
        for widget in widgets:
            layout.addWidget(widget)
        if layout.count() == 0 or layout.itemAt(layout.count() - 1).spacerItem() is None:
            layout.addStretch(1)


def apply_top10_subbar_visibility(window: Any, visible: bool) -> None:
    if not hasattr(window, "top10_subbar"):
        return
    window.top10_subbar.setVisible(visible)
    if visible:
        window.top10_subbar.setMaximumHeight(16777215)
        window.top10_subbar.setMinimumHeight(0)
    else:
        window.top10_subbar.setFixedHeight(0)


def apply_bijdragen_toolbar(
    window: Any,
    toolbar: BijdragenToolbarPlan | None,
) -> None:
    if toolbar is None:
        return
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
            box.setEnabled(pm_visible and toolbar.cm_filter_visible)
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
    if toolbar.contribution_subbar_visible:
        window.horizon_lifecycle_button.setVisible(False)
        window.horizon_per_year_button.setVisible(False)
        window.contribution_year_combo.setVisible(False)
        window.nb_hours_button.setVisible(toolbar.nb_display_toggles_visible)
        window.nb_percent_button.setVisible(toolbar.nb_display_toggles_visible)
    window._sync_lcc_filter_checks(toolbar.lcc_filters)
    from rcm_desktop.views.panels.meekoppel_workspace_binding import bind_meekoppel_panel

    bind_meekoppel_panel(window, snapshot)
    window._sync_lcc_axis_labels(snapshot)


def apply_fm_toolbar(
    window: Any,
    toolbar: FmToolbarPlan,
    *,
    preserve_shared_metric: bool = False,
) -> None:
    faalwijzen_action = window._workspace_menu.actions_by_id.get("analysis.faalwijzen_grid")
    if faalwijzen_action is not None:
        faalwijzen_action.setVisible(toolbar.batch_faalwijzen_visible)
    crop_action = window._workspace_menu.actions_by_id.get("view.column_crop")
    if crop_action is not None:
        crop_action.setVisible(toolbar.column_crop_visible)
    if hasattr(window, "column_crop_button"):
        window.column_crop_button.setVisible(toolbar.column_crop_visible)
    compare_mode = window.workspace_state.snapshot().compare_mode
    fm_compare_active = toolbar.fm_compare_view_toggle_visible and compare_mode
    fm_single_active = toolbar.fm_compare_view_toggle_visible and not compare_mode
    view_mode = toolbar.fm_view_mode
    show_nmf_rf = toolbar.fm_show_nmf_rf
    if hasattr(window, "fm_compare_nmf_rf_toggle"):
        compare_nmf_visible = (
            toolbar.fm_compare_nmf_rf_toggle_visible
            and fm_compare_active
            and view_mode == FM_COMPARE_VIEW_TABLE
        )
        window.fm_compare_nmf_rf_toggle.setVisible(compare_nmf_visible)
        if not compare_nmf_visible and window.fm_compare_nmf_rf_toggle.isChecked():
            blocker = window.fm_compare_nmf_rf_toggle.blockSignals(True)
            window.fm_compare_nmf_rf_toggle.setChecked(False)
            window.fm_compare_nmf_rf_toggle.blockSignals(blocker)
            window.workspace_state.set_fm_show_nmf_rf(False)
    if hasattr(window, "fm_single_nmf_rf_toggle"):
        single_nmf_visible = (
            toolbar.fm_compare_nmf_rf_toggle_visible
            and fm_single_active
            and view_mode == FM_COMPARE_VIEW_TABLE
        )
        window.fm_single_nmf_rf_toggle.setVisible(single_nmf_visible)
        if single_nmf_visible and hasattr(window, "_fm_bind"):
            window._fm_bind.sync_nmf_rf_toggles(show_nmf_rf)
    if hasattr(window, "fm_compare_table_view_button"):
        window.fm_compare_table_view_button.setVisible(fm_compare_active)
        window.fm_compare_diagram_view_button.setVisible(fm_compare_active)
        if fm_compare_active and hasattr(window, "_fm_bind"):
            window._fm_bind.sync_view_mode_buttons(view_mode)
            window._fm_bind.sync_compare_view_chrome(show_nmf_rf=show_nmf_rf)
        if hasattr(window, "fm_single_table_view_button"):
            window.fm_single_table_view_button.setVisible(fm_single_active)
            window.fm_single_diagram_view_button.setVisible(fm_single_active)
            if fm_single_active and hasattr(window, "_fm_bind"):
                window._fm_bind.sync_view_mode_buttons(view_mode)
                window._fm_bind.sync_single_view_chrome(show_nmf_rf=show_nmf_rf)
    if hasattr(window, "new_fm_button"):
        window.new_fm_button.setVisible(toolbar.new_fm_visible)
        if toolbar.new_fm_visible:
            sync_new_fm_button_enabled(window)
    if hasattr(window, "delete_fm_button"):
        window.delete_fm_button.setVisible(toolbar.delete_fm_visible)
        if toolbar.delete_fm_visible:
            sync_delete_fm_button_enabled(window)
    if hasattr(window, "fm_inspector_container"):
        window.fm_inspector_container.setVisible(toolbar.fm_inspector_visible)
        if toolbar.clear_fm_inspector:
            from rcm_desktop.views.panels.fm_inspector_binding import refresh_fm_inspector

            refresh_fm_inspector(window, None)
    if toolbar.effect_nb_filter_visible:
        pass
    if not preserve_shared_metric:
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
        if not toolbar.horizon_lifecycle_visible:
            window.nb_hours_button.setVisible(False)
            window.nb_percent_button.setVisible(False)
        window.nb_effect_filter_combo.setVisible(toolbar.effect_nb_filter_visible)
        if toolbar.effect_nb_filter_visible:
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
    if hasattr(window, "fm_single_slot_pane"):
        window.fm_single_slot_pane.setVisible(compare.fm_single_visible)
    if hasattr(window, "fm_compare_pane"):
        window.fm_compare_pane.setVisible(compare.fm_compare_visible)


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
