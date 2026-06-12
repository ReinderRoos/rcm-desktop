"""Meekoppel-paneel handlers voor LCC-modus (slice 54/55 + panel-extractie)."""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QMessageBox

from rcm_desktop import messages
from rcm_desktop.adapter.feature_flags import meekoppel_workflow_v2_enabled
from rcm_desktop.adapter.meekoppel_display_service import (
    due_calendar_year,
    format_meekoppel_preview_moves_text,
)
from rcm_desktop.adapter.meekoppel_panel_service import (
    MeekoppelPreviewGate,
    apply_meekoppel,
    preview_meekoppel,
    sync_meekoppel_panel,
)
from rcm_desktop.adapter.meekoppelkansen_discovery_service import (
    MeekoppelLocationGroup,
    collect_rev_tasks_for_pbs_selection,
)
from rcm_desktop.adapter.results_workspace_state import MODE_LCC, WorkspaceStateSnapshot
from rcm_desktop.views.meekoppel_preview_dialog import MeekoppelPreviewDialog


def meekoppel_current_anchor(window: Any) -> str:
    return "later" if window.meekoppel_anchor_later.isChecked() else "earlier"


def selected_meekoppel_pbs_ids(window: Any) -> frozenset[str]:
    return window._pbs_selected_ids_from_tree()


def ensure_whatif_for_meekoppel(window: Any) -> None:
    overlay = window.workspace_state.snapshot().planning_overlay
    blocker = window.lcc_whatif_button.blockSignals(True)
    try:
        if overlay.active:
            window.lcc_whatif_button.setChecked(True)
            return
        window.workspace_state.set_planning_overlay(overlay.begin_what_if())
        window.lcc_whatif_button.setChecked(True)
    finally:
        window.lcc_whatif_button.blockSignals(blocker)


def clear_meekoppel_preview_gate(window: Any) -> None:
    window._meekoppel_preview_gate = None


def bind_meekoppel_panel(window: Any, snapshot: WorkspaceStateSnapshot) -> None:
    session = window._project_session()
    selected_pbs_ids = selected_meekoppel_pbs_ids(window)
    panel = sync_meekoppel_panel(
        session,
        snapshot,
        window_years=int(window.meekoppel_window_spin.value()),
        preview_gate=window._meekoppel_preview_gate,
        selected_pbs_ids=selected_pbs_ids or None,
        current_anchor=meekoppel_current_anchor(window),  # type: ignore[arg-type]
    )
    window.meekoppel_whatif_hint_label.setVisible(panel.show_whatif_hint)
    window.meekoppel_window_spin.setEnabled(panel.window_spin_enabled)
    window.meekoppel_anchor_earlier.setEnabled(panel.window_spin_enabled)
    window.meekoppel_anchor_later.setEnabled(panel.window_spin_enabled)
    window.meekoppel_table_view.setVisible(panel.table_visible)
    window.meekoppel_preview_button.setEnabled(panel.preview_enabled)
    window.meekoppel_apply_button.setEnabled(panel.apply_enabled)
    window._meekoppel_location_groups = panel.location_groups
    window._meekoppel_table_model.set_panel_rows(panel.rows, columns=panel.columns)
    if panel.selection_summary_text:
        window.meekoppel_selection_summary_label.setText(panel.selection_summary_text)
        window.meekoppel_selection_summary_label.setVisible(True)
    else:
        window.meekoppel_selection_summary_label.setVisible(False)
    if panel.empty_label_text:
        window.meekoppel_empty_label.setText(panel.empty_label_text)
        window.meekoppel_empty_label.setVisible(True)
    else:
        window.meekoppel_empty_label.setVisible(False)


def on_meekoppel_anchor_changed(window: Any, _button) -> None:
    snapshot = window.workspace_state.snapshot()
    if snapshot.modus == MODE_LCC:
        bind_meekoppel_panel(window, snapshot)


def on_meekoppel_window_changed(window: Any, _value: int) -> None:
    snapshot = window.workspace_state.snapshot()
    if snapshot.modus == MODE_LCC:
        bind_meekoppel_panel(window, snapshot)


def selected_meekoppel_location_group(window: Any) -> MeekoppelLocationGroup | None:
    sm = window.meekoppel_table_view.selectionModel()
    if sm is None or not sm.hasSelection():
        return None
    panel_row = window._meekoppel_table_model.row_at(sm.currentIndex().row())
    if panel_row is None:
        return None
    for group in window._meekoppel_location_groups:
        if group.pbs_id == panel_row.pbs_id:
            return group
    return None


def on_meekoppel_preview(window: Any) -> None:
    session = window._project_session()
    if session is None:
        return
    ensure_whatif_for_meekoppel(window)
    overlay = window.workspace_state.snapshot().planning_overlay
    pbs_ids = selected_meekoppel_pbs_ids(window)
    anchor = meekoppel_current_anchor(window)
    if meekoppel_workflow_v2_enabled():
        if not pbs_ids:
            QMessageBox.warning(
                window,
                messages.LTAP_ERROR_DIALOG_TITLE,
                messages.WORKSPACE_MEEKOPPEL_SELECT_PBS,
            )
            return
        dialog = MeekoppelPreviewDialog(
            window,
            session=session,
            overlay=overlay,
            pbs_ids=pbs_ids,
            anchor=anchor,  # type: ignore[arg-type]
            location_group=selected_meekoppel_location_group(window),
            workflow=window._meekoppel_workflow,
        )
        dialog.exec()
        result = dialog.result_payload()
        if result.preview is None:
            return
        window._meekoppel_preview_gate = MeekoppelPreviewGate(
            pbs_ids=pbs_ids,
            anchor=anchor,  # type: ignore[arg-type]
        )
        if result.accepted and result.scope_kind is not None:
            apply_result = window._meekoppel_workflow.apply(
                session=session,
                overlay=overlay,
                pbs_ids=pbs_ids,
                anchor=anchor,  # type: ignore[arg-type]
                scope_kind=result.scope_kind,
                location_group=selected_meekoppel_location_group(window)
                if result.scope_kind == "location_row"
                else None,
                checked_pm_ids=result.checked_pm_ids,
            )
            if apply_result.status == "ok":
                window.workspace_state.set_planning_overlay(apply_result.overlay)
            elif apply_result.user_message:
                QMessageBox.critical(
                    window,
                    messages.LTAP_ERROR_DIALOG_TITLE,
                    apply_result.user_message,
                )
        bind_meekoppel_panel(window, window.workspace_state.snapshot())
        return
    if not pbs_ids:
        QMessageBox.warning(
            window,
            messages.LTAP_ERROR_DIALOG_TITLE,
            messages.WORKSPACE_MEEKOPPEL_SELECT_PBS,
        )
        return
    prev = preview_meekoppel(
        session,
        overlay,
        pbs_ids,
        anchor=anchor,  # type: ignore[arg-type]
    )
    if prev.blocked_reason:
        QMessageBox.information(
            window,
            messages.WORKSPACE_MEEKOPPEL_PREVIEW_TITLE,
            messages.WORKSPACE_MEEKOPPEL_PREVIEW_BLOCKED.format(reason=prev.blocked_reason),
        )
        return
    project = session.loaded.core()
    modeljaar = int(project.config.modeljaar)
    tasks = collect_rev_tasks_for_pbs_selection(project, pbs_ids)
    moves_text = format_meekoppel_preview_moves_text(
        project,
        overlay,
        modeljaar,
        prev,
        tasks,
    )
    pbs_footnote = messages.WORKSPACE_MEEKOPPEL_PREVIEW_PBS_FOOTNOTE.format(pbs_id=prev.pbs_id)
    QMessageBox.information(
        window,
        messages.WORKSPACE_MEEKOPPEL_PREVIEW_TITLE,
        messages.WORKSPACE_MEEKOPPEL_PREVIEW_BODY.format(
            location=prev.path_label,
            target=prev.target_year,
            target_cal=due_calendar_year(modeljaar, prev.target_year),
            moves=moves_text,
            pbs_footnote=pbs_footnote,
        ),
    )
    window._meekoppel_preview_gate = MeekoppelPreviewGate(
        pbs_ids=pbs_ids,
        anchor=anchor,  # type: ignore[arg-type]
    )
    bind_meekoppel_panel(window, window.workspace_state.snapshot())


def on_meekoppel_apply(window: Any) -> None:
    session = window._project_session()
    if session is None:
        return
    ensure_whatif_for_meekoppel(window)
    overlay = window.workspace_state.snapshot().planning_overlay
    pbs_ids = selected_meekoppel_pbs_ids(window)
    anchor = meekoppel_current_anchor(window)
    if meekoppel_workflow_v2_enabled():
        workflow_result = window._meekoppel_workflow.apply(
            session=session,
            overlay=overlay,
            pbs_ids=pbs_ids,
            anchor=anchor,  # type: ignore[arg-type]
            scope_kind="pbs_selection",
        )
        if workflow_result.status == "validation":
            QMessageBox.warning(
                window,
                messages.LTAP_ERROR_DIALOG_TITLE,
                workflow_result.user_message,
            )
            return
        if workflow_result.status != "ok":
            QMessageBox.critical(
                window,
                messages.LTAP_ERROR_DIALOG_TITLE,
                workflow_result.user_message,
            )
            return
        window.workspace_state.set_planning_overlay(workflow_result.overlay)
    else:
        if not pbs_ids:
            QMessageBox.warning(
                window,
                messages.LTAP_ERROR_DIALOG_TITLE,
                messages.WORKSPACE_MEEKOPPEL_SELECT_PBS,
            )
            return
        result = apply_meekoppel(
            session,
            overlay,
            pbs_ids,
            anchor=anchor,  # type: ignore[arg-type]
        )
        if result.error:
            QMessageBox.critical(window, messages.LTAP_ERROR_DIALOG_TITLE, result.error)
            return
        window.workspace_state.set_planning_overlay(result.overlay)
    bind_meekoppel_panel(window, window.workspace_state.snapshot())
