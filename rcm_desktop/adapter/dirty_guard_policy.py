"""Pure policy for dirty-grid resolution before opening editors."""

from __future__ import annotations

from typing import Literal

from rcm_desktop.adapter.editing_host import EditingHost

DirtyChoice = Literal["save", "discard", "cancel"]
DirtyOutcome = Literal["proceed", "cancel", "warn_save_failed"]


def resolve_dirty_choice(host: EditingHost, choice: DirtyChoice) -> DirtyOutcome:
    if not host.is_grid_dirty():
        return "proceed"
    if choice == "cancel":
        return "cancel"
    if choice == "discard":
        host.discard_buffer_changes()
        return "proceed"
    if host.invoke_grid_save():
        return "proceed"
    return "warn_save_failed"
