"""One A/B compare column (chart + table + header) for the werkruimte."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QTableView, QVBoxLayout, QWidget

from rcm_desktop import messages
from rcm_desktop.views.widgets.contribution_bar_chart import ContributionBarChartWidget
from rcm_desktop.views.widgets.lcc_stacked_bar_chart import LCCStackedBarChartWidget


def build_bijdragen_compare_column(parent: QWidget | None = None) -> dict[str, QWidget]:
    host = QWidget(parent)
    layout = QVBoxLayout(host)
    layout.setContentsMargins(0, 0, 0, 0)
    header = QLabel("")
    header.setStyleSheet("font-weight: 600;")
    placeholder = QLabel("")
    placeholder.setStyleSheet("color: #9E9E9E;")
    placeholder.setWordWrap(True)
    chart = ContributionBarChartWidget(host)
    layout.addWidget(header)
    layout.addWidget(placeholder)
    layout.addWidget(chart, stretch=1)
    return {
        "host": host,
        "header": header,
        "placeholder": placeholder,
        "chart": chart,
    }


def build_lcc_compare_column(parent: QWidget | None = None) -> dict[str, QWidget]:
    host = QWidget(parent)
    layout = QVBoxLayout(host)
    layout.setContentsMargins(0, 0, 0, 0)
    header = QLabel("")
    header.setStyleSheet("font-weight: 600;")
    placeholder = QLabel("")
    placeholder.setStyleSheet("color: #9E9E9E;")
    placeholder.setWordWrap(True)
    chart = LCCStackedBarChartWidget(host)
    table = QTableView(host)
    table.setAlternatingRowColors(True)
    layout.addWidget(header)
    layout.addWidget(placeholder)
    layout.addWidget(chart, stretch=2)
    layout.addWidget(table, stretch=1)
    return {
        "host": host,
        "header": header,
        "placeholder": placeholder,
        "chart": chart,
        "table": table,
    }


def set_compare_placeholder(column: dict[str, QWidget], *, slot_key: str) -> None:
    column["placeholder"].setText(
        messages.WORKSPACE_COMPARE_SLOT_PLACEHOLDER.format(slot=slot_key)
    )
    column["placeholder"].setVisible(True)
    column["chart"].setVisible(False)
    if "table" in column:
        column["table"].setVisible(False)
