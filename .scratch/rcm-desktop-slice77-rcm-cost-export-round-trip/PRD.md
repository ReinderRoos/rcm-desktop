# PRD — Slice 77: RCM-Cost export via bewaarde AW-bron (round-trip)

**Status:** ready-for-agent
**Voorganger:** slice 35 (RCM-Cost import), slice 65 (RCM-Cost parity), ADR-0004, **ADR-0011**
**Datum:** 2026-06-11
**Triage:** `ready-for-agent`

> Synthese van een `/grill-with-docs`-sessie (2026-06-11). Wens 5 van 5.
> Heropent bewust de export-uitstel-clausule van ADR-0004 → **ADR-0011**.

---

## Problem Statement

RCM2 kan een **RCM-Cost / Availability-Workbench (AW)** export (25 sheets)
**inlezen** (slice 35), maar er is **geen weg terug**. Een analist die het model in
RCM2 bewerkt (faalwijzen, effecten, PM/correctieve taken) kan die wijzigingen niet
terugbrengen naar AW/RCM-Cost. De importmapper leest bovendien maar **10 van de 25
sheets**; een vanuit het slanke RCM2-model heropgebouwde workbook zou de 15
niet-gemodelleerde sheets (Labor, Spares, Equipments, profielen, join-tabellen)
verliezen — geen werkbare round-trip.

## Solution

Vanuit de gebruiker gezien:

- De analist kan vanuit de tool een **AW-leesbaar bestand exporteren** dat het in
  RCM2 bewerkte model bevat en in RCM-Cost ingelezen kan worden.
- De export behoudt **volledige fidelity**: niet-gemodelleerde sheets/velden komen
  ongewijzigd mee, doordat RCM2 bij import een **kopie van de originele workbook**
  (de **AW-bron-sidecar**) heeft bewaard en die op export her-emitteert met alleen
  de bewerkte velden **gepatcht**.
- In RCM2 **nieuw aangemaakte** entiteiten worden als **nieuwe rijen toegevoegd**;
  rijen die RCM2 mist worden **niet automatisch verwijderd** maar **gemeld**, zodat
  de analist verwijdering bewust in AW afhandelt.
- Ontbreekt de bron, dan **blokkeert** de export met een duidelijke melding en een
  **file-picker** om de originele AW-workbook te lokaliseren.

---

## Zoom-out: modulekaart

```
 IMPORT (bestaand)                          EXPORT (NIEUW, spiegelt import)
 ────────────────                           ──────────────────────────────
 isograph_excel_reader  (openpyxl read)     isograph_export_service  (openpyxl write)
        │                                            ▲   patch must-v1 sheets
 isograph_import_service  build_from_sheets         │   + append nieuwe rijen
        │  → RCMProject                       AW-bron-sidecar  <project>.rcm.source.xlsx
 isograph_open_flow_service  persist          (bewaard bij import)
        │  save_project_atomically                  ▲
        │  + KOPIE workbook → sidecar  ──────────────┘
        ▼
 import_settings["source_workbook_path"]
```

Betrokken seams (domeintaal → bestand):

- **Layout-contract (kern)** — `rcm_core/isograph_export_contract.py`
  (`EXPECTED_SHEET_NAMES` (25), `MUST_V1_SHEET_HEADERS` (10), `load_workbook_headers`).
  Definieert welke sheets/kolommen RCM2 begrijpt → de **patch-doelen**.
- **Importmapper (adapter)** — `rcm_desktop/adapter/isograph_import_service.py`
  (`build_from_sheets`, AW-ID-behoud, `pm_id = Cause|TaskId|SubIndex`,
  `link_id`-formules). De **reverse mapping** spiegelt dit.
- **Persist-gate (adapter)** — `rcm_desktop/adapter/isograph_open_flow_service.py`
  (`persist_import_wizard_result`). Hier wordt de **sidecar-kopie** geschreven.
- **Project-pad-resolutie (adapter)** — `rcm_desktop/adapter/project_path_resolution_service.py`
  (`ResolvedProjectPath.cache_path()` → `.rcm.cache.json`). Voeg
  `source_workbook_path()` → `.rcm.source.xlsx` toe (zelfde conventie).
- **import_settings (kern)** — `rcm_core/import_settings_contract.py`
  (`normalize_import_settings`, pass-through). Nieuwe erkende key
  `source_workbook_path`.
- **Atomic save (adapter)** — `rcm_desktop/adapter/save_service.py`
  (`save_project_atomically`).
- **Export-service (NIEUW, adapter)** — `rcm_desktop/adapter/isograph_export_service.py`,
  Qt-vrij; laadt de sidecar (openpyxl), patcht must-v1 sheets uit `RCMProject`,
  voegt nieuwe rijen toe, verzamelt waarschuwingen, schrijft de output-workbook.
- **Werkruimte-venster** — `rcm_desktop/views/results_workspace_window.py`:
  export-actie (knop/menu), file-pickers, blokkade- en waarschuwingsdialogen.

---

## Implementation Decisions

### Besloten ontwerpkeuzes (grilling → ADR-0011)

- **Doel: het bewerkte MODEL (`edited_model`).** Export brengt de in RCM2 bewerkte
  modelstructuur (causes/faalwijzen, effecten, PM/correctieve taken, koppelingen)
  terug; geen analyse-uitvoer.
- **Fidelity via bewaarde bron + patch (`preserve_source_patch`).** Bij import wordt
  de originele AW-workbook bewaard; export her-emitteert alle 25 sheets en patcht
  **alleen** de must-v1 velden die RCM2 bewerkt. De 15 niet-gemodelleerde sheets
  gaan ongewijzigd mee.
- **Opslag als sidecar (`sidecar`).** De bron staat als
  `<project>.rcm.source.xlsx` naast het project; het pad in
  `import_settings["source_workbook_path"]`.
- **Patch-scope (`edit_append_warn_delete`).** Bewerken op bestaande rijen (match op
  behouden AW-ID / gereverseerde synthetische sleutel) + nieuwe rijen toevoegen
  (gegenereerde AW-ID's). **Niet** auto-verwijderen; **wel waarschuwen** als RCM2
  rijen mist die de bron had.
- **Ontbrekende bron blokkeert (`block_locate`).** Geen sidecar → blokkeer met
  melding + file-picker om de bron te lokaliseren; daarna sidecar-pad bijwerken.
- **ADR (`new_superseding`).** ADR-0011 superseedt de export-clausule van ADR-0004.

### Reverse-mapping-contract (must-v1)

| RCM2-entiteit | AW-sheet | Sleutel (match) | Gepatchte velden |
|---------------|----------|------------------|------------------|
| `Faalwijze` | `RcmCauses` | `fm_id` = `Id` | FmMttf, FmStd, InitialAge, Mttr, FmDistribution, LocationId, Description |
| `EffectKlasse` | `RcmEffects` | `klasse_id` = `Id` | Description (+ Type indien bewerkt) |
| `FMEffectLink` | `RcmCauseEffectAssignments` | `(Cause, Effect, SubIndex)` ← `link_id` | RedundancyFactor, PEnable/IEnable/CEnable |
| `PMTask` | `RcmScheduledTasks` | `pm_id` → `(Cause, TaskId, SubIndex)` | TaskDuration, FixedInterval, Enabled, Type, Description |
| corrective | `RcmCorrectiveTasks` | `Cause` | TaskDuration, Description |
| `PBSItem` | `RcmLocations` | `pbs_id` = `Id` | Parent, Description |
| `Functie` | `RcmFunctions` | `functie_id` = `Id` | Parent, Description |
| `TaskGroup` | `TaskGroups` | `group_id` = `Id` | Description |
| (FF) | `RcmFunctionalFailures` | afgeleid uit `eindgevolg`/parent | Description |
| config | `Project` | n.v.t. (singleton) | LifeTime, RcmNoSimulations, RcmRandomNoSeed |

`import_settings.isograph_*` (pass-through ruwe AW-kolommen) wordt waar relevant
mee teruggeschreven, zodat niet-gemodelleerde must-v1-velden niet stilletjes
verloren gaan.

### Onderscheid imported vs RCM2-created

Er is **geen expliciete vlag** op entiteiten. Onderscheid wordt afgeleid uit
**aanwezigheid in de sidecar**: een entiteit waarvan de (gereverseerde) sleutel
**wel** in de brons-sheet staat → **patch**; **niet** in de bron → **append** met
gegenereerde AW-ID. Een sleutel die **wel** in de bron staat maar **niet** meer in
`RCMProject` → **waarschuwing** (kandidaat-verwijdering, niet automatisch).

### Architectuurprincipes (AGENTS.md / ADR-0004)

- Export-mapper is **Qt-vrij** in de adapterlaag; UI alleen via adapter.
- `rcm_core` blijft Qt-vrij; het contract (`isograph_export_contract`) blijft de
  bron voor sheet/kolomnamen.
- `openpyxl` is al een runtime-dependency.

---

## User Stories

1. Als RCM-analist wil ik mijn in RCM2 bewerkte model exporteren naar een
   AW-leesbaar bestand, zodat ik het in RCM-Cost kan inlezen.
2. Als analist wil ik dat de export alle 25 AW-sheets bevat, zodat RCM-Cost het
   zonder fouten leest.
3. Als analist wil ik dat sheets/velden die RCM2 niet modelleert ongewijzigd
   meekomen, zodat ik niets uit het origineel verlies.
4. Als analist wil ik dat mijn bewerkingen (MTTF, hersteltijd, RF, taakduur,
   interval, omschrijvingen…) op de juiste AW-rijen worden gepatcht, zodat AW mijn
   wijzigingen overneemt.
5. Als analist wil ik dat in RCM2 nieuw aangemaakte faalwijzen/taken als nieuwe
   AW-rijen worden toegevoegd met geldige ID's, zodat ze in AW verschijnen.
6. Als analist wil ik **niet** dat de export rijen verwijdert, maar dat het mij
   **waarschuwt** welke bron-rijen RCM2 mist, zodat ik dat bewust in AW afhandel.
7. Als analist wil ik dat de tool bij import een kopie van mijn originele workbook
   bewaart, zodat round-trip-export later mogelijk is.
8. Als analist wil ik dat de export blokkeert met een duidelijke melding als de
   originele workbook ontbreekt, zodat ik geen kapot/onvolledig bestand krijg.
9. Als analist wil ik in dat geval een **file-picker** om de originele workbook te
   lokaliseren, zodat ik de export alsnog kan voltooien.
10. Als analist wil ik een overzicht van wat gepatcht, toegevoegd en gewaarschuwd is
    na de export, zodat ik de uitkomst kan controleren.
11. Als analist wil ik dat behouden AW-ID's (pbs_id, functie_id, fm_id, klasse_id)
    de match sturen, zodat de juiste rijen worden bijgewerkt.
12. Als analist wil ik dat het exportbestand mijn origineel niet overschrijft (apart
    pad/save-picker), zodat de bron veilig blijft.

---

## Testing Decisions

Goede tests toetsen **extern gedrag** aan de seam; export is adapter-first/Qt-vrij.

- **Sidecar-behoud (persist-seam):** na `persist_import_wizard_result` bestaat
  `<project>.rcm.source.xlsx` en staat het pad in
  `import_settings["source_workbook_path"]`. Round-trip-load behoudt de key
  (pass-through-contract).
- **Export-mapper (`isograph_export_service`, Qt-vrij):**
  1. **Identiteit/no-op:** importeren → direct exporteren zonder bewerking levert
     een workbook waarvan alle 25 sheets inhoudelijk gelijk zijn aan de bron
     (mod. cel-normalisatie).
  2. **Patch:** een bewerkt veld (bv. `FmMttf`) verschijnt op de juiste
     `RcmCauses`-rij; ongemodelleerde sheets ongewijzigd.
  3. **Append:** een in RCM2 toegevoegde faalwijze levert een nieuwe `RcmCauses`-rij
     met geldige `Id`; bijbehorende assignments/taken meegenomen.
  4. **Warn-delete:** een in de bron aanwezige cause die in `RCMProject` ontbreekt →
     waarschuwing in het resultaat, géén verwijdering uit de output.
  5. **Round-trip via import:** export → opnieuw `build_from_sheets` → het bewerkte
     `RCMProject` komt terug (sleutelvelden gelijk).
- **Ontbrekende bron:** export zonder geldige sidecar geeft een geblokkeerd
  resultaat met een "locate"-signaal (geen bestand geschreven).
- **pytest-qt (venster):** export-actie → save-picker; ontbrekende bron → blokkade-
  dialoog + file-picker; samenvatting (patched/added/warned) getoond.
- **Prior art:** `tests/test_isograph_import_service.py`,
  `tests/test_isograph_open_flow_service.py`,
  `tests/test_isograph_export_fixture_contract.py`,
  `tests/test_import_settings_contract.py`, fixtures onder `tests/fixtures/`
  (`RCMCostdata export_*.xlsx`).

---

## Out of Scope

- Bidirectionele live-sync / conflictoplossing tussen RCM2 en AW.
- Heropbouw van een AW-workbook **zonder** bron (de slanke-model-route is verworpen).
- Exporteren van analyse-uitvoer (LCC/Top 10) naar AW.
- Het modelleren van de 15 niet-must-v1 sheets in `RCMProject` (blijven pass-through
  via de bron).
- Automatisch verwijderen van rijen (alleen waarschuwen).
- Migratie/seeding van een sidecar voor **bestaande** projecten zonder bron, anders
  dan via de locate-file-picker.

## Further Notes

- ADR-0011 (`docs/adr/ADR-0011-rcm-cost-export-round-trip.md`) legt het besluit en de
  verworpen alternatieven vast; `CONTEXT.md` definieert **AW-bron-sidecar** en
  **RCM-Cost export (round-trip)**.
- Reverse van synthetische sleutels: `pm_id` = `Cause|TaskId|SubIndex`,
  `link_id` (`FMEL|cause|effect|SubIndex`, `PMEL|pm_id|effect`) — herbruik de
  formules uit `isograph_import_service` / `isograph_pm_import_rules` om drift te
  voorkomen.
- Volgorde (tracer-bullet): 01 sidecar-behoud → 02 patch bestaande rijen → 03
  append + warn-delete → 04 UI-actie + block/locate + samenvatting.
