"""Unit tests — meekoppel bundle preview insight (slice 54, 03d)."""

from __future__ import annotations

from rcm_core.config import RCMConfig
from rcm_core.models import Faalwijze, PBSItem, PMTask, RCMProject, TaskType

from rcm_desktop.adapter.loaded_project import LoadedProject
from rcm_desktop.adapter.meekoppel_bundle_insight_service import (
    build_bundle_insight,
    preview_meekoppel_with_insight,
    resolve_default_scope_kind,
)
from rcm_desktop.adapter.meekoppel_apply_service import preview_meekoppel_rev_tasks
from rcm_desktop.adapter.meekoppelkansen_discovery_service import (
    discover_meekoppel_locations,
)
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.project_session import ProjectSession


def _hwp_in_project() -> RCMProject:
    """P1- en P2-groepen gescheiden (geen gedeelde parent-rollup naar ROOT)."""
    return RCMProject(
        config=RCMConfig(lifecycle_years=40.0, modeljaar=2026),
        pbs_items={
            "P1": PBSItem("P1", "obj", "el", "HWP-IN"),
            "P2": PBSItem("P2", "obj", "el", "Other"),
        },
        faalwijzes={
            "FM-1": Faalwijze("FM-1", "P1", "F1", "Leak"),
            "FM-2": Faalwijze("FM-2", "P2", "F1", "Wear"),
        },
        pm_tasks={
            "PM-A": PMTask("PM-A", "FM-1", TaskType.REV, interval_jaar=2.0),
            "PM-B": PMTask("PM-B", "FM-1", TaskType.REV, interval_jaar=2.0),
            "PM-C": PMTask(
                "PM-C",
                "FM-2",
                TaskType.REV,
                interval_jaar=2.0,
                taak_omschrijving="Late driver",
            ),
        },
    )


def _session(project: RCMProject) -> ProjectSession:
    return ProjectSession.from_parts(LoadedProject.from_core(project))


def test_resolve_default_scope_kind_prefers_location_row():
    project = _hwp_in_project()
    group = discover_meekoppel_locations(project, window_years=5)[0]
    assert resolve_default_scope_kind(selected_location_group=group) == "location_row"
    assert resolve_default_scope_kind(selected_location_group=None) == "pbs_selection"


def test_hwp_in_row_scope_no_moves_pbs_scope_targets_driver():
    project = _hwp_in_project()
    overlay = (
        PlanningOverlayState.inactive()
        .begin_what_if()
        .with_anchor_years({"PM-C": 19.0})
    )
    groups = discover_meekoppel_locations(project, window_years=5)
    row_group = next(g for g in groups if g.pbs_id == "P1")
    session = _session(project)

    row_prev = preview_meekoppel_with_insight(
        session,
        overlay,
        pbs_ids=frozenset({"P1", "P2"}),
        anchor="later",
        scope_kind="location_row",
        location_group=row_group,
    )
    assert row_prev.blocked_reason is None
    assert row_prev.target_year == 2
    assert row_prev.moves == ()
    insight = row_prev.bundle_insight
    assert insight is not None
    assert insight.scope_kind == "location_row"
    assert insight.scope_task_count == 2

    pbs_prev = preview_meekoppel_with_insight(
        session,
        overlay,
        pbs_ids=frozenset({"P1", "P2"}),
        anchor="later",
        scope_kind="pbs_selection",
        location_group=row_group,
    )
    assert pbs_prev.target_year == 21
    assert len(pbs_prev.moves) >= 1
    pbs_insight = pbs_prev.bundle_insight
    assert pbs_insight is not None
    assert any(d.pm_id == "PM-C" for d in pbs_insight.target_drivers)
    assert pbs_insight.summary_lines[1].startswith("Bepaald door:")


def test_task_rows_delta_is_effective_to_target():
    project = _hwp_in_project()
    overlay = PlanningOverlayState.inactive().begin_what_if()
    group = discover_meekoppel_locations(project, window_years=5)[0]
    preview = preview_meekoppel_rev_tasks(
        project,
        overlay,
        pbs_id_label=group.pbs_id,
        path_label=group.path_label,
        tasks=group.tasks,
        anchor="later",
    )
    insight = build_bundle_insight(
        project,
        overlay,
        scope_kind="location_row",
        scope_label="test",
        tasks=group.tasks,
        preview=preview,
    )
    row = insight.task_rows[0]
    assert row.delta_years == row.target_year - row.effective_year
