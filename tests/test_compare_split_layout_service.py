from __future__ import annotations

from rcm_desktop.adapter.compare_split_layout_service import (
    SPLIT_HORIZONTAL,
    SPLIT_NONE,
    SPLIT_VERTICAL,
    compute_compare_split_layout,
)
from rcm_desktop.adapter.results_workspace_state import MODE_BIJDRAGEN, MODE_LCC


def test_compare_off_returns_none():
    layout = compute_compare_split_layout(compare_mode=False, modus=MODE_BIJDRAGEN)
    assert layout.orientation == SPLIT_NONE
    assert not layout.compare_mode


def test_compare_top10_is_horizontal():
    layout = compute_compare_split_layout(compare_mode=True, modus=MODE_BIJDRAGEN)
    assert layout.orientation == SPLIT_HORIZONTAL
    assert layout.compare_mode


def test_compare_lcc_is_vertical():
    layout = compute_compare_split_layout(compare_mode=True, modus=MODE_LCC)
    assert layout.orientation == SPLIT_VERTICAL


def test_compare_fm_detail_is_horizontal():
    from rcm_desktop.adapter.results_workspace_state import MODE_FM_DETAIL

    layout = compute_compare_split_layout(compare_mode=True, modus=MODE_FM_DETAIL)
    assert layout.orientation == SPLIT_HORIZONTAL
