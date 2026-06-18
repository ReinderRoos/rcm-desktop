# PRD — RCM2 desktop slice 23 (resultatenwerkruimte met PBS-sidebar en scenario-slots)

**Status:** done  
**Versie:** 1.0  
**Triage-labels:** done

## Problem Statement

Het huidige `ValidateWindow` voelt visueel vol en stuurt de gebruiker niet naar
een duidelijke beslis-as. Validatie, projectoverzicht, faalwijzen-editor,
FM-resultatentabel, PBS-resultatenboom, LCC-single-run, LCC-compare,
KPI-vergelijking en LTAP what-if delen één scherm met verticale stapeling.
Daardoor:

- **Geen helder mentaal model.** De PBS-hiërarchie verschijnt pas onderaan als
  resultatenboom, terwijl de bediening (welke FM-set, welk scenario, welke
  metric) verspreid is over rijen knoppen en getoggelde panelen.
- **Resultaten zijn statisch.** De gebruiker ziet altijd een FM-tabel én een
  PBS-boom én een LCC-grafiek tegelijk; selectief inzoomen op één deel
  (bijv. *“laat me alleen de bijdragen aan niet-beschikbaarheid van dit
  PBS-subtree zien”*) bestaat niet.
- **Scenariovergelijking is een korte momentopname.** De huidige
  `Vergelijk scenario's (CM/PM)`-knop draait beide in één klik en toont een
  KPI-lijst plus een gestapelde LCC-grafiek; de twee scenario-resultaten leven
  niet als afzonderlijke ‘slots’ die de gebruiker over alle weergaven
  (bijdragen, LCC, niet-beschikbaarheid, preventief onderhoud) naast elkaar kan
  vergelijken.
- **‘Huidig project’ en ‘CM-scenario’ overlappen visueel.** De huidige
  single-run-LCC en de compare-CM-curve gebruiken vergelijkbare labels en
  kleurpalet, terwijl `Huidig project` in deze herinrichting geen plaats meer
  heeft.
- **Tijd-as voor niet-beschikbaarheid ontbreekt.** Niet-beschikbaarheid is nu
  een lifecycle-totaal in `PBSResult`/`PBSResultsTreeModel`; een grafiek
  `Niet-beschikbaarheid over kalenderjaren` bestaat niet.

Voor reliability-analisten en assetmanagers leidt dit tot extra klik- en
interpretatiewerk: ze moeten zelf navigeren tussen panelen, zelf koppelen welke
PBS bij welk getal hoort, en kunnen scenario-uitkomsten niet als A/B in vier
verschillende grafiekvormen lezen.

## Solution

Vervang het bestaande `ValidateWindow` door een **resultatenwerkruimte** met
een vast mentaal model:

- **Links — PBS-kolom als vaste navigatiekolom**: hybride boom (structuur +
  aggregaattotalen voor het actieve scenario-slot) met substring-filter;
  toggle-baar via toolbar, default zichtbaar; harde filter op
  grafiek/tabel/KPI’s wanneer een knoop is geselecteerd; `Toon hele project`
  als reset.
- **Rechts — resultatengebied** met drie verticale zones:
  - **KPI-tabel** boven (één gedeelde tabel met scenario-kolommen,
    PBS-scope-aware voor 3 van de 4 rijen).
  - **Gesplitste grafiek-zone** in het midden (CM boven/links, PM onder/rechts;
    verticaal voor tijdreeksen, horizontaal voor categorie-bijdragen).
  - **Detailtabel** onder de grafiek, meebewegend met de actieve modus.
- **Modi** als kerncontract van de werkruimte: `Bijdragen`, `LCC`,
  `Niet-beschikbaarheid`, `Preventief onderhoud`, plus `FM-detail` als
  detailmodus. Sub-toggles per modus (`Bijdragen` heeft `PBS`/`Faalwijze` plus
  metric-keuze; `Preventief onderhoud` heeft `Kosten`/`Aantal uitvoeringen`).
- **Scenario-slot-model** met twee aparte run-knoppen `Run CM-scenario` en
  `Run PM-scenario`. Resultaten leven in sessie-geheugen per scenario-key
  (`CM`, `PM`). Gesplitste grafiekweergave zodra in scenario-modus; placeholder
  voor leeg slot.
- **PBS-scope is presentatie-filter, geen deelrun.** De motor draait altijd op
  het hele project. Een Qt-vrije presentatie-adapter filtert `RunResult` op
  PBS-subtree voor grafiek/tabel/KPI/boomtotalen.
- **Niet-beschikbaarheid over kalenderjaren** in deze slice als **proxy** uit
  het bestaande faalmomenten-jaarprofiel (`lcc_profile`), met expliciete
  disclaimer; lifecycle-totaal reconcilieert exact met motor-output.
- **`Huidig project / één run` vervalt.** `Volledige analyse` en
  `Vergelijk scenario's (CM/PM)` knoppen worden verwijderd zodra de
  scenario-slot-flow live is.
- **Validate- en save/dirty-flow ongewijzigd**: pas na geldige validate zijn
  scenario-knoppen actief; faalwijzen-overlay, save, save-as, mtime-conflict
  en save-blocked-during-run gedragen zich identiek.
- **LTAP what-if** wordt een aparte tab/sub-werkruimte met behoud van
  bundel-shift; `Preventief onderhoud`-modus in de hoofdwerkruimte is
  read-only.

Gefaseerde uitrol binnen deze PRD:

1. **Fase A — Layout-skeleton + presentatie-adapter.** Nieuwe werkruimte,
   PBS-sidebar, KPI-tabel-stub, placeholders. Bestaande `Volledige analyse`-
   en `Vergelijk`-knoppen blijven tijdelijk werken zodat regressies vermijdbaar
   zijn.
2. **Fase B — Modi-switch.** `Bijdragen`, `LCC`, `Niet-beschikbaarheid`
   (proxy), `Preventief onderhoud`, `FM-detail`. Detailtabel beweegt mee.
3. **Fase C — Scenario-slot-model + run-knop-splitsing.**
   `Run CM-scenario` / `Run PM-scenario` vervangen oude knoppen. KPI-tabel
   toont twee scenario-kolommen.

Latere slices (apart te ontwerpen): config + `Start Analyse` met PM-niveau (D),
`Geoptimaliseerd` scenario (E), deelruns + Monte Carlo + faalwijze-isolatie (F),
echte niet-beschikbaarheid-jaarvector in de kern.

## User Stories

### Hoofdindeling en PBS-sidebar

1. Als reliability-analist wil ik een vaste **PBS-kolom links** met de
   hiërarchie van het project, zodat ik altijd weet welk deel van het systeem
   ik bekijk.
2. Als reliability-analist wil ik de PBS-kolom met **één toolbar-knop
   verbergen/tonen**, zodat ik bij smalle schermen extra ruimte krijg voor
   grafiek en tabel.
3. Als gebruiker wil ik dat de PBS-kolom **default zichtbaar** is na project
   laden, zodat ik direct navigatiehouvast heb.
4. Als gebruiker wil ik dat de PBS-kolom **ook vóór een run zichtbaar** is met
   de projectstructuur (lege cijferkolommen), zodat ik me kan oriënteren op
   het project voordat ik reken.
5. Als gebruiker wil ik dat **klikken op een PBS-item** alle weergaven rechts
   filtert op dat subtree, zodat ik focus kan houden op één deel van het
   systeem.
6. Als gebruiker wil ik een prominente actie **`Toon hele project`**, zodat ik
   snel terug ben naar projectbrede weergave.
7. Als analist wil ik dat de PBS-boom **subtree-totalen** toont (faalmomenten,
   downtime, niet-beschikbaarheid %, kosten), zodat de cijfers in de boom
   overeenkomen met wat de grafiek toont.
8. Als gebruiker wil ik een **substring-filter** boven de PBS-boom op `pbs_id`
   en `bouwdeel_naam`, zodat ik snel een knoop kan vinden bij honderden items.
9. Als gebruiker wil ik dat **gematchte paden in het filter automatisch
   uitklappen**, zodat ik de gevonden knoop direct zie.
10. Als gebruiker wil ik dat de PBS-boom **default ingeklapt** start, zodat
    grote projecten geen overweldigende boom geven.

### Resultaten-werkruimte: KPI-tabel, grafiek, detailtabel

11. Als gebruiker wil ik **één gedeelde KPI-tabel** met scenario-kolommen,
    zodat ik in één blik scenario’s op kerncijfers kan vergelijken.
12. Als analist wil ik dat de KPI-tabel **lifecycle faalmomenten,
    niet-beschikbaarheid %, lifecycle kosten EUR en PM-taken actief** toont,
    zodat ik de drie hoofdvragen plus scenario-context direct lees.
13. Als gebruiker wil ik dat **drie van de vier KPI’s de PBS-scope
    respecteren** (faalmomenten, niet-beschikbaarheid %, kosten EUR), zodat ze
    meebewegen met mijn selectie.
14. Als gebruiker wil ik dat **PM-taken actief** een scenario-eigenschap blijft
    (rij 4 negeert PBS-scope), zodat scope-filtering die metric niet vervormt.
15. Als gebruiker wil ik dat het **actieve scenario** voor de PBS-boom-cijfers
    herkenbaar is via een **accent op de kolom-header** in de KPI-tabel.
16. Als gebruiker wil ik op een **scenario-kolomheader klikken om dat scenario
    te activeren** voor de PBS-boom, zodat ik geen aparte toggle nodig heb.
17. Als gebruiker wil ik dat een leeg scenario-kolom een **`—`-placeholder**
    toont, zodat de tabelbreedte niet springt na een tweede run.
18. Als gebruiker wil ik een **gesplitste grafiek-zone** met twee
    scenario-slots, zodat A/B-vergelijking de standaardvorm is in
    scenario-modus.
19. Als gebruiker wil ik dat **tijdreeksen verticaal** worden gesplitst (CM
    boven, PM onder), zodat de kalenderjaar-as breed leesbaar blijft.
20. Als gebruiker wil ik dat **categorie-bijdragen horizontaal** worden
    gesplitst (CM links, PM rechts), zodat ik staafhoogten direct kan
    vergelijken.
21. Als gebruiker wil ik dat **scenario-identiteit** via titel-label en vaste
    positie zichtbaar is, niet via kleurcodering, zodat datatype-kleuren
    (correctief/preventief) eenduidig blijven.
22. Als gebruiker wil ik dat de **detailtabel onder de grafiek meebeweegt** met
    de actieve modus, zodat de lees-laag onder de grafiek altijd overeenkomt
    met de visualisatie.
23. Als gebruiker wil ik dat de **detailtabel ook PBS-scope respecteert**,
    zodat data en grafiek consistent zijn.

### Modi

24. Als reliability-analist wil ik een knop **`Bijdragen`** met staafdiagram,
    zodat ik in één oogopslag de grootste bijdragers zie.
25. Als reliability-analist wil ik in `Bijdragen` een sub-toggle
    **`PBS`/`Faalwijze`**, zodat ik dezelfde metric kan tonen op verschillende
    analysebronnen.
26. Als gebruiker wil ik dat `Bijdragen` standaard **PBS** als bron heeft,
    zodat de samenhang met de linker PBS-kolom direct duidelijk is.
27. Als analist wil ik in `Bijdragen` een **metric-keuze**
    (`Niet-beschikbaarheid`, `Kosten`, `Downtime`, `Faalmomenten`, `Risico`),
    zodat ik de bijdragen op verschillende KPI-hoeken kan rangschikken.
28. Als gebruiker wil ik dat `Bijdragen` default
    **`Niet-beschikbaarheid`** rangschikt, zodat het scherm aansluit op de
    oorspronkelijke wens *“belangrijkste bijdrage aan niet-beschikbaarheid”*.
29. Als gebruiker wil ik dat `Bijdragen` standaard de **top-10** toont, zodat
    de staafdiagram leesbaar blijft.
30. Als analist wil ik een knop **`LCC`** met kosten over kalenderjaren
    (correctief + preventief), zodat ik kostenpieken in de tijd kan beoordelen.
31. Als analist wil ik een knop **`Niet-beschikbaarheid`** met
    niet-beschikbaarheid per kalenderjaar, zodat ik beschikbaarheidspieken in
    de tijd kan beoordelen.
32. Als analist wil ik een knop **`Preventief onderhoud`** met PM-kosten per
    kalenderjaar, zodat ik onderhoudsbelasting in de tijd kan beoordelen.
33. Als gebruiker wil ik in `Preventief onderhoud` een sub-toggle
    **`Kosten`/`Aantal uitvoeringen`**, zodat ik tussen financiële en
    plannings-impact kan wisselen.
34. Als gebruiker wil ik een knop **`FM-detail`** met de huidige
    FM-resultatentabel, zodat de gedetailleerde lijst niet verloren gaat.
35. Als gebruiker wil ik dat de losse `Kosten`-knop **vervalt**, omdat kosten
    al in `LCC` zitten, zodat de toolbar simpeler blijft.

### Stickiness en defaults

36. Als gebruiker wil ik dat **PBS-selectie behouden blijft** bij modus-wissel,
    scenario-wissel en nieuwe analyse-runs, zodat ik niet opnieuw hoef te
    zoeken.
37. Als gebruiker wil ik dat **sub-toggles per modus sticky** blijven, zodat
    mijn voorkeur bij teruggaan naar dezelfde modus weer geldt.
38. Als gebruiker wil ik dat de **metric in `Bijdragen` sticky** blijft, zodat
    ik dezelfde KPI kan blijven onderzoeken.
39. Als gebruiker wil ik dat **bij ander project laden alles wordt gereset**
    naar defaults (`Bijdragen`, `Niet-beschikbaarheid`, geen PBS-selectie),
    zodat ik niet aan het vorige model blijf vasthangen.
40. Als gebruiker wil ik dat **na de eerste run de initiële modus `Bijdragen`**
    is, zodat ik direct topbijdragen zie.

### Scenario-slots

41. Als analist wil ik **twee aparte run-knoppen** (`Run CM-scenario`,
    `Run PM-scenario`), zodat ik scenario’s sequentieel kan runnen en bewaren.
42. Als gebruiker wil ik dat scenario-resultaten **per scenario-key** worden
    bewaard, zodat een tweede run van hetzelfde scenario het bestaande slot
    vervangt.
43. Als gebruiker wil ik dat scenario-resultaten **alleen in deze sessie**
    bestaan, zodat niets ‘stale’ op disk staat zonder project-identiteit.
44. Als gebruiker wil ik dat **ander project laden of reload** alle
    scenario-slots leegt, zodat oude curves niet blijven hangen.
45. Als gebruiker wil ik dat **één scenario-run tegelijk** kan lopen (andere
    knoppen disabled), zodat de motor-state voorspelbaar blijft.
46. Als gebruiker wil ik dat het **laatst-gerunde scenario automatisch actief**
    wordt voor de PBS-boom-totalen, zodat ik direct verder kan analyseren.
47. Als gebruiker wil ik dat zodra ik in **scenario-modus** zit, het
    grafiek-gebied direct **gesplitst** is met placeholder “Draai ook het
    andere scenario”, zodat het mentale model van twee slots vanaf het begin
    duidelijk is.
48. Als gebruiker wil ik dat de **oude `Vergelijk scenario's`-knop verdwijnt**
    zodra fase C live is, zodat er één manier is om scenario’s te runnen.
49. Als gebruiker wil ik dat de **oude `Volledige analyse`-knop verdwijnt**,
    omdat `Huidig project` als concept vervalt.

### Empty states en placeholders

50. Als gebruiker wil ik direct na project laden **zichtbare maar lege
    skeletten** voor grafiek en tabel met begeleidende tekst, zodat ik weet
    wat me te wachten staat zonder dat de layout springt na de eerste run.
51. Als gebruiker wil ik per modus een **korte uitleg-zin** boven de lege
    grafiek, zodat ik weet wat de modus betekent zonder eerst te runnen.
52. Als gebruiker wil ik bij **PBS-scope op een leeg subtree** een expliciete
    empty-state, zodat ik niet denk dat de motor faalde.

### Niet-beschikbaarheid proxy

53. Als analist wil ik dat **niet-beschikbaarheid per kalenderjaar** in deze
    slice een proxy uit het faalmomenten-jaarprofiel toont, zodat ik de
    tijd-as nu al krijg.
54. Als analist wil ik dat het **lifecycle-totaal niet-beschikbaarheid** exact
    gelijk blijft aan de motor-output, zodat er geen drift ontstaat tussen
    tabel en grafiek.
55. Als gebruiker wil ik een **expliciete disclaimer in tooltip en titel** dat
    dit een proxy is, zodat ik weet dat een latere kern-iteratie dit kan
    verfijnen.

### Reconciliatie en consistentie

56. Als analist wil ik dat **LCC-tijdreeksen** in deze werkruimte dezelfde
    reconciliatie aanhouden als slice 21 (correctief en preventief
    somreconciliatie tegen `RunResult`).
57. Als analist wil ik dat **PBS-scope-filtering optelt** tot exact dezelfde
    totalen als unscoped wanneer het hele project geselecteerd is, zodat
    scope-filter onbedoelde rebalancing voorkomt.
58. Als analist wil ik dat de **KPI-tabel-cijfers** overeenkomen met de
    FM-tabel- en PBS-boomtotalen voor dezelfde scope, zodat ik geen drie
    versies van dezelfde waarheid zie.

### Validate- en save-flow

59. Als gebruiker wil ik dat **scenario-runs pas mogelijk zijn na geldige
    validate**, zodat ik geen run op een ongeldig project start.
60. Als gebruiker wil ik dat **`Faalwijzen bewerken`** een overlay-paneel
    blijft, zodat editor-context en analyse-context niet samenvallen.
61. Als gebruiker wil ik dat **save/save-as/mtime-conflict** identiek werkt aan
    de huidige flow, zodat ik geen data verlies in de overgang.
62. Als gebruiker wil ik dat **save geblokkeerd** is tijdens een lopende
    scenario-run, zodat ik geen halve resultaten persisteer.

### LTAP

63. Als planner wil ik dat **LTAP what-if** een eigen tab/sub-werkruimte
    heeft, zodat planning niet vermengt met scenario-analyse.
64. Als planner wil ik dat **`Preventief onderhoud`** in de hoofdwerkruimte
    read-only blijft, zodat de what-if-bewerking ondubbelzinnig bij LTAP
    hoort.

### Architectuur en testbaarheid

65. Als ontwikkelaar wil ik dat **PBS-scope-filtering** in een Qt-vrije
    presentatie-adapter wordt geïmplementeerd, zodat tests zonder Qt-widgets
    de scope-regels valideren.
66. Als ontwikkelaar wil ik dat **scenario-slot-state** een Qt-vrije module
    is, zodat slotbeheer en clear-regels apart testbaar zijn.
67. Als ontwikkelaar wil ik dat **werkruimte-state** (modus, slot, scope,
    sticky-regels) Qt-vrij is, zodat UI-flow-tests klein blijven.
68. Als ontwikkelaar wil ik dat de **kern (`rcm_core`) niet wijzigt** in deze
    slice, zodat `CACHE_INPUTS_VERSION` ongewijzigd blijft.
69. Als ontwikkelaar wil ik dat **views in `rcm_desktop/views/` geen directe
    `rcm_core`-imports doen** (behalve typing-only), conform AGENTS.md.
70. Als ontwikkelaar wil ik dat **bestaande compare-pipeline (`run_compare`)
    blijft bestaan** tot fase C live is, zodat fasering veilig terugrol-baar
    is.

### Toekomst (informatief)

71. Als productowner wil ik dat deze slice de **fundering legt** voor latere
    config + `Start Analyse` (fase D), geoptimaliseerd scenario (fase E) en
    deelruns/Monte Carlo (fase F), zodat die uitbreidingen additief zijn.
72. Als productowner wil ik dat **scenario-slot-state** een derde slot kan
    dragen (`Geoptimaliseerd`) zonder herontwerp.
73. Als productowner wil ik dat **proxy-niet-beschikbaarheid** later vervangen
    kan worden door echte downtime-jaarvector zonder UI-wijziging.

## Implementation Decisions

### Architectuur

- **UI/kern-decoupling als MUST.** Alle nieuwe presentatie-, scope-, KPI- en
  state-logica zit in de **Adapter Qt**-laag. Views consumeren alleen
  Qt-vrije outputs. Geen `rcm_core`-imports in views buiten typing-only
  (conform AGENTS.md).
- **Kern blijft puur.** Geen wijziging in `rcm_core/`. Geen wijziging in
  `CACHE_INPUTS_VERSION` of cache-discipline.
- **Bestaande compare-pipeline (`scenario_run_service.run_compare`) blijft
  bestaan** tot fase C de scenario-slot-flow definitief vervangt; in fase A
  blijft hij actief om regressies te dempen.
- **Adapter Qt** krijgt twee nieuwe scenario-aanroepen: `run_cm()` en
  `run_pm()` als afzonderlijke wrappers die elk één scenario draaien via de
  bestaande materialisatie (CM-clone / PM-clone) plus
  `incremental_run.run_incremental_analysis`. `run_compare` blijft als
  legacy-pad in fase A/B; in fase C wordt het uit de UI losgekoppeld.

### Nieuwe deep modules (Qt-vrij)

- **`result_filter_service`** — Presentatie-laag op `RunResult`. Input:
  `RunResult` + optionele `pbs_scope_id`. Output: gefilterde
  `FMResultRow`-lijst, gefilterde `PBSResultRow`-lijst, scoped KPI-totalen,
  scoped boomstructuur (`PBSTreeNode`-roots). Filtering is een subtree-filter
  op de bestaande boomstructuur uit `result_view_service`. Geen
  motor-aanroep.
- **`contribution_chart_service`** — Bouwt staafdiagram-data voor
  `Bijdragen`. Parameters: bron (`PBS`/`Faalwijze`), metric
  (`niet-beschikbaarheid`/`kosten`/`downtime`/`faalmomenten`/`risico`),
  top-N, scope. Output: lijst van (categorie-label, waarde, aandeel-%).
  Categorie-volgorde stabiel; ties op alfabetische categorie-id.
- **`unavailability_chart_service`** — Bouwt niet-beschikbaarheid-jaarvector
  als proxy uit het bestaande faalmomenten-jaarprofiel uit `lcc_profile`
  (zelfde aging-/random-pad als de correctief-discretisatie). Output: tuple
  `(kalenderjaar, niet_beschikbaarheid_pct, downtime_uren)` per bucket.
  Lifecycle-totaal `downtime_uren` reconcilieert exact tegen
  `RunMetrics.total_downtime_hr` voor dezelfde scope.
- **`pm_chart_service`** — Bouwt PM-jaarvector. Modus `Kosten`: hergebruikt
  `preventief_eur` uit bestaande LCC-builders. Modus `Aantal uitvoeringen`:
  aggregeert per kalenderjaar uit `ltap_service.build_ltap_view`. PBS-scope
  filtert op PM-taken onder dat subtree.
- **`scenario_slot_state`** — Sessiegeheugen-store. Keys: `CM`, `PM` (later
  in fase E ook `OPTIMIZED`). API: `put(scenario_key, run_result,
  project_snapshot)`, `get(scenario_key)`, `clear_all()`, `last_run_key()`.
  Bij `put` vervangt bestaande slot van dezelfde key. Geen disk-persistentie.
  Project-identiteit via path + mtime; afwijkend pad → harde clear.
- **`results_workspace_state`** — Orchestrator. Houdt actieve modus, actief
  slot, PBS-scope, sub-toggle-keuzes per modus, metric-keuze voor
  `Bijdragen`, filtertekst PBS-boom. Stickiness-regels per branch:
  PBS-selectie sticky over modus-/scenario-/run-wissels; sub-toggles sticky
  per modus; metric sticky binnen `Bijdragen`. Reset-policy bij ander
  project. Initiële default: modus = `Bijdragen`, metric =
  `Niet-beschikbaarheid`, scope = `None`. Emit signaal op state-wissel zodat
  de view declaratief kan herrenderen.
- **`kpi_table_service`** — Bouwt KPI-tabel-rijen voor N scenario-slots
  gegeven `scope_id`. Rij-volgorde vast: faalmomenten,
  niet-beschikbaarheid %, kosten EUR, PM-taken actief. Lege scenario-cellen
  krijgen sentinel-waarde. Rij 4 (PM-taken actief) negeert scope.

### Nieuwe view-module

- **`results_workspace_window`** — Hoofdvenster. Hoofdsplitter horizontaal:
  links PBS-kolom-widget, rechts werkruimte. Werkruimte verticaal: KPI-tabel
  (vast), grafiek-zone (resizable splitter binnenin afhankelijk van
  modus-oriëntatie), detailtabel (resizable). Toolbar boven: project-pad,
  validate, save, save-as, faalwijzen-toggle, run-CM, run-PM, PBS-toggle,
  reset-layout, modus-keuze (segmented control), metric/sub-toggle inline
  naast modus. Geen TDD op widget-internals (conform AGENTS.md); flow-tests
  dekken kritieke pad.

### Te wijzigen

- Centrale **NL-messages** — nieuwe labels en tooltips voor modi,
  sub-toggles, KPI-rijen, scenario-kolommen, empty-states en proxy-disclaimer.
- **`scenario_run_service`** — naast `run_compare` ook `run_cm()` en
  `run_pm()` als afzonderlijke entrypoints, met gedeelde
  materialisatie-helper.
- **`pbs_results_tree_model`** — uitbreiding zodat boom **structuur** kan
  tonen vóór run (met lege/grijze cijferkolommen), bovenop bestaande
  aggregaat-cijferweergave na run. Cijferweergave volgt actief scenario-slot.
- **`main.py`** — instantieert `ResultsWorkspaceWindow` in plaats van
  `ValidateWindow`.
- **`validate_window.py`** — blijft eerst beschikbaar in fase A; in fase C
  verwijderd of als legacy-only entrypoint behouden voor regressie-onderzoek.

### Interactie-contracten

- **PBS-scope = harde filter op presentatie.** Niet op motor; geen
  motor-aanroep bij PBS-klik. Hele project = sentinel `None`.
  `Toon hele project`-knop reset scope naar `None`.
- **Modus-switch** zet alleen de actieve modus-key in
  `results_workspace_state`; sub-toggles en metric blijven sticky per modus.
- **Scenario-run** roept `run_cm()` of `run_pm()` aan; bij succes wordt slot
  gevuld via `scenario_slot_state.put`; bij mislukking blijft het bestaande
  slot ongewijzigd. Faaltekst toont in placeholder van dat slot.
- **Actief slot** voor PBS-boom-cijfers: klik op kolom-header in KPI-tabel.
  Initieel = `scenario_slot_state.last_run_key()`.
- **Validate-gate**: `run_cm` en `run_pm` zijn disabled zolang
  `AppState.last_project` ontbreekt.
- **Save-blocked-during-run**: identiek aan bestaand gedrag, ongeacht welk
  scenario draait.
- **Reset-layout**: zet panel-zichtbaarheid (PBS-kolom aan, detailtabel
  zichtbaar, KPI-tabel zichtbaar) en splittergroottes terug naar default.

### Presentatie-oriëntatie

- Modus-categorie `tijdreeks` (`LCC`, `Niet-beschikbaarheid`,
  `Preventief onderhoud`) → grafiek-zone **verticaal** gesplitst; CM boven,
  PM onder.
- Modus-categorie `categorie-bijdragen` (`Bijdragen`) → grafiek-zone
  **horizontaal** gesplitst; CM links, PM rechts.
- Modus `FM-detail` → geen splitsing in deze slice; toont één detailtabel
  actief-slot-gebonden.
- Kleur per **datatype** (correctief / preventief / aantal uitvoeringen /
  niet-beschikbaarheid) consistent tussen slots; **geen kleurcode per
  scenario-identiteit**.

### Empty states

- Vóór een run: skeletten zichtbaar; placeholder “Start eerst een analyse:
  Run CM-scenario of Run PM-scenario.”
- Na één scenario-run in scenario-modus: gesplitste weergave actief; tweede
  slot toont “Draai ook het andere scenario”.
- PBS-scope op leeg subtree: detailtabel + grafiek tonen modus-specifieke
  empty-state, KPI-cellen tonen 0 of `—` op een eenduidige manier.

## Testing Decisions

- **Goede tests** valideren extern gedrag op publieke functies en publieke
  UI-acties. Niet asserten op private widget-attributen, niet asserten op
  exacte stijling/kleur, niet asserten op interne signal-listings.
- **Adapter-first volgens AGENTS.md**: alle nieuwe deep modules krijgen
  test-eerst dekking.
- **TDD-modules**:
  - `result_filter_service`: scope-filter reconcilieert tegen unscoped
    totalen wanneer `scope_id=None`; subtree-totalen tellen exact op tot
    subtree-rootwaarden; FM-rijen onder scope = FM-rijen waarvan `pbs_id` in
    subtree-set zit.
  - `contribution_chart_service`: top-N volgorde per metric correct; ties op
    `pbs_id`/`fm_id`; PBS-bron vs faalwijze-bron geven verschillende
    categorie-sets; scope filtert deelnemers.
  - `unavailability_chart_service`: lifecycle-totaal reconcilieert exact
    (binnen 1e-3) tegen `RunMetrics.total_downtime_hr` voor zowel `aging`-
    als `random`-faaltypes; bucket-aantal gelijk aan
    `ltap_horizon_bucket_count`.
  - `pm_chart_service`: `Kosten`-modus reconcilieert tegen
    `preventief_eur`-totaal uit bestaande LCC-builders;
    `Aantal uitvoeringen`-modus aligneert per jaar met `ltap_service`-output.
  - `scenario_slot_state`: put/get/clear-semantiek; vervang-bij-zelfde-key;
    clear bij project-identiteitswissel; `last_run_key` tracking.
  - `results_workspace_state`: stickiness-regels per modus; reset bij ander
    project; PBS-scope-persistentie over modus-wissels; default-modus-keten
    bij eerste run.
  - `kpi_table_service`: rij-aggregaten kloppen met `RunMetrics` voor
    scope=None; scope-cellen kloppen met subtree-totalen; rij 4 negeert
    scope.
- **pytest-qt flow-test (één file)** op `results_workspace_window`: project
  laden → run CM → KPI-cellen gevuld voor CM-kolom → run PM → tweede kolom
  gevuld → modus `Bijdragen` → modus `LCC` → modus `Niet-beschikbaarheid` →
  PBS-knoop selecteren → KPI-cellen rij 1–3 wijzigen → `Toon hele project` →
  cellen terug naar projecttotaal → ander project laden → alles gereset.
- **Prior art** in repo:
  - LCC-reconciliatie-tests in `tests/test_desktop_lcc_chart_service.py`.
  - PBS-tree-model-tests in `tests/test_desktop_pbs_results_tree_model.py`.
  - Compare-flow in `tests/test_desktop_scenario_compare_service.py` en
    `tests/test_desktop_scenario_run_service.py`.
  - State + signal-discipline in `tests/test_desktop_qt_flow.py`.
- **Bestaande seam**: `patch op rcm_core.incremental_run as ir` blijft de
  manier om de motor te mocken in scenario-run-tests (conform AGENTS.md).
  Adapter-specifieke mocks blijven binnen `rcm_desktop.adapter.*`.
- **Wat niet getest wordt**: visuele detail-rendering, exacte
  splittergroottes, kleurpaletten, exacte aantal pixels van scroll-zones.

## Out of Scope

- **Fase D**: CM/PM als config-knoppen + aparte `Start Analyse`-knop met
  PM-niveau via PBS-scope. Aparte PRD.
- **Fase E**: `Geoptimaliseerd` scenario met handmatige IN/REV-selectie.
  Aparte PRD.
- **Fase F**: echte deelruns (sub-PBS / deelmodel), Monte Carlo-schaal,
  faalwijze-isolatie als motor-API. Raakt `rcm_core` en vraagt ADR.
- **Echte niet-beschikbaarheid-jaarvector** in de kern (slice 22-stijl
  uitbreiding voor downtime). Deze PRD levert alleen een proxy met
  disclaimer.
- **Export** (CSV/Excel/PDF) van grafiek- of tabeldata.
- **Theming / kleurpalet-finetuning** voorbij datatype-consistentie.
- **Multi-window docking** of dock-architectuur.
- **Persistent layout-preferences** voor de nieuwe werkruimte (alleen
  reset-default; volledige persistentie pas later).
- **Killer/olifant-classificatie** of vergelijkbare classificeerlogica (zie
  ADR-0003; bewust uit RCM2).
- **Wijzigingen aan validate-, save-, dirty- of faalwijzen-edit-flow.**
- **Wijziging aan compare-KPI-semantiek** van slice 21; deze PRD consumeert
  alleen bestaande velden in `RunResult`/`RunMetrics`.

## Further Notes

- **Fasering binnen deze PRD** (A → B → C) is bedoeld zodat elke fase een
  werkende kleine UI oplevert: na fase A draait de bestaande compare-pipeline
  in de nieuwe layout, na fase B werken alle modi tegen die compare-output,
  in fase C splitst de run-knop en verdwijnen de oude `Volledige analyse`-
  en `Vergelijk`-knoppen. Tussentijdse regressies blijven dempbaar.
- **Risico — drift tussen scoped en unscoped totalen.** Tests dwingen
  reconciliatie af: scope=None ≡ projecttotaal; subtree-totalen tellen op
  tot subtree-root.
- **Risico — proxy-niet-beschikbaarheid wordt mentaal verward met echte
  jaarvector.** Mitigatie: expliciete disclaimer in tooltip + titel +
  modus-uitleg-zin.
- **Risico — `scenario_run_service` splitsing.** `run_cm()` en `run_pm()`
  moeten exact dezelfde materialisatie gebruiken als `run_compare`, anders
  driften scenario-cijfers tussen UI-paden. Mitigatie: gedeelde
  materialisatie-helper achter `run_compare` en de twee nieuwe entrypoints.
- **Migratie**: `ValidateWindow` blijft in fase A actief naast de nieuwe
  werkruimte zodat reviewers de oude en nieuwe UI naast elkaar kunnen
  draaien; in fase C wordt het verwijderd of als legacy-only entrypoint
  behouden voor regressie-onderzoek.
- **Toekomst** — de structuur van `scenario_slot_state` met meerdere keys en
  `results_workspace_state` met scope/modus/metric is bewust open zodat fase
  D (config + `Start Analyse`), fase E (`Geoptimaliseerd`) en fase F
  (deelruns, Monte Carlo, faalwijze-isolatie) zonder herontwerp kunnen
  aansluiten. Bij fase F vervangt een echte deelrun-API alleen de
  input-`RunResult`, niet de presentatie-adapter.
