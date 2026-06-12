"""Bijdragen-modus panel voor de resultatenwerkruimte (slice 62 PR1)."""



from __future__ import annotations



from dataclasses import dataclass



from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget



from rcm_desktop import messages

from rcm_desktop.views.compare_slot_column import build_bijdragen_compare_column

from rcm_desktop.views.widgets.contribution_bar_chart import ContributionBarChartWidget





@dataclass

class BijdragenWorkspacePanel:

    page: QWidget

    chart_label: QLabel

    single_slot_pane: QWidget

    chart_widget: ContributionBarChartWidget

    compare_pane: QWidget

    compare_col_a: dict[str, QWidget]

    compare_col_b: dict[str, QWidget]





def build_bijdragen_workspace_panel() -> BijdragenWorkspacePanel:

    page = QWidget()

    page_layout = QVBoxLayout(page)

    page_layout.setContentsMargins(0, 0, 0, 0)



    chart_label = QLabel(messages.WORKSPACE_BIJDRAGE_EMPTY_STATE)

    chart_label.setStyleSheet("color: #9E9E9E;")

    page_layout.addWidget(chart_label)



    single_slot_pane = QWidget()

    single_layout = QVBoxLayout(single_slot_pane)

    single_layout.setContentsMargins(0, 0, 0, 0)

    chart_widget = ContributionBarChartWidget()

    single_layout.addWidget(chart_widget, stretch=1)

    page_layout.addWidget(single_slot_pane, stretch=1)



    compare_pane = QWidget()

    compare_layout = QHBoxLayout(compare_pane)

    compare_layout.setContentsMargins(0, 0, 0, 0)

    compare_col_a = build_bijdragen_compare_column(compare_pane)

    compare_col_b = build_bijdragen_compare_column(compare_pane)

    compare_layout.addWidget(compare_col_a["host"], stretch=1)

    compare_layout.addWidget(compare_col_b["host"], stretch=1)

    compare_pane.setVisible(False)

    page_layout.addWidget(compare_pane, stretch=1)



    return BijdragenWorkspacePanel(

        page=page,

        chart_label=chart_label,

        single_slot_pane=single_slot_pane,

        chart_widget=chart_widget,

        compare_pane=compare_pane,

        compare_col_a=compare_col_a,

        compare_col_b=compare_col_b,

    )

