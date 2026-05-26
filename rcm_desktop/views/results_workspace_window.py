"""Nieuwe resultatenwerkruimte (slice 23 + slice 26).

Hoofdvenster met vaste PBS-sidebar links en resultatengebied rechts.
Analyse via één knop `Start analyse` / `Herbereken analyse` op het volledige
geladen project; presentatie-cache versnelt projecttotaal-modi.

Architectuur-discipline (zie AGENTS.md):
- Views consumeren Qt-vrije adapter-output; geen `rcm_core`-imports buiten
  typing-only.
- Presentatielogica (scope-filter, structuur-/totalen-boom, split-state) zit
  in `rcm_desktop.adapter.result_filter_service`,
  `rcm_desktop.adapter.result_view_service` en
  `rcm_desktop.adapter.workspace_split_layout`.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    QItemSelection,
    QItemSelectionModel,
    QModelIndex,
    QSortFilterProxyModel,
    Qt,
    Signal,
)
from PySide6.QtGui import QCloseEvent, QColor
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
from rcm_desktop.adapter.analysis_cache_service import (
    fm_cache_available,
    hydrate_run_from_cache,
)
from rcm_desktop.adapter.kpi_table_model import KPITableModel
from rcm_desktop.adapter.kpi_table_service import build_kpi_table
from rcm_desktop.adapter.presentation_cache_service import (
    PresentationProjectTotal,
    load_presentation_from_cache,
)
from rcm_desktop.adapter.lcc_warmup_runner import LCCWarmupRunner
from rcm_desktop.adapter.presentation_lazy_service import (
    default_lcc_warmup_snapshot,
    presentation_rebuild_needed_for_startup,
    warm_lcc_render_index,
)
from rcm_desktop.adapter.presentation_rebuild_runner import PresentationRebuildRunner
from rcm_desktop.adapter.run_runner import PHASE_MOTOR, PHASE_PRESENTATION, RunRunner
from rcm_desktop.adapter.contribution_table_model import ContributionTableModel
from rcm_desktop.adapter.fm_results_table_model import (
    FMResultsSortProxy,
    FMResultsTableModel,
    RAW_ROLE,
)
from rcm_desktop.adapter.fm_verification_service import (
    FMVerificationView,
    build_fm_verification_view,
)
from rcm_desktop.adapter.fm_verification_year_table_model import (
    FMVerificationYearTableModel,
)
from rcm_desktop.formatting import format_eur, format_float, format_int
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.workspace_view_service import (
    build_bijdragen_view,
    build_fm_detail_view,
    build_lcc_view,
)
from rcm_desktop.adapter.lcc_planning_service import (
    build_lcc_year_detail,
)
from rcm_desktop.adapter.lcc_detail_selection import rev_row_indices
from rcm_desktop.adapter.lcc_type_filter import LCCTypeFilterSet
from rcm_desktop.adapter.lcc_year_detail_table_model import (
    LCCYearDetailTableModel,
    PASSIVE_COLUMN,
)
from rcm_desktop.adapter.lcc_year_table_model import LCCYearTableModel
from rcm_desktop.adapter.planning_cm_preset_service import apply_cm_policy_preset
from rcm_desktop.adapter.import_flow_service import gate_workbook, persist_wizard_result
from rcm_desktop.adapter.isograph_open_flow_service import PersistImportSuccess
from rcm_desktop.adapter.meekoppel_panel_service import (
    apply_meekoppel,
    preview_meekoppel,
    sync_meekoppel_panel,
)
from rcm_desktop.adapter.meekoppel_suggestions_table_model import (
    MeekoppelSuggestionsTableModel,
)
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.planning_whatif_service import apply_overlay_shift
from rcm_desktop.adapter.pbs_results_tree_model import PBSResultsTreeModel
from rcm_desktop.adapter.rcm_navigation_tree_builder import build_rcm_navigation_tree
from rcm_desktop.adapter.rcm_navigation_tree_model import RcmNavigationTreeModel
from rcm_desktop.adapter.contribution_horizon_value_service import (
    calendar_years_for_project,
)
from rcm_desktop.adapter.faalwijzen_edit_service import FaalwijzenEditService
from rcm_desktop.adapter.faalwijzen_grid_registry import get_active_grid_service, set_active_grid_service
from rcm_desktop.views.fm_editor_dialog import FmEditorDialog
from rcm_desktop.views.validate_faalwijzen_panel import ValidateFaalwijzenPanel
from rcm_desktop.views.import_wizard_dialog import ImportDialogInput, run_import_wizard
from rcm_desktop.views.widgets.contribution_bar_chart import ContributionBarChartWidget
from rcm_desktop.views.widgets.lcc_stacked_bar_chart import LCCStackedBarChartWidget
from rcm_desktop.adapter.preview_service import build as build_project_preview
from rcm_desktop.adapter.project_paths import resolve_default_fixture_path
from rcm_desktop.adapter.result_view_service import (
    build_pbs_structure_tree,
    build_pbs_tree,
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
from rcm_desktop.adapter.workspace_detail_render_scope import (
    RenderSplitDepth,
    required_detail_builders,
    should_refresh_kpi_for_render_depth,
    workspace_detail_split_render_depth,
)
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

    def __init__(self) -> None:
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
        self.batch_faalwijzen_button = QPushButton(messages.WORKSPACE_MENU_FAALWIJZEN_BATCH)
        self.batch_faalwijzen_button.setToolTip(messages.WORKSPACE_MENU_FAALWIJZEN_BATCH)
        self.batch_faalwijzen_button.clicked.connect(self._open_batch_faalwijzen_grid)

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
        if project is not None:
            for year in calendar_years_for_project(project):
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
        filter_layout = QHBoxLayout(self.lcc_filter_bar)
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
        self.lcc_filter_bar.setVisible(False)
        page_layout.addWidget(self.lcc_filter_bar)

        self.lcc_overlay_status_label = QLabel("")
        self.lcc_overlay_status_label.setStyleSheet("color: #E65100; font-weight: 600;")
        page_layout.addWidget(self.lcc_overlay_status_label)

        self.meekoppel_panel = QWidget()
        meekoppel_layout = QVBoxLayout(self.meekoppel_panel)
        meekoppel_layout.setContentsMargins(0, 0, 0, 0)
        self.meekoppel_title_label = QLabel(messages.WORKSPACE_MEEKOPPEL_PANEL_TITLE)
        self.meekoppel_title_label.setStyleSheet("font-weight: 600;")
        meekoppel_layout.addWidget(self.meekoppel_title_label)
        self.meekoppel_help_label = QLabel(messages.WORKSPACE_MEEKOPPEL_PANEL_HELP)
        self.meekoppel_help_label.setWordWrap(True)
        self.meekoppel_help_label.setStyleSheet("color: #616161; font-size: 11px;")
        meekoppel_layout.addWidget(self.meekoppel_help_label)
        self.meekoppel_whatif_hint_label = QLabel(messages.WORKSPACE_MEEKOPPEL_WHATIF_HINT)
        self.meekoppel_whatif_hint_label.setWordWrap(True)
        self.meekoppel_whatif_hint_label.setStyleSheet("color: #757575;")
        meekoppel_layout.addWidget(self.meekoppel_whatif_hint_label)
        meekoppel_tb = QHBoxLayout()
        meekoppel_tb.addWidget(QLabel(messages.WORKSPACE_MEEKOPPEL_WINDOW_LABEL))
        self.meekoppel_window_spin = QSpinBox()
        self.meekoppel_window_spin.setRange(1, 5)
        self.meekoppel_window_spin.setValue(2)
        self.meekoppel_window_spin.valueChanged.connect(self._on_meekoppel_window_changed)
        meekoppel_tb.addWidget(self.meekoppel_window_spin)
        self.meekoppel_preview_button = QPushButton(messages.WORKSPACE_MEEKOPPEL_PREVIEW)
        self.meekoppel_preview_button.clicked.connect(self._on_meekoppel_preview)
        meekoppel_tb.addWidget(self.meekoppel_preview_button)
        self.meekoppel_apply_button = QPushButton(messages.WORKSPACE_MEEKOPPEL_APPLY)
        self.meekoppel_apply_button.clicked.connect(self._on_meekoppel_apply)
        meekoppel_tb.addWidget(self.meekoppel_apply_button)
        meekoppel_tb.addStretch(1)
        meekoppel_layout.addLayout(meekoppel_tb)
        self.meekoppel_empty_label = QLabel(messages.WORKSPACE_MEEKOPPEL_EMPTY)
        self.meekoppel_empty_label.setStyleSheet("color: #9E9E9E;")
        meekoppel_layout.addWidget(self.meekoppel_empty_label)
        self.meekoppel_table_view = QTableView()
        self.meekoppel_table_view.setAlternatingRowColors(True)
        self.meekoppel_table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.meekoppel_table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        _apply_workspace_data_table_header_policy(self.meekoppel_table_view.horizontalHeader())
        self._meekoppel_table_model = MeekoppelSuggestionsTableModel(parent=self.meekoppel_table_view)
        self.meekoppel_table_view.setModel(self._meekoppel_table_model)
        meekoppel_layout.addWidget(self.meekoppel_table_view, stretch=1)
        self.meekoppel_panel.setVisible(False)
        self._meekoppel_last_anchor: str = "later"
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

        # Legacy single-slot pane. Sinds issue 08 wordt deze codepath
        # uitsluitend nog gebruikt vóórdat het eerste scenario-slot gevuld is
        # (dus puur als empty-state-container); zodra de KPI-tabel een
        # scenario-run registreert schakelt de view automatisch over op de
        # split-view. De attribuut-namen blijven bestaan voor tests die de
        # data-pijplijn van vóór scenario-modus aanroepen.
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
        return page

    def _build_fm_detail_page(self) -> QWidget:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)

        self.fm_detail_splitter = QSplitter(Qt.Vertical)
        table_host = QWidget()
        table_layout = QVBoxLayout(table_host)
        table_layout.setContentsMargins(0, 0, 0, 0)
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
        self.pbs_tree_view.clicked.connect(self._on_pbs_tree_clicked)

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

    def _on_pbs_tree_clicked(self, proxy_index: QModelIndex) -> None:
        if not proxy_index.isValid():
            return
        source_index = self.pbs_proxy.mapToSource(proxy_index)
        source_model = self._pbs_source_model
        if source_model is None:
            return
        scope_id = self._pbs_scope_from_tree_index(source_model, source_index)
        if scope_id is None:
            return
        self.set_pbs_scope(scope_id)

    def _on_show_whole_project_clicked(self) -> None:
        self.set_pbs_scope(None)

    def set_pbs_scope(self, scope_id: str | None) -> None:
        """Stel de actieve PBS-scope in; detailzone volgt via workspace_state."""
        self._pbs_scope_id = scope_id
        self.workspace_state.set_scope(scope_id)
        self._update_scope_status_label()

    def _on_workspace_state_changed(self, snapshot: WorkspaceStateSnapshot) -> None:
        page = self._detail_pages.get(snapshot.modus, self.bijdragen_page)
        if self.detail_stack.currentWidget() is not page:
            self.detail_stack.setCurrentWidget(page)
        target_button = self.modus_buttons.get(snapshot.modus)
        if target_button is not None and not target_button.isChecked():
            target_button.setChecked(True)
        # Source toggle reflects current modus' sticky source.
        if snapshot.source == SOURCE_PBS and not self.source_toggle_pbs_button.isChecked():
            self.source_toggle_pbs_button.setChecked(True)
        elif (
            snapshot.source == SOURCE_FAALWIJZE
            and not self.source_toggle_faalwijze_button.isChecked()
        ):
            self.source_toggle_faalwijze_button.setChecked(True)
        # Metric combo reflects sticky metric.
        idx = self.metric_combo.findData(snapshot.metric)
        if idx >= 0 and idx != self.metric_combo.currentIndex():
            blocker = self.metric_combo.blockSignals(True)
            self.metric_combo.setCurrentIndex(idx)
            self.metric_combo.blockSignals(blocker)
        bijdragen_active = snapshot.modus == MODE_BIJDRAGEN
        self.top10_subbar.setVisible(bijdragen_active)
        pres = snapshot.contribution_presentation
        horizon_metric = snapshot.metric in (
            METRIC_FAALMOMENTEN,
            METRIC_NIET_BESCHIKBAARHEID,
        )
        self.horizon_lifecycle_button.setVisible(bijdragen_active and horizon_metric)
        self.horizon_per_year_button.setVisible(bijdragen_active and horizon_metric)
        year_combo_visible = (
            bijdragen_active and horizon_metric and pres.horizon == "per_year"
        )
        self.contribution_year_combo.setVisible(year_combo_visible)
        nb_toggle_visible = (
            bijdragen_active and snapshot.metric == METRIC_NIET_BESCHIKBAARHEID
        )
        self.nb_hours_button.setVisible(nb_toggle_visible)
        self.nb_percent_button.setVisible(nb_toggle_visible)
        if bijdragen_active and horizon_metric:
            if pres.horizon == "lifecycle":
                if not self.horizon_lifecycle_button.isChecked():
                    self.horizon_lifecycle_button.setChecked(True)
            elif not self.horizon_per_year_button.isChecked():
                self.horizon_per_year_button.setChecked(True)
        if nb_toggle_visible:
            if pres.unavailability_display == "hours":
                if not self.nb_hours_button.isChecked():
                    self.nb_hours_button.setChecked(True)
            elif not self.nb_percent_button.isChecked():
                self.nb_percent_button.setChecked(True)
        if year_combo_visible:
            year_data = pres.year_choice
            idx = self.contribution_year_combo.findData(year_data)
            if idx >= 0 and idx != self.contribution_year_combo.currentIndex():
                blocker = self.contribution_year_combo.blockSignals(True)
                self.contribution_year_combo.setCurrentIndex(idx)
                self.contribution_year_combo.blockSignals(blocker)
        lcc_active = snapshot.modus == MODE_LCC
        self.lcc_filter_bar.setVisible(lcc_active)
        self.lcc_show_all_years_button.setVisible(lcc_active)
        self.lcc_year_summary_label.setVisible(lcc_active)
        self.meekoppel_panel.setVisible(lcc_active)
        if lcc_active:
            self._sync_meekoppel_panel(snapshot)
        fm_active = snapshot.modus == MODE_FM_DETAIL
        self.fm_evident_filter_combo.setVisible(fm_active)
        self.fm_evident_filter_combo.setEnabled(fm_active)
        if hasattr(self, "fm_inspector_container"):
            self.fm_inspector_container.setVisible(fm_active)
            if not fm_active:
                self._refresh_fm_inspector(None)
        if lcc_active:
            self._sync_lcc_filter_checks(snapshot.lcc_filters)
        # KPI-tabel hangt af van actieve scope; refresh bij scope-wissel.
        split_depth = workspace_detail_split_render_depth(
            self._last_workspace_snapshot_for_split_depth,
            snapshot,
        )
        if should_refresh_kpi_for_render_depth(split_depth) and hasattr(self, "kpi_table_view"):
            self._refresh_kpi_table_view()
        self._sync_kpi_panel_visibility(snapshot)
        # Sync scope_id with the orchestrator (clicks set both, but reset paths only update state).
        if snapshot.scope_id != self._pbs_scope_id:
            self._pbs_scope_id = snapshot.scope_id
            self._update_scope_status_label()
        self._rerender_detail_for_current_scope(split_render_depth=split_depth)
        self._last_workspace_snapshot_for_split_depth = snapshot

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
        self.workspace_state.reset_for_new_project()
        self._seed_planning_overlay_from_import(project)
        self._sync_pbs_tree_for_state()
        self._rerender_detail_for_current_scope()
        self._refresh_kpi_table_view()
        self._update_run_buttons_enabled()
        self._update_scope_status_label()

    def _on_state_run_changed(self, run_result: object) -> None:
        self._sync_pbs_tree_for_state()
        self._rerender_detail_for_current_scope()
        self._refresh_kpi_table_view()
        if isinstance(run_result, RunResult) and run_result.error is not None:
            self._show_run_error(run_result.error)

    def _sync_pbs_tree_for_state(self) -> None:
        project = self._session_core()
        run_result = self._state.last_run
        if project is None:
            self._set_pbs_source_model(None, show_totals=False)
            return
        if isinstance(run_result, RunResult) and run_result.status == "done" and run_result.pbs_rows:
            roots = build_pbs_tree(list(run_result.pbs_rows))
            self._set_pbs_source_model(PBSResultsTreeModel(roots), show_totals=True)
            return
        if project.functies:
            nav_roots = build_rcm_navigation_tree(project)
            self._set_pbs_source_model(
                RcmNavigationTreeModel(nav_roots, project), show_totals=False
            )
            return
        roots = build_pbs_structure_tree(project)
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

    def _session_core(self):
        session = self._project_session()
        if session is None:
            return None
        return session.loaded.core()

    def _rerender_detail_for_current_scope(
        self,
        *,
        split_render_depth: RenderSplitDepth = "all_splits",
    ) -> None:
        session = self._project_session()
        snapshot = self.workspace_state.snapshot()

        if session is None or not session.has_completed_run():
            self._clear_detail_zone()
            return

        required = required_detail_builders(snapshot, split_render_depth)
        if split_render_depth == "all_splits":
            self._render_index.on_workspace_state_reset()

        modus = snapshot.modus
        if modus == MODE_FM_DETAIL and MODE_FM_DETAIL in required:
            fm_view = build_fm_detail_view(session, snapshot)
            if fm_view is not None:
                self._render_fm_rows(fm_view.fm_rows)
        elif modus == MODE_BIJDRAGEN and MODE_BIJDRAGEN in required:
            bijdragen_view = build_bijdragen_view(
                session,
                snapshot,
                render_index=self._render_index,
                project_total_presentation=self._project_total_presentation,
            )
            if bijdragen_view is not None:
                self._bind_bijdragen_view(bijdragen_view, snapshot)
        elif modus == MODE_LCC and MODE_LCC in required:
            lcc_view = build_lcc_view(
                session,
                snapshot,
                render_index=self._render_index,
                prev_snapshot=self._last_lcc_render_snapshot,
            )
            if lcc_view is not None:
                self._render_lcc_view(session, lcc_view, snapshot)

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

    def _open_batch_faalwijzen_grid(self) -> None:
        project = self._session_core()
        if project is None:
            QMessageBox.information(
                self,
                messages.WORKSPACE_MENU_FAALWIJZEN_BATCH,
                messages.WORKSPACE_FM_INSPECTOR_INPUTS_MISSING,
            )
            return
        grid_svc = get_active_grid_service()
        if grid_svc is None or not grid_svc.is_active():
            grid_svc = FaalwijzenEditService()
            grid_svc.reset(project)
            set_active_grid_service(grid_svc)
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
        if grid_svc.is_dirty() and grid_svc.error_count() == 0:
            built = grid_svc.materialize_for_run()
            self._state.set_last_project(built, path=self.path_input.text().strip() or None)

    def _on_fm_table_double_clicked(self, index: QModelIndex) -> None:
        if self.workspace_state.snapshot().modus != MODE_FM_DETAIL:
            return
        project = self._session_core()
        if project is None:
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
        if fm_key not in project.faalwijzes:
            QMessageBox.warning(
                self,
                messages.FM_EDITOR_VALIDATION_TITLE,
                messages.WORKSPACE_FM_INSPECTOR_INPUTS_MISSING,
            )
            return
        from rcm_desktop.adapter.dirty_session_coordinator import resolve_grid_dirty_before_editor
        from rcm_desktop.adapter.faalwijzen_grid_registry import get_active_grid_service

        if resolve_grid_dirty_before_editor(self) == "cancel":
            return
        path = self.path_input.text().strip() or None
        grid_svc = get_active_grid_service()
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
            self._state.set_last_project(result.project, path=path)
        if result.run_result is not None:
            self._state.set_last_run(result.run_result)
            self._load_presentation_cache()
            self._render_index.on_workspace_state_reset()
            self._rerender_detail_for_current_scope()
            self._refresh_fm_inspector(str(fm_id))

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
        project = self._session_core()
        fmr = self._fm_core_result_for_id(fm_id)
        if project is None or fmr is None:
            self.fm_inspector_empty_label.setVisible(True)
            self.fm_inspector_panel.setVisible(False)
            return
        view = build_fm_verification_view(project, fmr)
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
        project = session.loaded.core()
        run_result = session.run
        assert run_result is not None
        if scope == "detail_only":
            self.lcc_chart_widget.set_selected_year(snapshot.lcc_calendar_year)
            self._sync_lcc_chrome(snapshot)
            self._render_lcc_year_detail(project, run_result, snapshot, planning_curve=curve)
            return
        buckets = tuple(curve.display_buckets)
        self.lcc_chart_widget.set_buckets(buckets)
        self.lcc_chart_widget.set_selected_year(snapshot.lcc_calendar_year)
        self._lcc_table_model_legacy = LCCYearTableModel(buckets)
        self.lcc_table_view.setModel(self._lcc_table_model_legacy)
        self.lcc_empty_state_label.setVisible(False)
        self._sync_lcc_chrome(snapshot)
        self._render_lcc_year_detail(project, run_result, snapshot, planning_curve=curve)

    def _sync_lcc_chrome(self, snapshot: WorkspaceStateSnapshot) -> None:
        project = self._session_core()
        overlay = snapshot.planning_overlay
        active = overlay.active
        year_selected = snapshot.lcc_calendar_year is not None
        self.lcc_whatif_button.setChecked(active)
        self.lcc_reset_overlay_button.setEnabled(active)
        self.lcc_bulk_rev_passive_button.setEnabled(active and project is not None)
        self.lcc_cm_preset_button.setEnabled(active and project is not None)
        if project is not None and overlay.all_rev_passive(project):
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

    def _sync_meekoppel_panel(self, snapshot: WorkspaceStateSnapshot) -> None:
        panel = sync_meekoppel_panel(
            self._project_session(),
            snapshot,
            window_years=int(self.meekoppel_window_spin.value()),
        )
        self.meekoppel_whatif_hint_label.setVisible(panel.show_whatif_hint)
        self.meekoppel_window_spin.setEnabled(panel.window_spin_enabled)
        self.meekoppel_table_view.setVisible(panel.table_visible)
        self.meekoppel_preview_button.setEnabled(panel.preview_enabled)
        self.meekoppel_apply_button.setEnabled(panel.apply_enabled)
        self._meekoppel_table_model.set_rows(panel.rows)
        self.meekoppel_empty_label.setVisible(panel.show_empty_label)

    def _selected_meekoppel_group(self):
        selection = self.meekoppel_table_view.selectionModel()
        if selection is None or not selection.hasSelection():
            return None
        row = selection.selectedRows()[0].row()
        return self._meekoppel_table_model.row_at(row)

    def _meekoppel_preview_anchor(self) -> str:
        dialog = QDialog(self)
        dialog.setWindowTitle(messages.WORKSPACE_MEEKOPPEL_PREVIEW_TITLE)
        layout = QVBoxLayout(dialog)
        earlier = QRadioButton(messages.WORKSPACE_MEEKOPPEL_PREVIEW_ANCHOR_EARLIER)
        later = QRadioButton(messages.WORKSPACE_MEEKOPPEL_PREVIEW_ANCHOR_LATER)
        later.setChecked(True)
        layout.addWidget(earlier)
        layout.addWidget(later)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return ""
        anchor = "later" if later.isChecked() else "earlier"
        self._meekoppel_last_anchor = anchor
        return anchor

    def _on_meekoppel_window_changed(self, _value: int) -> None:
        snapshot = self.workspace_state.snapshot()
        if snapshot.modus == MODE_LCC:
            self._sync_meekoppel_panel(snapshot)

    def _on_meekoppel_preview(self) -> None:
        session = self._project_session()
        if session is None:
            return
        overlay = self.workspace_state.snapshot().planning_overlay
        if not overlay.active:
            return
        group = self._selected_meekoppel_group()
        if group is None:
            QMessageBox.warning(
                self,
                messages.LTAP_ERROR_DIALOG_TITLE,
                messages.WORKSPACE_MEEKOPPEL_SELECT_ROW,
            )
            return
        anchor = self._meekoppel_preview_anchor()
        if not anchor:
            return
        prev = preview_meekoppel(
            session, overlay, group, anchor=anchor  # type: ignore[arg-type]
        )
        if prev.blocked_reason:
            QMessageBox.information(
                self,
                messages.WORKSPACE_MEEKOPPEL_PREVIEW_TITLE,
                messages.WORKSPACE_MEEKOPPEL_PREVIEW_BLOCKED.format(reason=prev.blocked_reason),
            )
            return
        if not prev.moves:
            moves_text = messages.WORKSPACE_MEEKOPPEL_PREVIEW_NO_MOVES
        else:
            moves_text = "\n".join(
                messages.WORKSPACE_MEEKOPPEL_PREVIEW_MOVE_LINE.format(
                    pm_id=m.pm_id,
                    from_year=m.from_year,
                    to_year=m.to_year,
                    shift=m.shift_years,
                )
                for m in prev.moves
            )
        QMessageBox.information(
            self,
            messages.WORKSPACE_MEEKOPPEL_PREVIEW_TITLE,
            messages.WORKSPACE_MEEKOPPEL_PREVIEW_BODY.format(
                location=prev.path_label,
                pbs_id=prev.pbs_id,
                target=prev.target_year,
                moves=moves_text,
            ),
        )

    def _on_meekoppel_apply(self) -> None:
        session = self._project_session()
        if session is None:
            return
        overlay = self.workspace_state.snapshot().planning_overlay
        if not overlay.active:
            return
        group = self._selected_meekoppel_group()
        if group is None:
            QMessageBox.warning(
                self,
                messages.LTAP_ERROR_DIALOG_TITLE,
                messages.WORKSPACE_MEEKOPPEL_SELECT_ROW,
            )
            return
        result = apply_meekoppel(
            session,
            overlay,
            group,
            anchor=self._meekoppel_last_anchor,  # type: ignore[arg-type]
        )
        if result.error:
            QMessageBox.critical(self, messages.LTAP_ERROR_DIALOG_TITLE, result.error)
            return
        self.workspace_state.set_planning_overlay(result.overlay)
        self._sync_meekoppel_panel(self.workspace_state.snapshot())

    def _render_lcc_year_detail(
        self,
        project,
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
        detail = build_lcc_year_detail(
            project,
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
            self.workspace_state.set_planning_overlay(overlay.reset_overlay())

    def _on_lcc_reset_overlay(self) -> None:
        self._lcc_passive_kept_after_run = False
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

    def _sync_kpi_panel_visibility(self, snapshot: WorkspaceStateSnapshot) -> None:
        if not hasattr(self, "kpi_collapse_button"):
            return
        lcc_active = snapshot.modus == MODE_LCC
        self.kpi_collapse_button.setVisible(lcc_active)
        self.kpi_panel_title.setVisible(lcc_active)
        collapsed = snapshot.kpi_collapsed_in_lcc if lcc_active else False
        self.kpi_table_view.setVisible(not collapsed)
        self.kpi_collapse_button.setText("▼" if not collapsed else "▶")
        self.kpi_collapse_button.setEnabled(lcc_active)

    def _on_lcc_bulk_rev_toggle(self) -> None:
        project = self._session_core()
        if project is None:
            return
        overlay = self.workspace_state.snapshot().planning_overlay
        if not overlay.active:
            overlay = overlay.begin_what_if()
        if overlay.all_rev_passive(project):
            overlay = overlay.bulk_all_rev_active(project)
        else:
            overlay = overlay.bulk_all_rev_passive(project)
        self.workspace_state.set_planning_overlay(overlay)

    def _on_lcc_cm_policy_preset(self) -> None:
        project = self._session_core()
        if project is None:
            return
        overlay = self.workspace_state.snapshot().planning_overlay
        if not overlay.active:
            overlay = overlay.begin_what_if()
        self.workspace_state.set_planning_overlay(apply_cm_policy_preset(overlay, project))

    def _on_lcc_shift_selected(self) -> None:
        project = self._session_core()
        if project is None:
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
        result = apply_overlay_shift(
            project, overlay, pm_ids=pm_ids, shift_years=shift_years
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

    def _update_scope_status_label(self) -> None:
        if self._pbs_scope_id is None:
            self.scope_status_label.setText("Scope: hele project")
            return
        project = self._session_core()
        bouwdeel = ""
        if project is not None and self._pbs_scope_id in project.pbs_items:
            bouwdeel = project.pbs_items[self._pbs_scope_id].bouwdeel_naam
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
        project = self._session_core()
        if project is not None:
            default_modeljaar = int(project.config.modeljaar)

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

    def _start_analyse(self) -> None:
        path = self.path_input.text().strip()
        project = self._session_core()
        if project is None:
            return
        overlay = self.workspace_state.snapshot().planning_overlay
        path = self.path_input.text().strip()
        force = bool(
            project is not None
            and path
            and fm_cache_available(project, path)
        )
        if self._run_runner.start(
            project,
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
        plan = ResultsWorkspaceController.plan_after_successful_run(overlay)
        if overlay.active:
            self.workspace_state.set_planning_overlay(plan.overlay)
        if plan.had_passive_before_run:
            self._lcc_passive_kept_after_run = True
        if isinstance(presentation, PresentationProjectTotal):
            self._project_total_presentation = presentation
        else:
            self._load_presentation_cache()
        if plan.invalidate_render_index:
            self._render_index.on_workspace_state_reset()
        self._last_lcc_render_snapshot = None
        self._maybe_start_lcc_warmup()
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
        project = self._session_core()
        scope_id = self.workspace_state.snapshot().scope_id
        table = build_kpi_table(
            project=project,
            run_result=self._state.last_run,
            scope_id=scope_id,
        )
        self._kpi_table_model = KPITableModel(table)
        self.kpi_table_view.setModel(self._kpi_table_model)

    def _update_run_button_label(self) -> None:
        if not hasattr(self, "run_analyse_button"):
            return
        project = self._session_core()
        path = self.path_input.text().strip()
        if project is not None and path and fm_cache_available(project, path):
            self.run_analyse_button.setText(messages.WORKSPACE_RECOMPUTE_ANALYSE_BUTTON_LABEL)
        else:
            self.run_analyse_button.setText(messages.WORKSPACE_START_ANALYSE_BUTTON_LABEL)

    def _load_presentation_cache(self) -> None:
        project = self._session_core()
        path = self.path_input.text().strip()
        if project is None or not path:
            self._project_total_presentation = None
            return
        self._project_total_presentation = load_presentation_from_cache(project, path)

    def _maybe_start_presentation_rebuild(self) -> None:
        project = self._session_core()
        path = self.path_input.text().strip()
        run = self._state.last_run
        if (
            project is None
            or not path
            or not isinstance(run, RunResult)
            or run.status != "done"
            or not presentation_rebuild_needed_for_startup(project, path)
            or self._run_runner.busy
            or self._presentation_rebuild_runner.busy
        ):
            return
        self._presentation_rebuild_runner.start(project, path, run)

    def _maybe_start_lcc_warmup(self) -> None:
        project = self._session_core()
        run = self._state.last_run
        if (
            project is None
            or not isinstance(run, RunResult)
            or run.status != "done"
            or self._run_runner.busy
            or self._lcc_warmup_runner.busy
        ):
            return
        snapshot = default_lcc_warmup_snapshot(self.workspace_state.snapshot())
        self._lcc_warmup_runner.start(project, run, self._render_index, snapshot)

    def _after_project_validated(self, project: object) -> None:
        path = self.path_input.text().strip()
        if project is None or not path or not hasattr(project, "config"):
            return
        hydrated = hydrate_run_from_cache(project, path)
        if hydrated is not None:
            self._state.set_last_run(hydrated)
        self._load_presentation_cache()
        self._update_run_button_label()
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

    def _update_run_buttons_enabled(self) -> None:
        validation_ok = (
            self._state.last_result is not None
            and self._state.last_result.status in {"valid", "valid_with_warnings"}
        )
        busy = self._run_runner.busy or self._presentation_rebuild_runner.busy
        can_run = validation_ok and self._project_session() is not None and not busy
        if hasattr(self, "run_analyse_button"):
            self.run_analyse_button.setEnabled(can_run)

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
