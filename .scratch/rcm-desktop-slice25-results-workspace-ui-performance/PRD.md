# PRD — RCM2 desktop slice 25 (resultatenwerkruimte: UI-respons en dubbel werk weg)

**Status:** done  
**Versie:** 1.0  
**Triage-labels:** done

## Problem Statement

Gebruikers ervaren de **resultatenwerkruimte** (standaard na start) als **traag**,
zelfs wanneer de **analytische run** al klaar is. Typische pijnpunten:

- **Wisselen tussen scenario’s** (CM ↔ PM via KPI-kolom of na een run) voelt
  als een merkbare pauze, terwijl er geen nieuwe motor-run nodig is.
- **Wisselen tussen modi** (Bijdragen, LCC, Niet-beschikbaarheid, Preventief
  onderhoud, FM-detail) triggert zichtbaar zwaar werk op het hoofdvenster.
- Grote projecten versterken het effect: **PBS-boom**, **tabellen** en
  **grafiek-adapters** worden vaak opnieuw opgebouwd zonder dat de gebruiker
  daar expliciet om vroeg.

De oorzaak zit **niet alleen** in de rekencode (`RunResult` is al beschikbaar),
maar in **synchrone presentatie op de UI-thread**: dubbele signalen bij
state-updates, **parallelle “legacy”- en scenario-split**-renderpaden, en
kostbare Qt-layout (o.a. breedte-meting over alle cellen, volledig uitklappen
van de boom bij filter).

## Solution

Maak de werkruimte **responsief** door **hetzelfde werk niet twee keer** te doen,
**alleen wat nodig is voor de zichtbare modus** (binnen redelijke architectuur),
en **Qt-kosten** te temperen — **zonder** het functionele contract te breken:

- **Scenario-activering**: wanneer `project_snapshot` en `RunResult` samen
  wisselen, moet de UI **één coherente update** krijgen (één rerender-rondje),
  niet twee achtereenvolgens door losse `project_changed`- en
  `run_changed`-signalen.
- **Scenario-modus + gesplitste weergave**: zodra de gesplitste CM/PM-zone de
  canonieke presentatie is voor tijdreeksen en bijdragen, mag het vullen van
  verborgen **legacy single-slot**-widgets **geen dubbele adapterketens**
  meer veroorzaken (tenzij een modus die split expliciet niet gebruikt daar nog
  van profiteert — zie beslissingen).
- **Moduswissel**: herbouw alleen de **presentatie voor de actieve modus** (en
  wat de KPI-tabel minimaal nodig heeft), niet blind alle vier split-ketens bij
  elke state-wissel als dat functioneel overbodig is.
- **Qt-presentatie**: vervang of beperk **ResizeToContents** waar het schaalt
  slecht; beperk **`expandAll`** op de PBS-boom tot wat nodig is voor
  filter-navigatie.
- **Observability**: leg **acceptatiecriteria** vast (bijv. scenario-wissel onder
  X ms op referentie-fixture, of geen dubbele aanroep-teller in tests) en
  documenteer een **korte profiling-handreiking** voor maintainers.

Architectuurregels blijven gelden: **Adapter Qt** blijft eigenaar van venster-
orchestratie; **domain model** en **Run-orchestratie** in de kern worden niet
“versneld” in deze slice tenzij profiling een aparte bottleneck aantoont.

## User Stories

### Scenario-wissel en AppState

1. Als **analist** wil ik bij **klikken op een andere scenario-kolom in de
   KPI-tabel** dat de werkruimte **direct** meeschakelt, zodat ik niet wacht op
   dubbel werk dat ik niet zie.
2. Als **analist** wil ik dat **activeren van het scenario na een run** dezelfde
   snappy ervaring geeft als daarna nog eens wisselen, zodat het systeem
   voorspelbaar reageert.
3. Als **maintainer** wil ik dat **één scenario-slot-actie** hooguit **één**
   volledige **PBS-sync + detail-rerender + KPI-refresh** veroorzaakt, zodat
   regressies testbaar zijn.
4. Als **maintainer** wil ik een **duidelijk seam** (methode of signaal) voor
   “atomisch project+run voor scenario”, zodat toekomstige features niet weer
   dubbele emits introduceren.

### Dubbele renderpaden (legacy vs split)

5. Als **analist** wil ik dat **CM- en PM-curven naast elkaar** in scenario-
   modus **correct** blijven, zonder dat ik merk van interne dubbele berekening.
6. Als **analist** wil ik dat **FM-detail** bij scenario-modus **gebonden blijft
   aan het actieve scenario-slot**, zoals nu bedoeld.
7. Als **maintainer** wil ik dat **LCC-, bijdragen-, PM- en
   niet-beschikbaarheid-adapters** niet **drie keer** dezelfde curve/rij-set
   bouwen voor één UI-state als dat vermijdbaar is.
8. Als **product owner** accepteer ik dat **legacy widgets** kort **leeg** mogen
   blijven in scenario-split-modi **als** er geen regressie is in zichtbare
   UI-tests en schermopnames.

### Moduswissel en lazy werk

9. Als **analist** wil ik bij **overschakelen naar LCC** dat alleen **LCC-gerelateerde**
   presentatie opnieuw wordt opgebouwd, zodat grote bijdragen-aggregaties me
   niet vertragen als ik ze niet nodig heb.
10. Als **analist** wil ik bij **overschakelen naar Bijdragen** dat **bron/metric**
    combinaties **snel** reageren zodra ik ze wijzig.
11. Als **analist** wil ik dat **KPI-tabel** na scope-wijziging **correct** blijft
    en **binnen één rerender** wordt ververst.
12. Als **maintainer** wil ik dat de **orchestrator** (vensterlaag) een **expliciete
    beslistabel** heeft: welke modus vraagt welke adapter(s), zodat uitbreiding
    van modi niet impliceert “alles altijd”.

### PBS-sidebar en filter

13. Als **analist** met een **grote PBS** wil ik dat **filteren** in de sidebar
    **bruikbaar blijft** zonder secondenlange UI-freeze.
14. Als **analist** wil ik dat **gematchte takken zichtbaar** blijven bij filter,
    zonder dat de hele wereldboom onnodig wordt uitgeklapt.
15. Als **analist** wil ik dat **wisselen van scenario** de boom **één keer**
    synchroniseert met de actieve run, niet twee keer achter elkaar.

### Qt-tabellen en headers

16. Als **analist** wil ik dat **kolombreedtes** logisch blijven (leesbaarheid),
    ook als we niet overal `ResizeToContents` gebruiken.
17. Als **analist** met **veel FM-regels** accepteer ik **Interactieve resize**
    of **Stretch** waar dat de UI **vlot** houdt.
18. Als **maintainer** wil ik **centrale policy** voor resize-gedrag per tabel-
    type, vergelijkbaar met eerdere drempelpatronen elders in de desktop.

### KPI en scope

19. Als **analist** wil ik dat **KPI-cellen** na scenario-wissel **consistent** zijn
    met het actieve slot en de gekozen PBS-scope.
20. Als **analist** wil ik dat **lege scenario-slots** zichtbaar blijven als
    placeholder **zonder** dat daardoor dubbel werk voor gevulde slots wordt
    gedaan.

### Non-functioneel en regressie

21. Als **maintainer** wil ik **pytest** op de **Adapter Qt**-laag die **aantal
    zware bouw-calls** begrenst of **één emit** afdwingt, zodat performance-
    regressies CI vangen.
22. Als **maintainer** wil ik **bestaande scenario-slot- en workspace-state-tests**
    groen houden, zodat gedrag van modus/source/metric niet breekt.
23. Als **maintainer** wil ik een **korte notitie** in de slice hoe ik **cProfile**
    of sampling op de main thread gebruik bij twijfel over bottlenecks.
24. Als **product owner** wil ik dat **ValidateWindow** (legacy vlag) **niet**
    verplicht in scope is, tenzij dezelfde anti-patronen er trivial hergebruikt
    worden — dan **minimale parity** of expliciet **out of scope**.

### Documentatie en gebruikersverwachting

25. Als **gebruiker** wil ik dat **traagheid na een run** duidelijk te onderscheiden
    is van **traagheid bij klikken**, zodat support begrijpt waar te meten.
26. Als **analist** wil ik dat **toolbar-acties** (validate, run CM, run PM)
    **responsief** blijven door geen onnodig zwaar werk op dezelfde tick te stapelen
    waar dat vermijdbaar is.

### Edge cases

27. Als **analist** wil ik bij **alleen CM-slot gevuld** dat **PM-placeholder**
    zichtbaar blijft **zonder** dat CM-data dubbel wordt herbouwd.
28. Als **analist** wil ik bij **project wisselen** dat **scenario-slots** worden
    gewist zoals nu bedoeld, **zonder** extra freezes door overbodige renders
    vóór de clear.
29. Als **analist** wil ik dat **`Toon hele project`** en **PBS-klik** snel
    reageren na optimalisatie.
30. Als **maintainer** wil ik dat **teardown / setModel(None)** patronen voor Qt-
    ownership **intact** blijven (geen nieuwe crash bij sluiten venster).

## Implementation Decisions

- **AppState-seam uitbreiden of wrappen** met een **atomische update** voor
  “scenario-slot actief: project + run samen”, zodat verbonden views **één**
  `project_changed`/`run_changed`-equivalent of **één** gecombineerd signaal
  ontvangen. Alternatief: **batchvlag** op `AppState` die tijdelijk onderdrukt
  tussenliggende renders — voorkeur naar **eenvoudig contract** (één signaal of
  één publieke `apply_scenario_slot_view(slot)` die intern coherent is).
- **Resultatenwerkruimte-orchestratie**: herstructureer `_rerender_detail_*` zodat
  **scenario-modus** niet blind **legacy single-slot + split** voor dezelfde
  datasets uitvoert tenzij een modus dat echt nodig heeft (expliciet vastleggen
  per modus: FM-detail, overige).
- **Render-scoping per modus**: een kleine **beslissingslaag** (diep module-
  kandidaat) die uit `ResultsWorkspaceState` + `ScenarioSlotState` een **lijst
  vereiste presentatie-adapters** afleidt — testbaar zonder Qt.
- **PBS-proxy / filter**: vervang of beperk **globaal `expandAll`**; voorkeur:
  **alleen paden naar matches** uitklappen, of **dieptelimiet**, of uitstellen
  naar `singleShot(0)` alleen voor expand-stap — vastleggen welk gedrag UX-
  acceptabel is in issues.
- **Tabel header policy**: centraliseer **resize-beleid** (constanten + helper)
  voor KPI-, bijdragen-, jaar-tabellen; standaard **niet** overal
  `ResizeToContents` op grote views.
- **Architectuur**: geen nieuwe directe imports vanuit views naar `rcm_core`
  (bestaand contract); zware pure functies blijven in **Adapter**-services;
  venster blijft dunne orchestratie.
- **Motor/cache**: geen wijziging aan `CACHE_INPUTS_VERSION` of run-semantiek
  behorend bij deze slice, tenzij profiling een aparte PRD rechtvaardigt.

## Testing Decisions

- **Goede tests** observeren **extern gedrag** of **meetbare contracten**:
  aantal keren dat een **stub-adapter** wordt aangeroepen bij scenario-wissel;
  of model-rijen na moduswissel overeenkomen met verwachting op fixture-data.
- **Modules met voorkeur voor unittest zonder GUI**: de nieuwe of uitgebreide
  **render-beslissingsfunctie** (pure mapping van state → vereiste views).
- **pytest-qt / vensterflows** waar nodig voor **signaalvolgorde** en **geen
  dubbele sync** na scenario-activering.
- **Prior art**: bestaande tests rond `ResultsWorkspaceState`, `ScenarioSlotState`,
  KPI-tabelservice, workspace-split-layout; patroon uit eerdere slice voor
  **drempels / policy** op zware Qt-operaties.

## Out of Scope

- Nieuwe **Monte Carlo**, **deelruns**, of wijzigingen aan **JSON-schema** /
  **domain model** serialisatie.
- **Volledige** migratie van `ValidateWindow` (legacy) tenzij expliciet gekozen
  in een issue met mini-parity.
- **Viewport-virtualisatie** voor alle tabellen — alleen als follow-up als
  header-policy onvoldoende is.
- **Persistente QSettings** voor resize-voorkeuren — later mogelijk.

## Further Notes

- Parent functioneel ontwerp: resultatenwerkruimte (scenario-slots, modi, PBS-
  scope als presentatie-filter op `RunResult`).
- Meet op **representatieve fixtures** (groot/klein) voordat drempels definitief
  worden.
- **Issues (verticale snede):** `issues/01.md` (atomische state), `issues/02.md`
  (legacy vs split dedupe), `issues/03.md` (modus-gescopeerde render), `issues/04.md`
  (Qt resize + PBS-expand). Kies per issue waar pytest zuiver volstaat vs.
  pytest-qt — voorkeur: pure beslislaag zonder GUI waar mogelijk.
- Korte **main-thread profiling**-notitie (bijv. `cProfile` of sampling) mag in
  `issues/01.md` of team-wiki; geen verplichte tooling in CI in deze slice.
- **Status follow-up:** issues 01–04 en deze PRD zijn op `done` gezet na
  implementatie + groene `pytest tests/` (volledige suite).
