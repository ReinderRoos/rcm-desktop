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



from rcm_desktop.adapter.fm_evident_filter import EvidentFilter

from rcm_desktop.adapter.lcc_type_filter import LCCTypeFilterSet

from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState



# Modi (product: Top 10, Tijdsplot, FM-detail)

MODE_BIJDRAGEN = "bijdragen"

MODE_LCC = "lcc"

MODE_FM_DETAIL = "fm_detail"



ALL_MODES: tuple[str, ...] = (

    MODE_BIJDRAGEN,

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



ContributionHorizon = Literal["lifecycle", "per_year"]

ContributionYearChoice = Literal["average"] | int

UnavailabilityDisplay = Literal["hours", "percent"]





@dataclass(frozen=True)

class ContributionPresentation:

    horizon: ContributionHorizon = "per_year"

    year_choice: ContributionYearChoice = "average"

    unavailability_display: UnavailabilityDisplay = "hours"





def normalize_modus(modus: str) -> str:

    """Map verwijderde modi naar actieve modi (slice 33)."""

    if modus == _LEGACY_MODE_PREVENTIEF_ONDERHOUD:

        return MODE_LCC

    if modus == _LEGACY_MODE_NIET_BESCHIKBAARHEID:

        return MODE_BIJDRAGEN

    return modus





def normalize_metric(metric: str) -> str:

    """Map verwijderde metrics naar veilige default (slice 33)."""

    if metric in (_LEGACY_METRIC_RISICO, _LEGACY_METRIC_DOWNTIME):

        return METRIC_NIET_BESCHIKBAARHEID

    return metric





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

    fm_evident_filter: EvidentFilter = "all"

    kpi_collapsed_in_lcc: bool = False

    meekoppel_collapsed_in_lcc: bool = False

    lcc_whatif_collapsed_in_lcc: bool = False

    compare_mode: bool = False





_DEFAULT_SNAPSHOT = WorkspaceStateSnapshot(

    modus=MODE_BIJDRAGEN,

    source=SOURCE_PBS,

    metric=METRIC_NIET_BESCHIKBAARHEID,

    top_n=10,

    scope_id=None,

    filter_text="",

    contribution_presentation=ContributionPresentation(),

    lcc_filters=LCCTypeFilterSet.all_on(),

    lcc_calendar_year=None,

    planning_overlay=PlanningOverlayState.inactive(),

    fm_evident_filter="all",

    kpi_collapsed_in_lcc=False,

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

        sticky_source = self._source_by_modus.get(modus, SOURCE_PBS)

        if modus == MODE_LCC:
            self._snapshot = replace(
                self._snapshot,
                modus=modus,
                source=sticky_source,
                kpi_collapsed_in_lcc=True,
                meekoppel_collapsed_in_lcc=True,
                lcc_whatif_collapsed_in_lcc=True,
            )
        else:
            self._snapshot = replace(self._snapshot, modus=modus, source=sticky_source)

        self._emit()



    def set_scope(self, scope_id: str | None) -> None:

        if scope_id == self._snapshot.scope_id:

            return

        self._snapshot = replace(self._snapshot, scope_id=scope_id)

        self._emit()



    def set_source(self, source: str) -> None:

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



    def set_fm_evident_filter(self, evident_filter: EvidentFilter) -> None:

        if evident_filter == self._snapshot.fm_evident_filter:

            return

        self._snapshot = replace(self._snapshot, fm_evident_filter=evident_filter)

        self._emit()



    def set_kpi_collapsed_in_lcc(self, collapsed: bool) -> None:

        if collapsed == self._snapshot.kpi_collapsed_in_lcc:

            return

        self._snapshot = replace(self._snapshot, kpi_collapsed_in_lcc=collapsed)

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



    def reset_for_new_project(self) -> None:

        """Reset alle keuzes naar de factory-defaults (modus/metric/scope/filter)."""

        self._source_by_modus = {modus: SOURCE_PBS for modus in ALL_MODES}

        if self._snapshot == _DEFAULT_SNAPSHOT:

            return

        self._snapshot = _DEFAULT_SNAPSHOT

        self._emit()


