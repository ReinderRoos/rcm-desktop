"""Slice 76 issue 01 — Qt-vrije werkruimte-menubalk-spec + validator."""

from __future__ import annotations

import pytest

from rcm_desktop.adapter.workspace_menu_spec import (
    WORKSPACE_MENU_SPEC,
    WorkspaceMenuItem,
    WorkspaceMenuSection,
    validate_workspace_menu_spec,
)


def test_validator_rejects_duplicate_action_id() -> None:
    spec = (
        WorkspaceMenuSection(
            menu_id="test",
            label="Test",
            items=(
                WorkspaceMenuItem(
                    action_id="dup",
                    label="A",
                    checkable=False,
                    shortcut="Ctrl+A",
                ),
                WorkspaceMenuItem(
                    action_id="dup",
                    label="B",
                    checkable=False,
                    shortcut="Ctrl+B",
                ),
            ),
        ),
    )
    with pytest.raises(ValueError, match="action_id"):
        validate_workspace_menu_spec(spec)


def test_validator_rejects_duplicate_shortcut() -> None:
    spec = (
        WorkspaceMenuSection(
            menu_id="test",
            label="Test",
            items=(
                WorkspaceMenuItem(
                    action_id="a",
                    label="A",
                    checkable=False,
                    shortcut="Ctrl+X",
                ),
                WorkspaceMenuItem(
                    action_id="b",
                    label="B",
                    checkable=False,
                    shortcut="Ctrl+X",
                ),
            ),
        ),
    )
    with pytest.raises(ValueError, match="shortcut"):
        validate_workspace_menu_spec(spec)


def test_validator_requires_state_source_for_checkable_items() -> None:
    spec = (
        WorkspaceMenuSection(
            menu_id="test",
            label="Test",
            items=(
                WorkspaceMenuItem(
                    action_id="toggle",
                    label="Toggle",
                    checkable=True,
                    shortcut=None,
                    state_source=None,
                ),
            ),
        ),
    )
    with pytest.raises(ValueError, match="state_source"):
        validate_workspace_menu_spec(spec)


def test_workspace_menu_spec_is_valid_golden() -> None:
    validate_workspace_menu_spec(WORKSPACE_MENU_SPEC)

    by_id = {
        item.action_id: item
        for section in WORKSPACE_MENU_SPEC
        for item in section.items
    }
    assert by_id["file.open_project"].shortcut == "Ctrl+O"
    assert by_id["file.open_rcm_cost"].shortcut == "Ctrl+I"
    assert by_id["file.quit"].shortcut == "Ctrl+Q"
    assert by_id["view.pbs_tree_visible"].shortcut == "Ctrl+B"
    assert by_id["view.pbs_tree_visible"].state_source == "pbs_sidebar_visible"
    assert by_id["view.kpi_overview_visible"].shortcut == "Ctrl+K"
    assert by_id["view.kpi_overview_visible"].state_source == "kpi_overview_visible"
    assert by_id["view.column_crop"].shortcut == "Ctrl+Shift+C"
    assert by_id["view.column_crop"].state_source == "fm_column_crop"
    assert by_id["analysis.revalidate_input"].shortcut == "F7"
    assert by_id["analysis.faalwijzen_grid"].shortcut == "Ctrl+G"
    assert by_id["analysis.model_settings"].shortcut == "Ctrl+,"
    assert by_id["analysis.generate_report"].shortcut == "Ctrl+R"
    assert by_id["run.toggle_whatif"].shortcut == "Ctrl+Shift+W"
    assert by_id["run.slot_a"].shortcut == "Ctrl+Shift+A"
    assert by_id["run.slot_b"].shortcut == "Ctrl+Shift+B"
    assert by_id["run.scenario_cm"].shortcut == "Ctrl+Shift+M"
    assert by_id["run.scenario_pm"].shortcut == "Ctrl+Shift+P"
