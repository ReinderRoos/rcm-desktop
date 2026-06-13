"""Input-zijde entity-grid pagina voor de resultatenwerkruimte (slice 93)."""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QDialog, QHBoxLayout, QMessageBox, QPushButton, QVBoxLayout, QWidget

from rcm_desktop import messages
from rcm_desktop.adapter import workspace_session_service as wss
from rcm_desktop.adapter.entity_edit_service import EntityEditService
from rcm_desktop.adapter.fm_delete_service import (
    build_fm_delete_confirmation,
    delete_faalwijze_row,
    format_fm_delete_confirmation_message,
)
from rcm_desktop.adapter.workspace_navigation_policy import INPUT_FAALWIJZEN_VIEW
from rcm_desktop.views.fm_editor_dialog import FmEditorDialog
from rcm_desktop.views.grid_dirty_guard import resolve_grid_dirty_before_editor
from rcm_desktop.views.panels.entity_grid_panel import EntityGridPanel


def build_input_entity_grid_page(window: Any) -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(0, 0, 0, 0)
    toolbar = QHBoxLayout()
    window.new_fm_button = QPushButton(messages.FM_EDITOR_NEW_FM)
    window.new_fm_button.setToolTip(messages.FM_EDITOR_NEW_FM_TOOLTIP)
    window.new_fm_button.setVisible(False)
    toolbar.addWidget(window.new_fm_button)
    window.delete_fm_button = QPushButton(messages.FM_DELETE_BUTTON_LABEL)
    window.delete_fm_button.setToolTip(messages.FM_DELETE_BUTTON_TOOLTIP)
    window.delete_fm_button.setVisible(False)
    toolbar.addWidget(window.delete_fm_button)
    toolbar.addStretch(1)
    layout.addLayout(toolbar)
    window._entity_grid_panel = EntityGridPanel()
    window._entity_grid_panel.set_hidden_columns_handler(window._on_entity_grid_columns_changed)
    layout.addWidget(window._entity_grid_panel)
    window.new_fm_button.clicked.connect(lambda: handle_new_fm_clicked(window))
    window.delete_fm_button.clicked.connect(lambda: handle_delete_fm_clicked(window))
    return page


def sync_new_fm_button_enabled(window: Any) -> None:
    button = getattr(window, "new_fm_button", None)
    if button is None:
        return
    leaf = window._selected_leaf_pbs_id_for_create()
    has_project = window._project_session() is not None
    button.setEnabled(has_project and leaf is not None)


def handle_new_fm_clicked(window: Any) -> None:
    if window.workspace_state.snapshot().active_view_id != INPUT_FAALWIJZEN_VIEW:
        return
    session = window._project_session()
    if session is None:
        QMessageBox.information(
            window,
            messages.FM_EDITOR_VALIDATION_TITLE,
            messages.FM_EDITOR_NO_PROJECT,
        )
        return
    pbs_id = window._selected_leaf_pbs_id_for_create()
    if pbs_id is None:
        QMessageBox.information(
            window,
            messages.FM_EDITOR_VALIDATION_TITLE,
            messages.FM_EDITOR_NEW_FM_NO_LEAF_PBS,
        )
        return
    project = wss.editing_project(session)
    host = window._editing_host
    prev_save = host.swap_save_handler(window._commit_active_grid_edits)
    try:
        if resolve_grid_dirty_before_editor(window, host) == "cancel":
            return
        path = window.path_input.text().strip() or None
        grid_svc = host.grid_service()
        shared_session = None
        if grid_svc is not None and grid_svc.is_active():
            shared_session = grid_svc.editing_session
        dialog = FmEditorDialog(
            window,
            project=project,
            create_pbs_id=pbs_id,
            project_path=path,
            save_to_disk=bool(path),
            editing_session=shared_session,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted or dialog.commit_result is None:
            return
        result = dialog.commit_result
        if result.project is not None:
            window._state.set_last_project(
                result.project, path=path, preserve_workspace_ui=True
            )
        if result.run_result is not None:
            window._state.set_last_run(result.run_result)
            window._project_total_presentation = window._load_presentation_from_disk()
            window._render_index.on_workspace_state_reset()
            window._rerender_detail_for_current_scope()
        window._entity_grid_panel.refresh_view()
    finally:
        host.set_save_handler(prev_save)


def wire_entity_grid_delete_selection(window: Any) -> None:
    panel = getattr(window, "_entity_grid_panel", None)
    if panel is None:
        return
    selection = panel._table.selectionModel()
    if selection is not None:
        selection.selectionChanged.connect(lambda *_args: sync_delete_fm_button_enabled(window))
    sync_delete_fm_button_enabled(window)


def sync_delete_fm_button_enabled(window: Any) -> None:
    button = getattr(window, "delete_fm_button", None)
    if button is None:
        return
    has_project = window._project_session() is not None
    panel = getattr(window, "_entity_grid_panel", None)
    has_selection = (
        window.workspace_state.snapshot().active_view_id == INPUT_FAALWIJZEN_VIEW
        and panel is not None
        and panel.selected_row_key() is not None
    )
    button.setEnabled(has_project and has_selection)


def handle_delete_fm_clicked(window: Any) -> None:
    if window.workspace_state.snapshot().active_view_id != INPUT_FAALWIJZEN_VIEW:
        return
    panel = window._entity_grid_panel
    fm_id = panel.selected_row_key()
    if not fm_id:
        QMessageBox.information(
            window,
            messages.FM_DELETE_CONFIRM_TITLE,
            messages.FM_DELETE_NO_SELECTION,
        )
        return
    session = window._project_session()
    if session is None:
        QMessageBox.information(
            window,
            messages.FM_DELETE_CONFIRM_TITLE,
            messages.FM_EDITOR_NO_PROJECT,
        )
        return
    project = wss.editing_project(session)
    host = window._editing_host
    grid_svc = host.ensure_grid(project)
    entity_svc = EntityEditService.for_view(INPUT_FAALWIJZEN_VIEW)
    entity_svc.attach_editing_session(grid_svc.editing_session)
    confirmation = build_fm_delete_confirmation(entity_svc, fm_id)
    answer = QMessageBox.question(
        window,
        messages.FM_DELETE_CONFIRM_TITLE,
        format_fm_delete_confirmation_message(confirmation),
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    if answer != QMessageBox.StandardButton.Yes:
        return
    delete_faalwijze_row(entity_svc, fm_id)
    panel.refresh_view()
    window._on_entity_grid_changed()
