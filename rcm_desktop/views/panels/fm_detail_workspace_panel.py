"""FM-detail-modus panel voor de resultatenwerkruimte (slice 62 PR2)."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableView,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from rcm_desktop.views.compare_slot_column import build_fm_compare_column
from rcm_desktop.views.widgets.faalwijze_compare_bar_chart import FaalwijzeCompareBarChartWidget

from rcm_desktop import messages
from rcm_desktop.adapter.fm_results_filter_policy import (
    FM_FILTER_BOOL_COLUMNS,
    FM_FILTER_NUMERIC_COLUMNS,
    FM_FILTER_TEXT_COLUMNS,
)
from rcm_desktop.adapter.fm_results_table_model import FMResultsSortProxy, RAW_ROLE
from rcm_desktop.adapter.table_column_filter_proxy import TableColumnFilterProxy
from rcm_desktop.views.panels.fm_results_filter_binding import build_fm_table_filter_row
from rcm_desktop.views.widgets.table_filter_row import TableFilterRowWidget


@dataclass
class FmDetailWorkspacePanel:
    page: QWidget
    fm_single_slot_pane: QWidget
    fm_compare_pane: QWidget
    fm_compare_toolbar: QWidget
    fm_compare_view_button_group: QButtonGroup
    fm_compare_table_view_button: QToolButton
    fm_compare_diagram_view_button: QToolButton
    fm_compare_nmf_rf_toggle: QToolButton
    fm_compare_columns_host: QWidget
    fm_compare_chart_scroll: QScrollArea
    fm_compare_chart: FaalwijzeCompareBarChartWidget
    fm_compare_col_a: dict
    fm_compare_col_b: dict
    fm_detail_splitter: QSplitter
    column_crop_button: QToolButton
    fm_table_filter_row: TableFilterRowWidget
    fm_filter_clear_button: QPushButton
    fm_filter_row_count_label: QLabel
    fm_table_view: QTableView
    fm_table_filter_proxy: TableColumnFilterProxy
    fm_table_proxy: FMResultsSortProxy
    detail_empty_state_label: QLabel
    fm_inspector_container: QWidget
    fm_inspector_empty_label: QLabel
    fm_inspector_panel: QWidget
    fm_inspector_identity_label: QLabel
    fm_inspector_lifecycle_label: QLabel
    fm_inspector_hash_label: QLabel
    fm_inspector_reconcile_label: QLabel
    fm_inspector_profile_missing_label: QLabel
    fm_inspector_year_table_view: QTableView


def build_fm_detail_workspace_panel() -> FmDetailWorkspacePanel:
    page = QWidget()
    page_layout = QVBoxLayout(page)
    page_layout.setContentsMargins(0, 0, 0, 0)

    fm_detail_splitter = QSplitter(Qt.Vertical)
    table_host = QWidget()
    table_layout = QVBoxLayout(table_host)
    table_layout.setContentsMargins(0, 0, 0, 0)
    fm_toolbar = QHBoxLayout()
    column_crop_button = QToolButton()
    column_crop_button.setText(messages.WORKSPACE_FM_COLUMN_CROP)
    column_crop_button.setToolTip(messages.WORKSPACE_FM_COLUMN_CROP_TOOLTIP)
    column_crop_button.setCheckable(True)
    fm_toolbar.addWidget(column_crop_button)
    fm_toolbar.addStretch(1)
    table_layout.addLayout(fm_toolbar)

    fm_table_view = QTableView()
    fm_table_view.setSortingEnabled(True)
    fm_table_view.setAlternatingRowColors(True)
    fm_table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
    fm_table_view.setSelectionMode(QAbstractItemView.SingleSelection)
    fm_table_filter_proxy = TableColumnFilterProxy(
        text_columns=FM_FILTER_TEXT_COLUMNS,
        bool_columns=FM_FILTER_BOOL_COLUMNS,
        numeric_columns=FM_FILTER_NUMERIC_COLUMNS,
        raw_role=RAW_ROLE,
    )
    fm_table_proxy = FMResultsSortProxy()
    fm_table_proxy.setSourceModel(fm_table_filter_proxy)
    fm_table_view.setModel(fm_table_proxy)

    fm_table_filter_row = build_fm_table_filter_row(table_host)
    table_layout.addWidget(fm_table_filter_row)

    filter_aux_row = QHBoxLayout()
    fm_filter_clear_button = QPushButton(messages.TABLE_FILTER_CLEAR)
    filter_aux_row.addWidget(fm_filter_clear_button)
    filter_aux_row.addStretch(1)
    fm_filter_row_count_label = QLabel("")
    filter_aux_row.addWidget(fm_filter_row_count_label)
    table_layout.addLayout(filter_aux_row)

    table_layout.addWidget(fm_table_view, stretch=1)
    detail_empty_state_label = QLabel(messages.WORKSPACE_DETAIL_EMPTY_STATE)
    detail_empty_state_label.setObjectName("MutedHintLabel")
    table_layout.addWidget(detail_empty_state_label)
    fm_detail_splitter.addWidget(table_host)

    fm_inspector_container = QWidget()
    inspector_layout = QVBoxLayout(fm_inspector_container)
    inspector_layout.setContentsMargins(4, 4, 4, 4)
    inspector_title = QLabel(messages.WORKSPACE_FM_INSPECTOR_TITLE)
    inspector_title.setStyleSheet("font-weight: bold;")
    inspector_layout.addWidget(inspector_title)
    fm_inspector_empty_label = QLabel(messages.WORKSPACE_FM_INSPECTOR_EMPTY)
    fm_inspector_empty_label.setObjectName("MutedHintLabel")
    inspector_layout.addWidget(fm_inspector_empty_label)
    fm_inspector_panel = QWidget()
    panel_layout = QVBoxLayout(fm_inspector_panel)
    panel_layout.setContentsMargins(0, 0, 0, 0)
    fm_inspector_identity_label = QLabel()
    fm_inspector_identity_label.setWordWrap(True)
    panel_layout.addWidget(fm_inspector_identity_label)
    fm_inspector_lifecycle_label = QLabel()
    fm_inspector_lifecycle_label.setWordWrap(True)
    panel_layout.addWidget(fm_inspector_lifecycle_label)
    fm_inspector_hash_label = QLabel()
    fm_inspector_hash_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
    panel_layout.addWidget(fm_inspector_hash_label)
    fm_inspector_reconcile_label = QLabel()
    fm_inspector_reconcile_label.setWordWrap(True)
    panel_layout.addWidget(fm_inspector_reconcile_label)
    fm_inspector_profile_missing_label = QLabel()
    fm_inspector_profile_missing_label.setWordWrap(True)
    fm_inspector_profile_missing_label.setStyleSheet("color: #E65100;")
    panel_layout.addWidget(fm_inspector_profile_missing_label)
    fm_inspector_year_table_view = QTableView()
    fm_inspector_year_table_view.setAlternatingRowColors(True)
    fm_inspector_year_table_view.setToolTip(
        messages.WORKSPACE_FM_INSPECTOR_FAALMOMENTEN_PROXY_TOOLTIP
    )
    fm_inspector_year_table_view.horizontalHeader().setStretchLastSection(True)
    panel_layout.addWidget(fm_inspector_year_table_view, stretch=1)
    inspector_layout.addWidget(fm_inspector_panel)
    fm_inspector_panel.setVisible(False)
    fm_inspector_container.setVisible(False)
    fm_detail_splitter.addWidget(fm_inspector_container)
    fm_detail_splitter.setStretchFactor(0, 2)
    fm_detail_splitter.setStretchFactor(1, 1)

    fm_single_slot_pane = QWidget()
    single_layout = QVBoxLayout(fm_single_slot_pane)
    single_layout.setContentsMargins(0, 0, 0, 0)
    single_layout.addWidget(fm_detail_splitter, stretch=1)

    fm_compare_pane = QWidget()
    compare_layout = QVBoxLayout(fm_compare_pane)
    compare_layout.setContentsMargins(0, 0, 0, 0)
    fm_compare_toolbar = QWidget(fm_compare_pane)
    compare_toolbar_layout = QHBoxLayout(fm_compare_toolbar)
    compare_toolbar_layout.setContentsMargins(0, 0, 0, 0)
    fm_compare_view_button_group = QButtonGroup(fm_compare_toolbar)
    fm_compare_view_button_group.setExclusive(True)
    fm_compare_table_view_button = QToolButton(fm_compare_toolbar)
    fm_compare_table_view_button.setText(messages.WORKSPACE_FM_COMPARE_VIEW_TABLE)
    fm_compare_table_view_button.setToolTip(messages.WORKSPACE_FM_COMPARE_VIEW_TOOLTIP)
    fm_compare_table_view_button.setCheckable(True)
    fm_compare_table_view_button.setChecked(True)
    fm_compare_diagram_view_button = QToolButton(fm_compare_toolbar)
    fm_compare_diagram_view_button.setText(messages.WORKSPACE_FM_COMPARE_VIEW_DIAGRAM)
    fm_compare_diagram_view_button.setToolTip(messages.WORKSPACE_FM_COMPARE_VIEW_TOOLTIP)
    fm_compare_diagram_view_button.setCheckable(True)
    fm_compare_view_button_group.addButton(fm_compare_table_view_button)
    fm_compare_view_button_group.addButton(fm_compare_diagram_view_button)
    compare_toolbar_layout.addWidget(fm_compare_table_view_button)
    compare_toolbar_layout.addWidget(fm_compare_diagram_view_button)
    compare_toolbar_layout.addSpacing(12)
    fm_compare_nmf_rf_toggle = QToolButton(fm_compare_toolbar)
    fm_compare_nmf_rf_toggle.setText(messages.WORKSPACE_FM_COMPARE_NMF_RF)
    fm_compare_nmf_rf_toggle.setToolTip(messages.WORKSPACE_FM_COMPARE_NMF_RF_TOOLTIP)
    fm_compare_nmf_rf_toggle.setCheckable(True)
    compare_toolbar_layout.addWidget(fm_compare_nmf_rf_toggle)
    compare_toolbar_layout.addStretch(1)
    compare_layout.addWidget(fm_compare_toolbar)
    fm_compare_columns_host = QWidget(fm_compare_pane)
    compare_columns = QHBoxLayout(fm_compare_columns_host)
    compare_columns.setContentsMargins(0, 0, 0, 0)
    fm_compare_col_a = build_fm_compare_column(fm_compare_columns_host)
    fm_compare_col_b = build_fm_compare_column(fm_compare_columns_host)
    compare_columns.addWidget(fm_compare_col_a["host"], stretch=1)
    compare_columns.addWidget(fm_compare_col_b["host"], stretch=1)
    compare_layout.addWidget(fm_compare_columns_host, stretch=1)
    fm_compare_chart = FaalwijzeCompareBarChartWidget(fm_compare_pane)
    fm_compare_chart_scroll = QScrollArea(fm_compare_pane)
    fm_compare_chart_scroll.setWidgetResizable(False)
    fm_compare_chart_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    fm_compare_chart_scroll.setFrameShape(QScrollArea.NoFrame)
    fm_compare_chart_scroll.setWidget(fm_compare_chart)
    fm_compare_chart_scroll.setVisible(False)
    compare_layout.addWidget(fm_compare_chart_scroll, stretch=1)
    fm_compare_pane.setVisible(False)

    page_layout.addWidget(fm_single_slot_pane, stretch=1)
    page_layout.addWidget(fm_compare_pane, stretch=1)

    return FmDetailWorkspacePanel(
        page=page,
        fm_single_slot_pane=fm_single_slot_pane,
        fm_compare_pane=fm_compare_pane,
        fm_compare_toolbar=fm_compare_toolbar,
        fm_compare_view_button_group=fm_compare_view_button_group,
        fm_compare_table_view_button=fm_compare_table_view_button,
        fm_compare_diagram_view_button=fm_compare_diagram_view_button,
        fm_compare_nmf_rf_toggle=fm_compare_nmf_rf_toggle,
        fm_compare_columns_host=fm_compare_columns_host,
        fm_compare_chart_scroll=fm_compare_chart_scroll,
        fm_compare_chart=fm_compare_chart,
        fm_compare_col_a=fm_compare_col_a,
        fm_compare_col_b=fm_compare_col_b,
        fm_detail_splitter=fm_detail_splitter,
        column_crop_button=column_crop_button,
        fm_table_filter_row=fm_table_filter_row,
        fm_filter_clear_button=fm_filter_clear_button,
        fm_filter_row_count_label=fm_filter_row_count_label,
        fm_table_view=fm_table_view,
        fm_table_filter_proxy=fm_table_filter_proxy,
        fm_table_proxy=fm_table_proxy,
        detail_empty_state_label=detail_empty_state_label,
        fm_inspector_container=fm_inspector_container,
        fm_inspector_empty_label=fm_inspector_empty_label,
        fm_inspector_panel=fm_inspector_panel,
        fm_inspector_identity_label=fm_inspector_identity_label,
        fm_inspector_lifecycle_label=fm_inspector_lifecycle_label,
        fm_inspector_hash_label=fm_inspector_hash_label,
        fm_inspector_reconcile_label=fm_inspector_reconcile_label,
        fm_inspector_profile_missing_label=fm_inspector_profile_missing_label,
        fm_inspector_year_table_view=fm_inspector_year_table_view,
    )
