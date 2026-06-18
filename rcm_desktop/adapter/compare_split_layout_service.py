"""A/B compare split layout for the resultatenwerkruimte (slice 56, 58)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_desktop.adapter.results_workspace_state import MODE_BIJDRAGEN, MODE_FM_DETAIL, MODE_LCC

SPLIT_NONE = "none"
SPLIT_VERTICAL = "vertical"
SPLIT_HORIZONTAL = "horizontal"


@dataclass(frozen=True)
class CompareSplitLayout:
    orientation: str
    compare_mode: bool


def compute_compare_split_layout(*, compare_mode: bool, modus: str) -> CompareSplitLayout:
    if not compare_mode:
        return CompareSplitLayout(orientation=SPLIT_NONE, compare_mode=False)
    if modus == MODE_BIJDRAGEN:
        return CompareSplitLayout(orientation=SPLIT_HORIZONTAL, compare_mode=True)
    if modus == MODE_LCC:
        return CompareSplitLayout(orientation=SPLIT_VERTICAL, compare_mode=True)
    if modus == MODE_FM_DETAIL:
        return CompareSplitLayout(orientation=SPLIT_HORIZONTAL, compare_mode=True)
    return CompareSplitLayout(orientation=SPLIT_NONE, compare_mode=False)
