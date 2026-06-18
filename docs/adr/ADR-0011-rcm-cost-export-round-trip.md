# ADR-0011 — RCM-Cost export via bewaarde AW-bron (round-trip)

## Status

Accepted (2026-06-11). **Supersedes** de export-uitstel-clausule van ADR-0004
(§"Excel-export (out of scope deze ADR)" / "subset-export blijft latere slice").
De import-besluiten en het `import_settings`-contract van ADR-0004 blijven
onveranderd van kracht.

## Datum

2026-06-11

## Context

ADR-0004 stelde RCM-Cost **export** bewust uit: import was bootstrap-only,
asymmetrisch, geen bidirectionele sync. Analisten willen nu het in RCM2
**bewerkte model** (faalwijzen/causes, effecten, PM/correctieve taken) terug in
RCM-Cost / Availability Workbench (AW) inlezen.

De importmapper leest maar **10 van de 25 sheets** (`MUST_V1_SHEET_HEADERS`); de
overige 15 sheets (Labor, Spares, Equipments, profielen, join-tabellen) worden
op de import-gate wel gevalideerd maar niet naar het slanke RCM2-model
gemodelleerd. Een vanuit dat slanke model heropgebouwde 25-tab workbook zou die
velden verliezen — geen werkbare round-trip.

## Beslissing

1. **Bron-behoud bij import.** Bij Excel-import bewaart RCM2 een **kopie van de
   originele AW-workbook** als sidecar-bestand naast het project
   (`<project>.rcm.source.xlsx`, naast `<project>.rcm.json` zoals de bestaande
   `.rcm.cache.json`-conventie); het pad wordt vastgelegd in `import_settings`
   (`source_workbook_path`, pass-through-key conform ADR-0004).

2. **Export = patch op de bewaarde bron.** Export her-emitteert alle 25 sheets uit
   de sidecar en **patcht alleen de velden die RCM2 bewerkt** (de must-v1 sheets:
   RcmCauses, RcmEffects, RcmCauseEffectAssignments, RcmCorrectiveTasks,
   RcmScheduledTasks, RcmFunctions, RcmFunctionalFailures, RcmLocations,
   TaskGroups, Project). Niet-gemodelleerde sheets/velden gaan **ongewijzigd**
   mee → volledige fidelity.

3. **Patch-scope: bewerken + toevoegen, niet verwijderen.** Bewerkte waarden
   worden op **bestaande rijen** gepatcht (gematcht op behouden AW-ID's:
   `pbs_id`/`functie_id`/`fm_id`/`klasse_id`/`group_id`, en de gereverseerde
   synthetische sleutels `pm_id` → `Cause|TaskId|SubIndex`, `link_id` →
   assignment-rij). In RCM2 **nieuw aangemaakte** entiteiten worden als **nieuwe
   rijen toegevoegd** met gegenereerde AW-ID's. De export **verwijdert nooit
   automatisch** rijen, maar **waarschuwt** als RCM2 rijen mist die de bron wél
   had — de analist handelt verwijdering in AW af.

4. **Ontbrekende bron blokkeert.** Is de sidecar niet beschikbaar bij export
   (oude projecten van vóór deze ADR, verplaatst bestand), dan **blokkeert** de
   export met een duidelijke melding en biedt een **file-picker** om de originele
   AW-workbook te lokaliseren; daarna wordt het sidecar-pad bijgewerkt.

## Verworpen alternatieven

- **Heropbouw uit het slanke RCM2-model** — verliest de 15 niet-gemodelleerde
  AW-sheets/velden; geen werkbare round-trip.
- **Bidirectionele live-sync** — te zwaar; sidecar-patch geeft round-trip zonder
  sync-complexiteit en zonder conflictmodel.
- **Auto-delete van ontbrekende rijen** — riskant (de analist kan in AW
  afhankelijkheden hebben); waarschuwen + analist beslist is veiliger.

## Consequenties

- `import_settings` krijgt een expliciet erkende `source_workbook_path`-key; de
  pass-through-normalisatie (`import_settings_contract`) blijft ongewijzigd.
- `openpyxl` blijft een **runtime**-dependency (was al runtime voor import).
- Nieuwe adapter-module spiegelt de import (`isograph_export_service`,
  Qt-vrij); UI alleen via adapter (architectuurprincipe).
- Oude projecten zonder sidecar zijn niet kapot, maar exporteren pas na
  het lokaliseren van de bron.
- `CONTEXT.md`: nieuwe termen **AW-bron-sidecar** en **RCM-Cost export
  (round-trip)**.

## Gerelateerd

- Supersedes-clausule: ADR-0004 §"Excel-export (out of scope deze ADR)".
- ADR-0008 (RCM-Cost parity), `rcm_core/isograph_export_contract.py`.
- PRD: `.scratch/rcm-desktop-slice77-rcm-cost-export-round-trip/PRD.md`.
