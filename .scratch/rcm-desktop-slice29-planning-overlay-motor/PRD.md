# Slice 29 — What-if overlay in motor, werkruimte-manipulatie, afbouw CM/PM-scenario

**Triage:** done  
**Type:** AFK (adapter + beperkte kern-run-input; geen persistent schema op `PMTask`)  
**Parent:** slice 28 (LCC-planning what-if presentatie), slice 23 (resultatenwerkruimte), `rcm_core.scenarios` (CM-beleid)  
**Supersedes (gedeelte):** slice 28 — “Herberekening met overlay buiten scope” en epic Planning-herberekening fase 1  
**Versie:** 1.0  
**Datum:** 2026-05-19  

**Vervolg:** slice 30 (`rcm-desktop-slice30-lcc-whatif-ux`) — post-run passief behouden in plot, selectie-UX, inklapbare KPI.

## Problem Statement

Slice 28 levert in de **resultatenwerkruimte** een sterke **lees- en presentatielaag** voor LCC-planning: type-filters, jaarklik naar taken, what-if overlay (`disabled_pm_ids`, `anchor_years`) en bulk **Alle REV passief**. De **motor** (`last_run`) blijft echter op het **ongewijzigde project**; correctief onderhoud in de LCC-staaf verandert daarom **niet** wanneer de analist REV-taken passief maakt of een CM-achtig scenario verkent. Dat botst met de verwachting “passief = niet uitvoeren” en dwingt analisten terug naar **ValidateWindow-LTAP** of naar **twee aparte CM/PM-scenario-runs** — traag, dubbel administratief, en semantisch verwarrend naast de what-if-knoppen.

Tegelijkertijd ontbreekt in de werkruimte nog **handmatige manipulatie**: verschuiven van geselecteerde taken (adapter klaar, UI niet), **toggle REV passief/actief**, en **passief per taak** in de jaardetailtabel.

Productbesluit uit grill-me: **één analyse-run** plus what-if vervangt functioneel de **gedwongen CM/PM-scenariovergelijking**; CM-beleid wordt een **preset** op de overlay, geen tweede motor-run.

## Solution

1. **Motor-bridge (fase 1):** Wanneer **What-if planning** actief is en de gebruiker **Herbereken analyse** start, materialiseert de adapter een **tijdelijk run-project** zonder passieve PM-taken (`disabled_pm_ids`). De motor draait op die clone; **`last_run`** wordt vervangen. **Geen** wijziging aan opgeslagen JSON. Na succes: **`disabled_pm_ids` leegmaken** (passief zit in de run); **`anchor_years` behouden** (verschuivingen blijven presentatie-only tot fase 2).
2. **Werkruimte-manipulatie:** Jaardetail-toolbar (na jaarklik): **verschuif geselecteerd**, **passief per rij**, **Alle REV passief/actief** met label-toggle en copy dat **CM pas na herberekenen** meebeweegt.
3. **CM-beleid-preset:** Knop/preset die het bestaande **`pm_tasks_for_scenario(..., "cm")`**-complement in `disabled_pm_ids` zet (zelfde semantiek als CM-scenario, zonder aparte scenario-key-run).
4. **Afbouw scenario-pad:** CM/PM **dubbele motor-runs** en split-LCC als standaardpad uitfaseren; KPI-tabel en placeholders terug naar **één `last_run`**. Scenario-code in kern/adapter mag blijven voor cache-compat of wordt later opgeruimd — geen nieuwe features op scenario-slots.

**Presentatie na herberekening:** LCC toont primair de nieuwe `last_run`; geen misleidende baseline-vs-overlay-PM-vergelijking waarbij CM al “scenario-achtig” is en baseline-LTAP nog volledige REV uit JSON toont.

## User Stories

### Mentale eenheid en verwachtingsmanagement

1. Als onderhoudsingenieur wil ik dat **passief = niet uitgevoerd in de motor** na herberekenen, zodat correctief onderhoud logisch stijgt wanneer REV uitblijft.
2. Als analist wil ik begrijpen dat **verschuiven (ankerjaren)** in fase 1 nog **geen** motor-impact heeft, zodat ik niet verwacht dat CM meebeweegt bij alleen verschuiven.
3. Als trainer wil ik in de UI lezen dat **what-if zonder herberekenen** vooral **preventief** direct toont en **correctief** pas na herberekenen, zodat presentatie vs motor helder blijft.
4. Als productowner wil ik **geen tweede CM/PM-run** meer als standaardworkflow, zodat de tool sneller en eenvoudiger wordt.
5. Als analist wil ik **CM-beleid** (SVO, wettelijk, NMF IN/TST) als **één preset** kunnen toepassen, zodat ik het oude CM-scenario kan verkennen zonder aparte run.

### Herberekenen met overlay (motor)

6. Als analist wil ik dat **Herbereken analyse** de overlay **alleen** meeneemt als **What-if planning** aan staat, zodat een uitgeschakelde modus echt baseline herberekent.
7. Als analist wil ik na geslaagde herberekening met passieve taken dat **`disabled_pm_ids` gewist** wordt, zodat passief niet dubbel (motor + overlay) wordt toegepast.
8. Als analist wil ik dat **ankerjaren** na herberekening **behouden** blijven voor presentatie, zodat ik verschuivingen kan blijven fine-tunen tot fase 2.
9. Als ontwikkelaar wil ik dat de run-input een **clone** van `RCMProject` is met gefilterde `pm_tasks` / `pm_effect_links`, zodat JSON en edit-buffer onaangetast blijven.
10. Als ontwikkelaar wil ik bij motorwijziging zonder schema-drift **`CACHE_INPUTS_VERSION`** verhogen wanneer de run-invoer zich wijzigt, zodat cache niet verkeerd hergebruikt.
11. Als analist wil ik bij herbereken-fout de overlay **niet stilletjes** te verliezen, zodat ik kan corrigeren en opnieuw proberen.
12. Als tester wil ik op fixture **`one_fm_planning.rcm.json`** kunnen asserten dat **alle REV passief + herbereken** het totale verwachte correctief verhoogt en PM in `last_run` daalt, zodat regressie deterministisch is.

### LCC-presentatie na run

13. Als analist wil ik na herberekening **één consistente LCC-curve** op `last_run`, zodat ik niet baseline-LTAP-met-REV vergelijk met CM uit een run-zonder-REV.
14. Als analist wil ik dat **what-if overlay** na herberekening alleen nog zinvol is voor **nieuwe** wijzigingen (passief/ankers), niet om hetzelfde passief nogmaals toe te passen.
15. Als analist wil ik in de jaarsamenvatting geen **misleidende Δ preventief** tussen baseline-JSON en overlay als de motor al het passief-scenario heeft gedraaid.
16. Als gebruiker wil ik **Reset naar baseline** nog steeds kunnen gebruiken om ankers en what-if-modus te wissen vóór nieuwe experimenten.

### Verschuiven (punt 1)

17. Als onderhoudsingenieur wil ik **geselecteerde verschuifbare taken** in what-if kunnen **bundelverschuiven** (integer jaren) vanuit de **LCC-jaardetailtabel**, zodat ik ValidateWindow niet hoef.
18. Als gebruiker wil ik verschuif-controls **alleen na jaarselectie** zien, zodat acties gekoppeld zijn aan “taken in dit jaar”.
19. Als gebruiker wil ik **multi-select** op detailrijen, spinbox (−50…+50) en knop **Verschuif geselecteerd**, zodat het gedrag aansluit bij LTAP.
20. Als gebruiker wil ik dat **SVO/WET** verschuiven **blokkeert** met duidelijke fouttekst, zodat governance-taken beschermd blijven.
21. Als tester wil ik shift blijven testen via de **publieke bundel-API** (`apply_overlay_shift`), zodat UI-wijzigingen de domeinregels niet herdefiniëren.

### Passief per taak en REV-bulk (punt 3)

22. Als onderhoudsingenieur wil ik **één taak** in de jaardetailtabel **passief/actief** kunnen zetten (what-if), zodat ik gericht kan experimenteren.
23. Als gebruiker wil ik dat passief per rij dezelfde regels volgt als LTAP (**niet** voor niet-toepasbare taken waar van toepassing).
24. Als onderhoudsingenieur wil ik **Alle REV passief** en, wanneer alle REV al passief zijn, **Alle REV actief**, zodat ik snel kan wisselen.
25. Als gebruiker wil ik een statusregel dat **correctief na bulk passief pas na herberekenen** verandert, zodat ik niet denk dat CM al is bijgewerkt.
26. Als domein-expert wil ik dat bulk REV **alleen** `TaskType.REV` raakt, zodat IN/TST/SVO/WET bewust apart blijven.

### CM-beleid-preset

27. Als analist wil ik preset **CM-beleid** die alle PM-taken uitzet **behalve** de toegestane CM-set (`pm_tasks_for_scenario`), zodat semantiek gelijk blijft aan het oude CM-scenario.
28. Als analist wil ik na CM-preset **optioneel herberekenen** om correctief te zien, zodat ik de oude CM-run vervang door één actie.
29. Als trainer wil ik dat CM-preset **niet** hetzelfde is als **Alle REV passief**, zodat copy en training niet verwarren.

### Afbouw CM/PM-scenario in werkruimte

30. Als analist wil ik **één knop Herbereken analyse** als standaard, zonder verplichte **Run CM** / **Run PM** voor dagelijks werk.
31. Als analist wil ik dat de **verticale CM|PM LCC-split** niet meer de primaire modus is, zodat het scherm overeenkomt met slice 26 single-run plus what-if.
32. Als analist wil ik dat de **KPI-tabel** niet meer twee scenario-kolommen vereist voor basisinzicht, zodat één `last_run` volstaat.
33. Als ontwikkelaar wil ik scenario-run-services **niet uitbreiden**; bestaande code mag deprecaten of ongebruikt blijven tot opruim-slice.
34. Als productowner wil ik tooltips/help over **scenariovergelijking** bijwerken naar what-if-taal, zodat documentatie niet tegenstrijdig is.

### Architectuur en onderhoud

35. Als ontwikkelaar wil ik **views** zonder directe `rcm_core`-imports (typing-only), conform AGENTS.md.
36. Als ontwikkelaar wil ik **planning-overlay state** uitbreiden met `bulk_all_rev_active`, `apply_cm_policy_preset`, en `clear_disabled_after_run`, zodat transities testbaar blijven.
37. Als ontwikkelaar wil ik **LTAP/LCC** en **motor-run-input** dezelfde definitie van “uitgezette PM” delen, zodat geen drift ontstaat.
38. Als ontwikkelaar wil ik **jaardetail** `pm_id` en `shiftable`/`passive` beschikbaar hebben in het view-contract voor UI-acties.

### Toegankelijkheid en fouten

39. Als gebruiker wil ik manipulatieknoppen **uit** zonder what-if, zodat read-only duidelijk blijft.
40. Als gebruiker wil ik **Nederlandse foutteksten** via message constants voor shift-, passief- en run-fouten.
41. Als gebruiker wil ik bij lege selectie voor verschuiven een duidelijke melding, zodat ik weet dat ik rijen moet kiezen.

## Implementation Decisions

### Scope en fasering

- **Fase A — Motor-bridge + herbereken-contract:** Materialiseer run-project uit overlay; herbereken met H1/R2; LCC-presentatie na run vereenvoudigen (geen dubbele passief-laag).
- **Fase B — Werkruimte UI:** U3 shift-toolbar, P1 per-rij passief, T2 REV-toggle + statuscopy.
- **Fase C — CM-preset + scenario-afbouw:** S1 preset; verberg/verwijder scenario-split en dubbele run-entrypoints uit werkruimte; update messages/tooltips.

Fase A is merge-blocker voor B/C; B en C kunnen parallel zodra overlay→run contract vastligt.

### Deep modules (testbare interfaces)

| Module | Verantwoordelijkheid | Testeer |
|--------|---------------------|---------|
| **Planning overlay state** (uitbreiding) | Transities: `bulk_all_rev_active`, `apply_cm_policy_preset(project)` → disabled set via scenario-complement, `clear_disabled_pm_ids()`, `all_rev_passive(project)` detectie voor label | Ja — pure unit |
| **Planning run materializer** (nieuw) | `materialize_project_for_overlay(project, overlay) -> RCMProject` clone; verwijdert `disabled_pm_ids` uit `pm_tasks` en `pm_effect_links`; geen JSON-write | Ja — adapter/kern unit |
| **Run service bridge** | `run(..., planning_overlay=...)` of wrapper: als overlay.active → materialize, anders baseline; what-if uit → negeer disabled | Ja — adapter met patch op `incremental_run` |
| **Post-run overlay policy** | Na succesvolle run: `overlay.clear_disabled_pm_ids()`; behoud `active` + `anchor_years` volgens R2 | Ja — unit |
| **LCC planning view builder** (aanpassing) | Na run met gewiste disabled: display = `last_run` zonder dubbele baseline/overlay-PM tenzij nieuwe overlay-wijzigingen | Ja — adapter |
| **What-if shift bridge** (bestaand) | Ongewijzigde bundel-API; UI roept aan | Ja — bestaand |
| **LCC year detail contract** (uitbreiding) | Rijen bevatten `pm_id`, `shiftable`, `is_passive` (afgeleid uit overlay) voor UI | Ja — adapter |
| **CM policy preset service** (dun) | Wrapper om `pm_tasks_for_scenario` → `disabled_pm_ids = all_pm - allowed` | Ja — unit |
| **Results workspace state** | Geen scenario-slot als primaire modus; planning overlay blijft sticky | Ja — unit waar nodig |

Views: toolbar op jaardetail, sync knoplabels, enablement op what-if + jaarselectie.

### Motor-input (geen schema op PMTask)

- **Geen** persistent `enabled`-veld op `PMTask` in deze slice.
- Run gebruikt **project-clone** met gefilterde PM-set (zelfde patroon als `build_project_for_scenario`, maar op `disabled_pm_ids`).
- **`anchor_years` gaan niet de motor in** (fase 2 / aparte PRD): documenteer in UI.
- **Herberekening:** overlay alleen als `PlanningOverlayState.active` (H1).
- **Na succes:** `disabled_pm_ids = ∅` (R2); optioneel overlay `active` laten voor verdere anker-edits.

```python
# Post-run overlay (besluit R2)
def after_successful_overlay_run(overlay: PlanningOverlayState) -> PlanningOverlayState:
    return PlanningOverlayState(
        active=overlay.active,
        anchor_years=overlay.anchor_years,
        disabled_pm_ids=frozenset(),
    )
```

### REV bulk toggle (T2)

- Knoplabel afhankelijk van: alle REV in project ∈ `disabled_pm_ids` → **Alle REV actief** (verwijdert REV uit set); anders **Alle REV passief** (union met alle REV ids).
- Actie vereist what-if actief (zoals nu); bij bulk passief zonder what-if: `begin_what_if()` eerst (bestaand gedrag).

### Jaardetail UI (U3, P1)

- Controls zichtbaar als: `last_run` aanwezig, LCC-modus, **kalenderjaar geselecteerd**, what-if **aan**.
- Selectie: `QTableView` selection model op detailtabel; map rij → `pm_id` via model.
- Per-rij passief: checkbox of toggle in extra kolom; roept `set_passive(pm_id, passive=...)`.
- Shift: spinbox + knop → `apply_overlay_shift`.

### CM-beleid-preset (S1)

- Preset zet `disabled_pm_ids` = `{pm_id for all tasks} - pm_tasks_for_scenario(project, "cm")`.
- **Niet** automatisch herberekenen; gebruiker kiest **Herbereken analyse** (what-if aan).
- Copy onderscheidt preset van REV-bulk.

### Afbouw CM/PM-scenario

- Werkruimte: **geen** primaire flow meer via `scenario_run_runner` / split LCC / “draai ander scenario”.
- **`last_run`** in app state blijft SSOT; KPI-tabel toont **Huidige analyse** (bestaande key), geen verplichte CM/PM-kolommen.
- Kern `scenarios.py` en scenario-cache-keys **niet verwijderen** in deze slice tenzij opruim expliciet; wel **geen nieuwe UI** op scenario-slots.
- Help-teksten in messages die CM/PM-run als hoofdpad beschrijven → bijwerken naar what-if + preset.

### Relatie slice 28

- Slice 28 PRD-regel “herberekening met overlay buiten scope” is **vervallen** voor passief (fase A).
- Slice 28 UI/copy “CM pas na aparte herberekening” wordt **concreet**: herberekening mét what-if is die actie.
- Presentatie-note bij what-if aan past aan: PM direct; CM na herberekenen **met what-if aan**.

## Testing Decisions

### Wat is een goede test

- Test **extern gedrag**: run-metrics, LCC-buckets, overlay-transities, UI enablement — niet private paint/layout.
- **Geen pixel-asserties** als merge-gate.
- Motor-tests: patch op `rcm_core.incremental_run` waar nodig (project seam), of integratie met kleine fixture.

### Te testen modules

| Module | Type | Prior art |
|--------|------|-----------|
| Planning overlay state (uitbreiding) | Unit | `tests/test_desktop_planning_overlay_state.py` |
| Planning run materializer | Unit | `build_project_for_scenario` in scenario_run_service |
| Run bridge + post-run policy | Adapter unit | `tests/test_slice28_lcc_planning.py`, run adapter tests |
| CM preset | Unit | `rcm_core.scenarios` tests indien aanwezig; anders nieuw |
| LCC na overlay-run | Integration | `tests/test_slice28_lcc_planning.py`, `one_fm_planning.rcm.json` |
| Werkruimte smoke | Optioneel pytest-qt | `tests/test_slice28_workspace_smoke.py` |

### Golden fixture

- **`one_fm_planning.rcm.json`**: uitbreiden documentatie met verwachting na **REV passief + herbereken** (CM↑, PM↓, totals).
- Assertie-tolerantie: reconcile-toleranties slice 21/28 blijven gelden.

### Niet verplicht in deze slice

- Volledige verwijdering van alle scenario-tests in repo (kan follow-up).
- B2: ankerjaren in motor.
- E2E op volledige demo-projecten.

## Out of Scope

### Expliciet niet in slice 29

- **B2 — Verschuivingen in motor:** `anchor_years` beïnvloeden `run_incremental_analysis`; CM mee bij shift-only — eigen PRD.
- **Overlay committen naar JSON** / persistent `enabled` op `PMTask` + schema/parity/migratie.
- **PBS-bundeling REV (Planning-2b)** en **functioneel meekoppelen (Planning-2c)**.
- **Volledige verwijdering** van `scenario_run_service`, compare-runner, cache scenario-keys — aparte opruim-slice na stabilisatie.
- **CM|PM split LCC** opnieuw activeren met gedeelde filters.
- **ValidateWindow** volledig verwijderen.
- **Export**, Monte Carlo, per-FM correctief in jaardetail.

### Vervolg-epics (vastgelegd)

| Epic | Inhoud |
|------|--------|
| **Planning-anker-motor (B2)** | Motor-run met effectief PM-schema uit `anchor_years` |
| **Scenario-code opruimen** | Dead code scenario-slots, compare API, cache keys |
| **Planning-2b / 2c** | PBS-bundeling, meekoppelen (ADR scrub-list) |

## Further Notes

### Grill-me besluiten (samenvatting)

| Onderwerp | Besluit |
|-----------|---------|
| Herberekening | Overlay meenemen in motor (was slice 28 out-of-scope) |
| Motor-input fase 1 | Alleen `disabled_pm_ids`; ankers presentatie-only |
| Na herberekening | `disabled_pm_ids` leeg; ankers behouden |
| What-if gate | Motor-overlay alleen als what-if aan |
| CM/PM-scenario | Uitfaseren als standaardpad; CM-beleid = preset |
| Shift UI | Na jaarselectie, LTAP-pariteit |
| REV-knop | Toggle passief/actief + copy CM na herberekenen |
| Per taak | Passief in jaardetail |

### Risico’s

- **LCC baseline/overlay na run:** presentatielaag moet niet opnieuw “twee werelden” tonen; mogelijk baseline/overlay-split alleen bij actieve niet-gereconcilieerde wijzigingen.
- **Cache:** run met materialized project moet consistent zijn met `CACHE_INPUTS_VERSION` / scenario_key-beleid; geen stille cache-hit op verkeerde PM-set.
- **Scenario-afbouw:** grote touch op `test_desktop_results_workspace_window.py` — plan als sub-issue of fase C.
- **Gebruikers met oude workflow:** help en release note: CM/PM-run → what-if preset + herberekenen.

### Afhankelijkheden

- Slice **28** geleverd (overlay state, LCC planning, detailtabel, bundel-bridge).
- Slice **27** (NMF motor) voor NMF-gerelateerde CM-preset-asserties — geen harde blocker voor passief/REV-pad.
