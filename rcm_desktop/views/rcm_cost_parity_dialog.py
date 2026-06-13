"""Modelcontrole-dialoog — RCM-Cost parity tabel (slice 65)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from rcm_desktop.adapter.view_core_facade import FMResult, ParityVerdict, RCMProject
from rcm_desktop import messages
from rcm_desktop.adapter.failure_validation_export_service import export_validation_excel
from rcm_desktop.adapter.rcm_cost_parity_service import ParityView, ParityViewRow


class RcmCostParityDialog(QDialog):
    """Read-only FM-parity tabel met filter op status."""

    def __init__(
        self,
        view: ParityView,
        *,
        project: RCMProject | None = None,
        fm_results: dict[str, FMResult] | None = None,
        project_path: Path | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._view = view
        self._project = project
        self._fm_results = fm_results or {}
        self._project_path = project_path
        self._all_rows = list(view.rows)

        self.setWindowTitle(messages.RCM_COST_PARITY_TITLE)
        layout = QVBoxLayout(self)

        intro = QLabel(messages.RCM_COST_PARITY_INTRO)
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self._summary_label = QLabel(view.summary.headline)
        layout.addWidget(self._summary_label)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Filter:"))
        self._filter_combo = QComboBox()
        for label in (
            messages.RCM_COST_PARITY_FILTER_ALL,
            messages.RCM_COST_PARITY_FILTER_FAIL,
            messages.RCM_COST_PARITY_FILTER_PASS,
        ):
            self._filter_combo.addItem(label)
        self._filter_combo.currentIndexChanged.connect(self._apply_filter)
        filter_row.addWidget(self._filter_combo)
        filter_row.addStretch(1)

        self._export_button = QPushButton(messages.RCM_COST_PARITY_EXPORT_BUTTON)
        self._export_button.setToolTip(messages.RCM_COST_PARITY_EXPORT_TOOLTIP)
        self._export_button.clicked.connect(self._export_validation)
        self._export_button.setEnabled(project is not None and bool(self._fm_results))
        filter_row.addWidget(self._export_button)
        layout.addLayout(filter_row)

        headers = messages.RCM_COST_PARITY_HEADERS
        self._table = QTableWidget(0, len(headers))
        self._table.setHorizontalHeaderLabels(list(headers))
        layout.addWidget(self._table)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._apply_filter()

    def visible_row_count(self) -> int:
        return self._table.rowCount()

    def _apply_filter(self) -> None:
        label = self._filter_combo.currentText()
        if label == messages.RCM_COST_PARITY_FILTER_FAIL:
            rows = [r for r in self._all_rows if r.verdict == ParityVerdict.FAIL]
        elif label == messages.RCM_COST_PARITY_FILTER_PASS:
            rows = [r for r in self._all_rows if r.verdict == ParityVerdict.PASS]
        else:
            rows = self._all_rows
        self._populate(rows)

    def _populate(self, rows: list[ParityViewRow]) -> None:
        self._table.setRowCount(len(rows))
        for idx, row in enumerate(rows):
            for col, text in enumerate(
                (
                    row.fm_id,
                    row.omschrijving,
                    row.verdict_label,
                    row.aw_total_cost,
                    row.rcm_total_cost,
                    row.cost_delta,
                    row.cost_tolerance,
                    row.aw_total_tdt,
                    row.rcm_total_tdt,
                    row.aw_expected_failures,
                    row.rcm_expected_failures,
                    row.failures_delta,
                    row.rev_moments,
                    row.rev_years,
                    row.rev_intervals,
                    row.aw_cm_downtime,
                    row.rcm_cm_downtime,
                    row.aw_pm_downtime,
                    row.rcm_pm_downtime,
                    row.aw_insp_downtime,
                    row.rcm_cm_cost,
                    row.rcm_pm_cost,
                    row.p_fail_rcm,
                    row.current_age,
                    row.mttf_aw,
                    row.mttf_rcm,
                    row.pm_tasks,
                )
            ):
                self._table.setItem(idx, col, QTableWidgetItem(text))
        self._table.resizeColumnsToContents()

    def _export_validation(self) -> None:
        if self._project is None or not self._fm_results:
            return
        default_name = f"{self._project.projectnaam or 'project'}_validatie_falen.xlsx"
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            messages.RCM_COST_PARITY_EXPORT_TITLE,
            default_name,
            messages.RCM_COST_PARITY_EXPORT_FILTER,
        )
        if not save_path:
            return
        path = Path(save_path)
        if path.suffix.lower() != ".xlsx":
            path = path.with_suffix(".xlsx")
        try:
            written = export_validation_excel(
                self._project, self._fm_results, path, input_file=self._project_path
            )
        except Exception as exc:  # pragma: no cover - UI fallback
            QMessageBox.warning(
                self,
                messages.RCM_COST_PARITY_EXPORT_TITLE,
                messages.RCM_COST_PARITY_EXPORT_FAILED.format(error=exc),
            )
            return
        QMessageBox.information(
            self,
            messages.RCM_COST_PARITY_EXPORT_TITLE,
            messages.RCM_COST_PARITY_EXPORT_SUCCESS.format(path=written),
        )


def show_rcm_cost_parity_dialog(
    view: ParityView,
    *,
    project: RCMProject | None = None,
    fm_results: dict[str, FMResult] | None = None,
    project_path: Path | None = None,
    parent: QWidget | None = None,
) -> None:
    dialog = RcmCostParityDialog(
        view,
        project=project,
        fm_results=fm_results,
        project_path=project_path,
        parent=parent,
    )
    dialog.exec()
