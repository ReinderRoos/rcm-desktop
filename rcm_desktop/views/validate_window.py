from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QModelIndex, Qt, QSortFilterProxyModel, QSettings
from PySide6.QtGui import QColor, QCloseEvent, QKeySequence, QAction
from PySide6.QtWidgets import (
    QAbstractItemView,
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
    QTableWidget,
    QTableWidgetItem,
    QSpinBox,
    QSplitter,
    QToolButton,
    QTableView,
    QTreeView,
    QVBoxLayout,
    QWidget,
)
try:
    from PySide6.QtCharts import QBarCategoryAxis, QBarSeries, QBarSet, QChart, QChartView, QValueAxis

    HAS_QT_CHARTS = True
except ImportError:  # pragma: no cover - fallback for environments without QtCharts
    HAS_QT_CHARTS = False

from rcm_desktop import messages
from rcm_desktop.adapter.faalwijzen_edit_service import (
    FaalwijzenEditService,
    FaalwijzenMaterializeBlockedError,
)
from rcm_desktop.adapter.faalwijzen_grid_registry import (
    set_active_grid_service,
    set_grid_save_handler,
)
from rcm_desktop.views.validate_faalwijzen_panel import ValidateFaalwijzenPanel
from rcm_desktop.adapter.compare_runner import CompareRunner
from rcm_desktop.adapter.fm_results_table_model import (
    FMResultsSortProxy,
    FMResultsTableModel,
    RAW_ROLE,
)
from rcm_desktop.adapter.ltap_bundle_service import apply_bundle_shift, reset_overlay
from rcm_desktop.adapter.ltap_service import LTAPTaskDetail, LTAPView, LTAPYearRow, build_ltap_view
from rcm_desktop.adapter.pbs_results_tree_model import PBSResultsTreeModel
from rcm_desktop.adapter.project_paths import resolve_default_fixture_path
from rcm_desktop.adapter.preview_service import ProjectPreview
from rcm_desktop.adapter.run_runner import RunRunner
from rcm_desktop.adapter.save_service import SaveConflictError, current_mtime_ns, save_project_atomically
from rcm_desktop.adapter.run_service import RunResult
from rcm_desktop.adapter.scenario_compare_service import ScenarioCompareView
from rcm_desktop.adapter.validate_runner import ValidateRunner
from rcm_desktop.adapter.result_view_service import build_pbs_tree
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
        self._compare_runner = CompareRunner()
        self._runner.state_changed.connect(self._on_runner_state_changed)
        self._runner.result_ready.connect(self._on_result_ready)
        self._runner.preview_ready.connect(self._on_preview_ready)
        self._runner.project_ready.connect(self._on_project_ready)
        self._run_runner.state_changed.connect(self._on_run_state_changed)
        self._run_runner.result_ready.connect(self._on_run_result_ready)
        self._compare_runner.state_changed.connect(self._on_compare_state_changed)
        self._compare_runner.result_ready.connect(self._on_compare_result_ready)
        self._state.result_changed.connect(self._render_result)
        self._state.preview_changed.connect(self._render_preview)
        self._state.project_changed.connect(self._on_state_project_changed)
        self._state.run_changed.connect(self._render_run_result)

        self._faalwijzen_edit = FaalwijzenEditService()
        self._faalwijzen_panel: ValidateFaalwijzenPanel | None = None
        self._active_project_path: Path | None = None
        self._loaded_path_mtime_ns: int | None = None
        self._suppress_path_change = False
        self._ltap_overlay_anchor_years: dict[str, float] = {}
        self._ltap_baseline_view: LTAPView | None = None
        self._ltap_current_view: LTAPView | None = None
        self._ltap_baseline_run: RunResult | None = None
        self._ltap_year_rows: dict[int, LTAPYearRow] = {}
        self._ltap_selected_year: int | None = None
        self._ltap_filter_mode = "all"
        self._panel_widgets: dict[str, QWidget] = {}
        self._panel_visibility: dict[str, bool] = {}
        self._active_result_panel = "fm"
        self._manual_result_override = False

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Pad naar projectbestand (*.rcm.json)")
        self.path_input.textChanged.connect(self._on_path_changed)
        self.pick_button = QPushButton(messages.PICK_BUTTON_LABEL)
        self.pick_button.clicked.connect(self._pick_file)
        self.validate_button = QPushButton(messages.VALIDATE_BUTTON_LABEL)
        self.validate_button.clicked.connect(self._start_validate)
        self.run_button = QPushButton(messages.RUN_BUTTON_LABEL)
        self.run_button.setEnabled(False)
        self.run_button.clicked.connect(self._start_run)
        self.compare_button = QPushButton(messages.COMPARE_BUTTON_LABEL)
        self.compare_button.setEnabled(False)
        self.compare_button.clicked.connect(self._start_compare)
        self.save_button = QPushButton("Opslaan")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self._save_current)
        self.save_as_button = QPushButton("Opslaan als...")
        self.save_as_button.setEnabled(False)
        self.save_as_button.clicked.connect(self._save_as)
        self.result_focus_fm_button = QToolButton()
        self.result_focus_fm_button.setText(messages.RESULT_FOCUS_FM_BUTTON)
        self.result_focus_fm_button.setCheckable(True)
        self.result_focus_fm_button.clicked.connect(lambda: self._set_active_result_panel("fm", manual=True))
        self.result_focus_pbs_button = QToolButton()
        self.result_focus_pbs_button.setText(messages.RESULT_FOCUS_PBS_BUTTON)
        self.result_focus_pbs_button.setCheckable(True)
        self.result_focus_pbs_button.clicked.connect(lambda: self._set_active_result_panel("pbs", manual=True))
        self.toggle_preview_button = QToolButton()
        self.toggle_preview_button.setText(messages.PANEL_TOGGLE_PREVIEW)
        self.toggle_preview_button.setCheckable(True)
        self.toggle_preview_button.toggled.connect(
            lambda checked: self._set_panel_visible("preview", checked, from_toggle=True)
        )
        self.toggle_faalwijzen_button = QToolButton()
        self.toggle_faalwijzen_button.setText(messages.PANEL_TOGGLE_FAALWIJZEN)
        self.toggle_faalwijzen_button.setCheckable(True)
        self.toggle_faalwijzen_button.toggled.connect(
            lambda checked: self._set_panel_visible("faalwijzen", checked, from_toggle=True)
        )
        self.toggle_compare_button = QToolButton()
        self.toggle_compare_button.setText(messages.PANEL_TOGGLE_COMPARE)
        self.toggle_compare_button.setCheckable(True)
        self.toggle_compare_button.toggled.connect(
            lambda checked: self._set_panel_visible("compare", checked, from_toggle=True)
        )
        self.reset_layout_button = QPushButton(messages.PANEL_RESET_LAYOUT_BUTTON)
        self.reset_layout_button.clicked.connect(self._reset_layout_defaults)
        for button in (
            self.validate_button,
            self.run_button,
            self.compare_button,
            self.save_button,
            self.save_as_button,
            self.reset_layout_button,
        ):
            button.setMinimumHeight(30)

        self.idle_banner = QWidget()
        idle_layout = QVBoxLayout(self.idle_banner)
        self.status_label = QLabel(messages.status_label("idle"))
        self.summary_label = QLabel("")
        idle_layout.addWidget(self.status_label)
        idle_layout.addWidget(self.summary_label)

        self.preview_group = QGroupBox(messages.OVERVIEW_STRIP_GROUP_TITLE)
        strip_layout = QHBoxLayout(self.preview_group)

        self.strip_left_column = QWidget()
        preview_counts = QFormLayout(self.strip_left_column)
        self.preview_pbs_value = QLabel("0")
        self.preview_functies_value = QLabel("0")
        self.preview_faalwijzes_value = QLabel("0")
        self.preview_pm_tasks_value = QLabel("0")
        preview_counts.addRow(messages.PREVIEW_LABEL_PBS, self.preview_pbs_value)
        preview_counts.addRow(messages.PREVIEW_LABEL_FUNCTIES, self.preview_functies_value)
        preview_counts.addRow(messages.PREVIEW_LABEL_FAALWIJZES, self.preview_faalwijzes_value)
        preview_counts.addRow(messages.PREVIEW_LABEL_PM_TASKS, self.preview_pm_tasks_value)
        strip_layout.addWidget(self.strip_left_column)

        self.strip_middle_column = QWidget()
        middle_outer = QVBoxLayout(self.strip_middle_column)
        self.strip_validate_face = QWidget()
        validate_face_layout = QVBoxLayout(self.strip_validate_face)
        self.strip_validate_status_label = QLabel("")
        self.strip_validate_summary_label = QLabel("")
        self.strip_validate_summary_label.setWordWrap(True)
        validate_face_layout.addWidget(self.strip_validate_status_label)
        validate_face_layout.addWidget(self.strip_validate_summary_label)

        self.strip_run_face = QWidget()
        run_face_layout = QVBoxLayout(self.strip_run_face)
        run_values = QFormLayout()
        self.run_status_value = QLabel("")
        self.run_summary_value = QLabel("")
        self.run_fm_result_count_value = QLabel("0")
        self.run_total_faalmomenten_value = QLabel("0.0")
        self.run_total_cost_value = QLabel("0.0")
        self.run_total_cost_value.setStyleSheet("font-weight: 700;")
        run_values.addRow(messages.RUN_LABEL_STATUS, self.run_status_value)
        run_values.addRow(messages.RUN_LABEL_SUMMARY, self.run_summary_value)
        run_values.addRow(messages.RUN_LABEL_FM_RESULTS, self.run_fm_result_count_value)
        run_values.addRow(messages.RUN_LABEL_TOTAL_FAALMOMENTEN, self.run_total_faalmomenten_value)
        run_values.addRow(messages.RUN_LABEL_TOTAL_COST_EUR, self.run_total_cost_value)
        run_face_layout.addLayout(run_values)

        middle_outer.addWidget(self.strip_validate_face)
        middle_outer.addWidget(self.strip_run_face)
        strip_layout.addWidget(self.strip_middle_column, stretch=1)

        self.strip_right_column = QWidget()
        right_col_layout = QVBoxLayout(self.strip_right_column)
        right_col_layout.addWidget(QLabel(messages.PREVIEW_TOP5_TITLE))
        self.preview_top5_list = QListWidget()
        right_col_layout.addWidget(self.preview_top5_list)
        strip_layout.addWidget(self.strip_right_column)

        self.preview_group.setVisible(False)
        self._faalwijzen_panel = ValidateFaalwijzenPanel()
        self._faalwijzen_panel.setVisible(False)
        self.result_table_group = QGroupBox(messages.FM_RESULTS_GROUP_TITLE)
        result_table_layout = QVBoxLayout(self.result_table_group)
        self.result_table = QTableView()
        self.result_table.setSortingEnabled(True)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.result_table_proxy = FMResultsSortProxy(self.result_table)
        self.result_table.setModel(self.result_table_proxy)
        result_table_layout.addWidget(self.result_table)
        self.result_table_group.setVisible(False)
        self.pbs_table_group = QGroupBox(messages.PBS_RESULTS_GROUP_TITLE)
        pbs_panel_layout = QVBoxLayout(self.pbs_table_group)
        self.pbs_tree = QTreeView()
        self.pbs_tree.setSortingEnabled(False)
        self.pbs_tree.setAlternatingRowColors(True)
        self.pbs_tree.header().setSectionResizeMode(QHeaderView.Stretch)
        pbs_panel_layout.addWidget(self.pbs_tree)
        self.pbs_table_group.setVisible(False)
        self.result_stack_group = QGroupBox("Resultaten")
        result_stack_layout = QVBoxLayout(self.result_stack_group)
        result_stack_layout.addWidget(self.result_table_group)
        result_stack_layout.addWidget(self.pbs_table_group)
        self.result_stack_group.setVisible(False)
        self.compare_group = QGroupBox(messages.COMPARE_GROUP_TITLE)
        compare_layout = QVBoxLayout(self.compare_group)
        self.compare_summary_label = QLabel("")
        self.compare_kpi_list = QListWidget()
        compare_layout.addWidget(self.compare_summary_label)
        compare_layout.addWidget(self.compare_kpi_list)
        self.compare_group.setVisible(False)
        self.ltap_group = QGroupBox(messages.LTAP_GROUP_TITLE)
        ltap_layout = QVBoxLayout(self.ltap_group)
        ltap_controls = QHBoxLayout()
        ltap_controls.addWidget(QLabel(messages.LTAP_SELECT_LABEL))
        self.ltap_select_input = QLineEdit()
        self.ltap_select_input.setReadOnly(True)
        self.ltap_select_input.setPlaceholderText(messages.LTAP_CONTEXT_SELECTION_EMPTY)
        self.ltap_select_input.setToolTip("Taaklabels gebruiken SVO/WET/TG voor taaktype, wettelijke status en taakgroep.")
        ltap_controls.addWidget(self.ltap_select_input, stretch=1)
        ltap_controls.addWidget(QLabel(messages.LTAP_SHIFT_LABEL))
        self.ltap_shift_spin = QSpinBox()
        self.ltap_shift_spin.setMinimum(-50)
        self.ltap_shift_spin.setMaximum(50)
        ltap_controls.addWidget(self.ltap_shift_spin)
        self.ltap_apply_button = QPushButton(messages.LTAP_APPLY_BUTTON)
        self.ltap_apply_button.setToolTip("Pas de bundel toe op de geselecteerde zichtbare LTAP-taken.")
        self.ltap_apply_button.clicked.connect(self._apply_ltap_bundle)
        ltap_controls.addWidget(self.ltap_apply_button)
        self.ltap_filter_button = QPushButton(messages.LTAP_FILTER_REV_ONLY_BUTTON)
        self.ltap_filter_button.setToolTip("Schakel tussen alle taken en alleen REV-taken.")
        self.ltap_filter_button.clicked.connect(self._toggle_ltap_filter_mode)
        ltap_controls.addWidget(self.ltap_filter_button)
        self.ltap_reset_button = QPushButton(messages.LTAP_RESET_BUTTON)
        self.ltap_reset_button.setToolTip("Verwijder de what-if overlay en herstel LTAP-baseline.")
        self.ltap_reset_button.clicked.connect(self._reset_ltap_bundle)
        ltap_controls.addWidget(self.ltap_reset_button)
        ltap_layout.addLayout(ltap_controls)
        self.ltap_context_label = QLabel("")
        ltap_layout.addWidget(self.ltap_context_label)
        self.ltap_impact_label = QLabel(messages.LTAP_IMPACT_LABEL_EMPTY)
        ltap_layout.addWidget(self.ltap_impact_label)
        self.ltap_year_summary_label = QLabel(messages.LTAP_YEAR_SUMMARY_EMPTY)
        ltap_layout.addWidget(self.ltap_year_summary_label)
        self.ltap_chart_hint_label = QLabel(messages.LTAP_CHART_HINT_LABEL)
        ltap_layout.addWidget(self.ltap_chart_hint_label)
        self.ltap_chart_view: QChartView | None = None
        self._ltap_chart_years: list[int] = []
        self._ltap_chart_set: QBarSet | None = None
        if HAS_QT_CHARTS:
            self.ltap_chart_view = QChartView()
            self.ltap_chart_view.setMinimumHeight(220)
            ltap_layout.addWidget(self.ltap_chart_view)
        self.ltap_year_list = QListWidget()
        self.ltap_year_list.currentRowChanged.connect(self._on_ltap_year_row_changed)
        ltap_layout.addWidget(self.ltap_year_list)
        self.ltap_show_all_button = QPushButton(messages.LTAP_SHOW_ALL_YEARS_BUTTON)
        self.ltap_show_all_button.clicked.connect(self._show_all_ltap_years)
        ltap_layout.addWidget(self.ltap_show_all_button)
        self.ltap_detail_table = QTableWidget(0, 6)
        self.ltap_detail_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ltap_detail_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.ltap_detail_table.setAlternatingRowColors(True)
        self.ltap_detail_table.verticalHeader().setDefaultSectionSize(24)
        self.ltap_detail_table.itemSelectionChanged.connect(self._on_ltap_selection_changed)
        self.ltap_detail_table.setHorizontalHeaderLabels(
            [
                messages.LTAP_DETAIL_HEADER_PM_ID,
                messages.LTAP_DETAIL_HEADER_FM_ID,
                messages.LTAP_DETAIL_HEADER_TASK,
                messages.LTAP_DETAIL_HEADER_EXECUTIONS,
                messages.LTAP_DETAIL_HEADER_COST_EUR,
                messages.LTAP_DETAIL_HEADER_DOWNTIME_HR,
            ]
        )
        self.ltap_detail_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        if self.ltap_detail_table.horizontalHeaderItem(0) is not None:
            self.ltap_detail_table.horizontalHeaderItem(0).setToolTip(
                "PM-id met labels: [TYPE] [TG/GEEN-TG] [WET/NIET-WET]"
            )
        ltap_layout.addWidget(self.ltap_detail_table)
        self.ltap_group.setVisible(False)
        self.details_toggle = QToolButton()
        self.details_toggle.setText("Toon details")
        self.details_toggle.setCheckable(True)
        self.details_toggle.setChecked(False)
        self.details_toggle.setEnabled(False)
        self.details_toggle.toggled.connect(self._on_toggle_details)
        self.details_text = QPlainTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setVisible(False)

        self._init_panel_registry()
        self._build_layout()
        self._apply_balanced_profile()
        self._restore_layout_preferences()
        self._set_default_fixture_path()
        self._refresh_ltap_context_label()

    def _build_layout(self) -> None:
        root = QWidget()
        outer = QVBoxLayout(root)
        row = QHBoxLayout()
        row.addWidget(self.path_input)
        row.addWidget(self.pick_button)
        row.addWidget(self.validate_button)
        row.addWidget(self.run_button)
        row.addWidget(self.compare_button)
        row.addWidget(self.save_button)
        row.addWidget(self.save_as_button)
        row.addWidget(self.result_focus_fm_button)
        row.addWidget(self.result_focus_pbs_button)
        row.addWidget(self.toggle_preview_button)
        row.addWidget(self.toggle_faalwijzen_button)
        row.addWidget(self.toggle_compare_button)
        row.addWidget(self.reset_layout_button)

        self.core_splitter = QSplitter(Qt.Vertical)
        self.core_splitter.addWidget(self.result_stack_group)
        self.core_splitter.addWidget(self.ltap_group)
        self.core_splitter.setChildrenCollapsible(False)

        outer.addLayout(row)
        outer.addWidget(self.idle_banner)
        outer.addWidget(self.preview_group)
        outer.addWidget(self._faalwijzen_panel)
        outer.addWidget(self.compare_group)
        outer.addWidget(self.core_splitter)
        outer.addWidget(self.details_toggle)
        outer.addWidget(self.details_text)
        self.setCentralWidget(root)
        self.resize(760, 520)
        self.statusBar()
        self._init_shortcuts()

    def _init_panel_registry(self) -> None:
        self._panel_widgets = {
            "preview": self.preview_group,
            "faalwijzen": self._faalwijzen_panel,
            "compare": self.compare_group,
            "result_stack": self.result_stack_group,
            "ltap": self.ltap_group,
        }
        self._panel_visibility = {
            "preview": True,
            "faalwijzen": False,
            "compare": False,
            "result_stack": False,
            "ltap": True,
        }

    def _apply_balanced_profile(self) -> None:
        for panel_id, visible in self._panel_visibility.items():
            self._set_panel_visible(panel_id, visible)
        self._set_active_result_panel("fm", manual=False)
        self.core_splitter.setSizes([320, 260])

    def _set_panel_visible(self, panel_id: str, visible: bool, *, from_toggle: bool = False) -> None:
        widget = self._panel_widgets.get(panel_id)
        if widget is None:
            return
        self._panel_visibility[panel_id] = visible
        widget.setVisible(visible)
        if from_toggle:
            return
        mapping = {
            "preview": self.toggle_preview_button,
            "faalwijzen": self.toggle_faalwijzen_button,
            "compare": self.toggle_compare_button,
        }
        toggle = mapping.get(panel_id)
        if toggle is not None and toggle.isChecked() != visible:
            toggle.blockSignals(True)
            toggle.setChecked(visible)
            toggle.blockSignals(False)

    def _set_active_result_panel(self, panel: str, *, manual: bool) -> None:
        if panel not in {"fm", "pbs"}:
            return
        if manual:
            self._manual_result_override = True
        self._active_result_panel = panel
        self.result_focus_fm_button.setChecked(panel == "fm")
        self.result_focus_pbs_button.setChecked(panel == "pbs")
        has_fm = self.result_table_proxy.sourceModel() is not None
        has_pbs = self.pbs_tree.model() is not None
        self.result_table_group.setVisible(panel == "fm" and has_fm)
        self.pbs_table_group.setVisible(panel == "pbs" and has_pbs)
        self._set_panel_visible("result_stack", has_fm or has_pbs)

    def _choose_active_result_panel(self) -> str:
        has_fm = self.result_table_proxy.sourceModel() is not None
        has_pbs = self.pbs_tree.model() is not None
        if self._manual_result_override and self._active_result_panel == "fm" and has_fm:
            return "fm"
        if self._manual_result_override and self._active_result_panel == "pbs" and has_pbs:
            return "pbs"
        self._manual_result_override = False
        if has_fm:
            return "fm"
        if has_pbs:
            return "pbs"
        return "fm"

    def _reset_layout_defaults(self) -> None:
        self._manual_result_override = False
        self._panel_visibility.update({"preview": True, "faalwijzen": False, "compare": False, "ltap": True})
        self._apply_balanced_profile()

    def _restore_layout_preferences(self) -> None:
        settings = QSettings("rcm2", "desktop")
        preview = settings.value("layout/panel_preview", True, type=bool)
        faal = settings.value("layout/panel_faalwijzen", False, type=bool)
        compare = settings.value("layout/panel_compare", False, type=bool)
        self._set_panel_visible("preview", preview)
        self._set_panel_visible("faalwijzen", faal)
        self._set_panel_visible("compare", compare)
        self._active_result_panel = settings.value("layout/active_result_panel", "fm", type=str)
        self._manual_result_override = settings.value("layout/manual_override", False, type=bool)
        sizes = settings.value("layout/core_splitter_sizes", None)
        if isinstance(sizes, list) and sizes:
            try:
                self.core_splitter.setSizes([int(x) for x in sizes])
            except Exception:
                pass

    def _save_layout_preferences(self) -> None:
        settings = QSettings("rcm2", "desktop")
        settings.setValue("layout/panel_preview", self._panel_visibility.get("preview", True))
        settings.setValue("layout/panel_faalwijzen", self._panel_visibility.get("faalwijzen", False))
        settings.setValue("layout/panel_compare", self._panel_visibility.get("compare", False))
        settings.setValue("layout/active_result_panel", self._active_result_panel)
        settings.setValue("layout/manual_override", self._manual_result_override)
        settings.setValue("layout/core_splitter_sizes", self.core_splitter.sizes())

    def _refresh_overview_strip_visibility(self) -> None:
        show_strip = (
            self._run_runner.busy
            or self._state.last_run is not None
            or self._state.last_result is not None
            or isinstance(self._state.last_preview, ProjectPreview)
        )
        self._set_panel_visible("preview", show_strip)
        self.idle_banner.setVisible(not show_strip)

    def _sync_preview_side_columns_visible(self) -> None:
        has_preview = isinstance(self._state.last_preview, ProjectPreview)
        self.strip_left_column.setVisible(has_preview)
        self.strip_right_column.setVisible(has_preview)

    def _sync_strip_validate_vs_run_face(self) -> None:
        run_on = self._run_runner.busy or self._state.last_run is not None
        self.strip_validate_face.setVisible(not run_on)
        self.strip_run_face.setVisible(run_on)

    def _on_state_project_changed(self, _project: object) -> None:
        self._sync_faalwijzen_panel()
        self._update_run_button_enabled()
        self._sync_ltap_panel()

    def _tear_down_faalwijzen_panel(self) -> None:
        self._faalwijzen_edit.bind_changed(None)
        if self._faalwijzen_panel is not None:
            self._faalwijzen_panel.detach()
        self._set_panel_visible("faalwijzen", False)
        self._faalwijzen_edit.clear()
        set_active_grid_service(None)
        set_grid_save_handler(None)
        self._clear_ltap_view()

    def _sync_faalwijzen_panel(self) -> None:
        validation_ok = (
            self._state.last_result is not None
            and self._state.last_result.status in {"valid", "valid_with_warnings"}
        )
        project = self._state.last_project
        if validation_ok and project is not None:
            self._faalwijzen_edit.reset(project)
            self._faalwijzen_edit.bind_changed(self._on_faalwijzen_edit_changed)
            if self._faalwijzen_panel is not None:
                self._faalwijzen_panel.attach(self._faalwijzen_edit, project)
            set_active_grid_service(self._faalwijzen_edit)
            set_grid_save_handler(self._save_current)
            self._set_panel_visible("faalwijzen", True)
            self._sync_dirty_ui()
        else:
            self._tear_down_faalwijzen_panel()
            self._sync_dirty_ui()

    def _on_faalwijzen_edit_changed(self) -> None:
        if self._faalwijzen_panel is not None:
            self._faalwijzen_panel.refresh_view()
        self._update_run_button_enabled()
        self._sync_dirty_ui()

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
            if not self._confirm_unsaved_before_destructive_action():
                return
            self.path_input.setText(filename)

    def _start_validate(self) -> None:
        if not self._confirm_unsaved_before_destructive_action():
            return
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
        self.strip_validate_summary_label.clear()
        self.strip_validate_status_label.clear()
        self.details_text.clear()
        self.details_toggle.setChecked(False)
        self.details_text.setVisible(False)
        self._state.set_last_preview(None)
        self._refresh_overview_strip_visibility()
        self._sync_preview_side_columns_visible()
        self._sync_strip_validate_vs_run_face()

    def _clear_run_output_only(self) -> None:
        self._clear_result_table()
        self._clear_pbs_table()
        self._clear_compare_view()
        self.run_status_value.clear()
        self.run_summary_value.clear()
        self.run_fm_result_count_value.setText("0")
        self.run_total_faalmomenten_value.setText("0.0")
        self.run_total_cost_value.setText("0.0")
        self._state.set_last_run(None)
        self._refresh_overview_strip_visibility()
        self._sync_strip_validate_vs_run_face()
        self._update_run_button_enabled()
        self._ltap_baseline_run = None

    def _clear_run_view(self) -> None:
        self._clear_run_output_only()
        self._tear_down_faalwijzen_panel()

    def _clear_result_table(self) -> None:
        self.result_table_group.setVisible(False)
        self.result_table_proxy.setSourceModel(None)
        self._set_active_result_panel(self._choose_active_result_panel(), manual=False)

    def _clear_pbs_table(self) -> None:
        self.pbs_table_group.setVisible(False)
        self.pbs_tree.setModel(None)
        self._set_active_result_panel(self._choose_active_result_panel(), manual=False)

    def _on_runner_state_changed(self, state: str) -> None:
        if state == "busy":
            busy_text = messages.status_label("busy")
            self.status_label.setText(busy_text)
            self.strip_validate_status_label.setText(busy_text)
            self._apply_semantic_status_style(self.status_label, "busy")
            self._apply_semantic_status_style(self.strip_validate_status_label, "busy")
            self._refresh_overview_strip_visibility()
            self._sync_strip_validate_vs_run_face()
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
            self._active_project_path = None
            self._loaded_path_mtime_ns = None
        else:
            self._state.set_last_project(project)
            active_path = Path(self.path_input.text().strip())
            self._active_project_path = active_path
            self._loaded_path_mtime_ns = current_mtime_ns(active_path)
        self._sync_dirty_ui()
        self._sync_ltap_panel()

    def _start_run(self) -> None:
        path = self.path_input.text().strip()
        project = self._state.last_project
        if self._faalwijzen_edit.is_active():
            try:
                project = self._faalwijzen_edit.materialize_for_run()
            except FaalwijzenMaterializeBlockedError as exc:
                self._show_run_error(
                    UserFacingError(code="EDIT_VALIDATION_BLOCKED", message=str(exc)),
                )
                return
        self._clear_run_output_only()
        started = self._run_runner.start(project, path, force_recompute=False)
        if started:
            self.run_button.setEnabled(False)
        self._sync_dirty_ui()

    def _on_run_state_changed(self, state: str) -> None:
        if state == "busy":
            self.run_status_value.setText(messages.status_label("busy"))
            self._apply_semantic_status_style(self.run_status_value, "busy")
        self._refresh_overview_strip_visibility()
        self._sync_strip_validate_vs_run_face()
        self._update_run_button_enabled()
        self._sync_dirty_ui()

    def _on_compare_state_changed(self, _state: str) -> None:
        self._update_run_button_enabled()
        self._sync_dirty_ui()

    def _on_run_result_ready(self, result: object) -> None:
        if isinstance(result, RunResult):
            self._state.set_last_run(result)
            if self._ltap_baseline_run is None:
                self._ltap_baseline_run = result

    def _on_compare_result_ready(self, result: object) -> None:
        if isinstance(result, ScenarioCompareView):
            self._render_compare_result(result)

    def _render_result(self, result: object) -> None:
        if not isinstance(result, ValidateResult):
            return
        status_text = messages.status_label(result.status)
        self.status_label.setText(status_text)
        self.summary_label.setText(result.summary)
        self.strip_validate_status_label.setText(status_text)
        self._apply_semantic_status_style(self.status_label, result.status)
        self._apply_semantic_status_style(self.strip_validate_status_label, result.status)
        self.strip_validate_summary_label.setText(result.summary)
        self.details_text.setPlainText(self._format_details(result.details))
        self.details_toggle.setEnabled(bool(result.details))
        if result.error is not None:
            self._show_error(result.error.message)
        self._refresh_overview_strip_visibility()
        self._sync_preview_side_columns_visible()
        self._sync_strip_validate_vs_run_face()
        self._update_run_button_enabled()

    def _render_preview(self, preview: object) -> None:
        if not isinstance(preview, ProjectPreview):
            self.preview_top5_list.clear()
            self.preview_pbs_value.setText("0")
            self.preview_functies_value.setText("0")
            self.preview_faalwijzes_value.setText("0")
            self.preview_pm_tasks_value.setText("0")
            self._sync_preview_side_columns_visible()
            self._refresh_overview_strip_visibility()
            return

        self.preview_pbs_value.setText(str(preview.pbs_items))
        self.preview_functies_value.setText(str(preview.functies))
        self.preview_faalwijzes_value.setText(str(preview.faalwijzes))
        self.preview_pm_tasks_value.setText(str(preview.pm_tasks))
        self.preview_top5_list.clear()
        if not preview.top_faalwijzes:
            self.preview_top5_list.addItem(messages.PREVIEW_EMPTY_TOP5)
            self._sync_preview_side_columns_visible()
            self._refresh_overview_strip_visibility()
            return
        for item in preview.top_faalwijzes:
            self.preview_top5_list.addItem(f"{item.fm_id} — {item.faalwijze_omschrijving}")
        self._sync_preview_side_columns_visible()
        self._refresh_overview_strip_visibility()

    def _render_run_result(self, run_result: object) -> None:
        if not isinstance(run_result, RunResult):
            self._clear_result_table()
            self._clear_pbs_table()
            self._refresh_overview_strip_visibility()
            self._sync_strip_validate_vs_run_face()
            return
        self.run_status_value.setText(messages.status_label(run_result.status))
        self._apply_semantic_status_style(self.run_status_value, run_result.status)
        self.run_summary_value.setText(run_result.summary)
        self.run_fm_result_count_value.setText(format_int(run_result.metrics.fm_result_count))
        self.run_total_faalmomenten_value.setText(format_float(run_result.metrics.total_lifecycle_faalmomenten))
        self.run_total_cost_value.setText(format_eur(run_result.metrics.total_cost_eur))
        if run_result.status == "done" and run_result.rows:
            model = FMResultsTableModel(run_result.rows, self.result_table)
            self.result_table_proxy.setSourceModel(model)
            self.result_table.sortByColumn(6, Qt.DescendingOrder)
        else:
            self._clear_result_table()
        if run_result.status == "done" and run_result.pbs_rows:
            tree_roots = build_pbs_tree(run_result.pbs_rows)
            tree_model = PBSResultsTreeModel(tree_roots, self.pbs_tree)
            self.pbs_tree.setModel(tree_model)
            root_index = QModelIndex()
            for i in range(tree_model.rowCount(root_index)):
                self.pbs_tree.expand(tree_model.index(i, 0, root_index))
        else:
            self._clear_pbs_table()
        self._set_active_result_panel(self._choose_active_result_panel(), manual=False)
        if run_result.error is not None:
            self._show_run_error(run_result.error)
        self._refresh_overview_strip_visibility()
        self._sync_preview_side_columns_visible()
        self._sync_strip_validate_vs_run_face()
        self._update_run_button_enabled()

    def _update_run_button_enabled(self) -> None:
        validation_ok = (
            self._state.last_result is not None
            and self._state.last_result.status in {"valid", "valid_with_warnings"}
        )
        edit_blocks = self._faalwijzen_edit.is_active() and self._faalwijzen_edit.has_errors()
        can_run = (
            validation_ok
            and self._state.last_project is not None
            and not self._run_runner.busy
            and not self._compare_runner.busy
            and not edit_blocks
        )
        self.run_button.setEnabled(can_run)
        self.compare_button.setEnabled(can_run)
        self._sync_save_buttons()
        self._sync_ltap_buttons()

    def _on_path_changed(self, _text: str) -> None:
        if self._suppress_path_change:
            return
        if self._faalwijzen_edit.is_active() and self._faalwijzen_edit.is_dirty():
            if not self._confirm_unsaved_before_destructive_action():
                if self._active_project_path is not None:
                    self._suppress_path_change = True
                    self.path_input.setText(str(self._active_project_path))
                    self._suppress_path_change = False
                return
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
        err_status = messages.status_label("error")
        self.status_label.setText(err_status)
        self.strip_validate_status_label.setText(err_status)
        self._apply_semantic_status_style(self.status_label, "error")
        self._apply_semantic_status_style(self.strip_validate_status_label, "error")
        QMessageBox.critical(self, messages.ERROR_DIALOG_TITLE, message)

    def _show_run_error(self, error: UserFacingError) -> None:
        self.run_status_value.setText(messages.status_label("error"))
        self._apply_semantic_status_style(self.run_status_value, "error")
        QMessageBox.critical(self, messages.RUN_ERROR_DIALOG_TITLE, error.message)

    def _start_compare(self) -> None:
        if not self._confirm_unsaved_before_destructive_action():
            return
        path = self.path_input.text().strip()
        project = self._state.last_project
        if self._faalwijzen_edit.is_active():
            try:
                project = self._faalwijzen_edit.materialize_for_run()
            except FaalwijzenMaterializeBlockedError as exc:
                self._show_run_error(UserFacingError(code="EDIT_VALIDATION_BLOCKED", message=str(exc)))
                return
        self._clear_compare_view()
        started = self._compare_runner.start(project, path)
        if started:
            self.compare_button.setEnabled(False)

    def _clear_compare_view(self) -> None:
        self._set_panel_visible("compare", False)
        self.compare_summary_label.clear()
        self.compare_kpi_list.clear()

    def _sync_ltap_buttons(self) -> None:
        enabled = self.ltap_group.isVisible() and not self._run_runner.busy and not self._compare_runner.busy
        self.ltap_apply_button.setEnabled(enabled and bool(self._selected_ltap_pm_ids()))
        self.ltap_reset_button.setEnabled(enabled and bool(self._ltap_overlay_anchor_years))
        self.ltap_show_all_button.setEnabled(enabled)

    def _sync_ltap_panel(self) -> None:
        project = self._state.last_project
        validation_ok = (
            self._state.last_result is not None
            and self._state.last_result.status in {"valid", "valid_with_warnings"}
        )
        if not validation_ok or project is None:
            self._clear_ltap_view()
            return
        self._ltap_overlay_anchor_years = reset_overlay()
        self._ltap_filter_mode = "all"
        self._sync_ltap_filter_button_text()
        self._ltap_baseline_view = self._build_ltap_view(project, overlay_anchor_years=self._ltap_overlay_anchor_years)
        self._ltap_current_view = self._ltap_baseline_view
        self._render_ltap_view(self._ltap_baseline_view)
        self._ltap_baseline_run = None
        self._set_panel_visible("ltap", True)
        self.ltap_impact_label.setText(messages.LTAP_IMPACT_LABEL_EMPTY)
        self._sync_ltap_buttons()
        self._refresh_ltap_context_label()

    def _clear_ltap_view(self) -> None:
        self._set_panel_visible("ltap", False)
        self.ltap_year_list.clear()
        self.ltap_detail_table.setRowCount(0)
        self._ltap_year_rows = {}
        self._ltap_selected_year = None
        self.ltap_impact_label.setText(messages.LTAP_IMPACT_LABEL_EMPTY)
        self.ltap_year_summary_label.setText(messages.LTAP_YEAR_SUMMARY_EMPTY)
        self._ltap_overlay_anchor_years = {}
        self._ltap_baseline_view = None
        self._ltap_current_view = None
        self._ltap_baseline_run = None
        self._ltap_filter_mode = "all"
        self._sync_ltap_filter_button_text()
        self._ltap_clear_chart()
        self._sync_ltap_buttons()
        self._refresh_ltap_context_label()

    def _render_ltap_view(self, view: LTAPView) -> None:
        self._ltap_year_rows = {year_row.year: year_row for year_row in view.years}
        selected_year = self._ltap_selected_year
        self.ltap_year_list.blockSignals(True)
        self.ltap_year_list.clear()
        for year_row in view.years:
            self.ltap_year_list.addItem(
                f"Jaar {year_row.year}: taken={year_row.task_count} | PM={format_eur(year_row.pm_cost_eur)} | downtime={format_float(year_row.planned_downtime_hr)} h"
            )
        self.ltap_year_list.blockSignals(False)
        self._ltap_render_chart(baseline=self._ltap_baseline_view or view, current=view)
        if selected_year is not None and selected_year in self._ltap_year_rows:
            self._select_ltap_year(selected_year)
            return
        self._show_all_ltap_years()

    def _ltap_clear_chart(self) -> None:
        self._ltap_chart_years = []
        self._ltap_chart_set = None
        if self.ltap_chart_view is not None:
            self.ltap_chart_view.setChart(QChart())

    def _ltap_render_chart(self, *, baseline: LTAPView, current: LTAPView) -> None:
        if self.ltap_chart_view is None:
            return
        chart = QChart()
        chart.setTitle(messages.LTAP_CHART_TITLE)
        years = [row.year for row in current.years]
        self._ltap_chart_years = years
        baseline_set = QBarSet(messages.LTAP_CHART_SERIES_BASELINE)
        current_set = QBarSet(messages.LTAP_CHART_SERIES_WHAT_IF)
        baseline_set.setColor(QColor("#9AA0A6"))
        current_set.setColor(QColor("#1E88E5"))
        baseline_by_year = {row.year: row.pm_cost_eur for row in baseline.years}
        for row in current.years:
            baseline_set.append(float(baseline_by_year.get(row.year, 0.0)))
            current_set.append(float(row.pm_cost_eur))
        baseline_set.clicked.connect(self._on_ltap_bar_clicked)
        current_set.clicked.connect(self._on_ltap_bar_clicked)
        self._ltap_chart_set = current_set
        series = QBarSeries()
        series.append(baseline_set)
        series.append(current_set)
        chart.addSeries(series)
        axis_x = QBarCategoryAxis()
        axis_x.append([str(year) for year in years])
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        axis_y = QValueAxis()
        axis_y.setTitleText(messages.LTAP_CHART_AXIS_Y_TITLE)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        self.ltap_chart_view.setChart(chart)
        self._refresh_ltap_context_label()

    def _on_ltap_bar_clicked(self, index: int) -> None:
        if index < 0 or index >= len(self._ltap_chart_years):
            return
        year = self._ltap_chart_years[index]
        self._select_ltap_year(year)

    def _on_ltap_year_row_changed(self, row_index: int) -> None:
        if row_index < 0:
            self._show_all_ltap_years()
            return
        if row_index >= len(self._ltap_year_rows):
            return
        year = sorted(self._ltap_year_rows.keys())[row_index]
        self._select_ltap_year(year)

    def _select_ltap_year(self, year: int) -> None:
        year_row = self._ltap_year_rows.get(year)
        if year_row is None:
            self.ltap_detail_table.setRowCount(0)
            return
        self._ltap_selected_year = year
        sorted_years = sorted(self._ltap_year_rows.keys())
        if year in sorted_years:
            self.ltap_year_list.blockSignals(True)
            self.ltap_year_list.setCurrentRow(sorted_years.index(year))
            self.ltap_year_list.blockSignals(False)
        self._ltap_populate_details(tuple(year_row.details))
        baseline_cost = self._ltap_year_cost(self._ltap_baseline_view, year)
        current_cost = self._ltap_year_cost(self._ltap_current_view, year)
        self.ltap_year_summary_label.setText(
            messages.LTAP_YEAR_SUMMARY_LABEL.format(
                year=year,
                baseline=format_eur(baseline_cost),
                what_if=format_eur(current_cost),
                delta=format_eur(current_cost - baseline_cost),
            )
        )
        self._refresh_ltap_context_label()

    def _show_all_ltap_years(self) -> None:
        self._ltap_selected_year = None
        self.ltap_year_list.blockSignals(True)
        self.ltap_year_list.clearSelection()
        self.ltap_year_list.setCurrentRow(-1)
        self.ltap_year_list.blockSignals(False)
        all_details: list = []
        for year in sorted(self._ltap_year_rows.keys()):
            all_details.extend(self._ltap_year_rows[year].details)
        self._ltap_populate_details(tuple(all_details))
        self.ltap_year_summary_label.setText(messages.LTAP_YEAR_SUMMARY_EMPTY)
        self._refresh_ltap_context_label()

    def _ltap_populate_details(self, details: tuple[LTAPTaskDetail, ...]) -> None:
        if not details:
            self.ltap_detail_table.setRowCount(1)
            self.ltap_detail_table.setItem(0, 0, QTableWidgetItem(messages.LTAP_DETAIL_EMPTY_TEXT))
            for col in range(1, self.ltap_detail_table.columnCount()):
                self.ltap_detail_table.setItem(0, col, QTableWidgetItem(""))
            self._sync_ltap_selection_text()
            return
        self.ltap_detail_table.setRowCount(len(details))
        for idx, detail in enumerate(details):
            task_label = detail.taak_omschrijving
            if not detail.shiftable:
                task_label = f"{task_label} ({messages.LTAP_DETAIL_NON_SHIFTABLE_TAG})"
            pm_label_item = QTableWidgetItem(detail.pm_label)
            pm_label_item.setData(Qt.UserRole, detail.pm_id)
            self.ltap_detail_table.setItem(idx, 0, pm_label_item)
            self.ltap_detail_table.setItem(idx, 1, QTableWidgetItem(detail.fm_id))
            self.ltap_detail_table.setItem(idx, 2, QTableWidgetItem(task_label))
            executions_item = QTableWidgetItem(str(detail.executions))
            executions_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.ltap_detail_table.setItem(idx, 3, executions_item)
            cost_item = QTableWidgetItem(format_eur(detail.pm_cost_eur))
            cost_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.ltap_detail_table.setItem(idx, 4, cost_item)
            downtime_item = QTableWidgetItem(format_float(detail.planned_downtime_hr))
            downtime_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.ltap_detail_table.setItem(idx, 5, downtime_item)
        self._sync_ltap_selection_text()

    def _ltap_year_cost(self, view: LTAPView | None, year: int) -> float:
        if view is None:
            return 0.0
        for row in view.years:
            if row.year == year:
                return row.pm_cost_eur
        return 0.0

    def _apply_ltap_bundle(self) -> None:
        project = self._state.last_project
        if project is None:
            return
        pm_ids = self._selected_ltap_pm_ids()
        if not pm_ids:
            self.ltap_impact_label.setText(messages.LTAP_IMPACT_LABEL_EMPTY)
            QMessageBox.critical(self, messages.LTAP_ERROR_DIALOG_TITLE, messages.LTAP_SELECTION_REQUIRED_ERROR)
            return
        shift_years = int(self.ltap_shift_spin.value())
        result = apply_bundle_shift(
            project,
            current_overlay_anchor_years=self._ltap_overlay_anchor_years,
            pm_ids=pm_ids,
            shift_years=shift_years,
        )
        if not result.ok:
            self.ltap_impact_label.setText(messages.LTAP_IMPACT_LABEL_EMPTY)
            QMessageBox.critical(self, messages.LTAP_ERROR_DIALOG_TITLE, result.error or "Onbekende LTAP-fout.")
            return
        self._ltap_overlay_anchor_years = result.overlay_anchor_years
        self._ltap_current_view = self._build_ltap_view(project, overlay_anchor_years=self._ltap_overlay_anchor_years)
        self._render_ltap_view(self._ltap_current_view)
        self._recompute_ltap_impact()
        self._sync_ltap_buttons()
        self._refresh_ltap_context_label()

    def _reset_ltap_bundle(self) -> None:
        project = self._state.last_project
        if project is None:
            return
        self._ltap_overlay_anchor_years = reset_overlay()
        self._ltap_selected_year = None
        self._ltap_current_view = self._build_ltap_view(project, overlay_anchor_years=self._ltap_overlay_anchor_years)
        self._render_ltap_view(self._ltap_current_view)
        self.ltap_impact_label.setText(messages.LTAP_IMPACT_LABEL_EMPTY)
        self._sync_ltap_buttons()
        self._refresh_ltap_context_label()

    def _selected_ltap_pm_ids(self) -> list[str]:
        selection_model = self.ltap_detail_table.selectionModel()
        if selection_model is None:
            return []
        ids: list[str] = []
        seen: set[str] = set()
        for index in selection_model.selectedRows(0):
            item = self.ltap_detail_table.item(index.row(), 0)
            if item is None:
                continue
            if item.text() == messages.LTAP_DETAIL_EMPTY_TEXT:
                continue
            pm_id = item.data(Qt.UserRole) or item.text().split(" ")[0]
            if pm_id in seen:
                continue
            seen.add(pm_id)
            ids.append(str(pm_id))
        return ids

    def _on_ltap_selection_changed(self) -> None:
        self._sync_ltap_selection_text()
        self._sync_ltap_buttons()
        self._refresh_ltap_context_label()

    def _sync_ltap_selection_text(self) -> None:
        self.ltap_select_input.setText(", ".join(self._selected_ltap_pm_ids()))

    def _toggle_ltap_filter_mode(self) -> None:
        project = self._state.last_project
        if project is None:
            return
        self._ltap_filter_mode = "rev-only" if self._ltap_filter_mode == "all" else "all"
        self._sync_ltap_filter_button_text()
        self._ltap_baseline_view = self._build_ltap_view(project, overlay_anchor_years={})
        self._ltap_current_view = self._build_ltap_view(project, overlay_anchor_years=self._ltap_overlay_anchor_years)
        self._render_ltap_view(self._ltap_current_view)
        self._recompute_ltap_impact()
        self._sync_ltap_buttons()
        self._refresh_ltap_context_label()

    def _sync_ltap_filter_button_text(self) -> None:
        if self._ltap_filter_mode == "rev-only":
            self.ltap_filter_button.setText(messages.LTAP_FILTER_SHOW_ALL_BUTTON)
            return
        self.ltap_filter_button.setText(messages.LTAP_FILTER_REV_ONLY_BUTTON)

    def _build_ltap_view(self, project, *, overlay_anchor_years: dict[str, float]) -> LTAPView:
        taak_type_filter = "REV" if self._ltap_filter_mode == "rev-only" else None
        return build_ltap_view(project, overlay_anchor_years=overlay_anchor_years, taak_type_filter=taak_type_filter)

    def _recompute_ltap_impact(self) -> None:
        project = self._state.last_project
        baseline = self._ltap_baseline_view
        current = self._ltap_current_view
        if project is None or baseline is None or current is None:
            return
        delta_cost = current.total_pm_cost_eur - baseline.total_pm_cost_eur
        delta_downtime = current.total_planned_downtime_hr - baseline.total_planned_downtime_hr
        if self._ltap_baseline_run is None:
            self._ltap_baseline_run = self._state.last_run
        rerun = self._state.last_run
        kpi_delta = 0.0
        if self._ltap_baseline_run is not None and rerun is not None:
            kpi_delta = rerun.metrics.total_cost_eur - self._ltap_baseline_run.metrics.total_cost_eur
        self.ltap_impact_label.setText(
            f"Δ PM-kosten {format_eur(delta_cost)} | Δ downtime {format_float(delta_downtime)} h | Δ scenario-KPI {format_eur(kpi_delta)}"
        )
        self._refresh_ltap_context_label()

    def _render_compare_result(self, view: ScenarioCompareView) -> None:
        if view.status != "done":
            self._clear_compare_view()
            QMessageBox.critical(self, messages.COMPARE_ERROR_DIALOG_TITLE, view.summary)
            return
        self.compare_summary_label.setText(view.summary)
        self.compare_kpi_list.clear()
        for kpi in view.kpis:
            self.compare_kpi_list.addItem(
                f"{kpi.label}: CM {kpi.cm_display} | PM {kpi.pm_display} | Δ {kpi.delta_display}"
            )
            if kpi.cm_drivers:
                self.compare_kpi_list.addItem(f"  CM top-3: {', '.join(kpi.cm_drivers)}")
            if kpi.pm_drivers:
                self.compare_kpi_list.addItem(f"  PM top-3: {', '.join(kpi.pm_drivers)}")
        self._set_panel_visible("compare", True)

    def _init_shortcuts(self) -> None:
        save_action = QAction(self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self._save_current)
        self.addAction(save_action)

        save_as_action = QAction(self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self._save_as)
        self.addAction(save_as_action)

        ltap_apply_action = QAction(self)
        ltap_apply_action.setShortcut(QKeySequence("Ctrl+Return"))
        ltap_apply_action.triggered.connect(self._apply_ltap_bundle)
        self.addAction(ltap_apply_action)

        ltap_reset_action = QAction(self)
        ltap_reset_action.setShortcut(QKeySequence("Ctrl+Backspace"))
        ltap_reset_action.triggered.connect(self._reset_ltap_bundle)
        self.addAction(ltap_reset_action)

    def _refresh_ltap_context_label(self) -> None:
        filter_mode = (
            messages.LTAP_CONTEXT_FILTER_REV if self._ltap_filter_mode == "rev-only" else messages.LTAP_CONTEXT_FILTER_ALL
        )
        year_mode = (
            messages.LTAP_CONTEXT_YEAR_SELECTED.format(year=self._ltap_selected_year)
            if self._ltap_selected_year is not None
            else messages.LTAP_CONTEXT_YEAR_ALL
        )
        selected_count = len(self._selected_ltap_pm_ids())
        selection_mode = (
            messages.LTAP_CONTEXT_SELECTION_COUNT.format(count=selected_count)
            if selected_count > 0
            else messages.LTAP_CONTEXT_SELECTION_EMPTY
        )
        overlay_count = len(self._ltap_overlay_anchor_years)
        overlay_mode = (
            messages.LTAP_CONTEXT_OVERLAY_ACTIVE.format(count=overlay_count)
            if overlay_count > 0
            else messages.LTAP_CONTEXT_OVERLAY_INACTIVE
        )
        self.ltap_context_label.setText(
            messages.LTAP_CONTEXT_LABEL.format(
                filter_mode=filter_mode,
                year_mode=year_mode,
                selection_mode=selection_mode,
                overlay_mode=overlay_mode,
            )
        )

    def _apply_semantic_status_style(self, label: QLabel, status: str) -> None:
        colors = {
            "valid": "#2E7D32",
            "valid_with_warnings": "#ED6C02",
            "invalid": "#D32F2F",
            "error": "#D32F2F",
            "busy": "#1565C0",
            "idle": "#616161",
            "done": "#2E7D32",
        }
        label.setStyleSheet(f"color: {colors.get(status, '#424242')}; font-weight: 600;")

    def _sync_save_buttons(self) -> None:
        can_save = (
            self._faalwijzen_edit.is_active()
            and self._faalwijzen_edit.is_dirty()
            and not self._run_runner.busy
            and not self._compare_runner.busy
        )
        self.save_button.setEnabled(can_save)
        self.save_as_button.setEnabled(can_save)

    def _sync_dirty_ui(self) -> None:
        dirty = self._faalwijzen_edit.is_active() and self._faalwijzen_edit.is_dirty()
        title = "RCM2 desktop — validate tracer-bullet"
        self.setWindowTitle(f"{title}*" if dirty else title)
        self._sync_save_buttons()

    def _save_current(self) -> bool:
        if self._run_runner.busy:
            self.statusBar().showMessage(messages.SAVE_BLOCKED_WHILE_RUN, 3000)
            return False
        if not self._faalwijzen_edit.is_active() or not self._faalwijzen_edit.is_dirty():
            return True
        if self._active_project_path is None:
            return self._save_as()
        return self._persist_to_path(self._active_project_path, check_conflict=True)

    def _save_as(self) -> bool:
        if self._run_runner.busy:
            self.statusBar().showMessage(messages.SAVE_BLOCKED_WHILE_RUN, 3000)
            return False
        if not self._faalwijzen_edit.is_active() or not self._faalwijzen_edit.is_dirty():
            return True
        filename, _selected_filter = QFileDialog.getSaveFileName(
            self,
            "Opslaan als",
            self.path_input.text() or str(Path.cwd()),
            "RCM JSON (*.rcm.json);;JSON (*.json)",
        )
        if not filename:
            return False
        return self._persist_to_path(Path(filename), check_conflict=False)

    def _persist_to_path(self, target_path: Path, *, check_conflict: bool) -> bool:
        try:
            project = self._faalwijzen_edit.materialize_for_save()
            success = save_project_atomically(
                project,
                target_path,
                baseline_mtime_ns=self._loaded_path_mtime_ns,
                check_conflict=check_conflict,
            )
        except SaveConflictError:
            QMessageBox.critical(self, messages.SAVE_ERROR_DIALOG_TITLE, messages.SAVE_CONFLICT_MESSAGE)
            return False
        except Exception as exc:
            QMessageBox.critical(self, messages.SAVE_ERROR_DIALOG_TITLE, str(exc))
            return False

        self._active_project_path = success.path
        self._loaded_path_mtime_ns = success.mtime_ns
        self._suppress_path_change = True
        self.path_input.setText(str(success.path))
        self._suppress_path_change = False
        self._faalwijzen_edit.mark_saved()
        self.statusBar().showMessage(messages.SAVE_SUCCESS_STATUS, 3000)
        self._sync_dirty_ui()
        return True

    def _confirm_unsaved_before_destructive_action(self) -> bool:
        if not self._faalwijzen_edit.is_active() or not self._faalwijzen_edit.is_dirty():
            return True
        choice = self._show_unsaved_dialog()
        if choice == "save":
            return self._save_current()
        if choice == "discard":
            return True
        return False

    def _show_unsaved_dialog(self) -> str:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle(messages.UNSAVED_DIALOG_TITLE)
        box.setText(messages.UNSAVED_DIALOG_TEXT)
        save_btn = box.addButton("Opslaan", QMessageBox.AcceptRole)
        discard_btn = box.addButton("Verwerpen", QMessageBox.DestructiveRole)
        cancel_btn = box.addButton("Annuleren", QMessageBox.RejectRole)
        box.setDefaultButton(save_btn)
        box.exec()
        clicked = box.clickedButton()
        if clicked == save_btn:
            return "save"
        if clicked == discard_btn:
            return "discard"
        assert clicked == cancel_btn
        return "cancel"

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._confirm_unsaved_before_destructive_action():
            self._save_layout_preferences()
            event.accept()
            return
        event.ignore()
