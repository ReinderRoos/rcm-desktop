"""Registratie actieve faalwijzen-grid service voor cross-window dirty guard."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rcm_desktop.adapter.faalwijzen_edit_service import FaalwijzenEditService

_active: FaalwijzenEditService | None = None
_save_handler: Callable[[], bool] | None = None


def set_active_grid_service(service: FaalwijzenEditService | None) -> None:
    global _active
    _active = service


def get_active_grid_service() -> FaalwijzenEditService | None:
    return _active


def set_grid_save_handler(handler: Callable[[], bool] | None) -> None:
    global _save_handler
    _save_handler = handler


def invoke_grid_save() -> bool:
    if _save_handler is not None:
        return _save_handler()
    svc = _active
    if svc is None or not svc.is_active():
        return True
    if svc.has_errors():
        return False
    svc.mark_saved()
    return True
