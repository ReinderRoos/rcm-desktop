"""Semantische visuele flags voor compare v1 (slice 96 issue 05)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from rcm_desktop.adapter.scenario_compare_chrome import scenario_color_hex
from rcm_desktop.adapter.compare_slot_state import COMPARE_SLOT_A, COMPARE_SLOT_B
from rcm_desktop.adapter.compare_workspace_presentation_service import MATCH_KIND_BADGE_LABELS

if TYPE_CHECKING:
    from rcm_desktop.adapter.compare_workspace_presentation_service import CompareWorkspaceViewState


def match_kind_badge(match_kind: str) -> str:
    return MATCH_KIND_BADGE_LABELS.get(match_kind, match_kind)


def run_source_label(source: str) -> str:
    if source == "cache":
        return "cache"
    if source == "run":
        return "run"
    return "—"


@dataclass(frozen=True)
class CompareVisualFlags:
    label_a: str
    label_b: str
    color_a: str
    color_b: str
    run_status_text_a: str
    run_status_text_b: str


def build_compare_visual_flags(state: CompareWorkspaceViewState) -> CompareVisualFlags:
    return CompareVisualFlags(
        label_a=state.label_a,
        label_b=state.label_b,
        color_a=scenario_color_hex(COMPARE_SLOT_A),
        color_b=scenario_color_hex(COMPARE_SLOT_B),
        run_status_text_a=f"A: {run_source_label(state.run_source_a)}",
        run_status_text_b=f"B: {run_source_label(state.run_source_b)}",
    )
