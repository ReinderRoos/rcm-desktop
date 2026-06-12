# Slice 28 — LCC-planning, what-if overlay en FM-detail NMF-filter

**Triage:** done  
**Type:** AFK (presentatie + planning-overlay; geen domain-model mutatie)  
**Parent:** resultatenwerkruimte (slice 23), LCC-kalenderjaar (slice 21), LTAP-bundeling (slice 11/12/14)  
**Versie:** 1.0  
**Datum:** 2026-05-19  

**Vervolg:** slice 29 (`rcm-desktop-slice29-planning-overlay-motor`) — herberekening met passief-overlay in motor, werkruimte-manipulatie UI, afbouw CM/PM-scenario als standaardpad.

## Problem Statement

Onderhoudsplanning en LCC-analyse leven nu op **twee plekken** met tegenstrijdige contracten:

- In de **resultatenwerkruimte** toont de **LCC-modus** alleen een geaggregeerde staaf (**correctief + preventief**). Er is geen filter op taaktype (REV, IN, TST, SVO, WET), geen jaarklik naar geplande taken, en geen what-if.
- De modus **Preventief onderhoud** is **read-only** (slice 23) en dupliceert deels het LTAP-inzicht zonder bewerkbaarheid.
- Volledige **LTAP what-if** (verschuiven, bundel, REV-filter) zit nog in **ValidateWindow** (legacy), los van de standaard analyseflow (`main.py` opent de werkruimte).

Daardoor kan de analist niet in één tijdas zien **wanneer welk type onderhoud** plaatsvindt, **welke taken** in een jaar gepland zijn, en **wat-if** scenario’s verkennen (verschuiven, taken passief) zonder terug te vallen op een oud scherm. **NMF** (`Faalwijze.is_evident`) is in de motor wel modelleerbaar (slice 27), maar in **FM-detail** ontbreekt een filter op evident vs niet-evident falen.

Automatisering zoals **PBS-bundeling** en **functioneel meekoppelen** stonden in RCM1-roadmap en scrub-list; ze zijn bewust niet geporteerd en horen niet impliciet in deze slice.

## Solution

Integreer **planning en manipulatie in de LCC-modus** van de resultatenwerkruimte:

1. **Leeslaag:** multi-select **laag-toggles** op de LCC-tijdas — **CM** = correctief (faalgebonden) segment; **REV / IN / TST / SVO / WET** = PM-types in het preventief-deel; default alles aan. **Jaarklik** opent een **detailtabel** met geplande PM-taken (LTAP-achtig), gefilterd op actieve types; bij alleen CM een jaarregel correctief zonder PM-rijen.
2. **What-if-laag:** expliciete modus **What-if planning** (standaard read-only). Overlay met `anchor_years` (verschuiven, hergebruik bundel-engine) en `disabled_pm_ids` (passief). Indicator, **Reset naar baseline**. Bulkactie **Alle REV passief**. Geen mutatie van project-JSON; `last_run` blijft baseline tot expliciete herberekening (latere slice).
3. **FM-detail:** drietrapfilter **Alle | Alleen NMF | Alleen evident** op `is_evident`, in de adapter.
4. **Eén LCC-grafiek** op `last_run` (slice 26-lijn); modus **Preventief onderhoud** uitfaseren (verwijderen of doorverwijzen naar LCC). Legacy ValidateWindow-LTAP deprecaten op termijn.
5. **Verificatie:** golden fixture `one_fm_planning.rcm.json` + adapter/kern-pytest; optioneel één pytest-qt smoke (what-if → shift → reset).

Gefaseerde levering binnen deze PRD (tracer-bullet):

- **Fase A — LCC leescontract:** type-filters, staafsegmenten of gefilterde som, jaarklik → takenlijst, jaarsamenvatting, PBS-scope.
- **Fase B — What-if:** overlay-state, shift/passief, bulk REV passief, presentatie baseline vs what-if.
- **Fase C — FM-detail NMF-filter** (kan parallel met A als adapter-only).

## User Stories

### Mentale eenheid: LCC als planningstijdas

1. Als onderhoudsingenieur wil ik **één tijdas** in de resultatenwerkruimte voor zowel kosten als geplande taken, zodat ik niet tussen LCC en een apart LTAP-paneel hoef te wisselen.
2. Als analist wil ik dat de **LCC-modus** de primaire plek is voor REV/PM-inzicht, zodat mijn workflow aansluit bij `Herbereken analyse` als standaardpad.
3. Als productowner wil ik de modus **Preventief onderhoud** opheffen of laten doorverwijzen naar LCC, zodat er geen dubbele read-only PM-weergave meer is.
4. Als gebruiker wil ik dat **ValidateWindow-LTAP** op termijn vervangen wordt door de werkruimte-LCC-flow, zodat onderhoud één productpad heeft.
5. Als trainer wil ik in documentatie lezen dat **planning what-if** een overlay is op de laatste analyse, niet op het opgeslagen projectbestand.

### LCC — taaktype-filters (laag-toggles)

6. Als onderhoudsingenieur wil ik **REV, IN, TST, SVO, WET en CM** als filters op de LCC-grafiek, zodat ik per type kan focussen wanneer wat gebeurt.
7. Als analist wil ik **meerdere PM-types tegelijk** kunnen aanzetten (multi-select), zodat ik bijvoorbeeld REV+IN combineer zonder alles te zien.
8. Als analist wil ik dat **CM** het **correctief (faalgebonden)** segment toont/verbergt, zodat ik het niet verwar met het **CM-scenario** (beleidsvariant).
9. Als gebruiker wil ik dat **alle filters default aan** staan, zodat de eerste indruk gelijk is aan de huidige totaal-LCC.
10. Als analist wil ik dat **REV … WET** alleen het **preventief-deel** beïnvloeden, zodat correctief semantisch los blijft van PM-taaktypen.
11. Als assetmanager wil ik bij uitschakelen van alle PM-types nog **correctief** kunnen tonen, zodat ik puur faalgebonden jaarlast zie.
12. Als gebruiker wil ik dat filterkeuze **sticky** blijft tijdens sessie (moduswissel binnen werkruimte), zodat ik niet telkens opnieuw moet instellen.
13. Als analist wil ik dat de **legenda** de actieve taaktypes toont, zodat ik de staaf kan decoderen zonder tooltip alleen.
14. Als gebruiker wil ik **tooltips** die uitleggen dat bedragen **verwacht en nominaal** zijn, zodat financiële interpretatie correct blijft (slice 21).
15. Als ontwikkelaar wil ik dat filterlogica in de **adapter** zit, zodat views geen `rcm_core` importeren.

### LCC — staaf en reconciliatie

16. Als analist wil ik per kalenderjaar een **gestapelde staaf** met zichtbare segmenten per actief type (of één preventief-blok gefilterd op types), zodat pieken per taaksoort zichtbaar zijn.
17. Als analist wil ik dat de **som van jaarbedragen** per component (correctief / preventief per type) reconcileert met de onderliggende LTAP- en motor-totalen binnen afgesproken tolerantie, zodat filters geen stille drift introduceren.
18. Als analist wil ik dat **preventief per type** uit dezelfde **LTAP-view** komt als planning-detail, zodat grafiek en tabel één waarheid delen.
19. Als gebruiker wil ik bij **lange horizons** horizontaal kunnen scrollen, zodat jaarlabels leesbaar blijven.
20. Als gebruiker zonder QtCharts wil ik een **tabel-fallback** met dezelfde gefilterde cijfers, zodat analyse door kan gaan.

### LCC — jaarselectie en detailtabel

21. Als onderhoudsingenieur wil ik op een **kalenderjaar-staaf kunnen klikken**, zodat ik direct de taken van dat jaar zie.
22. Als gebruiker wil ik in de detailtabel **PM-id/label, taaktype, faalwijze, PBS, uitvoeringen, kosten en downtime** zien, zodat ik uitvoerbaarheid kan beoordelen.
23. Als gebruiker wil ik dat de detailtabel **alleen taaktypes toont die in de filter aan staan**, zodat tabel en grafiek consistent zijn.
24. Als gebruiker wil ik bij **alleen CM-filter aan** een **samenvattingsregel correctief** voor dat jaar zien en **geen PM-rijen**, zodat het gedrag voorspelbaar is.
25. Als gebruiker wil ik boven de detailtabel een **jaarsamenvatting** (baseline / what-if / delta wanneer overlay actief), zodat ik niet hoef te rekenen.
26. Als gebruiker wil ik **Toon alle jaren** om het jaarfilter op te heffen, zodat ik snel terug ben naar totaaloverzicht.
27. Als gebruiker wil ik bij een jaar **zonder taken** een expliciete empty-state, zodat ik weet dat de selectie gelukt is.
28. Als gebruiker wil ik dat **SVO/WET** in detail herkenbaar en **niet verschuifbaar** blijven (bestaande LTAP-regels), zodat governance-taken beschermd zijn.
29. Als gebruiker wil ik dat **jaarselectie sticky** blijft na filterwijziging zolang het jaar geldig is, zodat ik in context blijf werken.
30. Als analist wil ik dat **PBS-scope** (subtree-selectie links) ook LCC-filters, staaf en jaardetail beïnvloedt, zodat focus op een deel van het systeem consistent is.

### What-if planning — modus en overlay

31. Als analist wil ik standaard **alleen lezen** kunnen in LCC (filters + jaardetail), zodat ik niet per ongeluk de planning wijzig.
32. Als analist wil ik met **What-if planning** een overlay kunnen activeren, zodat verschuiven en passief maken expliciet is.
33. Als gebruiker wil ik een zichtbare indicator **What-if actief** met telling van wijzigingen, zodat ik nooit baseline en overlay verwar.
34. Als gebruiker wil ik **Reset naar baseline** die overlay en passief-status wist, zodat ik snel opnieuw kan beginnen.
35. Als gebruiker wil ik dat **Herbereken analyse** de overlay **niet stilletjes** in het project wegschrijft, zodat opgeslagen JSON de edit-buffer blijft.
36. Als productowner wil ik begrijpen dat **impact op correctief** in `last_run` pas zichtbaar wordt na een **latere expliciete herberekening met overlay** (buiten deze slice), zodat verwachtingen kloppen.

### What-if — verschuiven (shift)

37. Als onderhoudsingenieur wil ik geselecteerde **verschuifbare** PM-taken in what-if-modus kunnen **bundelverschuiven** (integer jaren), zodat ik uitstel/groepering kan simuleren.
38. Als gebruiker wil ik verschuiven vanuit de **jaardetailtabel-selectie**, zodat ik niet naar ValidateWindow hoef.
39. Als gebruiker wil ik dat **SVO/WET** een bundelactie **blokkeren** (all-or-nothing), zodat er geen stille partial updates zijn.
40. Als gebruiker wil ik een **duidelijke foutmelding** met PM-id’s bij blokkade, zodat ik gericht kan corrigeren.
41. Als gebruiker wil ik dat **overlay_anchor_years** de geplande ankerjaren overschrijft in LTAP/LCC-presentatie, zodat de tijdas de what-if toont.
42. Als tester wil ik shift-gedrag testen via de **publieke bundel-API** (overlay in, shift, reset), zodat tests refactorbestendig zijn.

### What-if — passief (disabled)

43. Als onderhoudsingenieur wil ik een taak **passief** kunnen maken (niet uitvoeren in what-if), zodat ik kan verkennen wat er gebeurt als REV uitblijft.
44. Als analist wil ik dat passieve taken **niet meetellen** in what-if preventief/LTAP-presentatie, zodat de staaf daalt zonder JSON te wijzigen.
45. Als gebruiker wil ik passief per taak kunnen **terugzetten** in what-if-modus, zodat ik iteratief kan vergelijken.
46. Als onderhoudsingenieur wil ik de bulkactie **Alle REV passief**, zodat ik snel een scenario zonder revisie kan tonen.
47. Als analist wil ik dat bulk passief alleen **REV**-taken raakt, zodat IN/TST/SVO/WET gedrag bewust blijft.
48. Als domein-expert wil ik dat passief **geen** nieuw `enabled`-veld op `PMTask` vereist in deze slice, zodat schema-parity en migratie uitblijven.

### What-if — presentatie baseline vs overlay

49. Als gebruiker wil ik in what-if de **grafiek en/of jaarsamenvatting** baseline en what-if kunnen vergelijken (Δ), zodat bundeleffect zichtbaar is (slice 12-gedrag, nu in LCC-context).
50. Als gebruiker wil ik dat **jaarselectie** behouden blijft na shift zolang het jaar in range is, zodat itereren snel gaat.
51. Als gebruiker wil ik dat **reset** ook de jaarselectie naar totaaloverzicht kan herstellen conform bestaande LTAP-policy, zodat UI consistent blijft.

### FM-detail — NMF-filter

52. Als analist wil ik in **FM-detail** filteren op **Alle | Alleen NMF | Alleen evident**, zodat ik niet-evidente faalwijzen kan isoleren.
53. Als analist wil ik default **Alle** zien, zodat het scherm niet verrast bij openen.
54. Als gebruiker wil ik dat het filter **sticky** is per sessie, zodat mijn focus behouden blijft.
55. Als ontwikkelaar wil ik het filter in de **adapter** (niet in de view), zodat pytest zonder Qt kan valideren.
56. Als analist wil ik optioneel later een kolom **Evident/NMF** in de tabel, zodat herkenning zonder filter ook kan (niet verplicht in deze slice).
57. Als analist wil ik dat gefilterde FM-rijen **reconciliëren** met scope-filter (PBS), zodat FM-detail en sidebar consistent zijn.

### Architectuur en onderhoud

58. Als ontwikkelaar wil ik **views** zonder directe `rcm_core`-imports (typing-only), conform AGENTS.md.
59. Als ontwikkelaar wil ik **LTAP-bouwlogica** hergebruiken (`build_ltap_view`, bundel-engine), zodat domeinregels niet dubbel ontstaan.
60. Als ontwikkelaar wil ik een **Qt-vrije planning-overlay state** met duidelijke transities, zodat what-if testbaar is zonder UI.
61. Als ontwikkelaar wil ik **LCC-chart input** uitbreiden met optionele **per-type preventief buckets**, zodat slice 21’s latere sub-split voorbereid blijft zonder contractbreuk.
62. Als productowner wil ik **minimale diff** op slice-26 single-run renderpad, zodat presentatie-cache niet onnodig wordt gebroken.

### Testen en golden fixture

63. Als tester wil ik fixture **`one_fm_planning.rcm.json`** met minimaal één aging-FM, 1–2 REV, optioneel één NMF+IN/TST, zodat planning en filters deterministisch zijn.
64. Als tester wil ik **validate → run → LCC buckets → jaardetail → overlay shift/passief → NMF-filter** in pytest te kunnen afdekken, zodat regressies vroeg vallen.
65. Als tester wil ik **geen pixel-asserties** als merge-gate, zodat CI stabiel blijft.
66. Als tester wil ik optioneel **één pytest-qt smoke** (what-if aan → shift → reset), zodat wiring in de werkruimte niet rot.
67. Als analist wil ik in fixture-documentatie lezen **welke verwachtingen** golden zijn (jaar, totaal, aantal taken), zodat “geschikt maken” van één FM reproduceerbaar is.

### Toegankelijkheid en fouten

68. Als gebruiker wil ik **duidelijke lege states** als er nog geen `last_run` is, zodat ik weet dat ik moet herberekenen.
69. Als gebruiker wil ik dat what-if acties **uitgeschakeld** zijn zonder actieve overlay, zodat read-only echt read-only voelt.
70. Als gebruiker wil ik **Nederlandse foutteksten** via message constants, zodat copy consistent blijft.

## Implementation Decisions

### Scope en architectuur

- **Eén scherm:** resultatenwerkruimte **LCC-modus** is SSOT voor lezen + what-if; **Preventief onderhoud**-modus wordt verwijderd of redirect naar LCC met passende filters.
- **Geen tweede figuur:** geen apart LTAP-paneel naast LCC; LTAP blijft **adapter-concept** achter LCC UI.
- **Single-run presentatie:** eerste levering gebruikt **één LCC-grafiek** op `last_run` (slice 26). CM|PM-split UI blijft in codebase maar **niet** geactiveerd in deze slice.
- **Scenario-split later:** wanneer CM|PM-split terugkomt, geldt **gedeelde filterbalk** en **paneel-gekoppelde jaarklik** (besluit uit grill-me; implementatie in vervolg-PRD).

### Deep modules (testbare interfaces)

| Module | Verantwoordelijkheid | Testeer |
|--------|---------------------|---------|
| **LCC type-filter + bucket builder** | Bouwt gefilterde jaarreeksen: correctief + preventief per `TaskType` (REV…WET); past multi-select toggles toe; reconcilieert met lifecycle-totalen | Ja — kern/adapter unit |
| **Planning overlay state** | Immutable state: `active`, `anchor_years`, `disabled_pm_ids`; transities: activate, reset, shift, set_passive, bulk_rev_passive | Ja — pure unit |
| **LCC planning view builder** | Composeert LTAP-view + overlay + typefilters + PBS-scope → chart input + jaardetail rijen | Ja — adapter |
| **Year detail contract** | Rijen voor geselecteerd kalenderjaar; empty-state; CM-only samenvatting | Ja — adapter |
| **FM evident filter** | `EvidentFilter = Literal["all","nmf_only","evident_only"]` op `FMResultRow`-lijst | Ja — adapter |
| **What-if shift bridge** | Dunne wrapper boven bestaande bundel-engine (`apply_bundle_shift`, `reset_overlay`) met overlay + disabled set | Ja — adapter (bestaand patroon slice 11) |

Views blijven **dun**: toggles, modusknoppen, chart-klik → roepen adapter aan.

### Filtersemantiek LCC

- **CM-toggle:** toont/verbergt **correctief_eur** (faalgebonden), **niet** CM-scenario-run.
- **REV…WET:** filteren **preventief** naar taken met overeenkomstig `TaskType`; meerdere tegelijk = som/segmenten van geselecteerde types.
- **Default:** alle toggles **aan**.
- **Staaf:** voorkeur **gestapelde segmenten** per actief type; minimale v1 mag één preventief-blok tonen dat gefilterd is op geselecteerde types — mits reconcileerbaar en uitbreidbaar naar sub-segmenten (slice 21 voorbereiding).

### Jaardetail

- Bron: **LTAP-view** op actueel project + overlay; gefilterd op kalenderjaar en actieve type-toggles.
- **CM-only:** één regel jaar-totaal correctief; geen PM-takenrijen.
- **Geen per-FM correctief-uitsplitsing** in planningstabel (blijft FM-detail/NMF).

### What-if overlay (prototype contract)

```python
@dataclass(frozen=True)
class PlanningOverlayState:
    active: bool
    anchor_years: dict[str, float]   # pm_id -> kalenderjaar anker
    disabled_pm_ids: frozenset[str]

# Transities (adapter, Qt-vrij):
# - begin_what_if() -> active=True, lege maps/sets
# - reset_overlay() -> active=False, leeg
# - apply_shift(pm_ids, delta_years) -> via bundel-engine + anchor_years
# - set_passive(pm_id, passive: bool) -> disabled_pm_ids
# - bulk_all_rev_passive(project) -> alle REV pm_id in disabled_pm_ids
```

- **Geen** persistente wijziging aan `RCMProject` / JSON.
- **`last_run`** blijft baseline; what-if beïnvloedt **presentatie** (LTAP/LCC buckets uit overlay-view).
- **Herberekening met overlay** (motor ziet gewijzigde PM-set): **buiten scope** deze slice — zie vervolg-epic Planning-herberekening.

### PBS-scope

- Filters, LCC-buckets en jaardetail respecteren **actieve PBS-subtree** (zelfde presentatie-filter als andere werkruimte-modi).
- Onbekende scope → lege planning/LCC conform bestaand `filter_run_result`-gedrag.

### FM-detail NMF

- Filter op `Faalwijze.is_evident` via `fm_id` lookup in project bij het bouwen/filteren van `FMResultRow`.
- Drietrap: **Alle | Alleen NMF (`not is_evident`) | Alleen evident**.
- Implementatie in adapter-laag (uitbreiding `result_filter_service` of parallelle `filter_fm_rows_by_evident`).

### Deprecatie

- **Preventief onderhoud**-modus: verwijderen uit modus-switch of redirect met user message.
- **ValidateWindow LTAP:** geen nieuwe features; pariteit what-if in werkruimte; legacy kan tijdelijk blijven tot expliciete verwijder-ADR.

### Afhankelijkheden

- **Slice 27 (NMF motor):** FM-detail NMF-filter is UI; volledige NMF-correctheid in jaarcijfers vereist slice 27 in motor — geen harde merge-blocker voor overlay UI, wel voor NMF-asserties in fixture.
- **Slice 21:** terminologie **Correctief/Preventief** en kalenderjaar blijven; type-split is **filter** i.p.v. aparte chart-modus.

## Testing Decisions

### Wat is een goede test

- Test **observeerbaar gedrag** en **contracten** (bucket-sommen, aantal taken per jaar, overlay na reset leeg, filter reduceert rijen), niet private methoden of chart-internals.
- **Geen** screenshot/pixel-tests als merge-gate.
- Fixtures **klein en stabiel**; golden `one_fm_planning.rcm.json` met gedocumenteerde verwachtingen.

### Te testen modules

| Module | Testtype | Prior art |
|--------|----------|-----------|
| Planning overlay state | Unit (pure transities) | `ltap_bundle_service` tests |
| LCC type-filter + buckets | Adapter/kern unit + reconciliatie | `test_lcc_*`, slice 21 tests |
| LCC planning view builder | Adapter integration | LTAP service tests, slice 12 |
| Year detail | Adapter | ValidateWindow LTAP jaarfilter tests |
| FM evident filter | Adapter unit | `result_filter_service` / FM table tests |
| Werkruimte wiring | Optioneel 1× pytest-qt smoke | `test_desktop_results_workspace_window.py` |

### Golden fixture

- **`tests/fixtures/one_fm_planning.rcm.json`:** 1 aging-FM, 1–2 REV-taken, optioneel 1 NMF-FM met IN/TST; kleine horizon; voorspelbare jaarkosten.
- Documentatie: korte README of issue-acceptatie met verwachte totalen/jaar met taken.

### pytest-qt

- **Optioneel:** één smoke — open werkruimte, load fixture, LCC-modus, what-if aan, shift, reset — niet verplicht voor slice-afsluiting.

## Out of Scope

### Expliciet niet in slice 28

- **CM | PM scenario-split** opnieuw activeren (twee grafieken); gedeelde filters al wel **ontworpen** voor vervolg.
- **Herbereken analyse met what-if overlay** (motor-run op tijdelijke PM-set) — epic Planning-herberekening.
- **Persistent `enabled` op `PMTask`** + schema/parity/migratie.
- **PBS-bundeling REV (3b):** per element schuiven naar laatste/eerste REV-moment — **eigen PRD Planning-2b**.
- **Functioneel meekoppelen (3c):** NB-gedreven mee-verplaatsen — **eigen PRD Planning-2c**; scrub-list `meekoppelkansen` vereist ADR vóór port.
- **Automatische bundel-suggesties** uit RCM1 `ltap_light` / `meekoppelkansen_v1`.
- **Per-FM correctieve uitsplitsing** in LCC-jaardetailtabel.
- **Export** (Excel/PDF) van planning.
- **Monte Carlo** en **faalwijze-isolatie** als product-API (slice 23-F).
- **Domain model wijzigingen** zonder expliciet besluit (`models.py` / `schemas.py` parity).
- **ValidateWindow** volledig verwijderen (alleen geen nieuwe LTAP-features daar).

### Vervolg-epics (vastgelegd, niet bouwen)

| Epic | Inhoud |
|------|--------|
| **Planning-2b** | PBS-bundeling REV: alle taken onder element naar **laatste** of **eerste** geplande REV-anker; bulk `anchor_years`; conflict SVO/WET |
| **Planning-2c** | Functioneel meekoppelen o.b.v. functie-NB en FM-koppeling; voorstel vs auto-apply; ADR t.o.v. scrub-list |
| **Scenario A/B** | `Run CM` / `Run PM` + split render + gedeelde filterbalk |
| **Planning-herberekening** | Expliciete actie overlay → run → bijgewerkte correctief in presentatie |

## Further Notes

### Relatie grill-me en eerdere slices

- Dit PRD **supersedes** voor de werkruimte het slice-23-scheiding **read-only Preventief vs apart LTAP-tab** voor nieuwe ontwikkeling.
- Slice **12/14** gedrag (jaarklik, REV-filter, selectie-bundel) wordt **hergebruikt**, niet opnieuw uitgevonden.
- Gebruiker zag **één LCC-grafiek**: conform slice **26** (bewust), geen regressie-bug.

### Risico’s

- **What-if zonder herberekening:** gebruikers kunnen denken dat correctief in `last_run` al stijgt bij REV passief — copy en indicator moeten **presentatie vs motor** scheiden.
- **PBS-scope op LCC:** als deels ontbreekt in huidige PM-modus, moet slice 28 scope **end-to-end** trekken.
- **Performance:** extra LTAP-bouwen per filter/jaar — hergebruik presentatie-cache waar slice 26 dat al doet.

### Issue-tracker

Issues **01–0N** kunnen uit deze PRD worden gesneden via `/to-issues` (fase A/B/C als verticale slices).
