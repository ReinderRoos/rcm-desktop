"""Afsluit-helpers voor de resultatenwerkruimte (slice 78 + panel-extractie)."""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QMessageBox

from rcm_desktop import messages


def cancel_background_runners(window: Any) -> None:
    for runner in (
        window._runner,
        window._run_runner,
        window._presentation_rebuild_runner,
        window._compare_run_runner,
        window._lcc_warmup_runner,
        window._report_runner,
    ):
        background = getattr(runner, "_background", None)
        if background is not None:
            background.cancel()


def any_runner_busy(window: Any) -> bool:
    return any(
        getattr(runner, "busy", False)
        for runner in (
            window._runner,
            window._run_runner,
            window._presentation_rebuild_runner,
            window._compare_run_runner,
            window._lcc_warmup_runner,
            window._report_runner,
        )
    )


def detach_table_models_before_close(window: Any) -> None:
    for view_name in (
        "fm_table_view",
        "lcc_table_view",
        "lcc_table_view_cm",
        "lcc_table_view_pm",
        "unavailability_table_view",
        "unavailability_table_view_cm",
        "unavailability_table_view_pm",
        "pm_table_view",
        "pm_table_view_cm",
        "pm_table_view_pm",
        "kpi_table_view",
    ):
        view = getattr(window, view_name, None)
        if view is not None:
            view.setModel(None)


def confirm_busy_shutdown(window: Any) -> bool:
    box = QMessageBox(window)
    box.setWindowTitle(messages.SHUTDOWN_BUSY_TITLE)
    box.setText(messages.SHUTDOWN_BUSY_TEXT)
    confirm = box.addButton(messages.SHUTDOWN_BUSY_CONFIRM, QMessageBox.DestructiveRole)
    cancel = box.addButton(messages.SHUTDOWN_BUSY_CANCEL, QMessageBox.RejectRole)
    box.setDefaultButton(cancel)
    box.exec()
    return box.clickedButton() is confirm
