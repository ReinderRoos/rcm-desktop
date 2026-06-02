# PRD — RCM2 desktop slice 55 (meekoppel discovery parent-rollup)

**Status:** ready-for-agent  
**Versie:** 1.0  
**Triage-labels:** ready-for-agent  
**Type:** Productsemantiek discovery (Planning-2b amendement); adapter + paneel-scope; geen motor-run  
**Parent:** slice 40 (PBS-locatiebundeling); ADR-0005; grill-me parent-rollup (2026-06-02)  
**Blokkeert:** slice 54 issues 03+ (checkbox-preview bouwt op gevulde locatietabel)  
**Datum:** 2026-06-02  
**Referentie-fixture:** `tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json`

## Problem Statement

In de resultatenwerkruimte (LCC + what-if) tonen meekoppelkansen locatiegroepen die REV-taken bundelen op het **leaf-PBS-niveau** van de gekoppelde faalwijze (`fm.pbs_id`). Bij diepe Isograph-bomen staan veel REV-taken op **sibling-leaves** onder dezelfde parent; per leaf zijn er dan vaak minder dan twee taken of een te grote due-span binnen het tijdsvenster.

Gevolg voor analisten:

- De **selectiesamenvatting** toont wel REV-taken onder een PBS-selectie, maar de tabel **Meekoppelkansen** blijft leeg of zeer mager (“Geen locatiegroepen voor het gekozen tijdsvenster”).
- Bundelen op leaf-niveau is **te smal** voor het mentale model “onderhoud op dit onderdeel / deze locatie in de boom”.
- Analisten willen **meer voorstellen** zien en irrelevante voorstellen later **handmatig** uitsluiten (o.a. via de geplande checkbox-preview in slice 54).

Dit is geen regressiebug maar een **bewuste verfijning** van slice-40-semantiek: discovery één trede hoger in de PBS-hiërarchie.

## Solution

Verhoog het **discovery-bundelniveau** exact **één parent** ten opzichte van de FM-knoop:

- **Bundelsleutel:** `parent_pbs_id(fm.pbs_id)` indien die parent in het domain model bestaat; anders `fm.pbs_id` (fallback leaf).
- **Locatiegroep** in de suggestietabel: `pbs_id` en boompad op **parent**; taken in de groep behouden **leaf**-traceerbaarheid per REV.
- **Groepsregels ongewijzigd** op de samengevoegde parent-groep: ≥ 2 REV en `max(due) − min(due) ≤ tijdsvenster` (default 2 jaar).
- **PBS-selectiefilter:** toon een parent-rij als **minstens één leaf** van een groeps-REV onder de geselecteerde PBS-subboom valt (leaf-dekking), niet alleen als de parent zelf geselecteerd is.
- **Locatierij-acties** (preview/apply op één rij) gebruiken de **zelfde parent-groep** als discovery.
- **PBS-multi-select** preview/apply blijft een **platte** lijst van alle REV onder de selectie (geen automatische opsplitsing in meerdere parent-bundels).
- **Geen feature-flag** — dit wordt direct de nieuwe standaard; ADR-0005 wordt geamendeerd.

Uitrol vóór slice 54 issues 03+ zodat checkbox-preview en workflow op een realistische locatietabel bouwen.

## User Stories

### Bundelniveau en discovery

1. Als **onderhoudsingenieur** wil ik meekoppelkansen groeperen op het **parent-PBS-niveau** van de FM-knoop, zodat sibling-REV’s op verschillende leaves één bundelvoorstel vormen.
2. Als **analist** wil ik dat bundelen **exact één trede hoger** gaat (niet configureerbaar in deze slice), zodat gedrag voorspelbaar blijft.
3. Als **analist** wil ik dat REV-taken zonder geldige parent **op leaf-niveau** blijven groeperen, zodat root- en import-gap-knooppunten geen taken verliezen.
4. Als **analist** wil ik dat ontbrekende of orphan `parent_pbs_id` **per taak** terugvalt naar leaf, zodat Haarlem-import geen REV’s verbergt.
5. Als **analist** wil ik dat alleen **REV-taken** met `interval_jaar > 0` en geldige FM/PBS in discovery komen, zodat bestaande datakwaliteitsregels gelden.
6. Als **analist** wil ik due-jaar = `round(interval_jaar)` ongewijzigd, zodat LCC- en overlay-semantiek consistent blijven.
7. Als **analist** wil ik dat een locatiegroep alleen verschijnt bij **≥ 2 REV** op dezelfde bundelsleutel, zodat enkelvoudige locaties geen ruis geven.
8. Als **analist** wil ik dat **max(due) − min(due) ≤ N** op de **hele parent-groep** geldt (default N = 2), zodat “meekoppelkans” nabije momenten blijft betekenen.
9. Als **analist** wil ik het tijdsvenster **N instelbaar** (1–5) via bestaande spinbox, zodat ik bredere kansen kan zien zonder semantiek te wijzigen.
10. Als **maintainer** wil ik discovery als **pure adapter-logica** (geen Qt), zodat gedrag pytestbaar blijft.

### Presentatie en traceerbaarheid

11. Als **analist** wil ik in de tabel het **boompad van de parent-bundelsleutel** zien, zodat ik de locatie herken in de navigatieboom.
12. Als **analist** wil ik dat `MeekoppelLocationGroup` de **parent** als groeps-`pbs_id` draagt, zodat rij-selectie en labels consistent zijn.
13. Als **analist** wil ik dat elke `MeekoppelRevTask` de **leaf** `pbs_id` behoudt, zodat preview, audit en FM-notities aan de echte FM-locatie gekoppeld blijven.
14. Als **analist** wil ik in tooltips/preview nog steeds **per-taak leaf-context** kunnen herkennen, zodat brede parent-groepen uitlegbaar blijven.
15. Als **trainer** wil ik in documentatie dat discovery nu op **parent van FM-knoop** groepeert (niet op `element_naam`), zodat ADR en UI hetzelfde verhaal vertellen.

### PBS-selectie en tabelscope

16. Als **analist** wil ik bij multi-select op **onderliggende PBS-knooppunten** parent-rijen zien zodra een groeps-REV op een leaf onder die selectie valt, zodat de tabel aansluit bij de selectiesamenvatting.
17. Als **analist** wil ik **geen** parent-rij zien als geen enkele groeps-REV onder mijn PBS-selectie valt, zodat filtering relevant blijft.
18. Als **analist** wil ik dat filter op **enkele scope-knoop** (subboom) dezelfde leaf-dekking-logica gebruikt, zodat gedrag gelijk is aan multi-select.
19. Als **analist** wil ik een duidelijke **empty-state** als er wel REV onder selectie zijn maar geen groepen binnen N, zodat ik venster of selectie kan aanpassen.
20. Als **analist** wil ik dat de **selectiesamenvatting** (platte REV-telling) **ongewijzigd** blijft, zodat ik onderscheid tussen “alle taken onder selectie” en “bundelbare kansen” begrijp.

### Locatierij vs PBS-multi-select

21. Als **onderhoudsingenieur** wil ik op een **locatierij** preview/apply op de **volledige parent-groep**, zodat één actie alle sibling-REV’s op die bundelsleutel meeneemt.
22. Als **onderhoudsingenieur** wil ik bij **PBS-multi-select** nog steeds **alle REV onder selectie** in één platte preview kunnen uitlijnen, zodat mijn brede selectie-flow behouden blijft.
23. Als **product owner** wil ik dat slice 54 **geen** automatische opsplitsing in meerdere parent-bundels in één PBS-preview introduceert, zodat scope van 55 en 54 gescheiden blijft.
24. Als **analist** wil ik irrelevante voorstellen in de tabel kunnen **negeren** en later via slice 54 **uitvinken**, zodat bredere discovery geen verplichte bundel wordt.

### Architectuur en uitrol

25. Als **ontwikkelaar** wil ik een centrale **`bundling_pbs_id`**-helper, zodat discovery en scope-filter dezelfde sleutel gebruiken.
26. Als **ontwikkelaar** wil ik **geen feature-flag** voor rollup, zodat de testmatrix en productiegedrag eenduidig blijven.
27. Als **product owner** wil ik slice 55 **vóór** slice 54 issues 03+ afronden, zodat checkbox-preview op realistische data test.
28. Als **maintainer** wil ik ADR-0005 geamendeerd, zodat architectuurdrift tussen code en besluiten verdwijnt.

### Acceptatie en kwaliteit

29. Als **QA** wil ik unit-tests op synthetische bomen (sibling-leaves → één groep), zodat regressie van leaf-groepering wordt voorkomen.
30. Als **QA** wil ik tests op **fallback zonder parent** en **orphan parent**, zodat import-edge cases gedekt zijn.
31. Als **QA** wil ik tests op **leaf-dekking** in scope-filter, zodat multi-select niet opnieuw een lege tabel geeft.
32. Als **analist** wil ik een **Haarlem-handcheck** met vaste stappen, zodat de oorspronkelijke pijn (samenvatting vs lege tabel) productie-bewijsbaar is.
33. Als **trainer** wil ik bekende risico’s (brede parent-groep, grote span) in handoff, zodat verwachtingen over venster 2 jaar helder zijn.

## Implementation Decisions

### Traject en grenzen

- Eigen slice **55**; niet opnemen in slice 54 workflow-seam scope freeze.
- **Geen** feature-flag; vervangt leaf-groepering in discovery direct.
- **Geen** wijziging aan motor, `.rcm.json`-persist, of `PlanningOverlayState`-schema buiten bestaande apply-paden.

### Diepe modules (interfaces)

- **`bundling_pbs_id(project, fm_pbs_id) -> str`**  
  Encapsuleert: lees `PBSItem` voor `fm_pbs_id`; als `parent_pbs_id` bestaat én in `project.pbs_items` → return parent; anders return `fm_pbs_id`. Pure functie, Qt-vrij, hergebruik in discovery én paneel-scope.

- **`meekoppelkansen_discovery_service` (uitbreiden)**  
  `_collect_rev_by_pbs` bucket op `bundling_pbs_id` i.p.v. raw `fm.pbs_id`.  
  `MeekoppelRevTask.pbs_id` blijft **leaf** (`fm.pbs_id`).  
  `MeekoppelLocationGroup.pbs_id` en `path_label` op **bundelsleutel** (parent).  
  `discover_meekoppel_locations` blijft extern contract; groepsregels ≥2 en span ≤ venster ongewijzigd.

- **`meekoppel_panel_service` (scope-filter)**  
  `_filter_groups_by_scope`: rij behouden als `any(task.pbs_id in covered for task in row.tasks)` (leaf-dekking).  
  Subtree-filter op `scope_id`: zelfde leaf-dekking i.p.v. alleen `row.pbs_id in subtree` wanneer parent buiten subtree ligt.  
  `preview_meekoppel` / `apply_meekoppel` via PBS-multi-select: **ongewijzigd** plat (`collect_rev_tasks_for_pbs_selection`).  
  Locatierij-pad (`preview_meekoppel_location` / `apply_meekoppel_location`): gebruikt al `group.tasks` van discovery — geen aparte leaf-bucket.

- **`pbs_path_label_service`**  
  Geen contractwijziging; `path_label` op parent-`pbs_id` voor groepslabel.

- **ADR-0005**  
  Amendement sectie Discovery (2b): groepering op **parent van FM-knoop (één niveau)** met leaf-fallback; expliciet geen `element_naam`; `MeekoppelRevTask` traceert leaf.

### Datacontract (stabiel)

```text
MeekoppelRevTask:
  pm_id, pbs_id (leaf = fm.pbs_id), due_jaar

MeekoppelLocationGroup:
  pbs_id (bundelsleutel = parent of leaf-fallback)
  path_label (pad naar bundelsleutel)
  tasks: tuple[MeekoppelRevTask, ...]
  min_due_jaar, max_due_jaar, span_jaar
```

### UX-copy (optioneel in deze slice)

- Verduidelijk empty-state wanneer selectiesamenvatting > 0 maar tabel leeg: onderscheid “geen REV onder selectie” vs “geen groep binnen tijdsvenster”.
- Geen wijziging aan spinbox-bereik of anker-gedrag.

### Architectuurregels

- UI → adapter → kern; views geen `rcm_core` behalve typing-only.
- Geen nieuwe overlay-mutatiepaden; apply blijft via bestaande `apply_meekoppel_rev_tasks` / overlay-shift.

## Testing Decisions

Goede tests valiceren **observeerbaar gedrag** via publieke adapter-API’s, niet interne bucket-implementatie.

### Testprincipes

- Assert op groeps-`pbs_id`, taak-count, span en aanwezigheid/afwezigheid van groepen.
- Gebruik minimale `RCMProject`-fixtures met expliciete parent/child PBS en meerdere FM’s op sibling-leaves.
- Regressie: twee leaves metzelfde `element_naam` blijven **niet** samensmelten via `element_naam` (alleen via shared parent bucket).

### Modules onder test

- `bundling_pbs_id` (via discovery-tests of dedicated tests).
- `discover_meekoppel_locations` en `collect_rev_tasks_for_pbs_selection` (laatste ongewijzigd gedrag bevestigen).
- `meekoppel_panel_service._filter_groups_by_scope` gedrag via `sync_meekoppel_panel` / bestaande panel-tests.

### Verplichte scenario’s

1. Twee REV op sibling-leaves metzelfde parent, due binnen venster → **één** groep met parent-`pbs_id` en twee taken met verschillende leaf-`pbs_id`.
2. Twee REV op verschillende parents → twee groepen.
3. Parent ontbreekt in `pbs_items` → fallback leaf-groep (gedrag als voorheen op die knoop).
4. PBS-multi-select op child: parent-groep **zichtbaar** via leaf-dekking.
5. Span op parent-groep > venster → **geen** groep (regel A uit grill).

### Prior art

- `tests/test_meekoppelkansen_discovery_service.py`
- `tests/test_meekoppel_panel_service.py`
- `tests/test_desktop_meekoppel_workspace.py`

### Menselijke gate

- **Haarlem-handcheck** checklist in `KANBAN_HANDOFF.md` (niet verplicht geautomatiseerd): LCC + what-if, realistische PBS-selectie, verwachting **meer** locatierijen dan pre-rollup bij venster 2; noteer edge cases (orphan parent, zeer brede parent).

## Out of Scope

- Configureerbaar bundelniveau (leaf / parent / selectie-root).
- PBS-multi-select preview automatisch splitsen in meerdere parent-bundels.
- Verwijderen of versoepelen van tijdsvenster-filter (alleen bestaande spinbox).
- Slice 54 workflow-seam, checkbox-preview, audittrail, feature-flag `meekoppel_workflow_v2`.
- Motor-run, `.rcm.json`-mutatie, ltap_light-korting.
- ValidateWindow/LTAP meekoppelkansen.
- Meekoppelen op `element_naam` (historisch; blijft uitgesloten).

## Further Notes

- Zie `SLICE_MAP.md` voor volgorde t.o.v. slice 54 en architectuur-golf.
- **Risico:** brede parent-groepen → meer taken per rij; mitigatie in slice 54 via checkboxes.
- **Risico:** grote due-span binnen één parent → groep blijft buiten venster; analist verhoogt N handmatig.
- Na merge slice 55: slice 54 issues 03+ kunnen starten zonder discovery-semantiek te heropenen.
