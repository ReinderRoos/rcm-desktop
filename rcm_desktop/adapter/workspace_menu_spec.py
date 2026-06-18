"""Qt-vrije menubalk-spec voor de resultatenwerkruimte (slice 76)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_desktop import messages

# state_source-waarden voor checkable menu-items (binding in issue 02).
STATE_SOURCE_PBS_SIDEBAR_VISIBLE = "pbs_sidebar_visible"
STATE_SOURCE_FM_COLUMN_CROP = "fm_column_crop"


@dataclass(frozen=True)
class WorkspaceMenuItem:
    action_id: str
    label: str
    checkable: bool
    shortcut: str | None
    state_source: str | None = None


@dataclass(frozen=True)
class WorkspaceMenuSection:
    menu_id: str
    label: str
    items: tuple[WorkspaceMenuItem, ...]


WORKSPACE_MENU_SPEC: tuple[WorkspaceMenuSection, ...] = (
    WorkspaceMenuSection(
        menu_id="file",
        label=messages.WORKSPACE_MENU_FILE,
        items=(
            WorkspaceMenuItem(
                action_id="file.open_project",
                label=messages.WORKSPACE_MENU_OPEN_PROJECT,
                checkable=False,
                shortcut="Ctrl+O",
            ),
            WorkspaceMenuItem(
                action_id="file.open_rcm_cost",
                label=messages.WORKSPACE_MENU_OPEN_RCM_COST,
                checkable=False,
                shortcut="Ctrl+I",
            ),
            WorkspaceMenuItem(
                action_id="file.export_rcm_cost",
                label=messages.WORKSPACE_MENU_EXPORT_RCM_COST,
                checkable=False,
                shortcut=None,
            ),
            WorkspaceMenuItem(
                action_id="file.quit",
                label=messages.WORKSPACE_MENU_QUIT,
                checkable=False,
                shortcut="Ctrl+Q",
            ),
        ),
    ),
    WorkspaceMenuSection(
        menu_id="view",
        label=messages.WORKSPACE_MENU_VIEW,
        items=(
            WorkspaceMenuItem(
                action_id="view.pbs_tree_visible",
                label=messages.WORKSPACE_MENU_PBS_TREE_VISIBLE,
                checkable=True,
                shortcut="Ctrl+B",
                state_source=STATE_SOURCE_PBS_SIDEBAR_VISIBLE,
            ),
            WorkspaceMenuItem(
                action_id="view.column_crop",
                label=messages.WORKSPACE_FM_COLUMN_CROP,
                checkable=True,
                shortcut="Ctrl+Shift+C",
                state_source=STATE_SOURCE_FM_COLUMN_CROP,
            ),
            WorkspaceMenuItem(
                action_id="view.pbs_select_prev_sibling",
                label=messages.WORKSPACE_MENU_PBS_SELECT_PREV_SIBLING,
                checkable=False,
                shortcut="Alt+Up",
            ),
            WorkspaceMenuItem(
                action_id="view.pbs_select_next_sibling",
                label=messages.WORKSPACE_MENU_PBS_SELECT_NEXT_SIBLING,
                checkable=False,
                shortcut="Alt+Down",
            ),
            WorkspaceMenuItem(
                action_id="view.pbs_select_parent",
                label=messages.WORKSPACE_MENU_PBS_SELECT_PARENT,
                checkable=False,
                shortcut="Alt+Left",
            ),
            WorkspaceMenuItem(
                action_id="view.pbs_select_first_child",
                label=messages.WORKSPACE_MENU_PBS_SELECT_FIRST_CHILD,
                checkable=False,
                shortcut="Alt+Right",
            ),
            WorkspaceMenuItem(
                action_id="view.pbs_move_up",
                label=messages.WORKSPACE_MENU_PBS_MOVE_UP,
                checkable=False,
                shortcut="Ctrl+Alt+Up",
            ),
            WorkspaceMenuItem(
                action_id="view.pbs_move_down",
                label=messages.WORKSPACE_MENU_PBS_MOVE_DOWN,
                checkable=False,
                shortcut="Ctrl+Alt+Down",
            ),
        ),
    ),
    WorkspaceMenuSection(
        menu_id="whatif",
        label=messages.WORKSPACE_MENU_WHATIF,
        items=(
            WorkspaceMenuItem(
                action_id="whatif.toggle",
                label=messages.WORKSPACE_MENU_TOGGLE_WHATIF,
                checkable=False,
                shortcut="Ctrl+Shift+W",
            ),
        ),
    ),
    WorkspaceMenuSection(
        menu_id="run",
        label=messages.WORKSPACE_MENU_RUN,
        items=(
            WorkspaceMenuItem(
                action_id="run.slot_a",
                label=messages.WORKSPACE_MENU_RUN_SLOT_A,
                checkable=False,
                shortcut="Ctrl+Shift+A",
            ),
            WorkspaceMenuItem(
                action_id="run.slot_b",
                label=messages.WORKSPACE_MENU_RUN_SLOT_B,
                checkable=False,
                shortcut="Ctrl+Shift+B",
            ),
        ),
    ),
    WorkspaceMenuSection(
        menu_id="analysis",
        label=messages.WORKSPACE_MENU_ANALYSIS,
        items=(
            WorkspaceMenuItem(
                action_id="analysis.compare_models",
                label=messages.WORKSPACE_MENU_COMPARE_MODELS,
                checkable=False,
                shortcut="Ctrl+Shift+L",
            ),
            WorkspaceMenuItem(
                action_id="analysis.revalidate_input",
                label=messages.WORKSPACE_MENU_REVALIDATE_INPUT,
                checkable=False,
                shortcut="F7",
            ),
            WorkspaceMenuItem(
                action_id="analysis.faalwijzen_grid",
                label=messages.WORKSPACE_MENU_FAALWIJZEN_GRID,
                checkable=False,
                shortcut="Ctrl+G",
            ),
            WorkspaceMenuItem(
                action_id="analysis.model_settings",
                label=f"{messages.MODEL_SETTINGS_BUTTON_LABEL}…",
                checkable=False,
                shortcut="Ctrl+,",
            ),
            WorkspaceMenuItem(
                action_id="analysis.generate_report",
                label=messages.REPORT_GENERATE_BUTTON_LABEL,
                checkable=False,
                shortcut="Ctrl+R",
            ),
        ),
    ),
)


def validate_workspace_menu_spec(
    spec: tuple[WorkspaceMenuSection, ...],
) -> None:
    """Valideer unieke action_id's en sneltoetsen; checkable vereist state_source."""
    seen_action_ids: set[str] = set()
    seen_shortcuts: set[str] = set()

    for section in spec:
        for item in section.items:
            if item.action_id in seen_action_ids:
                raise ValueError(f"duplicate action_id: {item.action_id}")
            seen_action_ids.add(item.action_id)

            if item.shortcut is not None:
                if item.shortcut in seen_shortcuts:
                    raise ValueError(f"duplicate shortcut: {item.shortcut}")
                seen_shortcuts.add(item.shortcut)

            if item.checkable and not item.state_source:
                raise ValueError(
                    f"checkable item {item.action_id} missing state_source"
                )
            if not item.checkable and item.state_source is not None:
                raise ValueError(
                    f"non-checkable item {item.action_id} must not have state_source"
                )


validate_workspace_menu_spec(WORKSPACE_MENU_SPEC)
