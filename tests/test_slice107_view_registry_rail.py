"""Slice 107 — view-registry rail_label + KPI-entry."""

from __future__ import annotations

from rcm_desktop import messages
from rcm_desktop.adapter.workspace_view_registry import (
    SIDE_OUTPUT,
    WORKSPACE_VIEW_REGISTRY,
    view_by_id,
)


def test_output_kpi_overview_entry_exists() -> None:
    entry = view_by_id(WORKSPACE_VIEW_REGISTRY, "output.kpi_overview")
    assert entry is not None
    assert entry.enabled is True
    assert entry.rail_label == "KPI"
    assert entry.shortcut == "Ctrl+K"


def test_fm_results_rail_label_topx_and_view_label() -> None:
    entry = view_by_id(WORKSPACE_VIEW_REGISTRY, "output.fm_results")
    assert entry is not None
    assert entry.rail_label == "TopX"
    assert entry.label == messages.WORKSPACE_VIEW_TOP_BIJDRAGEN


def test_all_enabled_views_have_rail_label() -> None:
    for entry in WORKSPACE_VIEW_REGISTRY:
        if not entry.enabled:
            continue
        assert entry.rail_label, f"missing rail_label for {entry.view_id}"


def test_kpi_is_first_output_view_by_order() -> None:
    output = [e for e in WORKSPACE_VIEW_REGISTRY if e.side == SIDE_OUTPUT and e.enabled]
    assert output[0].view_id == "output.kpi_overview"
