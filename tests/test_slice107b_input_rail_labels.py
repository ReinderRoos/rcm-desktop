"""Slice 107-B issue 02 — Input rail bedieningslabels + breedte."""

from __future__ import annotations

from rcm_desktop.adapter.workspace_view_registry import (
    SIDE_INPUT,
    SIDE_OUTPUT,
    WORKSPACE_NAV_RAIL_WIDTH_PX,
    WORKSPACE_VIEW_REGISTRY,
    view_by_id,
)


def test_nav_rail_width_160px() -> None:
    assert WORKSPACE_NAV_RAIL_WIDTH_PX == 160


def test_input_faalwijzen_rail_label() -> None:
    entry = view_by_id(WORKSPACE_VIEW_REGISTRY, "input.faalwijzen")
    assert entry is not None
    assert entry.rail_label == "Faalwijzen"


def test_input_bedieningslabels() -> None:
    expected = {
        "input.faalwijzen": "Faalwijzen",
        "input.rev_tasks": "REV",
        "input.effecten": "Effect",
        "input.taakgroepen": "Taakgroep",
        "input.correctief": "Correctief",
    }
    for view_id, label in expected.items():
        entry = view_by_id(WORKSPACE_VIEW_REGISTRY, view_id)
        assert entry is not None
        assert entry.rail_label == label


def test_output_rail_labels_still_compact() -> None:
    expected = {
        "output.kpi_overview": "KPI",
        "output.lcc_plot": "LCC",
        "output.ltap": "LTAP",
        "output.fm_results": "TopX",
    }
    for view_id, label in expected.items():
        entry = view_by_id(WORKSPACE_VIEW_REGISTRY, view_id)
        assert entry is not None
        assert entry.rail_label == label


def test_input_views_are_input_side() -> None:
    for view_id in (
        "input.faalwijzen",
        "input.rev_tasks",
        "input.effecten",
        "input.taakgroepen",
        "input.correctief",
    ):
        entry = view_by_id(WORKSPACE_VIEW_REGISTRY, view_id)
        assert entry is not None
        assert entry.side == SIDE_INPUT


def test_output_views_are_output_side() -> None:
    for view_id in ("output.kpi_overview", "output.lcc_plot", "output.ltap", "output.fm_results"):
        entry = view_by_id(WORKSPACE_VIEW_REGISTRY, view_id)
        assert entry is not None
        assert entry.side == SIDE_OUTPUT
