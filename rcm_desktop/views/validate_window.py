from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QToolButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from rcm_desktop import messages
from rcm_desktop.adapter.fm_results_table_model import FMResultsTableModel, RAW_ROLE
from rcm_desktop.adapter.project_paths import resolve_default_fixture_path
from rcm_desktop.adapter.preview_service import ProjectPreview
from rcm_desktop.adapter.run_runner import RunRunner
from rcm_desktop.adapter.run_service import RunResult
from rcm_desktop.adapter.validate_runner import ValidateRunner
from rcm_desktop.adapter.validate_service import DetailItem, ValidateResult, UserFacingError
from rcm_desktop.app_state import AppState
from rcm_desktop.formatting import format_eur, format_float, format_int


class ValidateWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("RCM2 desktop — validate tracer-bullet")

        self._state = AppState()
        self._runner = ValidateRunner()
        self._run_runner = RunRunner()
        self._runner.state_changed.connect(self._on_runner_state_changed)
        self._runner.result_ready.connect(self._on_result_ready)
        self._runner.preview_ready.connect(self._on_preview_ready)
        self._runner.project_ready.connect(self._on_project_ready)
        self._run_runner.state_changed.connect(self._on_run_state_changed)
        self._run_runner.result_ready.connect(self._on_run_result_ready)
        self._state.result_changed.connect(self._render_result)
        self._state.preview_changed.connect(self._render_preview)
        self._state.project_changed.connect(lambda _project: self._update_run_button_enabled())
        self._state.run_changed.connect(self._render_run_result)

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Pad naar projectbestand (*.rcm.json)")
        self.path_input.textChanged.connect(self._on_path_changed)
        self.pick_button = QPushButton("Kies bestand")
        self.pick_button.clicked.connect(self._pick_file)
        self.validate_button = QPushButton("Validate")
        self.validate_button.clicked.connect(self._start_validate)
        self.run_button = QPushButton("Run --full")
        self.run_button.setEnabled(False)
        self.run_button.clicked.connect(self._start_run)
        self.status_label = QLabel(messages.status_label("idle"))
        self.summary_label = QLabel("")
        self.preview_group = QGroupBox(messages.PREVIEW_GROUP_TITLE)
        preview_layout = QVBoxLayout(self.preview_group)
        preview_counts = QFormLayout()
        self.preview_pbs_value = QLabel("0")
        self.preview_functies_value = QLabel("0")
        self.preview_faalwijzes_value = QLabel("0")
        self.preview_pm_tasks_value = QLabel("0")
        preview_counts.addRow(messages.PREVIEW_LABEL_PBS, self.preview_pbs_value)
        preview_counts.addRow(messages.PREVIEW_LABEL_FUNCTIES, self.preview_functies_value)
        preview_counts.addRow(messages.PREVIEW_LABEL_FAALWIJZES, self.preview_faalwijzes_value)
        preview_counts.addRow(messages.PREVIEW_LABEL_PM_TASKS, self.preview_pm_tasks_value)
        preview_layout.addLayout(preview_counts)
        preview_layout.addWidget(QLabel(messages.PREVIEW_TOP5_TITLE))
        self.preview_top5_list = QListWidget()
        preview_layout.addWidget(self.preview_top5_list)
        self.preview_group.setVisible(False)
        self.run_group = QGroupBox(messages.RUN_GROUP_TITLE)
        run_layout = QVBoxLayout(self.run_group)
        run_values = QFormLayout()
        self.run_status_value = QLabel("")
        self.run_summary_value = QLabel("")
        self.run_fm_result_count_value = QLabel("0")
        self.run_total_faalmomenten_value = QLabel("0.0")
        self.run_total_cost_value = QLabel("0.0")
        run_values.addRow(messages.RUN_LABEL_STATUS, self.run_status_value)
        run_values.addRow(messages.RUN_LABEL_SUMMARY, self.run_summary_value)
        run_values.addRow(messages.RUN_LABEL_FM_RESULTS, self.run_fm_result_count_value)
        run_values.addRow(messages.RUN_LABEL_TOTAL_FAALMOMENTEN, self.run_total_faalmomenten_value)
        run_values.addRow(messages.RUN_LABEL_TOTAL_COST_EUR, self.run_total_cost_value)
        run_layout.addLayout(run_values)
        self.run_group.setVisible(False)
        self.result_table_group = QGroupBox(messages.FM_RESULTS_GROUP_TITLE)
        result_table_layout = QVBoxLayout(self.result_table_group)
        self.result_table = QTableView()
        self.result_table.setSortingEnabled(True)
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.result_table_proxy = QSortFilterProxyModel(self.result_table)
        self.result_table_proxy.setSortRole(RAW_ROLE)
        self.result_table.setModel(self.result_table_proxy)
        result_table_layout.addWidget(self.result_table)
        self.result_table_group.setVisible(False)
        self.details_toggle = QToolButton()
        self.details_toggle.setText("Toon details")
        self.details_toggle.setCheckable(True)
        self.details_toggle.setChecked(False)
        self.details_toggle.setEnabled(False)
        self.details_toggle.toggled.connect(self._on_toggle_details)
        self.details_text = QPlainTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setVisible(False)

        self._build_layout()
        self._set_default_fixture_path()

    def _build_layout(self) -> None:
        root = QWidget()
        outer = QVBoxLayout(root)
        row = QHBoxLayout()
        row.addWidget(self.path_input)
        row.addWidget(self.pick_button)
        row.addWidget(self.validate_button)
        row.addWidget(self.run_button)

        outer.addLayout(row)
        outer.addWidget(self.status_label)
        outer.addWidget(self.summary_label)
        outer.addWidget(self.preview_group)
        outer.addWidget(self.run_group)
        outer.addWidget(self.result_table_group)
        outer.addWidget(self.details_toggle)
        outer.addWidget(self.details_text)
        self.setCentralWidget(root)
        self.resize(760, 440)

    def _set_default_fixture_path(self) -> None:
        default_path = resolve_default_fixture_path()
        if default_path is None:
            self.summary_label.setText(messages.ERROR_DEFAULT_FIXTURE_MISSING)
            return
        self.path_input.setText(str(default_path))

    def _pick_file(self) -> None:
        filename, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Kies projectbestand",
            self.path_input.text() or str(Path.cwd()),
            "RCM JSON (*.rcm.json);;JSON (*.json)",
        )
        if filename:
            self.path_input.setText(filename)

    def _start_validate(self) -> None:
        path = self.path_input.text().strip()
        self._clear_result_view()
        self._clear_run_view()
        if not path:
            self._show_error(messages.ERROR_EMPTY_PATH)
            return
        started = self._runner.start(path)
        if started:
            self.validate_button.setEnabled(False)

    def _clear_result_view(self) -> None:
        self.summary_label.clear()
        self.details_text.clear()
        self.details_toggle.setChecked(False)
        self.details_text.setVisible(False)
        self._state.set_last_preview(None)

    def _clear_run_view(self) -> None:
        self.run_group.setVisible(False)
        self._clear_result_table()
        self.run_status_value.clear()
        self.run_summary_value.clear()
        self.run_fm_result_count_value.setText("0")
        self.run_total_faalmomenten_value.setText("0.0")
        self.run_total_cost_value.setText("0.0")
        self._state.set_last_run(None)
        self._update_run_button_enabled()

    def _clear_result_table(self) -> None:
        self.result_table_group.setVisible(False)
        self.result_table_proxy.setSourceModel(None)

    def _on_runner_state_changed(self, state: str) -> None:
        if state == "busy":
            self.status_label.setText(messages.status_label("busy"))
            return
        if state == "idle":
            self.validate_button.setEnabled(True)
            self._update_run_button_enabled()

    def _on_result_ready(self, result: object) -> None:
        if isinstance(result, ValidateResult):
            self._state.set_last_result(result)

    def _on_preview_ready(self, preview: object) -> None:
        if isinstance(preview, ProjectPreview):
            self._state.set_last_preview(preview)
            return
        self._state.set_last_preview(None)

    def _on_project_ready(self, project: object) -> None:
        if project is None:
            self._state.set_last_project(None)
        else:
            self._state.set_last_project(project)
        self._update_run_button_enabled()

    def _start_run(self) -> None:
        path = self.path_input.text().strip()
        self._clear_run_view()
        started = self._run_runner.start(self._state.last_project, path)
        if started:
            self.run_button.setEnabled(False)

    def _on_run_state_changed(self, state: str) -> None:
        if state == "busy":
            self.run_group.setVisible(True)
            self.run_status_value.setText(messages.status_label("busy"))
        self._update_run_button_enabled()

    def _on_run_result_ready(self, result: object) -> None:
        if isinstance(result, RunResult):
            self._state.set_last_run(result)

    def _render_result(self, result: object) -> None:
        if not isinstance(result, ValidateResult):
            return
        self.status_label.setText(messages.status_label(result.status))
        self.summary_label.setText(result.summary)
        self.details_text.setPlainText(self._format_details(result.details))
        self.details_toggle.setEnabled(bool(result.details))
        if result.error is not None:
            self._show_error(result.error.message)
        self._update_run_button_enabled()

    def _render_preview(self, preview: object) -> None:
        if not isinstance(preview, ProjectPreview):
            self.preview_group.setVisible(False)
            self.preview_top5_list.clear()
            return

        self.preview_group.setVisible(True)
        self.preview_pbs_value.setText(str(preview.pbs_items))
        self.preview_functies_value.setText(str(preview.functies))
        self.preview_faalwijzes_value.setText(str(preview.faalwijzes))
        self.preview_pm_tasks_value.setText(str(preview.pm_tasks))
        self.preview_top5_list.clear()
        if not preview.top_faalwijzes:
            self.preview_top5_list.addItem(messages.PREVIEW_EMPTY_TOP5)
            return
        for item in preview.top_faalwijzes:
            self.preview_top5_list.addItem(f"{item.fm_id} — {item.faalwijze_omschrijving}")

    def _render_run_result(self, run_result: object) -> None:
        if not isinstance(run_result, RunResult):
            self.run_group.setVisible(False)
            self._clear_result_table()
            return
        self.run_group.setVisible(True)
        self.run_status_value.setText(messages.status_label(run_result.status))
        self.run_summary_value.setText(run_result.summary)
        self.run_fm_result_count_value.setText(format_int(run_result.metrics.fm_result_count))
        self.run_total_faalmomenten_value.setText(format_float(run_result.metrics.total_lifecycle_faalmomenten))
        self.run_total_cost_value.setText(format_eur(run_result.metrics.total_cost_eur))
        if run_result.status == "done" and run_result.rows:
            model = FMResultsTableModel(run_result.rows, self.result_table)
            self.result_table_proxy.setSourceModel(model)
            self.result_table_group.setVisible(True)
            self.result_table.sortByColumn(6, Qt.DescendingOrder)
        else:
            self._clear_result_table()
        if run_result.error is not None:
            self._show_run_error(run_result.error)
        self._update_run_button_enabled()

    def _update_run_button_enabled(self) -> None:
        validation_ok = (
            self._state.last_result is not None
            and self._state.last_result.status in {"valid", "valid_with_warnings"}
        )
        can_run = validation_ok and self._state.last_project is not None and not self._run_runner.busy
        self.run_button.setEnabled(can_run)

    def _on_path_changed(self, _text: str) -> None:
        self._clear_run_view()

    def _on_toggle_details(self, checked: bool) -> None:
        self.details_text.setVisible(checked)
        self.details_toggle.setText("Verberg details" if checked else "Toon details")

    def _format_details(self, details: list[DetailItem]) -> str:
        lines = []
        for item in details:
            context = f" [{item.context}]" if item.context else ""
            lines.append(f"{item.severity.upper()} {item.code}{context}: {item.message}")
        return "\n".join(lines)

    def _show_error(self, message: str) -> None:
        self.status_label.setText(messages.status_label("error"))
        QMessageBox.critical(self, messages.ERROR_DIALOG_TITLE, message)

    def _show_run_error(self, error: UserFacingError) -> None:
        self.run_status_value.setText(messages.status_label("error"))
        QMessageBox.critical(self, messages.RUN_ERROR_DIALOG_TITLE, error.message)
