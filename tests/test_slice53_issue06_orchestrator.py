"""Slice 53 issue 06 — orchestrator + dirty policy + host ownership."""

from __future__ import annotations

import pytest
from pathlib import Path

from rcm_desktop.adapter.dirty_guard_policy import resolve_dirty_choice
from rcm_desktop.adapter.editing_host import EditingHost
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.results_workspace_controller import ResultsWorkspaceController


class _DirtyGridStub:
    def __init__(self) -> None:
        self._dirty = True
        self.discarded = False

    def is_active(self) -> bool:
        return True

    def is_dirty(self) -> bool:
        return self._dirty

    def discard_changes(self) -> None:
        self.discarded = True
        self._dirty = False

    def has_errors(self) -> bool:
        return False

    def mark_saved(self) -> None:
        self._dirty = False


def test_dirty_policy_is_adapter_only_and_unit_testable() -> None:
    host = EditingHost()
    grid = _DirtyGridStub()
    host.attach_grid(grid)  # type: ignore[arg-type]
    assert resolve_dirty_choice(host, "cancel") == "cancel"
    assert resolve_dirty_choice(host, "discard") == "proceed"
    assert grid.discarded is True


def test_dirty_policy_save_failed_returns_warn() -> None:
    host = EditingHost()
    host.attach_grid(_DirtyGridStub())  # type: ignore[arg-type]
    host.set_save_handler(lambda: False)
    assert resolve_dirty_choice(host, "save") == "warn_save_failed"


def test_controller_plans_post_run_and_validate() -> None:
    overlay = PlanningOverlayState.inactive().begin_what_if().set_passive("PM-1", passive=True)
    run_plan = ResultsWorkspaceController.plan_after_successful_run(
        overlay,
        has_presentation_payload=False,
    )
    assert run_plan.had_passive_before_run is True
    assert run_plan.invalidate_render_index is True
    assert run_plan.load_presentation_from_disk is True
    assert run_plan.warmup_lcc is True

    validate_plan = ResultsWorkspaceController.plan_after_validate(
        has_hydrated_run=True,
        has_path=True,
        has_session=True,
        run_done=True,
        presentation_rebuild_needed=True,
        run_runner_busy=False,
        presentation_runner_busy=False,
    )
    assert validate_plan.load_presentation_from_disk is True
    assert validate_plan.start_presentation_rebuild is True


def test_workspace_window_owns_editing_host_and_no_legacy_loader() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication
    from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

    app = QApplication.instance() or QApplication([])
    w1 = ResultsWorkspaceWindow()
    w2 = ResultsWorkspaceWindow()
    assert w1._editing_host is not w2._editing_host
    source = (
        Path(__file__).resolve().parent.parent
        / "rcm_desktop"
        / "views"
        / "results_workspace_window.py"
    ).read_text(encoding="utf-8")
    assert "get_editing_host(" not in source
    assert "def _load_presentation_cache(" not in source
    w1.close()
    w2.close()
    app.processEvents()
