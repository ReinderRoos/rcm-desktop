# PRD: workspace_derived_refresh module (slice 92)

**Triage-label:** `done`

## Problem Statement

Na slices 85–91 berekent `top10_workspace_binding.refresh_nb_effect_filter_combo`
de NB-effectfilter presentatie inline: het haalt `session.run.fm_core_results` op
via `window._project_session()` en roept dan `build_nb_effect_filter_presentation`
aan. De *berekening* van presentatiewaarden staat daarmee in de view-bindings-laag,
niet in de adapterlaag. Dat maakt de berekening moeilijk te testen zonder widget,
en het patroon groeit naarmate er meer derived workspace state bijkomt.

## Solution

Een Qt-vrij adaptermodule `workspace_derived_refresh.py` met pure functies die
derived werkruimte-state berekenen uit expliciete inputs (project + run-resultaten).
De binding-functies in `top10_workspace_binding.py` delegeren de berekening aan
dit module; ze doen zelf alleen nog data-ophalen en widget-updates.

## User Stories

1. Als ontwikkelaar wil ik `plan_nb_filter_refresh(project, fm_results)` kunnen
   aanroepen zonder een Qt-widget, zodat de berekening unit-testbaar is.
2. Als ontwikkelaar wil ik dat `refresh_nb_effect_filter_combo` alleen nog
   data-ophalen en widget-update doet, zodat de logicalaag en de UI-laag gescheiden
   blijven.
3. Als analist wil ik dat na een run nog steeds effectklassen selecteerbaar zijn
   in het NB-filter (geen regressie van slice 91).

## Implementation Decisions

- `plan_nb_filter_refresh(project, fm_results)` is een pure functie in
  `rcm_desktop/adapter/workspace_derived_refresh.py`.
- `refresh_nb_effect_filter_combo` (binding) haalt `fm_results` zelf op uit de
  session en delegeert de berekening.
- Geen nieuw signaal, geen nieuw state-veld: alleen herindeling van verantwoordelijkheid.
- Geen motorwijziging; `CACHE_INPUTS_VERSION` hoeft niet omhoog.

## Testing Decisions

- `tests/test_slice92_workspace_derived_refresh.py`: pure tests op
  `plan_nb_filter_refresh` zonder Qt.
- Bestaande slice 91 NB-filter-tests (`test_slice91_nb_filter_run_refresh.py`)
  blijven groen.

## Out of Scope

- `loaded.core()`-aanroepen in `results_workspace_window.py` (aparte follow-up).
- Verdere derived-state producers (PBS-boom, KPI-tabel, rapport-eligibiliteit).
- Autosave of periodiek wegschrijven.
