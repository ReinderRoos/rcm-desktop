from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rcm_desktop.adapter.compare_slot_state import (
    COMPARE_SLOT_A,
    CompareSlotSnapshot,
    CompareSlotState,
)
from rcm_desktop.adapter.compare_view_service import workspace_snapshot_for_slot
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.results_workspace_state import _DEFAULT_SNAPSHOT
from rcm_desktop.adapter.run_service import RunMetrics, RunResult


def _done_run() -> RunResult:
    return RunResult(
        status="done",
        summary="ok",
        metrics=RunMetrics(
            fm_result_count=0,
            total_lifecycle_faalmomenten=0.0,
            total_cost_eur=0.0,
        ),
    )

ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_WINDOW = ROOT / "rcm_desktop" / "views" / "results_workspace_window.py"
ADR_0007 = ROOT / "docs" / "adr" / "ADR-0007-workspace-ab-compare.md"


def test_adr_0007_exists_and_references_legacy_boundary() -> None:
    text = ADR_0007.read_text(encoding="utf-8")
    assert "CompareRunner" in text
    assert "ADR-0006" in text
    assert "A/B" in text or "A/B" in text


def test_issue56_workspace_has_ab_compare_path_not_legacy_compare_runner() -> None:
    source = WORKSPACE_WINDOW.read_text(encoding="utf-8")
    assert "_compare_slots" in source
    assert "CompareRunner" not in source
    assert "compare_mode" in source


def test_frozen_overlay_isolates_slot_from_live_workspace_overlay() -> None:
    live = PlanningOverlayState.inactive().begin_what_if()
    frozen = PlanningOverlayState.inactive()
    snap = CompareSlotSnapshot.from_motor_run(
        run_result=_done_run(),
        presentation=None,
        scenario_key=None,
        overlay_at_run=frozen,
        label="A",
    )
    workspace = replace(_DEFAULT_SNAPSHOT, planning_overlay=live)

    first = workspace_snapshot_for_slot(workspace, snap)
    workspace2 = replace(workspace, planning_overlay=live.begin_what_if())
    second = workspace_snapshot_for_slot(workspace2, snap)

    assert first.planning_overlay == frozen
    assert second.planning_overlay == frozen


def test_compare_workspace_controller_keeps_slot_on_failed_rerun() -> None:
    from rcm_desktop.adapter.compare_run_service import CompareRunOutcome
    from rcm_desktop.adapter.compare_workspace_controller import CompareWorkspaceController

    slots = CompareSlotState()
    overlay = PlanningOverlayState.inactive()
    from rcm_desktop.adapter.compare_slot_state import COMPARE_SLOT_B

    previous = CompareSlotSnapshot.from_motor_run(
        run_result=_done_run(),
        presentation=None,
        scenario_key=None,
        overlay_at_run=overlay,
        label="B — oud",
    )
    slots.put(COMPARE_SLOT_B, previous)
    failed = CompareRunOutcome(status="error", summary="mislukt", snapshot=None)

    assert CompareWorkspaceController.should_keep_previous_slot_on_error(
        COMPARE_SLOT_B, failed, previous=previous
    )
