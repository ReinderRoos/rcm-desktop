"""Dialoog voor werkruimte-rapportgeneratie (slice 57)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from rcm_core.models import RCMProject

from rcm_desktop import messages
from rcm_desktop.adapter.compare_slot_state import CompareSlotState
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.report_eligibility_service import (
    assess_report_workspace,
    preview_report_counts,
)
from rcm_desktop.adapter.report_options import ReportOptions
from rcm_desktop.adapter.report_run_source_service import ReportRunBundle
from rcm_desktop.adapter.run_service import RunResult


class ReportGenerationDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None,
        *,
        project: RCMProject,
        project_path: Path,
        last_run: RunResult | None,
        compare_slots: CompareSlotState | None,
        live_overlay: PlanningOverlayState,
        default_output_path: Path,
        scope_id: str | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(messages.REPORT_DIALOG_TITLE)
        self._project = project
        self._project_path = project_path
        self._last_run = last_run
        self._compare_slots = compare_slots
        self._live_overlay = live_overlay
        self._scope_id = scope_id
        self._workspace = assess_report_workspace(
            last_run=last_run,
            compare_slots=compare_slots,
            live_overlay=live_overlay,
        )
        self._bundle: ReportRunBundle | None = None
        self._options: ReportOptions | None = None

        layout = QVBoxLayout(self)
        form = QFormLayout()

        path_row = QHBoxLayout()
        self._path_edit = QLineEdit(str(default_output_path))
        browse = QPushButton("…")
        browse.clicked.connect(self._browse_path)
        path_row.addWidget(self._path_edit)
        path_row.addWidget(browse)
        form.addRow(messages.REPORT_DIALOG_OUTPUT_PATH, path_row)

        self._pdf_check = QCheckBox(messages.REPORT_DIALOG_GENERATE_PDF)
        self._pdf_check.setChecked(True)
        self._pdf_check.stateChanged.connect(self._refresh_preview)
        form.addRow("", self._pdf_check)

        self._nb_threshold = QDoubleSpinBox()
        self._nb_threshold.setRange(0.0, 100.0)
        self._nb_threshold.setValue(1.0)
        self._nb_threshold.setSuffix(" %")
        self._nb_threshold.valueChanged.connect(self._refresh_preview)
        form.addRow(messages.REPORT_DIALOG_NB_THRESHOLD, self._nb_threshold)

        self._cost_threshold = QDoubleSpinBox()
        self._cost_threshold.setRange(0.0, 100.0)
        self._cost_threshold.setValue(2.0)
        self._cost_threshold.setSuffix(" %")
        self._cost_threshold.valueChanged.connect(self._refresh_preview)
        form.addRow(messages.REPORT_DIALOG_COST_THRESHOLD, self._cost_threshold)

        self._below_threshold = QCheckBox(messages.REPORT_DIALOG_INCLUDE_BELOW)
        self._below_threshold.stateChanged.connect(self._refresh_preview)
        form.addRow("", self._below_threshold)

        self._pbs_deepdive = QCheckBox(messages.REPORT_DIALOG_PBS_DEEPDIVE)
        self._pbs_deepdive.setToolTip(messages.REPORT_GENERATE_BUTTON_TOOLTIP)
        self._pbs_deepdive.stateChanged.connect(self._on_pbs_deepdive_changed)
        form.addRow("", self._pbs_deepdive)

        self._preview_label = QLabel()
        form.addRow(messages.REPORT_DIALOG_PREVIEW, self._preview_label)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._refresh_preview()

    def options(self) -> ReportOptions | None:
        return self._options

    def _browse_path(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            messages.REPORT_DIALOG_OUTPUT_PATH,
            self._path_edit.text(),
            "Word-document (*.docx)",
        )
        if path:
            if not path.lower().endswith(".docx"):
                path += ".docx"
            self._path_edit.setText(path)

    def _on_pbs_deepdive_changed(self) -> None:
        self._refresh_preview()

    def _current_options(self) -> ReportOptions | None:
        if self._workspace.bundle is None:
            return None
        scope_id = self._scope_id if self._pbs_deepdive.isChecked() else None
        return ReportOptions(
            output_docx_path=Path(self._path_edit.text()),
            generate_pdf=self._pdf_check.isChecked(),
            scope_id=scope_id,
            nb_threshold_pct=float(self._nb_threshold.value()),
            cost_threshold_pct=float(self._cost_threshold.value()),
            include_below_threshold=self._below_threshold.isChecked(),
        )

    def _refresh_preview(self) -> None:
        bundle = self._workspace.bundle
        options = self._current_options()
        if bundle is None or options is None:
            self._preview_label.setText("—")
            return
        counts = preview_report_counts(self._project, bundle, options)
        self._preview_label.setText(
            messages.REPORT_DIALOG_PREVIEW_TEMPLATE.format(
                mode=counts.mode,
                nb_pages=counts.nb_function_pages,
                cost_pages=counts.cost_function_pages,
            )
        )

    def _accept(self) -> None:
        bundle = self._workspace.bundle
        options = self._current_options()
        if bundle is None or options is None:
            return
        self._bundle = bundle
        self._options = options
        self.accept()

    def bundle(self) -> ReportRunBundle | None:
        return self._bundle
