"""Portfolio-wizard dialoog (slice 64 issue 03)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from rcm_desktop import messages
from rcm_desktop.adapter.portfolio_wizard_service import (
    PortfolioWizardPreview,
    PortfolioWizardResult,
    complete_portfolio_merge,
    preview_portfolio_scan,
)


@dataclass(frozen=True)
class PortfolioWizardInput:
    scan_root: Path
    scan_root_label: str = ""


class PortfolioWizardDialog(QDialog):
    """Preview scan + selectie netwerkschakels voor portfolio-merge."""

    def __init__(
        self,
        dialog_input: PortfolioWizardInput,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._input = dialog_input
        self._preview: PortfolioWizardPreview = preview_portfolio_scan(
            dialog_input.scan_root,
            scan_root_label=dialog_input.scan_root_label,
        )
        self._result: PortfolioWizardResult | None = None

        self.setWindowTitle(messages.PORTFOLIO_WIZARD_TITLE)
        layout = QVBoxLayout(self)

        intro = QLabel(messages.PORTFOLIO_WIZARD_INTRO)
        intro.setWordWrap(True)
        layout.addWidget(intro)

        form = QFormLayout()
        root_label = QLabel(str(dialog_input.scan_root))
        root_label.setWordWrap(True)
        form.addRow(messages.PORTFOLIO_WIZARD_ROOT_LABEL, root_label)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText(dialog_input.scan_root_label or dialog_input.scan_root.name)
        form.addRow(messages.PORTFOLIO_WIZARD_NAME_LABEL, self._name_edit)
        layout.addLayout(form)

        headers = messages.PORTFOLIO_WIZARD_TABLE_HEADERS
        self._table = QTableWidget(len(self._preview.rows), len(headers))
        self._table.setHorizontalHeaderLabels(list(headers))
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        for row_idx, row in enumerate(self._preview.rows):
            values = (
                row.netwerkschakel_label,
                row.relative_path,
                str(row.fm_count),
                "" if row.lifecycle_years is None else f"{row.lifecycle_years:.0f}",
                "" if row.modeljaar is None else str(row.modeljaar),
            )
            for col, text in enumerate(values):
                item = QTableWidgetItem(text)
                if not row.loadable:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                else:
                    item.setCheckState(Qt.CheckState.Checked)
                self._table.setItem(row_idx, col, item)
        self._table.resizeColumnsToContents()
        layout.addWidget(self._table)

        if self._preview.config_warnings or self._preview.scan_errors:
            warn_lines = list(self._preview.config_warnings) + list(self._preview.scan_errors)
            warn = QLabel(
                f"{messages.PORTFOLIO_WIZARD_WARNINGS_LABEL}: " + "; ".join(warn_lines)
            )
            warn.setWordWrap(True)
            layout.addWidget(warn)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def result_value(self) -> PortfolioWizardResult | None:
        return self._result

    def _selected_relative_paths(self) -> list[str]:
        selected: list[str] = []
        for row_idx, row in enumerate(self._preview.rows):
            item = self._table.item(row_idx, 0)
            if item is None or not item.flags() & Qt.ItemFlag.ItemIsEnabled:
                continue
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(row.relative_path)
        return selected

    def _on_accept(self) -> None:
        name = self._name_edit.text().strip()
        if not name:
            name = self._input.scan_root_label or self._input.scan_root.name
        self._result = complete_portfolio_merge(
            self._preview,
            selected_relative_paths=self._selected_relative_paths(),
            portfolio_name=name,
        )
        self.accept()


def run_portfolio_wizard(
    dialog_input: PortfolioWizardInput,
    parent: QWidget | None = None,
) -> PortfolioWizardResult | None:
    dialog = PortfolioWizardDialog(dialog_input, parent=parent)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    return dialog.result_value()


def run_portfolio_wizard_with_root_picker(
    parent: QWidget | None = None,
) -> PortfolioWizardResult | None:
    """Open sync-root dialoog, daarna preview + merge wizard."""
    root = QFileDialog.getExistingDirectory(
        parent,
        messages.PORTFOLIO_OPEN_ROOT_DIALOG_TITLE,
    )
    if not root:
        return None
    return run_portfolio_wizard(
        PortfolioWizardInput(scan_root=Path(root)),
        parent=parent,
    )
