"""Qt dirty-guard vóór openen FM-editor (slice 46-08 — geen Qt in adapter)."""

from __future__ import annotations

from typing import Literal

from PySide6.QtWidgets import QMessageBox, QWidget

from rcm_desktop import messages
from rcm_desktop.adapter.dirty_guard_policy import resolve_dirty_choice
from rcm_desktop.adapter.editing_host import EditingHost, get_editing_host
GridDirtyResolution = Literal["proceed", "cancel"]


def resolve_grid_dirty_before_editor(
    parent: QWidget | None,
    host: EditingHost | None = None,
) -> GridDirtyResolution:
    """Waarschuw als batch-grid dirty is; optioneel opslaan via host save-handler."""
    editing_host = host if host is not None else get_editing_host()
    if not editing_host.is_grid_dirty():
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
        outcome = resolve_dirty_choice(editing_host, "cancel")
    elif clicked is discard_btn:
        outcome = resolve_dirty_choice(editing_host, "discard")
    elif clicked is save_btn:
        outcome = resolve_dirty_choice(editing_host, "save")
    else:
        outcome = "cancel"
    if outcome == "warn_save_failed":
        QMessageBox.warning(
            parent,
            messages.GRID_DIRTY_GUARD_TITLE,
            messages.FAALWIJZEN_BULK_FAILED.format(detail="Grid opslaan mislukt."),
        )
        return "cancel"
    return "proceed" if outcome == "proceed" else "cancel"
