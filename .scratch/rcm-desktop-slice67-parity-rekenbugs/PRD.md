# PRD — RCM2 desktop slice 67 (parity-rekenbugs: import, scenario, invoer)

**Status:** ready-for-agent  
**Versie:** 1.0  
**Triage-labels:** ready-for-agent  
**Type:** AFK (import + motor + parity-gate)  
**Parent:** ADR-0008 (RCM-Cost parity); slice 65 (modelcontrole + validatie-export); slice 66 (**done** — REV-segment survival); slice 52 (`aw_mc_lifecycle_horizon`); slice 35 (Excel-import)  
**Referentie-fixtures:** `tests/fixtures/RCMCostdata export_Gaarkeuken.rcm.json`; validatie-export `Modellering door Delta Pi_validatie_falen*.xlsx`  
**Baseline (2026-06-05):** Gaarkeuken — **128/135** cost-parity fails; validatie-export **114/139** # falen-fails; **42× B1**, **32× A1**, **24× A2** primair

## Problem Statement

Analisten die AW-projecten importeren en **modelcontrole AW** (ADR-0008) of **validatie-export** (# falen) gebruiken, zien systematische afwijkingen tussen RCM2 en AW — vooral **RCM2 telt te weinig falen** en **TotalCost** wijkt af. Na slice 66 (REV-survival motorfix) verdwenen astronomische `expected_failures`-explosies, maar **de overgrote meerderheid van parity-fails blijft**.

De analist kan daardoor:

- Niet betrouwbaar beoordelen of een FM “groen” is na import.
- Ten onrechte concluderen dat verschillen “inherent Monte Carlo vs analytisch” zijn, terwijl **import-, scenario- en invoerbugs** het beeld domineren.
- Tijd verliezen aan handmatige FM-voor-FM correcties zonder prioriteit op **structurele fixes** (geen nieuwe CM-taken in AWB nodig).

**Geverifieerde bevindingen (validatie-export v1→v3, Gaarkeuken):**

| Oorzaakcode | Primair (bij fail) | Kern | AWB CM-taak nodig? |
|-------------|-------------------|------|--------------------|
| **B1** | ~42 | `repair_quality` blijft **1.0** (as-new default); AW export bevat geen gemapte kolom → RCM2 telt te weinig CM-falen | **Nee** |
| **A2** | ~24 | LifeTime-semantiek: RCM2 resterende studieduur vs AW volledige LifeTime (`TotalW`) | **Nee** (checkbox slice 52) |
| **A1** | ~32 | Analytisch vs Monte Carlo — residu binnen AW-band | **Nee** (accepteren) |
| **A4** | ~13 | Random falen / MTTF / multipliciteit + MC-residu | **Nee** |
| **B2** | enkele | REV `aging_effect_pct` niet overal 100% na import | **Nee** |
| **C1/C4** | enkele | Run wijkt af van CM-overlay-seed | **Nee** |
| **B3–B5, D1–D2** | rest | Invoer- en REV-planning parity | **Meestal nee** |

**Slice 66 (afgerond)** loste één **motor-rekenbug** op (stale REV-segment survival); residuele 128 fails zijn **geen explosies** meer maar echte import/scenario/invoer-gaps.

## Solution

Voer een **geprioriteerde rekenbug-roadmap** uit — eerst alles wat **zonder nieuwe CM-taak in AWB** kan:

1. **Import-correctheid** — `repair_quality` en REV `aging_effect_pct` betrouwbaar uit AW Excel; expliciete fallback-policy wanneer kolommen ontbreken; regressie op Gaarkeuken-fixture.
2. **Scenario-alignment** — run-resultaten consistent met CM-overlay (`aw_disabled_pm_ids`); `ef_actual` ≈ `ef_cm_overlay` wanneer overlay uit import komt.
3. **Horizon-productkeuze** — `aw_mc_lifecycle_horizon` blijft **default False**; analist-handboek + optionele import-hint (niet auto-flip).
4. **Invoerparity** — InitialAge→leeftijd, MTTF/sigma/verdeling, Quantity/multipliciteit audit + fixes waar afwijkingen structureel zijn.
5. **REV-planning parity** — interval/momenten waar D1/D2 counterfactuals domineren (binnen bestaande import, geen AWB).
6. **Parity-gate aanscherpen** — na fixes: Gaarkeuken `fail_count` en validatie-export fail-count **dalen meetbaar**; drempels in regressietests finetunen.
7. **Residu accepteren** — A1/A4/F1 expliciet buiten “rekenbug”-scope; band-gebaseerde pass blijft ADR-0008.

Geen UI-redesign; wel modelinstellingen/import-wizard waar nodig voor correcte defaults.

## User Stories

### Analist — vertrouwen en workflow

1. Als **analist**, wil ik dat na AW-import **`repair_quality` overeenkomt met AW** (typisch as-old ≈ 0), zodat # falen niet structureel te laag is.
2. Als **analist**, wil ik dat REV-taken **`aging_effect_pct=100%`** krijgen wanneer AW dat impliceert, zodat REV-rejuvenatie klopt.
3. Als **analist**, wil ik **`aw_mc_lifecycle_horizon` bewust kunnen inschakelen** (slice 52) na motorfixes, zodat # falen beter aansluit bij AW `TotalW`-semantiek.
4. Als **analist**, wil ik dat mijn **run het CM-scenario volgt** dat bij import is vastgelegd, zodat validatie-export `ef_actual` niet misleidt t.o.v. `ef_cm_overlay`.
5. Als **analist**, wil ik dat **modelcontrole AW** na structurele fixes **merkbaar meer groen** toont op Gaarkeuken, zodat ik FM’s hoef te filteren op “obvious bugs”.
6. Als **analist**, wil ik in validatie-export **duidelijke oorzaakcodes** die na fixes verschuiven van B1/A2 naar A1/residu, zodat restverschil interpreteerbaar blijft.
7. Als **analist**, wil ik **geen nieuwe CM-taken in AWB** hoeven aanmaken voor de eerste golf fixes, zodat ik in RCM2 kan blijven werken.
8. Als **analist**, wil ik een **korte playbook** (herimport, horizon, overlay reset), zodat “stap 0” niet opnieuw misgaat.

### Maintainer — import en motor

9. Als **maintainer**, wil ik **kolom-discovery** voor repair quality op echte AW-exports (CorrectiveTasks, Causes, Project), zodat B1-fixtures niet alleen synthetische Excel dekken.
10. Als **maintainer**, wil ik een **documenteerde fallback** wanneer AW geen repair-quality kolom heeft (bijv. default 0.0 i.p.v. impliciet 1.0), zodat gedrag expliciet en testbaar is.
11. Als **maintainer**, wil ik dat **aging_effect_pct** op REV-taken uit ScheduledTasks/CauseEffectAssignments komt met AW-default 100%, zodat B2 verdwijnt.
12. Als **maintainer**, wil ik **InitialAge → PBS-leeftijd** consistent mappen en conflicten via wizard blijven oplossen, zodat B3 afneemt.
13. Als **maintainer**, wil ik **MTTF/sigma/verdeling** (uren→jaren, FmDistribution) geaudit tegen `import_settings.isograph_causes`, zodat B4 meetbaar daalt.
14. Als **maintainer**, wil ik **Quantity/multipliciteit** alignen met AW waar kolommen bestaan, zodat B5 niet stilletjes faalmomenten schaalt.
15. Als **maintainer**, wil ik **REV-intervallen** (`TaskInterval`) en actieve REV-telling gelijk trekken met AW CM-scenario, zodat D1/D2 counterfactuals kleiner worden.
16. Als **maintainer**, wil ik **`CACHE_INPUTS_VERSION` bumpen** na elke motor/import-wijziging die FM-hashes beïnvloedt.
17. Als **maintainer**, wil ik dat slice-66 REV-survival fix **ongewijzigd groen** blijft, zodat regressie niet terugkomt.

### Tester — regressie

18. Als **maintainer**, wil ik een **Gaarkeuken-import regressietest** die assert dat minstens één FM `repair_quality < 1.0` heeft na import van de echte export-fixture (of expliciet gedocumenteerde fallback), zodat B1 niet terugkomt.
19. Als **maintainer**, wil ik een **validatie-export aggregatietest** (cause-code verdeling of fail-count drempel), zodat voortgang meetbaar is.
20. Als **maintainer**, wil ik **`build_parity_report` fail_count** op Gaarkeuken te monitoren met aangescherpte drempel na issue-golf 1–3, zodat ADR-0008 end-to-end bewaakt.
21. Als **maintainer**, wil ik **counterfactual-tests** uitbreiden (`ef_actual` vs `ef_cm_overlay`, `ef_rq_0`), zodat scenario/import bugs vroeg worden gevangen.
22. Als **maintainer**, wil ik bestaande **`test_isograph_import_service`**, **`test_failure_parity_validation`**, **`test_gaarkeuken_parity_gate`** groen houden.

### Product / scope

23. Als **product owner**, wil ik **prioriteit 1 = import + scenario zonder AWB**, zodat analisten snel waarde zien.
24. Als **product owner**, wil ik **A1 MC-residu niet als rekenbug** behandelen, zodat scope niet explodeert naar volledige MC-parity.
25. Als **trainer**, wil ik documentatie dat **AW-brondata** (bijv. ongeldig uitvoeringsjaar / achterstallig onderhoud) parity kan verstoren vóór RCM2, zodat analisten eerst AW-invoer valideren.

### Scope-afbakening

26. Als **analist**, accepteer ik dat **volledige MC-parity** (A1) **buiten scope** blijft, zodat slice 67 import/scenario/invoer fixeert en niet de analytische motor vervangt.
27. Als **analist**, accepteer ik dat **nieuwe CM-taken genereren in AWB** **niet** vereist is voor slice 67, zodat C2-scenario’s met extra REV in AW buiten de eerste golf blijven.

## Implementation Decisions

### Prioritering (implementatievolgorde)

| Golf | Focus | Oorzaakcodes | AWB CM? |
|------|--------|--------------|---------|
| **0 (done)** | REV-segment survival motorfix | explosies | Nee |
| **1** | Repair quality import + fallback policy | B1, E1 | Nee |
| **2** | REV `aging_effect_pct` import + default 100% | B2 | Nee |
| **3** | CM-overlay run alignment (`ef_actual` ≈ overlay) | C1, C4 | Nee |
| **4** | Horizon playbook + import hint (geen default flip) | A2 | Nee |
| **5** | Invoerparity InitialAge, MTTF, Quantity | B3, B4, B5 | Nee |
| **6** | REV-interval / planning parity | D1, D2 | Meestal nee |
| **7** | Parity-gate drempels + documentatie | alle | Nee |

### Golf 1 — Repair quality (B1)

- **Module:** Isograph importmapper (faalwijze-constructie uit Causes + CorrectiveTasks).
- **Besluit:** Breid kolom-discovery uit op echte Gaarkeuken-export; log in `import_settings` welke bron is gebruikt.
- **Fallback (prototype-besluit):**

```
if repair_quality_column_present:
    map AW → repair_quality ∈ [0, 1]
else:
    repair_quality = 0.0   # AW CM-default as-old; expliciet i.p.v. Faalwijze-default 1.0
```

- **Migratie:** bestaande `.rcm.json` zonder veld → herimport of expliciete “pas defaults toe”-actie (geen stille massa-mutatie zonder analist).

### Golf 2 — REV aging effect (B2)

- **Module:** ScheduledTasks-import; REV `aging_effect_pct`.
- **Besluit:** Map AW rejuvenation-kolommen; waar afwezig: **100%** voor REV (AW-default), niet 0%.
- **Consistentie:** zelfde `_parse_pct_0_100`-pad als slice 35-tests.

### Golf 3 — CM-overlay alignment (C1/C4)

- **Module:** planning overlay state + run pad (`run_incremental_analysis` / `engine`).
- **Besluit:** Wanneer `aw_disabled_pm_ids` uit import komt, moet standaard run **dezelfde PM-set** gebruiken als counterfactual `ef_cm_overlay`; handmatige overlay-reset naar import-seed blijft analist-actie.
- **Diagnostiek:** validatie-export `Δ scenario` ≈ 0 na fresh import + run.

### Golf 4 — Horizon (A2)

- **Geen default wijziging:** `aw_mc_lifecycle_horizon=False` blijft (slice 66).
- **Besluit:** modelinstellingen-dialog tooltip/playbook; optioneel import-metadata flag “AW gebruikt LifeTime-forward” **alleen informatief**, geen auto-enable.

### Golf 5–6 — Invoer en REV

- Audit-rapport of unit tests per dimensie (leeftijd, MTTF, Quantity, TaskInterval).
- Fixes alleen waar systematische afwijking t.o.v. `import_settings.isograph_causes` bewezen is.

### Golf 7 — Parity-gate

- **`build_parity_report`:** streef Gaarkeuken `fail_count` **≤ 40** na golf 1–3 (finetune); **≤ 20** na golf 5–6 — conservatief starten na eerste groene run.
- **Validatie-export:** streef # falen-fails **≤ 60** na golf 1–4 (baseline 114).

### Issues-splitsing

| Issue | Inhoud |
|-------|--------|
| **01** | Repair quality: kolom-discovery + fallback 0.0 + Gaarkeuken import regressie |
| **02** | REV aging_effect_pct: import + default 100% + regressie |
| **03** | CM-overlay run alignment + `Δ scenario` ≈ 0 test |
| **04** | Horizon playbook + modelinstellingen hint (docs/light UI copy) |
| **05** | Invoerparity audit (InitialAge, MTTF, Quantity) + gerichte fixes |
| **06** | REV-interval parity (D1/D2) waar dominant |
| **07** | Parity-gate drempels + KANBAN_HANDOFF + analist playbook |

## Testing Decisions

### Wat maakt een goede test

- Test **extern gedrag**: geïmporteerd project → run → parity/validatie-uitkomsten; geen private import-helper asserts tenzij geen seam bestaat.
- Gebruik **Gaarkeuken-fixture** en waar mogelijk **echte AW Excel** (skipif als vertrouwelijk ontbreekt).
- Counterfactuals via **`build_failure_validation_report`**; cost gate via **`build_parity_report`**.

### Test-seams (hoog → laag)

| Prioriteit | Seam | Assertie |
|------------|------|----------|
| **1** | Isograph import → `RCMProject.faalwijzen[].repair_quality` | Niet alles 1.0 op Gaarkeuken; fallback gedocumenteerd |
| **2** | Import → REV `aging_effect_pct` | REV-taken 100% waar AW default |
| **3** | `build_failure_validation_report` | `ef_actual ≈ ef_cm_overlay` na fresh import-run; `Δ scenario` klein |
| **4** | `build_failure_validation_report` | B1-count ↓ op fixture; `ef_rq_0` dichter bij AW |
| **5** | `build_parity_report` (Gaarkeuken) | `fail_count` onder issue-drempel; geen `ef_rcm > 10⁴` (slice 66) |
| **6** | `test_isograph_import_service` | Bestaande repair_quality/aging tests groen |

**Geen** Qt-smoke voor rekenlogica; **geen** nieuwe MC-run productiepad.

### Prior art

- `tests/test_isograph_import_service.py` — repair_quality, aging_effect_pct
- `tests/test_failure_parity_validation.py` — counterfactuals
- `tests/test_gaarkeuken_parity_gate.py` — slice 66 parity gate
- `tests/test_rev_segment_survival.py` — motor REV (regressiebewaking)
- `rcm_desktop/adapter/failure_validation_export_service.py` — oorzaakcatalogus A–F

### Acceptatie-drempels (voorstel, finetune per issue)

- Golf 1: ≥ 1 FM met `repair_quality < 0.99` op Gaarkeuken **of** expliciete `import_settings.repair_quality_source=missing_default_0`
- Golf 3: median `|Δ scenario| < 0.01` op FM’s met CM-overlay
- Golf 7: `fail_count ≤ 40` (tussendoel), daarna `≤ 20` (stretch)

## Out of Scope

- **Volledige Monte Carlo-parity** (A1) — band blijft voldoende; seeded MC productiepad is toekomst.
- **Nieuwe CM-taken in AWB** genereren of scenario’s wijzigen in AW.
- **Automatisch `aw_mc_lifecycle_horizon=True`** bij import.
- **Portfolio-merge projecttotaal-gate** (slice 64).
- **AW UI-validatie** (bijv. ongeldig uitvoeringsjaar / JVU — brondata in AW corrigeren is analist-taak in AW, niet RCM2-code).
- **Bidirectionele sync** RCM2 ↔ AW.

## Further Notes

### Relatie slice 66

Slice 66 fixte **motor-rekenbug** (REV-segment survival). Slice 67 adresseert **resterende 128/135 cost-fails** en **114/139 # falen-fails** — dominant **import + semantiek**, niet explosies.

### Causaliteitsketen (typisch B1 + A2)

```
AW export zonder gemapte repair_quality
  → RCM2 default repair_quality = 1.0 (as-new)
  → CM-falen resetten leeftijd volledig
  → expected_failures RCM2 << AW TotalW
  + kortere studieduur zonder aw_mc_lifecycle_horizon
  → dubbele onderschatting # falen
  → validatie-export: B1 + A2 dominant
```

### Analist playbook (samenvatting)

1. Herimport AW Excel (`RCMCostdata export_*.xlsx`, niet validatie-xlsx).
2. Modelinstellingen: **AW MC-horizon** aan indien # falen vs TotalW leidend is.
3. Run → modelcontrole → validatie-export; controleer oorzaakcodes.
4. Overlay reset naar import-seed als C4 dominant.

### AW-brondata (screenshot-context)

Ongeldige planning in AW (bijv. uitvoeringsjaar < huidig jaar, “faaloorzaak niet volledig”) kan **REV/PM-seeds** in de export vervuilen. RCM2 kan dat niet repareren; analist moet AW-model eerst consistent maken vóór export.

### Risico’s

- **Gaarkeuken-export zonder repair_quality-kolom** → fallback-policy is productbesluit; documenteer in ADR/import-matrix.
- **Te strakke fail_count-drempel** → finetune na eerste groene run per golf.
- **Herimport breaking handmatige edits** → playbook waarschuwt; geen stille overwrite zonder wizard.
