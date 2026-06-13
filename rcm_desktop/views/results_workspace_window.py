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
    QSettings,
    QSortFilterProxyModel,
    Qt,
    QUrl,
    Signal,
)
from PySide6.QtGui import QCloseEvent, QColor, QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QButtonGroup,
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
from rcm_desktop.adapter.shutdown_planner import ShutdownStep, plan_shutdown
from rcm_desktop.adapter.contribution_chart_service import build_contribution_rows
from rcm_desktop.adapter.fm_results_column_settings import (
    read_fm_hidden_optional_columns,
    write_fm_hidden_optional_columns,
)
from rcm_desktop.adapter.fm_results_sort_policy import default_fm_sort_column
from rcm_desktop.adapter.fm_results_table_model import FMResultsTableModel, RAW_ROLE
from rcm_desktop.adapter.fm_verification_service import FMVerificationView
from rcm_desktop.adapter.fm_verification_year_table_model import (
    FMVerificationYearTableModel,
)
from rcm_desktop.formatting import format_eur, format_float, format_int
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.lcc_planning_service import build_lcc_planning_curve_reconciled
from rcm_desktop.adapter.lcc_detail_selection import rev_row_indices
from rcm_desktop.adapter.lcc_type_filter import LCCTypeFilterSet
from rcm_desktop.adapter.lcc_year_detail_table_model import PASSIVE_COLUMN
from rcm_desktop.adapter.lcc_year_table_model import LCCYearTableModel
from rcm_desktop.adapter.workspace_lcc_preset_service import effective_lcc_filters
from rcm_desktop.adapter.import_flow_service import gate_workbook, persist_wizard_result
from rcm_desktop.adapter.isograph_export_flow_service import (
    ExportFlowBlocked,
    ExportFlowSuccess,
    export_rcm_cost_project,
)
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
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.planning_whatif_service import apply_overlay_shift
from rcm_desktop.adapter.pbs_results_tree_model import PBSResultsTreeModel
from rcm_desktop.adapter.rcm_navigation_tree_model import RcmNavigationTreeModel
from rcm_desktop.adapter import workspace_session_service as wss
from rcm_desktop.adapter.editing_host import EditingHost
from rcm_desktop.adapter.entity_edit_service import EntityEditService
from rcm_desktop.adapter.entity_grid_column_settings import (
    read_hidden_entity_columns,
    write_hidden_entity_columns,
)
from rcm_desktop.views.fm_editor_dialog import FmEditorDialog
from rcm_desktop.views.grid_dirty_guard import resolve_grid_dirty_before_editor
from rcm_desktop.views.model_settings_dialog import ModelSettingsDialog
from rcm_desktop.views.validate_faalwijzen_panel import ValidateFaalwijzenPanel
from rcm_desktop.views.import_wizard_dialog import ImportDialogInput, run_import_wizard
from rcm_desktop.adapter.portfolio_wizard_service import persist_portfolio_wizard_result
from rcm_desktop.adapter.rcm_cost_parity_service import build_parity_view
from rcm_desktop.adapter.view_core_facade import has_aw_benchmarks
from rcm_desktop.views.portfolio_wizard_dialog import run_portfolio_wizard_with_root_picker
from rcm_desktop.views.rcm_cost_parity_dialog import show_rcm_cost_parity_dialog
from rcm_desktop.views.compare_slot_column import set_compare_placeholder
from rcm_desktop.views.panels.bijdragen_workspace_panel import (
    build_bijdragen_workspace_panel,
)
from rcm_desktop.views.panels.fm_detail_workspace_panel import (
    build_fm_detail_workspace_panel,
)
from rcm_desktop.views.panels.fm_results_column_binding import (
    apply_fm_optional_column_visibility,
    build_fm_column_context_menu,
)
from rcm_desktop.views.panels.fm_results_filter_binding import (
    apply_fm_filter_row_to_proxy,
    bind_fm_filter_row,
)
from rcm_desktop.views.panels.entity_grid_panel import EntityGridPanel
from rcm_desktop.views.panels.lcc_workspace_panel import build_lcc_workspace_panel
from rcm_desktop.adapter.column_fit_policy import ColumnFitMode
from rcm_desktop.adapter.column_fit_settings import (
    column_fit_mode_from_crop_checked,
    crop_checked_from_column_fit_mode,
    read_fm_detail_column_fit_mode,
    write_fm_detail_column_fit_mode,
)
from rcm_desktop.views.panels.workspace_menu_binding import (
    WorkspaceMenuBinding,
    WorkspaceMenuHandlers,
    build_workspace_menu_bar,
    sync_workspace_menu_check_states,
)
from rcm_desktop.views.panels.workspace_navigation_panel import (
    apply_workspace_navigation_plan,
    build_workspace_navigation_panel,
)
from rcm_desktop.views.panels.fm_inspector_binding import (
    apply_fm_inspector_view,
    refresh_fm_inspector,
)
from rcm_desktop.views.panels.meekoppel_workspace_binding import (
    bind_meekoppel_panel,
    clear_meekoppel_preview_gate,
    ensure_whatif_for_meekoppel,
    on_meekoppel_anchor_changed,
    on_meekoppel_apply,
    on_meekoppel_preview,
    on_meekoppel_window_changed,
)
from rcm_desktop.views.panels.pbs_sidebar_panel import build_pbs_sidebar_panel
from rcm_desktop.views.panels.pbs_tree_navigation_binding import (
    pbs_tree_has_focus,
    pbs_tree_navigate,
    pbs_tree_reorder,
)
from rcm_desktop.views.panels.top10_workspace_binding import (
    build_and_wire_top10_subbar,
    refresh_contribution_year_combo,
    refresh_nb_effect_filter_combo,
)
from rcm_desktop.views.panels.workspace_shutdown_binding import (
    any_runner_busy,
    cancel_background_runners as cancel_window_background_runners,
    confirm_busy_shutdown,
    detach_table_models_before_close,
)
from rcm_desktop.views.panels.workspace_toolbar_sync import (
    apply_bijdragen_toolbar,
    apply_collapse_panels,
    apply_compare_chrome,
    apply_fm_toolbar,
    apply_lcc_toolbar,
)
from rcm_desktop.views.panels.workspace_table_policy import (
    apply_column_fit_mode_to_table,
    apply_workspace_data_table_header_policy,
)
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
from rcm_desktop.adapter.workspace_navigation_settings import (
    read_workspace_navigation,
    write_workspace_navigation,
)
from rcm_desktop.adapter.workspace_render_index import WorkspaceRenderIndex
from rcm_desktop.views.widgets.nb_effect_filter_combo import NbEffectFilterCombo
from rcm_desktop.app_state import AppState
from rcm_desktop.table_ui_constants import PBS_FILTER_MAX_EXPAND_NODES


def _apply_workspace_data_table_header_policy(header: QHeaderView) -> None:
    apply_workspace_data_table_header_policy(header)


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
        self._last_lcc_toolbar_plan = None
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
        self._build_workspace_menu()
        self._restore_fm_column_fit_preferences()
        self._restore_fm_optional_column_preferences()
        self._restore_workspace_navigation_preferences()
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
        self.portfolio_wizard_button = QPushButton(messages.PORTFOLIO_WIZARD_BUTTON_LABEL)
        self.portfolio_wizard_button.setToolTip(messages.PORTFOLIO_WIZARD_BUTTON_TOOLTIP)
        self.portfolio_wizard_button.clicked.connect(self._open_portfolio_wizard)
        self.rcm_cost_parity_button = QPushButton(messages.RCM_COST_PARITY_BUTTON_LABEL)
        self.rcm_cost_parity_button.setToolTip(messages.RCM_COST_PARITY_BUTTON_TOOLTIP)
        self.rcm_cost_parity_button.setEnabled(False)
        self.rcm_cost_parity_button.clicked.connect(self._open_rcm_cost_parity)
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

        self.show_whole_project_button = QPushButton(messages.WORKSPACE_SHOW_WHOLE_PROJECT_BUTTON)
        self.show_whole_project_button.setToolTip(messages.WORKSPACE_SHOW_WHOLE_PROJECT_TOOLTIP)
        self.show_whole_project_button.clicked.connect(self._on_show_whole_project_clicked)

        self._build_workspace_navigation()
        self._build_validate_status_strip()

    def _build_workspace_navigation(self) -> None:
        self._workspace_navigation = build_workspace_navigation_panel(self.workspace_state)
        self._build_top10_subbar()

    def _build_workspace_menu(self) -> None:
        self._workspace_menu: WorkspaceMenuBinding = build_workspace_menu_bar(
            self,
            WorkspaceMenuHandlers(
                open_project=self._start_validate,
                open_rcm_cost=self._open_rcm_cost_export,
                export_rcm_cost=self._export_rcm_cost_workbook,
                quit=self.close,
                set_pbs_sidebar_visible=self._set_pbs_sidebar_visible,
                set_kpi_overview_visible=self._set_kpi_overview_visible,
                set_fm_column_crop=self._on_fm_column_crop_toggled,
                toggle_lcc_whatif=self._toggle_lcc_whatif_from_menu,
                run_compare_slot_a=self._start_run_slot_a,
                run_compare_slot_b=self._start_run_slot_b,
                set_compare_scenario_cm=lambda: self._set_compare_scenario("cm"),
                set_compare_scenario_pm=lambda: self._set_compare_scenario("pm"),
                revalidate_input=self._revalidate_input,
                open_faalwijzen_grid=self._open_batch_faalwijzen_grid,
                open_model_settings=self._open_model_settings,
                open_report_generation=self._open_report_generation,
                pbs_select_prev_sibling=lambda: self._pbs_tree_navigate("prev_sibling"),
                pbs_select_next_sibling=lambda: self._pbs_tree_navigate("next_sibling"),
                pbs_select_parent=lambda: self._pbs_tree_navigate("parent"),
                pbs_select_first_child=lambda: self._pbs_tree_navigate("first_child"),
                pbs_move_up=lambda: self._pbs_tree_reorder("up"),
                pbs_move_down=lambda: self._pbs_tree_reorder("down"),
                set_workspace_side=self.workspace_state.set_workspace_side,
                set_active_view=self.workspace_state.set_active_view,
            ),
        )
        self._sync_workspace_menu_check_states()

    def _sync_workspace_menu_check_states(self) -> None:
        crop_checked = None
        if hasattr(self, "_fm_column_fit_mode"):
            crop_checked = crop_checked_from_column_fit_mode(self._fm_column_fit_mode)
        snapshot = self.workspace_state.snapshot()
        sync_workspace_menu_check_states(
            self._workspace_menu,
            pbs_sidebar_visible=not self.pbs_sidebar.isHidden(),
            kpi_overview_visible=not snapshot.kpi_collapsed_in_lcc,
            fm_column_crop_checked=crop_checked,
            workspace_side=snapshot.workspace_side,
            active_view_id=snapshot.active_view_id,
        )
        self._update_report_menu_enabled()

    def _pbs_tree_has_focus(self) -> bool:
        return pbs_tree_has_focus(self)

    def _current_pbs_scope_id(self) -> str | None:
        from rcm_desktop.views.panels.pbs_tree_navigation_binding import current_pbs_scope_id

        return current_pbs_scope_id(self)

    def _select_pbs_id_in_tree(self, pbs_id: str) -> None:
        from rcm_desktop.views.panels.pbs_tree_navigation_binding import select_pbs_id_in_tree

        select_pbs_id_in_tree(self, pbs_id)

    def _pbs_tree_navigate(self, action: str) -> None:
        pbs_tree_navigate(self, action)

    def _pbs_tree_reorder(self, direction: str) -> None:
        pbs_tree_reorder(self, direction)

    def _set_pbs_sidebar_visible(self, visible: bool) -> None:
        self.pbs_sidebar.setVisible(visible)
        self._sync_workspace_menu_check_states()

    def _set_kpi_overview_visible(self, visible: bool) -> None:
        self.workspace_state.set_kpi_collapsed_in_lcc(not visible)

    def _report_menu_action(self):
        return self._workspace_menu.actions_by_id.get("analysis.generate_report")

    def _update_report_menu_enabled(self) -> None:
        action = self._report_menu_action()
        if action is None:
            return
        assessment = assess_report_workspace(
            last_run=self._state.last_run,
            compare_slots=self._compare_slots,
            live_overlay=self.workspace_state.snapshot().planning_overlay,
        )
        busy = getattr(self, "_report_runner", None) is not None and self._report_runner.busy
        action.setEnabled(assessment.eligible and not busy)

    def _build_validate_status_strip(self) -> None:
        self.validate_status_label = QLabel(messages.status_label("idle"))
        self.validate_summary_label = QLabel("")
        self.validate_summary_label.setWordWrap(True)
        self._apply_semantic_status_style(self.validate_status_label, "idle")

    def _build_top10_subbar(self) -> None:
        build_and_wire_top10_subbar(self)

    def _refresh_nb_effect_filter_combo(self, project: object) -> None:
        refresh_nb_effect_filter_combo(self, project)

    def _refresh_contribution_year_combo(self, project) -> None:
        refresh_contribution_year_combo(self, project)

    def _build_pbs_sidebar(self) -> None:
        pbs = build_pbs_sidebar_panel()
        self.pbs_sidebar = pbs.sidebar
        self.pbs_filter_input = pbs.filter_input
        self.pbs_tree_view = pbs.tree_view
        self.pbs_empty_state_label = pbs.empty_state_label
        self.pbs_proxy = pbs.proxy
        self.pbs_filter_input.textChanged.connect(self._on_pbs_filter_text_changed)

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
        self.input_placeholder_page = self._build_placeholder_page(
            messages.WORKSPACE_INPUT_PLACEHOLDER
        )
        self.input_entity_grid_page = QWidget()
        input_grid_layout = QVBoxLayout(self.input_entity_grid_page)
        input_grid_layout.setContentsMargins(0, 0, 0, 0)
        self._entity_grid_panel = EntityGridPanel()
        self._entity_grid_panel.set_hidden_columns_handler(self._on_entity_grid_columns_changed)
        input_grid_layout.addWidget(self._entity_grid_panel)
        self._entity_grid_view_id: str | None = None
        self._entity_grid_hidden: frozenset[str] = frozenset()

        self._detail_pages: dict[str, QWidget] = {
            MODE_BIJDRAGEN: self.bijdragen_page,
            MODE_LCC: self.lcc_page,
            MODE_FM_DETAIL: self.fm_detail_page,
        }
        for modus_key in (MODE_BIJDRAGEN, MODE_LCC, MODE_FM_DETAIL):
            self.detail_stack.addWidget(self._detail_pages[modus_key])
        self.detail_stack.addWidget(self.input_placeholder_page)
        self.detail_stack.addWidget(self.input_entity_grid_page)
        detail_layout.addWidget(self.detail_stack, stretch=1)


    def _build_bijdragen_page(self) -> QWidget:
        panel = build_bijdragen_workspace_panel()
        self.bijdragen_chart_label = panel.chart_label
        self.bijdragen_single_slot_pane = panel.single_slot_pane
        self.bijdragen_chart_widget = panel.chart_widget
        self.bijdragen_compare_pane = panel.compare_pane
        self._bijdragen_compare_col_a = panel.compare_col_a
        self._bijdragen_compare_col_b = panel.compare_col_b
        return panel.page

    def _build_lcc_page(self) -> QWidget:
        panel = build_lcc_workspace_panel()
        self.lcc_empty_state_label = panel.lcc_empty_state_label
        self.lcc_filter_bar = panel.lcc_filter_bar
        self.lcc_whatif_collapse_button = panel.lcc_whatif_collapse_button
        self.lcc_whatif_bar_title = panel.lcc_whatif_bar_title
        self.lcc_whatif_content = panel.lcc_whatif_content
        self._lcc_filter_checks = panel.lcc_filter_checks
        self.lcc_whatif_button = panel.lcc_whatif_button
        self.lcc_reset_overlay_button = panel.lcc_reset_overlay_button
        self.lcc_bulk_rev_passive_button = panel.lcc_bulk_rev_passive_button
        self.lcc_cm_preset_button = panel.lcc_cm_preset_button
        self.lcc_overlay_status_label = panel.lcc_overlay_status_label
        self.meekoppel_panel = panel.meekoppel_panel
        self.meekoppel_collapse_button = panel.meekoppel_collapse_button
        self.meekoppel_title_label = panel.meekoppel_title_label
        self.meekoppel_content = panel.meekoppel_content
        self.meekoppel_help_label = panel.meekoppel_help_label
        self.meekoppel_whatif_hint_label = panel.meekoppel_whatif_hint_label
        self.meekoppel_selection_summary_label = panel.meekoppel_selection_summary_label
        self.meekoppel_window_spin = panel.meekoppel_window_spin
        self.meekoppel_anchor_earlier = panel.meekoppel_anchor_earlier
        self.meekoppel_anchor_later = panel.meekoppel_anchor_later
        self._meekoppel_anchor_group = panel.meekoppel_anchor_group
        self.meekoppel_preview_button = panel.meekoppel_preview_button
        self.meekoppel_apply_button = panel.meekoppel_apply_button
        self.meekoppel_empty_label = panel.meekoppel_empty_label
        self.meekoppel_table_view = panel.meekoppel_table_view
        self._meekoppel_table_model = panel.meekoppel_table_model
        self._meekoppel_preview_gate: MeekoppelPreviewGate | None = None
        self._meekoppel_location_groups: tuple[MeekoppelLocationGroup, ...] = ()
        self._meekoppel_workflow = MeekoppelWorkflowService()
        self.lcc_year_summary_label = panel.lcc_year_summary_label
        self.lcc_show_all_years_button = panel.lcc_show_all_years_button
        self.lcc_detail_toolbar = panel.lcc_detail_toolbar
        self.lcc_shift_selection_hint = panel.lcc_shift_selection_hint
        self.lcc_select_rev_button = panel.lcc_select_rev_button
        self.lcc_shift_spin = panel.lcc_shift_spin
        self.lcc_shift_button = panel.lcc_shift_button
        self.lcc_single_slot_pane = panel.lcc_single_slot_pane
        self.lcc_chart_widget = panel.lcc_chart_widget
        self.lcc_table_view = panel.lcc_table_view
        self.lcc_detail_table_view = panel.lcc_detail_table_view
        self._lcc_detail_model = panel.lcc_detail_model
        self.lcc_compare_pane = panel.lcc_compare_pane
        self._lcc_compare_col_a = panel.lcc_compare_col_a
        self._lcc_compare_col_b = panel.lcc_compare_col_b

        self.lcc_whatif_collapse_button.clicked.connect(self._on_lcc_whatif_collapse_toggled)
        for box in self._lcc_filter_checks.values():
            box.toggled.connect(self._on_lcc_filter_toggled)
        self.lcc_whatif_button.toggled.connect(self._on_lcc_whatif_toggled)
        self.lcc_reset_overlay_button.clicked.connect(self._on_lcc_reset_overlay)
        self.lcc_bulk_rev_passive_button.clicked.connect(self._on_lcc_bulk_rev_toggle)
        self.lcc_cm_preset_button.clicked.connect(self._on_lcc_cm_policy_preset)
        self.meekoppel_collapse_button.clicked.connect(self._on_meekoppel_collapse_toggled)
        self.meekoppel_window_spin.valueChanged.connect(self._on_meekoppel_window_changed)
        self._meekoppel_anchor_group.buttonClicked.connect(self._on_meekoppel_anchor_changed)
        self.meekoppel_preview_button.clicked.connect(self._on_meekoppel_preview)
        self.meekoppel_apply_button.clicked.connect(self._on_meekoppel_apply)
        self.lcc_show_all_years_button.clicked.connect(self._on_lcc_show_all_years)
        self.lcc_select_rev_button.clicked.connect(self._on_lcc_select_rev_in_year)
        self.lcc_shift_button.clicked.connect(self._on_lcc_shift_selected)
        self.lcc_chart_widget.year_clicked.connect(self._on_lcc_year_clicked)
        self.lcc_detail_table_view.clicked.connect(self._on_lcc_detail_cell_clicked)
        self._lcc_compare_col_a["chart"].year_clicked.connect(self._on_lcc_year_clicked)
        self._lcc_compare_col_b["chart"].year_clicked.connect(self._on_lcc_year_clicked)
        return panel.page

    def _build_fm_detail_page(self) -> QWidget:
        panel = build_fm_detail_workspace_panel()
        self.fm_detail_splitter = panel.fm_detail_splitter
        self.new_fm_button = panel.new_fm_button
        panel.column_crop_button.setVisible(False)
        self.fm_table_view = panel.fm_table_view
        self._fm_table_filter_proxy = panel.fm_table_filter_proxy
        self._fm_table_proxy = panel.fm_table_proxy
        self.fm_table_filter_row = panel.fm_table_filter_row
        self.fm_filter_clear_button = panel.fm_filter_clear_button
        self.fm_filter_row_count_label = panel.fm_filter_row_count_label
        self.detail_empty_state_label = panel.detail_empty_state_label
        self.fm_inspector_container = panel.fm_inspector_container
        self.fm_inspector_empty_label = panel.fm_inspector_empty_label
        self.fm_inspector_panel = panel.fm_inspector_panel
        self.fm_inspector_identity_label = panel.fm_inspector_identity_label
        self.fm_inspector_lifecycle_label = panel.fm_inspector_lifecycle_label
        self.fm_inspector_hash_label = panel.fm_inspector_hash_label
        self.fm_inspector_reconcile_label = panel.fm_inspector_reconcile_label
        self.fm_inspector_profile_missing_label = panel.fm_inspector_profile_missing_label
        self.fm_inspector_year_table_view = panel.fm_inspector_year_table_view
        self.new_fm_button.clicked.connect(self._on_new_fm_clicked)
        sel = self.fm_table_view.selectionModel()
        if sel is not None:
            sel.selectionChanged.connect(self._on_fm_table_selection_changed)
        self.fm_table_view.doubleClicked.connect(self._on_fm_table_double_clicked)
        bind_fm_filter_row(
            self.fm_table_filter_row,
            self.fm_table_view,
            self._fm_table_filter_proxy,
            on_filters_changed=self._refresh_fm_filter_row_count,
        )
        self.fm_filter_clear_button.clicked.connect(self._on_fm_filter_clear)
        fm_header = self.fm_table_view.horizontalHeader()
        fm_header.setContextMenuPolicy(Qt.CustomContextMenu)
        fm_header.customContextMenuRequested.connect(self._on_fm_table_header_context_menu)
        return panel.page

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
            self.portfolio_wizard_button,
            self.rcm_cost_parity_button,
            self.validate_button,
            self.compare_scenario_combo,
            self.run_slot_a_button,
            self.run_slot_b_button,
            self.compare_toggle_button,
            self.clear_compare_button,
            self.run_analyse_button,
        ):
            toolbar_row.addWidget(w)
        toolbar_row.addStretch(1)
        toolbar_row.addWidget(self.show_whole_project_button)

        modus_row = QHBoxLayout()
        modus_row.addWidget(self._workspace_navigation.widget)
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
        self.kpi_panel_title = QLabel(messages.WORKSPACE_KPI_PANEL_TITLE)
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
        session = self._project_session()
        project = wss.editing_project(session) if session is not None else None
        self._entity_grid_panel.set_scope(scope_id, project)

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
        self._persist_workspace_navigation_preferences(snapshot)

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
        apply_workspace_navigation_plan(
            self._workspace_navigation,
            workspace_side=plan.navigation.workspace_side,
            active_view_id=plan.navigation.active_view_id,
            dropdown_items=plan.navigation.dropdown_items,
        )
        if plan.navigation.show_input_placeholder:
            if self.detail_stack.currentWidget() is not self.input_placeholder_page:
                self.detail_stack.setCurrentWidget(self.input_placeholder_page)
        elif plan.navigation.show_input_entity_grid:
            if self.detail_stack.currentWidget() is not self.input_entity_grid_page:
                self.detail_stack.setCurrentWidget(self.input_entity_grid_page)
            self._refresh_entity_grid(plan.navigation.active_view_id)
        else:
            page = self._detail_pages.get(plan.detail_page_modus, self.bijdragen_page)
            if self.detail_stack.currentWidget() is not page:
                self.detail_stack.setCurrentWidget(page)
        if plan.detail_page_modus != MODE_FM_DETAIL:
            self._fm_sort_metric = None
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
        if hasattr(self, "_workspace_menu"):
            self._sync_workspace_menu_check_states()

    def _apply_bijdragen_toolbar(self, toolbar: BijdragenToolbarPlan | None) -> None:
        apply_bijdragen_toolbar(self, toolbar)

    def _apply_lcc_toolbar(
        self,
        toolbar: LccToolbarVisibilityPlan | None,
        snapshot: WorkspaceStateSnapshot,
    ) -> None:
        apply_lcc_toolbar(self, toolbar, snapshot)

    def _apply_fm_toolbar(self, toolbar: FmToolbarPlan) -> None:
        apply_fm_toolbar(self, toolbar)

    def _apply_compare_chrome(self, compare: CompareChromePlan) -> None:
        apply_compare_chrome(self, compare)

    def _apply_collapse_panels(self, collapse: CollapsePanelsPlan) -> None:
        apply_collapse_panels(self, collapse)

    def _seed_planning_overlay_from_import(self, project: object) -> None:
        import_settings = getattr(project, "import_settings", None)
        if import_settings is None:
            return
        overlay = PlanningOverlayState.from_import_settings(import_settings)
        if overlay.active:
            self.workspace_state.set_planning_overlay(overlay)

    def _on_state_project_changed(self, project: object) -> None:
        self._refresh_contribution_year_combo(project)
        self._refresh_nb_effect_filter_combo(project)
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
        if isinstance(run_result, RunResult) and run_result.status == "done":
            project = self._state.last_project
            if project is not None:
                self._refresh_nb_effect_filter_combo(project)
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

    def _restore_fm_column_fit_preferences(self) -> None:
        settings = QSettings("rcm2", "desktop")
        mode = read_fm_detail_column_fit_mode(settings)
        self._fm_column_fit_mode = mode
        self._apply_fm_column_fit_mode(mode)
        if hasattr(self, "_workspace_menu"):
            self._sync_workspace_menu_check_states()

    def _restore_fm_optional_column_preferences(self) -> None:
        settings = QSettings("rcm2", "desktop")
        self._fm_hidden_optional_columns = read_fm_hidden_optional_columns(settings)
        self._apply_fm_optional_column_visibility()

    def _apply_fm_optional_column_visibility(self) -> None:
        if not hasattr(self, "fm_table_view"):
            return
        hidden = getattr(self, "_fm_hidden_optional_columns", frozenset({"pbs_id"}))
        apply_fm_optional_column_visibility(
            self.fm_table_view,
            hidden_optional_columns=hidden,
        )
        if hasattr(self, "fm_table_filter_row"):
            self.fm_table_filter_row._sync_column_widths()

    def _on_fm_table_header_context_menu(self, pos) -> None:
        hidden = getattr(self, "_fm_hidden_optional_columns", frozenset({"pbs_id"}))
        menu = build_fm_column_context_menu(
            self.fm_table_view,
            hidden_optional_columns=hidden,
            on_toggle=self._on_fm_optional_column_toggled,
        )
        header = self.fm_table_view.horizontalHeader()
        menu.exec(header.mapToGlobal(pos))

    def _on_fm_optional_column_toggled(self, column_id: str, visible: bool) -> None:
        hidden = set(getattr(self, "_fm_hidden_optional_columns", frozenset()))
        if visible:
            hidden.discard(column_id)
        else:
            hidden.add(column_id)
        self._fm_hidden_optional_columns = frozenset(hidden)
        write_fm_hidden_optional_columns(
            QSettings("rcm2", "desktop"),
            self._fm_hidden_optional_columns,
        )
        self._apply_fm_optional_column_visibility()

    def _restore_workspace_navigation_preferences(self) -> None:
        settings = QSettings("rcm2", "desktop")
        side, sticky = read_workspace_navigation(settings)
        self.workspace_state.restore_navigation(side, sticky)

    def _persist_workspace_navigation_preferences(self, snapshot: WorkspaceStateSnapshot) -> None:
        write_workspace_navigation(
            QSettings("rcm2", "desktop"),
            workspace_side=snapshot.workspace_side,
            sticky_by_side=self.workspace_state.sticky_views_by_side(),
        )

    def _apply_fm_column_fit_mode(self, mode: ColumnFitMode) -> None:
        if not hasattr(self, "fm_table_view"):
            return
        apply_column_fit_mode_to_table(self.fm_table_view, mode)

    def _on_fm_column_crop_toggled(self, checked: bool) -> None:
        mode = column_fit_mode_from_crop_checked(checked)
        self._fm_column_fit_mode = mode
        write_fm_detail_column_fit_mode(QSettings("rcm2", "desktop"), mode)
        self._apply_fm_column_fit_mode(mode)
        self._sync_workspace_menu_check_states()

    def _render_fm_rows(self, fm_rows) -> None:
        prior_fm_id = self._selected_fm_id_from_table()
        model = FMResultsTableModel(list(fm_rows), self.fm_table_view)
        self._fm_table_filter_proxy.setSourceModel(model)
        metric = self.workspace_state.snapshot().metric
        if getattr(self, "_fm_sort_metric", None) != metric:
            self._fm_sort_metric = metric
            col = default_fm_sort_column(metric)
            self.fm_table_view.sortByColumn(col, Qt.DescendingOrder)
        self._apply_fm_optional_column_visibility()
        self.detail_empty_state_label.setVisible(model.rowCount() == 0)
        if hasattr(self, "_fm_column_fit_mode"):
            self._apply_fm_column_fit_mode(self._fm_column_fit_mode)
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
        self._refresh_fm_filter_row_count()

    def _refresh_fm_filter_row_count(self) -> None:
        if not hasattr(self, "fm_filter_row_count_label"):
            return
        visible = self._fm_table_proxy.rowCount()
        source = self._fm_table_filter_proxy.sourceModel()
        total = source.rowCount() if source is not None else visible
        self.fm_filter_row_count_label.setText(
            messages.TABLE_FILTER_ROW_COUNT.format(visible=visible, total=total)
        )

    def _on_fm_filter_clear(self) -> None:
        self.fm_table_filter_row.clear_all()
        self._fm_table_filter_proxy.clear_filters()
        self.fm_table_filter_row.apply_invalid_numeric_columns(frozenset())
        self._refresh_fm_filter_row_count()

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
        if not host.is_grid_dirty() or grid_svc.error_count() != 0:
            return grid_svc.error_count() == 0
        path = self.path_input.text().strip() or None
        result = host.commit_grid_edits(path=path, save_to_disk=bool(path))
        if not result.ok:
            return False
        if result.project is not None:
            self._state.set_last_project(result.project, path=path)
        if result.run_result is not None:
            self._state.set_last_run(result.run_result)
        return True

    def _revalidate_input(self) -> None:
        session = self._project_session()
        if session is None:
            return
        from rcm_desktop.adapter.input_revalidation_service import revalidate_input_buffer

        project = wss.editing_project(session)
        host = self._editing_host
        grid = host.ensure_grid(project)
        revalidate_input_buffer(grid.editing_session)
        self._entity_grid_panel.refresh_view()

    def _on_entity_grid_changed(self) -> None:
        self._entity_grid_panel.refresh_view()
        self._update_run_buttons_enabled()

    def _on_entity_grid_columns_changed(self, hidden: frozenset[str]) -> None:
        view_id = self._entity_grid_view_id
        if view_id is None:
            return
        write_hidden_entity_columns(QSettings("rcm2", "desktop"), view_id, hidden)
        self._entity_grid_hidden = hidden

    def _refresh_entity_grid(self, view_id: str) -> None:
        hidden = read_hidden_entity_columns(QSettings("rcm2", "desktop"), view_id)
        if (
            view_id == self._entity_grid_view_id
            and hidden == self._entity_grid_hidden
            and self._entity_grid_panel.table_model() is not None
        ):
            return
        session = self._project_session()
        if session is None:
            self._entity_grid_panel.detach()
            self._entity_grid_view_id = None
            self._entity_grid_hidden = frozenset()
            return
        project = wss.editing_project(session)
        host = self._editing_host
        shared = host.ensure_grid(project)
        entity_svc = EntityEditService.for_view(
            view_id,
            changed=self._on_entity_grid_changed,
        )
        entity_svc.attach_editing_session(shared.editing_session)
        self._entity_grid_panel.attach(
            entity_svc,
            project,
            view_id=view_id,
            hidden_columns=hidden,
        )
        self._entity_grid_panel.set_scope(self._pbs_scope_id, project)
        self._entity_grid_view_id = view_id
        self._entity_grid_hidden = hidden

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
        if host.is_grid_dirty() and grid_svc.error_count() == 0:
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
        refresh_fm_inspector(self, fm_id)

    def _apply_fm_inspector_view(self, view: FMVerificationView) -> None:
        apply_fm_inspector_view(self, view)

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
        self._sync_lcc_axis_labels(snapshot)
        self._lcc_table_model = LCCYearTableModel(buckets)
        self.lcc_table_view.setModel(self._lcc_table_model)
        self.lcc_empty_state_label.setVisible(False)
        self._sync_lcc_chrome(snapshot)
        self._render_lcc_year_detail(session, run_result, snapshot, planning_curve=curve)

    def _sync_lcc_chrome(self, snapshot: WorkspaceStateSnapshot) -> None:
        session = self._project_session()
        snapshot = self.workspace_state.snapshot()
        overlay = snapshot.planning_overlay
        active = overlay.active
        year_selected = snapshot.lcc_calendar_year is not None
        whatif_blocker = self.lcc_whatif_button.blockSignals(True)
        try:
            self.lcc_whatif_button.setChecked(active)
        finally:
            self.lcc_whatif_button.blockSignals(whatif_blocker)
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

    def _ensure_whatif_for_meekoppel(self) -> None:
        ensure_whatif_for_meekoppel(self)

    def _clear_meekoppel_preview_gate(self) -> None:
        clear_meekoppel_preview_gate(self)

    def _sync_meekoppel_panel(self, snapshot: WorkspaceStateSnapshot) -> None:
        bind_meekoppel_panel(self, snapshot)

    def _on_meekoppel_anchor_changed(self, _button) -> None:
        on_meekoppel_anchor_changed(self, _button)

    def _on_meekoppel_window_changed(self, _value: int) -> None:
        on_meekoppel_window_changed(self, _value)

    def _on_meekoppel_preview(self) -> None:
        on_meekoppel_preview(self)

    def _on_meekoppel_apply(self) -> None:
        on_meekoppel_apply(self)

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
            type_filters=effective_lcc_filters(snapshot),
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
        ui_filters = self._lcc_filters_from_ui()
        plan = self._last_lcc_toolbar_plan
        if plan is not None and not plan.cm_filter_visible:
            ui_filters = LCCTypeFilterSet(
                cm=self.workspace_state.snapshot().lcc_filters.cm,
                rev=ui_filters.rev,
                in_task=ui_filters.in_task,
                tst=ui_filters.tst,
                svo=ui_filters.svo,
                wet=ui_filters.wet,
            )
        self.workspace_state.set_lcc_filters(ui_filters)

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

    def _sync_lcc_axis_labels(self, snapshot: WorkspaceStateSnapshot) -> None:
        from rcm_desktop.adapter.lcc_plot_axis_labels import lcc_plot_axis_labels

        pres = snapshot.contribution_presentation
        x_label, y_label = lcc_plot_axis_labels(
            snapshot.metric,
            unavailability_display=pres.unavailability_display,
        )
        self.lcc_chart_widget.set_axis_labels(x_label=x_label, y_label=y_label)
        for col in getattr(self, "_compare_lcc_columns", ()) or ():
            chart = col.get("chart")
            if chart is not None:
                chart.set_axis_labels(x_label=x_label, y_label=y_label)

    def _bind_bijdragen_view(
        self,
        bijdragen_view,
        snapshot: WorkspaceStateSnapshot,
    ) -> None:
        rows = bijdragen_view.contribution_rows
        self.bijdragen_chart_widget.set_display_context(
            snapshot.metric,
            snapshot.contribution_presentation,
        )
        self.bijdragen_chart_widget.set_rows(rows)
        self.bijdragen_chart_label.setVisible(len(rows) == 0)

    def _clear_detail_zone(self) -> None:
        self._fm_table_filter_proxy.setSourceModel(None)
        self.detail_empty_state_label.setVisible(True)
        self._refresh_fm_inspector(None)
        self.bijdragen_chart_widget.set_rows(())
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

        outcome = persist_wizard_result(
            wizard,
            Path(save_path),
            source_workbook_path=Path(excel_path),
        )
        if outcome.kind == "blocked":
            if outcome.validate_result is not None:
                self._state.set_last_result(outcome.validate_result)
            failure = outcome.failure
            message = failure.message if failure is not None else messages.ISOGRAPH_IMPORT_VALIDATION_FAILED
            QMessageBox.critical(self, messages.ERROR_DIALOG_TITLE, message)
            return

        assert outcome.success is not None
        self._apply_import_success(outcome.success)

    def _open_portfolio_wizard(self) -> None:
        result = run_portfolio_wizard_with_root_picker(parent=self)
        if result is None:
            return

        default_name = result.project.projectnaam.strip().replace(" ", "_") or "portfolio"
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            messages.PORTFOLIO_SAVE_TITLE,
            str(Path.cwd() / f"{default_name}.rcm.json"),
            messages.PORTFOLIO_SAVE_FILTER,
        )
        if not save_path:
            return

        path = Path(save_path)
        if not path.name.endswith(".rcm.json"):
            stem = path.name[:-5] if path.name.endswith(".json") else path.name
            path = path.with_name(f"{stem}.rcm.json")

        persist_portfolio_wizard_result(result, path)

        self._suppress_path_change = True
        self.path_input.setText(str(path))
        self._suppress_path_change = False
        self._state.set_last_run(None)
        self._state.set_last_project(result.project)
        self._state.set_last_preview(build_project_preview(result.project))
        self._project_total_presentation = None
        self._clear_compare_slots()
        self.validate_summary_label.setText(
            messages.PORTFOLIO_SAVE_SUCCESS.format(path=path)
        )

        if result.warnings:
            QMessageBox.warning(
                self,
                messages.PORTFOLIO_WIZARD_TITLE,
                "; ".join(result.warnings),
            )

        self._start_validate()

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

    def _toggle_lcc_whatif_from_menu(self) -> None:
        if self.workspace_state.snapshot().modus != MODE_LCC:
            return
        self.lcc_whatif_button.toggle()

    def _set_compare_scenario(self, scenario_key: str | None) -> None:
        for index in range(self.compare_scenario_combo.count()):
            if self.compare_scenario_combo.itemData(index) == scenario_key:
                self.compare_scenario_combo.setCurrentIndex(index)
                return

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
        chart = column["chart"]
        chart.set_display_context(
            snapshot.metric,
            snapshot.contribution_presentation,
        )
        chart.set_rows(rows)
        column["placeholder"].setVisible(len(rows) == 0)
        column["chart"].setVisible(len(rows) > 0)

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
        self._update_report_menu_enabled()

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
            action = self._report_menu_action()
            if action is not None:
                action.setEnabled(False)
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
        self._update_parity_button_enabled()

    def _update_parity_button_enabled(self) -> None:
        if not hasattr(self, "rcm_cost_parity_button"):
            return
        session = self._project_session()
        run = self._state.last_run
        has_run = run is not None and run.status == "done" and bool(run.fm_core_results)
        has_bench = session is not None and has_aw_benchmarks(session.loaded.core())
        busy = self._run_runner.busy or self._compare_run_runner.busy
        self.rcm_cost_parity_button.setEnabled(has_run and has_bench and not busy)

    def _open_rcm_cost_parity(self) -> None:
        session = self._project_session()
        run = self._state.last_run
        if session is None or run is None or run.status != "done":
            QMessageBox.information(
                self,
                messages.RCM_COST_PARITY_TITLE,
                messages.RCM_COST_PARITY_NO_RUN,
            )
            return
        project = session.loaded.core()
        if not has_aw_benchmarks(project):
            QMessageBox.information(
                self,
                messages.RCM_COST_PARITY_TITLE,
                messages.RCM_COST_PARITY_NO_BENCHMARK,
            )
            return
        fm_results = {fmr.fm_id: fmr for fmr in run.fm_core_results}
        view = build_parity_view(project, fm_results)
        project_path = Path(session.path) if session.path else None
        show_rcm_cost_parity_dialog(
            view,
            project=project,
            fm_results=fm_results,
            project_path=project_path,
            parent=self,
        )

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

    def cancel_background_runners(self) -> None:
        cancel_window_background_runners(self)

    def _any_runner_busy(self) -> bool:
        return any_runner_busy(self)

    def _detach_table_models_before_close(self) -> None:
        detach_table_models_before_close(self)

    def _confirm_busy_shutdown(self) -> bool:
        return confirm_busy_shutdown(self)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        plan = plan_shutdown(
            grid_dirty=self._editing_host.is_grid_dirty(),
            busy=self._any_runner_busy(),
        )
        for step in plan.steps:
            if step is ShutdownStep.RESOLVE_GRID_DIRTY:
                resolution = resolve_grid_dirty_before_editor(
                    self, self._editing_host, context="shutdown"
                )
                if resolution == "cancel":
                    event.ignore()
                    return
            elif step is ShutdownStep.CONFIRM_BUSY_CANCEL:
                if not self._confirm_busy_shutdown():
                    event.ignore()
                    return
                self.cancel_background_runners()
                app = QApplication.instance()
                if app is not None:
                    for _ in range(200):
                        if not self._any_runner_busy():
                            break
                        app.processEvents()
            elif step is ShutdownStep.CLOSE:
                self._detach_table_models_before_close()
                event.accept()

    def _export_rcm_cost_workbook(self) -> None:
        session = self._project_session()
        if session is None:
            QMessageBox.information(
                self,
                messages.ERROR_DIALOG_TITLE,
                messages.MODEL_SETTINGS_NO_PROJECT,
            )
            return
        resolved = resolve_project_file_path(
            session_path=session.path,
            path_text=self.path_input.text(),
        )
        if resolved.file_path is None:
            QMessageBox.information(
                self,
                messages.ERROR_DIALOG_TITLE,
                messages.ERROR_EMPTY_PATH,
            )
            return
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            messages.ISOGRAPH_EXPORT_FILE_DIALOG_TITLE,
            str(resolved.file_path.with_suffix("").with_suffix(".export.xlsx")),
            messages.ISOGRAPH_OPEN_FILE_FILTER,
        )
        if not save_path:
            return
        outcome = export_rcm_cost_project(
            session.loaded.core(),
            project_file_path=resolved.file_path,
            output_path=Path(save_path),
        )
        if isinstance(outcome, ExportFlowBlocked):
            if outcome.code != "MISSING_SOURCE_WORKBOOK":
                QMessageBox.critical(self, messages.ERROR_DIALOG_TITLE, outcome.message)
                return
            located, _ = QFileDialog.getOpenFileName(
                self,
                messages.ISOGRAPH_EXPORT_MISSING_SOURCE_TITLE,
                str(resolved.file_path.parent),
                messages.ISOGRAPH_OPEN_FILE_FILTER,
            )
            if not located:
                return
            outcome = export_rcm_cost_project(
                session.loaded.core(),
                project_file_path=resolved.file_path,
                output_path=Path(save_path),
                located_source_path=Path(located),
            )
            if isinstance(outcome, ExportFlowBlocked):
                QMessageBox.critical(self, messages.ERROR_DIALOG_TITLE, outcome.message)
                return
        assert isinstance(outcome, ExportFlowSuccess)
        result = outcome.result
        QMessageBox.information(
            self,
            messages.ISOGRAPH_EXPORT_SUMMARY_TITLE,
            messages.ISOGRAPH_EXPORT_SUMMARY_BODY.format(
                patched=result.total_patched,
                added=result.total_added,
                warned=result.total_warned,
            ),
        )
