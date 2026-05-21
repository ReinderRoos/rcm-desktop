# Slice 36 — Werkruimte run- en presentatie-performance

**Triage:** ready-for-agent  
**Type:** AFK (issue 05 raakt motor; overige adapter/UI)  
**Parent:** performance-onderzoek sessie 2026-05-21 (AWZI Haarlem Waarderpolder); follow-up op slice 25 (onvolledig) en slice 27 (horizon_profile niet gekoppeld)  
**Versie:** 1.0  
**Datum:** 2026-05-21  
**Referentie-fixture:** `tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json` (~100 FM, ~100 PM, lifecycle 60j)  
**Performance-baseline:** `tests/perf/baseline.json` (pre-slice-24 handmatige meetwaarden)

## Problem Statement

Analisten ervaren het **zelfde project** (AWZI Haarlem Waarderpolder demo) als **merkbaar trager** dan voorheen, zowel bij **Start/Herbereken analyse** als bij **navigeren in de resultatenwerkruimte** (moduswissel, PBS-scope, LCC-filters, jaarselectie).

Typische klachten:

- Een analyse-run duurt **minuten** terwijl het model inhoudelijk niet is gewijzigd.
- Na de run voelt **Tijdsplot (LCC)** en soms **Top 10 / Bijdragen** traag bij elke klik.
- Er is **verwarring over cache**: gebruikers vrezen dat een ander project (bijv. Gaarkeuken-fixture) de performance beïnvloedt.

Onderzoek toont aan:

- **Geen cross-project cache-contaminatie** — FM- en presentatie-cache hangen aan `<project>.rcm.cache.json` + `global_digest`.
- De traagheid komt vooral door **architectuur keuzes sinds slices 21–28**: resultatenwerkruimte als default entry, **presentatie-fase na elke run**, **zware LCC/LTAP-ketens**, en **RunRunner die incrementele cache en parallelisme omzeilt**.
- Slice 25 is gemarkeerd **done**, maar **`split_render_depth` wordt berekend en vervolgens genegeerd** — moduswissels triggeren onnodig zwaar werk.
- De motor vult **`horizon_profile` niet** op `FMResult`; presentatie valt terug op **legacy per-FM bucket-berekening** bij elke LCC/NB-build.

Referentie-baseline voor Haarlem-fixture: volledige run ~**120 s**, herhaalde run met geldige cache ~**5 s** — het huidige gedrag zit structureel in de cold-start-zone.

## Solution

Herstel **voorspelbare performance** op het referentie-demo-project door vier complementaire lagen te verbeteren, **zonder** functioneel contract van modi (Top 10, LCC, FM-detail, inspector) te breken:

1. **Run-beslissing:** gebruik **incrementele FM-cache** wanneer digest en FM-hashes vertrouwd zijn; reserveer **volledige herberekening** voor expliciete “Herbereken” of cache-mismatch. Schakel **parallel motor** in waar veilig.
2. **Presentatie-memoization:** **LTAP-view** en **LCC-planningcurve** niet opnieuw bouwen voor dezelfde `(project, overlay, scope, filters)`-combinatie binnen één sessie.
3. **Modus-gescopeerde rerender:** maak slice-25 **`active_modus_only`** werkelijk — geen zware LCC-build wanneer de gebruiker in FM-detail zit en alleen metric/filter wisselt waar dat kan.
4. **Motor-profilen:** vul **`horizon_profile`** bij run zodat LCC/NB/inspector **geen legacy fallback** meer per interactie uitvoeren.

Observability: behoud/uitbreid **`tests/perf/`** met meetbare drempels; documenteer kort **motor vs presentatie vs UI-rerender** in slice-handoff.

Architectuurregels blijven: **UI → adapter → kern**; geen `rcm_core` in views (typing-only).

## User Stories

### Run en cache

1. Als **analist** wil ik dat **Start analyse** op een ongewijzigd project **de FM-cache hergebruikt**, zodat ik niet opnieuw minuten wacht.
2. Als **analist** wil ik **Herbereken analyse** expliciet een **volledige motor-run** doen, zodat ik bewust cache overschrijf wanneer nodig.
3. Als **analist** wil ik dat na **valideren/laden** een bestaande `.rcm.cache.json` **direct** resultaten toont zonder motor, zodat cold start alleen bij eerste run gebeurt.
4. Als **maintainer** wil ik dat **parallel motor** standaard aan staat in de werkruimte-runner, zodat volledige runs op multi-core profiteren.
5. Als **analist** wil ik **geen verkeerde cache van een ander project**, zodat ik vertrouwen houd in “snel na tweede keer” — digest per projectpad moet dat garanderen (bestaand gedrag, testbaar vastleggen).

### Presentatie na run (slice 26)

6. Als **analist** wil ik dat de **presentatie-fase** na een run **niet langer duurt dan nodig**, zodat de knop “Presentatie…” kort blijft.
7. Als **maintainer** wil ik dat **LTAP** per unieke overlay/scope/filter **maximaal één keer** per render-cyclus wordt berekend, zodat dubbel werk meetbaar verdwijnt.
8. Als **analist** wil ik in **LCC** bij **jaarselectie** geen merkbare pauze, zodat verkenning van jaren vloeiend blijft.
9. Als **maintainer** wil ik dat **LCC jaardetail** de **reeds gebouwde planningcurve** hergebruikt, zodat curve + detail niet twee keer dezelfde keten doorlopen.

### UI-respons (slice 25 gap)

10. Als **analist** wil ik bij **wisselen tussen FM-detail en Top 10** snelle respons, zodat moduswissel niet als “nieuwe run” voelt.
11. Als **analist** wil ik bij **metric/filter-wijziging in Top 10** alleen **Bijdragen-presentatie** herbouwd zien, niet LCC/LTAP, zodat irrelevant werk wegblijft.
12. Als **analist** wil ik bij **PBS-scope-wissel** correcte scoped totalen **zonder dubbele KPI-rerender**, zodat sidebar-klikken snappy blijven.
13. Als **maintainer** wil ik dat **`workspace_detail_split_render_depth`** daadwerkelijk **rerender-scope beperkt**, zodat slice-25 intentie in code zichtbaar is.

### Motor-profilen (slice 27 → presentatie)

14. Als **analist** wil ik in **FM-inspector** een **jaartabel** op echte runs, zodat verificatie niet alleen lifecycle-totalen toont.
15. Als **analist** wil ik **LCC/NB jaarverdeling** die consistent is met de motor, zodat ik niet elke klik legacy herberekening triggert.
16. Als **maintainer** wil ik **`horizon_profile`** bij run vullen via bestaande **jaartoerekening-SSOT**, zodat presentatie het profiel leest i.p.v. `_legacy_*` paden.
17. Als **maintainer** wil ik bij motorwijziging die analytische uitkomsten beïnvloedt **`CACHE_INPUTS_VERSION`** verhogen, zodat oude caches niet stilletjes fout zijn.

### Import / overlay (niet de Haarlem-case, wel regressie)

18. Als **analist** met **geïmporteerd AW-project** wil ik dat **planning-overlay materialisatie** alleen bij run gebeurt, niet bij elke UI-klik, zodat grote imports bruikbaar blijven.
19. Als **maintainer** wil ik **performance-regressietests** op Haarlem-fixture, zodat toekomstige slices trage runs vroeg vangen.

### Observability en support

20. Als **support** wil ik onderscheid **motor-tijd / presentatie-tijd / UI-rerender**, zodat klachten gericht worden.
21. Als **maintainer** wil ik **pytest-adapter tests** met **call-count stubs** op LTAP/LCC-builders, zodat dubbele aanroepen CI vangen zonder flaky timing.
22. Als **product owner** accepteer ik **lazy presentatie-cache** (alleen actieve modus direct na run) als **follow-up** als issue 01–04 onvoldoende zijn — niet verplicht in v1 van deze slice.

### Edge cases

23. Als **analist** wil ik na **code-upgrade** één langzame run accepteren bij **digest-mismatch**, daarna weer cache-snelheid — gedrag expliciet documenteren.
24. Als **analist** wil ik dat **ValidateWindow** dezelfde **run-beslissingslaag** gebruikt waar trivial, zodat legacy venster niet sneller blijft dan werkruimte.
25. Als **analist** wil ik **geen UI-freeze** op main thread tijdens zware presentatie — achtergrondthread blijft leidend (bestaand patroon behouden).

## Implementation Decisions

- **Run-beslissingsmodule (diep, Qt-vrij):** smalle API die uit `(project, path, user_intent)` afleidt:
  - `use_cache: bool` → `full_recompute=not use_cache`
  - `parallel: bool` (default true voor volledige runs)
  - `user_intent`: `start_or_load` vs `force_recompute`
  - Hergebruik bestaande `fm_cache_available` en `find_affected_fms`; geen parallelle cache-logica in views.
- **RunRunner / run-worker:** roept beslissingsmodule aan; **ValidateWindow-runner** dezelfde module waar haalbaar (minimale parity).
- **LTAP memoization (diep, Qt-vrij):** cache-key op canonieke overlay-state (disabled set + anchor years), PBS-scope, optionele taaktype-filter; **invalidate** bij project-wissel of overlay-mutatie die key wijzigt. Interface: `get_ltap_view(project, **kwargs) -> LTAPView`.
- **LCC planning:** `build_lcc_year_detail` accepteert optionele **reeds gebouwde curve**; render-index of LTAP-cache levert die. Geen tweede volledige `build_lcc_planning_curve_reconciled` binnen één UI-tick.
- **Render-scoping:** `_rerender_detail_for_current_scope` **respecteert** `RenderSplitDepth`:
  - `all_splits`: scope wijzigde → volledige detail-rerender + KPI
  - `active_modus_only`: alleen adapter(s) voor actieve modus (+ minimale KPI indien scope ongewijzigd)
  - Pure functie `required_detail_builders(snapshot, depth) -> frozenset[Modus]` testbaar zonder Qt.
- **Motor `horizon_profile`:** na `run_analytical` / vóór cache-write elk `FMResult` verrijken via bestaande horizon-profile builder (slice 27 SSOT). Presentatie-services lezen profiel; legacy pad alleen als profiel ontbreekt (migratie oude cache).
- **CACHE_INPUTS_VERSION:** verhogen in issue 05 wanneer profiel-invloed op FM-resultaat-digest of cache-trust policy wijzigt — expliciet in issue acceptance.
- **Geen wijziging** aan scrub-list, import-semantiek slice 35, of planning-overlay **business rules** — alleen performance van bestaande paden.

## Testing Decisions

- **Goede tests** meten **extern gedrag** of **contracten**: cache-only run telt 0 FM-recalculations; stub telt LTAP-aanroepen; moduswissel zonder scope triggert geen LCC-builder.
- **Modules met unit tests (geen GUI):** run-beslissingsmodule, LTAP-cache, render-scoping functie, LCC year-detail met injected curve.
- **Adapter tests:** uitbreiding `test_desktop_run_service`, run-runner tests met monkeypatch op `run_incremental_analysis`.
- **Performance-regressie:** uitbreiden `tests/perf/test_slice24_regression.py` of sibling met drempels t.o.v. `baseline.json` (cache-hit pad; optioneel boven-grens volledige run — flaky vermijden met ruime marge of alleen call-count in CI).
- **Prior art:** `test_desktop_analysis_cache_service`, `test_incremental_run`, slice 25 workspace tests, `FMResultsSortProxy`-patroon voor pure adapter modules.
- **Parity:** bestaande slice-35 import-tests en LCC what-if smoke blijven groen.

## Out of Scope

- **Volledige viewport-virtualisatie** voor alle tabellen.
- **Monte Carlo**, **deelruns**, **JSON-schema-wijzigingen** buiten eventuele `horizon_profile` serialisatie in cache (indien al aanwezig in FMResult-dict — geen nieuw top-level veld op project).
- **Subset-export Excel** (slice 35 follow-up).
- **Profileringstooling in CI** (cProfile artifacts) — alleen handreiking in handoff.
- **Lazy presentatie-cache per modus** (alle vier blokken pas bij eerste modusbezoek) — follow-up issue indien 01–04 onvoldoende.
- **Horizon_profile in FM-inspector reconcile-UX** uitbreiden beyond wat motor + bestaande slice 34 UI al doen.

## Further Notes

- **Issues (verticale snede):**

| # | Titel | Type |
|---|--------|------|
| 01 | Incrementele run + parallel in werkruimte | AFK |
| 02 | LTAP presentatie-cache (memoization) | AFK |
| 03 | LCC jaardetail hergebruikt curve | AFK |
| 04 | Modus-gescopeerde rerender (slice 25 gap) | AFK |
| 05 | Motor: horizon_profile bij run | AFK |

- **Aanbevolen volgorde:** 01 → 02 → 03 ∥ 04 → 05 (05 kan parallel na 01, maar cache-bump apart committen).
- **Handoff:** update `KANBAN_HANDOFF.md` in slice-map na implementatie; verwijs naar `tests/perf/baseline.json`.
- **Gebruikerscommunicatie:** traagheid ≠ verkeerde fixture-cache; check `<project>.rcm.cache.json` naast eigen `.rcm.json`.
