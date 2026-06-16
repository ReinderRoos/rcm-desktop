"""Build Top10/LCC views for A/B compare (slice 56)."""

from __future__ import annotations

from dataclasses import dataclass, replace

from rcm_desktop.adapter.compare_slot_state import (
    COMPARE_SLOT_A,
    COMPARE_SLOT_B,
    CompareSlotSnapshot,
    CompareSlotState,
)
from rcm_core.models import RCMProject

from rcm_desktop.adapter.lcc_view_service import LCCView
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.results_workspace_state import WorkspaceStateSnapshot
from rcm_desktop.adapter.run_service import RunResult
from rcm_desktop.adapter.simulation_engine_service import build_run_result_from_mc_p50
from rcm_desktop.adapter.simulation_job_service import RunMode
from rcm_desktop.adapter.workspace_render_index import (
    SLOT_A,
    SLOT_B,
    WorkspaceRenderIndex,
)
from rcm_desktop.adapter.workspace_view_service import (
    BijdragenView,
    FMDetailView,
    build_bijdragen_view,
    build_fm_detail_view_for_compare_slot,
    build_lcc_view,
)


@dataclass(frozen=True)
class ComparePanel:
    slot_key: str
    label: str
    filled: bool
    bijdragen: BijdragenView | None = None
    lcc: LCCView | None = None
    fm: FMDetailView | None = None


def workspace_snapshot_for_slot(
    workspace: WorkspaceStateSnapshot,
    slot: CompareSlotSnapshot,
) -> WorkspaceStateSnapshot:
    return replace(workspace, planning_overlay=slot.overlay_at_run)


def resolve_compare_slot_run(
    project: RCMProject,
    slot: CompareSlotSnapshot,
) -> RunResult | None:
    """Presentation run for a frozen compare slot (MC P50 rollup when needed)."""
    if slot.run_result.status != "done":
        return None
    if (
        slot.run_mode is RunMode.MONTE_CARLO
        and slot.mc_run is not None
        and slot.mc_run.status == "done"
        and slot.mc_run.fm_results
    ):
        rebuilt = build_run_result_from_mc_p50(project, slot.mc_run)
        if rebuilt.fm_core_results:
            return rebuilt
    if slot.run_result.fm_core_results:
        return slot.run_result
    return None


def _session_for_slot(
    session: ProjectSession,
    slot: CompareSlotSnapshot,
) -> ProjectSession:
    loaded = session.loaded
    project = loaded.core()
    run = resolve_compare_slot_run(project, slot) or slot.run_result
    if slot.run_mode is RunMode.MONTE_CARLO and slot.mc_run is not None:
        return ProjectSession.from_parts(
            loaded,
            path=session.path,
            run=run,
            mc_run=slot.mc_run,
        )
    return ProjectSession.from_parts(loaded, path=session.path, run=run)


def build_bijdragen_compare_panels(
    session: ProjectSession,
    workspace: WorkspaceStateSnapshot,
    *,
    slots: CompareSlotState,
    render_index: WorkspaceRenderIndex,
    project_total_presentation: object | None,
) -> tuple[ComparePanel, ...]:
    out: list[ComparePanel] = []
    for slot_key, index_slot in (
        (COMPARE_SLOT_A, SLOT_A),
        (COMPARE_SLOT_B, SLOT_B),
    ):
        snap = slots.get(slot_key)
        if snap is None:
            out.append(ComparePanel(slot_key=slot_key, label=slot_key, filled=False))
            continue
        slot_session = _session_for_slot(session, snap)
        effective = workspace_snapshot_for_slot(workspace, snap)
        view = build_bijdragen_view(
            slot_session,
            effective,
            render_index=render_index,
            project_total_presentation=None,
            slot=index_slot,
        )
        out.append(
            ComparePanel(
                slot_key=slot_key,
                label=snap.label,
                filled=True,
                bijdragen=view,
            )
        )
    return tuple(out)


def build_lcc_compare_panels(
    session: ProjectSession,
    workspace: WorkspaceStateSnapshot,
    *,
    slots: CompareSlotState,
    render_index: WorkspaceRenderIndex,
    prev_snapshot: WorkspaceStateSnapshot | None,
) -> tuple[ComparePanel, ...]:
    out: list[ComparePanel] = []
    for slot_key, index_slot in (
        (COMPARE_SLOT_A, SLOT_A),
        (COMPARE_SLOT_B, SLOT_B),
    ):
        snap = slots.get(slot_key)
        if snap is None:
            out.append(ComparePanel(slot_key=slot_key, label=slot_key, filled=False))
            continue
        slot_session = _session_for_slot(session, snap)
        effective = workspace_snapshot_for_slot(workspace, snap)
        view = build_lcc_view(
            slot_session,
            effective,
            render_index=render_index,
            prev_snapshot=prev_snapshot,
            slot=index_slot,
            run_mode=RunMode.ANALYTICAL,
        )
        out.append(
            ComparePanel(
                slot_key=slot_key,
                label=snap.label,
                filled=True,
                lcc=view,
            )
        )
    return tuple(out)


def build_fm_compare_panels(
    session: ProjectSession,
    workspace: WorkspaceStateSnapshot,
    *,
    slots: CompareSlotState,
) -> tuple[ComparePanel, ...]:
    out: list[ComparePanel] = []
    for slot_key in (COMPARE_SLOT_A, COMPARE_SLOT_B):
        snap = slots.get(slot_key)
        if snap is None:
            out.append(ComparePanel(slot_key=slot_key, label=slot_key, filled=False))
            continue
        slot_session = _session_for_slot(session, snap)
        effective = workspace_snapshot_for_slot(workspace, snap)
        view = build_fm_detail_view_for_compare_slot(slot_session, snap, effective)
        out.append(
            ComparePanel(
                slot_key=slot_key,
                label=snap.label,
                filled=True,
                fm=view,
            )
        )
    return tuple(out)
