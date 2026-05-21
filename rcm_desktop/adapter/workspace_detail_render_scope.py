"""Pure beslislogica: hoe zwaar moet detail-rerender in scenario-modus (slice 25).

Qt-vrij zodat unit-tests zonder QApplication kunnen draaien.
"""
from __future__ import annotations

from typing import Literal

from rcm_desktop.adapter.results_workspace_state import WorkspaceStateSnapshot

RenderSplitDepth = Literal["all_splits", "active_modus_only"]

_DETAIL_MODI = frozenset(
    {
        "fm_detail",
        "bijdragen",
        "lcc",
    }
)


def workspace_detail_split_render_depth(
    previous: WorkspaceStateSnapshot | None,
    current: WorkspaceStateSnapshot,
) -> RenderSplitDepth:
    """Bepaal of alle scenario-splitketens herbouwd moeten worden.

    - `all_splits`: PBS-scope wijzigde → PM/Bijdragen/Niet-beschikbaarheid kunnen
      andere scoped totalen tonen; gebruiker moet bij moduswissel geen stale data zien.
    - `active_modus_only`: alleen modus-/presentatie-toggles (metric, bron,
      PM-submodus, filtertekst) wijzigden → geen scope-shift; splits voor niet-
      actieve modi hoeven niet opnieuw door adapters.
    """
    if previous is None:
        return "all_splits"
    if previous.scope_id != current.scope_id:
        return "all_splits"
    return "active_modus_only"


def required_detail_builders(
    snapshot: WorkspaceStateSnapshot,
    depth: RenderSplitDepth,
) -> frozenset[str]:
    """Welke modus-adapters in deze tick herbouwd mogen worden."""
    if depth == "active_modus_only":
        return frozenset({snapshot.modus})
    return frozenset(_DETAIL_MODI)


def should_refresh_kpi_for_render_depth(depth: RenderSplitDepth) -> bool:
    return depth == "all_splits"
