"""Gedeelde Top-10 / LCC / FM sub-balk (slice 62 follow-up)."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QToolButton,
    QWidget,
)

from rcm_desktop import messages
from rcm_desktop.adapter.results_workspace_state import (
    ALL_METRICS,
    METRIC_FAALMOMENTEN,
    METRIC_KOSTEN,
    METRIC_NIET_BESCHIKBAARHEID,
)
from rcm_desktop.views.widgets.nb_effect_filter_combo import NbEffectFilterCombo


@dataclass
class Top10SubbarPanel:
    widget: QWidget
    metric_combo: QComboBox
    nb_effect_filter_combo: NbEffectFilterCombo
    horizon_button_group: QButtonGroup
    horizon_lifecycle_button: QToolButton
    horizon_per_year_button: QToolButton
    contribution_year_combo: QComboBox
    nb_display_button_group: QButtonGroup
    nb_hours_button: QToolButton
    nb_percent_button: QToolButton


def build_top10_subbar_panel(parent: QWidget | None = None) -> Top10SubbarPanel:
    widget = QWidget(parent)
    row = QHBoxLayout(widget)
    row.setContentsMargins(0, 0, 0, 0)
    row.addWidget(QLabel(messages.WORKSPACE_TOP10_SUBBAR_LABEL))

    metric_combo = QComboBox()
    metric_labels = {
        METRIC_FAALMOMENTEN: messages.WORKSPACE_METRIC_FAALMOMENTEN,
        METRIC_NIET_BESCHIKBAARHEID: messages.WORKSPACE_METRIC_NIET_BESCHIKBAARHEID,
        METRIC_KOSTEN: messages.WORKSPACE_METRIC_KOSTEN,
    }
    for metric_key in ALL_METRICS:
        metric_combo.addItem(metric_labels[metric_key], userData=metric_key)
    row.addWidget(metric_combo)

    nb_effect_filter_combo = NbEffectFilterCombo(widget)
    nb_effect_filter_combo.setToolTip(messages.WORKSPACE_NB_EFFECT_FILTER_TOOLTIP)
    row.addWidget(nb_effect_filter_combo, stretch=1)
    row.addSpacing(12)

    horizon_button_group = QButtonGroup(widget)
    horizon_button_group.setExclusive(True)
    horizon_lifecycle_button = QToolButton()
    horizon_lifecycle_button.setText(messages.WORKSPACE_CONTRIBUTION_HORIZON_LIFECYCLE)
    horizon_lifecycle_button.setCheckable(True)
    horizon_lifecycle_button.setToolTip(messages.WORKSPACE_CONTRIBUTION_HORIZON_TOOLTIP)
    horizon_per_year_button = QToolButton()
    horizon_per_year_button.setText(messages.WORKSPACE_CONTRIBUTION_HORIZON_PER_YEAR)
    horizon_per_year_button.setCheckable(True)
    horizon_per_year_button.setChecked(True)
    horizon_per_year_button.setToolTip(messages.WORKSPACE_CONTRIBUTION_HORIZON_TOOLTIP)
    horizon_button_group.addButton(horizon_lifecycle_button)
    horizon_button_group.addButton(horizon_per_year_button)
    row.addWidget(horizon_lifecycle_button)
    row.addWidget(horizon_per_year_button)

    contribution_year_combo = QComboBox()
    contribution_year_combo.addItem(
        messages.WORKSPACE_CONTRIBUTION_YEAR_AVERAGE,
        userData="average",
    )
    contribution_year_combo.setToolTip(messages.WORKSPACE_CONTRIBUTION_YEAR_AVERAGE_TOOLTIP)
    row.addWidget(contribution_year_combo)

    nb_display_button_group = QButtonGroup(widget)
    nb_display_button_group.setExclusive(True)
    nb_hours_button = QToolButton()
    nb_hours_button.setText(messages.WORKSPACE_CONTRIBUTION_NB_HOURS)
    nb_hours_button.setCheckable(True)
    nb_hours_button.setChecked(True)
    nb_percent_button = QToolButton()
    nb_percent_button.setText(messages.WORKSPACE_CONTRIBUTION_NB_PERCENT)
    nb_percent_button.setCheckable(True)
    nb_percent_button.setToolTip(messages.WORKSPACE_CONTRIBUTION_NB_PERCENT_TOOLTIP)
    nb_display_button_group.addButton(nb_hours_button)
    nb_display_button_group.addButton(nb_percent_button)
    row.addWidget(nb_hours_button)
    row.addWidget(nb_percent_button)
    row.addStretch(1)

    return Top10SubbarPanel(
        widget=widget,
        metric_combo=metric_combo,
        nb_effect_filter_combo=nb_effect_filter_combo,
        horizon_button_group=horizon_button_group,
        horizon_lifecycle_button=horizon_lifecycle_button,
        horizon_per_year_button=horizon_per_year_button,
        contribution_year_combo=contribution_year_combo,
        nb_display_button_group=nb_display_button_group,
        nb_hours_button=nb_hours_button,
        nb_percent_button=nb_percent_button,
    )
