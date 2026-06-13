"""Qt-vrije view-registry voor de resultatenwerkruimte (slice 79)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from rcm_desktop import messages

ToolbarFamily = Literal["none", "top10", "lcc", "fm", "input_grid"]
from rcm_desktop.adapter.workspace_menu_spec import WORKSPACE_MENU_SPEC, WorkspaceMenuSection

SIDE_INPUT = "input"
SIDE_OUTPUT = "output"

# Legacy modus-mapping (zelfde waarden als results_workspace_state.MODE_*).
_LEGACY_MODUS_BIJDRAGEN = "bijdragen"
_LEGACY_MODUS_LCC = "lcc"
_LEGACY_MODUS_FM_DETAIL = "fm_detail"


@dataclass(frozen=True)
class LccViewPreset:
    """Hard preset op het LCC-panel; niet overrulebaar vanuit de UI."""

    cm_enabled: bool


@dataclass(frozen=True)
class WorkspaceSideEntry:
    side_id: str
    label: str
    shortcut: str


@dataclass(frozen=True)
class WorkspaceChromeProfile:
    """Declaratief chrome-beleid per view (slice 95)."""

    allows_new_fm: bool = False
    allows_delete_fm: bool = False
    shows_nb_effect_filter: bool = False
    shows_metric_combo: bool = False
    shows_batch_faalwijzen: bool = False
    shows_column_crop: bool = False
    toolbar_family: ToolbarFamily = "none"


@dataclass(frozen=True)
class WorkspaceViewEntry:
    view_id: str
    side: str
    label: str
    shortcut: str
    order: int
    enabled: bool
    legacy_modus: str | None = None
    lcc_preset: LccViewPreset | None = None
    chrome: WorkspaceChromeProfile | None = None


WORKSPACE_SIDES: tuple[WorkspaceSideEntry, ...] = (
    WorkspaceSideEntry(
        side_id=SIDE_INPUT,
        label=messages.WORKSPACE_SIDE_INPUT,
        shortcut="Ctrl+1",
    ),
    WorkspaceSideEntry(
        side_id=SIDE_OUTPUT,
        label=messages.WORKSPACE_SIDE_OUTPUT,
        shortcut="Ctrl+2",
    ),
)

_CHROME_TOP10 = WorkspaceChromeProfile(
    toolbar_family="top10",
    shows_metric_combo=True,
    shows_nb_effect_filter=True,
)
_CHROME_LCC = WorkspaceChromeProfile(
    toolbar_family="lcc",
    shows_metric_combo=True,
    shows_nb_effect_filter=True,
)
_CHROME_FM_INPUT = WorkspaceChromeProfile(
    toolbar_family="fm",
    allows_new_fm=True,
    allows_delete_fm=True,
    shows_batch_faalwijzen=True,
)
_CHROME_FM_OUTPUT = WorkspaceChromeProfile(
    toolbar_family="fm",
    shows_column_crop=True,
    shows_metric_combo=True,
    shows_nb_effect_filter=True,
)
_CHROME_INPUT_GRID = WorkspaceChromeProfile(toolbar_family="input_grid")

WORKSPACE_VIEW_REGISTRY: tuple[WorkspaceViewEntry, ...] = (
    WorkspaceViewEntry(
        view_id="output.top_10",
        side=SIDE_OUTPUT,
        label=messages.WORKSPACE_VIEW_TOP_10,
        shortcut="Ctrl+Alt+1",
        order=1,
        enabled=True,
        legacy_modus=_LEGACY_MODUS_BIJDRAGEN,
        chrome=_CHROME_TOP10,
    ),
    WorkspaceViewEntry(
        view_id="output.lcc_plot",
        side=SIDE_OUTPUT,
        label=messages.WORKSPACE_VIEW_LCC_PLOT,
        shortcut="Ctrl+Alt+2",
        order=2,
        enabled=True,
        legacy_modus=_LEGACY_MODUS_LCC,
        chrome=_CHROME_LCC,
    ),
    WorkspaceViewEntry(
        view_id="output.ltap",
        side=SIDE_OUTPUT,
        label=messages.WORKSPACE_VIEW_LTAP,
        shortcut="Ctrl+Alt+3",
        order=3,
        enabled=True,
        legacy_modus=_LEGACY_MODUS_LCC,
        lcc_preset=LccViewPreset(cm_enabled=False),
        chrome=_CHROME_LCC,
    ),
    WorkspaceViewEntry(
        view_id="output.fm_results",
        side=SIDE_OUTPUT,
        label=messages.WORKSPACE_VIEW_FM_RESULTS,
        shortcut="Ctrl+Alt+4",
        order=4,
        enabled=True,
        legacy_modus=_LEGACY_MODUS_FM_DETAIL,
        chrome=_CHROME_FM_OUTPUT,
    ),
    WorkspaceViewEntry(
        view_id="input.faalwijzen",
        side=SIDE_INPUT,
        label=messages.WORKSPACE_VIEW_FAALWIJZEN,
        shortcut="Ctrl+Alt+1",
        order=1,
        enabled=True,
        legacy_modus=None,
        chrome=_CHROME_FM_INPUT,
    ),
    WorkspaceViewEntry(
        view_id="input.rev_tasks",
        side=SIDE_INPUT,
        label=messages.WORKSPACE_VIEW_REV_TASKS,
        shortcut="Ctrl+Alt+2",
        order=2,
        enabled=True,
        legacy_modus=None,
        chrome=_CHROME_INPUT_GRID,
    ),
    WorkspaceViewEntry(
        view_id="input.effecten",
        side=SIDE_INPUT,
        label=messages.WORKSPACE_VIEW_EFFECTEN,
        shortcut="Ctrl+Alt+3",
        order=3,
        enabled=True,
        legacy_modus=None,
        chrome=_CHROME_INPUT_GRID,
    ),
    WorkspaceViewEntry(
        view_id="input.taakgroepen",
        side=SIDE_INPUT,
        label=messages.WORKSPACE_VIEW_TAAKGROEPEN,
        shortcut="Ctrl+Alt+4",
        order=4,
        enabled=True,
        legacy_modus=None,
        chrome=_CHROME_INPUT_GRID,
    ),
    WorkspaceViewEntry(
        view_id="input.correctief",
        side=SIDE_INPUT,
        label=messages.WORKSPACE_VIEW_CORRECTIEF,
        shortcut="Ctrl+Alt+5",
        order=5,
        enabled=True,
        legacy_modus=None,
        chrome=_CHROME_INPUT_GRID,
    ),
)

DEFAULT_VIEW_BY_SIDE: dict[str, str] = {
    SIDE_OUTPUT: "output.top_10",
    SIDE_INPUT: "input.faalwijzen",
}


def views_for_side(
    registry: tuple[WorkspaceViewEntry, ...],
    side: str,
) -> tuple[WorkspaceViewEntry, ...]:
    return tuple(
        sorted(
            (entry for entry in registry if entry.side == side),
            key=lambda entry: entry.order,
        )
    )


def view_by_id(
    registry: tuple[WorkspaceViewEntry, ...],
    view_id: str,
) -> WorkspaceViewEntry | None:
    for entry in registry:
        if entry.view_id == view_id:
            return entry
    return None


def chrome_for_view(
    registry: tuple[WorkspaceViewEntry, ...],
    view_id: str,
) -> WorkspaceChromeProfile | None:
    entry = view_by_id(registry, view_id)
    if entry is None:
        return None
    return entry.chrome


def _menu_shortcuts(spec: tuple[WorkspaceMenuSection, ...]) -> set[str]:
    shortcuts: set[str] = set()
    for section in spec:
        for item in section.items:
            if item.shortcut is not None:
                shortcuts.add(item.shortcut)
    return shortcuts


def validate_workspace_view_registry(
    registry: tuple[WorkspaceViewEntry, ...],
    menu_spec: tuple[WorkspaceMenuSection, ...],
    *,
    sides: tuple[WorkspaceSideEntry, ...] = WORKSPACE_SIDES,
) -> None:
    """Valideer unieke view_id's en sneltoetsen (incl. menubalk-spec)."""
    seen_view_ids: set[str] = set()
    seen_shortcuts: set[str] = set(_menu_shortcuts(menu_spec))

    for side in sides:
        if side.shortcut in seen_shortcuts:
            raise ValueError(f"duplicate shortcut: {side.shortcut}")
        seen_shortcuts.add(side.shortcut)

    for entry in registry:
        if entry.view_id in seen_view_ids:
            raise ValueError(f"duplicate view_id: {entry.view_id}")
        seen_view_ids.add(entry.view_id)

        if not entry.label.strip():
            raise ValueError(f"missing label for view_id: {entry.view_id}")

        if entry.side not in {SIDE_INPUT, SIDE_OUTPUT}:
            raise ValueError(f"invalid side for {entry.view_id}: {entry.side!r}")

    shortcuts_by_side: dict[str, set[str]] = {SIDE_INPUT: set(), SIDE_OUTPUT: set()}
    for entry in registry:
        side_shortcuts = shortcuts_by_side[entry.side]
        if entry.shortcut in side_shortcuts:
            raise ValueError(
                f"duplicate shortcut within side {entry.side!r}: {entry.shortcut}"
            )
        side_shortcuts.add(entry.shortcut)


validate_workspace_view_registry(WORKSPACE_VIEW_REGISTRY, WORKSPACE_MENU_SPEC)
