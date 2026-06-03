from __future__ import annotations

from dataclasses import replace
from unittest.mock import MagicMock, patch

from rcm_desktop.adapter.compare_slot_state import (
    COMPARE_SLOT_A,
    COMPARE_SLOT_B,
    CompareSlotSnapshot,
    CompareSlotState,
)
from rcm_desktop.adapter.compare_view_service import (
    build_bijdragen_compare_panels,
    build_lcc_compare_panels,
    workspace_snapshot_for_slot,
)
from rcm_desktop.adapter.lcc_view_service import LCCView
from rcm_desktop.adapter.workspace_render_index import SLOT_A, SLOT_B
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
from rcm_desktop.adapter.results_workspace_state import (
    WorkspaceStateSnapshot,
    _DEFAULT_SNAPSHOT,
)


def test_workspace_snapshot_for_slot_uses_frozen_overlay():
    live_overlay = PlanningOverlayState.inactive().begin_what_if()
    frozen = PlanningOverlayState.inactive()
    workspace = replace(_DEFAULT_SNAPSHOT, planning_overlay=live_overlay)
    snap = CompareSlotSnapshot.from_motor_run(
        run_result=_done_run(),
        presentation=None,
        scenario_key=None,
        overlay_at_run=frozen,
        label="A",
    )

    effective = workspace_snapshot_for_slot(workspace, snap)

    assert effective.planning_overlay == frozen
    assert effective.planning_overlay is not live_overlay


def test_build_bijdragen_compare_panels_uses_distinct_slot_overlays():
    overlay_a = PlanningOverlayState.inactive()
    overlay_b = PlanningOverlayState.inactive().begin_what_if()
    slots = CompareSlotState()
    slots.put(
        COMPARE_SLOT_A,
        CompareSlotSnapshot.from_motor_run(
            run_result=_done_run(),
            presentation=None,
            scenario_key=None,
            overlay_at_run=overlay_a,
            label="A",
        ),
    )
    slots.put(
        COMPARE_SLOT_B,
        CompareSlotSnapshot.from_motor_run(
            run_result=_done_run(),
            presentation=None,
            scenario_key=None,
            overlay_at_run=overlay_b,
            label="B",
        ),
    )
    workspace = _DEFAULT_SNAPSHOT
    captured: list[PlanningOverlayState] = []

    def fake_build(session, snapshot, **kwargs):
        captured.append(snapshot.planning_overlay)
        return MagicMock(contribution_rows=(), cache_modus_key="k", from_presentation_cache=False)

    session = MagicMock()
    session.has_completed_run.return_value = True
    session.loaded.core.return_value = MagicMock()
    session.run = MagicMock()

    with patch(
        "rcm_desktop.adapter.compare_view_service.build_bijdragen_view",
        side_effect=fake_build,
    ):
        panels = build_bijdragen_compare_panels(
            session,
            workspace,
            slots=slots,
            render_index=MagicMock(),
            project_total_presentation=None,
        )

    assert len(panels) == 2
    assert captured[0] == overlay_a
    assert captured[1] == overlay_b


def test_build_bijdragen_compare_panels_uses_frozen_overlay_not_live_workspace() -> None:
    """Slice 56 issue 06 — live workspace-overlay wijzigt slot-render niet."""
    frozen = PlanningOverlayState.inactive()
    live = PlanningOverlayState.inactive().begin_what_if()
    slots = CompareSlotState()
    slots.put(
        COMPARE_SLOT_A,
        CompareSlotSnapshot.from_motor_run(
            run_result=_done_run(),
            presentation=None,
            scenario_key=None,
            overlay_at_run=frozen,
            label="A",
        ),
    )
    workspace = replace(_DEFAULT_SNAPSHOT, planning_overlay=live)
    captured: list[PlanningOverlayState] = []

    def fake_build(session, snapshot, **kwargs):
        captured.append(snapshot.planning_overlay)
        return MagicMock(contribution_rows=(), cache_modus_key="k", from_presentation_cache=False)

    session = MagicMock()
    session.has_completed_run.return_value = True
    session.loaded.core.return_value = MagicMock()
    session.run = MagicMock()

    with patch(
        "rcm_desktop.adapter.compare_view_service.build_bijdragen_view",
        side_effect=fake_build,
    ):
        build_bijdragen_compare_panels(
            session,
            workspace,
            slots=slots,
            render_index=MagicMock(),
            project_total_presentation=None,
        )

    assert len(captured) == 1
    assert captured[0] == frozen
    assert captured[0] is not live


def test_build_lcc_compare_panels_uses_workspace_lcc_view_per_slot():
    slots = CompareSlotState()
    run = _done_run()
    slots.put(
        COMPARE_SLOT_A,
        CompareSlotSnapshot.from_motor_run(
            run_result=run,
            presentation=None,
            scenario_key=None,
            overlay_at_run=PlanningOverlayState.inactive(),
            label="A",
        ),
    )
    slots.put(
        COMPARE_SLOT_B,
        CompareSlotSnapshot.from_motor_run(
            run_result=run,
            presentation=None,
            scenario_key=None,
            overlay_at_run=PlanningOverlayState.inactive().begin_what_if(),
            label="B",
        ),
    )
    captured_slots: list[str] = []

    def fake_lcc(session, snapshot, **kwargs):
        captured_slots.append(kwargs.get("slot"))
        return LCCView(curve=MagicMock(display_buckets=(MagicMock(),)), render_scope="full")

    session = MagicMock()
    session.has_completed_run.return_value = True
    session.loaded.core.return_value = MagicMock()
    session.path = None

    with patch(
        "rcm_desktop.adapter.compare_view_service.build_lcc_view",
        side_effect=fake_lcc,
    ):
        panels = build_lcc_compare_panels(
            session,
            _DEFAULT_SNAPSHOT,
            slots=slots,
            render_index=MagicMock(),
            prev_snapshot=None,
        )

    assert len(panels) == 2
    assert all(p.filled and p.lcc is not None and p.lcc.curve is not None for p in panels)
    assert captured_slots == [SLOT_A, SLOT_B]
