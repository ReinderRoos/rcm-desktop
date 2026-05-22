# Slice 38 — LCC snel zichtbaar (lazy jaardetail + lichte plot-build)

**Triage:** ready-for-agent  
**Type:** AFK (adapter/UI; geen motorwijziging)  
**Parent:** slice 37 follow-up (LCC plot traag na snelle run); slice 36 LTAP-cache + render-index  
**Versie:** 1.0  
**Datum:** 2026-05-21  
**Referentie-fixture:** `tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json`

## Problem Statement

Na slice 36 (LTAP-memoization, render-scoping) en slice 37 (contribution-only post-run, lazy LCC via `WorkspaceRenderIndex`) is de **analyse-run en moduswissel naar Bijdragen/FM-detail** weer acceptabel snel op het referentie-demo-project (AWZI Haarlem Waarderpolder).

Het **eerste tonen van de LCC-modus** blijft echter merkbaar traag: de gebruiker wacht op de volledige planningcurve-build voordat staafgrafiek en jaartabel verschijnen. Oorzaken in de huidige keten:

1. **Curve-cache key bevat `lcc_calendar_year`** — elke jaarklik invalideert de curve en triggert opnieuw `build_lcc_planning_curve_reconciled`, terwijl jaardetail de curve al hergebruikt kan.
2. **Dubbele reconciliatie** — `build_lcc_planning_curve` schaalt PM al; `build_lcc_planning_curve_reconciled` roept `reconcile_planning_curve_pm_total` opnieuw aan.
3. **Dubbele LTAP-build bij inactieve overlay** — `_ltap_preventief_series` wordt twee keer aangeroepen (baseline + overlay) ook wanneer what-if uit staat en overlay geen PM beïnvloedt.
4. **Plot-build = volledige LTAP-view** — voor de staafgrafiek zijn per jaar alleen **PM-totalen** nodig; `LTAPTaskDetail`-rijen worden pas bij **jaarklik** (jaardetail) gevraagd maar worden nu al mee opgebouwd.

De analist wil **snel het macro-beeld** (LCC over alle jaren) zien en pas daarna — optioneel — **drill-down per jaar** met what-if-manipulatie. Jaardetail mag **niet** verdwijnen; het mag **lazy** zijn (plot eerst, detail na klik).

## Solution

Versnel de LCC-modus in vier complementaire lagen, zonder functioneel contract van slice 28/29/30 (filters, jaardetail, what-if shift/passief) te breken:

1. **Gescheiden cache-keys:** curve-key op `(scope, filters, overlay-state)`; jaardetail apart op `(curve + calendar_year)`. Jaarklik herbouwt **geen** curve.
2. **Curve-builder opschonen:** één reconciliatie-pad; overlay-inactief fast path (één LTAP-aanroep waar veilig).
3. **LTAP light path voor plot:** nieuwe adapter-API levert per-jaar PM-totalen (+ filter-unie) zonder `LTAPTaskDetail`; volledige LTAP-view blijft voor jaardetail en what-if-toolbar.
4. **Lazy jaardetail in UI:** LCC-render toont grafiek + jaartabel zodra curve klaar is; jaardetailtabel vult pas na jaarselectie (bestaande toolbar/passief/shift ongewijzigd).
5. **Optionele achtergrond-warmup:** na geslaagde run LCC-curve (default filters, geen overlay) in worker-thread pre-builden in `WorkspaceRenderIndex`, analoog aan `PresentationRebuildRunner`.

Observability: uitbreid `tests/perf/` met slice-38 call-count contracts; handmatige Haarlem-validatie in handoff.

Architectuurregels blijven: **UI → adapter → kern**; geen `rcm_core` in views (typing-only).

## User Stories

### Snelheid — plot zichtbaar

1. Als **analist** wil ik dat de **LCC-staafgrafiek en jaartabel** binnen enkele seconden verschijnen na moduswissel naar LCC, zodat verkenning niet blokkeert op LTAP-detail.
2. Als **analist** wil ik dat **jaarklik** geen merkbare pauze geeft door herbouw van de hele curve, zodat ik snel tussen jaren kan klikken.
3. Als **analist** wil ik na **Start/Herbereken analyse** dat LCC **vaak al warm** is wanneer ik naar Tijdsplot ga, zodat achtergrond-warmup de wacht op modusbezoek verkort.
4. Als **analist** wil ik bij **PBS-scope-wissel** correcte scoped LCC-curve zien zonder onnodige detail-rebuilds, zodat sidebar-navigatie responsief blijft.
5. Als **analist** wil ik bij **type-filter toggle** (CM/REV/IN/…) alleen de curve herbouwd zien wanneer filters de plot beïnvloeden, niet bij elke jaarselectie.

### Jaardetail blijft — lazy, niet weg

6. Als **onderhoudsingenieur** wil ik na **klik op een kalenderjaar** nog steeds de **PM-takenlijst** zien (label, type, faalwijze, uitvoeringen, kosten, downtime), zodat drill-down behouden blijft.
7. Als **onderhoudsingenieur** wil ik met **What-if planning aan + jaarselectie** de **detail-toolbar** (verschuif, REV-selectie, passief-kolom) gebruiken, zodat slice 29-manipulatie in de werkruimte blijft werken.
8. Als **analist** wil ik boven jaardetail de **jaarsamenvatting** (baseline / what-if delta) zien, zodat ik per jaar PM-impact begrijp zonder te rekenen.
9. Als **analist** wil ik bij **alleen CM-filter** bij jaarklik geen PM-rijen maar wel correctief-samenvatting, zodat cm-only gedrag voorspelbaar blijft.
10. Als **analist** wil ik **Toon alle jaren** jaardetail leegmaken zonder curve-rebuild, zodat terug naar macro-overzicht snel is.

### What-if en overlay

11. Als **analist** wil ik **What-if toggle** zonder jaarselectie bulk-acties kunnen doen (alle REV passief, CM-beleid), zodat macro-scenario's snel blijven.
12. Als **analist** wil ik dat **overlay-wijziging** (shift/passief) de **curve** herbouwt maar **niet** per ongeluk jaardetail-cache verwart, zodat totalen en detail consistent blijven.
13. Als **analist** wil ik na **herberekenen met what-if** passieve taken nog zichtbaar houden in jaardetail volgens slice 30-contract, zodat verificatie mogelijk blijft.

### Correctheid en reconciliatie

14. Als **analist** wil ik dat **som preventief over jaren** nog steeds reconcileert met scoped motor-PM-totaal, zodat filters geen stille drift introduceren.
15. Als **analist** wil ik dat **grafiek, jaartabel en jaardetail** dezelfde LTAP-bron delen (light path vs full view), zodat er geen twee waarheden ontstaan.
16. Als **maintainer** wil ik dat **inactive overlay** geen dubbele LTAP-build triggert, zodat de common case (read-only LCC) snel is.

### Cache en sessie

17. Als **maintainer** wil ik **WorkspaceRenderIndex** curve en detail logisch gescheiden cachen, zodat invalidatie gericht blijft.
18. Als **maintainer** wil ik **LTAPViewCache** hergebruiken tussen light path (totalen) en jaardetail (full view) waar overlay/scope gelijk is, zodat jaarklik geen cold LTAP start als plot net gebouwd is.
19. Als **analist** wil ik bij **project wisselen** geen stale LCC uit vorig project, zodat bestaande `on_project_changed`-invalidatie intact blijft.

### UX tijdens laden

20. Als **analist** wil ik bij trage jaardetail-build een **duidelijke loading-hint** (of lege tabel + statusregel), zodat ik weet dat detail nog opgebouwd wordt — geen bevroren UI zonder feedback.
21. Als **analist** wil ik **geen regressie** in FM-detail, Bijdragen of run-flow, zodat slice 36/37-winst behouden blijft.

### Observability

22. Als **maintainer** wil ik **pytest call-count contracts** dat jaarklik **0 curve-rebuilds** doet, zodat regressie CI vangt.
23. Als **maintainer** wil ik contracten dat **inactive overlay** maximaal **1 LTAP-build** per curve-build vergt (was 2), zodat optimalisatie meetbaar is.
24. Als **maintainer** wil ik **handmatige Haarlem-checklist** in handoff (LCC open, jaarklik, what-if shift), zodat UX na merge gevalideerd wordt.

### Edge cases

25. Als **analist** wil ik bij **ongeldig kalenderjaar** (buiten horizon) geen crash maar lege detail-state, zodat sticky jaarselectie veilig is.
26. Als **analist** wil ik bij **leeg jaar** (geen taken voor filters) expliciete empty-state, zodat ik filters vs data kan onderscheiden.
27. Als **analist** wil ik **SVO/WET niet verschuifbaar** houden in jaardetail volgens bestaande LTAP-regels, zodat governance ongewijzigd blijft.

## Implementation Decisions

### Diepe modules (Qt-vrij, test-first)

- **LCC render cache key builder (diep):** pure functie(s) die uit `WorkspaceStateSnapshot` twee keys afleiden:
  - `curve_key`: scope, type-filters, overlay `(active, change_count)` — **zonder** `lcc_calendar_year`
  - `detail_key`: curve identity + `calendar_year` (of detail-only invalidation via state)
  - Vervangt impliciete monolithische `_render_cache_modus_key` voor LCC-curve; jaardetail gebruikt curve uit index + year uit snapshot.
- **LCC planning curve builder (refactor):** consolideer reconciliatie:
  - `build_lcc_planning_curve` levert display + baseline; **één** `reconcile_planning_curve_pm_total` aan het eind van `build_lcc_planning_curve_reconciled` (niet dubbel intern).
  - **Overlay-inactief fast path:** wanneer `not overlay.active` of overlay raakt PM-presentatie niet (`_overlay_affects_preventief_presentatie`), één `_ltap_preventief_series`-aanroep; display = gefilterde baseline.
- **LTAP PM cost series (nieuw, diep):** smalle API naast `build_ltap_view`:
  - Input: zelfde kwargs als LTAP-cache (overlay anchors, disabled set, PBS-scope).
  - Output: per horizon-index `(raw_pm_eur, filtered_pm_eur)` tuples — **geen** `LTAPTaskDetail`.
  - Implementatie mag intern dezelfde scheduling-loop als LTAP hergebruiken, maar slaat detail-objecten over; of deelt partial met `build_ltap_view` via geëxtraheerde kern.
  - **Jaardetail** blijft `get_ltap_view` → `years[h].details` voor volledige rijen.
- **Lazy LCC render orchestration (adapter):** uitbreiding `presentation_lazy_service` of sibling:
  - `warm_lcc_curve(...)` — light path + render index
  - `build_lcc_year_detail_lazy(...)` — alleen bij `calendar_year is not None`; hergebruikt gecachte curve + LTAP full view
- **LCC warmup runner (Qt, optioneel issue):** analoog `PresentationRebuildRunner`:
  - Na run success: background thread bouwt default LCC curve `(scope=None, filters=all, overlay=inactive)` in session-scoped render index
  - Geen UI-bindings in worker; alleen adapter + render index injectie
  - Cancel/ignore bij project-wissel of nieuwe run start

### UI-wijzigingen (minimaal)

- **`_render_lcc_for_run`:** split in curve-render (sync, snel) + `_render_lcc_year_detail` (alleen als `lcc_calendar_year` gezet).
- **State change routing:** jaarselectie triggert **detail-only** rerender (geen `on_workspace_state_reset` voor curve-cache).
- **Loading feedback:** optioneel label "Jaardetail laden…" tijdens detail-build op main thread (v1); achtergrond-detail alleen als main-thread freeze > drempel — anders out of scope.

### Contracten

- `LCCPlanningCurve`, `LCCYearDetailView`, `PlanningOverlayState` — **geen** shape-wijziging.
- `WorkspaceRenderIndex.get_or_build` blijft; mogelijk **tweede index-slot** of geneste key-structuur voor detail (beslissing in implementatie: één index met prefixed modus-keys is voldoende).
- LTAP-cache key ongewijzigd; light path en full view delen cache waar overlay/scope identiek.

### Prototype-beslissing (cache key split)

```
curve_key   = f"lcc_curve|{scope}|{filters}|{overlay.active}|{overlay.change_count()}"
detail_tick = calendar_year  # geen curve rebuild; detail leest curve uit index
```

## Testing Decisions

- **Goede tests** meten **extern gedrag** en **call-count contracten**, geen wall-clock in CI (flaky).
- **Unit tests (geen Qt):**
  - Cache key builder: jaarselectie wijzigt curve_key niet
  - Curve builder: inactive overlay → spy op LTAP max 1 build
  - Reconciled builder: spy op `reconcile_planning_curve_pm_total` max 1 per curve build
  - LTAP PM cost series: totalen matchen full LTAP-view op fixture `one_fm_planning`
- **Adapter tests:**
  - Jaardetail met injected curve: geen curve-rebuild (bestaand slice 36 test blijft groen)
  - Lazy detail: year=None → geen `build_lcc_year_detail` LTAP full path (indien gescheiden)
- **Perf-regressie:** `tests/perf/test_slice38_regression.py` + `baseline.json` slice38_contracts:
  - `lcc_year_click_curve_rebuilds_max: 0`
  - `lcc_inactive_overlay_ltap_builds_max: 1` (per curve build)
  - `lcc_reconcile_calls_per_curve_max: 1`
  - Optioneel: `post_run_lcc_warmup_builds_max: 1` wanneer warmup issue meelevert
- **Prior art:** `test_slice36_regression.py`, `test_slice37_regression.py`, `test_desktop_lcc_year_detail_curve.py`, `test_desktop_ltap_view_cache.py`
- **Handmatig:** Haarlem demo — LCC modus, jaarklik 3×, what-if + shift één taak, filter toggle

## Out of Scope

- **Verwijderen of beperken van jaardetail** — drill-down en what-if per taak blijven verplicht.
- **ValidateWindow-LTAP** wijzigingen of deprecatie.
- **Motor / `CACHE_INPUTS_VERSION`** — geen analytische wijziging.
- **Volledige async LCC-render op UI-thread** (plot in worker + Qt signal) — tenzij warmup onvoldoende; progressive CM-first render is **nice-to-have**, niet v1.
- **Viewport-virtualisatie** LCC-tabellen.
- **Monte Carlo**, export, nieuwe planning-overlay business rules.
- **Wijziging type-filter semantiek** (CM vs PM-types).

## Further Notes

- **Aanbevolen issue-volgorde (tracer-bullet):**

| # | Titel | Fase |
|---|--------|------|
| 01 | LCC curve-cache key zonder calendar_year | A |
| 02 | Curve-builder dedup (reconcile + inactive overlay) | A |
| 03 | LTAP PM cost series (light path) | B |
| 04 | Lazy jaardetail render-split in werkruimte | B |
| 05 | LCC achtergrond-warmup na run | C |
| 06 | Perf-contract slice 38 + handoff | D |

- **Verwachte winst (indicatief, Haarlem):** jaarklik ~0 curve-rebuild; inactive overlay ~50% minder LTAP bij curve; light path ~30–60% sneller plot (modelafhankelijk); warmup maakt **tweede** LCC-bezoek often cache-hit.
- **Relatie slice 37:** post-run bouwt nog geen LCC; slice 38 optimaliseert **eerste LCC-modusbezoek** en **jaarnavigatie**.
- **Gebruikerscommunicatie:** "Lazy jaardetail" = plot eerst, detail na klik — **niet** minder functionaliteit.
- **Handoff:** na implementatie `KANBAN_HANDOFF.md` in deze slice-map; update `tests/perf/README.md` met slice38-contracts.
