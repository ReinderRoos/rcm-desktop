"""Qt-vrije modus-builders voor de resultatenwerkruimte (slice 41)."""

from __future__ import annotations

from dataclasses import dataclass
from rcm_desktop.adapter.contribution_chart_service import ContributionRow, build_contribution_rows
from rcm_desktop.adapter.lcc_render_cache_service import build_lcc_curve_cache_key
from rcm_desktop.adapter.lcc_view_service import LCCView, build_lcc_view as build_lcc_view_core
from rcm_desktop.adapter.presentation_cache_service import PresentationProjectTotal
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.result_filter_service import filter_run_result
from rcm_desktop.adapter.result_view_service import (
    FMResultRow,
    apply_presentation_scale_to_fm_rows,
    enrich_fm_rows_with_nmf_rf,
)
from rcm_desktop.adapter.simulation_engine_service import FMMCResultRow
from rcm_desktop.adapter.simulation_job_service import RunMode
from rcm_desktop.adapter.simulation_workspace_service import fm_detail_source_for_run_mode
from rcm_desktop.adapter.results_workspace_state import (
    MODE_BIJDRAGEN,
    MODE_FM_DETAIL,
    MODE_LCC,
    WorkspaceStateSnapshot,
)
from rcm_desktop.adapter.workspace_render_index import SLOT_CURRENT, WorkspaceRenderIndex


@dataclass(frozen=True)
class FMDetailView:
    fm_rows: tuple[FMResultRow, ...] = ()
    mc_rows: tuple[FMMCResultRow, ...] = ()
    is_mc_mode: bool = False
    empty_message: str = ""


@dataclass(frozen=True)
class BijdragenView:
    contribution_rows: tuple[ContributionRow, ...]
    cache_modus_key: str
    from_presentation_cache: bool


def build_workspace_cache_modus_key(snapshot: WorkspaceStateSnapshot) -> str:
    if snapshot.modus == MODE_BIJDRAGEN:
        p = snapshot.contribution_presentation
        year = p.year_choice if p.year_choice == "average" else int(p.year_choice)
        filt = snapshot.effect_nb_filter
        filt_key = (
            "all"
            if filt.is_all()
            else ",".join(sorted(filt.selected_klasse_ids))
        )
        return (
            f"{snapshot.modus}|{snapshot.source}|{snapshot.metric}|{snapshot.top_n}|"
            f"{p.horizon}|{year}|{p.unavailability_display}|nb:{filt_key}"
        )
    if snapshot.modus == MODE_LCC:
        return build_lcc_curve_cache_key(snapshot)
    if snapshot.modus == MODE_FM_DETAIL:
        filt = snapshot.effect_nb_filter
        filt_key = "all" if filt.is_all() else ",".join(sorted(filt.selected_klasse_ids))
        return f"fm|{snapshot.scope_id}|nb:{filt_key}"
    return snapshot.modus


def _contribution_cache_matches(
    snapshot: WorkspaceStateSnapshot,
    project_total_presentation: PresentationProjectTotal | None,
) -> bool:
    cached = project_total_presentation
    if cached is None or snapshot.scope_id is not None:
        return False
    p = snapshot.contribution_presentation
    filt = snapshot.effect_nb_filter
    return (
        snapshot.source == cached.contribution_source
        and snapshot.metric == cached.contribution_metric
        and snapshot.top_n == cached.contribution_top_n
        and p == cached.contribution_presentation
        and filt.is_all()
    )


def build_fm_detail_view(
    session: ProjectSession,
    snapshot: WorkspaceStateSnapshot,
    *,
    run_mode: RunMode = RunMode.ANALYTICAL,
) -> FMDetailView | None:
    source = fm_detail_source_for_run_mode(run_mode, session)
    if source == "analytical":
        if not session.has_completed_run():
            return None
        project = session.loaded.core()
        run = session.run
        assert run is not None
        view = filter_run_result(project, run, snapshot.scope_id)
        rows = apply_presentation_scale_to_fm_rows(
            project,
            run.fm_core_results,
            view.fm_rows,
            presentation=snapshot.contribution_presentation,
            nb_filter=snapshot.effect_nb_filter,
        )
        rows = enrich_fm_rows_with_nmf_rf(
            project, out=rows, nb_filter=snapshot.effect_nb_filter
        )
        return FMDetailView(fm_rows=rows, is_mc_mode=False)

    if source == "mc_bands":
        assert session.mc_run is not None
        from rcm_desktop import messages

        return FMDetailView(
            mc_rows=session.mc_run.rows,
            is_mc_mode=True,
            empty_message="",
        )
    from rcm_desktop import messages

    empty_msg = (
        messages.SIMULATION_MC_FM_EMPTY_CANCELLED
        if source == "mc_cancelled"
        else messages.SIMULATION_RUN_MODE_MONTE_CARLO + " — niet gestart"
    )
    return FMDetailView(is_mc_mode=True, empty_message=empty_msg)


def build_bijdragen_view(
    session: ProjectSession,
    snapshot: WorkspaceStateSnapshot,
    *,
    render_index: WorkspaceRenderIndex,
    project_total_presentation: PresentationProjectTotal | None,
    slot: str = SLOT_CURRENT,
) -> BijdragenView | None:
    if not session.has_completed_run():
        return None
    cache_modus = build_workspace_cache_modus_key(snapshot)
    if _contribution_cache_matches(snapshot, project_total_presentation):
        assert project_total_presentation is not None
        rows = project_total_presentation.contribution_rows
        return BijdragenView(
            contribution_rows=rows,
            cache_modus_key=cache_modus,
            from_presentation_cache=True,
        )
    project = session.loaded.core()
    run = session.run
    assert run is not None
    rows = render_index.get_or_build(
        slot,
        snapshot.scope_id,
        cache_modus,
        lambda: build_contribution_rows(
            project,
            run,
            source=snapshot.source,
            metric=snapshot.metric,
            top_n=snapshot.top_n,
            scope_id=snapshot.scope_id,
            presentation=snapshot.contribution_presentation,
            effect_nb_filter=snapshot.effect_nb_filter,
        ),
    )
    return BijdragenView(
        contribution_rows=tuple(rows),
        cache_modus_key=cache_modus,
        from_presentation_cache=False,
    )


def build_lcc_view(
    session: ProjectSession,
    snapshot: WorkspaceStateSnapshot,
    *,
    render_index: WorkspaceRenderIndex,
    prev_snapshot: WorkspaceStateSnapshot | None,
    slot: str = SLOT_CURRENT,
) -> LCCView | None:
    if not session.has_completed_run():
        return None
    project = session.loaded.core()
    run = session.run
    assert run is not None
    return build_lcc_view_core(
        project,
        run,
        snapshot,
        render_index=render_index,
        prev_snapshot=prev_snapshot,
        slot=slot,
    )
