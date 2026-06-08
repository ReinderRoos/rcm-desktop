"""Unit tests for meekoppel workflow seam (slice 54 issue 01/02)."""

from __future__ import annotations

from dataclasses import replace

from rcm_core.config import RCMConfig
from rcm_core.models import Faalwijze, PBSItem, PMTask, RCMProject, TaskType

from rcm_desktop import messages
from rcm_desktop.adapter.loaded_project import LoadedProject
from rcm_desktop.adapter.meekoppel_workflow_service import MeekoppelWorkflowService
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.project_session import ProjectSession


def _project_with_rev_tasks() -> RCMProject:
    return RCMProject(
        config=RCMConfig(lifecycle_years=40.0, modeljaar=2026),
        pbs_items={
            "P1": PBSItem("P1", "obj", "el", "Pump", parent_pbs_id="ROOT"),
            "P2": PBSItem("P2", "obj", "el", "Valve", parent_pbs_id="ROOT"),
            "ROOT": PBSItem("ROOT", "obj", "el", "Site"),
        },
        faalwijzes={
            "FM-1": Faalwijze("FM-1", "P1", "F1", "Leak"),
            "FM-2": Faalwijze("FM-2", "P2", "F1", "Wear"),
        },
        pm_tasks={
            "PM-A": PMTask("PM-A", "FM-1", TaskType.REV, interval_jaar=5.0),
            "PM-B": PMTask("PM-B", "FM-1", TaskType.REV, interval_jaar=6.0),
            "PM-C": PMTask("PM-C", "FM-2", TaskType.REV, interval_jaar=7.0),
            "PM-D": PMTask("PM-D", "FM-2", TaskType.REV, interval_jaar=8.0),
        },
    )


def _session(project: RCMProject) -> ProjectSession:
    return ProjectSession.from_parts(LoadedProject.from_core(project))


def test_preview_returns_ok_with_payload_for_valid_selection() -> None:
    service = MeekoppelWorkflowService()
    project = _project_with_rev_tasks()
    result = service.preview(
        session=_session(project),
        overlay=PlanningOverlayState.inactive().begin_what_if(),
        pbs_ids=frozenset({"P1", "P2"}),
        anchor="later",
    )
    assert result.status == "ok"
    assert result.preview_payload is not None
    assert result.preview_payload.blocked_reason is None
    assert "preview" in result.telemetry_flags


def test_preview_returns_validation_when_selection_empty() -> None:
    service = MeekoppelWorkflowService()
    overlay = PlanningOverlayState.inactive().begin_what_if()
    result = service.preview(
        session=_session(_project_with_rev_tasks()),
        overlay=overlay,
        pbs_ids=frozenset(),
        anchor="later",
    )
    assert result.status == "validation"
    assert result.user_message == messages.WORKSPACE_MEEKOPPEL_SELECT_PBS
    assert result.overlay == overlay


def test_preview_returns_blocked_for_non_shiftable_selection() -> None:
    service = MeekoppelWorkflowService()
    project = _project_with_rev_tasks()
    project.pm_tasks["PM-A"] = replace(project.pm_tasks["PM-A"], is_wettelijk_verplicht=True)
    project.pm_tasks["PM-B"] = replace(project.pm_tasks["PM-B"], is_wettelijk_verplicht=True)
    result = service.preview(
        session=_session(project),
        overlay=PlanningOverlayState.inactive().begin_what_if(),
        pbs_ids=frozenset({"P1"}),
        anchor="later",
    )
    assert result.status == "blocked"
    assert result.user_message == messages.WORKSPACE_MEEKOPPEL_SELECT_MIN_SHIFTABLE_REV
    assert "blocked" in result.telemetry_flags


def test_apply_returns_ok_and_updates_overlay_for_valid_selection() -> None:
    service = MeekoppelWorkflowService()
    overlay = PlanningOverlayState.inactive().begin_what_if()
    result = service.apply(
        session=_session(_project_with_rev_tasks()),
        overlay=overlay,
        pbs_ids=frozenset({"P1", "P2"}),
        anchor="later",
    )
    assert result.status == "ok"
    assert result.overlay.change_count() > overlay.change_count()
    assert "apply" in result.telemetry_flags


def test_apply_with_checked_pm_ids_uses_subset() -> None:
    service = MeekoppelWorkflowService()
    project = _project_with_rev_tasks()
    overlay = PlanningOverlayState.inactive().begin_what_if()
    before = overlay.change_count()
    result = service.apply(
        session=_session(project),
        overlay=overlay,
        pbs_ids=frozenset({"P1", "P2"}),
        anchor="later",
        scope_kind="pbs_selection",
        checked_pm_ids=frozenset({"PM-A", "PM-B"}),
    )
    assert result.status == "ok"
    assert result.overlay.change_count() > before


def test_apply_returns_validation_when_selection_empty() -> None:
    service = MeekoppelWorkflowService()
    overlay = PlanningOverlayState.inactive().begin_what_if()
    result = service.apply(
        session=_session(_project_with_rev_tasks()),
        overlay=overlay,
        pbs_ids=frozenset(),
        anchor="later",
    )
    assert result.status == "validation"
    assert result.user_message == messages.WORKSPACE_MEEKOPPEL_SELECT_PBS
    assert result.overlay == overlay
