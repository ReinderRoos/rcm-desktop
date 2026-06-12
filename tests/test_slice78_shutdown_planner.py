"""Slice 78 issue 01 — Qt-vrije afsluit-planner."""

from __future__ import annotations

from rcm_desktop.adapter.shutdown_planner import ShutdownStep, plan_shutdown


def test_plan_shutdown_immediate_when_clean() -> None:
    plan = plan_shutdown(grid_dirty=False, busy=False)
    assert plan.steps == (ShutdownStep.CLOSE,)


def test_plan_shutdown_grid_before_busy() -> None:
    plan = plan_shutdown(grid_dirty=True, busy=True)
    assert plan.steps == (
        ShutdownStep.RESOLVE_GRID_DIRTY,
        ShutdownStep.CONFIRM_BUSY_CANCEL,
        ShutdownStep.CLOSE,
    )


def test_plan_shutdown_grid_only() -> None:
    plan = plan_shutdown(grid_dirty=True, busy=False)
    assert plan.steps == (ShutdownStep.RESOLVE_GRID_DIRTY, ShutdownStep.CLOSE)


def test_plan_shutdown_busy_only() -> None:
    plan = plan_shutdown(grid_dirty=False, busy=True)
    assert plan.steps == (ShutdownStep.CONFIRM_BUSY_CANCEL, ShutdownStep.CLOSE)
