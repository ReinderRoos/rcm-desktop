"""Waarschuwing bij openen FM-editor terwijl faalwijzen-grid dirty is."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from PySide6.QtWidgets import QMessageBox, QWidget

from rcm_desktop import messages
from rcm_desktop.adapter.faalwijzen_grid_registry import get_active_grid_service, invoke_grid_save

if TYPE_CHECKING:
    from rcm_desktop.adapter.faalwijzen_edit_service import FaalwijzenEditService

GridDirtyResolution = Literal["proceed", "cancel"]


def resolve_grid_dirty_before_editor(parent: QWidget | None) -> GridDirtyResolution:
    svc = get_active_grid_service()
    if svc is None or not svc.is_active() or not svc.is_dirty():
        return "proceed"

    box = QMessageBox(parent)
    box.setWindowTitle(messages.GRID_DIRTY_GUARD_TITLE)
    box.setText(messages.GRID_DIRTY_GUARD_TEXT)
    save_btn = box.addButton(messages.GRID_DIRTY_SAVE, QMessageBox.AcceptRole)
    discard_btn = box.addButton(messages.GRID_DIRTY_DISCARD, QMessageBox.DestructiveRole)
    cancel_btn = box.addButton(messages.GRID_DIRTY_CANCEL_EDITOR, QMessageBox.RejectRole)
    box.setDefaultButton(cancel_btn)
    box.exec()

    clicked = box.clickedButton()
    if clicked is cancel_btn:
        return "cancel"
    if clicked is discard_btn:
        _discard_grid(svc)
        return "proceed"
    if clicked is save_btn:
        if not invoke_grid_save():
            QMessageBox.warning(
                parent,
                messages.GRID_DIRTY_GUARD_TITLE,
                messages.FAALWIJZEN_BULK_FAILED.format(detail="Grid opslaan mislukt."),
            )
            return "cancel"
        return "proceed"
    return "cancel"


def _discard_grid(svc: FaalwijzenEditService) -> None:
    svc.discard_changes()
