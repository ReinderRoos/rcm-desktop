"""Qt-vrije orchestratie voor resultatenwerkruimte snapshot-ticks (slice 61).

``plan_ui_sync`` — toolbar-zichtbaarheid, modus-sync, compare-chrome, collapse.
``plan_render`` / ``plan_workspace_tick`` — detail-presentatie zonder Qt.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from rcm_desktop.adapter.compare_split_layout_service import compute_compare_split_layout
from rcm_desktop.adapter.compare_slot_state import (
    COMPARE_SLOT_A,
    COMPARE_SLOT_B,
    CompareSlotState,
)
from rcm_desktop.adapter.compare_view_service import (
    ComparePanel,
    build_bijdragen_compare_panels,
    build_fm_compare_panels,
    build_lcc_compare_panels,
)
from rcm_desktop.adapter.faalwijze_analyse_service import (
    FaalwijzePresentationBundle,
    FM_COMPARE_VIEW_TABLE,
    build_faalwijze_bundle_for_compare,
    build_faalwijze_bundle_for_fm_view,
)
from rcm_desktop.adapter.lcc_type_filter import LCCTypeFilterSet
from rcm_desktop.adapter.lcc_view_service import LCCView
from rcm_desktop.adapter.workspace_lcc_preset_service import (
    effective_lcc_filters,
    lcc_preset_for_view,
)
from rcm_desktop.adapter.presentation_cache_service import PresentationProjectTotal
from rcm_desktop.adapter.project_session import ProjectSession
from rcm_desktop.adapter.simulation_job_service import RunMode
from rcm_desktop.adapter.simulation_workspace_service import live_run_available
from rcm_desktop.adapter.results_workspace_state import (
    FM_VIEW_MODE_TABLE,
    METRIC_FAALMOMENTEN,
    METRIC_KOSTEN,
    METRIC_NIET_BESCHIKBAARHEID,
    MODE_BIJDRAGEN,
    MODE_FM_DETAIL,
    MODE_LCC,
    ContributionYearChoice,
    WorkspaceStateSnapshot,
)
from rcm_desktop.adapter.workspace_detail_render_scope import (
    RenderSplitDepth,
    required_detail_builders,
    should_refresh_kpi_for_render_depth,
    workspace_detail_split_render_depth,
)
from rcm_desktop.adapter.workspace_render_index import WorkspaceRenderIndex
from rcm_desktop.adapter.workspace_view_registry import (
    SIDE_INPUT,
    WORKSPACE_VIEW_REGISTRY,
    WorkspaceChromeProfile,
    chrome_for_view,
    detail_stack_key_for_view,
    enabled_views_for_side,
    rail_label_for_view,
    view_by_id,
)
from rcm_desktop.adapter.workspace_view_service import (
    BijdragenView,
    FMDetailView,
    build_bijdragen_view,
    build_fm_detail_view,
    build_lcc_view,
)

RenderKind = Literal[
    "empty",
    "compare_placeholder",
    "fm",
    "bijdragen",
    "lcc",
    "bijdragen_compare",
    "lcc_compare",
    "fm_compare",
]

_COLLAPSE_EXPANDED = "▼"
_COLLAPSE_COLLAPSED = "▶"


def _on_output_side(snapshot: WorkspaceStateSnapshot) -> bool:
    return snapshot.workspace_side != SIDE_INPUT


@dataclass(frozen=True)
class WorkspaceViewDropdownItem:
    view_id: str
    label: str
    rail_label: str
    enabled: bool
    selected: bool


@dataclass(frozen=True)
class WorkspaceNavigationPlan:
    workspace_side: str
    active_view_id: str
    side_input_checked: bool
    side_output_checked: bool
    dropdown_items: tuple[WorkspaceViewDropdownItem, ...]
    show_input_placeholder: bool
    show_input_entity_grid: bool


@dataclass(frozen=True)
class BijdragenToolbarPlan:
    top10_subbar_visible: bool
    horizon_lifecycle_visible: bool
    horizon_per_year_visible: bool
    year_combo_visible: bool
    nb_hours_visible: bool
    nb_percent_visible: bool
    effect_nb_filter_visible: bool
    horizon_lifecycle_checked: bool
    horizon_per_year_checked: bool
    nb_hours_checked: bool
    nb_percent_checked: bool
    year_choice: ContributionYearChoice


@dataclass(frozen=True)
class LccToolbarVisibilityPlan:
    filter_bar_visible: bool
    pm_type_filters_visible: bool
    metric_combo_visible: bool
    effect_nb_filter_visible: bool
    show_all_years_visible: bool
    year_summary_label_visible: bool
    meekoppel_panel_visible: bool
    cm_filter_visible: bool
    cm_preset_button_visible: bool
    lcc_filters: LCCTypeFilterSet
    contribution_subbar_visible: bool = False
    nb_display_toggles_visible: bool = False


@dataclass(frozen=True)
class FmToolbarPlan:
    batch_faalwijzen_visible: bool
    new_fm_visible: bool
    column_crop_visible: bool
    fm_inspector_visible: bool
    clear_fm_inspector: bool
    delete_fm_visible: bool = False
    effect_nb_filter_visible: bool = True
    metric_combo_visible: bool = False
    horizon_lifecycle_visible: bool = False
    horizon_per_year_visible: bool = False
    year_combo_visible: bool = False
    horizon_lifecycle_checked: bool = True
    horizon_per_year_checked: bool = False
    year_choice: str | int = "average"
    fm_compare_nmf_rf_toggle_visible: bool = False
    fm_compare_view_toggle_visible: bool = False
    fm_view_mode: str = FM_COMPARE_VIEW_TABLE
    fm_show_nmf_rf: bool = False


@dataclass(frozen=True)
class CompareChromePlan:
    compare_mode_checked: bool
    bijdragen_single_visible: bool
    bijdragen_compare_visible: bool
    bijdragen_chart_label_visible: bool
    lcc_single_visible: bool
    lcc_compare_visible: bool
    lcc_empty_state_visible: bool
    fm_single_visible: bool = True
    fm_compare_visible: bool = False


@dataclass(frozen=True)
class CollapsePanelPlan:
    chrome_visible: bool
    content_visible: bool
    collapse_glyph: str
    chrome_enabled: bool


@dataclass(frozen=True)
class MeekoppelCollapsePlan:
    chrome_visible: bool
    content_visible: bool
    collapse_glyph: str
    chrome_enabled: bool
    ensure_whatif_if_expanding: bool


@dataclass(frozen=True)
class CollapsePanelsPlan:
    kpi: CollapsePanelPlan | None
    lcc_whatif: CollapsePanelPlan | None
    meekoppel: MeekoppelCollapsePlan | None


@dataclass(frozen=True)
class SharedToolbarPlan:
    effect_nb_filter_in_shared_row: bool


@dataclass(frozen=True)
class WorkspaceChromeFooterPlan:
    visible: bool
    context_label: str
    middle_chrome_visible: bool
    lcc_measure_stack_visible: bool
    lcc_whatif_light_visible: bool
    fm_toolbar: FmToolbarPlan | None = None
    lcc_toolbar: LccToolbarVisibilityPlan | None = None


@dataclass(frozen=True)
class WorkspaceUiSyncPlan:
    detail_page_modus: str
    modus_button: str
    view_title: str
    navigation: WorkspaceNavigationPlan
    source_toggle: str
    metric: str
    shared_toolbar: SharedToolbarPlan
    chrome_footer: WorkspaceChromeFooterPlan
    top10_subbar_visible: bool
    status_strip_visible: bool
    bijdragen: BijdragenToolbarPlan | None
    lcc_toolbar: LccToolbarVisibilityPlan | None
    fm_toolbar: FmToolbarPlan | None
    compare: CompareChromePlan
    collapse: CollapsePanelsPlan
    refresh_kpi: bool
    pbs_tree_extended_selection: bool
    scope_id: str | None


@dataclass(frozen=True)
class WorkspaceRenderContext:
    session: ProjectSession | None
    compare_slots: CompareSlotState
    project_total_presentation: PresentationProjectTotal | None
    render_index: WorkspaceRenderIndex
    prev_lcc_snapshot: WorkspaceStateSnapshot | None
    run_mode: RunMode = RunMode.ANALYTICAL


@dataclass(frozen=True)
class RenderPlan:
    kind: RenderKind
    fm: FMDetailView | None = None
    bijdragen: BijdragenView | None = None
    lcc: LCCView | None = None
    compare_panels: tuple[ComparePanel, ...] | None = None
    faalwijze_bundle: FaalwijzePresentationBundle | None = None


@dataclass(frozen=True)
class WorkspaceTickPlan:
    ui_sync: WorkspaceUiSyncPlan
    render: RenderPlan
    split_depth: RenderSplitDepth


def plan_compare_chrome(snapshot: WorkspaceStateSnapshot) -> CompareChromePlan:
    """Publieke planner voor compare-pane-zichtbaarheid (ui_sync + render-only ticks)."""
    return _plan_compare_chrome(snapshot)


def _plan_navigation(snapshot: WorkspaceStateSnapshot) -> WorkspaceNavigationPlan:
    active_entry = view_by_id(WORKSPACE_VIEW_REGISTRY, snapshot.active_view_id)
    on_input_side = snapshot.workspace_side == SIDE_INPUT
    input_view_ready = (
        active_entry is not None
        and active_entry.side == SIDE_INPUT
        and active_entry.enabled
    )
    show_input_entity_grid = on_input_side and input_view_ready
    show_input_placeholder = on_input_side and not input_view_ready
    dropdown_items = tuple(
        WorkspaceViewDropdownItem(
            view_id=entry.view_id,
            label=entry.label,
            rail_label=rail_label_for_view(entry),
            enabled=entry.enabled,
            selected=entry.view_id == snapshot.active_view_id,
        )
        for entry in enabled_views_for_side(WORKSPACE_VIEW_REGISTRY, snapshot.workspace_side)
    )
    return WorkspaceNavigationPlan(
        workspace_side=snapshot.workspace_side,
        active_view_id=snapshot.active_view_id,
        side_input_checked=snapshot.workspace_side == SIDE_INPUT,
        side_output_checked=snapshot.workspace_side != SIDE_INPUT,
        dropdown_items=dropdown_items,
        show_input_placeholder=show_input_placeholder,
        show_input_entity_grid=show_input_entity_grid,
    )


def _plan_status_strip_visible(snapshot: WorkspaceStateSnapshot) -> bool:
    """Validatiestrip overal verborgen (slice 105 issue 30, optie C)."""
    return False


def _plan_top10_subbar_visible(snapshot: WorkspaceStateSnapshot) -> bool:
    """Top-10/metric-subbar alleen op output-chrome (slice 105 issue 18)."""
    if not _on_output_side(snapshot):
        return False
    active_entry = view_by_id(WORKSPACE_VIEW_REGISTRY, snapshot.active_view_id)
    if active_entry is not None and active_entry.side == SIDE_INPUT:
        return False
    if _plan_bijdragen_toolbar(snapshot) is not None:
        return True
    profile = chrome_for_view(WORKSPACE_VIEW_REGISTRY, snapshot.active_view_id)
    if profile is None:
        return False
    if profile.allows_new_fm or profile.toolbar_family == "input_grid":
        return False
    if profile.shows_lcc_contribution_subbar:
        return True
    if profile.toolbar_family == "fm" and not profile.allows_new_fm:
        return False
    return False


def _plan_bijdragen_toolbar(
    snapshot: WorkspaceStateSnapshot,
) -> BijdragenToolbarPlan | None:
    if not _on_output_side(snapshot) or snapshot.modus != MODE_BIJDRAGEN:
        return None
    pres = snapshot.contribution_presentation
    horizon_metric = snapshot.metric in (
        METRIC_FAALMOMENTEN,
        METRIC_NIET_BESCHIKBAARHEID,
    )
    year_combo_visible = horizon_metric and pres.horizon == "per_year"
    nb_visible = snapshot.metric == METRIC_NIET_BESCHIKBAARHEID
    return BijdragenToolbarPlan(
        top10_subbar_visible=True,
        horizon_lifecycle_visible=horizon_metric,
        horizon_per_year_visible=horizon_metric,
        year_combo_visible=year_combo_visible,
        nb_hours_visible=nb_visible,
        nb_percent_visible=nb_visible,
        effect_nb_filter_visible=nb_visible,
        horizon_lifecycle_checked=pres.horizon == "lifecycle",
        horizon_per_year_checked=pres.horizon == "per_year",
        nb_hours_checked=pres.unavailability_display == "hours",
        nb_percent_checked=pres.unavailability_display == "percent",
        year_choice=pres.year_choice,
    )


def _plan_lcc_toolbar(
    snapshot: WorkspaceStateSnapshot,
    profile: WorkspaceChromeProfile,
) -> LccToolbarVisibilityPlan:
    nb_visible = snapshot.metric == METRIC_NIET_BESCHIKBAARHEID
    whatif_active = snapshot.planning_overlay.active
    preset = effective_lcc_filters(snapshot)
    view_preset = lcc_preset_for_view(snapshot.active_view_id)
    cm_controls = view_preset is None or view_preset.cm_enabled
    return LccToolbarVisibilityPlan(
        filter_bar_visible=True,
        pm_type_filters_visible=snapshot.metric == METRIC_KOSTEN,
        metric_combo_visible=profile.shows_metric_combo,
        effect_nb_filter_visible=nb_visible and profile.shows_nb_effect_filter,
        show_all_years_visible=True,
        year_summary_label_visible=True,
        meekoppel_panel_visible=whatif_active,
        cm_filter_visible=cm_controls,
        cm_preset_button_visible=cm_controls,
        lcc_filters=preset,
        contribution_subbar_visible=profile.shows_lcc_contribution_subbar,
        nb_display_toggles_visible=nb_visible and profile.shows_lcc_contribution_subbar,
    )


def _plan_input_faalwijzen_chrome(profile: WorkspaceChromeProfile) -> FmToolbarPlan:
    return FmToolbarPlan(
        batch_faalwijzen_visible=profile.shows_batch_faalwijzen,
        new_fm_visible=profile.allows_new_fm,
        column_crop_visible=profile.shows_column_crop,
        fm_inspector_visible=False,
        clear_fm_inspector=False,
        delete_fm_visible=profile.allows_delete_fm,
        effect_nb_filter_visible=profile.shows_nb_effect_filter,
    )


def _plan_output_fm_results_toolbar(
    snapshot: WorkspaceStateSnapshot,
    profile: WorkspaceChromeProfile,
) -> FmToolbarPlan:
    pres = snapshot.contribution_presentation
    fm_compare = snapshot.compare_mode and profile.shows_fm_compare_toggles
    return FmToolbarPlan(
        batch_faalwijzen_visible=profile.shows_batch_faalwijzen,
        new_fm_visible=profile.allows_new_fm,
        column_crop_visible=profile.shows_column_crop and not fm_compare,
        fm_inspector_visible=profile.shows_fm_inspector
        and not fm_compare
        and snapshot.fm_inspector_mode
        and snapshot.fm_view_mode == FM_VIEW_MODE_TABLE,
        clear_fm_inspector=fm_compare,
        fm_compare_nmf_rf_toggle_visible=profile.shows_fm_compare_toggles,
        fm_compare_view_toggle_visible=profile.shows_fm_compare_toggles,
        delete_fm_visible=False,
        effect_nb_filter_visible=profile.shows_nb_effect_filter,
        metric_combo_visible=profile.shows_metric_combo,
        horizon_lifecycle_visible=profile.shows_horizon_controls,
        horizon_per_year_visible=profile.shows_horizon_controls,
        year_combo_visible=profile.shows_horizon_controls and pres.horizon == "per_year",
        horizon_lifecycle_checked=pres.horizon == "lifecycle",
        horizon_per_year_checked=pres.horizon == "per_year",
        year_choice=pres.year_choice,
        fm_view_mode=snapshot.fm_view_mode,
        fm_show_nmf_rf=snapshot.fm_show_nmf_rf,
    )


def _plan_fm_toolbar(snapshot: WorkspaceStateSnapshot) -> FmToolbarPlan:
    profile = chrome_for_view(WORKSPACE_VIEW_REGISTRY, snapshot.active_view_id)
    if profile is None or profile.toolbar_family != "fm":
        return _inactive_fm_toolbar()
    if profile.allows_new_fm:
        return _plan_input_faalwijzen_chrome(profile)
    return _plan_output_fm_results_toolbar(snapshot, profile)


def plan_chrome_toolbar(snapshot: WorkspaceStateSnapshot) -> FmToolbarPlan | LccToolbarVisibilityPlan | None:
    """Declaratieve toolbar-planning uit chrome-profiel (slice 105 issue 12)."""
    if not _on_output_side(snapshot):
        return None
    profile = chrome_for_view(WORKSPACE_VIEW_REGISTRY, snapshot.active_view_id)
    if profile is None:
        return None
    if profile.toolbar_family == "fm":
        return _plan_fm_toolbar(snapshot)
    if profile.toolbar_family == "lcc":
        return _plan_lcc_toolbar(snapshot, profile)
    return None


def plan_view_title(snapshot: WorkspaceStateSnapshot) -> str:
    """Volledig view-label boven detail_zone (slice 107-B, ADR-0021)."""
    entry = view_by_id(WORKSPACE_VIEW_REGISTRY, snapshot.active_view_id)
    return entry.label if entry is not None else ""


def plan_chrome_footer(snapshot: WorkspaceStateSnapshot) -> WorkspaceChromeFooterPlan:
    """Footer-plan onder detail_zone (slice 107, ADR-0020; context → view-titel 107-B)."""
    entry = view_by_id(WORKSPACE_VIEW_REGISTRY, snapshot.active_view_id)
    context_label = ""
    if not _on_output_side(snapshot) or entry is None:
        fm_toolbar = _plan_fm_toolbar(snapshot) if entry and entry.chrome and entry.chrome.toolbar_family == "fm" and entry.chrome.allows_new_fm else None
        return WorkspaceChromeFooterPlan(
            visible=fm_toolbar is not None and (
                fm_toolbar.new_fm_visible or fm_toolbar.batch_faalwijzen_visible
            ),
            context_label=context_label,
            middle_chrome_visible=False,
            lcc_measure_stack_visible=False,
            lcc_whatif_light_visible=False,
            fm_toolbar=fm_toolbar,
        )
    toolbar = plan_chrome_toolbar(snapshot)
    fm_toolbar = toolbar if isinstance(toolbar, FmToolbarPlan) else None
    lcc_toolbar = toolbar if isinstance(toolbar, LccToolbarVisibilityPlan) else None
    middle = fm_toolbar is not None and (
        fm_toolbar.metric_combo_visible
        or fm_toolbar.horizon_lifecycle_visible
        or fm_toolbar.effect_nb_filter_visible
    )
    if lcc_toolbar is not None:
        middle = middle or lcc_toolbar.metric_combo_visible or lcc_toolbar.effect_nb_filter_visible
    lcc_stack = (
        lcc_toolbar is not None
        and lcc_toolbar.pm_type_filters_visible
        and snapshot.metric == METRIC_KOSTEN
    )
    lcc_whatif = lcc_toolbar is not None and lcc_toolbar.filter_bar_visible
    visible = middle or lcc_stack or lcc_whatif or (
        fm_toolbar is not None
        and (
            fm_toolbar.fm_inspector_visible
            or fm_toolbar.column_crop_visible
            or fm_toolbar.fm_compare_nmf_rf_toggle_visible
        )
    )
    if snapshot.active_view_id == "output.kpi_overview":
        return WorkspaceChromeFooterPlan(
            visible=True,
            context_label=context_label,
            middle_chrome_visible=False,
            lcc_measure_stack_visible=False,
            lcc_whatif_light_visible=False,
        )
    return WorkspaceChromeFooterPlan(
        visible=visible,
        context_label=context_label,
        middle_chrome_visible=middle,
        lcc_measure_stack_visible=lcc_stack,
        lcc_whatif_light_visible=lcc_whatif,
        fm_toolbar=fm_toolbar,
        lcc_toolbar=lcc_toolbar,
    )


def _plan_compare_chrome(snapshot: WorkspaceStateSnapshot) -> CompareChromePlan:
    bijdragen_compare = snapshot.compare_mode and snapshot.modus == MODE_BIJDRAGEN
    lcc_compare = snapshot.compare_mode and snapshot.modus == MODE_LCC
    fm_compare = snapshot.compare_mode and snapshot.modus == MODE_FM_DETAIL
    return CompareChromePlan(
        compare_mode_checked=snapshot.compare_mode,
        bijdragen_single_visible=not bijdragen_compare,
        bijdragen_compare_visible=bijdragen_compare,
        bijdragen_chart_label_visible=not bijdragen_compare,
        lcc_single_visible=not lcc_compare,
        lcc_compare_visible=lcc_compare,
        lcc_empty_state_visible=not lcc_compare,
        fm_single_visible=not fm_compare,
        fm_compare_visible=fm_compare,
    )


def _collapse_glyph(collapsed: bool) -> str:
    return _COLLAPSE_COLLAPSED if collapsed else _COLLAPSE_EXPANDED


def _plan_collapse_panels(
    previous: WorkspaceStateSnapshot | None,
    snapshot: WorkspaceStateSnapshot,
) -> CollapsePanelsPlan:
    return CollapsePanelsPlan(
        kpi=None,
        lcc_whatif=_plan_lcc_whatif_collapse(snapshot),
        meekoppel=_plan_meekoppel_collapse(previous, snapshot),
    )


def _plan_lcc_whatif_collapse(
    snapshot: WorkspaceStateSnapshot,
) -> CollapsePanelPlan | None:
    if snapshot.modus != MODE_LCC:
        return None
    collapsed = snapshot.lcc_whatif_collapsed_in_lcc
    return CollapsePanelPlan(
        chrome_visible=True,
        content_visible=not collapsed,
        collapse_glyph=_collapse_glyph(collapsed),
        chrome_enabled=True,
    )


def _meekoppel_ensure_whatif(
    previous: WorkspaceStateSnapshot | None,
    current: WorkspaceStateSnapshot,
) -> bool:
    if current.modus != MODE_LCC or current.meekoppel_collapsed_in_lcc:
        return False
    if previous is None:
        return True
    if previous.modus != MODE_LCC:
        return True
    return previous.meekoppel_collapsed_in_lcc and not current.meekoppel_collapsed_in_lcc


def _plan_meekoppel_collapse(
    previous: WorkspaceStateSnapshot | None,
    snapshot: WorkspaceStateSnapshot,
) -> MeekoppelCollapsePlan | None:
    if snapshot.modus != MODE_LCC or not snapshot.planning_overlay.active:
        return None
    collapsed = snapshot.meekoppel_collapsed_in_lcc
    content_visible = not collapsed
    return MeekoppelCollapsePlan(
        chrome_visible=True,
        content_visible=content_visible,
        collapse_glyph=_collapse_glyph(collapsed),
        chrome_enabled=True,
        ensure_whatif_if_expanding=_meekoppel_ensure_whatif(previous, snapshot),
    )


def _inactive_fm_toolbar() -> FmToolbarPlan:
    return FmToolbarPlan(
        batch_faalwijzen_visible=False,
        new_fm_visible=False,
        column_crop_visible=False,
        fm_inspector_visible=False,
        clear_fm_inspector=True,
        effect_nb_filter_visible=False,
    )


def _plan_shared_toolbar(snapshot: WorkspaceStateSnapshot) -> SharedToolbarPlan:
    if not _on_output_side(snapshot):
        return SharedToolbarPlan(effect_nb_filter_in_shared_row=False)
    modus = snapshot.modus
    if modus == MODE_BIJDRAGEN:
        visible = snapshot.metric == METRIC_NIET_BESCHIKBAARHEID
    elif modus == MODE_LCC:
        visible = snapshot.metric == METRIC_NIET_BESCHIKBAARHEID
    elif modus == MODE_FM_DETAIL:
        visible = True
    else:
        visible = False
    return SharedToolbarPlan(effect_nb_filter_in_shared_row=visible)


class ResultsWorkspaceOrchestrator:
    """Adapter-orchestrator voor workspace snapshot → UI-sync- en render-plannen."""

    @staticmethod
    def plan_ui_sync(
        previous: WorkspaceStateSnapshot | None,
        current: WorkspaceStateSnapshot,
    ) -> WorkspaceUiSyncPlan:
        split_depth = workspace_detail_split_render_depth(previous, current)
        profile = chrome_for_view(WORKSPACE_VIEW_REGISTRY, current.active_view_id)
        fm_toolbar = _plan_fm_toolbar(current)
        lcc_toolbar = (
            _plan_lcc_toolbar(current, profile)
            if profile is not None
            and profile.toolbar_family == "lcc"
            and _on_output_side(current)
            else None
        )
        return WorkspaceUiSyncPlan(
            detail_page_modus=detail_stack_key_for_view(
                WORKSPACE_VIEW_REGISTRY, current.active_view_id
            ),
            modus_button=current.modus,
            view_title=plan_view_title(current),
            navigation=_plan_navigation(current),
            source_toggle=current.source,
            metric=current.metric,
            shared_toolbar=_plan_shared_toolbar(current),
            chrome_footer=plan_chrome_footer(current),
            top10_subbar_visible=_plan_top10_subbar_visible(current),
            status_strip_visible=_plan_status_strip_visible(current),
            bijdragen=_plan_bijdragen_toolbar(current),
            lcc_toolbar=lcc_toolbar,
            fm_toolbar=fm_toolbar,
            compare=plan_compare_chrome(current),
            collapse=_plan_collapse_panels(previous, current),
            refresh_kpi=should_refresh_kpi_for_render_depth(split_depth),
            pbs_tree_extended_selection=current.modus == MODE_LCC,
            scope_id=current.scope_id,
        )

    @staticmethod
    def plan_render(
        current: WorkspaceStateSnapshot,
        ctx: WorkspaceRenderContext,
        *,
        split_depth: RenderSplitDepth = "active_modus_only",
    ) -> RenderPlan:
        session = ctx.session
        if session is None:
            return RenderPlan(kind="empty")

        compare_view = current.compare_mode and current.modus in (
            MODE_BIJDRAGEN,
            MODE_LCC,
            MODE_FM_DETAIL,
        )
        has_compare_data = ctx.compare_slots.both_filled()
        has_live = live_run_available(session, ctx.run_mode)
        mc_fm_detail = (
            ctx.run_mode is RunMode.MONTE_CARLO and current.modus == MODE_FM_DETAIL
        )
        if not has_live and not (compare_view and has_compare_data):
            fm_analytical_without_run = (
                current.modus == MODE_FM_DETAIL
                and ctx.run_mode is RunMode.ANALYTICAL
            )
            if not mc_fm_detail and not fm_analytical_without_run:
                return RenderPlan(kind="empty")
        if compare_view and not has_compare_data:
            return RenderPlan(kind="compare_placeholder")

        depth = split_depth
        if depth == "all_splits":
            ctx.render_index.on_workspace_state_reset()

        required = required_detail_builders(current, depth)
        modus = current.modus

        if modus == MODE_FM_DETAIL and MODE_FM_DETAIL in required:
            layout = compute_compare_split_layout(
                compare_mode=current.compare_mode, modus=modus
            )
            if layout.compare_mode and has_compare_data:
                panels = build_fm_compare_panels(
                    session,
                    current,
                    slots=ctx.compare_slots,
                )
                bundle = build_faalwijze_bundle_for_compare(
                    panels,
                    metric=current.metric,
                )
                return RenderPlan(
                    kind="fm_compare",
                    compare_panels=panels,
                    faalwijze_bundle=bundle,
                )
            fm_view = build_fm_detail_view(session, current, run_mode=ctx.run_mode)
            return RenderPlan(
                kind="fm",
                fm=fm_view,
                faalwijze_bundle=build_faalwijze_bundle_for_fm_view(
                    fm_view,
                    metric=current.metric,
                ),
            )

        if modus == MODE_BIJDRAGEN and MODE_BIJDRAGEN in required:
            layout = compute_compare_split_layout(
                compare_mode=current.compare_mode, modus=modus
            )
            if layout.compare_mode:
                panels = build_bijdragen_compare_panels(
                    session,
                    current,
                    slots=ctx.compare_slots,
                    render_index=ctx.render_index,
                    project_total_presentation=ctx.project_total_presentation,
                )
                return RenderPlan(kind="bijdragen_compare", compare_panels=panels)
            return RenderPlan(
                kind="bijdragen",
                bijdragen=build_bijdragen_view(
                    session,
                    current,
                    render_index=ctx.render_index,
                    project_total_presentation=ctx.project_total_presentation,
                    run_mode=ctx.run_mode,
                ),
            )

        if modus == MODE_LCC and MODE_LCC in required:
            layout = compute_compare_split_layout(
                compare_mode=current.compare_mode, modus=modus
            )
            if layout.compare_mode:
                panels = build_lcc_compare_panels(
                    session,
                    current,
                    slots=ctx.compare_slots,
                    render_index=ctx.render_index,
                    prev_snapshot=ctx.prev_lcc_snapshot,
                )
                return RenderPlan(kind="lcc_compare", compare_panels=panels)
            return RenderPlan(
                kind="lcc",
                lcc=build_lcc_view(
                    session,
                    current,
                    render_index=ctx.render_index,
                    prev_snapshot=ctx.prev_lcc_snapshot,
                    run_mode=ctx.run_mode,
                ),
            )

        return RenderPlan(kind="empty")

    @staticmethod
    def plan_workspace_tick(
        previous: WorkspaceStateSnapshot | None,
        current: WorkspaceStateSnapshot,
        ctx: WorkspaceRenderContext,
    ) -> WorkspaceTickPlan:
        split_depth = workspace_detail_split_render_depth(previous, current)
        return WorkspaceTickPlan(
            ui_sync=ResultsWorkspaceOrchestrator.plan_ui_sync(previous, current),
            render=ResultsWorkspaceOrchestrator.plan_render(
                current, ctx, split_depth=split_depth
            ),
            split_depth=split_depth,
        )
