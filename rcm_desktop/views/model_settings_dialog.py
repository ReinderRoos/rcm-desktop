"""Modaal dialoog Modelinstellingen (slice 52)."""

from __future__ import annotations

import copy
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from rcm_desktop import messages
from rcm_desktop.adapter.model_settings_service import (
    ModelSettingsCommitResult,
    ModelSettingsDraft,
    apply_default_aging_to_fms,
    build_draft,
    commit_model_settings,
    count_aging_faalwijzen,
    dialog_title,
    validate_draft,
)


class ModelSettingsDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None,
        *,
        project,
        project_path: str | Path | None = None,
        save_to_disk: bool = False,
        baseline_mtime_ns: int | None = None,
    ) -> None:
        super().__init__(parent)
        self._source_project = project
        self._working_project = copy.deepcopy(project)
        self._baseline = build_draft(project)
        self._path = Path(project_path) if project_path else None
        self._save_to_disk = save_to_disk
        self._baseline_mtime_ns = baseline_mtime_ns
        self._aging_fm_ids_applied: tuple[str, ...] = ()
        self.commit_result: ModelSettingsCommitResult | None = None

        self.setWindowTitle(dialog_title(project, project_path))
        self.setMinimumWidth(480)

        root = QVBoxLayout(self)
        root.addWidget(self._build_project_section())
        root.addWidget(self._build_horizon_section())
        root.addWidget(self._build_aging_section())
        root.addWidget(self._build_failparams_section())
        root.addWidget(self._build_monte_carlo_section())

        self._rerun_checkbox = QCheckBox(messages.MODEL_SETTINGS_RERUN_CHECKBOX)
        self._rerun_checkbox.setChecked(False)
        self._rerun_checkbox.setEnabled(False)
        root.addWidget(self._rerun_checkbox)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self._sync_rerun_enabled()

    def _build_project_section(self) -> QGroupBox:
        box = QGroupBox(messages.MODEL_SETTINGS_SECTION_PROJECT)
        form = QFormLayout(box)
        self._projectnaam = QLineEdit(self._working_project.projectnaam)
        self._modelleur = QLineEdit(self._working_project.modelleur)
        form.addRow(messages.MODEL_SETTINGS_PROJECTNAAM, self._projectnaam)
        form.addRow(messages.MODEL_SETTINGS_MODELLEUR, self._modelleur)
        return box

    def _build_horizon_section(self) -> QGroupBox:
        box = QGroupBox(messages.MODEL_SETTINGS_SECTION_HORIZON)
        form = QFormLayout(box)
        cfg = self._working_project.config
        self._lifecycle = QDoubleSpinBox()
        self._lifecycle.setRange(1.0, 500.0)
        self._lifecycle.setDecimals(1)
        self._lifecycle.setValue(float(cfg.lifecycle_years))
        self._modeljaar = QSpinBox()
        self._modeljaar.setRange(1900, 2200)
        self._modeljaar.setValue(int(cfg.modeljaar))
        interval_label = QLabel(messages.MODEL_SETTINGS_BUCKET_INTERVAL_VALUE)
        interval_label.setEnabled(False)
        form.addRow(messages.MODEL_SETTINGS_LIFECYCLE, self._lifecycle)
        form.addRow(messages.MODEL_SETTINGS_MODELJAAR, self._modeljaar)
        form.addRow(messages.MODEL_SETTINGS_BUCKET_INTERVAL, interval_label)
        self._lifecycle.valueChanged.connect(self._sync_rerun_enabled)
        self._modeljaar.valueChanged.connect(self._sync_rerun_enabled)
        return box

    def _build_aging_section(self) -> QGroupBox:
        box = QGroupBox(messages.MODEL_SETTINGS_SECTION_AGING)
        layout = QVBoxLayout(box)
        form = QFormLayout()
        cfg = self._working_project.config
        self._aging_distribution = QComboBox()
        self._aging_distribution.addItem("Normaal", "normal")
        self._aging_distribution.addItem("Links-afgeknipt normal 0+", "truncated_normal_0")
        self._aging_distribution.addItem("Weibull 2p", "weibull_2p")
        idx = self._aging_distribution.findData(cfg.default_aging_distribution or "normal")
        if idx >= 0:
            self._aging_distribution.setCurrentIndex(idx)
        self._default_beta = QDoubleSpinBox()
        self._default_beta.setRange(0.01, 100.0)
        self._default_beta.setDecimals(2)
        self._default_beta.setValue(float(cfg.default_beta_jaar or 0.0))
        form.addRow(messages.MODEL_SETTINGS_DEFAULT_AGING_DISTRIBUTION, self._aging_distribution)
        form.addRow(messages.MODEL_SETTINGS_DEFAULT_BETA, self._default_beta)
        layout.addLayout(form)
        self._apply_aging_btn = QPushButton(messages.MODEL_SETTINGS_APPLY_AGING)
        self._apply_aging_btn.clicked.connect(self._on_apply_aging)
        layout.addWidget(self._apply_aging_btn)
        self._aging_distribution.currentIndexChanged.connect(self._sync_beta_visibility)
        self._aging_distribution.currentIndexChanged.connect(self._sync_rerun_enabled)
        self._default_beta.valueChanged.connect(self._sync_rerun_enabled)
        self._sync_beta_visibility()
        return box

    def _build_failparams_section(self) -> QGroupBox:
        box = QGroupBox(messages.MODEL_SETTINGS_SECTION_FAILPARAMS)
        form = QFormLayout(box)
        cfg = self._working_project.config
        self._mttf_multiplier = QDoubleSpinBox()
        self._mttf_multiplier.setRange(0.01, 10.0)
        self._mttf_multiplier.setDecimals(3)
        self._mttf_multiplier.setValue(float(cfg.default_mttf_multiplier))
        self._mttf_multiplier.setToolTip(messages.MODEL_SETTINGS_DEFAULT_MTTF_MULTIPLIER_TTIP)
        self._sigma_fraction = QDoubleSpinBox()
        self._sigma_fraction.setRange(0.01, 1.0)
        self._sigma_fraction.setDecimals(3)
        self._sigma_fraction.setValue(float(cfg.default_sigma_fraction))
        form.addRow(messages.MODEL_SETTINGS_DEFAULT_MTTF_MULTIPLIER, self._mttf_multiplier)
        form.addRow(messages.MODEL_SETTINGS_DEFAULT_SIGMA_FRACTION, self._sigma_fraction)
        self._mttf_multiplier.valueChanged.connect(self._sync_rerun_enabled)
        self._sigma_fraction.valueChanged.connect(self._sync_rerun_enabled)
        return box

    def _build_monte_carlo_section(self) -> QGroupBox:
        box = QGroupBox(messages.MODEL_SETTINGS_SECTION_MONTE_CARLO)
        form = QFormLayout(box)
        cfg = self._working_project.config
        self._mc_n = QSpinBox()
        self._mc_n.setRange(100, 1_000_000)
        self._mc_n.setValue(int(cfg.monte_carlo_n))
        self._mc_n.setEnabled(False)
        self._mc_n.setToolTip(messages.MODEL_SETTINGS_MONTE_CARLO_DISABLED_TTIP)
        seed_label = QLabel(str(cfg.monte_carlo_seed) if cfg.monte_carlo_seed is not None else "—")
        seed_label.setEnabled(False)
        seed_label.setToolTip(messages.MODEL_SETTINGS_MONTE_CARLO_DISABLED_TTIP)
        form.addRow(messages.MODEL_SETTINGS_MONTE_CARLO_N, self._mc_n)
        form.addRow(messages.MODEL_SETTINGS_MONTE_CARLO_SEED, seed_label)
        box.setToolTip(messages.MODEL_SETTINGS_MONTE_CARLO_DISABLED_TTIP)
        return box

    def _sync_beta_visibility(self) -> None:
        is_weibull = self._aging_distribution.currentData() == "weibull_2p"
        self._default_beta.setEnabled(is_weibull)

    def _current_draft(self) -> ModelSettingsDraft:
        cfg = self._working_project.config
        return ModelSettingsDraft(
            projectnaam=self._projectnaam.text().strip(),
            modelleur=self._modelleur.text().strip(),
            lifecycle_years=float(self._lifecycle.value()),
            modeljaar=int(self._modeljaar.value()),
            default_mttf_multiplier=float(self._mttf_multiplier.value()),
            default_sigma_fraction=float(self._sigma_fraction.value()),
            default_aging_distribution=str(self._aging_distribution.currentData()),
            default_beta_jaar=float(self._default_beta.value()),
            monte_carlo_n=int(cfg.monte_carlo_n),
            monte_carlo_seed=cfg.monte_carlo_seed,
        )

    def _sync_rerun_enabled(self) -> None:
        from rcm_desktop.adapter.model_settings_service import compute_requires_rerun

        draft = self._current_draft()
        requires = compute_requires_rerun(
            self._baseline,
            draft,
            aging_fm_ids_applied=self._aging_fm_ids_applied,
        )
        self._rerun_checkbox.setEnabled(requires)

    def _on_apply_aging(self) -> None:
        draft = self._current_draft()
        errors = validate_draft(draft)
        if errors:
            QMessageBox.warning(self, messages.MODEL_SETTINGS_VALIDATION_TITLE, errors[0])
            return
        count = count_aging_faalwijzen(self._working_project)
        if count == 0:
            QMessageBox.information(
                self,
                messages.MODEL_SETTINGS_SECTION_AGING,
                "Geen aging-faalwijzen in dit project.",
            )
            return
        dist_label = self._aging_distribution.currentText()
        beta_line = ""
        if draft.default_aging_distribution == "weibull_2p":
            beta_line = messages.MODEL_SETTINGS_APPLY_AGING_BETA_LINE.format(
                beta=draft.default_beta_jaar
            )
        confirm = messages.MODEL_SETTINGS_APPLY_AGING_CONFIRM.format(
            count=count,
            dist=dist_label,
            beta_line=beta_line,
        )
        answer = QMessageBox.question(
            self,
            messages.MODEL_SETTINGS_APPLY_AGING,
            confirm,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        updated, result = apply_default_aging_to_fms(self._working_project, draft)
        self._working_project = updated
        self._aging_fm_ids_applied = result.fm_ids
        self._sync_rerun_enabled()

    def _on_accept(self) -> None:
        draft = self._current_draft()
        errors = validate_draft(draft)
        if errors:
            QMessageBox.warning(self, messages.MODEL_SETTINGS_VALIDATION_TITLE, errors[0])
            return
        result = commit_model_settings(
            self._source_project,
            draft,
            baseline=self._baseline,
            project_path=self._path,
            save_to_disk=self._save_to_disk,
            baseline_mtime_ns=self._baseline_mtime_ns,
            working_project=self._working_project,
            aging_fm_ids_applied=self._aging_fm_ids_applied,
            run_after_commit=self._rerun_checkbox.isChecked(),
        )
        if not result.ok:
            detail = result.errors[0] if result.errors else "Onbekende fout"
            QMessageBox.warning(
                self,
                messages.MODEL_SETTINGS_VALIDATION_TITLE,
                messages.MODEL_SETTINGS_COMMIT_FAILED.format(detail=detail),
            )
            return
        self.commit_result = result
        self.accept()
