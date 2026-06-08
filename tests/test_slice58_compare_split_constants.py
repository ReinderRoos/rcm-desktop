"""Slice 58 — split-constanten SSOT in compare_split_layout_service."""

from __future__ import annotations

import rcm_desktop.adapter.compare_split_layout_service as compare_mod
import rcm_desktop.adapter.workspace_split_layout as legacy_mod


def test_split_constants_reexported_from_legacy_stub() -> None:
    assert legacy_mod.SPLIT_NONE == compare_mod.SPLIT_NONE
    assert legacy_mod.SPLIT_VERTICAL == compare_mod.SPLIT_VERTICAL
    assert legacy_mod.SPLIT_HORIZONTAL == compare_mod.SPLIT_HORIZONTAL
