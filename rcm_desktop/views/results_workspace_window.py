"""Nieuwe resultatenwerkruimte (slice 23 + slice 26).

Hoofdvenster met vaste PBS-sidebar links en resultatengebied rechts.
Analyse via één knop `Start analyse` / `Herbereken analyse` op het volledige
geladen project; presentatie-cache versnelt projecttotaal-modi.

Architectuur-discipline (zie AGENTS.md):
- Views consumeren Qt-vrije adapter-output; geen `rcm_core`-imports buiten
  typing-only.
- Presentatielogica (scope-filter, structuur-/totalen-boom) zit
  in `rcm_desktop.adapter.result_filter_service`,
  `rcm_desktop.adapter.result_view_service` en
  `rcm_desktop.adapter.workspace_view_service`.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    QItemSelection,
    QItemSelectionModel,
    QModelIndex,
    QSortFilterProxyModel,
    Qt,
    QUrl,
    Signal,
)
from PySide6.QtGui import QCloseEvent, QColor, QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QDialog,
    QDialogButtonBox,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTableView,
    QToolButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from rcm_desktop import messages
from rcm_desktop.adapter.kpi_table_model import KPITableModel
from rcm_desktop.adapter.presentation_cache_service import PresentationProjectTotal
from rcm_desktop.adapter.lcc_warmup_runner import LCCWarmupRunner
from rcm_desktop.adapter.presentation_lazy_service import (
    default_lcc_warmup_snapshot,
    warm_lcc_render_index,
)
from rcm_desktop.adapter.presentation_rebuild_runner import PresentationRebuildRunner
from rcm_desktop.adapter.compare_run_config import CompareRunConfig
from rcm_desktop.adapter.compare_run_runner import CompareRunRunner
from rcm_desktop.adapter.compare_run_service import CompareRunOutcome
from rcm_desktop.adapter.compare_slot_label import build_compare_slot_label
from rcm_desktop.adapter.compare_slot_state import (
    COMPARE_SLOT_A,
    COMPARE_SLOT_B,
    CompareSlotState,
)
from rcm_desktop.adapter.compare_view_service import ComparePanel
from rcm_desktop.adapter.compare_presentation_policy import (
    resolve_shared_calendar_year,
    shared_lcc_y_max,
)
from rcm_desktop.adapter.compare_workspace_controller import CompareWorkspaceController
from rcm_desktop.adapter.report_eligibility_service import assess_report_workspace
from rcm_desktop.adapter.report_generation_service import ReportGenerationOutcome
from rcm_desktop.adapter.project_path_resolution_service import resolve_project_file_path
from rcm_desktop.adapter.report_runner import ReportRunner
from rcm_desktop.adapter.run_runner import PHASE_MOTOR, PHASE_PRESENTATION, RunRunner
from rcm_desktop.adapter.contribution_table_model import ContributionTableModel
from rcm_desktop.adapter.contribution_chart_service import build_contribution_rows
from rcm_desktop.adapter.fm_results_table_model import (
    FMResultsSortProxy,
    FMResultsTableModel,
    RAW_ROLE,
)
from rcm_desktop.adapter.fm_verification_service import FMVerificationView
from rcm_desktop.adapter.fm_verification_year_table_model import (
    FMVerificationYearTableModel,
)
from rcm_desktop.formatting import format_eur, format_float, format_int
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.lcc_planning_service import build_lcc_planning_curve_reconciled
from rcm_desktop.adapter.lcc_detail_selection import rev_row_indices
from rcm_desktop.adapter.lcc_type_filter import LCCTypeFilterSet
from rcm_desktop.adapter.lcc_year_detail_table_model import (
    LCCYearDetailTableModel,
    PASSIVE_COLUMN,
)
from rcm_desktop.adapter.lcc_year_table_model import LCCYearTableModel
from rcm_desktop.adapter.import_flow_service import gate_workbook, persist_wizard_result
from rcm_desktop.adapter.isograph_open_flow_service import PersistImportSuccess
from rcm_desktop.adapter.meekoppel_display_service import (
    due_calendar_year,
    format_meekoppel_preview_moves_text,
)
from rcm_desktop.adapter.feature_flags import meekoppel_workflow_v2_enabled
from rcm_desktop.adapter.meekoppel_panel_service import (
    MeekoppelPreviewGate,
    apply_meekoppel,
    preview_meekoppel,
    sync_meekoppel_panel,
)
from rcm_desktop.adapter.meekoppel_workflow_service import MeekoppelWorkflowService
from rcm_desktop.adapter.meekoppelkansen_discovery_service import (
    MeekoppelLocationGroup,
    collect_rev_tasks_for_pbs_selection,
)
from rcm_desktop.views.meekoppel_preview_dialog import MeekoppelPreviewDialog
from rcm_desktop.views.report_generation_dialog import ReportGenerationDialog
from rcm_desktop.adapter.meekoppel_suggestions_table_model import (
    MeekoppelSuggestionsTableModel,
)
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.planning_whatif_service import apply_overlay_shift
from rcm_desktop.adapter.pbs_results_tree_model import PBSResultsTreeModel
from rcm_desktop.adapter.rcm_navigation_tree_model import RcmNavigationTreeModel
from rcm_desktop.adapter import workspace_session_service as wss
from rcm_desktop.adapter.editing_host import EditingHost
from rcm_desktop.adapter.faalwijzen_edit_service import FaalwijzenEditService
from rcm_desktop.views.fm_editor_dialog import FmEditorDialog
from rcm_desktop.views.grid_dirty_guard import resolve_grid_dirty_before_editor
from rcm_desktop.views.model_settings_dialog import ModelSettingsDialog
from rcm_desktop.views.validate_faalwijzen_panel import ValidateFaalwijzenPanel
from rcm_desktop.views.import_wizard_dialog import ImportDialogInput, run_import_wizard
from rcm_desktop.views.compare_slot_column import (
    build_bijdragen_compare_column,
    build_lcc_compare_column,
    set_compare_placeholder,
)
from rcm_desktop.views.widgets.contribution_bar_chart import ContributionBarChartWidget
from rcm_desktop.views.widgets.lcc_stacked_bar_chart import LCCStackedBarChartWidget
from rcm_desktop.adapter.preview_service import build as build_project_preview
from rcm_desktop.adapter.project_paths import resolve_default_fixture_path
from rcm_desktop.adapter.result_view_service import (
    build_pbs_tree,
)
from rcm_desktop.adapter.results_workspace_orchestrator import (
    BijdragenToolbarPlan,
    CollapsePanelPlan,
    CollapsePanelsPlan,
    CompareChromePlan,
    FmToolbarPlan,
    LccToolbarVisibilityPlan,
    MeekoppelCollapsePlan,
    RenderPlan,
    ResultsWorkspaceOrchestrator,
    WorkspaceRenderContext,
    WorkspaceUiSyncPlan,
    plan_compare_chrome,
)
from rcm_desktop.adapter.results_workspace_state import (
    ALL_METRICS,
    METRIC_FAALMOMENTEN,
    METRIC_KOSTEN,
    METRIC_NIET_BESCHIKBAARHEID,
    MODE_BIJDRAGEN,
    MODE_FM_DETAIL,
    MODE_LCC,
    SOURCE_FAALWIJZE,
    SOURCE_PBS,
    ResultsWorkspaceState,
    WorkspaceStateSnapshot,
)
from rcm_desktop.adapter.run_service import RunResult
from rcm_desktop.adapter.validate_runner import ValidateRunner
from rcm_desktop.adapter.validate_service import (
    DetailItem,
    UserFacingError,
    ValidateResult,
)
from rcm_desktop.adapter.workspace_detail_render_scope import RenderSplitDepth
from rcm_desktop.adapter.workspace_render_index import WorkspaceRenderIndex
from rcm_desktop.app_state import AppState
from rcm_desktop.table_ui_constants import PBS_FILTER_MAX_EXPAND_NODES


def _apply_workspace_data_table_header_policy(header: QHeaderView) -> None:
    """Schaalbare kolombreedtes i.p.v. ResizeToContents op grote tabellen (slice 25)."""
    header.setSectionResizeMode(QHeaderView.Interactive)
    header.setStretchLastSection(True)


class _PBSSidebarFilterProxy(QSortFilterProxyModel):
    """Recursief substring-filter op PBS-id en bouwdeelnaam."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setRecursiveFilteringEnabled(True)
        self._needle = ""

    def set_needle(self, needle: str) -> None:
        self._needle = needle.strip().lower()
        # `invalidate()` re-runs both filtering and sorting; for a tree with stable
        # rows the cost is negligible and avoids PySide6 deprecation noise on the
        # filter-only invalidator variants.
        self.invalidate()

    def has_needle(self) -> bool:
        return bool(self._needle)

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:  # noqa: N802
        if not self._needle:
            return True
        model = self.sourceModel()
        if model is None:
            return False
        idx_pbs = model.index(source_row, 0, source_parent)
        idx_bouw = model.index(source_row, 1, source_parent)
        pbs_text = (model.data(idx_pbs, Qt.DisplayRole) or "")
        bouw_text = (model.data(idx_bouw, Qt.DisplayRole) or "")
        return self._needle in str(pbs_text).lower() or self._needle in str(bouw_text).lower()


class ResultsWorkspaceWindow(QMainWindow):
    """Hoofdvenster van de nieuwe resultatenwerkruimte (slice 23 fase A)."""

    def __init__(self, *, editing_host: EditingHost | None = None) -> None:
        super().__init__()
        self.setWindowTitle(messages.WORKSPACE_WINDOW_TITLE)

        self._state = AppState()
        self._runner = ValidateRunner()
        self._run_runner = RunRunner()
        self._presentation_rebuild_runner = PresentationRebuildRunner()
        self._lcc_warmup_runner = LCCWarmupRunner()
        self._runner.state_changed.connect(self._on_validate_state_changed)
        self._runner.result_ready.connect(self._on_validate_result_ready)
        self._runner.project_ready.connect(self._on_project_ready_from_runner)
        self._run_runner.state_changed.connect(self._on_run_state_changed)
        self._run_runner.phase_changed.connect(self._on_run_phase_changed)
        self._run_runner.result_ready.connect(self._on_run_result_ready)
        self._presentation_rebuild_runner.state_changed.connect(
            self._on_presentation_rebuild_state_changed
        )
        self._presentation_rebuild_runner.result_ready.connect(
            self._on_presentation_rebuild_result_ready
        )
        self._state.project_changed.connect(self._on_state_project_changed)
        self._state.run_changed.connect(self._on_state_run_changed)
        self._state.result_changed.connect(self._render_validate_result)

        self._pbs_scope_id: str | None = None
        self._pbs_source_model: PBSResultsTreeModel | RcmNavigationTreeModel | None = None
        self._suppress_path_change = False
        self._project_total_presentation: PresentationProjectTotal | None = None
        self._render_index = WorkspaceRenderIndex()
        self._compare_slots = CompareSlotState()
        self._compare_slots.subscribe(self._on_compare_slots_changed)
        self._compare_run_runner = CompareRunRunner()
        self._compare_run_runner.state_changed.connect(self._on_compare_run_state_changed)
        self._compare_run_runner.slot_result_ready.connect(
            self._on_compare_slot_result_ready
        )
        self._report_runner = ReportRunner()
        self._report_runner.state_changed.connect(self._on_report_runner_state_changed)
        self._report_runner.finished.connect(self._on_report_generation_finished)
        self._report_runner.failed.connect(self._on_report_generation_failed)
        self._editing_host = editing_host if editing_host is not None else EditingHost()

        self.workspace_state = ResultsWorkspaceState()
        self._last_workspace_snapshot_for_split_depth: WorkspaceStateSnapshot | None = None
        self._last_lcc_render_snapshot: WorkspaceStateSnapshot | None = None
        self._lcc_passive_kept_after_run = False

        self._build_toolbar()
        self._build_pbs_sidebar()
        self._build_detail_zone()
        self._build_layout()
        self._wire_pbs_tree_interaction()
        self.workspace_state.subscribe(self._on_workspace_state_changed)
        # Sync UI elements to the current snapshot once so initial widget state
        # matches the orchestrator's defaults.
        self._on_workspace_state_changed(self.workspace_state.snapshot())

        self._set_default_fixture_path()
        self._update_run_buttons_enabled()

    def _build_toolbar(self) -> None:
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Pad naar projectbestand (*.rcm.json)")
        self.path_input.textChanged.connect(self._on_path_changed)
        self.pick_button = QPushButton(messages.PICK_BUTTON_LABEL)
        self.pick_button.clicked.connect(self._pick_file)
        self.open_isograph_button = QPushButton(messages.ISOGRAPH_OPEN_BUTTON_LABEL)
        self.open_isograph_button.clicked.connect(self._open_rcm_cost_export)
        self.validate_button = QPushButton(messages.VALIDATE_BUTTON_LABEL)
        self.validate_button.setToolTip(messages.VALIDATE_BUTTON_TOOLTIP)
        self.validate_button.clicked.connect(self._start_validate)
        self.run_analyse_button = QPushButton(messages.WORKSPACE_START_ANALYSE_BUTTON_LABEL)
        self.run_analyse_button.setToolTip(messages.WORKSPACE_START_ANALYSE_BUTTON_TOOLTIP)
        self.run_analyse_button.setEnabled(False)
        self.run_analyse_button.clicked.connect(self._start_analyse)
        self.run_analyse_button.setVisible(False)
        self.compare_scenario_combo = QComboBox()
        self.compare_scenario_combo.addItem(
            messages.WORKSPACE_COMPARE_SCENARIO_PROJECT, None
        )
        self.compare_scenario_combo.addItem(
            messages.WORKSPACE_COMPARE_SCENARIO_CM, "cm"
        )
        self.compare_scenario_combo.addItem(
            messages.WORKSPACE_COMPARE_SCENARIO_PM, "pm"
        )
        self.run_slot_a_button = QPushButton(messages.WORKSPACE_RUN_SLOT_A_BUTTON_LABEL)
        self.run_slot_a_button.setToolTip(messages.WORKSPACE_RUN_SLOT_A_BUTTON_TOOLTIP)
        self.run_slot_a_button.clicked.connect(self._start_run_slot_a)
        self.run_slot_b_button = QPushButton(messages.WORKSPACE_RUN_SLOT_B_BUTTON_LABEL)
        self.run_slot_b_button.setToolTip(messages.WORKSPACE_RUN_SLOT_B_BUTTON_TOOLTIP)
        self.run_slot_b_button.clicked.connect(self._start_run_slot_b)
        self.compare_toggle_button = QToolButton()
        self.compare_toggle_button.setText(messages.WORKSPACE_COMPARE_TOGGLE_LABEL)
        self.compare_toggle_button.setToolTip(messages.WORKSPACE_COMPARE_TOGGLE_TOOLTIP)
        self.compare_toggle_button.setCheckable(True)
        self.compare_toggle_button.toggled.connect(self._on_compare_toggle)
        self.clear_compare_button = QPushButton(messages.WORKSPACE_CLEAR_COMPARE_BUTTON_LABEL)
        self.clear_compare_button.clicked.connect(self._clear_compare_slots)
        self.batch_faalwijzen_button = QPushButton(messages.WORKSPACE_MENU_FAALWIJZEN_BATCH)
        self.batch_faalwijzen_button.setToolTip(messages.WORKSPACE_MENU_FAALWIJZEN_BATCH)
        self.batch_faalwijzen_button.clicked.connect(self._open_batch_faalwijzen_grid)
        self.model_settings_button = QPushButton(messages.MODEL_SETTINGS_BUTTON_LABEL)
        self.model_settings_button.setToolTip(messages.MODEL_SETTINGS_BUTTON_LABEL)
        self.model_settings_button.clicked.connect(self._open_model_settings)
        self.generate_report_button = QPushButton(messages.REPORT_GENERATE_BUTTON_LABEL)
        self.generate_report_button.setToolTip(messages.REPORT_GENERATE_BUTTON_TOOLTIP)
        self.generate_report_button.setEnabled(False)
        self.generate_report_button.clicked.connect(self._open_report_generation)

        self.pbs_toggle_button = QToolButton()
        self.pbs_toggle_button.setText(messages.WORKSPACE_PBS_TOGGLE_LABEL)
        self.pbs_toggle_button.setToolTip(messages.WORKSPACE_PBS_TOGGLE_TOOLTIP)
        self.pbs_toggle_button.setCheckable(True)
        self.pbs_toggle_button.setChecked(True)
        self.pbs_toggle_button.toggled.connect(self._on_pbs_toggle)

        self.show_whole_project_button = QPushButton(messages.WORKSPACE_SHOW_WHOLE_PROJECT_BUTTON)
        self.show_whole_project_button.setToolTip(messages.WORKSPACE_SHOW_WHOLE_PROJECT_TOOLTIP)
        self.show_whole_project_button.clicked.connect(self._on_show_whole_project_clicked)

        self._build_modus_segmented_control()
        self._build_validate_status_strip()

    def _build_validate_status_strip(self) -> None:
        self.validate_status_label = QLabel(messages.status_label("idle"))
        self.validate_summary_label = QLabel("")
        self.validate_summary_label.setWordWrap(True)
        self._apply_semantic_status_style(self.validate_status_label, "idle")

    def _build_modus_segmented_control(self) -> None:
        """Toolbar: drie modus-knoppen (Top 10, Tijdsplot, FM-detail)."""
        labels = (
            (MODE_BIJDRAGEN, messages.WORKSPACE_MODE_BIJDRAGEN),
            (MODE_LCC, messages.WORKSPACE_MODE_LCC),
            (MODE_FM_DETAIL, messages.WORKSPACE_MODE_FM_DETAIL),
        )
        self.modus_button_group = QButtonGroup(self)
        self.modus_button_group.setExclusive(True)
        self.modus_buttons: dict[str, QToolButton] = {}
        for modus_key, label in labels:
            button = QToolButton()
            button.setText(label)
            button.setCheckable(True)
            button.setChecked(modus_key == MODE_BIJDRAGEN)
            if modus_key == MODE_LCC:
                button.setToolTip(messages.WORKSPACE_LCC_MODE_TOOLTIP)
            button.clicked.connect(
                lambda _checked=False, key=modus_key: self.workspace_state.set_modus(key)
            )
            self.modus_button_group.addButton(button)
            self.modus_buttons[modus_key] = button

        self._build_top10_subbar()

    def _build_top10_subbar(self) -> None:
        """Sub-balk voor Top 10: bron, metric, horizon en NB-weergave."""
        self.top10_subbar = QWidget()
        row = QHBoxLayout(self.top10_subbar)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(QLabel(messages.WORKSPACE_TOP10_SUBBAR_LABEL))

        self.source_button_group = QButtonGroup(self.top10_subbar)
        self.source_button_group.setExclusive(True)
        self.source_toggle_pbs_button = QToolButton()
        self.source_toggle_pbs_button.setText(messages.WORKSPACE_SOURCE_TOGGLE_PBS)
        self.source_toggle_pbs_button.setCheckable(True)
        self.source_toggle_pbs_button.setChecked(True)
        self.source_toggle_pbs_button.clicked.connect(
            lambda _checked=False: self.workspace_state.set_source(SOURCE_PBS)
        )
        self.source_toggle_faalwijze_button = QToolButton()
        self.source_toggle_faalwijze_button.setText(
            messages.WORKSPACE_SOURCE_TOGGLE_FAALWIJZE
        )
        self.source_toggle_faalwijze_button.setCheckable(True)
        self.source_toggle_faalwijze_button.clicked.connect(
            lambda _checked=False: self.workspace_state.set_source(SOURCE_FAALWIJZE)
        )
        self.source_button_group.addButton(self.source_toggle_pbs_button)
        self.source_button_group.addButton(self.source_toggle_faalwijze_button)
        row.addWidget(self.source_toggle_pbs_button)
        row.addWidget(self.source_toggle_faalwijze_button)
        row.addSpacing(8)

        self.metric_combo = QComboBox()
        metric_labels = {
            METRIC_FAALMOMENTEN: messages.WORKSPACE_METRIC_FAALMOMENTEN,
            METRIC_NIET_BESCHIKBAARHEID: messages.WORKSPACE_METRIC_NIET_BESCHIKBAARHEID,
            METRIC_KOSTEN: messages.WORKSPACE_METRIC_KOSTEN,
        }
        for metric_key in ALL_METRICS:
            self.metric_combo.addItem(metric_labels[metric_key], userData=metric_key)
        self.metric_combo.currentIndexChanged.connect(self._on_metric_combo_changed)
        row.addWidget(self.metric_combo)
        row.addSpacing(12)

        self.horizon_button_group = QButtonGroup(self.top10_subbar)
        self.horizon_button_group.setExclusive(True)
        self.horizon_lifecycle_button = QToolButton()
        self.horizon_lifecycle_button.setText(
            messages.WORKSPACE_CONTRIBUTION_HORIZON_LIFECYCLE
        )
        self.horizon_lifecycle_button.setCheckable(True)
        self.horizon_lifecycle_button.setToolTip(
            messages.WORKSPACE_CONTRIBUTION_HORIZON_TOOLTIP
        )
        self.horizon_lifecycle_button.clicked.connect(
            lambda _c=False: self.workspace_state.set_contribution_horizon("lifecycle")
        )
        self.horizon_per_year_button = QToolButton()
        self.horizon_per_year_button.setText(
            messages.WORKSPACE_CONTRIBUTION_HORIZON_PER_YEAR
        )
        self.horizon_per_year_button.setCheckable(True)
        self.horizon_per_year_button.setChecked(True)
        self.horizon_per_year_button.setToolTip(
            messages.WORKSPACE_CONTRIBUTION_HORIZON_TOOLTIP
        )
        self.horizon_per_year_button.clicked.connect(
            lambda _c=False: self.workspace_state.set_contribution_horizon("per_year")
        )
        self.horizon_button_group.addButton(self.horizon_lifecycle_button)
        self.horizon_button_group.addButton(self.horizon_per_year_button)
        row.addWidget(self.horizon_lifecycle_button)
        row.addWidget(self.horizon_per_year_button)

        self.contribution_year_combo = QComboBox()
        self.contribution_year_combo.addItem(
            messages.WORKSPACE_CONTRIBUTION_YEAR_AVERAGE,
            userData="average",
        )
        self.contribution_year_combo.setToolTip(
            messages.WORKSPACE_CONTRIBUTION_YEAR_AVERAGE_TOOLTIP
        )
        self.contribution_year_combo.currentIndexChanged.connect(
            self._on_contribution_year_combo_changed
        )
        row.addWidget(self.contribution_year_combo)

        self.nb_display_button_group = QButtonGroup(self.top10_subbar)
        self.nb_display_button_group.setExclusive(True)
        self.nb_hours_button = QToolButton()
        self.nb_hours_button.setText(messages.WORKSPACE_CONTRIBUTION_NB_HOURS)
        self.nb_hours_button.setCheckable(True)
        self.nb_hours_button.setChecked(True)
        self.nb_hours_button.clicked.connect(
            lambda _c=False: self.workspace_state.set_unavailability_display("hours")
        )
        self.nb_percent_button = QToolButton()
        self.nb_percent_button.setText(messages.WORKSPACE_CONTRIBUTION_NB_PERCENT)
        self.nb_percent_button.setCheckable(True)
        self.nb_percent_button.setToolTip(
            messages.WORKSPACE_CONTRIBUTION_NB_PERCENT_TOOLTIP
        )
        self.nb_percent_button.clicked.connect(
            lambda _c=False: self.workspace_state.set_unavailability_display("percent")
        )
        self.nb_display_button_group.addButton(self.nb_hours_button)
        self.nb_display_button_group.addButton(self.nb_percent_button)
        row.addWidget(self.nb_hours_button)
        row.addWidget(self.nb_percent_button)
        row.addStretch(1)

    def _on_metric_combo_changed(self, _idx: int) -> None:
        metric = self.metric_combo.currentData()
        if isinstance(metric, str):
            self.workspace_state.set_metric(metric)

    def _on_contribution_year_combo_changed(self, _idx: int) -> None:
        data = self.contribution_year_combo.currentData()
        if data == "average":
            self.workspace_state.set_contribution_year_choice("average")
        elif isinstance(data, int):
            self.workspace_state.set_contribution_year_choice(data)

    def _refresh_contribution_year_combo(self, project) -> None:
        """Vul kalenderjaren uit projectconfig (alleen bij geladen project)."""
        blocker = self.contribution_year_combo.blockSignals(True)
        current = self.contribution_year_combo.currentData()
        self.contribution_year_combo.clear()
        self.contribution_year_combo.addItem(
            messages.WORKSPACE_CONTRIBUTION_YEAR_AVERAGE,
            userData="average",
        )
        session = self._project_session()
        if session is not None:
            for year in wss.calendar_years_for_session(session):
                self.contribution_year_combo.addItem(str(year), userData=year)
        if current is not None:
            idx = self.contribution_year_combo.findData(current)
            if idx >= 0:
                self.contribution_year_combo.setCurrentIndex(idx)
        self.contribution_year_combo.blockSignals(blocker)

    def _build_pbs_sidebar(self) -> None:
        self.pbs_sidebar = QWidget()
        sidebar_layout = QVBoxLayout(self.pbs_sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        title = QLabel(messages.WORKSPACE_PBS_SIDEBAR_TITLE)
        title.setStyleSheet("font-weight: 600;")
        sidebar_layout.addWidget(title)

        self.pbs_filter_input = QLineEdit()
        self.pbs_filter_input.setPlaceholderText(messages.WORKSPACE_PBS_FILTER_PLACEHOLDER)
        self.pbs_filter_input.setToolTip(messages.WORKSPACE_PBS_FILTER_TOOLTIP)
        self.pbs_filter_input.textChanged.connect(self._on_pbs_filter_text_changed)
        sidebar_layout.addWidget(self.pbs_filter_input)

        self.pbs_tree_view = QTreeView()
        self.pbs_tree_view.setSortingEnabled(False)
        self.pbs_tree_view.setAlternatingRowColors(True)
        self.pbs_tree_view.setHeaderHidden(False)
        self.pbs_tree_view.header().setSectionResizeMode(QHeaderView.Interactive)
        self.pbs_tree_view.header().setStretchLastSection(True)
        self.pbs_tree_view.setSelectionBehavior(QTreeView.SelectRows)
        sidebar_layout.addWidget(self.pbs_tree_view, stretch=1)

        self.pbs_empty_state_label = QLabel(messages.WORKSPACE_PBS_EMPTY_STATE)
        self.pbs_empty_state_label.setWordWrap(True)
        self.pbs_empty_state_label.setVisible(False)
        sidebar_layout.addWidget(self.pbs_empty_state_label)

        self.pbs_proxy = _PBSSidebarFilterProxy(self.pbs_tree_view)
        self.pbs_tree_view.setModel(self.pbs_proxy)

    def _build_detail_zone(self) -> None:
        self.detail_zone = QWidget()
        detail_layout = QVBoxLayout(self.detail_zone)

        self.kpi_placeholder = QLabel(messages.WORKSPACE_KPI_PLACEHOLDER)
        self.kpi_placeholder.setStyleSheet("color: #757575; font-style: italic;")
        self.kpi_placeholder.setVisible(False)
        detail_layout.addWidget(self.kpi_placeholder)

        self.scope_status_label = QLabel("")
        self.scope_status_label.setStyleSheet("color: #424242;")
        detail_layout.addWidget(self.scope_status_label)

        self.detail_stack = QStackedWidget()
        self.bijdragen_page = self._build_bijdragen_page()
        self.lcc_page = self._build_lcc_page()
        self.fm_detail_page = self._build_fm_detail_page()

        self._detail_pages: dict[str, QWidget] = {
            MODE_BIJDRAGEN: self.bijdragen_page,
            MODE_LCC: self.lcc_page,
            MODE_FM_DETAIL: self.fm_detail_page,
        }
        for modus_key in (MODE_BIJDRAGEN, MODE_LCC, MODE_FM_DETAIL):
            self.detail_stack.addWidget(self._detail_pages[modus_key])
        detail_layout.addWidget(self.detail_stack, stretch=1)


    def _build_bijdragen_page(self) -> QWidget:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)

        self.bijdragen_chart_label = QLabel(messages.WORKSPACE_BIJDRAGE_EMPTY_STATE)
        self.bijdragen_chart_label.setStyleSheet("color: #9E9E9E;")
        page_layout.addWidget(self.bijdragen_chart_label)

        # Legacy single-slot pane.
        self.bijdragen_single_slot_pane = QWidget()
        single_layout = QVBoxLayout(self.bijdragen_single_slot_pane)
        single_layout.setContentsMargins(0, 0, 0, 0)
        self.bijdragen_chart_widget = ContributionBarChartWidget()
        single_layout.addWidget(self.bijdragen_chart_widget, stretch=2)
        self.bijdragen_table_view = QTableView()
        self.bijdragen_table_view.setAlternatingRowColors(True)
        _apply_workspace_data_table_header_policy(self.bijdragen_table_view.horizontalHeader())
        single_layout.addWidget(self.bijdragen_table_view, stretch=1)
        page_layout.addWidget(self.bijdragen_single_slot_pane, stretch=1)
        self.bijdragen_compare_pane = QWidget()
        compare_layout = QHBoxLayout(self.bijdragen_compare_pane)
        compare_layout.setContentsMargins(0, 0, 0, 0)
        self._bijdragen_compare_col_a = build_bijdragen_compare_column(self.bijdragen_compare_pane)
        self._bijdragen_compare_col_b = build_bijdragen_compare_column(self.bijdragen_compare_pane)
        compare_layout.addWidget(self._bijdragen_compare_col_a["host"], stretch=1)
        compare_layout.addWidget(self._bijdragen_compare_col_b["host"], stretch=1)
        self.bijdragen_compare_pane.setVisible(False)
        page_layout.addWidget(self.bijdragen_compare_pane, stretch=1)
        return page

    def _build_lcc_page(self) -> QWidget:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)

        self.lcc_empty_state_label = QLabel(messages.WORKSPACE_LCC_EMPTY_STATE)
        self.lcc_empty_state_label.setStyleSheet("color: #9E9E9E;")
        self.lcc_empty_state_label.setVisible(True)
        page_layout.addWidget(self.lcc_empty_state_label)

        self.lcc_filter_bar = QWidget()
        filter_bar_layout = QVBoxLayout(self.lcc_filter_bar)
        filter_bar_layout.setContentsMargins(0, 0, 0, 0)
        filter_bar_layout.setSpacing(2)
        whatif_header = QHBoxLayout()
        self.lcc_whatif_collapse_button = QToolButton()
        self.lcc_whatif_collapse_button.setToolTip(messages.WORKSPACE_LCC_WHATIF_COLLAPSE_TOOLTIP)
        self.lcc_whatif_collapse_button.clicked.connect(self._on_lcc_whatif_collapse_toggled)
        self.lcc_whatif_bar_title = QLabel(messages.WORKSPACE_LCC_WHATIF_BAR_TITLE)
        self.lcc_whatif_bar_title.setStyleSheet("font-weight: 600;")
        whatif_header.addWidget(self.lcc_whatif_collapse_button)
        whatif_header.addWidget(self.lcc_whatif_bar_title)
        whatif_header.addStretch(1)
        filter_bar_layout.addLayout(whatif_header)
        self.lcc_whatif_content = QWidget()
        filter_layout = QHBoxLayout(self.lcc_whatif_content)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        self._lcc_filter_checks: dict[str, QCheckBox] = {}
        for key, label in (
            ("cm", messages.WORKSPACE_LCC_FILTER_CM),
            ("rev", messages.WORKSPACE_LCC_FILTER_REV),
            ("in_task", messages.WORKSPACE_LCC_FILTER_IN),
            ("tst", messages.WORKSPACE_LCC_FILTER_TST),
            ("svo", messages.WORKSPACE_LCC_FILTER_SVO),
            ("wet", messages.WORKSPACE_LCC_FILTER_WET),
        ):
            box = QCheckBox(label)
            box.setChecked(True)
            box.toggled.connect(self._on_lcc_filter_toggled)
            self._lcc_filter_checks[key] = box
            filter_layout.addWidget(box)
        filter_layout.addStretch(1)
        self.lcc_whatif_button = QPushButton(messages.WORKSPACE_LCC_WHAT_IF_TOGGLE)
        self.lcc_whatif_button.setCheckable(True)
        self.lcc_whatif_button.toggled.connect(self._on_lcc_whatif_toggled)
        filter_layout.addWidget(self.lcc_whatif_button)
        self.lcc_reset_overlay_button = QPushButton(messages.WORKSPACE_LCC_RESET_OVERLAY)
        self.lcc_reset_overlay_button.clicked.connect(self._on_lcc_reset_overlay)
        filter_layout.addWidget(self.lcc_reset_overlay_button)
        self.lcc_bulk_rev_passive_button = QPushButton(messages.WORKSPACE_LCC_BULK_REV_PASSIVE)
        self.lcc_bulk_rev_passive_button.clicked.connect(self._on_lcc_bulk_rev_toggle)
        filter_layout.addWidget(self.lcc_bulk_rev_passive_button)
        self.lcc_cm_preset_button = QPushButton(messages.WORKSPACE_LCC_CM_POLICY_PRESET)
        self.lcc_cm_preset_button.setToolTip(messages.WORKSPACE_LCC_CM_PRESET_TOOLTIP)
        self.lcc_cm_preset_button.clicked.connect(self._on_lcc_cm_policy_preset)
        filter_layout.addWidget(self.lcc_cm_preset_button)
        filter_bar_layout.addWidget(self.lcc_whatif_content)
        self.lcc_filter_bar.setVisible(False)
        page_layout.addWidget(self.lcc_filter_bar)

        self.lcc_overlay_status_label = QLabel("")
        self.lcc_overlay_status_label.setStyleSheet("color: #E65100; font-weight: 600;")
        page_layout.addWidget(self.lcc_overlay_status_label)

        self.meekoppel_panel = QWidget()
        meekoppel_layout = QVBoxLayout(self.meekoppel_panel)
        meekoppel_layout.setContentsMargins(0, 0, 0, 0)
        meekoppel_layout.setSpacing(2)
        meekoppel_header = QHBoxLayout()
        self.meekoppel_collapse_button = QToolButton()
        self.meekoppel_collapse_button.setToolTip(messages.WORKSPACE_MEEKOPPEL_COLLAPSE_TOOLTIP)
        self.meekoppel_collapse_button.clicked.connect(self._on_meekoppel_collapse_toggled)
        self.meekoppel_title_label = QLabel(messages.WORKSPACE_MEEKOPPEL_PANEL_TITLE)
        self.meekoppel_title_label.setStyleSheet("font-weight: 600;")
        meekoppel_header.addWidget(self.meekoppel_collapse_button)
        meekoppel_header.addWidget(self.meekoppel_title_label)
        meekoppel_header.addStretch(1)
        meekoppel_layout.addLayout(meekoppel_header)
        self.meekoppel_content = QWidget()
        meekoppel_content_layout = QVBoxLayout(self.meekoppel_content)
        meekoppel_content_layout.setContentsMargins(0, 0, 0, 0)
        self.meekoppel_help_label = QLabel(messages.WORKSPACE_MEEKOPPEL_PANEL_HELP)
        self.meekoppel_help_label.setWordWrap(True)
        self.meekoppel_help_label.setStyleSheet("color: #616161; font-size: 11px;")
        meekoppel_content_layout.addWidget(self.meekoppel_help_label)
        self.meekoppel_whatif_hint_label = QLabel(messages.WORKSPACE_MEEKOPPEL_WHATIF_HINT)
        self.meekoppel_whatif_hint_label.setWordWrap(True)
        self.meekoppel_whatif_hint_label.setStyleSheet("color: #757575;")
        meekoppel_content_layout.addWidget(self.meekoppel_whatif_hint_label)
        self.meekoppel_selection_summary_label = QLabel("")
        self.meekoppel_selection_summary_label.setWordWrap(True)
        self.meekoppel_selection_summary_label.setStyleSheet("color: #616161;")
        self.meekoppel_selection_summary_label.setVisible(False)
        meekoppel_content_layout.addWidget(self.meekoppel_selection_summary_label)
        meekoppel_tb = QHBoxLayout()
        meekoppel_tb.addWidget(QLabel(messages.WORKSPACE_MEEKOPPEL_WINDOW_LABEL))
        self.meekoppel_window_spin = QSpinBox()
        self.meekoppel_window_spin.setRange(1, 5)
        self.meekoppel_window_spin.setValue(2)
        self.meekoppel_window_spin.valueChanged.connect(self._on_meekoppel_window_changed)
        meekoppel_tb.addWidget(self.meekoppel_window_spin)
        self.meekoppel_anchor_earlier = QRadioButton(messages.WORKSPACE_MEEKOPPEL_ANCHOR_EARLIER)
        self.meekoppel_anchor_later = QRadioButton(messages.WORKSPACE_MEEKOPPEL_ANCHOR_LATER)
        self.meekoppel_anchor_later.setChecked(True)
        self._meekoppel_anchor_group = QButtonGroup(self)
        self._meekoppel_anchor_group.addButton(self.meekoppel_anchor_earlier)
        self._meekoppel_anchor_group.addButton(self.meekoppel_anchor_later)
        self._meekoppel_anchor_group.buttonClicked.connect(self._on_meekoppel_anchor_changed)
        meekoppel_tb.addWidget(self.meekoppel_anchor_earlier)
        meekoppel_tb.addWidget(self.meekoppel_anchor_later)
        self.meekoppel_preview_button = QPushButton(messages.WORKSPACE_MEEKOPPEL_PREVIEW)
        self.meekoppel_preview_button.clicked.connect(self._on_meekoppel_preview)
        meekoppel_tb.addWidget(self.meekoppel_preview_button)
        self.meekoppel_apply_button = QPushButton(messages.WORKSPACE_MEEKOPPEL_APPLY)
        self.meekoppel_apply_button.clicked.connect(self._on_meekoppel_apply)
        meekoppel_tb.addWidget(self.meekoppel_apply_button)
        meekoppel_tb.addStretch(1)
        meekoppel_content_layout.addLayout(meekoppel_tb)
        self.meekoppel_empty_label = QLabel(messages.WORKSPACE_MEEKOPPEL_EMPTY)
        self.meekoppel_empty_label.setStyleSheet("color: #9E9E9E;")
        meekoppel_content_layout.addWidget(self.meekoppel_empty_label)
        self.meekoppel_table_view = QTableView()
        self.meekoppel_table_view.setAlternatingRowColors(True)
        self.meekoppel_table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.meekoppel_table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        _apply_workspace_data_table_header_policy(self.meekoppel_table_view.horizontalHeader())
        self._meekoppel_table_model = MeekoppelSuggestionsTableModel(parent=self.meekoppel_table_view)
        self.meekoppel_table_view.setModel(self._meekoppel_table_model)
        meekoppel_content_layout.addWidget(self.meekoppel_table_view, stretch=1)
        meekoppel_layout.addWidget(self.meekoppel_content)
        self.meekoppel_panel.setVisible(False)
        self._meekoppel_preview_gate: MeekoppelPreviewGate | None = None
        self._meekoppel_location_groups: tuple[MeekoppelLocationGroup, ...] = ()
        self._meekoppel_workflow = MeekoppelWorkflowService()
        page_layout.addWidget(self.meekoppel_panel)

        self.lcc_year_summary_label = QLabel("")
        self.lcc_year_summary_label.setWordWrap(True)
        page_layout.addWidget(self.lcc_year_summary_label)

        self.lcc_show_all_years_button = QPushButton(messages.WORKSPACE_LCC_SHOW_ALL_YEARS)
        self.lcc_show_all_years_button.clicked.connect(self._on_lcc_show_all_years)
        page_layout.addWidget(self.lcc_show_all_years_button)

        self.lcc_detail_toolbar = QWidget()
        detail_tb = QHBoxLayout(self.lcc_detail_toolbar)
        detail_tb.setContentsMargins(0, 0, 0, 0)
        self.lcc_shift_selection_hint = QLabel(messages.WORKSPACE_LCC_SHIFT_SELECTION_HINT)
        self.lcc_shift_selection_hint.setWordWrap(True)
        detail_tb.addWidget(self.lcc_shift_selection_hint, stretch=1)
        self.lcc_select_rev_button = QPushButton(messages.WORKSPACE_LCC_SELECT_REV_IN_YEAR)
        self.lcc_select_rev_button.clicked.connect(self._on_lcc_select_rev_in_year)
        detail_tb.addWidget(self.lcc_select_rev_button)
        self.lcc_shift_spin = QSpinBox()
        self.lcc_shift_spin.setMinimum(-50)
        self.lcc_shift_spin.setMaximum(50)
        self.lcc_shift_spin.setToolTip(messages.WORKSPACE_LCC_SHIFT_SPIN_TOOLTIP)
        detail_tb.addWidget(self.lcc_shift_spin)
        self.lcc_shift_button = QPushButton(messages.WORKSPACE_LCC_SHIFT_SELECTED)
        self.lcc_shift_button.clicked.connect(self._on_lcc_shift_selected)
        detail_tb.addWidget(self.lcc_shift_button)
        detail_tb.addStretch(1)
        self.lcc_detail_toolbar.setVisible(False)
        page_layout.addWidget(self.lcc_detail_toolbar)

        # Single-run pane voor de LCC-weergave.
        # Attribuutnamen blijven stabiel voor bestaande UI-tests.
        self.lcc_single_slot_pane = QWidget()
        single_layout = QVBoxLayout(self.lcc_single_slot_pane)
        single_layout.setContentsMargins(0, 0, 0, 0)
        self.lcc_chart_widget = LCCStackedBarChartWidget()
        self.lcc_chart_widget.year_clicked.connect(self._on_lcc_year_clicked)
        single_layout.addWidget(self.lcc_chart_widget, stretch=2)
        self.lcc_table_view = QTableView()
        self.lcc_table_view.setAlternatingRowColors(True)
        _apply_workspace_data_table_header_policy(self.lcc_table_view.horizontalHeader())
        single_layout.addWidget(self.lcc_table_view, stretch=1)
        self.lcc_detail_table_view = QTableView()
        self.lcc_detail_table_view.setAlternatingRowColors(True)
        _apply_workspace_data_table_header_policy(self.lcc_detail_table_view.horizontalHeader())
        single_layout.addWidget(self.lcc_detail_table_view, stretch=1)
        self._lcc_detail_model = LCCYearDetailTableModel(parent=self.lcc_detail_table_view)
        self.lcc_detail_table_view.setModel(self._lcc_detail_model)
        self.lcc_detail_table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.lcc_detail_table_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lcc_detail_table_view.clicked.connect(self._on_lcc_detail_cell_clicked)
        page_layout.addWidget(self.lcc_single_slot_pane, stretch=1)
        self.lcc_compare_pane = QWidget()
        lcc_compare_layout = QVBoxLayout(self.lcc_compare_pane)
        lcc_compare_layout.setContentsMargins(0, 0, 0, 0)
        self._lcc_compare_col_a = build_lcc_compare_column(self.lcc_compare_pane)
        self._lcc_compare_col_b = build_lcc_compare_column(self.lcc_compare_pane)
        self._lcc_compare_col_a["chart"].year_clicked.connect(self._on_lcc_year_clicked)
        self._lcc_compare_col_b["chart"].year_clicked.connect(self._on_lcc_year_clicked)
        lcc_compare_layout.addWidget(self._lcc_compare_col_a["host"], stretch=1)
        lcc_compare_layout.addWidget(self._lcc_compare_col_b["host"], stretch=1)
        self.lcc_compare_pane.setVisible(False)
        page_layout.addWidget(self.lcc_compare_pane, stretch=1)
        return page

    def _build_fm_detail_page(self) -> QWidget:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)

        self.fm_detail_splitter = QSplitter(Qt.Vertical)
        table_host = QWidget()
        table_layout = QVBoxLayout(table_host)
        table_layout.setContentsMargins(0, 0, 0, 0)
        fm_toolbar = QHBoxLayout()
        self.new_fm_button = QPushButton(messages.FM_EDITOR_NEW_FM)
        self.new_fm_button.setToolTip(messages.FM_EDITOR_NEW_FM_TOOLTIP)
        self.new_fm_button.clicked.connect(self._on_new_fm_clicked)
        fm_toolbar.addWidget(self.new_fm_button)
        fm_toolbar.addStretch(1)
        table_layout.addLayout(fm_toolbar)
        self.fm_table_view = QTableView()
        self.fm_table_view.setSortingEnabled(True)
        self.fm_table_view.setAlternatingRowColors(True)
        self.fm_table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.fm_table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self._fm_table_proxy = FMResultsSortProxy(self.fm_table_view)
        self.fm_table_view.setModel(self._fm_table_proxy)
        sel = self.fm_table_view.selectionModel()
        if sel is not None:
            sel.selectionChanged.connect(self._on_fm_table_selection_changed)
        self.fm_table_view.doubleClicked.connect(self._on_fm_table_double_clicked)
        table_layout.addWidget(self.fm_table_view, stretch=1)
        self.detail_empty_state_label = QLabel(messages.WORKSPACE_DETAIL_EMPTY_STATE)
        self.detail_empty_state_label.setStyleSheet("color: #9E9E9E;")
        table_layout.addWidget(self.detail_empty_state_label)
        self.fm_detail_splitter.addWidget(table_host)

        self.fm_inspector_container = QWidget()
        inspector_layout = QVBoxLayout(self.fm_inspector_container)
        inspector_layout.setContentsMargins(4, 4, 4, 4)
        inspector_title = QLabel(messages.WORKSPACE_FM_INSPECTOR_TITLE)
        inspector_title.setStyleSheet("font-weight: bold;")
        inspector_layout.addWidget(inspector_title)
        self.fm_inspector_empty_label = QLabel(messages.WORKSPACE_FM_INSPECTOR_EMPTY)
        self.fm_inspector_empty_label.setStyleSheet("color: #9E9E9E;")
        inspector_layout.addWidget(self.fm_inspector_empty_label)
        self.fm_inspector_panel = QWidget()
        panel_layout = QVBoxLayout(self.fm_inspector_panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        self.fm_inspector_identity_label = QLabel()
        self.fm_inspector_identity_label.setWordWrap(True)
        panel_layout.addWidget(self.fm_inspector_identity_label)
        self.fm_inspector_lifecycle_label = QLabel()
        self.fm_inspector_lifecycle_label.setWordWrap(True)
        panel_layout.addWidget(self.fm_inspector_lifecycle_label)
        self.fm_inspector_hash_label = QLabel()
        self.fm_inspector_hash_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )
        panel_layout.addWidget(self.fm_inspector_hash_label)
        self.fm_inspector_reconcile_label = QLabel()
        self.fm_inspector_reconcile_label.setWordWrap(True)
        panel_layout.addWidget(self.fm_inspector_reconcile_label)
        self.fm_inspector_profile_missing_label = QLabel()
        self.fm_inspector_profile_missing_label.setWordWrap(True)
        self.fm_inspector_profile_missing_label.setStyleSheet("color: #E65100;")
        panel_layout.addWidget(self.fm_inspector_profile_missing_label)
        self.fm_inspector_year_table_view = QTableView()
        self.fm_inspector_year_table_view.setAlternatingRowColors(True)
        self.fm_inspector_year_table_view.setToolTip(
            messages.WORKSPACE_FM_INSPECTOR_FAALMOMENTEN_PROXY_TOOLTIP
        )
        self.fm_inspector_year_table_view.horizontalHeader().setStretchLastSection(True)
        panel_layout.addWidget(self.fm_inspector_year_table_view, stretch=1)
        inspector_layout.addWidget(self.fm_inspector_panel)
        self.fm_inspector_panel.setVisible(False)
        self.fm_inspector_container.setVisible(False)
        self.fm_detail_splitter.addWidget(self.fm_inspector_container)
        self.fm_detail_splitter.setStretchFactor(0, 2)
        self.fm_detail_splitter.setStretchFactor(1, 1)

        page_layout.addWidget(self.fm_detail_splitter, stretch=1)
        return page

    def _build_placeholder_page(self, text: str) -> QWidget:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet("color: #757575; font-style: italic;")
        page_layout.addWidget(label, stretch=1)
        return page

    def _build_layout(self) -> None:
        root = QWidget()
        outer = QVBoxLayout(root)
        toolbar_row = QHBoxLayout()
        for w in (
            self.path_input,
            self.pick_button,
            self.open_isograph_button,
            self.validate_button,
            self.batch_faalwijzen_button,
            self.model_settings_button,
            self.generate_report_button,
            self.compare_scenario_combo,
            self.run_slot_a_button,
            self.run_slot_b_button,
            self.compare_toggle_button,
            self.clear_compare_button,
            self.run_analyse_button,
        ):
            toolbar_row.addWidget(w)
        toolbar_row.addStretch(1)
        toolbar_row.addWidget(self.pbs_toggle_button)
        toolbar_row.addWidget(self.show_whole_project_button)

        modus_row = QHBoxLayout()
        for key in (MODE_BIJDRAGEN, MODE_LCC, MODE_FM_DETAIL):
            modus_row.addWidget(self.modus_buttons[key])
        self.fm_evident_filter_combo = QComboBox()
        for label, value in (
            (messages.WORKSPACE_FM_EVIDENT_FILTER_ALL, "all"),
            (messages.WORKSPACE_FM_EVIDENT_FILTER_NMF, "nmf_only"),
            (messages.WORKSPACE_FM_EVIDENT_FILTER_EVIDENT, "evident_only"),
        ):
            self.fm_evident_filter_combo.addItem(label, value)
        self.fm_evident_filter_combo.currentIndexChanged.connect(
            self._on_fm_evident_filter_changed
        )
        modus_row.addWidget(self.fm_evident_filter_combo)
        modus_row.addStretch(1)

        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.addWidget(self.pbs_sidebar)
        self.main_splitter.addWidget(self.detail_zone)
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setSizes([320, 720])

        self.kpi_panel = QWidget()
        kpi_panel_layout = QVBoxLayout(self.kpi_panel)
        kpi_panel_layout.setContentsMargins(0, 0, 0, 0)
        kpi_panel_layout.setSpacing(2)
        kpi_header = QHBoxLayout()
        self.kpi_collapse_button = QToolButton()
        self.kpi_collapse_button.setToolTip(messages.WORKSPACE_KPI_COLLAPSE_TOOLTIP)
        self.kpi_collapse_button.clicked.connect(self._on_kpi_collapse_toggled)
        self.kpi_panel_title = QLabel(messages.WORKSPACE_KPI_PANEL_TITLE)
        kpi_header.addWidget(self.kpi_collapse_button)
        kpi_header.addWidget(self.kpi_panel_title)
        kpi_header.addStretch(1)
        kpi_panel_layout.addLayout(kpi_header)
        self.kpi_table_view = QTableView()
        self.kpi_table_view.setAlternatingRowColors(True)
        _apply_workspace_data_table_header_policy(self.kpi_table_view.horizontalHeader())
        self.kpi_table_view.horizontalHeader().setSectionsClickable(False)
        self.kpi_table_view.verticalHeader().setVisible(False)
        self.kpi_table_view.setMaximumHeight(140)
        kpi_panel_layout.addWidget(self.kpi_table_view)

        validate_row = QHBoxLayout()
        validate_row.addWidget(self.validate_status_label)
        validate_row.addWidget(self.validate_summary_label, stretch=1)

        outer.addLayout(toolbar_row)
        outer.addLayout(validate_row)
        outer.addLayout(modus_row)
        outer.addWidget(self.top10_subbar)
        outer.addWidget(self.kpi_panel)
        outer.addWidget(self.main_splitter, stretch=1)
        self._refresh_kpi_table_view()

        self.setCentralWidget(root)
        self.resize(1100, 640)

    def _wire_pbs_tree_interaction(self) -> None:
        selection = self.pbs_tree_view.selectionModel()
        if selection is not None:
            selection.selectionChanged.connect(self._on_pbs_tree_selection_changed)

    def _set_default_fixture_path(self) -> None:
        default_path = resolve_default_fixture_path()
        if default_path is not None:
            self.path_input.setText(str(default_path))

    def _on_pbs_toggle(self, checked: bool) -> None:
        self.pbs_sidebar.setVisible(checked)

    def _expand_pbs_filtered_nodes_capped(self) -> None:
        """Expandeer zichtbare proxy-rijen tot diepte; geen `expandAll` (slice 25)."""
        proxy = self.pbs_proxy
        tree = self.pbs_tree_view
        root = QModelIndex()
        remaining = PBS_FILTER_MAX_EXPAND_NODES
        stack: list[QModelIndex] = [
            proxy.index(r, 0, root) for r in range(proxy.rowCount(root))
        ]
        while stack and remaining > 0:
            idx = stack.pop()
            if not idx.isValid():
                continue
            tree.expand(idx)
            remaining -= 1
            for r in range(proxy.rowCount(idx)):
                stack.append(proxy.index(r, 0, idx))

    def _on_pbs_filter_text_changed(self, text: str) -> None:
        self.pbs_proxy.set_needle(text)
        if self.pbs_proxy.has_needle():
            self._expand_pbs_filtered_nodes_capped()
        else:
            self.pbs_tree_view.collapseAll()
        has_matches = self.pbs_proxy.rowCount(QModelIndex()) > 0
        no_source = self._pbs_source_model is None
        self.pbs_empty_state_label.setVisible(not has_matches and not no_source and self.pbs_proxy.has_needle())

    def _on_pbs_tree_selection_changed(
        self, _selected: QItemSelection, _deselected: QItemSelection
    ) -> None:
        source_model = self._pbs_source_model
        if source_model is None:
            return
        current = self.pbs_tree_view.currentIndex()
        if current.isValid():
            source_index = self.pbs_proxy.mapToSource(current)
            scope_id = self._pbs_scope_from_tree_index(source_model, source_index)
            if scope_id is not None:
                self.set_pbs_scope(scope_id)
        self._sync_new_fm_button_enabled()
        snapshot = self.workspace_state.snapshot()
        if snapshot.modus == MODE_LCC:
            self._clear_meekoppel_preview_gate()
            self._sync_meekoppel_panel(snapshot)

    def _pbs_selected_ids_from_tree(self) -> frozenset[str]:
        source_model = self._pbs_source_model
        if source_model is None:
            return frozenset()
        selection = self.pbs_tree_view.selectionModel()
        if selection is None or not selection.hasSelection():
            return frozenset()
        pbs_ids: set[str] = set()
        for proxy_index in selection.selectedIndexes():
            if proxy_index.column() != 0:
                continue
            source_index = self.pbs_proxy.mapToSource(proxy_index)
            pbs_id = self._pbs_scope_from_tree_index(source_model, source_index)
            if pbs_id is not None:
                pbs_ids.add(pbs_id)
        return frozenset(pbs_ids)

    def _on_show_whole_project_clicked(self) -> None:
        self.set_pbs_scope(None)

    def set_pbs_scope(self, scope_id: str | None) -> None:
        """Stel de actieve PBS-scope in; detailzone volgt via workspace_state."""
        self._pbs_scope_id = scope_id
        self.workspace_state.set_scope(scope_id)
        self._update_scope_status_label()

    def _on_workspace_state_changed(self, snapshot: WorkspaceStateSnapshot) -> None:
        previous = self._last_workspace_snapshot_for_split_depth
        tick = ResultsWorkspaceOrchestrator.plan_workspace_tick(
            previous,
            snapshot,
            self._render_context(),
        )
        self._apply_ui_sync(tick.ui_sync, snapshot)
        self._apply_render_plan(tick.render, snapshot)
        self._last_workspace_snapshot_for_split_depth = snapshot

    def _render_context(self) -> WorkspaceRenderContext:
        return WorkspaceRenderContext(
            session=self._project_session(),
            compare_slots=self._compare_slots,
            project_total_presentation=self._project_total_presentation,
            render_index=self._render_index,
            prev_lcc_snapshot=self._last_lcc_render_snapshot,
        )

    def _rerender_detail_for_current_scope(
        self,
        *,
        split_render_depth: RenderSplitDepth = "active_modus_only",
    ) -> None:
        snapshot = self.workspace_state.snapshot()
        plan = ResultsWorkspaceOrchestrator.plan_render(
            snapshot,
            self._render_context(),
            split_depth=split_render_depth,
        )
        self._apply_render_plan(plan, snapshot)

    def _apply_render_plan(
        self,
        plan: RenderPlan,
        snapshot: WorkspaceStateSnapshot,
    ) -> None:
        if plan.kind == "empty":
            self._clear_detail_zone()
            return
        if plan.kind == "compare_placeholder":
            self._apply_compare_chrome(plan_compare_chrome(snapshot))
            if snapshot.modus == MODE_BIJDRAGEN:
                pairs = (
                    (self._bijdragen_compare_col_a, COMPARE_SLOT_A),
                    (self._bijdragen_compare_col_b, COMPARE_SLOT_B),
                )
            else:
                pairs = (
                    (self._lcc_compare_col_a, COMPARE_SLOT_A),
                    (self._lcc_compare_col_b, COMPARE_SLOT_B),
                )
            for col, slot in pairs:
                set_compare_placeholder(col, slot_key=slot)
            return
        if plan.kind == "fm":
            if plan.fm is not None:
                self._render_fm_rows(plan.fm.fm_rows)
            return
        if plan.kind == "bijdragen":
            self._apply_compare_chrome(plan_compare_chrome(snapshot))
            if plan.bijdragen is not None:
                self._bind_bijdragen_view(plan.bijdragen, snapshot)
            return
        if plan.kind == "lcc":
            self._apply_compare_chrome(plan_compare_chrome(snapshot))
            session = self._project_session()
            if session is not None and plan.lcc is not None:
                self._render_lcc_view(session, plan.lcc, snapshot)
            return
        if plan.kind == "bijdragen_compare":
            self._apply_compare_chrome(plan_compare_chrome(snapshot))
            self._apply_bijdragen_compare_panels(plan.compare_panels or (), snapshot)
            return
        if plan.kind == "lcc_compare":
            self._apply_compare_chrome(plan_compare_chrome(snapshot))
            self._apply_lcc_compare_panels(plan.compare_panels or (), snapshot)
            return

    def _apply_bijdragen_compare_panels(
        self,
        panels: tuple[ComparePanel, ...],
        snapshot: WorkspaceStateSnapshot,
    ) -> None:
        columns = {
            COMPARE_SLOT_A: self._bijdragen_compare_col_a,
            COMPARE_SLOT_B: self._bijdragen_compare_col_b,
        }
        for panel in panels:
            col = columns[panel.slot_key]
            col["header"].setText(
                messages.WORKSPACE_COMPARE_SLOT_HEADER.format(label=panel.label)
            )
            if not panel.filled or panel.bijdragen is None:
                set_compare_placeholder(col, slot_key=panel.slot_key)
                continue
            col["placeholder"].setVisible(False)
            self._bind_bijdragen_column(col, panel.bijdragen, snapshot)

    def _apply_lcc_compare_panels(
        self,
        panels: tuple[ComparePanel, ...],
        snapshot: WorkspaceStateSnapshot,
    ) -> None:
        columns = {
            COMPARE_SLOT_A: self._lcc_compare_col_a,
            COMPARE_SLOT_B: self._lcc_compare_col_b,
        }
        buckets_by_slot: dict[str, tuple] = {}
        for panel in panels:
            col = columns[panel.slot_key]
            col["header"].setText(
                messages.WORKSPACE_COMPARE_SLOT_HEADER.format(label=panel.label)
            )
            if not panel.filled or panel.lcc is None or panel.lcc.curve is None:
                set_compare_placeholder(col, slot_key=panel.slot_key)
                col["chart"].set_buckets(())
                col["chart"].set_scale_max(None)
                continue
            buckets = tuple(panel.lcc.curve.display_buckets)
            buckets_by_slot[panel.slot_key] = buckets
            col["placeholder"].setVisible(False)
            col["chart"].setVisible(True)
            col["table"].setVisible(True)
        y_max = 0.0
        if buckets_by_slot:
            y_max = shared_lcc_y_max(
                buckets_by_slot.get(COMPARE_SLOT_A, ()),
                buckets_by_slot.get(COMPARE_SLOT_B, ()),
            )
        shared_year = resolve_shared_calendar_year(
            workspace_year=snapshot.lcc_calendar_year,
            chart_a_year=None,
            chart_b_year=None,
        )
        for panel in panels:
            if not panel.filled or panel.lcc is None or panel.lcc.curve is None:
                continue
            col = columns[panel.slot_key]
            buckets = tuple(panel.lcc.curve.display_buckets)
            col["chart"].set_scale_max(y_max if y_max > 0 else None)
            col["chart"].set_buckets(buckets)
            col["chart"].set_selected_year(shared_year)
            col["table"].setModel(LCCYearTableModel(buckets))
        self._last_lcc_render_snapshot = snapshot

    def _apply_ui_sync(
        self,
        plan: WorkspaceUiSyncPlan,
        snapshot: WorkspaceStateSnapshot,
    ) -> None:
        page = self._detail_pages.get(plan.detail_page_modus, self.bijdragen_page)
        if self.detail_stack.currentWidget() is not page:
            self.detail_stack.setCurrentWidget(page)
        target_button = self.modus_buttons.get(plan.modus_button)
        if target_button is not None and not target_button.isChecked():
            target_button.setChecked(True)
        if plan.source_toggle == SOURCE_PBS and not self.source_toggle_pbs_button.isChecked():
            self.source_toggle_pbs_button.setChecked(True)
        elif (
            plan.source_toggle == SOURCE_FAALWIJZE
            and not self.source_toggle_faalwijze_button.isChecked()
        ):
            self.source_toggle_faalwijze_button.setChecked(True)
        idx = self.metric_combo.findData(plan.metric)
        if idx >= 0 and idx != self.metric_combo.currentIndex():
            blocker = self.metric_combo.blockSignals(True)
            self.metric_combo.setCurrentIndex(idx)
            self.metric_combo.blockSignals(blocker)
        self._apply_bijdragen_toolbar(plan.bijdragen)
        self._apply_lcc_toolbar(plan.lcc_toolbar, snapshot)
        self._apply_fm_toolbar(plan.fm_toolbar)
        self._apply_compare_chrome(plan.compare)
        if plan.pbs_tree_extended_selection:
            self.pbs_tree_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        else:
            self.pbs_tree_view.setSelectionMode(QAbstractItemView.SingleSelection)
        if plan.refresh_kpi and hasattr(self, "kpi_table_view"):
            self._refresh_kpi_table_view()
        self._apply_collapse_panels(plan.collapse)
        if plan.scope_id != self._pbs_scope_id:
            self._pbs_scope_id = plan.scope_id
            self._update_scope_status_label()

    def _apply_bijdragen_toolbar(self, toolbar: BijdragenToolbarPlan | None) -> None:
        if toolbar is None:
            self.top10_subbar.setVisible(False)
            self.horizon_lifecycle_button.setVisible(False)
            self.horizon_per_year_button.setVisible(False)
            self.contribution_year_combo.setVisible(False)
            self.nb_hours_button.setVisible(False)
            self.nb_percent_button.setVisible(False)
            return
        self.top10_subbar.setVisible(toolbar.top10_subbar_visible)
        self.horizon_lifecycle_button.setVisible(toolbar.horizon_lifecycle_visible)
        self.horizon_per_year_button.setVisible(toolbar.horizon_per_year_visible)
        self.contribution_year_combo.setVisible(toolbar.year_combo_visible)
        self.nb_hours_button.setVisible(toolbar.nb_hours_visible)
        self.nb_percent_button.setVisible(toolbar.nb_percent_visible)
        if toolbar.horizon_lifecycle_visible:
            if toolbar.horizon_lifecycle_checked and not self.horizon_lifecycle_button.isChecked():
                self.horizon_lifecycle_button.setChecked(True)
            elif toolbar.horizon_per_year_checked and not self.horizon_per_year_button.isChecked():
                self.horizon_per_year_button.setChecked(True)
        if toolbar.nb_hours_visible:
            if toolbar.nb_hours_checked and not self.nb_hours_button.isChecked():
                self.nb_hours_button.setChecked(True)
            elif toolbar.nb_percent_checked and not self.nb_percent_button.isChecked():
                self.nb_percent_button.setChecked(True)
        if toolbar.year_combo_visible:
            idx = self.contribution_year_combo.findData(toolbar.year_choice)
            if idx >= 0 and idx != self.contribution_year_combo.currentIndex():
                blocker = self.contribution_year_combo.blockSignals(True)
                self.contribution_year_combo.setCurrentIndex(idx)
                self.contribution_year_combo.blockSignals(blocker)

    def _apply_lcc_toolbar(
        self,
        toolbar: LccToolbarVisibilityPlan | None,
        snapshot: WorkspaceStateSnapshot,
    ) -> None:
        if toolbar is None:
            self.lcc_filter_bar.setVisible(False)
            self.lcc_show_all_years_button.setVisible(False)
            self.lcc_year_summary_label.setVisible(False)
            self.meekoppel_panel.setVisible(False)
            return
        self.lcc_filter_bar.setVisible(toolbar.filter_bar_visible)
        self.lcc_show_all_years_button.setVisible(toolbar.show_all_years_visible)
        self.lcc_year_summary_label.setVisible(toolbar.year_summary_label_visible)
        self.meekoppel_panel.setVisible(toolbar.meekoppel_panel_visible)
        self._sync_lcc_filter_checks(toolbar.lcc_filters)
        self._sync_meekoppel_panel(snapshot)

    def _apply_fm_toolbar(self, toolbar: FmToolbarPlan) -> None:
        self.batch_faalwijzen_button.setVisible(toolbar.batch_faalwijzen_visible)
        if hasattr(self, "new_fm_button"):
            self.new_fm_button.setVisible(toolbar.new_fm_visible)
            if toolbar.new_fm_visible:
                self._sync_new_fm_button_enabled()
        self.fm_evident_filter_combo.setVisible(toolbar.fm_evident_filter_visible)
        self.fm_evident_filter_combo.setEnabled(toolbar.fm_evident_filter_visible)
        if hasattr(self, "fm_inspector_container"):
            self.fm_inspector_container.setVisible(toolbar.fm_inspector_visible)
            if toolbar.clear_fm_inspector:
                self._refresh_fm_inspector(None)

    def _apply_compare_chrome(self, compare: CompareChromePlan) -> None:
        if hasattr(self, "compare_toggle_button"):
            if self.compare_toggle_button.isChecked() != compare.compare_mode_checked:
                blocker = self.compare_toggle_button.blockSignals(True)
                self.compare_toggle_button.setChecked(compare.compare_mode_checked)
                self.compare_toggle_button.blockSignals(blocker)
        if hasattr(self, "bijdragen_single_slot_pane"):
            self.bijdragen_single_slot_pane.setVisible(compare.bijdragen_single_visible)
            self.bijdragen_compare_pane.setVisible(compare.bijdragen_compare_visible)
            self.bijdragen_chart_label.setVisible(compare.bijdragen_chart_label_visible)
        if hasattr(self, "lcc_single_slot_pane"):
            self.lcc_single_slot_pane.setVisible(compare.lcc_single_visible)
            self.lcc_compare_pane.setVisible(compare.lcc_compare_visible)
            if compare.lcc_empty_state_visible:
                self.lcc_empty_state_label.setVisible(True)

    def _apply_collapse_panels(self, collapse: CollapsePanelsPlan) -> None:
        self._apply_collapse_panel(
            collapse.kpi,
            chrome_button=getattr(self, "kpi_collapse_button", None),
            title=getattr(self, "kpi_panel_title", None),
            content=getattr(self, "kpi_table_view", None),
        )
        self._apply_collapse_panel(
            collapse.lcc_whatif,
            chrome_button=getattr(self, "lcc_whatif_collapse_button", None),
            title=getattr(self, "lcc_whatif_bar_title", None),
            content=getattr(self, "lcc_whatif_content", None),
        )
        self._apply_meekoppel_collapse(collapse.meekoppel)

    @staticmethod
    def _apply_collapse_panel(
        panel: CollapsePanelPlan | None,
        *,
        chrome_button,
        title,
        content,
    ) -> None:
        if chrome_button is None:
            return
        if panel is None:
            chrome_button.setVisible(False)
            if title is not None:
                title.setVisible(False)
            if content is not None:
                content.setVisible(True)
            return
        chrome_button.setVisible(panel.chrome_visible)
        if title is not None:
            title.setVisible(panel.chrome_visible)
        if content is not None:
            content.setVisible(panel.content_visible)
        chrome_button.setText(panel.collapse_glyph)
        chrome_button.setEnabled(panel.chrome_enabled)

    def _apply_meekoppel_collapse(self, panel: MeekoppelCollapsePlan | None) -> None:
        if not hasattr(self, "meekoppel_collapse_button"):
            return
        if panel is None:
            self.meekoppel_collapse_button.setVisible(False)
            self.meekoppel_content.setVisible(False)
            return
        if panel.ensure_whatif_if_expanding:
            self._ensure_whatif_for_meekoppel()
        self.meekoppel_collapse_button.setVisible(panel.chrome_visible)
        self.meekoppel_content.setVisible(panel.content_visible)
        self.meekoppel_collapse_button.setText(panel.collapse_glyph)
        self.meekoppel_collapse_button.setEnabled(panel.chrome_enabled)

    def _seed_planning_overlay_from_import(self, project: object) -> None:
        import_settings = getattr(project, "import_settings", None)
        if import_settings is None:
            return
        overlay = PlanningOverlayState.from_import_settings(import_settings)
        if overlay.active:
            self.workspace_state.set_planning_overlay(overlay)

    def _on_state_project_changed(self, project: object) -> None:
        self._refresh_contribution_year_combo(project)
        if project is None:
            self._set_pbs_source_model(None, show_totals=False)
            self._pbs_scope_id = None
            self._clear_compare_slots()
            self._clear_detail_zone()
            self._project_total_presentation = None
            self._last_workspace_snapshot_for_split_depth = None
            self._last_lcc_render_snapshot = None
            self._render_index.on_project_changed()
            if self._state.last_run is not None:
                self._state.set_last_run(None)
            self._refresh_kpi_table_view()
            self._update_run_buttons_enabled()
            self._update_run_button_label()
            return
        self._pbs_scope_id = None
        self._last_workspace_snapshot_for_split_depth = None
        self._render_index.on_workspace_state_reset()
        self._clear_compare_slots()
        if not self._state.take_preserve_workspace_ui():
            self.workspace_state.reset_for_new_project()
        self._seed_planning_overlay_from_import(project)
        self._sync_pbs_tree_for_state()
        self._rerender_detail_for_current_scope()
        self._refresh_kpi_table_view()
        self._update_run_buttons_enabled()
        self._update_report_button_enabled()
        self._update_scope_status_label()

    def _on_state_run_changed(self, run_result: object) -> None:
        self._sync_pbs_tree_for_state()
        self._rerender_detail_for_current_scope()
        self._refresh_kpi_table_view()
        self._update_report_button_enabled()
        if isinstance(run_result, RunResult) and run_result.error is not None:
            self._show_run_error(run_result.error)

    def _sync_pbs_tree_for_state(self) -> None:
        session = self._project_session()
        run_result = self._state.last_run
        if session is None:
            self._set_pbs_source_model(None, show_totals=False)
            return
        if isinstance(run_result, RunResult) and run_result.status == "done" and run_result.pbs_rows:
            roots = build_pbs_tree(list(run_result.pbs_rows))
            self._set_pbs_source_model(PBSResultsTreeModel(roots), show_totals=True)
            return
        if wss.has_functies(session):
            self._set_pbs_source_model(
                wss.build_navigation_tree_model_for_session(session),
                show_totals=False,
            )
            return
        roots = wss.build_pbs_structure_tree_for_session(session)
        self._set_pbs_source_model(PBSResultsTreeModel(roots, show_totals=False), show_totals=False)

    def _pbs_scope_from_tree_index(self, source_model, source_index: QModelIndex) -> str | None:
        if isinstance(source_model, RcmNavigationTreeModel):
            return source_model.scope_pbs_id_for_index(source_index)
        if isinstance(source_model, PBSResultsTreeModel):
            return source_model.pbs_id_for_index(source_index)
        return None

    def _set_pbs_source_model(
        self,
        model: PBSResultsTreeModel | RcmNavigationTreeModel | None,
        *,
        show_totals: bool,
    ) -> None:
        self._pbs_source_model = model
        self.pbs_proxy.setSourceModel(model)
        if model is not None:
            self.pbs_tree_view.setHeader(self.pbs_tree_view.header())
            self.pbs_tree_view.header().setSectionResizeMode(QHeaderView.Interactive)
            self.pbs_tree_view.header().setStretchLastSection(True)
        self._on_pbs_filter_text_changed(self.pbs_filter_input.text())

    def _project_session(self) -> ProjectSession | None:
        return self._state.project_session

    def _selected_fm_id_from_table(self) -> str | None:
        model = self.fm_table_view.model()
        sel_model = self.fm_table_view.selectionModel()
        if model is None or sel_model is None:
            return None
        indexes = sel_model.selectedRows()
        if not indexes:
            return None
        fm_id = model.data(indexes[0], RAW_ROLE)
        return str(fm_id) if fm_id is not None else None

    def _render_fm_rows(self, fm_rows) -> None:
        prior_fm_id = self._selected_fm_id_from_table()
        model = FMResultsTableModel(list(fm_rows), self.fm_table_view)
        self._fm_table_proxy.setSourceModel(model)
        self.detail_empty_state_label.setVisible(model.rowCount() == 0)
        restore_row: int | None = None
        if prior_fm_id is not None:
            for row in range(self._fm_table_proxy.rowCount()):
                if self._fm_table_proxy.data(
                    self._fm_table_proxy.index(row, 0), RAW_ROLE
                ) == prior_fm_id:
                    restore_row = row
                    break
        if restore_row is not None:
            self.fm_table_view.selectRow(restore_row)
        else:
            self._refresh_fm_inspector(None)

    def _on_fm_table_selection_changed(
        self,
        selected: QItemSelection,
        deselected: QItemSelection,
    ) -> None:
        del selected, deselected
        if self.workspace_state.snapshot().modus != MODE_FM_DETAIL:
            return
        model = self.fm_table_view.model()
        if model is None:
            self._refresh_fm_inspector(None)
            return
        sel_model = self.fm_table_view.selectionModel()
        if sel_model is None:
            self._refresh_fm_inspector(None)
            return
        indexes = sel_model.selectedRows()
        if not indexes:
            self._refresh_fm_inspector(None)
            return
        fm_id = model.data(indexes[0], RAW_ROLE)
        self._refresh_fm_inspector(str(fm_id) if fm_id is not None else None)

    def _commit_active_grid_edits(self) -> bool:
        host = self._editing_host
        grid_svc = host.grid_service()
        if grid_svc is None or not grid_svc.is_active():
            return True
        if not grid_svc.is_dirty() or grid_svc.error_count() != 0:
            return grid_svc.error_count() == 0
        path = self.path_input.text().strip() or None
        result = host.commit_grid_edits(path=path, save_to_disk=bool(path))
        if not result.ok:
            return False
        if result.project is not None:
            self._state.set_last_project(result.project, path=path)
        if result.run_result is not None:
            self._state.set_last_run(result.run_result)
        grid_svc.mark_saved()
        return True

    def _open_batch_faalwijzen_grid(self) -> None:
        session = self._project_session()
        if session is None:
            QMessageBox.information(
                self,
                messages.WORKSPACE_MENU_FAALWIJZEN_BATCH,
                messages.WORKSPACE_FM_INSPECTOR_INPUTS_MISSING,
            )
            return
        project = wss.editing_project(session)
        host = self._editing_host
        grid_svc = host.ensure_grid(project)
        prev_save = host.swap_save_handler(self._commit_active_grid_edits)
        dialog = QDialog(self)
        dialog.setWindowTitle(messages.WORKSPACE_MENU_FAALWIJZEN_BATCH)
        dialog.resize(960, 520)
        layout = QVBoxLayout(dialog)
        panel = ValidateFaalwijzenPanel()
        panel.attach(grid_svc, project)
        layout.addWidget(panel)
        close_btn = QPushButton("Sluiten")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.exec()
        host.set_save_handler(prev_save)
        if grid_svc.is_dirty() and grid_svc.error_count() == 0:
            self._commit_active_grid_edits()

    def _on_fm_table_double_clicked(self, index: QModelIndex) -> None:
        if self.workspace_state.snapshot().modus != MODE_FM_DETAIL:
            return
        session = self._project_session()
        if session is None:
            QMessageBox.information(
                self,
                messages.FM_EDITOR_VALIDATION_TITLE,
                messages.FM_EDITOR_NO_PROJECT,
            )
            return
        model = self.fm_table_view.model()
        if model is None:
            return
        src_index = index
        proxy = self._fm_table_proxy
        if model is proxy:
            src_index = proxy.mapToSource(index)
            src_model = proxy.sourceModel()
        else:
            src_model = model
        if src_model is None:
            return
        fm_id = src_model.data(src_index, RAW_ROLE)
        if not fm_id:
            return
        fm_key = str(fm_id)
        if not wss.fm_exists(session, fm_key):
            QMessageBox.warning(
                self,
                messages.FM_EDITOR_VALIDATION_TITLE,
                messages.WORKSPACE_FM_INSPECTOR_INPUTS_MISSING,
            )
            return
        project = wss.editing_project(session)
        host = self._editing_host
        prev_save = host.swap_save_handler(self._commit_active_grid_edits)
        try:
            if resolve_grid_dirty_before_editor(self, host) == "cancel":
                return
            path = self.path_input.text().strip() or None
            grid_svc = host.grid_service()
            shared_session = None
            if grid_svc is not None and grid_svc.is_active():
                shared_session = grid_svc.editing_session
            dialog = FmEditorDialog(
                self,
                project=project,
                fm_id=fm_key,
                project_path=path,
                save_to_disk=bool(path),
                editing_session=shared_session,
            )
            if dialog.exec() != QDialog.DialogCode.Accepted or dialog.commit_result is None:
                return
            result = dialog.commit_result
            if result.project is not None:
                self._state.set_last_project(
                    result.project, path=path, preserve_workspace_ui=True
                )
            if result.run_result is not None:
                self._state.set_last_run(result.run_result)
                self._project_total_presentation = self._load_presentation_from_disk()
                self._render_index.on_workspace_state_reset()
                self._rerender_detail_for_current_scope()
                self._refresh_fm_inspector(str(fm_id))
        finally:
            host.set_save_handler(prev_save)

    def _selected_leaf_pbs_id_for_create(self) -> str | None:
        pbs_ids = self._pbs_selected_ids_from_tree()
        if len(pbs_ids) != 1:
            return None
        pbs_id = next(iter(pbs_ids))
        session = self._project_session()
        if session is None:
            return None
        project = wss.editing_project(session)
        from rcm_desktop.adapter.fm_create_service import is_leaf_pbs

        if not is_leaf_pbs(project, pbs_id):
            return None
        return pbs_id

    def _sync_new_fm_button_enabled(self) -> None:
        if not hasattr(self, "new_fm_button"):
            return
        leaf = self._selected_leaf_pbs_id_for_create()
        has_project = self._project_session() is not None
        self.new_fm_button.setEnabled(has_project and leaf is not None)

    def _on_new_fm_clicked(self) -> None:
        if self.workspace_state.snapshot().modus != MODE_FM_DETAIL:
            return
        session = self._project_session()
        if session is None:
            QMessageBox.information(
                self,
                messages.FM_EDITOR_VALIDATION_TITLE,
                messages.FM_EDITOR_NO_PROJECT,
            )
            return
        pbs_id = self._selected_leaf_pbs_id_for_create()
        if pbs_id is None:
            QMessageBox.information(
                self,
                messages.FM_EDITOR_VALIDATION_TITLE,
                messages.FM_EDITOR_NEW_FM_NO_LEAF_PBS,
            )
            return
        project = wss.editing_project(session)
        host = self._editing_host
        prev_save = host.swap_save_handler(self._commit_active_grid_edits)
        try:
            if resolve_grid_dirty_before_editor(self, host) == "cancel":
                return
            path = self.path_input.text().strip() or None
            grid_svc = host.grid_service()
            shared_session = None
            if grid_svc is not None and grid_svc.is_active():
                shared_session = grid_svc.editing_session
            dialog = FmEditorDialog(
                self,
                project=project,
                create_pbs_id=pbs_id,
                project_path=path,
                save_to_disk=bool(path),
                editing_session=shared_session,
            )
            if dialog.exec() != QDialog.DialogCode.Accepted or dialog.commit_result is None:
                return
            result = dialog.commit_result
            new_fm_id = dialog._fm_id
            if result.project is not None:
                self._state.set_last_project(
                    result.project, path=path, preserve_workspace_ui=True
                )
            if result.run_result is not None:
                self._state.set_last_run(result.run_result)
                self._project_total_presentation = self._load_presentation_from_disk()
                self._render_index.on_workspace_state_reset()
                self._rerender_detail_for_current_scope()
                self._select_fm_in_table(new_fm_id)
                self._refresh_fm_inspector(new_fm_id)
        finally:
            host.set_save_handler(prev_save)

    def _select_fm_in_table(self, fm_id: str) -> None:
        model = self.fm_table_view.model()
        if model is None:
            return
        src_model = model.sourceModel() if model is self._fm_table_proxy else model
        if src_model is None:
            return
        target = str(fm_id)
        for row in range(src_model.rowCount()):
            idx = src_model.index(row, 0)
            if str(src_model.data(idx, RAW_ROLE) or "") == target:
                proxy_idx = (
                    self._fm_table_proxy.mapFromSource(idx)
                    if model is self._fm_table_proxy
                    else idx
                )
                self.fm_table_view.selectRow(proxy_idx.row())
                break

    def _open_model_settings(self) -> None:
        session = self._project_session()
        if session is None:
            QMessageBox.information(
                self,
                messages.MODEL_SETTINGS_BUTTON_LABEL,
                messages.MODEL_SETTINGS_NO_PROJECT,
            )
            return
        project = wss.editing_project(session)
        host = self._editing_host
        prev_save = host.swap_save_handler(self._commit_active_grid_edits)
        try:
            if resolve_grid_dirty_before_editor(self, host) == "cancel":
                return
            path = self.path_input.text().strip() or None
            baseline_mtime = None
            if path:
                from rcm_desktop.adapter.save_service import current_mtime_ns
                from pathlib import Path as PathCls

                baseline_mtime = current_mtime_ns(PathCls(path))
            dialog = ModelSettingsDialog(
                self,
                project=project,
                project_path=path,
                save_to_disk=bool(path),
                baseline_mtime_ns=baseline_mtime,
            )
            if dialog.exec() != QDialog.DialogCode.Accepted or dialog.commit_result is None:
                return
            result = dialog.commit_result
            if result.project is not None:
                self._state.set_last_project(
                    result.project, path=path, preserve_workspace_ui=True
                )
            if result.run_result is not None:
                self._state.set_last_run(result.run_result)
                self._project_total_presentation = self._load_presentation_from_disk()
                self._render_index.on_workspace_state_reset()
                self._rerender_detail_for_current_scope()
                self.validate_summary_label.setText("")
            elif result.requires_rerun:
                self._state.set_last_run(None)
                self.validate_summary_label.setText(messages.MODEL_SETTINGS_RERUN_REQUIRED)
                self._refresh_kpi_table_view()
                self._update_run_buttons_enabled()
        finally:
            host.set_save_handler(prev_save)

    def _fm_core_result_for_id(self, fm_id: str):
        run = self._state.last_run
        if run is None or run.status != "done":
            return None
        for fmr in run.fm_core_results:
            if fmr.fm_id == fm_id:
                return fmr
        return None

    def _refresh_fm_inspector(self, fm_id: str | None) -> None:
        if not hasattr(self, "fm_inspector_panel"):
            return
        if fm_id is None:
            self.fm_inspector_empty_label.setVisible(True)
            self.fm_inspector_panel.setVisible(False)
            return
        session = self._project_session()
        fmr = self._fm_core_result_for_id(fm_id)
        if session is None or fmr is None:
            self.fm_inspector_empty_label.setVisible(True)
            self.fm_inspector_panel.setVisible(False)
            return
        view = wss.build_fm_verification_for_session(session, fmr)
        self._apply_fm_inspector_view(view)

    def _apply_fm_inspector_view(self, view: FMVerificationView) -> None:
        self.fm_inspector_empty_label.setVisible(False)
        self.fm_inspector_panel.setVisible(True)
        self.fm_inspector_identity_label.setText(
            f"{view.fm_id} — {view.faalwijze_omschrijving}\n"
            f"{view.pbs_id} — {view.bouwdeel_naam}"
        )
        lc = view.lifecycle
        lines = [
            f"{messages.WORKSPACE_FM_INSPECTOR_FAALMOMENTEN}: "
            f"{format_int(int(round(lc.expected_failures)))}",
            f"{messages.WORKSPACE_FM_INSPECTOR_RAW_DOWNTIME}: "
            f"{format_float(lc.expected_raw_downtime_hr)}",
            f"{messages.WORKSPACE_FM_INSPECTOR_DETECTION_DELAY}: "
            f"{format_float(lc.expected_detection_delay_hr)}",
            f"{messages.WORKSPACE_FM_INSPECTOR_PM_DOWNTIME}: "
            f"{format_float(lc.expected_pm_downtime_hr)}",
            f"{messages.WORKSPACE_FM_INSPECTOR_TOTAL_DOWNTIME}: "
            f"{format_float(lc.expected_total_downtime_hr)}",
            f"{messages.WORKSPACE_FM_INSPECTOR_CM_COST}: "
            f"{format_eur(lc.expected_cm_cost_eur)}",
            f"{messages.WORKSPACE_FM_INSPECTOR_PM_COST}: "
            f"{format_eur(lc.pm_cost_eur)}",
            f"{messages.WORKSPACE_FM_INSPECTOR_TOTAL_COST}: "
            f"{format_eur(lc.total_cost_eur)}",
        ]
        if lc.effect_bijdragen:
            effects = ", ".join(
                f"{kid}: {format_float(v)}" for kid, v in lc.effect_bijdragen
            )
            lines.append(f"{messages.WORKSPACE_FM_INSPECTOR_EFFECTS}: {effects}")
        self.fm_inspector_lifecycle_label.setText("\n".join(lines))
        if view.fm_input_hash:
            self.fm_inspector_hash_label.setText(
                f"{messages.WORKSPACE_FM_INSPECTOR_HASH_PREFIX} {view.fm_input_hash}"
            )
        else:
            self.fm_inspector_hash_label.setText(
                messages.WORKSPACE_FM_INSPECTOR_HASH_MISSING
            )
        if view.profile_missing:
            self.fm_inspector_profile_missing_label.setText(
                messages.WORKSPACE_FM_INSPECTOR_PROFILE_MISSING
            )
            self.fm_inspector_profile_missing_label.setVisible(True)
            self.fm_inspector_year_table_view.setVisible(False)
            self.fm_inspector_year_table_view.setModel(None)
            reconcile_prefix = messages.WORKSPACE_FM_INSPECTOR_RECONCILE_WARN
        else:
            self.fm_inspector_profile_missing_label.setVisible(False)
            self.fm_inspector_year_table_view.setVisible(True)
            year_model = FMVerificationYearTableModel(view.year_rows)
            self.fm_inspector_year_table_view.setModel(year_model)
            reconcile_prefix = (
                messages.WORKSPACE_FM_INSPECTOR_RECONCILE_OK
                if view.reconcile_ok
                else messages.WORKSPACE_FM_INSPECTOR_RECONCILE_WARN
            )
        notes = "; ".join(view.reconcile_notes)
        self.fm_inspector_reconcile_label.setText(f"{reconcile_prefix} — {notes}")

    def _render_lcc_view(
        self,
        session: ProjectSession,
        lcc_view,
        snapshot: WorkspaceStateSnapshot,
    ) -> None:
        """LCC-planning met type-filters, overlay en jaardetail (slice 28)."""
        scope = lcc_view.render_scope
        curve = lcc_view.curve
        self._last_lcc_render_snapshot = snapshot
        if curve is None or not curve.display_buckets:
            self.lcc_chart_widget.set_buckets(())
            self.lcc_chart_widget.set_selected_year(None)
            self.lcc_table_view.setModel(None)
            self._lcc_detail_model.set_view(None)
            self.lcc_empty_state_label.setVisible(True)
            self.lcc_year_summary_label.setText("")
            return
        run_result = session.run
        assert run_result is not None
        if scope == "detail_only":
            self.lcc_chart_widget.set_selected_year(snapshot.lcc_calendar_year)
            self._sync_lcc_chrome(snapshot)
            self._render_lcc_year_detail(session, run_result, snapshot, planning_curve=curve)
            return
        buckets = tuple(curve.display_buckets)
        self.lcc_chart_widget.set_buckets(buckets)
        self.lcc_chart_widget.set_selected_year(snapshot.lcc_calendar_year)
        self._lcc_table_model = LCCYearTableModel(buckets)
        self.lcc_table_view.setModel(self._lcc_table_model)
        self.lcc_empty_state_label.setVisible(False)
        self._sync_lcc_chrome(snapshot)
        self._render_lcc_year_detail(session, run_result, snapshot, planning_curve=curve)

    def _sync_lcc_chrome(self, snapshot: WorkspaceStateSnapshot) -> None:
        session = self._project_session()
        overlay = snapshot.planning_overlay
        active = overlay.active
        year_selected = snapshot.lcc_calendar_year is not None
        self.lcc_whatif_button.setChecked(active)
        self.lcc_reset_overlay_button.setEnabled(active)
        self.lcc_bulk_rev_passive_button.setEnabled(active and session is not None)
        self.lcc_cm_preset_button.setEnabled(active and session is not None)
        if session is not None and wss.overlay_all_rev_passive(session, overlay):
            self.lcc_bulk_rev_passive_button.setText(messages.WORKSPACE_LCC_BULK_REV_ACTIVE)
        else:
            self.lcc_bulk_rev_passive_button.setText(messages.WORKSPACE_LCC_BULK_REV_PASSIVE)
        show_detail_tb = active and year_selected
        self.lcc_detail_toolbar.setVisible(show_detail_tb)
        self.lcc_shift_button.setEnabled(show_detail_tb)
        self.lcc_shift_spin.setEnabled(show_detail_tb)
        self.lcc_select_rev_button.setEnabled(show_detail_tb)
        if self._lcc_passive_kept_after_run and overlay.disabled_pm_ids:
            self.lcc_overlay_status_label.setText(
                messages.WORKSPACE_LCC_AFTER_RECOMPUTE_PASSIVE_KEPT
            )
            self.lcc_overlay_status_label.setVisible(True)
        elif active and overlay.change_count() > 0:
            self.lcc_overlay_status_label.setText(
                messages.WORKSPACE_LCC_WHAT_IF_ACTIVE.format(count=overlay.change_count())
            )
            self.lcc_overlay_status_label.setVisible(True)
        elif active:
            note = messages.WORKSPACE_LCC_WHAT_IF_PRESENTATION_NOTE
            if overlay.disabled_pm_ids:
                note = f"{note} {messages.WORKSPACE_LCC_CM_AFTER_RECOMPUTE}"
            self.lcc_overlay_status_label.setText(note)
            self.lcc_overlay_status_label.setVisible(True)
        else:
            self.lcc_overlay_status_label.setVisible(False)
        if snapshot.modus == MODE_LCC:
            self._sync_meekoppel_panel(snapshot)

    def _meekoppel_current_anchor(self) -> str:
        return "later" if self.meekoppel_anchor_later.isChecked() else "earlier"

    def _selected_meekoppel_pbs_ids(self) -> frozenset[str]:
        return self._pbs_selected_ids_from_tree()

    def _ensure_whatif_for_meekoppel(self) -> None:
        overlay = self.workspace_state.snapshot().planning_overlay
        if overlay.active:
            return
        self.workspace_state.set_planning_overlay(overlay.begin_what_if())
        blocker = self.lcc_whatif_button.blockSignals(True)
        try:
            self.lcc_whatif_button.setChecked(True)
        finally:
            self.lcc_whatif_button.blockSignals(blocker)

    def _clear_meekoppel_preview_gate(self) -> None:
        self._meekoppel_preview_gate = None

    def _sync_meekoppel_panel(self, snapshot: WorkspaceStateSnapshot) -> None:
        session = self._project_session()
        selected_pbs_ids = self._selected_meekoppel_pbs_ids()
        panel = sync_meekoppel_panel(
            session,
            snapshot,
            window_years=int(self.meekoppel_window_spin.value()),
            preview_gate=self._meekoppel_preview_gate,
            selected_pbs_ids=selected_pbs_ids or None,
            current_anchor=self._meekoppel_current_anchor(),  # type: ignore[arg-type]
        )
        self.meekoppel_whatif_hint_label.setVisible(panel.show_whatif_hint)
        self.meekoppel_window_spin.setEnabled(panel.window_spin_enabled)
        self.meekoppel_anchor_earlier.setEnabled(panel.window_spin_enabled)
        self.meekoppel_anchor_later.setEnabled(panel.window_spin_enabled)
        self.meekoppel_table_view.setVisible(panel.table_visible)
        self.meekoppel_preview_button.setEnabled(panel.preview_enabled)
        self.meekoppel_apply_button.setEnabled(panel.apply_enabled)
        self._meekoppel_location_groups = panel.location_groups
        self._meekoppel_table_model.set_panel_rows(
            panel.rows, columns=panel.columns
        )
        if panel.selection_summary_text:
            self.meekoppel_selection_summary_label.setText(panel.selection_summary_text)
            self.meekoppel_selection_summary_label.setVisible(True)
        else:
            self.meekoppel_selection_summary_label.setVisible(False)
        if panel.empty_label_text:
            self.meekoppel_empty_label.setText(panel.empty_label_text)
            self.meekoppel_empty_label.setVisible(True)
        else:
            self.meekoppel_empty_label.setVisible(False)

    def _on_meekoppel_anchor_changed(self, _button) -> None:
        snapshot = self.workspace_state.snapshot()
        if snapshot.modus == MODE_LCC:
            self._sync_meekoppel_panel(snapshot)

    def _on_meekoppel_window_changed(self, _value: int) -> None:
        snapshot = self.workspace_state.snapshot()
        if snapshot.modus == MODE_LCC:
            self._sync_meekoppel_panel(snapshot)

    def _selected_meekoppel_location_group(self) -> MeekoppelLocationGroup | None:
        sm = self.meekoppel_table_view.selectionModel()
        if sm is None or not sm.hasSelection():
            return None
        panel_row = self._meekoppel_table_model.row_at(sm.currentIndex().row())
        if panel_row is None:
            return None
        for group in self._meekoppel_location_groups:
            if group.pbs_id == panel_row.pbs_id:
                return group
        return None

    def _on_meekoppel_preview(self) -> None:
        session = self._project_session()
        if session is None:
            return
        self._ensure_whatif_for_meekoppel()
        overlay = self.workspace_state.snapshot().planning_overlay
        pbs_ids = self._selected_meekoppel_pbs_ids()
        anchor = self._meekoppel_current_anchor()
        if meekoppel_workflow_v2_enabled():
            if not pbs_ids:
                QMessageBox.warning(
                    self,
                    messages.LTAP_ERROR_DIALOG_TITLE,
                    messages.WORKSPACE_MEEKOPPEL_SELECT_PBS,
                )
                return
            dialog = MeekoppelPreviewDialog(
                self,
                session=session,
                overlay=overlay,
                pbs_ids=pbs_ids,
                anchor=anchor,  # type: ignore[arg-type]
                location_group=self._selected_meekoppel_location_group(),
                workflow=self._meekoppel_workflow,
            )
            dialog.exec()
            result = dialog.result_payload()
            if result.preview is None:
                return
            self._meekoppel_preview_gate = MeekoppelPreviewGate(
                pbs_ids=pbs_ids,
                anchor=anchor,  # type: ignore[arg-type]
            )
            if result.accepted and result.scope_kind is not None:
                apply_result = self._meekoppel_workflow.apply(
                    session=session,
                    overlay=overlay,
                    pbs_ids=pbs_ids,
                    anchor=anchor,  # type: ignore[arg-type]
                    scope_kind=result.scope_kind,
                    location_group=self._selected_meekoppel_location_group()
                    if result.scope_kind == "location_row"
                    else None,
                    checked_pm_ids=result.checked_pm_ids,
                )
                if apply_result.status == "ok":
                    self.workspace_state.set_planning_overlay(apply_result.overlay)
                elif apply_result.user_message:
                    QMessageBox.critical(
                        self,
                        messages.LTAP_ERROR_DIALOG_TITLE,
                        apply_result.user_message,
                    )
            self._sync_meekoppel_panel(self.workspace_state.snapshot())
            return
        else:
            if not pbs_ids:
                QMessageBox.warning(
                    self,
                    messages.LTAP_ERROR_DIALOG_TITLE,
                    messages.WORKSPACE_MEEKOPPEL_SELECT_PBS,
                )
                return
            prev = preview_meekoppel(
                session,
                overlay,
                pbs_ids,
                anchor=anchor,  # type: ignore[arg-type]
            )
        if prev.blocked_reason:
            QMessageBox.information(
                self,
                messages.WORKSPACE_MEEKOPPEL_PREVIEW_TITLE,
                messages.WORKSPACE_MEEKOPPEL_PREVIEW_BLOCKED.format(reason=prev.blocked_reason),
            )
            return
        project = session.loaded.core()
        modeljaar = int(project.config.modeljaar)
        tasks = collect_rev_tasks_for_pbs_selection(project, pbs_ids)
        moves_text = format_meekoppel_preview_moves_text(
            project,
            overlay,
            modeljaar,
            prev,
            tasks,
        )
        pbs_footnote = messages.WORKSPACE_MEEKOPPEL_PREVIEW_PBS_FOOTNOTE.format(
            pbs_id=prev.pbs_id
        )
        QMessageBox.information(
            self,
            messages.WORKSPACE_MEEKOPPEL_PREVIEW_TITLE,
            messages.WORKSPACE_MEEKOPPEL_PREVIEW_BODY.format(
                location=prev.path_label,
                target=prev.target_year,
                target_cal=due_calendar_year(modeljaar, prev.target_year),
                moves=moves_text,
                pbs_footnote=pbs_footnote,
            ),
        )
        self._meekoppel_preview_gate = MeekoppelPreviewGate(
            pbs_ids=pbs_ids,
            anchor=anchor,  # type: ignore[arg-type]
        )
        self._sync_meekoppel_panel(self.workspace_state.snapshot())

    def _on_meekoppel_apply(self) -> None:
        session = self._project_session()
        if session is None:
            return
        self._ensure_whatif_for_meekoppel()
        overlay = self.workspace_state.snapshot().planning_overlay
        pbs_ids = self._selected_meekoppel_pbs_ids()
        anchor = self._meekoppel_current_anchor()
        if meekoppel_workflow_v2_enabled():
            workflow_result = self._meekoppel_workflow.apply(
                session=session,
                overlay=overlay,
                pbs_ids=pbs_ids,
                anchor=anchor,  # type: ignore[arg-type]
                scope_kind="pbs_selection",
            )
            if workflow_result.status == "validation":
                QMessageBox.warning(
                    self,
                    messages.LTAP_ERROR_DIALOG_TITLE,
                    workflow_result.user_message,
                )
                return
            if workflow_result.status != "ok":
                QMessageBox.critical(
                    self,
                    messages.LTAP_ERROR_DIALOG_TITLE,
                    workflow_result.user_message,
                )
                return
            self.workspace_state.set_planning_overlay(workflow_result.overlay)
        else:
            if not pbs_ids:
                QMessageBox.warning(
                    self,
                    messages.LTAP_ERROR_DIALOG_TITLE,
                    messages.WORKSPACE_MEEKOPPEL_SELECT_PBS,
                )
                return
            result = apply_meekoppel(
                session,
                overlay,
                pbs_ids,
                anchor=anchor,  # type: ignore[arg-type]
            )
            if result.error:
                QMessageBox.critical(self, messages.LTAP_ERROR_DIALOG_TITLE, result.error)
                return
            self.workspace_state.set_planning_overlay(result.overlay)
        self._sync_meekoppel_panel(self.workspace_state.snapshot())

    def _render_lcc_year_detail(
        self,
        session: ProjectSession,
        run_result: RunResult,
        snapshot: WorkspaceStateSnapshot,
        *,
        planning_curve=None,
    ) -> None:
        year = snapshot.lcc_calendar_year
        if year is None:
            self.lcc_year_summary_label.setText("")
            self._lcc_detail_model.set_view(None)
            return
        detail = wss.build_lcc_year_detail_for_session(
            session,
            run_result,
            year,
            scope_id=snapshot.scope_id,
            overlay=snapshot.planning_overlay,
            type_filters=snapshot.lcc_filters,
            planning_curve=planning_curve,
        )
        if detail is None:
            self.lcc_year_summary_label.setText(messages.WORKSPACE_LCC_DETAIL_EMPTY_YEAR)
            self._lcc_detail_model.set_view(None)
            return
        o = snapshot.planning_overlay
        show_whatif_delta = (
            o.active
            and detail.overlay_preventief_eur is not None
            and (
                abs(detail.overlay_preventief_eur - detail.baseline_preventief_eur) > 1.0
                or bool(o.disabled_pm_ids)
                or any(abs(y) > 1e-12 for _, y in o.anchor_years)
            )
        )
        if show_whatif_delta:
            delta = detail.overlay_preventief_eur - detail.baseline_preventief_eur
            self.lcc_year_summary_label.setText(
                messages.WORKSPACE_LCC_YEAR_SUMMARY_WHATIF.format(
                    year=year,
                    base=detail.baseline_preventief_eur,
                    overlay=detail.overlay_preventief_eur,
                    delta=delta,
                )
            )
        else:
            self.lcc_year_summary_label.setText(
                messages.WORKSPACE_LCC_YEAR_SUMMARY.format(
                    year=year,
                    corr=detail.baseline_correctief_eur,
                    prev=detail.baseline_preventief_eur,
                )
            )
        self._lcc_detail_model.set_view(
            detail, passive_column=snapshot.planning_overlay.active
        )

    def _lcc_filters_from_ui(self) -> LCCTypeFilterSet:
        c = self._lcc_filter_checks
        return LCCTypeFilterSet(
            cm=c["cm"].isChecked(),
            rev=c["rev"].isChecked(),
            in_task=c["in_task"].isChecked(),
            tst=c["tst"].isChecked(),
            svo=c["svo"].isChecked(),
            wet=c["wet"].isChecked(),
        )

    def _sync_lcc_filter_checks(self, filters: LCCTypeFilterSet) -> None:
        mapping = {
            "cm": filters.cm,
            "rev": filters.rev,
            "in_task": filters.in_task,
            "tst": filters.tst,
            "svo": filters.svo,
            "wet": filters.wet,
        }
        for key, checked in mapping.items():
            box = self._lcc_filter_checks[key]
            if box.isChecked() != checked:
                blocker = box.blockSignals(True)
                box.setChecked(checked)
                box.blockSignals(blocker)

    def _on_lcc_filter_toggled(self, _checked: bool = False) -> None:
        self.workspace_state.set_lcc_filters(self._lcc_filters_from_ui())

    def _on_lcc_year_clicked(self, calendar_year: int) -> None:
        self.workspace_state.set_lcc_calendar_year(calendar_year)

    def _on_lcc_show_all_years(self) -> None:
        self.workspace_state.set_lcc_calendar_year(None)

    def _on_lcc_whatif_toggled(self, checked: bool) -> None:
        overlay = self.workspace_state.snapshot().planning_overlay
        if checked:
            self.workspace_state.set_planning_overlay(overlay.begin_what_if())
        else:
            self._lcc_passive_kept_after_run = False
            self._clear_meekoppel_preview_gate()
            self.workspace_state.set_planning_overlay(overlay.reset_overlay())

    def _on_lcc_reset_overlay(self) -> None:
        self._lcc_passive_kept_after_run = False
        self._clear_meekoppel_preview_gate()
        self.workspace_state.set_planning_overlay(PlanningOverlayState.inactive())
        self.lcc_whatif_button.setChecked(False)

    def _on_lcc_select_rev_in_year(self) -> None:
        view = self._lcc_detail_model.detail_view()
        if view is None or view.cm_only:
            return
        row_indices = rev_row_indices(view)
        selection_model = self.lcc_detail_table_view.selectionModel()
        if selection_model is None:
            return
        selection_model.clearSelection()
        if not row_indices:
            return
        last_col = max(0, self._lcc_detail_model.columnCount() - 1)
        item_selection = QItemSelection()
        for row in row_indices:
            top_left = self._lcc_detail_model.index(row, 0)
            bottom_right = self._lcc_detail_model.index(row, last_col)
            item_selection.select(top_left, bottom_right)
        selection_model.select(item_selection, QItemSelectionModel.SelectionFlag.Select)

    def _on_kpi_collapse_toggled(self) -> None:
        snapshot = self.workspace_state.snapshot()
        if snapshot.modus != MODE_LCC:
            return
        self.workspace_state.set_kpi_collapsed_in_lcc(not snapshot.kpi_collapsed_in_lcc)

    def _on_lcc_whatif_collapse_toggled(self) -> None:
        snapshot = self.workspace_state.snapshot()
        if snapshot.modus != MODE_LCC:
            return
        self.workspace_state.set_lcc_whatif_collapsed_in_lcc(
            not snapshot.lcc_whatif_collapsed_in_lcc
        )

    def _on_meekoppel_collapse_toggled(self) -> None:
        snapshot = self.workspace_state.snapshot()
        if snapshot.modus != MODE_LCC:
            return
        self.workspace_state.set_meekoppel_collapsed_in_lcc(
            not snapshot.meekoppel_collapsed_in_lcc
        )

    def _on_lcc_bulk_rev_toggle(self) -> None:
        session = self._project_session()
        if session is None:
            return
        overlay = self.workspace_state.snapshot().planning_overlay
        if not overlay.active:
            overlay = overlay.begin_what_if()
        overlay = wss.toggle_bulk_rev_overlay(session, overlay)
        self.workspace_state.set_planning_overlay(overlay)

    def _on_lcc_cm_policy_preset(self) -> None:
        session = self._project_session()
        if session is None:
            return
        overlay = self.workspace_state.snapshot().planning_overlay
        if not overlay.active:
            overlay = overlay.begin_what_if()
        self.workspace_state.set_planning_overlay(
            wss.apply_cm_preset_for_session(session, overlay)
        )

    def _on_lcc_shift_selected(self) -> None:
        session = self._project_session()
        if session is None:
            return
        overlay = self.workspace_state.snapshot().planning_overlay
        if not overlay.active:
            return
        pm_ids = self._selected_lcc_detail_pm_ids()
        if not pm_ids:
            QMessageBox.warning(
                self,
                messages.LTAP_ERROR_DIALOG_TITLE,
                messages.WORKSPACE_LCC_SELECTION_REQUIRED,
            )
            return
        shift_years = int(self.lcc_shift_spin.value())
        result = wss.apply_overlay_shift_for_session(
            session, overlay, pm_ids=pm_ids, shift_years=shift_years
        )
        if result.error:
            QMessageBox.critical(self, messages.LTAP_ERROR_DIALOG_TITLE, result.error)
            return
        self.workspace_state.set_planning_overlay(result.overlay)

    def _selected_lcc_detail_pm_ids(self) -> list[str]:
        selection = self.lcc_detail_table_view.selectionModel()
        if selection is None:
            return []
        out: list[str] = []
        for index in selection.selectedRows():
            pm_id = self._lcc_detail_model.pm_id_at(index.row())
            if pm_id is not None:
                out.append(pm_id)
        return out

    def _on_lcc_detail_cell_clicked(self, index: QModelIndex) -> None:
        if not index.isValid() or index.column() != PASSIVE_COLUMN:
            return
        if not self.workspace_state.snapshot().planning_overlay.active:
            return
        pm_id = self._lcc_detail_model.pm_id_at(index.row())
        if pm_id is None:
            return
        overlay = self.workspace_state.snapshot().planning_overlay
        passive = pm_id in overlay.disabled_pm_ids
        self.workspace_state.set_planning_overlay(
            overlay.set_passive(pm_id, passive=not passive)
        )

    def _on_fm_evident_filter_changed(self, _index: int = 0) -> None:
        value = self.fm_evident_filter_combo.currentData()
        if value in ("all", "nmf_only", "evident_only"):
            self.workspace_state.set_fm_evident_filter(value)

    def _bind_bijdragen_view(
        self,
        bijdragen_view,
        snapshot: WorkspaceStateSnapshot,
    ) -> None:
        rows = bijdragen_view.contribution_rows
        self.bijdragen_chart_widget.set_rows(rows)
        table_model = ContributionTableModel(
            rows,
            metric=snapshot.metric,
            presentation=snapshot.contribution_presentation,
        )
        self.bijdragen_table_view.setModel(table_model)
        self.bijdragen_chart_label.setVisible(len(rows) == 0)

    def _clear_detail_zone(self) -> None:
        self._fm_table_proxy.setSourceModel(None)
        self.detail_empty_state_label.setVisible(True)
        self._refresh_fm_inspector(None)
        self.bijdragen_chart_widget.set_rows(())
        self.bijdragen_table_view.setModel(None)
        self.bijdragen_chart_label.setVisible(True)
        self.lcc_chart_widget.set_buckets(())
        self.lcc_table_view.setModel(None)
        self.lcc_empty_state_label.setVisible(True)
        self._apply_compare_chrome(plan_compare_chrome(ResultsWorkspaceState().snapshot()))

    def _update_scope_status_label(self) -> None:
        if self._pbs_scope_id is None:
            self.scope_status_label.setText("Scope: hele project")
            return
        session = self._project_session()
        bouwdeel = ""
        if session is not None and self._pbs_scope_id is not None:
            bouwdeel = wss.scope_bouwdeel_naam(session, self._pbs_scope_id)
        self.scope_status_label.setText(
            f"Scope: {self._pbs_scope_id}" + (f" — {bouwdeel}" if bouwdeel else "")
        )

    def _pick_file(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Kies projectbestand",
            self.path_input.text() or str(Path.cwd()),
            "RCM JSON (*.rcm.json);;JSON (*.json)",
        )
        if filename:
            self.path_input.setText(filename)

    def _open_rcm_cost_export(self) -> None:
        excel_path, _ = QFileDialog.getOpenFileName(
            self,
            messages.ISOGRAPH_OPEN_FILE_DIALOG_TITLE,
            self.path_input.text() or str(Path.cwd()),
            messages.ISOGRAPH_OPEN_FILE_FILTER,
        )
        if not excel_path:
            return

        gate = gate_workbook(Path(excel_path))
        if not gate.ok:
            QMessageBox.critical(self, messages.ERROR_DIALOG_TITLE, gate.error.message if gate.error else "")
            return

        default_modeljaar = 2026
        session = self._project_session()
        if session is not None:
            default_modeljaar = int(session.loaded.modeljaar)

        wizard = run_import_wizard(
            ImportDialogInput(path=Path(excel_path), default_modeljaar=default_modeljaar),
            parent=self,
        )
        if wizard is None:
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            messages.ISOGRAPH_SAVE_IMPORTED_TITLE,
            str(Path(excel_path).with_suffix(".rcm.json")),
            messages.ISOGRAPH_SAVE_IMPORTED_FILTER,
        )
        if not save_path:
            return

        outcome = persist_wizard_result(wizard, Path(save_path))
        if outcome.kind == "blocked":
            if outcome.validate_result is not None:
                self._state.set_last_result(outcome.validate_result)
            failure = outcome.failure
            message = failure.message if failure is not None else messages.ISOGRAPH_IMPORT_VALIDATION_FAILED
            QMessageBox.critical(self, messages.ERROR_DIALOG_TITLE, message)
            return

        assert outcome.success is not None
        self._apply_import_success(outcome.success)

    def _apply_import_success(self, outcome: PersistImportSuccess) -> None:
        self._suppress_path_change = True
        self.path_input.setText(str(outcome.save_path))
        self._suppress_path_change = False
        self._state.set_last_run(None)
        self._state.set_last_result(outcome.validate_result)
        self._state.set_last_project(outcome.project)
        self._state.set_last_preview(build_project_preview(outcome.project))
        self._project_total_presentation = None
        self._clear_compare_slots()
        self._after_project_validated(outcome.project)
        self.validate_summary_label.setText(
            messages.ISOGRAPH_IMPORT_SAVE_SUCCESS.format(path=outcome.save_path)
        )

    def _on_path_changed(self, _text: str) -> None:
        if self._suppress_path_change:
            return
        self._state.set_last_run(None)
        self._state.set_last_project(None)
        self._state.set_last_result(None)
        self._project_total_presentation = None
        self._clear_compare_slots()
        self._clear_validate_status_strip()
        self._update_run_button_label()

    def _start_validate(self) -> None:
        path = self.path_input.text().strip()
        if not path:
            QMessageBox.critical(self, messages.ERROR_DIALOG_TITLE, messages.ERROR_EMPTY_PATH)
            return
        self.validate_summary_label.clear()
        if self._runner.start(path):
            self.validate_button.setEnabled(False)

    def _compare_run_config(self) -> CompareRunConfig:
        snapshot = self.workspace_state.snapshot()
        scenario_key = self.compare_scenario_combo.currentData()
        return CompareRunConfig(
            scenario_key=scenario_key,
            planning_overlay=snapshot.planning_overlay,
            force_recompute=True,
        )

    def _start_run_slot_a(self) -> None:
        self._start_run_slot(COMPARE_SLOT_A)

    def _start_run_slot_b(self) -> None:
        self._start_run_slot(COMPARE_SLOT_B)

    def _start_run_slot(self, slot_key: str) -> None:
        session = self._project_session()
        if session is None:
            return
        path = self.path_input.text().strip()
        if self._compare_run_runner.start(
            wss.editing_project(session),
            path,
            slot_key,
            self._compare_run_config(),
        ):
            self._update_run_buttons_enabled()

    def _on_compare_run_state_changed(self, _state: str) -> None:
        self._update_run_buttons_enabled()

    def _on_compare_slot_result_ready(self, slot_key: str, outcome: object) -> None:
        if not isinstance(outcome, CompareRunOutcome):
            return
        previous = self._compare_slots.get(slot_key)
        if outcome.status != "done":
            QMessageBox.critical(
                self,
                messages.RUN_ERROR_DIALOG_TITLE,
                outcome.summary,
            )
            if CompareWorkspaceController.should_keep_previous_slot_on_error(
                slot_key, outcome, previous=previous
            ):
                return
            return
        plan = CompareWorkspaceController.plan_after_slot_run(
            slot_key, outcome, previous_snapshot=previous
        )
        if plan is None:
            return
        run_result = CompareWorkspaceController.apply_slot_run(self._compare_slots, plan)
        self._render_index.on_slot_updated(plan.render_slot_key)
        self._state.set_last_run(run_result)
        if plan.snapshot.presentation is not None:
            self._project_total_presentation = plan.snapshot.presentation
        self._rerender_detail_for_current_scope()

    def _on_compare_slots_changed(self) -> None:
        self._rerender_detail_for_current_scope()

    def _on_compare_toggle(self, checked: bool) -> None:
        self.workspace_state.set_compare_mode(checked)

    def _clear_compare_slots(self) -> None:
        self._compare_slots.clear_all()
        if self.workspace_state.snapshot().compare_mode:
            self.workspace_state.set_compare_mode(False)
        if hasattr(self, "compare_toggle_button"):
            self.compare_toggle_button.setChecked(False)

    def _maybe_auto_seed_baseline_slot_a(self) -> None:
        """Vul slot A na eerste geslaagde run als baseline (slice 60)."""
        if self._compare_slots.has(COMPARE_SLOT_A):
            return
        self._seed_last_run_into_slot(COMPARE_SLOT_A)

    def _seed_last_run_into_slot(self, slot_key: str) -> None:
        run = self._state.last_run
        if run is None or run.status != "done":
            return
        snapshot = self.workspace_state.snapshot()
        scenario_key = self.compare_scenario_combo.currentData()
        label = build_compare_slot_label(
            slot_key,
            scenario_key=scenario_key,
            overlay=snapshot.planning_overlay,
        )
        self._compare_slots.seed_from_last_run(
            slot_key,
            run_result=run,
            presentation=self._project_total_presentation,
            scenario_key=scenario_key,
            overlay_at_run=snapshot.planning_overlay,
            label=label,
        )

    def _bind_bijdragen_column(
        self,
        column: dict,
        bijdragen_view,
        snapshot: WorkspaceStateSnapshot,
    ) -> None:
        rows = bijdragen_view.contribution_rows
        column["chart"].set_rows(rows)
        table_model = ContributionTableModel(
            rows,
            metric=snapshot.metric,
            presentation=snapshot.contribution_presentation,
        )
        column["table"].setModel(table_model)
        column["placeholder"].setVisible(len(rows) == 0)
        column["chart"].setVisible(len(rows) > 0)
        column["table"].setVisible(len(rows) > 0)

    def _start_analyse(self) -> None:
        path = self.path_input.text().strip()
        session = self._project_session()
        if session is None:
            return
        overlay = self.workspace_state.snapshot().planning_overlay
        path = self.path_input.text().strip()
        force = bool(path and wss.fm_cache_available_for_session(session, path))
        if self._run_runner.start(
            wss.editing_project(session),
            path,
            planning_overlay=overlay,
            force_recompute=force,
        ):
            self.run_analyse_button.setEnabled(False)

    def _on_run_state_changed(self, _state: str) -> None:
        self._update_run_buttons_enabled()
        if _state == "idle":
            self._update_run_button_label()

    def _on_run_phase_changed(self, phase: str) -> None:
        if phase == PHASE_MOTOR:
            self.run_analyse_button.setText(messages.WORKSPACE_RUN_PHASE_MOTOR)
        elif phase == PHASE_PRESENTATION:
            self.run_analyse_button.setText(messages.WORKSPACE_RUN_PHASE_PRESENTATION)

    def _on_run_result_ready(self, result: object, presentation: object) -> None:
        from rcm_desktop.adapter.results_workspace_controller import ResultsWorkspaceController

        if not isinstance(result, RunResult):
            return
        if result.status != "done":
            QMessageBox.critical(
                self,
                messages.RUN_ERROR_DIALOG_TITLE,
                result.summary,
            )
            self._project_total_presentation = None
            return
        self._state.set_last_run(result)
        overlay = self.workspace_state.snapshot().planning_overlay
        plan = ResultsWorkspaceController.plan_after_successful_run(
            overlay,
            has_presentation_payload=isinstance(presentation, PresentationProjectTotal),
        )
        if overlay.active:
            self.workspace_state.set_planning_overlay(plan.overlay)
        if plan.had_passive_before_run:
            self._lcc_passive_kept_after_run = True
        if isinstance(presentation, PresentationProjectTotal):
            self._project_total_presentation = presentation
        elif plan.load_presentation_from_disk:
            self._project_total_presentation = self._load_presentation_from_disk()
        if plan.invalidate_render_index:
            self._render_index.on_workspace_state_reset()
        self._last_lcc_render_snapshot = None
        if plan.warmup_lcc and self.workspace_state.snapshot().modus == MODE_LCC:
            self._maybe_start_lcc_warmup()
        self._maybe_auto_seed_baseline_slot_a()
        self._update_run_button_label()

    def _on_presentation_rebuild_state_changed(self, state: str) -> None:
        self._update_run_buttons_enabled()
        if state == "busy":
            self.run_analyse_button.setText(messages.WORKSPACE_RUN_PHASE_PRESENTATION_UPDATE)
        elif state == "idle":
            self._update_run_button_label()

    def _on_presentation_rebuild_result_ready(self, dto: object) -> None:
        if isinstance(dto, PresentationProjectTotal):
            self._project_total_presentation = dto
            self._rerender_detail_for_current_scope()

    def _refresh_kpi_table_view(self) -> None:
        if not hasattr(self, "kpi_table_view"):
            return
        session = self._project_session()
        scope_id = self.workspace_state.snapshot().scope_id
        table = wss.build_kpi_table_for_session(
            session,
            run_result=self._state.last_run,
            scope_id=scope_id,
        )
        self._kpi_table_model = KPITableModel(table)
        self.kpi_table_view.setModel(self._kpi_table_model)

    def _update_run_button_label(self) -> None:
        if not hasattr(self, "run_analyse_button"):
            return
        session = self._project_session()
        path = self.path_input.text().strip()
        if session is not None and path and wss.fm_cache_available_for_session(session, path):
            self.run_analyse_button.setText(messages.WORKSPACE_RECOMPUTE_ANALYSE_BUTTON_LABEL)
        else:
            self.run_analyse_button.setText(messages.WORKSPACE_START_ANALYSE_BUTTON_LABEL)

    def _load_presentation_from_disk(self) -> PresentationProjectTotal | None:
        session = self._project_session()
        if session is None:
            return None
        resolved = resolve_project_file_path(
            session_path=session.path,
            path_text=self.path_input.text(),
        )
        if resolved.file_path is None:
            return None
        return wss.load_presentation_for_session(session, str(resolved.file_path))

    def _maybe_start_presentation_rebuild(self) -> None:
        session = self._project_session()
        path = self.path_input.text().strip()
        run = self._state.last_run
        if (
            session is None
            or not path
            or not isinstance(run, RunResult)
            or run.status != "done"
            or not wss.presentation_rebuild_needed_for_session(session, path)
            or self._run_runner.busy
            or self._presentation_rebuild_runner.busy
        ):
            return
        self._presentation_rebuild_runner.start(wss.editing_project(session), path, run)

    def _maybe_start_lcc_warmup(self) -> None:
        session = self._project_session()
        run = self._state.last_run
        if (
            session is None
            or not isinstance(run, RunResult)
            or run.status != "done"
            or self._run_runner.busy
            or self._lcc_warmup_runner.busy
        ):
            return
        snapshot = default_lcc_warmup_snapshot(self.workspace_state.snapshot())
        self._lcc_warmup_runner.start(
            wss.editing_project(session), run, self._render_index, snapshot
        )

    def _after_project_validated(self, project: object) -> None:
        from rcm_desktop.adapter.results_workspace_controller import ResultsWorkspaceController

        path = self.path_input.text().strip()
        if project is None or not path or not hasattr(project, "config"):
            return
        session = self._project_session()
        hydrated = (
            wss.hydrate_run_for_session(session, path)
            if session is not None
            else None
        )
        if hydrated is not None:
            self._state.set_last_run(hydrated)
        run = self._state.last_run
        plan = ResultsWorkspaceController.plan_after_validate(
            has_hydrated_run=hydrated is not None,
            has_path=bool(path),
            has_session=session is not None,
            run_done=isinstance(run, RunResult) and run.status == "done",
            presentation_rebuild_needed=(
                session is not None
                and bool(path)
                and wss.presentation_rebuild_needed_for_session(session, path)
            ),
            run_runner_busy=self._run_runner.busy,
            presentation_runner_busy=self._presentation_rebuild_runner.busy,
        )
        self._project_total_presentation = (
            self._load_presentation_from_disk() if plan.load_presentation_from_disk else None
        )
        self._maybe_auto_seed_baseline_slot_a()
        self._update_run_button_label()
        if plan.start_presentation_rebuild:
            self._maybe_start_presentation_rebuild()

    def _on_validate_state_changed(self, state: str) -> None:
        if state == "busy":
            self.validate_status_label.setText(messages.STATUS_BUSY_LOADING)
            self.validate_summary_label.clear()
            self._apply_semantic_status_style(self.validate_status_label, "busy")
            return
        if state == "idle":
            self.validate_button.setEnabled(True)
            self._update_run_buttons_enabled()

    def _on_validate_result_ready(self, result: object) -> None:
        if isinstance(result, ValidateResult):
            self._state.set_last_result(result)

    def _on_project_ready_from_runner(self, project: object) -> None:
        self._state.set_last_project(project)
        self._project_total_presentation = None
        self._after_project_validated(project)

    def _update_report_button_enabled(self) -> None:
        if not hasattr(self, "generate_report_button"):
            return
        assessment = assess_report_workspace(
            last_run=self._state.last_run,
            compare_slots=self._compare_slots,
            live_overlay=self.workspace_state.snapshot().planning_overlay,
        )
        busy = getattr(self, "_report_runner", None) is not None and self._report_runner.busy
        self.generate_report_button.setEnabled(assessment.eligible and not busy)

    def _open_report_generation(self) -> None:
        session = self._project_session()
        if session is None:
            return
        resolved = resolve_project_file_path(
            session_path=session.path,
            path_text=self.path_input.text(),
        )
        if resolved.file_path is None:
            QMessageBox.information(
                self,
                messages.REPORT_DIALOG_TITLE,
                messages.ERROR_EMPTY_PATH,
            )
            return
        project = session.loaded.core()
        project_path = resolved.file_path
        default_path = resolved.default_report_output_path(project)
        if default_path is None:
            return
        dialog = ReportGenerationDialog(
            self,
            project=project,
            project_path=project_path,
            last_run=self._state.last_run,
            compare_slots=self._compare_slots,
            live_overlay=self.workspace_state.snapshot().planning_overlay,
            default_output_path=default_path,
            scope_id=self.workspace_state.snapshot().scope_id,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        options = dialog.options()
        bundle = dialog.bundle()
        if options is None or bundle is None:
            return
        started = self._report_runner.start(
            project,
            bundle,
            options,
            project_path=project_path,
        )
        if not started:
            QMessageBox.warning(
                self,
                messages.REPORT_GENERATION_FAILED_TITLE,
                messages.REPORT_GENERATION_BUSY,
            )

    def _on_report_runner_state_changed(self, state: str) -> None:
        if state == "busy":
            self.generate_report_button.setEnabled(False)
        else:
            self._update_report_button_enabled()

    def _on_report_generation_finished(self, outcome: object) -> None:
        if not isinstance(outcome, ReportGenerationOutcome):
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(outcome.docx_path)))
        if outcome.pdf_error:
            QMessageBox.warning(
                self,
                messages.REPORT_PDF_FAILED_TITLE,
                messages.REPORT_PDF_FAILED_BODY.format(
                    docx_path=outcome.docx_path,
                    detail=outcome.pdf_error,
                ),
            )

    def _on_report_generation_failed(self, detail: str) -> None:
        QMessageBox.critical(self, messages.REPORT_GENERATION_FAILED_TITLE, detail)

    def _update_run_buttons_enabled(self) -> None:
        validation_ok = (
            self._state.last_result is not None
            and self._state.last_result.status in {"valid", "valid_with_warnings"}
        )
        busy = (
            self._run_runner.busy
            or self._presentation_rebuild_runner.busy
            or self._compare_run_runner.busy
            or self._report_runner.busy
        )
        can_run = validation_ok and self._project_session() is not None and not busy
        if hasattr(self, "run_analyse_button"):
            self.run_analyse_button.setEnabled(can_run)
        for btn in (
            getattr(self, "run_slot_a_button", None),
            getattr(self, "run_slot_b_button", None),
        ):
            if btn is not None:
                btn.setEnabled(can_run)
        self._update_report_button_enabled()

    def _clear_validate_status_strip(self) -> None:
        if not hasattr(self, "validate_status_label"):
            return
        self.validate_status_label.setText(messages.status_label("idle"))
        self.validate_summary_label.clear()
        self.validate_summary_label.setToolTip("")
        self._apply_semantic_status_style(self.validate_status_label, "idle")

    def _render_validate_result(self, result: object) -> None:
        if not isinstance(result, ValidateResult):
            return
        status_text = messages.status_label(result.status)
        self.validate_status_label.setText(status_text)
        self.validate_summary_label.setText(result.summary)
        self._apply_semantic_status_style(self.validate_status_label, result.status)
        if result.details:
            self.validate_summary_label.setToolTip(self._format_validate_details(result.details))
        else:
            self.validate_summary_label.setToolTip("")
        if result.error is not None:
            QMessageBox.critical(self, messages.ERROR_DIALOG_TITLE, result.error.message)

    @staticmethod
    def _format_validate_details(details: list[DetailItem]) -> str:
        lines: list[str] = []
        for item in details:
            context = f" [{item.context}]" if item.context else ""
            lines.append(f"{item.severity.upper()} {item.code}{context}: {item.message}")
        return "\n".join(lines)

    @staticmethod
    def _apply_semantic_status_style(label: QLabel, status: str) -> None:
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

    def _show_run_error(self, error: UserFacingError) -> None:
        QMessageBox.critical(self, messages.RUN_ERROR_DIALOG_TITLE, error.message)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        # Voorkom Windows-teardown crash (-1073741819 / ACCESS_VIOLATION) door
        # alle Qt-table-models expliciet te ontkoppelen vóórdat de window
        # Python-zijde wordt opgeruimd. Zonder dit kunnen modellen na de
        # `QTableView` worden vernietigd, met een dangling C++ pointer als gevolg.
        for view_name in (
            "fm_table_view",
            "bijdragen_table_view",
            "bijdragen_table_view_cm",
            "bijdragen_table_view_pm",
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
            view = getattr(self, view_name, None)
            if view is not None:
                view.setModel(None)
        event.accept()
