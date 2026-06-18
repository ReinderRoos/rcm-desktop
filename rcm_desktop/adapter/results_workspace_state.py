"""Qt-vrije orchestrator voor de resultatenwerkruimte (slice 23 fase B).



Houdt de actieve modus, PBS-scope, sub-toggle per modus, metric-keuze voor

`Bijdragen`, top-N en filtertekst van de PBS-boom bij. Past stickiness- en

reset-regels expliciet toe en stuurt een snapshot naar geregistreerde

luisteraars bij elke wijziging zodat de view declaratief kan herrenderen.



Bewust **geen Qt-imports**: pure Python observer-API (`subscribe`) zodat

unit-tests klein blijven en hetzelfde object in een Qt-view consumeerbaar is.

"""

from __future__ import annotations



from dataclasses import dataclass, replace

from typing import Callable, Literal



from rcm_core.effect_impact_service import EffectNbFilterSet

from rcm_desktop.adapter.lcc_type_filter import LCCTypeFilterSet

from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.workspace_navigation_policy import resolve_view_for_side_switch
from rcm_desktop.adapter.workspace_view_registry import (
    DEFAULT_VIEW_BY_SIDE,
    SIDE_INPUT,
    SIDE_OUTPUT,
    WORKSPACE_VIEW_REGISTRY,
    migrate_workspace_view_id,
    view_by_id,
)



# Modi (product: Top 10, Tijdsplot, FM-detail)

MODE_BIJDRAGEN = "bijdragen"

MODE_LCC = "lcc"

MODE_FM_DETAIL = "fm_detail"

MODE_KPI_OVERVIEW = "kpi_overview"

FM_VIEW_MODE_TABLE = "table"
FM_VIEW_MODE_DIAGRAM = "diagram"



ALL_MODES: tuple[str, ...] = (

    MODE_KPI_OVERVIEW,

    MODE_LCC,

    MODE_FM_DETAIL,

)



# Legacy modus-strings (migratie bij set_modus)

_LEGACY_MODE_NIET_BESCHIKBAARHEID = "niet_beschikbaarheid"

_LEGACY_MODE_PREVENTIEF_ONDERHOUD = "preventief_onderhoud"



# Bijdrage-metrics

METRIC_NIET_BESCHIKBAARHEID = "niet_beschikbaarheid"

METRIC_KOSTEN = "kosten"

METRIC_FAALMOMENTEN = "faalmomenten"



ALL_METRICS: tuple[str, ...] = (

    METRIC_FAALMOMENTEN,

    METRIC_NIET_BESCHIKBAARHEID,

    METRIC_KOSTEN,

)



_LEGACY_METRIC_DOWNTIME = "downtime"

_LEGACY_METRIC_RISICO = "risico"



# Bijdrage-bron (sub-toggle)

SOURCE_PBS = "pbs"

SOURCE_FAALWIJZE = "faalwijze"



ALL_SOURCES: tuple[str, ...] = (SOURCE_PBS, SOURCE_FAALWIJZE)

_LEGACY_SOURCE_EFFECTKLASSE = "effectklasse"
_LEGACY_METRIC_EFFECTIMPACT = "effectimpact"



ContributionHorizon = Literal["lifecycle", "per_year"]

ContributionYearChoice = Literal["average"] | int

UnavailabilityDisplay = Literal["hours", "percent"]





@dataclass(frozen=True)

class ContributionPresentation:

    horizon: ContributionHorizon = "per_year"

    year_choice: ContributionYearChoice = "average"

    unavailability_display: UnavailabilityDisplay = "hours"





def normalize_modus(modus: str) -> str:

    """Map verwijderde modi naar actieve modi (slice 33, slice 104)."""

    if modus == MODE_BIJDRAGEN:

        return MODE_FM_DETAIL

    if modus == _LEGACY_MODE_PREVENTIEF_ONDERHOUD:

        return MODE_LCC

    if modus == _LEGACY_MODE_NIET_BESCHIKBAARHEID:

        return MODE_FM_DETAIL

    return modus





def normalize_metric(metric: str) -> str:

    """Map verwijderde metrics naar veilige default (slice 33/71)."""

    if metric in (_LEGACY_METRIC_RISICO, _LEGACY_METRIC_DOWNTIME):

        return METRIC_NIET_BESCHIKBAARHEID

    if metric == _LEGACY_METRIC_EFFECTIMPACT:

        return METRIC_NIET_BESCHIKBAARHEID

    return metric





def normalize_source(source: str) -> str:

    """Map verwijderde bron Effectklasse naar PBS (slice 71)."""

    if source == _LEGACY_SOURCE_EFFECTKLASSE:

        return SOURCE_PBS

    return source





@dataclass(frozen=True)

class WorkspaceStateSnapshot:

    """Onveranderlijke momentopname van de werkruimte-state."""



    modus: str

    source: str

    metric: str

    top_n: int

    scope_id: str | None

    filter_text: str

    contribution_presentation: ContributionPresentation = ContributionPresentation()

    lcc_filters: LCCTypeFilterSet = LCCTypeFilterSet.all_on()

    lcc_calendar_year: int | None = None

    planning_overlay: PlanningOverlayState = PlanningOverlayState.inactive()

    meekoppel_collapsed_in_lcc: bool = False

    lcc_whatif_collapsed_in_lcc: bool = False

    compare_mode: bool = False

    fm_view_mode: str = FM_VIEW_MODE_TABLE

    fm_show_nmf_rf: bool = False

    fm_inspector_dismissed: bool = False

    fm_inspector_mode: bool = False

    fm_inspector_fm_id: str | None = None

    effect_nb_filter: EffectNbFilterSet = EffectNbFilterSet()

    workspace_side: str = SIDE_OUTPUT

    active_view_id: str = DEFAULT_VIEW_BY_SIDE[SIDE_OUTPUT]





_DEFAULT_SNAPSHOT = WorkspaceStateSnapshot(

    modus=MODE_FM_DETAIL,

    source=SOURCE_PBS,

    metric=METRIC_NIET_BESCHIKBAARHEID,

    top_n=10,

    scope_id=None,

    filter_text="",

    contribution_presentation=ContributionPresentation(),

    lcc_filters=LCCTypeFilterSet.all_on(),

    lcc_calendar_year=None,

    planning_overlay=PlanningOverlayState.inactive(),

    meekoppel_collapsed_in_lcc=False,

    lcc_whatif_collapsed_in_lcc=False,

)





class ResultsWorkspaceState:

    """Sticky werkruimte-state met observer-API."""



    def __init__(self) -> None:

        self._snapshot = _DEFAULT_SNAPSHOT

        self._listeners: list[Callable[[WorkspaceStateSnapshot], None]] = []

        self._source_by_modus: dict[str, str] = {
            modus: SOURCE_PBS for modus in ALL_MODES
        }

        self._sticky_view_by_side: dict[str, str] = dict(DEFAULT_VIEW_BY_SIDE)

        self._first_input_visit_pending = True



    def snapshot(self) -> WorkspaceStateSnapshot:

        return self._snapshot



    def subscribe(

        self, listener: Callable[[WorkspaceStateSnapshot], None]

    ) -> Callable[[], None]:

        """Registreer een luisteraar voor elke state-wissel. Retourneert een unsubscribe-handle."""

        self._listeners.append(listener)



        def _unsubscribe() -> None:

            try:

                self._listeners.remove(listener)

            except ValueError:

                pass



        return _unsubscribe



    def _emit(self) -> None:

        for listener in list(self._listeners):

            listener(self._snapshot)



    def set_modus(self, modus: str) -> None:

        modus = normalize_modus(modus)

        if modus not in ALL_MODES:

            raise ValueError(f"Onbekende modus: {modus!r}")

        if modus == self._snapshot.modus:

            return

        view_id = self._view_id_for_legacy_modus(modus)
        if view_id is not None:
            self.set_active_view(view_id)
            return

        self._apply_modus(modus)

    def set_active_view(self, view_id: str) -> None:
        view_id = migrate_workspace_view_id(view_id)
        entry = view_by_id(WORKSPACE_VIEW_REGISTRY, view_id)
        if entry is None:
            raise ValueError(f"Onbekende view: {view_id!r}")
        if not entry.enabled:
            raise ValueError(f"View is disabled: {view_id!r}")
        if (
            view_id == self._snapshot.active_view_id
            and entry.side == self._snapshot.workspace_side
            and entry.legacy_modus in (None, self._snapshot.modus)
        ):
            return
        if entry.legacy_modus is not None:
            self._apply_modus(
                entry.legacy_modus,
                workspace_side=entry.side,
                active_view_id=view_id,
            )
        else:
            self._snapshot = replace(
                self._snapshot,
                workspace_side=entry.side,
                active_view_id=view_id,
            )
            self._emit()
        self._sticky_view_by_side[entry.side] = view_id

    def set_workspace_side(self, side: str) -> None:
        if side not in DEFAULT_VIEW_BY_SIDE:
            raise ValueError(f"Onbekende werkruimte-zijde: {side!r}")
        if side == self._snapshot.workspace_side:
            return
        sticky_view_id, self._first_input_visit_pending = resolve_view_for_side_switch(
            side=side,
            sticky_view_by_side=self._sticky_view_by_side,
            first_input_visit_pending=self._first_input_visit_pending,
        )
        entry = view_by_id(WORKSPACE_VIEW_REGISTRY, sticky_view_id)
        if entry is None:
            sticky_view_id = DEFAULT_VIEW_BY_SIDE[side]
            entry = view_by_id(WORKSPACE_VIEW_REGISTRY, sticky_view_id)
        if entry is not None and entry.enabled:
            self.set_active_view(sticky_view_id)
            return
        self._snapshot = replace(
            self._snapshot,
            workspace_side=side,
            active_view_id=sticky_view_id,
        )
        self._emit()

    def sticky_views_by_side(self) -> dict[str, str]:
        return dict(self._sticky_view_by_side)

    def restore_navigation(self, side: str, sticky_by_side: dict[str, str]) -> None:
        if side not in DEFAULT_VIEW_BY_SIDE:
            side = SIDE_OUTPUT
        for sticky_side, view_id in sticky_by_side.items():
            if sticky_side not in DEFAULT_VIEW_BY_SIDE:
                continue
            view_id = migrate_workspace_view_id(view_id)
            entry = view_by_id(WORKSPACE_VIEW_REGISTRY, view_id)
            if entry is None or entry.side != sticky_side:
                view_id = DEFAULT_VIEW_BY_SIDE[sticky_side]
            self._sticky_view_by_side[sticky_side] = view_id
        if side == self._snapshot.workspace_side:
            sticky_view_id = self._sticky_view_by_side[side]
            entry = view_by_id(WORKSPACE_VIEW_REGISTRY, sticky_view_id)
            if entry is not None and entry.enabled:
                self.set_active_view(sticky_view_id)
            return
        self.set_workspace_side(side)

    def _view_id_for_legacy_modus(self, modus: str) -> str | None:
        side = self._snapshot.workspace_side
        sticky = self._sticky_view_by_side.get(side)
        if sticky is not None:
            sticky_entry = view_by_id(WORKSPACE_VIEW_REGISTRY, sticky)
            if (
                sticky_entry is not None
                and sticky_entry.enabled
                and sticky_entry.legacy_modus == modus
            ):
                return sticky
        for entry in WORKSPACE_VIEW_REGISTRY:
            if entry.legacy_modus == modus and entry.enabled:
                return entry.view_id
        return None

    def _apply_modus(
        self,
        modus: str,
        *,
        workspace_side: str | None = None,
        active_view_id: str | None = None,
    ) -> None:
        sticky_source = self._source_by_modus.get(modus, SOURCE_PBS)
        side = workspace_side if workspace_side is not None else self._snapshot.workspace_side
        view_id = active_view_id if active_view_id is not None else self._snapshot.active_view_id
        if modus == MODE_LCC:
            self._snapshot = replace(
                self._snapshot,
                modus=modus,
                source=sticky_source,
                workspace_side=side,
                active_view_id=view_id,
                meekoppel_collapsed_in_lcc=True,
                lcc_whatif_collapsed_in_lcc=True,
            )
        else:
            self._snapshot = replace(
                self._snapshot,
                modus=modus,
                source=sticky_source,
                workspace_side=side,
                active_view_id=view_id,
            )
        self._emit()



    def set_scope(self, scope_id: str | None) -> None:

        if scope_id == self._snapshot.scope_id:

            return

        self._snapshot = replace(self._snapshot, scope_id=scope_id)

        self._emit()



    def set_source(self, source: str) -> None:

        source = normalize_source(source)

        if source not in ALL_SOURCES:

            raise ValueError(f"Onbekende bron: {source!r}")

        self._source_by_modus[self._snapshot.modus] = source

        if source == self._snapshot.source:

            return

        self._snapshot = replace(self._snapshot, source=source)

        self._emit()



    def set_metric(self, metric: str) -> None:

        """Metric-keuze geldt binnen Top 10; sticky over modus-wissels."""

        metric = normalize_metric(metric)

        if metric not in ALL_METRICS:

            raise ValueError(f"Onbekende metric: {metric!r}")

        if metric == self._snapshot.metric:

            return

        self._snapshot = replace(self._snapshot, metric=metric)

        self._emit()



    def set_contribution_presentation(

        self, presentation: ContributionPresentation

    ) -> None:

        if presentation == self._snapshot.contribution_presentation:

            return

        self._snapshot = replace(

            self._snapshot, contribution_presentation=presentation

        )

        self._emit()



    def set_contribution_horizon(self, horizon: ContributionHorizon) -> None:

        pres = self._snapshot.contribution_presentation

        if horizon == pres.horizon:

            return

        self.set_contribution_presentation(replace(pres, horizon=horizon))



    def set_contribution_year_choice(self, year_choice: ContributionYearChoice) -> None:

        pres = self._snapshot.contribution_presentation

        if year_choice == pres.year_choice:

            return

        self.set_contribution_presentation(replace(pres, year_choice=year_choice))



    def set_unavailability_display(self, display: UnavailabilityDisplay) -> None:

        pres = self._snapshot.contribution_presentation

        if display == pres.unavailability_display:

            return

        self.set_contribution_presentation(

            replace(pres, unavailability_display=display)

        )



    def set_filter_text(self, text: str) -> None:

        if text == self._snapshot.filter_text:

            return

        self._snapshot = replace(self._snapshot, filter_text=text)

        self._emit()



    def set_effect_nb_filter(self, nb_filter: EffectNbFilterSet) -> None:

        if nb_filter == self._snapshot.effect_nb_filter:

            return

        self._snapshot = replace(self._snapshot, effect_nb_filter=nb_filter)

        self._emit()



    def set_lcc_filters(self, filters: LCCTypeFilterSet) -> None:

        if filters == self._snapshot.lcc_filters:

            return

        self._snapshot = replace(self._snapshot, lcc_filters=filters)

        self._emit()



    def set_lcc_calendar_year(self, calendar_year: int | None) -> None:

        if calendar_year == self._snapshot.lcc_calendar_year:

            return

        self._snapshot = replace(self._snapshot, lcc_calendar_year=calendar_year)

        self._emit()



    def set_planning_overlay(self, overlay: PlanningOverlayState) -> None:

        if overlay == self._snapshot.planning_overlay:

            return

        self._snapshot = replace(self._snapshot, planning_overlay=overlay)

        self._emit()



    def set_meekoppel_collapsed_in_lcc(self, collapsed: bool) -> None:

        if collapsed == self._snapshot.meekoppel_collapsed_in_lcc:

            return

        self._snapshot = replace(self._snapshot, meekoppel_collapsed_in_lcc=collapsed)

        self._emit()



    def set_lcc_whatif_collapsed_in_lcc(self, collapsed: bool) -> None:

        if collapsed == self._snapshot.lcc_whatif_collapsed_in_lcc:

            return

        self._snapshot = replace(self._snapshot, lcc_whatif_collapsed_in_lcc=collapsed)

        self._emit()



    def set_compare_mode(self, enabled: bool) -> None:

        if enabled == self._snapshot.compare_mode:

            return

        self._snapshot = replace(self._snapshot, compare_mode=enabled)

        self._emit()

    def set_fm_view_mode(self, mode: str) -> None:
        if mode not in (FM_VIEW_MODE_TABLE, FM_VIEW_MODE_DIAGRAM):
            raise ValueError(f"Onbekende FM-view-modus: {mode!r}")
        if mode == self._snapshot.fm_view_mode:
            return
        if mode == FM_VIEW_MODE_DIAGRAM and self._snapshot.fm_inspector_mode:
            self._snapshot = replace(
                self._snapshot,
                fm_view_mode=mode,
                fm_inspector_mode=False,
                fm_inspector_fm_id=None,
                fm_inspector_dismissed=True,
            )
            self._emit()
            return
        self._snapshot = replace(self._snapshot, fm_view_mode=mode)
        self._emit()

    def set_fm_show_nmf_rf(self, visible: bool) -> None:
        if visible == self._snapshot.fm_show_nmf_rf:
            return
        self._snapshot = replace(self._snapshot, fm_show_nmf_rf=visible)
        self._emit()

    def open_fm_inspector_mode(self, fm_id: str) -> None:
        fm_key = str(fm_id)
        if (
            self._snapshot.fm_inspector_mode
            and self._snapshot.fm_inspector_fm_id == fm_key
        ):
            return
        self._snapshot = replace(
            self._snapshot,
            fm_inspector_mode=True,
            fm_inspector_fm_id=fm_key,
            fm_inspector_dismissed=False,
            fm_view_mode=FM_VIEW_MODE_TABLE,
        )
        self._emit()

    def close_fm_inspector_mode(self) -> None:
        if not self._snapshot.fm_inspector_mode and self._snapshot.fm_inspector_fm_id is None:
            if self._snapshot.fm_inspector_dismissed:
                return
        self._snapshot = replace(
            self._snapshot,
            fm_inspector_mode=False,
            fm_inspector_fm_id=None,
            fm_inspector_dismissed=True,
        )
        self._emit()

    def step_fm_inspector(self, delta: int, ordered_fm_ids: tuple[str, ...]) -> None:
        if not self._snapshot.fm_inspector_mode or not ordered_fm_ids:
            return
        current = self._snapshot.fm_inspector_fm_id
        if current is None or current not in ordered_fm_ids:
            return
        idx = ordered_fm_ids.index(current) + delta
        if idx < 0 or idx >= len(ordered_fm_ids):
            return
        self.open_fm_inspector_mode(ordered_fm_ids[idx])

    def set_fm_inspector_dismissed(self, dismissed: bool) -> None:
        if dismissed:
            self.close_fm_inspector_mode()
            return
        if dismissed == self._snapshot.fm_inspector_dismissed:
            return
        self._snapshot = replace(self._snapshot, fm_inspector_dismissed=dismissed)
        self._emit()

    def reset_for_new_project(self) -> None:

        """Reset alle keuzes naar de factory-defaults (modus/metric/scope/filter)."""

        self._source_by_modus = {
            modus: SOURCE_PBS for modus in ALL_MODES
        }

        self._sticky_view_by_side[SIDE_INPUT] = DEFAULT_VIEW_BY_SIDE[SIDE_INPUT]
        self._first_input_visit_pending = True

        if self._snapshot == _DEFAULT_SNAPSHOT:

            return

        self._snapshot = _DEFAULT_SNAPSHOT

        self._emit()


