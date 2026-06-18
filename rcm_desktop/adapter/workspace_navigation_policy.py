"""Werkruimte-navigatiepolicy (slice 91): expliciete first-visit regels."""

from __future__ import annotations

from rcm_desktop.adapter.workspace_view_registry import (
    DEFAULT_VIEW_BY_SIDE,
    SIDE_INPUT,
    SIDE_OUTPUT,
)

INPUT_FAALWIJZEN_VIEW = "input.faalwijzen"


def resolve_view_for_side_switch(
    *,
    side: str,
    sticky_view_by_side: dict[str, str],
    first_input_visit_pending: bool,
) -> tuple[str, bool]:
    """Bepaal view bij zijde-wissel; markeer eerste Input-bezoek als afgehandeld."""
    if side == SIDE_INPUT and first_input_visit_pending:
        return INPUT_FAALWIJZEN_VIEW, False
    default = DEFAULT_VIEW_BY_SIDE.get(side, DEFAULT_VIEW_BY_SIDE[SIDE_OUTPUT])
    return sticky_view_by_side.get(side, default), first_input_visit_pending
