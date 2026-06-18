# Slice 35 — RCM-Cost (Isograph) Excel-import & navigatieboom

**Triage:** done (bootstrap-import af; zie KANBAN_HANDOFF.md)  
**Type:** AFK (fase 0 deels ready-for-human: PM-spike) + kern Qt-vrij, daarna desktop  
**Parent:** grill-me RCM-Cost import (2026-05-19); scrub-list Excel-IO  
**Versie:** 1.0  
**Datum:** 2026-05-19  
**Fixture (structuur):** `tests/fixtures/RCMCostdata export_leeg.xlsx` (inhoud bewust leeggemaakt i.v.m. vertrouwelijkheid)

## Problem Statement

Reliability-analisten werken vandaag in **Isograph RCM-Cost / Availability Workbench** met een exportformaat (`RCMCostdata export_*.xlsx`, 25 tabbladen). RCM2 desktop gebruikt **`.rcm.json`** met een slank **domain model** (`RCMProject`, PBS → functie → faalwijze, aparte FM- en PM-effectlinks).

Er is **geen importpad**. Handmatig overtypen is onhoudbaar; Excel-IO staat op de **scrub-list**. Tegelijk wil de organisatie:

- bestaande AW-projecten **bootstrappen** naar RCM2 (eenmalige migratie, geen bidirectionele sync in v1);
- later een **subset-export** terug naar AVSIM-importeerbaar Excel (niet alle kolommen);
- **herleidbare structuur** zoals in AW: Isograph-ID’s, PBS → functie → faalwijze in de UI;
- **geen gevolgkosten per effect** in RCM2 — wel beschikbaarheid/degradatie via effectklassen en **onafhankelijke** FM- vs PM-effecttoekenning;
- **geen rework** doordat import wordt gebouwd vóór duidelijk is welke export-domeinen modeluitbreiding vereisen (reservedelen-catalogi, Avsim-capaciteit, PM-semantiek `PEnable`/`IEnable`).

## Solution

### Fase 0 — Analyse (gate vóór implementatie)

1. **Import-capability matrix** (tabblad → RCM2-veld → must/should/won't + eenheden).
2. **PM-semantiek-spike** op een **gevuld intern testbestand** (niet het leeggemaakte fixture): betekenis van `PEnable`/`IEnable`/`CEnable` in `RcmCauseEffectAssignments` t.o.v. `PMEffectLink`.
3. **ADR** om Excel-IO van de scrub-list te halen en het contract voor top-level **`import_settings`** vast te leggen.

### Fase 1 — Verticale slice (na gate)

1. **Qt-vrije importmapper** (deep module): Excel → `RCMProject` + `import_settings` + conflictrapport (IA per locatie).
2. **Serialisatie** van `import_settings` in `.rcm.json` (passief tot Monte Carlo / export).
3. **Import-wizard** (minimaal): `modeljaar`; conflicten initiële leeftijd per PBS.
4. **Navigatieboom** in resultatenwerkruimte (en waar PBS-sidebar al bestaat): **PBS → functie → faalwijze** met Isograph-ID’s.
5. **Desktop:** “Project openen uit RCM-Cost export…” → validatie → opslaan als `.rcm.json` → openen in bestaande flow.

## User Stories

### Strategie en governance

1. Als productowner wil ik dat Excel-import **expliciet van de scrub-list** wordt gehaald via ADR, zodat agents niet stilletjes scope schenden.
2. Als analist wil ik **bootstrap-import** (AW → RCM2), zodat ik niet alles handmatig hoef over te typen.
3. Als analist wil ik **geen verplichte terug-sync** naar AW in v1, zodat scope beheersbaar blijft.
4. Als productowner wil ik een **import-matrix** vóór code, zodat rework na latere Avsim-analyse wordt voorkomen.
5. Als ontwikkelaar wil ik een **PM-spike** op echte data, zodat `pm_effect_links` niet verkeerd worden afgeleid uit `PEnable`.

### Domein: identiteit en structuur

6. Als analist wil ik **Isograph-hiërarchische ID’s** behouden (`pbs_id`, `functie_id`, `fm_id` = cause-id), zodat ik FM’s herken en later subset-export mogelijk is.
7. Als analist wil ik de keten **locatie → functie → functioneel falen → faalwijze** in RCM2 terugzien, zodat look-and-feel overeenkomt met AW.
8. Als analist wil ik dat **functioneel falen** (AW `RcmFunctionalFailures`) in **`eindgevolg`** van de faalwijze staat en de **cause-omschrijving** in `faalwijze_omschrijving`, zodat er geen vierde entiteit nodig is.
9. Als analist wil ik **dominant falen** modelleren (weinig FM’s per functie), zodat het model slank blijft.
10. Als analist wil ik in de **linker navigatieboom** doorklikken tot **faalwijze-niveau**, zodat ik vanuit een FM snel functie en component zie.

### Domein: leeftijd en tijd

11. Als analist wil ik **leeftijd op bouwdeel/PBS** houden (niet per FM zoals AW), zodat vervanging/REV alle onderliggende faalwijzen verjongt.
12. Als analist wil ik bij import **`modeljaar` expliciet** opgeven, zodat leeftijd en kalenderjaar kloppen.
13. Als analist wil ik bij **tegenstrijdige InitialAge** op één locatie een **wizard-keuze**, zodat geen stille fouten ontstaan.
14. Als analist wil ik dat AW-tijden in **uren** worden geïnterpreteerd en naar RCM2 **jaren** worden omgerekend waar nodig (÷8760), zodat MTTF en lifecycle kloppen.
15. Als ontwikkelaar wil ik ruwe AW-waarden in **`import_settings`** bewaren, zodat latere Monte Carlo/export traceerbaar blijft.

### Domein: effecten en beschikbaarheid

16. Als analist wil ik **geen gevolgkosten** (`cost_gevolg_eur`, `CostPerOccurrence`, ITdt/CTdt als kosten) in RCM2 importeren, zodat het product focus houdt op beschikbaarheid.
17. Als analist wil ik **effectklassen** kwalitatief importeren (`Id`, `Description`, koppeling aan functie via keten/regels in matrix).
18. Als analist wil ik **RF (RedundancyFactor)** uit AW als **`FMEffectLink.fractie`**, zodat 1% / 50% / 49%-verdeling klopt.
19. Als analist wil ik dat **FM-effecten** en **PM-effecten** **apart** blijven (`fm_effect_links` / `pm_effect_links`), zoals de motor al doet.
20. Als analist wil ik dat PM-impact op functies **niet wordt geraden** zolang de spike geen regels heeft, zodat beschikbaarheidscijfers betrouwbaar blijven.

### Import-scope tabbladen

21. Als analist wil ik dat **must v1** minimaal de RCM-kernketen importeert: pruned `RcmLocations`, Functions, FunctionalFailures, Causes, Effects, CauseEffectAssignments, Corrective/Scheduled Tasks, TaskGroups, `Project`-subset.
22. Als analist wil ik dat **Labor/Spares/Equipments** en profielen **niet** worden gemodelleerd in v1, zodat RCM2 slank blijft.
23. Als analist wil ik CM/PM-**kostentotalen** uit task-tabbladen (lump sum), niet uit spare-catalogi.
24. Als analist wil ik `LifeTime`, `RcmNoSimulations`, `RcmRandomNoSeed` in **`config`**, zodat lifecycle en toekomstige MC-aansluiting werken.
25. Als analist wil ik overige MC-/sim-kolommen uit `Project` in **`import_settings`**, zodat ze niet verloren gaan.

### PBS-boom

26. Als analist wil ik alleen **relevante locaties** (pruned subtree naar causes + ancestors), zodat de boom niet 1000+ lege nodes toont.
27. Als analist wil ik `Description` minimaal als **bouwdeelnaam** zien, zodat knopen leesbaar zijn.
28. Als analist wil ik na import de boom **vóór eerste run** al tot FM kunnen zien (structuurboom), zodat ik het model kan verkennen.

### Desktop en validatie

29. Als analist wil ik via menu **RCM-Cost export openen**, een bestand kiezen, en na wizard **`.rcm.json` opslaan**, zodat ik in RCM2 verder werk.
30. Als analist wil ik na import **validate + run** kunnen doen met bestaande adapters, zodat geen parallel pad ontstaat.
31. Als analist wil ik duidelijke **foutmeldingen** bij ontbrekende FK’s of lege must-sheets, zodat ik het bronbestand kan repareren.

### Architectuur en kwaliteit

32. Als ontwikkelaar wil ik een **Qt-vrije** `isograph_import_service` (of equivalent), zodat mapping pytestbaar is zonder QApplication.
33. Als ontwikkelaar wil ik Excel-parsing **gescheiden** van domein-mapping (reader vs builder), zodat tests met in-memory rijen kunnen.
34. Als ontwikkelaar wil ik **views** alleen via **adapter** te laten praten met import, zodat UI/kern-decoupling geldt.
35. Als tester wil ik **unit-tests** op de mapper met het structuur-fixture en minimaal één **intern gevuld** bestand wanneer beschikbaar.
36. Als tester wil ik **pytest-qt smoke**: open dialog mock → project geladen → navigatieboom toont FM-knoop onder functie.

### Documentatie

37. Als analist wil ik in `CONTEXT.md` een korte sectie **RCM-Cost import**, zodat het pad vindbaar is naast FM-verificatie.
38. Als ontwikkelaar wil ik de **import-matrix** in `.scratch/…/` als SSOT voor kolommapping, zodat export later dezelfde bron gebruikt.

### Toekomst (expliciet niet v1)

39. Als analist wil ik later **subset-export** naar AVSIM-importeerbaar Excel, zodat ik niet alles hoeft te vullen.
40. Als analist wil ik later **Monte Carlo** kunnen gebruiken met bewaarde `import_settings`, zodat AW-instellingen niet opnieuw hoeven.

## Implementation Decisions

### Fasering (grill-me besluiten)

| Fase | Inhoud | Gate |
|------|--------|------|
| **0** | Matrix + PM-spike + ADR | Geen importcode tot spike + matrix gereed |
| **1** | Mapper + serialisatie + wizard + navigatieboom + Open Excel | Na gate; één verticale demo-slice |

### Modules (diep vs ondiep)

| Module | Rol | Diepte |
|--------|-----|--------|
| **`isograph_excel_reader`** | Laadt workbook; levert sheet → rij-dicts; geen domeinlogica | Ondiep |
| **`isograph_import_service`** | Mapping AW → `RCMProject`, `import_settings`, `ImportBuildResult` (conflicten, warnings) | **Diep, Qt-vrij** |
| **`import_conflict_service`** | IA-conflicten per `pbs_id`, wizard-resolutie toepassen | Diep, Qt-vrij |
| **`RCMProject` serialisatie** | Optioneel top-level `import_settings: dict`; round-trip in `to_dict`/`from_dict` | Kern, klein |
| **`rcm_navigation_tree_builder`** | Uitbreiding structuurboom: PBS-knoop → kinderen functie → FM; node-type enum | Diep, Qt-vrij |
| **`rcm_navigation_tree_model`** | Qt-model voor sidebar (of uitbreiding `PBSResultsTreeModel`) | Ondiep |
| **`isograph_import_dialog` / adapter orchestration** | Bestand kiezen, modeljaar, conflict-UI, aanroep builder, `save_project` | Adapter |
| **`results_workspace_window`** (en evt. validate) | Sidebar op navigatieboom; selectie FM filtert FM-tabel | View |

### Mappingregels (must v1)

**Identiteit**

- `RcmLocations.Id` → `PBSItem.pbs_id`; `Parent` → `parent_pbs_id` (pruned: alleen ancestors van cause-locaties).
- `RcmFunctions.Id` → `Functie.functie_id`; `Parent` → koppeling naar PBS (laatste segment van ID-keten).
- `RcmCauses.Id` → `Faalwijze.fm_id`; `Parent` (FF-id) → tekst in `eindgevolg` via `RcmFunctionalFailures.Description`.
- Cause `Description` → `faalwijze_omschrijving`; `FunctionDescription` / keten voor display alleen.

**Faalmodel**

- `FmMttf`, `FmStd`, `InitialAge` (uren) → `mttf_jaar`, `sigma_jaar`; **niet** `InitialAge` op FM persistent maken.
- `FmDistribution` + wizard-vlaggen → `FailureType` (`random` / `aging`) volgens matrix-regels (spike op gevuld bestand).
- `Mttr` (uren) → `downtime_per_failure` in uren.
- `RcmCorrectiveTasks` / `RcmScheduledTasks` → CM-kosten/duration/interval op FM/PMTask; taaktype afleiden uit beschrijving/Enabled/FixedInterval waar nodig.

**Effecten**

- `RcmEffects`: **geen** kostenvelden; `EffectKlasse.klasse_id` = `Id`, `omschrijving` = `Description`; `functie_id` via matrix (keten cause → function).
- `RcmCauseEffectAssignments`: `RedundancyFactor` → `FMEffectLink.fractie`; `Cause`/`Effect` FK’s; `PEnable`/`IEnable`/`CEnable` → `import_settings` tot PM-spike klaar is.
- **`pm_effect_links`:** alleen vullen als spike expliciete regels geeft; anders leeg + waarschuwing in importrapport.

**Config & import_settings**

- `Project.LifeTime` (uren) → `config.lifecycle_years` (÷8760).
- `Project.RcmNoSimulations` → `config.monte_carlo_n`; `RcmRandomNoSeed` → `config.monte_carlo_seed`.
- Overige MC-/NPV-/criticality-kolommen uit `Project` + per-FM onzekerheidskolommen (`TotalCostErrPc`, …) → `import_settings` genest onder stabiele sleutels (`isograph_project`, `isograph_causes/{fm_id}`, …).

**Leeftijd**

- Per cause-locatie: verzamel `InitialAge`; bij één waarde → afleid `bouwjaar = modeljaar - age_jaar`; bij conflict → `ImportConflict` voor wizard.
- Ruwe cause-IA altijd in `import_settings` voor audit.

**Eenheden**

- Globale aanname: **AW exporttijden in uren**; conversietabel in matrix (kolom → doel-eenheid).

### `ImportBuildResult` (conceptueel)

```python
@dataclass(frozen=True)
class ImportConflict:
    pbs_id: str
    initial_ages_hr: tuple[float, ...]
    cause_ids: tuple[str, ...]

@dataclass(frozen=True)
class ImportBuildResult:
    project: RCMProject
    import_settings: dict[str, object]
    conflicts: tuple[ImportConflict, ...]
    warnings: tuple[str, ...]  # o.a. "pm_effect_links niet geïmporteerd: spike open"
```

### Navigatieknoop (conceptueel)

```python
class NavigationNodeKind(Enum):
    PBS = "pbs"
    FUNCTIE = "functie"
    FAALWIJZE = "faalwijze"

@dataclass(frozen=True)
class RcmNavigationNode:
    kind: NavigationNodeKind
    node_id: str  # pbs_id, functie_id of fm_id
    label: str
    children: tuple[RcmNavigationNode, ...]
    # Aggregaten alleen op PBS-niveau wanneer run_result aanwezig
```

- Selectie FM-knoop filtert FM-tabel / scope analoog aan PBS-subtree-selectie.
- Bestaande `build_pbs_structure_tree` blijft bruikbaar voor run-gekoppelde aggregaten; nieuwe builder voedt **structuur**-modus.

### ADR (verplicht vóór fase 1)

- Supersedes scrub-list item **Excel-IO** voor import (export subset = latere slice).
- Contract `import_settings`: versieveld `import_settings_schema_version: 1`; onbekende keys behouden bij round-trip.

## Testing Decisions

**Goede tests** controleren **gedrag aan de buitenkant** van de deep module: gegeven rij-data of een klein synthetisch workbook → verwacht `RCMProject` met juiste FK’s, fracties, eenheden, `import_settings`-sleutels; geen assert op interne parser-stappen.

**Modules met tests (verplicht):**

| Module | Type |
|--------|------|
| **isograph_import_service** | Unit — mapping, prune, RF, eenheden, conflicts, warnings bij ontbrekende PM-regels |
| **import_conflict_service** | Unit — resolve conflict → één bouwjaar |
| **rcm_navigation_tree_builder** | Unit — diepte PBS→functie→FM, deterministische sortering |
| **RCMProject serialisatie** | Unit — `import_settings` round-trip |
| **isograph_import_dialog / main flow** | pytest-qt smoke — file pick mock → project in state |

**Niet verplicht:** volledige UI-styling van wizard; elke Excel-kolom individueel (gedekt via matrix + steekproef).

**Prior art:** `tests/test_editing_pipeline.py`, `tests/test_desktop_result_filter_service.py`, `tests/test_desktop_pbs_results_tree_model.py`, `tests/test_desktop_faalwijzen_edit_service.py`.

**Fixture-beleid:** structuur-fixture leeggemaakt = layout/smoke; **acceptatie-mapping** op kernvelden vereist **intern gevuld testbestand** (issue 02) zodra beschikbaar.

## Out of Scope

- **Volledige** 25-tabblad-pariteit en **Avsim-capaciteit** (`Avsim*`-kolommen, capaciteitsgrafieken).
- **Labor / Spares / Equipments** catalogi en koppeltabellen in het domain model.
- **`RcmProjectProfile`** en locatie-specifieke kostennormen als modeluitbreiding.
- **Gevolgkosten per effect** (`cost_gevolg_eur` importeren of motorisch gebruiken); optionele latere ADR om veld te deprecaten.
- **Bidirectionele sync** AW ↔ RCM2; **subset-export** naar Excel (eigen slice).
- **Monte Carlo UI/motor** in deze slice (alleen bewaren instellingen).
- **Automatische PM-effectlinks** uit `PEnable` zonder afgeronde spike.
- **NEN-afleiding** uit `HierarchyLevel` als must (alleen should na validatie op gevuld export).
- **Killer/olifant**, LTAP-light, meekoppelkansen.

## Further Notes

### Must-import v1 tabbladen

| Must | Won't / defer v1 |
|------|------------------|
| RcmLocations (pruned) | Labor, Spares, Equipments + links |
| RcmFunctions | RcmProjectProfile, *Profiles |
| RcmFunctionalFailures (→ eindgevolg) | Avsim-capaciteit |
| RcmCauses | |
| RcmEffects (kwalitatief) | |
| RcmCauseEffectAssignments | |
| RcmCorrectiveTasks, RcmScheduledTasks | |
| TaskGroups | |
| Project (LifeTime, RcmNoSimulations, RcmRandomNoSeed + import_settings) | |

### Risico’s

| Risico | Mitigatie |
|--------|-----------|
| Leeggemaakt fixture mist IA/PEnable-patronen | PM-spike + gevuld testbestand |
| Verkeerde PM-semantiek | Geen `pm_effect_links` tot spike OK |
| `cost_gevolg_eur` in schema maar out of scope | Matrix + geen import; optionele ADR |
| ID-keten vs NEN-velden | Pruned PBS + Description; NEN later |
| Scrub-list | ADR vóór merge fase 1 |

### Issues (gepubliceerd)

| # | Titel | Triage |
|---|--------|--------|
| 01 | Import-capability matrix (AW → RCM2) | done |
| 02 | PM-semantiek-spike (PEnable/IEnable) | done |
| 03 | ADR Excel-IO + import_settings-contract | done |
| 04 | RCMProject: import_settings serialisatie | done |
| 05 | isograph_import_service (mapper, Qt-vrij) | done |
| 06 | Import-wizard: modeljaar + IA-conflicten | done |
| 07 | Navigatieboom PBS → functie → faalwijze | done |
| 08 | Desktop: Open RCM-Cost export + opslaan | done |
| 09 | AW Enabled → planning-overlay seed | done |

**Handoff:** zie `KANBAN_HANDOFF.md` in deze map.

**Afhankelijkheden:** 01 ∥ 02 ∥ 03; 03 → 04 → 05; 02 → 05 (PM-links deel); 05 → 06 → 08; 05 → 07 → 08. **Gate fase 1:** 01 + 02 + 03 gereed vóór 05 start (menselijk voor 02).
