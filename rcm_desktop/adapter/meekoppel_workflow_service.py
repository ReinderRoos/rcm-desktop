"""Meekoppel workflow seam for preview/apply orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from rcm_desktop import messages
from rcm_desktop.adapter.meekoppel_apply_service import (
    MeekoppelAnchor,
    MeekoppelLocationPreview,
    apply_meekoppel_rev_tasks,
)
from rcm_desktop.adapter.meekoppel_bundle_insight_service import (
    BundleScopeKind,
    preview_meekoppel_with_insight,
    resolve_scope_bundle,
)
from rcm_desktop.adapter.meekoppelkansen_discovery_service import MeekoppelLocationGroup
from rcm_desktop.adapter.meekoppel_panel_service import apply_meekoppel, preview_meekoppel
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.planning_whatif_service import WhatIfActionResult
from rcm_desktop.adapter.project_session import ProjectSession

WorkflowStatus = Literal["ok", "validation", "blocked", "system"]


@dataclass(frozen=True)
class WorkflowResult:
    status: WorkflowStatus
    user_message: str
    preview_payload: MeekoppelLocationPreview | None
    telemetry_flags: frozenset[str]
    overlay: PlanningOverlayState


def _as_validation(overlay: PlanningOverlayState, message: str) -> WorkflowResult:
    return WorkflowResult(
        status="validation",
        user_message=message,
        preview_payload=None,
        telemetry_flags=frozenset({"meekoppel_workflow_v2", "validation"}),
        overlay=overlay,
    )


def _preview_blocked_result(
    overlay: PlanningOverlayState,
    preview: MeekoppelLocationPreview,
) -> WorkflowResult:
    return WorkflowResult(
        status="blocked",
        user_message=preview.blocked_reason or messages.WORKSPACE_MEEKOPPEL_SELECT_MIN_REV,
        preview_payload=preview,
        telemetry_flags=frozenset({"meekoppel_workflow_v2", "blocked"}),
        overlay=overlay,
    )


class MeekoppelWorkflowService:
    """Single orchestration seam for v2 meekoppel flow."""

    def preview(
        self,
        *,
        session: ProjectSession,
        overlay: PlanningOverlayState,
        pbs_ids: frozenset[str],
        anchor: MeekoppelAnchor,
        scope_kind: BundleScopeKind | None = None,
        location_group: MeekoppelLocationGroup | None = None,
    ) -> WorkflowResult:
        if not pbs_ids:
            return _as_validation(overlay, messages.WORKSPACE_MEEKOPPEL_SELECT_PBS)

        preview = preview_meekoppel_with_insight(
            session,
            overlay,
            pbs_ids=pbs_ids,
            anchor=anchor,
            scope_kind=scope_kind,
            location_group=location_group,
        )
        if preview.blocked_reason:
            return _preview_blocked_result(overlay, preview)

        return WorkflowResult(
            status="ok",
            user_message="",
            preview_payload=preview,
            telemetry_flags=frozenset({"meekoppel_workflow_v2", "preview"}),
            overlay=overlay,
        )

    def apply(
        self,
        *,
        session: ProjectSession,
        overlay: PlanningOverlayState,
        pbs_ids: frozenset[str],
        anchor: MeekoppelAnchor,
        scope_kind: BundleScopeKind | None = None,
        location_group: MeekoppelLocationGroup | None = None,
        checked_pm_ids: frozenset[str] | None = None,
    ) -> WorkflowResult:
        if not pbs_ids:
            return _as_validation(overlay, messages.WORKSPACE_MEEKOPPEL_SELECT_PBS)

        if checked_pm_ids is not None and scope_kind is not None:
            result = self._apply_checked_scope(
                session=session,
                overlay=overlay,
                pbs_ids=pbs_ids,
                anchor=anchor,
                scope_kind=scope_kind,
                location_group=location_group,
                checked_pm_ids=checked_pm_ids,
            )
        else:
            result = apply_meekoppel(
                session,
                overlay,
                pbs_ids,
                anchor=anchor,
            )
        if result.error:
            status: WorkflowStatus = "blocked"
            telemetry = frozenset({"meekoppel_workflow_v2", "blocked"})
            if result.error == messages.WORKSPACE_MEEKOPPEL_SELECT_PBS:
                status = "validation"
                telemetry = frozenset({"meekoppel_workflow_v2", "validation"})
            return WorkflowResult(
                status=status,
                user_message=result.error,
                preview_payload=None,
                telemetry_flags=telemetry,
                overlay=overlay,
            )

        return WorkflowResult(
            status="ok",
            user_message="",
            preview_payload=None,
            telemetry_flags=frozenset({"meekoppel_workflow_v2", "apply"}),
            overlay=result.overlay,
        )

    def _apply_checked_scope(
        self,
        *,
        session: ProjectSession,
        overlay: PlanningOverlayState,
        pbs_ids: frozenset[str],
        anchor: MeekoppelAnchor,
        scope_kind: BundleScopeKind,
        location_group: MeekoppelLocationGroup | None,
        checked_pm_ids: frozenset[str],
    ) -> WhatIfActionResult:
        bundle = resolve_scope_bundle(
            session,
            scope_kind,
            pbs_ids=pbs_ids,
            location_group=location_group,
        )
        if bundle is None:
            return WhatIfActionResult(
                overlay=overlay,
                error=messages.WORKSPACE_MEEKOPPEL_SELECT_PBS,
            )
        pbs_id_label, path_label, tasks = bundle
        filtered = tuple(t for t in tasks if t.pm_id in checked_pm_ids)
        return apply_meekoppel_rev_tasks(
            session.loaded.core(),
            overlay,
            pbs_id_label=pbs_id_label,
            path_label=path_label,
            tasks=filtered,
            anchor=anchor,
        )
