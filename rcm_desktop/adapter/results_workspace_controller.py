"""Qt-free orchestration for resultatenwerkruimte (adapter deepening)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.presentation_cache_service import PresentationProjectTotal
from rcm_desktop.adapter.run_service import RunResult
from rcm_desktop.adapter.workspace_presentation_cache import WorkspacePresentationCache


@dataclass(frozen=True)
class RunCompletePlan:
    overlay: PlanningOverlayState
    had_passive_before_run: bool
    invalidate_render_index: bool


@dataclass(frozen=True)
class RunCompleteOutcome:
    error_message: str | None
    plan: RunCompletePlan | None
    presentation: PresentationProjectTotal | None


class ResultsWorkspaceController:
    """Orchestreert post-run state zonder Qt."""

    @staticmethod
    def plan_after_successful_run(
        overlay: PlanningOverlayState,
    ) -> RunCompletePlan:
        inv = WorkspacePresentationCache.invalidation_after_run()
        had_passive = overlay.active and bool(overlay.disabled_pm_ids)
        next_overlay = overlay.after_successful_overlay_run() if overlay.active else overlay
        return RunCompletePlan(
            overlay=next_overlay,
            had_passive_before_run=had_passive,
            invalidate_render_index=inv.reset_render_index,
        )

    @staticmethod
    def handle_run_result(
        result: RunResult,
        *,
        presentation: PresentationProjectTotal | None,
    ) -> RunCompleteOutcome:
        if result.status != "done":
            return RunCompleteOutcome(
                error_message=result.summary,
                plan=None,
                presentation=None,
            )
        return RunCompleteOutcome(
            error_message=None,
            plan=None,
            presentation=presentation,
        )
