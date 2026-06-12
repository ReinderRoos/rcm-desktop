"""Slice 79 issue 01 — Qt-vrije view-registry + validator."""

from __future__ import annotations

import pytest

from rcm_desktop import messages
from rcm_desktop.adapter.workspace_menu_spec import WORKSPACE_MENU_SPEC
from rcm_desktop.adapter.workspace_view_registry import (
    SIDE_INPUT,
    SIDE_OUTPUT,
    WORKSPACE_SIDES,
    WORKSPACE_VIEW_REGISTRY,
    _LEGACY_MODUS_BIJDRAGEN,
    _LEGACY_MODUS_FM_DETAIL,
    _LEGACY_MODUS_LCC,
    views_for_side,
    validate_workspace_view_registry,
)


def test_validator_rejects_duplicate_view_id() -> None:
    from rcm_desktop.adapter.workspace_view_registry import WorkspaceViewEntry

    bad = (
        WorkspaceViewEntry(
            view_id="dup",
            side=SIDE_OUTPUT,
            label="A",
            shortcut="Ctrl+Alt+1",
            order=1,
            enabled=True,
            legacy_modus=_LEGACY_MODUS_BIJDRAGEN,
        ),
        WorkspaceViewEntry(
            view_id="dup",
            side=SIDE_OUTPUT,
            label="B",
            shortcut="Ctrl+Alt+2",
            order=2,
            enabled=True,
            legacy_modus=_LEGACY_MODUS_LCC,
        ),
    )
    with pytest.raises(ValueError, match="view_id"):
        validate_workspace_view_registry(bad, WORKSPACE_MENU_SPEC)


def test_validator_rejects_duplicate_shortcut_within_side() -> None:
    from rcm_desktop.adapter.workspace_view_registry import WorkspaceViewEntry

    bad = (
        WorkspaceViewEntry(
            view_id="a",
            side=SIDE_OUTPUT,
            label="A",
            shortcut="Ctrl+Alt+9",
            order=1,
            enabled=True,
            legacy_modus=_LEGACY_MODUS_BIJDRAGEN,
        ),
        WorkspaceViewEntry(
            view_id="b",
            side=SIDE_OUTPUT,
            label="B",
            shortcut="Ctrl+Alt+9",
            order=2,
            enabled=True,
            legacy_modus=_LEGACY_MODUS_LCC,
        ),
    )
    with pytest.raises(ValueError, match="shortcut"):
        validate_workspace_view_registry(bad, WORKSPACE_MENU_SPEC)


def test_workspace_view_registry_golden() -> None:
    validate_workspace_view_registry(WORKSPACE_VIEW_REGISTRY, WORKSPACE_MENU_SPEC)

    by_id = {entry.view_id: entry for entry in WORKSPACE_VIEW_REGISTRY}

    assert len(by_id) == 9

    output = views_for_side(WORKSPACE_VIEW_REGISTRY, SIDE_OUTPUT)
    assert [v.view_id for v in output] == [
        "output.top_10",
        "output.lcc_plot",
        "output.ltap",
        "output.fm_results",
    ]
    assert output[0].label == messages.WORKSPACE_VIEW_TOP_10
    assert output[0].enabled is True
    assert output[0].legacy_modus == _LEGACY_MODUS_BIJDRAGEN
    assert output[0].shortcut == "Ctrl+Alt+1"
    assert output[1].label == messages.WORKSPACE_VIEW_LCC_PLOT
    assert output[1].legacy_modus == _LEGACY_MODUS_LCC
    assert output[2].label == messages.WORKSPACE_VIEW_LTAP
    assert output[2].enabled is True
    assert output[2].legacy_modus == _LEGACY_MODUS_LCC
    assert output[2].lcc_preset is not None
    assert output[2].lcc_preset.cm_enabled is False
    assert output[3].label == messages.WORKSPACE_VIEW_FM_RESULTS
    assert output[3].legacy_modus == _LEGACY_MODUS_FM_DETAIL

    input_views = views_for_side(WORKSPACE_VIEW_REGISTRY, SIDE_INPUT)
    assert len(input_views) == 5
    assert all(v.enabled for v in input_views)
    assert input_views[0].label == "Faalwijzen"
    assert input_views[0].shortcut == "Ctrl+Alt+1"

    side_shortcuts = {entry.side_id: entry.shortcut for entry in WORKSPACE_SIDES}
    assert side_shortcuts[SIDE_INPUT] == "Ctrl+1"
    assert side_shortcuts[SIDE_OUTPUT] == "Ctrl+2"
