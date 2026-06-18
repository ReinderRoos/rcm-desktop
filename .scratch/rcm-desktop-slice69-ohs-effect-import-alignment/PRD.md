# PRD — RCM2 desktop slice 69 (OHS cause–effect import alignment)

**Status:** ready-for-agent  
**Versie:** 1.0  
**Triage-labels:** ready-for-agent  
**Type:** AFK (Isograph Excel-import + kern importregels)  
**Parent:** ADR-0004 (Isograph Excel-import); slice 35 (RCM-Cost import + PM-semantiek-spike); slice 68 (**done** — parity-run-alignment)  
**Referentie-fixtures:** `tests/fixtures/RCMCostdata export_CM.xlsx`; `tests/fixtures/RCMCostdata export_Gaarkeuken.rcm.json`  
**Voorbeeld-cause (acceptatie):** `06H-350.1.1.1.1.1.A.1` — drukverlies slangen BINNEN, MTTF=25 jr, IA=2023

## Problem Statement

Bij het importeren van OHS/RCM-Cost Excel-exports (`RCMCostdata export_*.xlsx`) worden **effecten per faalwijze (cause)** en **effecten per preventieve maatregel (REV/IN)** niet volledig en niet conform AW-semantiek in het RCM2-project opgeslagen.

De analist ziet in AW/OHS per cause meerdere effectklassen met verschillende **RedundancyFactor (RF)**-waarden — bijvoorbeeld veiligheidsincident (10% VGM3 + 90% VGM2), hinder bij schutten (0–20%), en totaal functieverlies (81–100% met RF=0,5). De koppeling staat in tabblad **RcmCauseEffectAssignments** (`CEnable`, `PEnable`, `IEnable`, `RedundancyFactor`, `SubIndex`); effectdefinities in **RcmEffects**; een leesbare samenvatting in **RcmCauses.EffectIds** (vrije tekst met optioneel `[RF=…]`).

In RCM2 desktop vandaag:

| Aspect | Huidig gedrag | AW-verwachting |
|--------|---------------|----------------|
| **FM-effectlinks** (`FMEffectLink`) | Grotendeels correct via `CEnable` + `RedundancyFactor` → `fractie` | Meerdere effecten per cause met juiste RF |
| **PM-effectlinks** (`PMEffectLink`) | Alleen bij **exacte** `SubIndex`-match op `RcmScheduledTasks`; `fractie` hardcoded **1.0** | REV/IN-taken krijgen dezelfde effecten met **dezelfde RF** als bij correctief falen wanneer `PEnable`/`IEnable` true |
| **PEnable + IEnable beide true** | Eén gecombineerde taak-resolutie → vaak **geen** of **ambigue** link | Twee scopes (Planned vs Inspection) kunnen elk een eigen PM-link nodig hebben |
| **Ontbrekende SubIndex** | Assignment in `import_settings.isograph_assignments` + waarschuwing; **geen** PM-link | Analist verwacht structurele koppeling naar beschikbare REV/IN-taak |
| **RcmCauses.EffectIds** | **Niet** ingelezen | Audit/validatie tegen assignments; optioneel tonen in importrapport |
| **Voorbeeld-cause** | 4 FM-links met juiste RF; **0** PM-links; unresolved assignment `Schutten 0-20%` SubIndex 2 | PM-effect op REV/IN waar AW `PEnable`/`IEnable` aangeeft |

Gevolg: beschikbaarheids- en effectberekeningen in RCM2 wijken af van AW voor FM's waar PM-uitvoering (REV/IN) systemisch effect heeft op functies — onafhankelijk van de parity-slices 66–68 (die CM-overlay en motorbugs adresseerden).

## Solution

Voer een **import-alignment slice** uit die cause–effect-koppelingen uit AW volledig materialiseert:

1. **Semantiek vastleggen** — herzien slice-35 PM-spike waar nodig: RF op PM-links wanneer AW dat impliceert; beleid voor `PEnable`+`IEnable` dual-scope; SubIndex-fallback wanneer assignment-SubIndex geen scheduled task heeft.
2. **Assignments blijven bron van waarheid** — `RcmCauseEffectAssignments` levert alle `FMEffectLink`/`PMEffectLink`-rijen; `EffectIds` wordt geparsed voor **cross-check en importrapport**, niet als primaire link-bron.
3. **Robuustere PM-resolutie** — meerdere PM-links per assignment wanneer nodig (Planned vs Inspection); fallback naar enige REV/IN op cause wanneer SubIndex ontbreekt (met waarschuwing, niet stilzwijgend).
4. **RF op PM-fractie** — `RedundancyFactor` mappen naar `PMEffectLink.fractie` (analist-verwachting: zelfde RF als bij CM).
5. **Regressie op voorbeeld-cause + CM-fixture** — golden tests; unresolved PM-waarschuwingen dalen meetbaar; FM-editor/verificatie toont complete effectset.
6. **Importrapport** — waarschuwingen en EffectIds-mismatch zichtbaar na import (adapter, geen Qt-smoke verplicht).

Geen wijziging aan analytische motor-formules buiten wat correct geïmporteerde links al beïnvloeden; geen bidirectionele AW-export.

## User Stories

### Analist — correcte effectset na import

1. Als **analist**, wil ik na OHS-import **alle effecten per cause** zien die AW toont, zodat CM-gevolgen kloppen.
2. Als **analist**, wil ik dat **RF per effect** (bijv. 0,1 / 0,9 / 0,5) overeenkomt met AW, zodat veiligheids- en functieverlieskansen juist zijn.
3. Als **analist**, wil ik voor cause `06H-350.1.1.1.1.1.A.1` vier FM-effectlinks (VGM2, VGM3, Schutten 0–20%, Schutten 81–100%) met de juiste fracties, zodat het voorbeeld uit de tool auditbaar is.
4. Als **analist**, wil ik dat **REV-taken** de effecten krijgen waarvoor AW `PEnable=True` heeft, zodat onderhoudsdegradatie meerekent.
5. Als **analist**, wil ik dat **IN-taken** de effecten krijgen waarvoor AW `IEnable=True` heeft, zodat inspectie-effecten niet ontbreken.
6. Als **analist**, wil ik dat **dezelfde RF** geldt voor PM-effecten als voor CM-effecten op dezelfde cause–effect-combinatie, zodat AW en RCM2 één verhaal vertellen.
7. Als **analist**, wil ik in de **FM-editor / verificatie** alle FM- en PM-effectlinks per faalwijze zien, zodat ik import niet in ruwe JSON hoef te controleren.
8. Als **analist**, wil ik een **importrapport** met waarschuwingen over niet-resolved PM-koppelingen, zodat ik weet wat handmatig in AW moet worden gefixt.
9. Als **analist**, wil ik dat **EffectIds** uit RcmCauses wordt vergeleken met geïmporteerde links, zodat stille import-gaps zichtbaar worden.
10. Als **analist**, wil ik dat ontbrekende SubIndex **niet** betekent dat alle PM-effecten verdwijnen wanneer er wel een REV/IN op de cause staat, zodat pragmatische fallback helpt.
11. Als **analist**, wil ik bij **PEnable én IEnable** beide taaktypes gekoppeld krijgen wanneer AW dat aangeeft, zodat geen scope wordt weggelaten.
12. Als **analist**, wil ik na herimport **meetbaar minder** `PM-effect niet geïmporteerd`-waarschuwingen op CM-fixture, zodat voortgang objectief is.
13. Als **analist**, wil ik dat **effectklassen** aan de juiste **functie** hangen na import, zodat PBS/FM-navigatie klopt.
14. Als **analist**, wil ik dat import **geen** kosten per effect uit AW overneemt (ADR-0004), zodat het slanke model behouden blijft.
15. Als **analist**, wil ik dat **Enabled=False** op scheduled tasks de structurele PM-link **niet** blokkeert, zodat koppeling en scenario (overlay) gescheiden blijven.

### Maintainer — importregels en kern

16. Als **maintainer**, wil ik **één module** voor cause–effect importregels (`isograph_pm_import_rules` uitbreiden of sibling), zodat FM en PM dezelfde parsing delen.
17. Als **maintainer**, wil ik `resolve_pm_task_id` vervangen/uitbreiden door **multi-link resolutie** (`resolve_pm_task_ids`), zodat P+I dual-scope testbaar is.
18. Als **maintainer**, wil ik `pm_effect_fractie` afleiden uit `RedundancyFactor` i.p.v. altijd `1.0`, zodat slice-35 spike wordt bijgesteld waar analist dat vereist.
19. Als **maintainer**, wil ik een **parse_effect_ids** helper voor `RcmCauses.EffectIds` (komma-gescheiden, `[RF=0,1]` suffix, NL decimaal), zodat audit los van Excel-layout zit.
20. Als **maintainer**, wil ik dat `_build_effect_links` alle resolved links in één pass opbouwt, zodat geen dubbele logica in de adapter blijft.
21. Als **maintainer**, wil ik **link_id**-conventie stabiel houden (`FMEL|cause|effect|sub`, `PMEL|pm_id|effect`), zodat bestaande projecten mergebaar blijven.
22. Als **maintainer**, wil ik **ambiguous** taak-match nog steeds **geen** link + waarschuwing geven, zodat we geen foute koppelingen raden.
23. Als **maintainer**, wil ik **SubIndex-fallback** alleen bij **exact één** kandidaat REV of IN op cause, zodat ambiguïteit niet wordt verergerd.
24. Als **maintainer**, wil ik unresolved assignments in `import_settings.isograph_assignments` behouden, zodat round-trip en debug mogelijk blijven.
25. Als **maintainer**, wil ik **geen** wijziging aan `CACHE_INPUTS_VERSION` tenzij importgedrag FM-hashes beïnvloedt — PM-link fixes **wel** FM-resultaten; bump na issue-golf.
26. Als **maintainer**, wil ik **ADR-0004** aanvullen met RF-op-PM-besluit, zodat toekomstige agents niet terugvallen op slice-35 “RF niet op PM”.
27. Als **maintainer**, wil ik **editing schema parity** behouden voor `FMEffectLink`/`PMEffectLink`, zodat FM-editor niet breekt.
28. Als **maintainer**, wil ik **engine** ongewijzigd laten tenzij fractie-semantiek op PM expliciet anders moet — import levert correcte `fractie`-waarden.

### Tester — regressie en seams

29. Als **maintainer**, wil ik **synthetische sheet-tests** voor elke resolutie-policy, zodat edge cases zonder zware fixture draaien.
30. Als **maintainer**, wil ik **CM-fixture import** als integratietest, zodat 224 FM / 54+ PM-links en waarschuwing-count bewaakt worden.
31. Als **maintainer**, wil ik een **golden test** op `06H-350.1.1.1.1.1.A.1`, zodat het analist-voorbeeld nooit regressieert.
32. Als **maintainer**, wil ik **unit tests** op `parse_effect_ids` en `pm_effect_fractie`, zodat parsing en RF mapping geïsoleerd testbaar zijn.
33. Als **maintainer**, wil ik **bestaande** `test_isograph_pm_import_rules` en `test_isograph_import_service` groen houden of bewust updaten, zodat slice 35 niet stilletjes breekt.
34. Als **maintainer**, wil ik **geen Qt-smoke** voor importlogica, zodat TDD op adapter/kern blijft (AGENTS.md).
35. Als **maintainer**, wil ik optioneel **run smoke** dat geïmporteerde PM-effectbijdragen > 0 voor voorbeeld-cause, zodat end-to-end effect bereikbaar is.

### Product — scope en communicatie

36. Als **product owner**, wil ik **slice 69** expliciet **import-only** houden, zodat parity-slices 66–68 niet opnieuw openen.
37. Als **trainer**, wil ik in KANBAN_HANDOFF een **before/after** tabel voor CM PM-links, zodat volgende sessie snel kan implementeren.
38. Als **analist**, wil ik begrijpen dat **datakwaliteit in AW** (ontbrekende scheduled task op SubIndex) soms **niet** volledig automatisch opgelost kan worden, zodat verwachtingen realistisch zijn.

## Implementation Decisions

### Prioritering

| Issue | Focus | Kern |
|-------|--------|------|
| **01** | Semantiek-spike + ADR-supplement | RF op PM; P+I dual links; SubIndex-fallback |
| **02** | `EffectIds` parser + import-audit | Cross-check assignments vs Causes-tekst |
| **03** | FM-link regressie & completeness | CEnable + RF; geen regressie op bestaande FM's |
| **04** | PM-resolutie SubIndex-fallback | Unresolved ↓ wanneer één REV/IN kandidaat |
| **05** | PM dual-scope (P+I) | Aparte links per Planned vs Inspection |
| **06** | RF → `PMEffectLink.fractie` | Zelfde `RedundancyFactor` als FM |
| **07** | Golden cause + CM-fixture regressie | `06H-350.1.1.1.1.1.A.1`; waarschuwing-drempel |
| **08** | Importrapport / FM-verificatie UX | Waarschuwingen + EffectIds-mismatch zichtbaar |

### Issue 01 — Semantiek-spike (gate)

- Documenteer in `.scratch/.../EFFECT_SEMANTICS_SPIKE.md` (pattern slice 35 PM_SEMANTICS_SPIKE).
- **Besluit RF op PM:** analist vereist **zelfde RF als CM** op dezelfde assignment-rij → `PMEffectLink.fractie = parse_redundancy_factor(RedundancyFactor)`. Dit **herziet** slice-35 open punt §6.3 (“RF → PM? Nee”) voor OHS-parity.
- **Motor:** `compute_pm_totals` gebruikt al `duration × fractie × executions`; geen engine-wijziging nodig als `fractie` RF draagt.
- **Dual-scope:** wanneer `PEnable` en `IEnable` beide true → zoek **apart** Planned-task en Inspection-task (zelfde SubIndex, of fallback per scope).
- **SubIndex-fallback:** als geen task op assignment-SubIndex: kies **unieke** task in scope (Planned of Inspection) op cause; log waarschuwing `SubIndex-fallback`.
- ADR-0004 aanvulling (korte sectie of linked note in spike).

Prototype-besluit resolutie:

```
for assignment row (cause, effect, sub, RF, flags):
  if CEnable: emit FMEffectLink(fractie=RF)
  if PEnable: for each resolved Planned task: emit PMEffectLink(fractie=RF)
  if IEnable: for each resolved Inspection task: emit PMEffectLink(fractie=RF)
```

### Issue 02 — EffectIds audit

- Parse `RcmCauses.EffectIds` vrije tekst: split op komma; optioneel `[RF=x]` met komma-decimaal.
- Normaliseer effect-id tegen `RcmEffects.Id` / Description.
- Vergelijk verzameling met FM-links uit assignments voor dezelfde cause.
- Mismatch → importwaarschuwing (niet blokkerend); optioneel opslaan in `import_settings.isograph_causes[fm_id].effect_ids_parsed`.

### Issue 03 — FM-links

- Behoud huidige `should_create_fm_effect_link` / `fm_effect_fractie`.
- Regressietest: CM-fixture FM-count en fracties op steekproef causes blijven gelijk of verbeteren.
- Geen gebruik van EffectIds als primaire bron voor link-creatie.

### Issue 04 — SubIndex-fallback

- Nieuwe helper: `resolve_pm_tasks_for_scope(row, tasks, scope)` → `list[task_id]` (0, 1, of many).
- Fallback alleen bij 0 matches op SubIndex **en** exactly 1 task in scope op cause.
- Many matches → geen link + bestaande ambiguous-waarschuwing.

### Issue 05 — Dual-scope P+I

- Vervang single `resolve_pm_task_id` in `_build_effect_links` door iteratie over resolved tasks per scope.
- Link_id blijft uniek per `pm_id` + effect.
- Synthetische test: P+I true, REV SubIndex 0 + IN SubIndex 1 → twee PM-links.

### Issue 06 — RF op PM

- Vervang `pm_effect_fractie_default()` door `pm_effect_fractie(row)` = `parse_redundancy_factor(row.redundancy_factor)`.
- Update CM-fixture test: sample PM-link `fractie` kan < 1.0 zijn waar AW RF < 1.0.

### Issue 07 — Golden regressie

- Test `build_from_workbook(CM)` of Gaarkeuken JSON herimport:
  - Cause `06H-350.1.1.1.1.1.A.1`: 4 FM-links met fracties 0.1, 0.9, 1.0, 0.5; ≥1 PM-link voor effecten met P/I enable waar scheduled task bestaat.
  - `len(warnings)` PM-unresolved daalt t.o.v. baseline 15 (streef ≥ 20% reductie zonder false positives).
- Bump `CACHE_INPUTS_VERSION` na import-gedragswijziging die FM-hashes raakt.

### Issue 08 — Rapportage / verificatie

- Importresultaat: aggregeer waarschuwingen (unresolved, SubIndex-fallback, EffectIds-mismatch).
- FM-verificatie: optioneel PM-effectlinks tonen (read-only) naast FM-links — minimale uitbreiding adapter, geen FM-editor redesign.

## Testing Decisions

### Wat maakt een goede test

- Test **extern gedrag**: `build_from_sheets` / `build_from_workbook` → `project.fm_effect_links`, `project.pm_effect_links`, `result.warnings`, `import_settings`.
- Test **importregels** geïsoleerd in `test_isograph_pm_import_rules.py` (synthetisch, snel).
- Geen assert op private `_build_effect_links` internals; wel op link-aantallen, fracties, en waarschuwingsteksten.
- **Highest seam first:** volledige import via adapter; unit tests alleen voor parsing/resolutie-policies.

### Test-seams (hoog → laag)

| Prioriteit | Seam | Assertie |
|------------|------|----------|
| **1** | `build_from_workbook(CM_FIXTURE)` | FM/PM link counts; warnings ≤ baseline; PM fracties uit RF waar < 1 |
| **2** | Golden cause `06H-350.1.1.1.1.1.A.1` | 4 FM-links + verwachte fracties; PM-links voor P/I-enabled effecten met task |
| **3** | `build_from_sheets` synthetisch | Dual-scope P+I; SubIndex-fallback; ambiguous → geen link |
| **4** | `parse_effect_ids` unit | NL decimaal, meerdere effecten, RF suffix |
| **5** | `run_incremental_analysis` op mini-project | PM-effectbijdragen > 0 wanneer PM-links + RF (optioneel issue 07) |
| **6** | FM-verificatie adapter | Effectlinks zichtbaar na import (issue 08) |

**Besluit (goedgekeurd):** seams 1–4 zijn **adapter/kern** (geen Qt). Seam 5 (motor-smoke) in **issue 07**. Seam 6 in **issue 08**.

### Prior art

- `tests/test_isograph_import_service.py` — CM-fixture, `test_cm_fixture_pm_effect_links_resolved`
- `tests/test_isograph_pm_import_rules.py` — resolutie, ambiguous, disabled task
- `.scratch/rcm-desktop-slice35-rcm-cost-excel-import/PM_SEMANTICS_SPIKE.md` — te herzien in issue 01
- `tests/test_persistence.py` — FM/PM effect link round-trip

### Acceptatie-drempels

- Golden cause: **4 FM-links** met fracties **0.1, 0.9, 1.0, 0.5**; **≥1 PM-link** op cause (na fallback/dual-scope waar AW data het toelaat).
- CM-fixture: PM unresolved warnings **≤ 12** (was 15) zonder FM-link regressie.
- Geen nieuwe ambiguous false positives (warnings met “ambiguous” niet stijgen).
- Bestaande parity-gate tests (slice 66–68) blijven groen.

## Out of Scope

- **Bidirectionele export** naar AW Excel.
- **CostPerOccurrence** / gevolgkosten per effect in RCM2 (ADR-0004).
- **Automatisch AW Enabled → overlay** (slice 35 open punt §6.2).
- **Volledige parity** beschikbaarheid/LCC vs AW Monte Carlo.
- **FM-editor** bewerken van geïmporteerde links (read-only verificatie wel).
- **Handmatig corrigeren** van AW-modellen met ontbrekende scheduled tasks (analist in AW).
- **Portfolio-merge** of validatie-export oorzaakcodes.

## Further Notes

### Huidige baseline (voorbeeld-cause)

Na import Gaarkeuken/CM:

- **FM:** `VGM - Effect 3` RF=0.1; `VGM - Effect 2` RF=0.9; `Schutten 0-20%` RF=1.0; `Schutten 81-100%` RF=0.5 — **correct**.
- **PM:** geen links; assignment `Schutten 0-20%|2` met P+I in `isograph_assignments` — **gap**.
- **REV** op cause: `06H-350.1.1.1.1.1.A.1|REV|0` (SubIndex 0) terwijl assignment SubIndex **2** verwacht.

### Relatie slice 35

Slice 35 PM-spike leverde conservatieve resolutie (exact SubIndex, RF niet op PM). Slice 69 **verruimt** resolutie en **alignet RF op PM** op analist-verzoek. Spike-doc uit slice 35 blijft historisch; slice 69 spike is leidend.

### Risico's

- **RF op PM-fractie** kan PM-effectbijdragen verlagen t.o.v. huidige `fractie=1.0` — gewenst voor AW-alignment; documenteer in spike.
- **SubIndex-fallback** kan verkeerde taak kiezen bij meerdere REV's zonder SubIndex-match — alleen bij unieke kandidaat.
- **Herimport** overschrijft handmatige effect-edits — analist playbook: herimport na AW-wijziging.

### Analist playbook (post slice 69)

1. Exporteer consistent AW-model (`RCMCostdata export_*.xlsx`).
2. Import in RCM2; lees importwaarschuwingen (unresolved / EffectIds-mismatch).
3. Controleer voorbeeld-cause in FM-verificatie: 4 FM + PM-links.
4. Bij unresolved: fix SubIndex/scheduled tasks in AW en herimport.
