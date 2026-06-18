"""Pure mapping metric → LCC-plot aslabels (slice 85)."""

from __future__ import annotations

from typing import Literal

from rcm_desktop import messages
from rcm_desktop.adapter.results_workspace_state import (
    METRIC_FAALMOMENTEN,
    METRIC_KOSTEN,
    METRIC_NIET_BESCHIKBAARHEID,
)


def lcc_plot_axis_labels(
    metric: str,
    *,
    unavailability_display: Literal["hours", "percent"] = "hours",
) -> tuple[str, str]:
    x_label = messages.LCC_PLOT_AXIS_X_KALENDERJAREN
    if metric == METRIC_FAALMOMENTEN:
        return x_label, messages.LCC_PLOT_AXIS_Y_FAALMOMENTEN
    if metric == METRIC_NIET_BESCHIKBAARHEID:
        if unavailability_display == "percent":
            return x_label, messages.LCC_PLOT_AXIS_Y_NB_PERCENT
        return x_label, messages.LCC_PLOT_AXIS_Y_NB_HOURS
    if metric == METRIC_KOSTEN:
        return x_label, messages.LCC_PLOT_AXIS_Y_KOSTEN
    return x_label, ""
