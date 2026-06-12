# PRD — Slice 74: NB-effectfilter op FM-detail-niveau

**Status:** ready-for-agent
**Voorganger:** slice 71 (NB-effectfilter & metric 3-way), slice 73 (NB-scalar reconciliatie / bucketreeks-spine)
**Datum:** 2026-06-11
**Triage:** `ready-for-agent`

> Synthese van een `/grill-with-docs`-sessie (2026-06-11). Geen interview meer —
> dit document codificeert de besloten ontwerpkeuzes (wens 1 van 5).

---

## Problem Statement

De **NB-effectfilter** (`EffectNbFilterSet`) werkt vandaag alleen in de
**Bijdragen-modus (Top 10)** en de **Tijdsplot**. Wanneer de analist naar
**FM-detail** schakelt, toont de FM-tabel de **totale** verwachte downtime per
faalwijze, ongeacht de actieve NB-effectfilter. De analist die net een
effectklasse heeft geïsoleerd in Top 10 verliest die context zodra hij inzoomt op
de onderliggende faalwijzen — de getallen sluiten niet op elkaar aan.

## Solution

Vanuit de gebruiker gezien:

- De **NB-effectfilter geldt ook in FM-detail**. De downtime-kolom van de FM-tabel
  toont de **gefilterde** niet-beschikbaarheid per faalwijze (dezelfde
  bron-van-waarheid als Top 10/Tijdsplot: de NB-bucketreeks per FM, ADR-0010).
- De analist bedient **dezelfde** filter (geen aparte FM-detail-filter): de
  selectie die in Top 10 actief is, geldt direct in FM-detail en omgekeerd.
- Ook het **FM-inspectorpaneel** (lifecycle-totalen + jaarreeks) reflecteert de
  actieve filter, zodat de verificatie van één faalwijze consistent is met de
  tabel en met Top 10.

---

## Zoom-out: modulekaart

```
        Werkruimte-state (gedeeld)
   ResultsWorkspaceState.effect_nb_filter
                  │
   ┌──────────────┼───────────────────────────┐
   │              │                            │
 Top 10        Tijdsplot                  FM-detail (NIEUW)
 build_         tijdsplot_curve_          build_fm_detail_view
 contribution_  service                   (workspace_view_service)
 rows           (nb_filter=…)                  │
 (nb_filter=…)                          downtime-kolom + inspector
                                        via nb_scalar_for_fm (per FM)
```

Betrokken seams (domeintaal → bestand):

- **Effectimpact-deepmodule** — `rcm_core/effect_impact_service.py`
  (`nb_scalar_for_fm(project, fmr, nb_filter=…, presentation=…)`). Bestaand,
  Qt-vrij, **ongewijzigd publiek oppervlak**; de enige plek die de NB-bucketreeks
  reduceert.
- **FM-rij-fabriek** — `rcm_desktop/adapter/result_view_service.py`
  (`FMResultRow`, `build_rows`). De kolom `expected_total_downtime_hr` is vandaag
  de motor-waarde (totaal).
- **FM-detail-view-bouwer** — `rcm_desktop/adapter/workspace_view_service.py`
  (`build_fm_detail_view(session, snapshot)` → `FMDetailView.fm_rows`). Render-tijd
  seam waar de snapshot (incl. `effect_nb_filter`) beschikbaar is.
- **FM-inspector-seam** — `fm_verification_service` (lifecycle-totalen + jaarreeks
  per FM voor het inspectorpaneel).
- **Orchestrator** — `rcm_desktop/adapter/results_workspace_orchestrator.py`
  (`plan_ui_sync` / toolbar-zichtbaarheid): de NB-combo zichtbaar maken in
  FM-detail-modus.
- **Werkruimte-venster** — `rcm_desktop/views/results_workspace_window.py`
  (`nb_effect_filter_combo`, `_on_nb_effect_filter_changed`, FM-render-pad): de
  bestaande gedeelde combo ook in FM-detail tonen en re-render triggeren.

---

## Implementation Decisions

### Besloten ontwerpkeuzes (grilling)

- **Downtime-kolom: vervangen (`replace_downtime`).** De bestaande downtime-kolom
  van de FM-tabel toont de **gefilterde** NB; er komt **geen** extra kolom. Bij
  lege filter is de waarde identiek aan vandaag (totaal). Andere kolommen
  (faalmomenten, kosten) blijven ongewijzigd — de filter raakt alleen NB.
- **Eén gedeelde bediening (`surface_shared_combo`).** Dezelfde
  `NbEffectFilterCombo` + dezelfde `effect_nb_filter`-workspace-state worden in
  FM-detail getoond; geen tweede filterwidget en geen aparte state. Selectie is
  wederzijds zichtbaar tussen Top 10 en FM-detail.
- **Inspector volledig (`inspector_full`).** Het FM-inspectorpaneel
  (lifecycle-downtime + jaar-downtime-reeks) reflecteert de actieve filter via
  dezelfde `nb_scalar_for_fm` / NB-bucketreeks-spine.

### Seam-keuze

- De gefilterde downtime wordt **op render-tijd** berekend (de snapshot-tick), niet
  op motor-run-tijd, omdat de filter dynamisch wijzigt zonder run. Een **Qt-vrije
  helper** mapt `FMResultRow → FMResultRow` met de downtime-kolom vervangen door
  `nb_scalar_for_fm(project, fmr, nb_filter, presentation=lifecycle/uren)`.
- FM-detail-tabel rekent in **levensduur-uren** (`EffectPresentation(horizon=
  "lifecycle", unavailability_display="hours")`), consistent met de huidige
  kolom-semantiek.
- De combo-zichtbaarheid wordt via de **orchestrator** geregeld (FM-detail-modus
  toont de NB-combo), zodat het venster bind-only blijft.

### Architectuurprincipes (AGENTS.md)

- UI/kern-decoupling: views raken `rcm_core` alleen via de adapter.
- `rcm_core` blijft Qt-vrij; `nb_scalar_for_fm` wordt hergebruikt, niet
  gedupliceerd.
- Geen JSON-vormwijziging en geen motorwijziging → geen `CACHE_INPUTS_VERSION`-bump
  (presentatie-laag).

---

## User Stories

1. Als RCM-analist wil ik dat de downtime-kolom in FM-detail de actieve
   NB-effectfilter respecteert, zodat de FM-tabel aansluit op Top 10/Tijdsplot.
2. Als analist wil ik dezelfde filter bedienen in FM-detail als in Top 10, zodat ik
   niet twee filters hoef te onderhouden.
3. Als analist wil ik dat een lege filter in FM-detail exact de huidige
   (totale) downtime toont, zodat bestaande verificatie niet verandert.
4. Als analist wil ik dat de gefilterde downtime per faalwijze nooit groter is dan
   de totale downtime van die faalwijze, zodat deel ≤ geheel geldt.
5. Als analist wil ik dat het FM-inspectorpaneel (lifecycle-totaal + jaarreeks)
   dezelfde filter reflecteert, zodat het verifiëren van één FM consistent is.
6. Als analist wil ik dat het wisselen van filter direct de FM-tabel en inspector
   ververst zonder een nieuwe run, zodat het interactief blijft.
7. Als analist wil ik dat de NB-combo zichtbaar is in FM-detail-modus, zodat ik de
   filter daar kan aanpassen.
8. Als analist wil ik dat sorteren op de (gefilterde) downtime-kolom op de
   gefilterde waarde sorteert, zodat de ranking klopt met wat ik zie.

---

## Testing Decisions

Goede tests toetsen **extern gedrag** aan de seam, niet de implementatie.

- **Primaire seam (Qt-vrij): de FM-rij-filter-helper.**
  1. Lege filter → downtime per rij identiek aan `build_rows` (golden, ongewijzigd).
  2. Gevulde filter → downtime per rij = `nb_scalar_for_fm(project, fmr,
     nb_filter, lifecycle/uren)`, en per rij ≤ de totale downtime.
  3. Partitie: som van de losse posten (incl. restpost) = totaal per rij
     (erft uit ADR-0010-spine).
- **Adapter-seam: `build_fm_detail_view`** met een snapshot die `effect_nb_filter`
  draagt → `FMDetailView.fm_rows` met gefilterde downtime; evident-filter en scope
  blijven werken.
- **Inspector-seam: `fm_verification_service`** met `nb_filter` → lifecycle-totaal
  en jaarreeks reduceren uit de NB-bucketreeks; lege filter = huidig gedrag.
- **Orchestrator:** `plan_ui_sync` toont de NB-combo in FM-detail-modus.
- **pytest-qt (venster):** filter wijzigen in FM-detail re-rendert de tabel; combo
  zichtbaar; selectie gedeeld met Top 10.
- **Prior art:** `tests/test_slice71_nb_effectfilter.py`,
  `tests/test_desktop_result_view_service.py`,
  `tests/test_results_workspace_orchestrator.py`.

---

## Out of Scope

- Nieuwe kolommen in de FM-tabel (alleen de bestaande downtime-kolom wijzigt).
- Per-jaar/percent-presentatie in de FM-tabel (blijft levensduur-uren).
- Filter op kosten of faalmomenten in FM-detail (alleen NB).
- Wijzigingen aan de NB-bucketreeks-spine of motor (slice 73 / `engine.py`).

## Further Notes

- De ~60×- en deel≤geheel-invarianten zijn al geborgd in slice 73/ADR-0010; deze
  slice hergebruikt `nb_scalar_for_fm` en mag die invarianten niet breken.
- Volgorde: eerst de Qt-vrije helper + view-seam (issue 01), dan combo-zichtbaarheid
  (issue 02), dan inspector (issue 03).
