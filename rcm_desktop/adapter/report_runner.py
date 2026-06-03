"""Achtergrond-runner voor rapportgeneratie (slice 57)."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtCore import QObject, Signal, Slot

from rcm_desktop.adapter.qt.background_runner import BackgroundRunner
from rcm_desktop.adapter.report_generation_service import (
    ReportGenerationOutcome,
    generate_report_files,
)
from rcm_desktop.adapter.report_options import ReportOptions
from rcm_desktop.adapter.report_pdf_exporter import export_docx_to_pdf
from rcm_desktop.adapter.report_run_source_service import ReportRunBundle


class _ReportWorker(QObject):
    finished = Signal(object)

    def __init__(
        self,
        project: object,
        bundle: ReportRunBundle,
        options: ReportOptions,
        project_path: Path | None,
        pdf_exporter: Callable,
    ) -> None:
        super().__init__()
        self._project = project
        self._bundle = bundle
        self._options = options
        self._project_path = project_path
        self._pdf_exporter = pdf_exporter

    @Slot()
    def run(self) -> None:
        outcome = generate_report_files(
            self._project,
            self._bundle,
            self._options,
            project_path=self._project_path,
            pdf_exporter=self._pdf_exporter,
        )
        self.finished.emit(outcome)


class ReportRunner(QObject):
    state_changed = Signal(str)
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._background = BackgroundRunner(self, self.state_changed.emit)

    @property
    def busy(self) -> bool:
        return self._background.busy

    def start(
        self,
        project: object,
        bundle: ReportRunBundle,
        options: ReportOptions,
        *,
        project_path: Path | None = None,
        pdf_exporter: Callable = export_docx_to_pdf,
    ) -> bool:
        if self._background.busy:
            return False
        worker = _ReportWorker(
            project,
            bundle,
            options,
            project_path,
            pdf_exporter,
        )
        return self._background.start(worker, on_finished=self._on_finished)

    @Slot(object)
    def _on_finished(self, outcome: object) -> None:
        if isinstance(outcome, ReportGenerationOutcome):
            self.finished.emit(outcome)
            self.state_changed.emit("done")
        else:
            self.failed.emit("Onbekende uitkomst rapportgeneratie.")
            self.state_changed.emit("error")
