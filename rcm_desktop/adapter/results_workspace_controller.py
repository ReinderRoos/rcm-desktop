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
    warmup_lcc: bool
    load_presentation_from_disk: bool


@dataclass(frozen=True)
class RunCompleteOutcome:
    error_message: str | None
    plan: RunCompletePlan | None
    presentation: PresentationProjectTotal | None


@dataclass(frozen=True)
class ValidationHydratePlan:
    load_presentation_from_disk: bool
    start_presentation_rebuild: bool


class ResultsWorkspaceController:
    """Orchestreert post-run state zonder Qt."""

    @staticmethod
    def plan_after_successful_run(
        overlay: PlanningOverlayState,
        *,
        has_presentation_payload: bool,
    ) -> RunCompletePlan:
        inv = WorkspacePresentationCache.invalidation_after_run()
        had_passive = overlay.active and bool(overlay.disabled_pm_ids)
        next_overlay = overlay.after_successful_overlay_run() if overlay.active else overlay
        return RunCompletePlan(
            overlay=next_overlay,
            had_passive_before_run=had_passive,
            invalidate_render_index=inv.reset_render_index,
            warmup_lcc=True,
            load_presentation_from_disk=not has_presentation_payload,
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

    @staticmethod
    def plan_after_validate(
        *,
        has_hydrated_run: bool,
        has_path: bool,
        has_session: bool,
        run_done: bool,
        presentation_rebuild_needed: bool,
        run_runner_busy: bool,
        presentation_runner_busy: bool,
    ) -> ValidationHydratePlan:
        if not has_path or not has_session:
            return ValidationHydratePlan(
                load_presentation_from_disk=False,
                start_presentation_rebuild=False,
            )
        return ValidationHydratePlan(
            load_presentation_from_disk=True,
            start_presentation_rebuild=(
                has_hydrated_run
                and run_done
                and presentation_rebuild_needed
                and not run_runner_busy
                and not presentation_runner_busy
            ),
        )
