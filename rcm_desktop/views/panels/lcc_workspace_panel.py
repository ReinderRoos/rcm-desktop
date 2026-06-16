"""LCC-modus panel voor de resultatenwerkruimte (slice 62 PR3)."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTableView,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from rcm_desktop import messages
from rcm_desktop.adapter.lcc_year_detail_table_model import LCCYearDetailTableModel
from rcm_desktop.adapter.meekoppel_suggestions_table_model import (
    MeekoppelSuggestionsTableModel,
)
from rcm_desktop.views.compare_slot_column import build_lcc_compare_column
from rcm_desktop.views.panels.workspace_table_policy import (
    apply_workspace_data_table_header_policy,
)
from rcm_desktop.views.widgets.lcc_stacked_bar_chart import LCCStackedBarChartWidget


@dataclass
class LccWorkspacePanel:
    page: QWidget
    lcc_empty_state_label: QLabel
    lcc_filter_bar: QWidget
    lcc_whatif_collapse_button: QToolButton
    lcc_whatif_bar_title: QLabel
    lcc_whatif_content: QWidget
    lcc_filter_checks: dict[str, QCheckBox]
    lcc_whatif_button: QPushButton
    lcc_reset_overlay_button: QPushButton
    lcc_bulk_rev_passive_button: QPushButton
    lcc_cm_preset_button: QPushButton
    lcc_overlay_status_label: QLabel
    meekoppel_panel: QWidget
    meekoppel_collapse_button: QToolButton
    meekoppel_title_label: QLabel
    meekoppel_content: QWidget
    meekoppel_help_label: QLabel
    meekoppel_whatif_hint_label: QLabel
    meekoppel_selection_summary_label: QLabel
    meekoppel_window_spin: QSpinBox
    meekoppel_anchor_earlier: QRadioButton
    meekoppel_anchor_later: QRadioButton
    meekoppel_anchor_group: QButtonGroup
    meekoppel_preview_button: QPushButton
    meekoppel_apply_button: QPushButton
    meekoppel_empty_label: QLabel
    meekoppel_table_view: QTableView
    meekoppel_table_model: MeekoppelSuggestionsTableModel
    lcc_year_summary_label: QLabel
    lcc_show_all_years_button: QPushButton
    lcc_detail_toolbar: QWidget
    lcc_shift_selection_hint: QLabel
    lcc_select_rev_button: QPushButton
    lcc_shift_spin: QSpinBox
    lcc_shift_button: QPushButton
    lcc_single_slot_pane: QWidget
    lcc_chart_widget: LCCStackedBarChartWidget
    lcc_table_view: QTableView
    lcc_detail_table_view: QTableView
    lcc_detail_model: LCCYearDetailTableModel
    lcc_compare_pane: QWidget
    lcc_compare_col_a: dict[str, QWidget]
    lcc_compare_col_b: dict[str, QWidget]


def build_lcc_workspace_panel() -> LccWorkspacePanel:
    page = QWidget()
    page_layout = QVBoxLayout(page)
    page_layout.setContentsMargins(0, 0, 0, 0)

    lcc_empty_state_label = QLabel(messages.WORKSPACE_LCC_EMPTY_STATE)
    lcc_empty_state_label.setObjectName("MutedHintLabel")
    lcc_empty_state_label.setVisible(True)
    page_layout.addWidget(lcc_empty_state_label)

    lcc_filter_bar = QWidget()
    filter_bar_layout = QVBoxLayout(lcc_filter_bar)
    filter_bar_layout.setContentsMargins(0, 0, 0, 0)
    filter_bar_layout.setSpacing(2)
    whatif_header = QHBoxLayout()
    lcc_whatif_collapse_button = QToolButton()
    lcc_whatif_collapse_button.setToolTip(messages.WORKSPACE_LCC_WHATIF_COLLAPSE_TOOLTIP)
    lcc_whatif_bar_title = QLabel(messages.WORKSPACE_LCC_WHATIF_BAR_TITLE)
    lcc_whatif_bar_title.setStyleSheet("font-weight: 600;")
    whatif_header.addWidget(lcc_whatif_collapse_button)
    whatif_header.addWidget(lcc_whatif_bar_title)
    whatif_header.addStretch(1)
    filter_bar_layout.addLayout(whatif_header)
    lcc_whatif_content = QWidget()
    filter_layout = QHBoxLayout(lcc_whatif_content)
    filter_layout.setContentsMargins(0, 0, 0, 0)
    lcc_filter_checks: dict[str, QCheckBox] = {}
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
        lcc_filter_checks[key] = box
        filter_layout.addWidget(box)
    filter_layout.addStretch(1)
    lcc_whatif_button = QPushButton(messages.WORKSPACE_LCC_WHAT_IF_TOGGLE)
    lcc_whatif_button.setCheckable(True)
    filter_layout.addWidget(lcc_whatif_button)
    lcc_reset_overlay_button = QPushButton(messages.WORKSPACE_LCC_RESET_OVERLAY)
    filter_layout.addWidget(lcc_reset_overlay_button)
    lcc_bulk_rev_passive_button = QPushButton(messages.WORKSPACE_LCC_BULK_REV_PASSIVE)
    filter_layout.addWidget(lcc_bulk_rev_passive_button)
    lcc_cm_preset_button = QPushButton(messages.WORKSPACE_LCC_CM_POLICY_PRESET)
    lcc_cm_preset_button.setToolTip(messages.WORKSPACE_LCC_CM_PRESET_TOOLTIP)
    filter_layout.addWidget(lcc_cm_preset_button)
    filter_bar_layout.addWidget(lcc_whatif_content)

    meekoppel_panel = QWidget()
    meekoppel_layout = QVBoxLayout(meekoppel_panel)
    meekoppel_layout.setContentsMargins(0, 0, 0, 0)
    meekoppel_layout.setSpacing(2)
    meekoppel_header = QHBoxLayout()
    meekoppel_collapse_button = QToolButton()
    meekoppel_collapse_button.setToolTip(messages.WORKSPACE_MEEKOPPEL_COLLAPSE_TOOLTIP)
    meekoppel_title_label = QLabel(messages.WORKSPACE_MEEKOPPEL_PANEL_TITLE)
    meekoppel_title_label.setStyleSheet("font-weight: 600;")
    meekoppel_header.addWidget(meekoppel_collapse_button)
    meekoppel_header.addWidget(meekoppel_title_label)
    meekoppel_header.addStretch(1)
    meekoppel_layout.addLayout(meekoppel_header)
    meekoppel_content = QWidget()
    meekoppel_content_layout = QVBoxLayout(meekoppel_content)
    meekoppel_content_layout.setContentsMargins(0, 0, 0, 0)
    meekoppel_help_label = QLabel(messages.WORKSPACE_MEEKOPPEL_PANEL_HELP)
    meekoppel_help_label.setWordWrap(True)
    meekoppel_help_label.setObjectName("MutedHintLabel")
    meekoppel_content_layout.addWidget(meekoppel_help_label)
    meekoppel_whatif_hint_label = QLabel(messages.WORKSPACE_MEEKOPPEL_WHATIF_HINT)
    meekoppel_whatif_hint_label.setWordWrap(True)
    meekoppel_whatif_hint_label.setObjectName("MutedHintLabel")
    meekoppel_content_layout.addWidget(meekoppel_whatif_hint_label)
    meekoppel_selection_summary_label = QLabel("")
    meekoppel_selection_summary_label.setWordWrap(True)
    meekoppel_selection_summary_label.setObjectName("MutedHintLabel")
    meekoppel_selection_summary_label.setVisible(False)
    meekoppel_content_layout.addWidget(meekoppel_selection_summary_label)
    meekoppel_tb = QHBoxLayout()
    meekoppel_tb.addWidget(QLabel(messages.WORKSPACE_MEEKOPPEL_WINDOW_LABEL))
    meekoppel_window_spin = QSpinBox()
    meekoppel_window_spin.setRange(1, 5)
    meekoppel_window_spin.setValue(2)
    meekoppel_tb.addWidget(meekoppel_window_spin)
    meekoppel_anchor_earlier = QRadioButton(messages.WORKSPACE_MEEKOPPEL_ANCHOR_EARLIER)
    meekoppel_anchor_later = QRadioButton(messages.WORKSPACE_MEEKOPPEL_ANCHOR_LATER)
    meekoppel_anchor_later.setChecked(True)
    meekoppel_anchor_group = QButtonGroup(page)
    meekoppel_anchor_group.addButton(meekoppel_anchor_earlier)
    meekoppel_anchor_group.addButton(meekoppel_anchor_later)
    meekoppel_tb.addWidget(meekoppel_anchor_earlier)
    meekoppel_tb.addWidget(meekoppel_anchor_later)
    meekoppel_preview_button = QPushButton(messages.WORKSPACE_MEEKOPPEL_PREVIEW)
    meekoppel_tb.addWidget(meekoppel_preview_button)
    meekoppel_apply_button = QPushButton(messages.WORKSPACE_MEEKOPPEL_APPLY)
    meekoppel_tb.addWidget(meekoppel_apply_button)
    meekoppel_tb.addStretch(1)
    meekoppel_content_layout.addLayout(meekoppel_tb)
    meekoppel_empty_label = QLabel(messages.WORKSPACE_MEEKOPPEL_EMPTY)
    meekoppel_empty_label.setObjectName("MutedHintLabel")
    meekoppel_content_layout.addWidget(meekoppel_empty_label)
    meekoppel_table_view = QTableView()
    meekoppel_table_view.setAlternatingRowColors(True)
    meekoppel_table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
    meekoppel_table_view.setSelectionMode(QAbstractItemView.SingleSelection)
    apply_workspace_data_table_header_policy(meekoppel_table_view.horizontalHeader())
    meekoppel_table_model = MeekoppelSuggestionsTableModel(parent=meekoppel_table_view)
    meekoppel_table_view.setModel(meekoppel_table_model)
    meekoppel_content_layout.addWidget(meekoppel_table_view, stretch=1)
    meekoppel_layout.addWidget(meekoppel_content)
    meekoppel_panel.setVisible(False)
    filter_bar_layout.addWidget(meekoppel_panel)

    lcc_filter_bar.setVisible(False)
    page_layout.addWidget(lcc_filter_bar)

    lcc_overlay_status_label = QLabel("")
    lcc_overlay_status_label.setStyleSheet("color: #E65100; font-weight: 600;")
    page_layout.addWidget(lcc_overlay_status_label)

    lcc_year_summary_label = QLabel("")
    lcc_year_summary_label.setWordWrap(True)
    page_layout.addWidget(lcc_year_summary_label)

    lcc_show_all_years_button = QPushButton(messages.WORKSPACE_LCC_SHOW_ALL_YEARS)
    page_layout.addWidget(lcc_show_all_years_button)

    lcc_detail_toolbar = QWidget()
    detail_tb = QHBoxLayout(lcc_detail_toolbar)
    detail_tb.setContentsMargins(0, 0, 0, 0)
    lcc_shift_selection_hint = QLabel(messages.WORKSPACE_LCC_SHIFT_SELECTION_HINT)
    lcc_shift_selection_hint.setWordWrap(True)
    detail_tb.addWidget(lcc_shift_selection_hint, stretch=1)
    lcc_select_rev_button = QPushButton(messages.WORKSPACE_LCC_SELECT_REV_IN_YEAR)
    detail_tb.addWidget(lcc_select_rev_button)
    lcc_shift_spin = QSpinBox()
    lcc_shift_spin.setMinimum(-50)
    lcc_shift_spin.setMaximum(50)
    lcc_shift_spin.setToolTip(messages.WORKSPACE_LCC_SHIFT_SPIN_TOOLTIP)
    detail_tb.addWidget(lcc_shift_spin)
    lcc_shift_button = QPushButton(messages.WORKSPACE_LCC_SHIFT_SELECTED)
    detail_tb.addWidget(lcc_shift_button)
    detail_tb.addStretch(1)
    lcc_detail_toolbar.setVisible(False)
    page_layout.addWidget(lcc_detail_toolbar)

    lcc_single_slot_pane = QWidget()
    single_layout = QVBoxLayout(lcc_single_slot_pane)
    single_layout.setContentsMargins(0, 0, 0, 0)
    lcc_chart_widget = LCCStackedBarChartWidget()
    single_layout.addWidget(lcc_chart_widget, stretch=2)
    lcc_table_view = QTableView()
    lcc_table_view.setAlternatingRowColors(True)
    apply_workspace_data_table_header_policy(lcc_table_view.horizontalHeader())
    single_layout.addWidget(lcc_table_view, stretch=1)
    lcc_detail_table_view = QTableView()
    lcc_detail_table_view.setAlternatingRowColors(True)
    apply_workspace_data_table_header_policy(lcc_detail_table_view.horizontalHeader())
    single_layout.addWidget(lcc_detail_table_view, stretch=1)
    lcc_detail_model = LCCYearDetailTableModel(parent=lcc_detail_table_view)
    lcc_detail_table_view.setModel(lcc_detail_model)
    lcc_detail_table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
    lcc_detail_table_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
    page_layout.addWidget(lcc_single_slot_pane, stretch=1)

    lcc_compare_pane = QWidget()
    lcc_compare_layout = QVBoxLayout(lcc_compare_pane)
    lcc_compare_layout.setContentsMargins(0, 0, 0, 0)
    lcc_compare_col_a = build_lcc_compare_column(lcc_compare_pane)
    lcc_compare_col_b = build_lcc_compare_column(lcc_compare_pane)
    lcc_compare_layout.addWidget(lcc_compare_col_a["host"], stretch=1)
    lcc_compare_layout.addWidget(lcc_compare_col_b["host"], stretch=1)
    lcc_compare_pane.setVisible(False)
    page_layout.addWidget(lcc_compare_pane, stretch=1)

    return LccWorkspacePanel(
        page=page,
        lcc_empty_state_label=lcc_empty_state_label,
        lcc_filter_bar=lcc_filter_bar,
        lcc_whatif_collapse_button=lcc_whatif_collapse_button,
        lcc_whatif_bar_title=lcc_whatif_bar_title,
        lcc_whatif_content=lcc_whatif_content,
        lcc_filter_checks=lcc_filter_checks,
        lcc_whatif_button=lcc_whatif_button,
        lcc_reset_overlay_button=lcc_reset_overlay_button,
        lcc_bulk_rev_passive_button=lcc_bulk_rev_passive_button,
        lcc_cm_preset_button=lcc_cm_preset_button,
        lcc_overlay_status_label=lcc_overlay_status_label,
        meekoppel_panel=meekoppel_panel,
        meekoppel_collapse_button=meekoppel_collapse_button,
        meekoppel_title_label=meekoppel_title_label,
        meekoppel_content=meekoppel_content,
        meekoppel_help_label=meekoppel_help_label,
        meekoppel_whatif_hint_label=meekoppel_whatif_hint_label,
        meekoppel_selection_summary_label=meekoppel_selection_summary_label,
        meekoppel_window_spin=meekoppel_window_spin,
        meekoppel_anchor_earlier=meekoppel_anchor_earlier,
        meekoppel_anchor_later=meekoppel_anchor_later,
        meekoppel_anchor_group=meekoppel_anchor_group,
        meekoppel_preview_button=meekoppel_preview_button,
        meekoppel_apply_button=meekoppel_apply_button,
        meekoppel_empty_label=meekoppel_empty_label,
        meekoppel_table_view=meekoppel_table_view,
        meekoppel_table_model=meekoppel_table_model,
        lcc_year_summary_label=lcc_year_summary_label,
        lcc_show_all_years_button=lcc_show_all_years_button,
        lcc_detail_toolbar=lcc_detail_toolbar,
        lcc_shift_selection_hint=lcc_shift_selection_hint,
        lcc_select_rev_button=lcc_select_rev_button,
        lcc_shift_spin=lcc_shift_spin,
        lcc_shift_button=lcc_shift_button,
        lcc_single_slot_pane=lcc_single_slot_pane,
        lcc_chart_widget=lcc_chart_widget,
        lcc_table_view=lcc_table_view,
        lcc_detail_table_view=lcc_detail_table_view,
        lcc_detail_model=lcc_detail_model,
        lcc_compare_pane=lcc_compare_pane,
        lcc_compare_col_a=lcc_compare_col_a,
        lcc_compare_col_b=lcc_compare_col_b,
    )
