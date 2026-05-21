"""Import-wizard UI voor RCM-Cost Excel (issue 06)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from rcm_desktop import messages
from rcm_desktop.adapter.isograph_import_service import ImportConflict
from rcm_desktop.adapter.isograph_import_wizard_service import (
    ImportWizardResult,
    complete_import,
    initial_age_conflicts,
    preview_import,
)


@dataclass(frozen=True)
class ImportDialogInput:
    path: Path
    default_modeljaar: int = 2026


class IsographImportWizardDialog(QDialog):
    """Modeljaar + keuze bij tegenstrijdige initiële leeftijd per PBS."""

    def __init__(self, dialog_input: ImportDialogInput, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._input = dialog_input
        self._build_result = preview_import(
            dialog_input.path, modeljaar=dialog_input.default_modeljaar
        )
        self._conflicts = initial_age_conflicts(self._build_result)
        self._choice_widgets: dict[str, QComboBox] = {}
        self._result: ImportWizardResult | None = None

        self.setWindowTitle(messages.ISOGRAPH_IMPORT_DIALOG_TITLE)
        layout = QVBoxLayout(self)

        intro = QLabel(messages.ISOGRAPH_IMPORT_DIALOG_INTRO)
        intro.setWordWrap(True)
        layout.addWidget(intro)

        form = QFormLayout()
        self._modeljaar_spin = QSpinBox()
        self._modeljaar_spin.setRange(1900, 2200)
        self._modeljaar_spin.setValue(dialog_input.default_modeljaar)
        form.addRow(messages.ISOGRAPH_IMPORT_MODELJAAR_LABEL, self._modeljaar_spin)
        layout.addLayout(form)

        if self._conflicts:
            conflict_label = QLabel(messages.ISOGRAPH_IMPORT_CONFLICTS_INTRO)
            conflict_label.setWordWrap(True)
            layout.addWidget(conflict_label)
            conflict_form = QFormLayout()
            for conflict in self._conflicts:
                combo = QComboBox()
                for age_yr in conflict.values:
                    combo.addItem(
                        messages.ISOGRAPH_IMPORT_AGE_OPTION.format(age_years=age_yr),
                        age_yr,
                    )
                conflict_form.addRow(
                    messages.ISOGRAPH_IMPORT_CONFLICT_ROW.format(pbs_id=conflict.pbs_id),
                    combo,
                )
                self._choice_widgets[conflict.pbs_id] = combo
            layout.addLayout(conflict_form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def result_value(self) -> ImportWizardResult | None:
        return self._result

    def _on_accept(self) -> None:
        modeljaar = int(self._modeljaar_spin.value())
        choices: dict[str, float] = {}
        for pbs_id, combo in self._choice_widgets.items():
            age = combo.currentData()
            if age is not None:
                choices[pbs_id] = float(age)
        preview = preview_import(self._input.path, modeljaar=modeljaar)
        self._result = complete_import(
            preview, modeljaar=modeljaar, conflict_choices=choices or None
        )
        self.accept()


def run_import_wizard(
    dialog_input: ImportDialogInput,
    parent: QWidget | None = None,
) -> ImportWizardResult | None:
    dialog = IsographImportWizardDialog(dialog_input, parent=parent)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    return dialog.result_value()
