"""Of en hoe een rapport gegenereerd kan worden (slice 57)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_desktop import messages
from rcm_core.models import RCMProject

from rcm_desktop.adapter.compare_slot_state import CompareSlotState
from rcm_desktop.adapter.report_functie_selection_service import select_report_functies
from rcm_desktop.adapter.report_options import ReportOptions
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.report_run_source_service import ReportRunBundle, resolve_report_run_bundle
from rcm_desktop.adapter.run_service import RunResult


@dataclass(frozen=True)
class ReportEligibility:
    can_generate: bool
    reason: str


@dataclass(frozen=True)
class ReportWorkspaceAssessment:
    eligible: bool
    reason: str
    bundle: ReportRunBundle | None


@dataclass(frozen=True)
class ReportPreviewCounts:
    mode: str
    nb_function_pages: int
    cost_function_pages: int


def assess_report_workspace(
    *,
    last_run: RunResult | None,
    compare_slots: CompareSlotState | None,
    live_overlay: PlanningOverlayState | None = None,
) -> ReportWorkspaceAssessment:
    bundle = resolve_report_run_bundle(
        last_run=last_run,
        compare_slots=compare_slots,
        live_overlay=live_overlay,
    )
    if bundle is not None:
        return ReportWorkspaceAssessment(True, "", bundle)
    return ReportWorkspaceAssessment(
        False,
        messages.REPORT_INELIGIBLE_NO_RUN,
        None,
    )


def assess_report_eligibility(
    *,
    last_run: RunResult | None,
    compare_slots: CompareSlotState | None,
) -> ReportEligibility:
    assessment = assess_report_workspace(
        last_run=last_run,
        compare_slots=compare_slots,
        live_overlay=None,
    )
    return ReportEligibility(assessment.eligible, assessment.reason)


def preview_report_counts(
    project: RCMProject,
    bundle: ReportRunBundle,
    options: ReportOptions,
) -> ReportPreviewCounts:
    primary = bundle.scenarios[0]
    selection = select_report_functies(
        project,
        primary,
        scope_id=options.scope_id,
        nb_threshold_pct=options.nb_threshold_pct,
        cost_threshold_pct=options.cost_threshold_pct,
        include_below_threshold=options.include_below_threshold,
    )
    return ReportPreviewCounts(
        mode=bundle.mode,
        nb_function_pages=len(selection.nb_chapters),
        cost_function_pages=len(selection.cost_chapters),
    )


