"""Integration tests for architecture deepening modules (#4-#10)."""

from __future__ import annotations

from rcm_core.models import FMResult, RCMProject

from rcm_desktop.adapter.editing_session import EditingSession
from rcm_desktop.adapter.loaded_project import LoadedProject
from rcm_desktop.adapter.results_workspace_controller import ResultsWorkspaceController
from rcm_desktop.adapter.run_policy import DEFAULT_RUN_POLICY, RunUserIntent
from rcm_desktop.adapter.run_service import build_run_result
from rcm_desktop.adapter.workspace_presentation_cache import WorkspacePresentationCache


def _project() -> RCMProject:
    return RCMProject.from_dict(
        {
            "config": {"lifecycle_years": 10.0, "modeljaar": 2026},
            "pbs_items": {},
            "functies": {},
            "faalwijzes": {},
            "pm_tasks": {},
            "task_groups": {},
            "effect_klassen": {},
            "fm_effect_links": {},
            "pm_effect_links": {},
            "bibliotheek": {},
        }
    )


def test_run_policy_force_recompute():
    opts = DEFAULT_RUN_POLICY.resolve(user_intent=RunUserIntent.FORCE_RECOMPUTE)
    assert opts.full_recompute is True
    assert opts.parallel is False


def test_build_run_result_factory():
    project = _project()
    fmr = FMResult(
        fm_id="FM-1",
        pbs_id="PBS-1",
        p_failure_lifecycle=0.1,
        expected_failures=1.0,
        expected_raw_downtime_hr=0.0,
        expected_detection_delay_hr=0.0,
        expected_total_downtime_hr=0.0,
        expected_pm_downtime_hr=0.0,
        expected_cm_cost_eur=100.0,
        pm_cost_eur=0.0,
        total_cost_eur=100.0,
        risk_contribution=0.0,
        effect_bijdragen={},
    )
    rr = build_run_result(project, [fmr])
    assert rr.status == "done"
    assert rr.metrics.total_cost_eur == 100.0


def test_workspace_presentation_cache_invalidation_plan():
    plan = WorkspacePresentationCache.invalidation_after_run()
    assert plan.reset_render_index is True
    assert WorkspacePresentationCache.lcc_uses_render_index() is True


def test_loaded_project_projection():
    project = _project()
    loaded = LoadedProject.from_core(project)
    assert loaded.lifecycle_years == 10.0
    assert loaded.core() is project


def test_editing_session_builds_project():
    project = _project()
    session = EditingSession()
    session.load_project(project)
    rebuilt = session.build_project()
    assert rebuilt.config.lifecycle_years == project.config.lifecycle_years


def test_results_workspace_controller_passive_flag():
    from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState

    overlay = PlanningOverlayState.inactive().begin_what_if().set_passive("PM-1", passive=True)
    plan = ResultsWorkspaceController.plan_after_successful_run(overlay)
    assert plan.had_passive_before_run is True
    assert plan.invalidate_render_index is True
