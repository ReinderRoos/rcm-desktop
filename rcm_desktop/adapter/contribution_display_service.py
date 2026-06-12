"""Qt-vrije formattering voor Bijdragen-waarden (slice 72 display-seam)."""

from __future__ import annotations

from rcm_desktop.adapter.results_workspace_state import (
    ContributionPresentation,
    METRIC_FAALMOMENTEN,
    METRIC_KOSTEN,
    METRIC_NIET_BESCHIKBAARHEID,
)
from rcm_desktop.formatting import format_eur, format_float, format_int


def format_contribution_value(
    value: float,
    metric: str,
    presentation: ContributionPresentation,
) -> str:
    """Formatteer een bijdrage-waarde voor metric + NB-weergave."""
    if metric == METRIC_KOSTEN:
        return format_eur(value)
    if metric == METRIC_FAALMOMENTEN:
        return format_int(int(round(value)))
    if metric == METRIC_NIET_BESCHIKBAARHEID:
        if presentation.unavailability_display == "hours":
            return f"{format_float(value)} h"
        return f"{format_float(value, decimals=4)} %"
    return format_float(value)


def format_contribution_bar_annotation(
    value: float,
    metric: str,
    presentation: ContributionPresentation,
) -> str:
    """Compacte waarde-string voor staaflabels in het Top 10-diagram."""
    return format_contribution_value(value, metric, presentation)
