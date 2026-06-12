# PRD — RCM2 desktop slice 70 (effectcategorie-resultaten, AWB-pariteit)

**Status:** ready-for-agent  
**Versie:** 1.0  
**Triage-labels:** ready-for-agent  
**Type:** Presentatielaag + kern deep module (effect-impact)  
**Parent:** slice **69** (**done** — OHS cause–effect import alignment); slice **33** (Top 10 metrics); slice **57** (functierapport); ADR-0004 (import); ADR-0008 (RCM-Cost parity); `/improve-codebase-architecture` grill-sessie (2026-06-05)  
**Referentie-fixtures:** `tests/fixtures/RCMCostdata export_CM.xlsx`; golden cause `06H-350.1.1.1.1.1.A.1`  
**Analist-bevestiging (2026-06-05):** Slice 69 import werkt — FM-verificatie toont VGM/Schutten met juiste RF; `effect_bijdragen` > 0 in motor. Probleem zit in **resultatenwerkruimte**, niet import.

## Problem Statement

Na slice 69 staan **effecten per faalwijze en preventieve maatregel** correct in het RCM2-project (`FMEffectLink`, `PMEffectLink`, RF). De **analytische motor** berekent `effect_bijdragen` en `effect_bijdragen_per_jaar` per effectklasse. De **resultatenwerkruimte** gebruikt die data vrijwel niet.

De analist ziet in AWB per effectcategorie scores voor niet-beschikbaarheid, veiligheid (VGM), functieverlies (Schutten), enz. — elk met eigen RF. In RCM2 desktop vandaag:

| Aspect | Huidig gedrag | AWB-verwachting |
|--------|---------------|-----------------|
| **Top 10 metric NB** | Totale downtime (CM + PM) per component/faalwijze | Pareto per **effectklasse** (VGM3, Schutten 0–20%, …) |
| **`effect_bijdragen`** | Berekend in motor; alleen ruwe `klasse_id: waarde` in FM-inspector | Leesbare breakdown met RF, eenheid, CM vs PM |
| **Eenheden** | FM-deel = incidenten-equivalent (`expected_failures × RF`); PM-deel = uren — **gemengd** in één dict | Vergelijkbare maat per effectcategorie |
| **KPI / PBS-tabel** | `unavailability_pct` totaal | Opsplitsing per dominante effectcategorie |
| **Functierapport** | Effectnamen in koptekst; Top 10 scoped op PBS-subtree | Scope op FMs gekoppeld aan effecten van die functie |
| **Tijdsplot** | Faalmomenten/NB/kosten | `effect_bijdragen_per_jaar` ongebruikt |
| **AW-pariteit** | `EffectCost` geïmporteerd in `import_settings` | Geen vergelijking RCM2 vs AW per effect |
| **Validatie-export** | Faalmomenten/NB totaal | Geen tab per effectcategorie |

Gevolg: RCM2-resultaten zijn **niet vergelijkbaar** met AWB op effectniveau, ondanks correcte import (slice 69). De metric "Niet-beschikbaarheid" is te smal — één totaal i.p.v. alle AW-effectcategorieën.

## Solution

Voer een **presentatie- en aggregatieslice** uit die effectdata first-class maakt in de resultatenwerkruimte:

1. **Semantiek vastleggen** — wat betekent NB/impact per effect in RCM2 vs AWB; hoe omgaan met gemengde eenheden (HITL gate).
2. **Motor normaliseren** — splits of normaliseer FM- vs PM-effectbijdragen zodat UI één betrouwbare bron heeft.
3. **Deep module `EffectImpactService`** — Qt-vrije aggregatie per effectklasse, categorie, scope en horizon; SSOT voor Top 10, inspector, rapport, export, pariteit.
4. **Top 10 uitbreiden** — bron "Effectklasse"; metric NB verbreden naar per-effect rijen (naast totaal).
5. **Inspector, KPI, PBS, rapport, tijdsplot** — alle consumeren `EffectImpactService`.
6. **AW-pariteit & validatie-export** — informatieve `EffectCost`-vergelijking; effecttab in validatie-export.
7. **Regressie** — golden cause + CM-fixture motor-smoke in **resultaten** (niet alleen import).

Geen wijziging aan slice 69 importregels; geen bidirectionele AW-export.

## User Stories

### Analist — effectcategorieën in resultaten

1. Als **analist**, wil ik in Top 10 **effectklassen** kunnen ranken, zodat ik zie welke effectcategorieën (VGM, Schutten, …) het meest bijdragen.
2. Als **analist**, wil ik **Niet-beschikbaarheid per effectklasse** zien, zodat mijn RCM2-scores vergelijkbaar zijn met AWB.
3. Als **analist**, wil ik voor cause `06H-350.1.1.1.1.1.A.1` **vier effectrijen** (VGM3 RF=0,1; VGM2 RF=0,9; Schutten 0–20%; Schutten 81–100% RF=0,5), zodat het voorbeeld auditbaar is in resultaten — niet alleen in import.
4. Als **analist**, wil ik **RF per effect** in tooltips of subkolommen, zodat ik begrijp hoe incidenten over effecten verdeeld zijn.
5. Als **analist**, wil ik **CM- en PM-bijdrage** per effect gescheiden zien, zodat onderhoudsdegradatie per effectcategorie zichtbaar is.
6. Als **analist**, wil ik **effectcategorieën filteren** (beschikbaarheid, veiligheid, kosten), zodat ik focust op het type gevolg dat AW toont.
7. Als **analist**, wil ik in de **FM-inspector** effectomschrijvingen en eenheden zien i.p.v. ruwe `klasse_id`, zodat ik resultaten kan interpreteren zonder JSON.
8. Als **analist**, wil ik in **KPI-totalen** per scope zien hoeveel impact per dominante effectcategorie zit, zodat PBS-navigatie effectbewust is.
9. Als **analist**, wil ik in het **functierapport** Top 10 en tijdsplot scoped op de FMs die aan die functie-effecten hangen, zodat hoofdstukken consistent zijn met AW-logica.
10. Als **analist**, wil ik in het **functierapport** een tabel per effectklasse binnen de functie, zodat ik niet alleen een totaalpercentage zie.
11. Als **analist**, wil ik in **Tijdsplot** een effectklasse kunnen kiezen, zodat jaarlijkse effectontwikkeling zichtbaar is.
12. Als **analist**, wil ik **NB totaal** (huidig gedrag) behouden als default, zodat bestaande workflows niet breken.
13. Als **analist**, wil ik **Modelcontrole AW** uitbreiden met effectkosten (`EffectCost`) waar AW-data aanwezig is, zodat ik AWB-pariteit per effect kan beoordelen.
14. Als **analist**, wil ik een **validatie-export tab Effectcategorieën**, zodat ik RCM2 vs AW per FM × effect kan analyseren in Excel.
15. Als **analist**, wil ik begrijpen **welke eenheid** een effectscore heeft (incidenten, uren, %), zodat ik niet downtime met incidenten verwar.
16. Als **analist**, wil ik na run op CM-fixture **PM-effectbijdragen in resultaten** zien (niet alleen in ruwe motorvelden), zodat slice 69 PM-links meetbaar impact hebben in de UI.
17. Als **analist**, wil ik **horizon-keuzes** (lifecycle / per jaar / kalenderjaar) ook voor effectmetrics, zodat Top 10 consistent blijft met slice 33.
18. Als **analist**, wil ik **scope-filter** (PBS-subtree) op effectaggregaten, zodat component-analyse per effectcategorie kan.
19. Als **analist**, wil ik **compare A/B** effectbreakdowns kunnen vergelijken waar compare actief is, zodat scenario's effectbewust vergelijkbaar zijn.
20. Als **analist**, wil ik dat **veiligheidseffecten** (VGM) apart van **beschikbaarheidseffecten** (Schutten) gegroepeerd worden, conform AW `Type`-kolom.

### Maintainer — architectuur en deep modules

21. Als **maintainer**, wil ik **`EffectImpactService`** als Qt-vrije deep module, zodat effectlogica niet verspreid blijft over chart-, rapport- en verificatieservices.
22. Als **maintainer**, wil ik **geen duplicatie** tussen `contribution_horizon_value_service` en `report_functie_selection_service` voor effect-FM scope, zodat één SSOT geldt.
23. Als **maintainer**, wil ik **`FMResult.effect_bijdragen` eenheden** expliciet documenteren of splitsen, zodat UI nooit stil gemengde dicts interpreteert.
24. Als **maintainer**, wil ik **`result_view_service`** effectdata doorgeven i.p.v. strippen, zodat PBS-tabel effectkolommen kan tonen.
25. Als **maintainer**, wil ik **`SOURCE_EFFECTKLASSE`** in workspace state, zodat Top 10-bron consistent is met Component/Faalwijze.
26. Als **maintainer**, wil ik **presentatie-cache keys** effect-bron/metric bevatten, zodat stale Top 10 na wissel voorkomen wordt.
27. Als **maintainer**, wil ik **ADR-aanvulling** op effect-metrics semantics, zodat toekomstige agents niet opnieuw downtime/effect verwarren.
28. Als **maintainer**, wil ik **slice 69 import ongewijzigd** laten, zodat import- en presentatieslices gescheiden blijven.
29. Als **maintainer**, wil ik **`CACHE_INPUTS_VERSION` bumpen** alleen wanneer motor-normalisatie (issue 02) FM-hashes beïnvloedt.
30. Als **maintainer**, wil ik **geen Qt in kern/adapter deep modules**, zodat TDD op service-niveau blijft (AGENTS.md).

### Tester — seams en regressie

31. Als **maintainer**, wil ik **golden cause tests** op Top 10 + inspector + aggregatie, zodat vier effectrijen nooit regresseren.
32. Als **maintainer**, wil ik **`test_effect_per_jaar.py` uitbreiden** voor presentatielaag, zodat bucket-reconciliatie bewaakt blijft.
33. Als **maintainer**, wil ik **CM-fixture end-to-end** asserties op zichtbare PM-effecten in resultaten, zodat slice 69 → 70 keten gedekt is.
34. Als **maintainer**, wil ik **bestaande slice 33/57/68/69 tests groen**, zodat Top 10-modi en import niet breken.
35. Als **maintainer**, wil ik **pytest-qt smoke** alleen voor nieuwe UI-toggles (effect-bron, effect-selector), zodat unit tests de bulk dragen.

### Product — scope en verwachtingen

36. Als **product owner**, wil ik **HITL op semantics (issue 01)** vóór UI, zodat we niet op verkeerde eenheden bouwen.
37. Als **trainer**, wil ik **KANBAN_HANDOFF** met before/after screenshots beschrijving (effectrijen zichtbaar), zodat volgende sessie snel kan implementeren.
38. Als **analist**, wil ik weten dat **volledige AW Monte Carlo-pariteit** per effect **niet** in scope is — analytische benadering met duidelijke eenheden wel.

## Implementation Decisions

### Prioritering (13 issues)

| Issue | Focus | Type |
|-------|--------|------|
| **01** | Effect-metrics semantics spike + ADR | HITL |
| **02** | Motor: eenheden normaliseren / splitsen | AFK |
| **03** | Deep module `EffectImpactService` | AFK |
| **04** | Top 10 bron Effectklasse | AFK |
| **05** | Metric NB verbreden per effectcategorie | AFK |
| **06** | FM-inspector leesbare effectresultaten | AFK |
| **07** | KPI-tabel & PBS effectkolommen | AFK |
| **08** | Functierapport effect-aware scope | AFK |
| **09** | Tijdsplot per-effect jaargang | AFK |
| **10** | AW-pariteit EffectCost (informatief) | AFK |
| **11** | Import effect-taxonomie (+ optionele gevolgkosten HITL) | HITL + AFK |
| **12** | Validatie-export effecttab | AFK |
| **13** | Regressie & motor-smoke in resultaten | AFK |

**Aanbevolen volgorde:** 01 → 02 → 03 → (04+05+06 parallel) → 07–09 → 10–12 → 13.

### Issue 01 — Semantiek-spike (gate)

- Documenteer in `EFFECT_METRICS_SEMANTICS_SPIKE.md` (pattern slice 69 spike).
- Beslispunten:
  - CM `effect_bijdragen`: nu `expected_failures × RF` (incidenten-equivalent), **niet** downtime-uren.
  - PM: `duration × RF × executions` (uren).
  - AWB NB per effect: waarschijnlijk downtime × RF of eigen maat — vastleggen wat RCM2 **exposeert** vs **proxy**.
  - Groepering AW `RcmEffects.Type` → `{beschikbaarheid, veiligheid, kosten, …}`.
- ADR-0004/0008 aanvulling: effect-metrics zijn **presentatie-contract**, geen import-wijziging.
- Issues 02–05 implementeren pas na dit document.

### Issue 02 — Motor normalisatie

- Na spike-keuze:
  - **Optie A (voorkeur als spike zegt "transparant"):** splits `fm_effect_bijdragen` / `pm_effect_bijdragen` op `FMResult` (backward-compat: `effect_bijdragen` = som met gedocumenteerde mixed warning, of deprecated).
  - **Optie B:** normaliseer naar **effect-equivalente uren** voor NB-categorie (`RF × downtime_per_failure` voor CM).
- Documenteer eenheid op modelvelden; bump `CACHE_INPUTS_VERSION` indien serialisatie/hash wijzigt.
- Golden cause: vier effectrijen met verwachte RF/waarden na normalisatie.

### Issue 03 — EffectImpactService (deep module)

- Qt-vrij module in kern of adapter (besluit in spike: voorkeur **kern** als alleen `RCMProject` + `FMResult` nodig).
- Prototype-interface:

```
aggregate(
  project, fm_results, *,
  klasse_id | categorie | scope_id,
  metric, horizon, presentation,
) → tuple[EffectImpactRow, ...]

EffectImpactRow:
  klasse_id, label, categorie, rf_display,
  waarde_cm, waarde_pm, waarde_totaal,
  eenheid, share_pct
```

- Consumenten: Top 10, inspector, KPI, rapport, validatie-export, parity — **geen** eigen aggregatielogica elders.
- `collect_fm_ids_for_functie(project, functie_id, kind)` wordt SSOT (vervangt duplicaat in rapport/chart).

### Issue 04 — Top 10 bron Effectklasse

- Nieuwe constante `SOURCE_EFFECTKLASSE` in workspace state.
- `contribution_chart_service.build_contribution_rows` delegeert naar `EffectImpactService` wanneer bron = effectklasse.
- Sub-balk Top 10: `Component | Faalwijze | Effectklasse`.
- RF in tooltip of optionele subkolom.

### Issue 05 — NB per effectcategorie

- **Default:** NB totaal (huidig) ongewijzigd.
- **Nieuw:** bij bron Effectklasse + metric NB → rijen per effectklasse binnen gekozen categorie-filter.
- Filter op `EffectKlasse.categorie` (mapped taxonomy uit issue 11).
- Golden cause: 4 rijen zichtbaar met RF 0,1 / 0,9 / 1,0 / 0,5.

### Issue 06 — FM-inspector

- `fm_verification_service` gebruikt `EffectImpactService` voor resultaat-sectie.
- Tabel: effect | omschrijving | RF | CM | PM | totaal | eenheid.
- Optioneel: mini-jaarreeks uit `effect_bijdragen_per_jaar`.

### Issue 07 — KPI & PBS

- `ScopedKPITotals` uitbreiden of sibling DTO met top-N effectbijdragen.
- `PBSResultRow` / `result_view_service`: `effect_bijdragen` niet strippen.
- PBS-tabel: optionele dynamische kolommen (projectbreed top-N effectklassen).

### Issue 08 — Functierapport scope-fix

- `report_materialization_service` scoped Top 10/tijdsplot op FM-set uit `collect_fm_ids_for_functie`, **niet** op `functie.pbs_id`-subtree alleen.
- Extra sectie: effectklasse-breakdown per functiehoofdstuk.
- Fix slice 57 scope-mismatch.

### Issue 09 — Tijdsplot per effect

- Effect-selector (combobox) in Tijdsplot-modus of overlay.
- Data uit `effect_bijdragen_per_jaar` via `EffectImpactService`.
- Reconciliatie: som buckets ≈ lifecycle-totaal (tolerantie zoals `test_effect_per_jaar.py`).

### Issue 10 — EffectCost-pariteit

- Uitbreiding `rcm_cost_benchmark` of sibling `effect_cost_parity`.
- RCM2-side: waar `cost_gevolg_eur` > 0 → `Σ(effect_bijdragen × cost_gevolg_eur)`; anders incidenten/uren only.
- AW-side: `EffectCost` + err-kolommen uit `import_settings` — **informatief**, geen gate v1 (ADR-0008-stijl).
- UI: Modelcontrole-dialog uitbreiden of sibling tab "Effecten".

### Issue 11 — Effect-taxonomie import

- HITL: heropen ADR-0004 "geen gevolgkosten" **alleen** als analist AW kostenvergelijking per effect vereist.
- AFK: map AW `RcmEffects.Type` → genormaliseerde `EffectKlasse.categorie` enum-achtige strings.
- Optioneel: import `CostPerOccurrence` → `cost_gevolg_eur` na HITL-go.

### Issue 12 — Validatie-export effecttab

- Nieuwe tab "Effectcategorieën" in failure validation export.
- Kolommen: FM, effectklasse, RCM2-waarde, AW-benchmark (indien aanwezig), Δ, cause codes (E1 import, E2 metrics, …).
- Hergebruik `EffectImpactService` + bestaande cause-allocation pattern (slice 68).

### Issue 13 — Regressie

- Golden cause: 4 effectrijen in Top 10 (bron Effectklasse) + inspector.
- CM-fixture: PM-effect zichtbaar in aggregatie (niet alleen `test_slice69` motor-smoke).
- Geen regressie slice 33/57/68/69 parity/import tests.

## Testing Decisions

### Wat maakt een goede test

- Test **extern gedrag**: service-input (`RCMProject`, `RunResult` / `FMResult[]`) → DTO-rijen, Top 10-ranking, export-tabellen.
- Test **geen Qt-layout** voor aggregatielogica; pytest-qt alleen voor nieuwe toggles/comboboxes.
- Assert op **labels, waarden, eenheden, aantallen rijen** — niet private helpers.
- **Highest seam first:** `EffectImpactService.aggregate` + `build_contribution_rows(source=EFFECTKLASSE)` vóór window smoke.

### Test-seams (hoog → laag)

| Prioriteit | Seam | Assertie |
|------------|------|----------|
| **1** | `EffectImpactService.aggregate` | Golden cause 4 rijen; CM vs PM split; scope filter |
| **2** | `build_contribution_rows` + `SOURCE_EFFECTKLASSE` | Top-N ranking; share_pct som ≈ 100% |
| **3** | `contribution_value_for_fm` / NB per effect (issue 05) | Horizon lifecycle vs per jaar |
| **4** | `fm_verification_service` | Leesbare rijen met RF |
| **5** | `select_report_functies` + materialization (08) | FM-scope ≠ PBS-subtree when effect-only FMs |
| **6** | `effect_cost_parity` / benchmark (10) | AW EffectCost vs RCM2 waar data |
| **7** | Failure validation export (12) | Tab aanwezig; cause codes |
| **8** | `build_from_workbook(CM)` + run + aggregate (13) | PM-effect zichtbaar in UI-service layer |
| **9** | pytest-qt workspace smoke | Effect-bron toggle; effect-selector tijdsplot |

**Besluit:** seams 1–4 zijn **kern/adapter** (geen Qt). Seam 9 optioneel in issue 09/04.

### Prior art

- `tests/test_effect_per_jaar.py` — bucket reconciliatie
- `tests/test_desktop_contribution_chart_service.py` — Top 10 ranking
- `tests/test_desktop_contribution_horizon_value_service.py` — horizon/NB
- `tests/test_slice69_ohs_effect_import.py` — golden cause import + motor-smoke
- `tests/test_failure_validation_export.py` — export tabs + cause allocation
- `tests/test_rcm_cost_benchmark.py` — parity band logic
- `.scratch/rcm-desktop-slice33-workspace-top10-modi-metrics/` — metric/bron patterns

### Acceptatie-drempels

- Golden cause `06H-350.1.1.1.1.1.A.1`: **4 effectrijen** in `EffectImpactService` + Top 10 (bron Effectklasse) met RF **0,1 / 0,9 / 1,0 / 0,5**.
- CM-fixture run: **≥1 effectklasse** met PM-bijdrage > 0 in aggregatie (niet alleen ruwe `FMResult`).
- NB totaal (Component/Faalwijze bron): **geen regressie** t.o.v. huidige downtime-metric.
- Slice 69 import tests: **ongewijzigd groen**.
- Parity slice 66–68: **ongewijzigd groen**.

## Out of Scope

- **Bidirectionele export** naar AW Excel.
- **Volledige Monte Carlo-pariteit** per effectcategorie (AWB MC vs RCM2 analytisch).
- **Wijziging slice 69 importregels** (FM/PM links, RF, SubIndex-fallback).
- **FM-editor** bewerken van effectlinks (read-only blijft).
- **Portfolio-merge** effectaggregatie over submodellen.
- **Automatische gate** op EffectCost (alleen informatief v1).
- **CostPerOccurrence import** zonder expliciete HITL-go (issue 11).
- **Verwijderen** bestaande NB-totaal metric.

## Further Notes

### Diagnose (post slice 69, analist bevestigd)

| Laag | Status |
|------|--------|
| Import (69) | FM/PM links + RF ✓ |
| Motor | `effect_bijdragen` + per jaar ✓ |
| UI | Downtime-totaal only ✗ |
| AW-pariteit | EffectCost unused ✗ |

### Relatie architecture review

| Kandidaat | Issue |
|-----------|-------|
| EffectImpactService (deep module) | 03 |
| Motor eenheden | 02 |
| Functierapport scope | 08 |
| SOURCE_EFFECTKLASSE | 04–05 |
| EffectCost-pariteit | 10–11 |

### Risico's

- **Verkeerde eenheid in UI** als issue 01 overgeslagen wordt — **01 is hard gate**.
- **Breaking JSON** als `FMResult` velden splitsen — migration via `from_dict` tolerantie.
- **Performance** bij veel effectklassen — cache in presentation layer; top-N limit.
- **ADR-0004 conflict** bij gevolgkosten-import — alleen na HITL issue 11.

### Analist playbook (post slice 70)

1. Run analyse op geïmporteerd CM-model (slice 69 import + slice 68 CM-overlay default).
2. Top 10 → bron **Effectklasse** → metric **Niet-beschikbaarheid**.
3. Controleer golden cause: 4 effectrijen met RF.
4. Modelcontrole AW → tab Effecten (indien AW EffectCost aanwezig).
5. Validatie-export → tab Effectcategorieën voor Excel-vergelijking met AWB.

### Issues

Zie `issues/INDEX.md` — 13 issues, triage `ready-for-agent` (issue 01: `ready-for-human` tot spike done).
