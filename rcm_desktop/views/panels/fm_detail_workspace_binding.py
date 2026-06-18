"""FM-detail RenderPlan-binding voor de resultatenwerkruimte (slice 105 issue 11)."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt

from rcm_desktop import messages
from rcm_desktop.adapter.compare_slot_state import COMPARE_SLOT_A, COMPARE_SLOT_B
from rcm_desktop.adapter.compare_view_service import ComparePanel
from rcm_desktop.adapter.faalwijze_analyse_service import (
    FM_COMPARE_VIEW_DIAGRAM,
    FM_COMPARE_VIEW_TABLE,
    FaalwijzePresentationBundle,
    fm_table_context_row_indices,
)
from rcm_desktop.adapter.fm_compare_table_model import FMCompareTableModel
from rcm_desktop.adapter.fm_single_run_table_model import FMSingleRunTableModel
from rcm_desktop.views.panels.fm_results_column_binding import (
    apply_fm_optional_column_visibility as apply_fm_optional_columns_to_table,
)
from rcm_desktop.views.panels.workspace_table_policy import apply_column_fit_mode_to_table
from rcm_desktop.adapter.fm_results_sort_policy import default_fm_sort_column
from rcm_desktop.adapter.fm_results_table_model import RAW_ROLE
from rcm_desktop.adapter.results_workspace_orchestrator import RenderPlan
from rcm_desktop.adapter.results_workspace_state import WorkspaceStateSnapshot
from rcm_desktop.adapter.workspace_view_service import FMDetailView
from rcm_desktop.adapter.scenario_compare_chrome import compare_header_stylesheet
from rcm_desktop.views.compare_slot_column import set_compare_placeholder


def sync_fm_view_mode_buttons(window: Any, mode: str) -> None:
    for table_btn, diagram_btn in (
        (window.fm_compare_table_view_button, window.fm_compare_diagram_view_button),
        (window.fm_single_table_view_button, window.fm_single_diagram_view_button),
    ):
        blocker_table = table_btn.blockSignals(True)
        blocker_diagram = diagram_btn.blockSignals(True)
        table_btn.setChecked(mode == FM_COMPARE_VIEW_TABLE)
        diagram_btn.setChecked(mode == FM_COMPARE_VIEW_DIAGRAM)
        table_btn.blockSignals(blocker_table)
        diagram_btn.blockSignals(blocker_diagram)


def set_fm_view_mode(window: Any, mode: str) -> None:
    if mode not in (FM_COMPARE_VIEW_TABLE, FM_COMPARE_VIEW_DIAGRAM):
        return
    if window.workspace_state.snapshot().fm_view_mode == mode:
        return
    sync_fm_view_mode_buttons(window, mode)
    window.workspace_state.set_fm_view_mode(mode)
    show_nmf_rf = window.workspace_state.snapshot().fm_show_nmf_rf
    sync_fm_compare_view_chrome(window, show_nmf_rf=show_nmf_rf)
    sync_fm_single_view_chrome(window, show_nmf_rf=show_nmf_rf)


def layout_fm_compare_chart(window: Any) -> None:
    viewport = window.fm_compare_chart_scroll.viewport()
    window.fm_compare_chart.set_content_width(viewport.width())


def sync_fm_compare_view_chrome(window: Any, *, show_nmf_rf: bool) -> None:
    del show_nmf_rf
    table_mode = window.workspace_state.snapshot().fm_view_mode == FM_COMPARE_VIEW_TABLE
    window.fm_compare_columns_host.setVisible(table_mode)
    window.fm_compare_chart_scroll.setVisible(not table_mode)
    window.fm_compare_nmf_rf_toggle.setVisible(table_mode)
    if table_mode:
        for col in (window._fm_compare_col_a, window._fm_compare_col_b):
            if col["placeholder"].isVisible():
                col["table"].setVisible(False)
            else:
                col["table"].setVisible(True)
    else:
        layout_fm_compare_chart(window)


def layout_fm_single_chart(window: Any) -> None:
    viewport = window.fm_single_chart_scroll.viewport()
    window.fm_single_chart.set_content_width(viewport.width())


def sync_fm_single_view_chrome(window: Any, *, show_nmf_rf: bool) -> None:
    del show_nmf_rf
    table_mode = window.workspace_state.snapshot().fm_view_mode == FM_COMPARE_VIEW_TABLE
    window.fm_table_filter_row.setVisible(table_mode)
    window.fm_filter_clear_button.setVisible(table_mode)
    window.fm_filter_row_count_label.setVisible(table_mode)
    window.fm_table_view.setVisible(table_mode)
    window.fm_single_chart_scroll.setVisible(not table_mode)
    if not table_mode:
        layout_fm_single_chart(window)
    plan = getattr(window, "_last_fm_toolbar_plan", None)
    if plan is not None:
        if hasattr(window, "column_crop_button"):
            window.column_crop_button.setVisible(table_mode and plan.column_crop_visible)
        if hasattr(window, "fm_single_nmf_rf_toggle"):
            window.fm_single_nmf_rf_toggle.setVisible(
                table_mode and plan.fm_compare_nmf_rf_toggle_visible
            )


def apply_fm_single_presentation(window: Any, bundle: FaalwijzePresentationBundle) -> None:
    chart_pres = bundle.chart_presentation()
    if chart_pres is not None:
        window.fm_single_chart.set_presentation(chart_pres)
    show_nmf_rf = window.workspace_state.snapshot().fm_show_nmf_rf
    sync_fm_single_view_chrome(window, show_nmf_rf=show_nmf_rf)


def apply_fm_compare_panels(
    window: Any,
    panels: tuple[ComparePanel, ...],
    snapshot: WorkspaceStateSnapshot,
    *,
    bundle: FaalwijzePresentationBundle | None,
) -> None:
    if bundle is None or bundle.compare is None:
        return
    faalwijze_compare = bundle.compare
    columns = {
        COMPARE_SLOT_A: window._fm_compare_col_a,
        COMPARE_SLOT_B: window._fm_compare_col_b,
    }
    slot_sides = {
        COMPARE_SLOT_A: "s1",
        COMPARE_SLOT_B: "s2",
    }
    show_nmf_rf = window.workspace_state.snapshot().fm_show_nmf_rf
    window.fm_compare_chart.set_presentation(faalwijze_compare)
    for panel in panels:
        col = columns[panel.slot_key]
        col["header"].setStyleSheet(compare_header_stylesheet(panel.slot_key))
        col["header"].setText(
            messages.WORKSPACE_COMPARE_SLOT_HEADER.format(label=panel.label)
        )
        if not panel.filled or panel.fm is None:
            set_compare_placeholder(col, slot_key=panel.slot_key)
            continue
        col["placeholder"].setVisible(False)
        table = col["table"]
        model = FMCompareTableModel(
            faalwijze_compare,
            slot_side=slot_sides[panel.slot_key],
            show_nmf_rf=show_nmf_rf,
            parent=table,
        )
        table.setModel(model)
    sync_fm_compare_view_chrome(window, show_nmf_rf=show_nmf_rf)


def apply_fm_optional_column_visibility(window: Any) -> None:
    if not hasattr(window, "fm_table_view"):
        return
    hidden = getattr(window, "_fm_hidden_optional_columns", frozenset({"pbs_id"}))
    apply_fm_optional_columns_to_table(
        window.fm_table_view,
        hidden_optional_columns=hidden,
    )
    if hasattr(window, "fm_table_filter_row"):
        window.fm_table_filter_row._sync_column_widths()


def apply_fm_column_fit_mode(window: Any, mode: Any) -> None:
    if not hasattr(window, "fm_table_view"):
        return
    apply_column_fit_mode_to_table(window.fm_table_view, mode)


def render_mc_fm_rows(
    window: Any,
    mc_rows: Any,
    *,
    bundle: FaalwijzePresentationBundle,
    empty_message: str = "",
) -> None:
    snapshot = window.workspace_state.snapshot()
    if bundle.single_run is None:
        return
    pres = bundle.single_run
    show_nmf_rf = snapshot.fm_show_nmf_rf
    model = FMSingleRunTableModel(
        pres,
        show_nmf_rf=show_nmf_rf,
        parent=window.fm_table_view,
    )
    window._fm_table_filter_proxy.setSourceModel(model)
    apply_fm_single_presentation(window, bundle)
    if model.rowCount() == 0:
        window.detail_empty_state_label.setText(
            empty_message or messages.WORKSPACE_DETAIL_EMPTY_STATE
        )
        window.detail_empty_state_label.setVisible(True)
    else:
        window.detail_empty_state_label.setVisible(False)
    if hasattr(window, "_fm_column_fit_mode"):
        apply_fm_column_fit_mode(window, window._fm_column_fit_mode)
    window._refresh_fm_filter_row_count()


def sync_fm_table_inspector_context(window: Any) -> None:
    proxy = window._fm_table_proxy
    snap = window.workspace_state.snapshot()
    proxy.set_inspector_context_fm_ids(None)
    if not snap.fm_inspector_mode or not snap.fm_inspector_fm_id:
        return
    ordered: list[str] = []
    for row in range(proxy.rowCount()):
        fm_id = str(proxy.data(proxy.index(row, 0), RAW_ROLE) or "")
        if fm_id:
            ordered.append(fm_id)
    indices = fm_table_context_row_indices(tuple(ordered), snap.fm_inspector_fm_id)
    visible = frozenset(ordered[i] for i in indices)
    proxy.set_inspector_context_fm_ids(visible)


def ordered_fm_ids_from_table(window: Any) -> tuple[str, ...]:
    proxy = window._fm_table_proxy
    proxy.set_inspector_context_fm_ids(None)
    ordered: list[str] = []
    for row in range(proxy.rowCount()):
        fm_id = str(proxy.data(proxy.index(row, 0), RAW_ROLE) or "")
        if fm_id:
            ordered.append(fm_id)
    snap = window.workspace_state.snapshot()
    if snap.fm_inspector_mode and snap.fm_inspector_fm_id:
        sync_fm_table_inspector_context(window)
    return tuple(ordered)


def render_fm_rows(
    window: Any,
    fm_rows: Any,
    *,
    bundle: FaalwijzePresentationBundle,
    empty_message: str = "",
) -> None:
    prior_fm_id = window._selected_fm_id_from_table()
    snapshot = window.workspace_state.snapshot()
    if bundle.single_run is None:
        return
    pres = bundle.single_run
    show_nmf_rf = snapshot.fm_show_nmf_rf
    model = FMSingleRunTableModel(
        pres,
        show_nmf_rf=show_nmf_rf,
        parent=window.fm_table_view,
    )
    window._fm_table_filter_proxy.setSourceModel(model)
    apply_fm_single_presentation(window, bundle)
    metric = snapshot.metric
    if getattr(window, "_fm_sort_metric", None) != metric:
        window._fm_sort_metric = metric
        col = default_fm_sort_column(metric)
        window.fm_table_view.sortByColumn(col, Qt.DescendingOrder)
    if model.rowCount() == 0:
        window.detail_empty_state_label.setText(
            empty_message or messages.WORKSPACE_DETAIL_EMPTY_STATE
        )
        window.detail_empty_state_label.setVisible(True)
    else:
        window.detail_empty_state_label.setVisible(False)
    if hasattr(window, "_fm_column_fit_mode"):
        apply_fm_column_fit_mode(window, window._fm_column_fit_mode)
    restore_row: int | None = None
    if prior_fm_id is not None:
        for row in range(window._fm_table_proxy.rowCount()):
            if window._fm_table_proxy.data(
                window._fm_table_proxy.index(row, 0), RAW_ROLE
            ) == prior_fm_id:
                restore_row = row
                break
    if restore_row is not None:
        window.fm_table_view.selectRow(restore_row)
    elif snapshot.fm_inspector_mode and snapshot.fm_inspector_fm_id:
        window._refresh_fm_inspector(snapshot.fm_inspector_fm_id)
    sync_fm_table_inspector_context(window)
    window._refresh_fm_filter_row_count()


def apply_fm_detail_render(
    window: Any,
    plan: RenderPlan,
    snapshot: WorkspaceStateSnapshot,
) -> None:
    if plan.fm is None or plan.faalwijze_bundle is None:
        return
    if plan.fm.is_mc_mode:
        render_mc_fm_rows(
            window,
            plan.fm.mc_rows,
            bundle=plan.faalwijze_bundle,
            empty_message=plan.fm.empty_message,
        )
    else:
        render_fm_rows(
            window,
            plan.fm.fm_rows,
            bundle=plan.faalwijze_bundle,
            empty_message=plan.fm.empty_message,
        )


def apply_fm_compare_render(
    window: Any,
    plan: RenderPlan,
    snapshot: WorkspaceStateSnapshot,
) -> None:
    apply_fm_compare_panels(
        window,
        plan.compare_panels or (),
        snapshot,
        bundle=plan.faalwijze_bundle,
    )
