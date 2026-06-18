# PRD — RCM2 desktop slice 68 (parity-run-alignment + falen5 rapportage)

**Status:** ready-for-agent  
**Versie:** 1.0  
**Triage-labels:** ready-for-agent  
**Type:** AFK (run-pad + validatie-export + documentatie)  
**Parent:** ADR-0008 (RCM-Cost parity); slice 67 (**done** — import/scenario fixes); slice 66 (REV-survival); slice 65 (validatie-export); slice 35 (CM-overlay seed)  
**Referentie-fixtures:** `tests/fixtures/RCMCostdata export_Gaarkeuken.rcm.json`; `tests/fixtures/Modellering door Delta Pi_validatie_falen5.xlsx`  
**Baseline (2026-06-05, validatie_falen5):** 135 FM's — **15 Parity OK**, **25 C1** (run ≠ CM-overlay), **79 A1** (analytisch vs MC, accepteren), **13 A4** (random/MC-residu), **3 B3** (optioneel harmoniseren)

## Problem Statement

Na slice 66 (REV-survival) en slice 67 (repair_quality, CM-overlay helper, audits) verwacht de analist dat een **herimport + run + validatie-export** alleen nog **residuele model-keuzes** (A1/A4) toont — geen configureerbare rekenbugs meer.

De analyse van **validatie_falen5** (140 rijen, Gaarkeuken) laat echter zien:

| Actie (export) | # FM's | Aard |
|----------------|--------|------|
| Band gebruiken; dieper onderzoek sigma/NMF/verdeling | 79 | **Geen bug** — analytisch vs Monte Carlo (A1) |
| Run met CM-overlay materialiseren | 25 | **Actieverpunt** — `ef_actual ≠ ef_cm_overlay` (C1) |
| Geen actie nodig (Parity OK) | 15 | Opgelost |
| MTTF/multipliciteit controleren; rest via MC-band | 13 | **Geen bug** — A4 + MC-residu |
| Optioneel invoer harmoniseren | 3 | Secundair — B3 leeftijd |

De analist kan daardoor:

- Ten onrechte denken dat **128 cost-parity fails** nog steeds “rekenbugs” zijn, terwijl **~79/135** inherent A1 is.
- **25 FM's** zien met dominante **Δ scenario** (C1), terwijl slice 67 in **unit tests** wel `median |Δ scenario| = 0` rapporteert — dus de **desktop run-keten** (validate-venster, cache, overlay-state) wijkt af van wat tests bewijzen.
- Geen **vastgelegde rapportage** hebben van de falen5-conclusie voor stakeholders (“wat is opgelost vs geaccepteerd”).

**Kern:** slice 67 leverde `materialize_cm_overlay_project` en overlay-seed in de werkruimte, maar **niet alle run-entrypoints** garanderen dat `ef_actual` overeenkomt met `ef_cm_overlay` na import. De validatie-export classificeert 79 FM's nog als “probleem” terwijl de aanbevolen actie **band-accepteren** is.

## Solution

Voer een **smalle afsluitende parity-slice** uit:

1. **Run-pad alignment (C1)** — standaard run materialiseert altijd het AW CM-scenario uit `aw_disabled_pm_ids` wanneer dat uit import komt, ongeacht of de analist via validate-venster of werkruimte start; what-if overlay blijft expliciet analist-gedrag bovenop die baseline.
2. **End-to-end regressie** — Gaarkeuken: import → run (adapter) → `build_failure_validation_report`: **≤ 0 FM's** met significante Δ scenario (drempel zoals slice 67); falen5-fixture als regressie-artefact waar nuttig.
3. **Rapportage falen5** — vaste projectdocumentatie met statistieken, uitschieters, en duidelijke scheiding bug vs model-keuze.
4. **A1 band-acceptatie UX** — validatie-export markeert A1-dominante rijen expliciet als **“accepteren binnen AW-band”**, niet als software-actie.
5. **Optioneel B3-hint** — export/wizard hint voor leeftijd-harmonisatie waar AW InitialAge leidend is (geen massa-mutatie).

Geen nieuwe CM-taken in AWB; geen MC-motor; geen default flip van `aw_mc_lifecycle_horizon`.

## User Stories

### Analist — vertrouwen na falen5

1. Als **analist**, wil ik dat na herimport en run **`ef_actual ≈ ef_cm_overlay`** voor alle FM's met CM-overlay, zodat C1 niet meer ten onrechte verschijnt.
2. Als **analist**, wil ik **hetzelfde CM-scenario** ongeacht of ik run vanuit validate-venster of resultatenwerkruimte, zodat validatie-export consistent is.
3. Als **analist**, wil ik dat FM's waar **A1 dominant** is de actie **“Band gebruiken”** krijgen zonder rode “rekenbug”-suggestie, zodat ik focus houd op echte actiepunten.
4. Als **analist**, wil ik een **leesbaar rapport** van de falen5-analyse (15 OK, 25 C1, 79 A1, …), zodat ik stakeholders kan uitleggen wat opgelost vs geaccepteerd is.
5. Als **analist**, wil ik dat **15 Parity OK** FM's groen blijven na run-fix, zodat regressie zichtbaar is.
6. Als **analist**, wil ik bij **optionele B3** (3 FM's) een hint “InitialAge harmoniseren” zonder automatische leeftijdsmutatie, zodat ik bewust kies.
7. Als **analist**, wil ik na run-fix opnieuw validatie-export kunnen draaien en **C1-count ≈ 0** zien, zodat stap 0+1 afgerond is.
8. Als **analist**, wil ik dat **handmatige planning-overlay** (what-if) nog steeds werkt bovenop import-baseline, zodat slice 28/30 niet breekt.
9. Als **analist**, wil ik dat **overlay reset naar import-seed** C4-scenario's herstelt, zodat het playbook uit slice 67 blijft kloppen.
10. Als **analist**, wil ik begrijpen dat **ef_actual = 0 bij over-aged componenten** (10 FM's in falen5) model-gedrag is, zodat ik niet opnieuw een motorfix vraag.

### Maintainer — run-pad en cache

11. Als **maintainer**, wil ik **`run_service.run`** CM-overlay materialiseren wanneer `import_settings.aw_disabled_pm_ids` niet leeg is en geen actieve what-if overlay de disabled-set overschrijft, zodat C1 structureel verdwijnt.
12. Als **maintainer**, wil ik **één materialisatie-pad** (core `cm_overlay` + adapter overlay) zonder duplicatie, zodat counterfactuals en run dezelfde PM-set gebruiken.
13. Als **maintainer**, wil ik dat **incrementele cache** overlay-state meeneemt in invalidatie, zodat een run zonder overlay geen stale `ef_actual` levert na overlay-fix.
14. Als **maintainer**, wil ik **`validate_window` run** dezelfde overlay-default krijgt als werkruimte, zodat analisten niet per ongeluk C1 triggeren.
15. Als **maintainer**, wil ik **`CACHE_INPUTS_VERSION` bumpen** als run-materialisatie FM-resultaten beïnvloedt.
16. Als **maintainer**, wil ik regressie op **Gaarkeuken** (235 disabled PM's) behouden, zodat slice 35/67 niet regresseren.
17. Als **maintainer**, wil ik **falen5.xlsx** als fixture behouden voor aggregatietests (actie-verdeling), zodat UX-wijzigingen meetbaar blijven.

### Tester — seams

18. Als **maintainer**, wil ik een test **`run_service` + Gaarkeuken → validation report** met median `|Δ scenario| < 0.01`, zodat slice 67 unit-only gap gesloten is.
19. Als **maintainer**, wil ik een test **validate-venster run-pad** (adapter-niveau) met overlay-default, zodat entrypoint-parity bewezen is.
20. Als **maintainer**, wil ik **`test_desktop_run_service_materializes_overlay_disabled_pm`** uitbreiden met import-seed scenario, zodat slice 35 + 68 samenhangen.
21. Als **maintainer**, wil ik **`test_failure_validation_export`** uitbreiden met A1-actietekst, zodat band-acceptatie niet per ongeluk verdwijnt.
22. Als **maintainer**, wil ik bestaande **parity-gate** (128 fails ceiling, geen explosies) groen houden, zodat slice 66/67 intact blijven.

### Product / documentatie

23. Als **product owner**, wil ik **slice 68 expliciet out-of-scope A1-parity** houden, zodat scope klein blijft.
24. Als **trainer**, wil ik in het falen5-rapport **uitschieters** (bijv. Δ scenario −120.8 mastenveroudering) als voorbeelden van C1 vóór fix, zodat analisten leren wat ze moeten zien verdwijnen.
25. Als **trainer**, wil ik **ADR-0008 band-criterium** koppelen aan A1-acties in export, zodat TotalW ± TotalWErr leidend blijft.
26. Als **analist**, wil ik **KANBAN_HANDOFF** na slice 68 met reproduceerbare checks, zodat volgende sessie direct kan implementeren.

## Implementation Decisions

### Prioritering

| Issue | Focus | Oorzaak | AWB CM? |
|-------|--------|---------|---------|
| **01** | Run-pad CM-overlay default materialisatie | C1 (25 FM's) | Nee |
| **02** | E2E regressie validatie-export Δ scenario | C1 bewaking | Nee |
| **03** | Falen5 analyse-rapport in repo | stakeholdercommunicatie | Nee |
| **04** | A1 band-acceptatie in export-acties | A1 (79 FM's) UX | Nee |
| **05** | Optioneel B3 leeftijd-hint | B3 (3 FM's) | Nee |

### Issue 01 — Run-pad alignment (C1)

- **Module:** `run_service` (adapter); hergebruik `rcm_core.cm_overlay.materialize_cm_overlay_project` of equivalent via `PlanningOverlayState.from_import_settings`.
- **Besluit:** Wanneer `aw_disabled_pm_ids` aanwezig is:
  - **Default:** materialiseer disabled PM's vóór `run_incremental_analysis`, tenzij expliciete what-if overlay met andere `disabled_pm_ids` actief is.
  - **Validate-venster:** seed overlay uit import vóór run **of** run_service past import-default toe zonder UI-state.
- **Geen** wijziging aan counterfactual-logica in `failure_parity_validation` — die gebruikt al `_disabled_pm_ids(project)`.
- **Cache:** overlay-disabled-set hash moet cache-invalidatie triggeren (bestaand overlay-mechanisme uitbreiden indien nodig).

Prototype-besluit run-resolutie:

```
disabled = (
    planning_overlay.disabled_pm_ids
    if planning_overlay and planning_overlay.active
    else aw_disabled_pm_ids(project)
)
if disabled:
    run_project = materialize_without_disabled(project, disabled)
```

### Issue 02 — E2E regressie

- Test via **adapter seam** (geen Qt-smoke verplicht): `run_service.run(Gaarkeuken, overlay=from_import)` → FM results → `build_failure_validation_report`.
- Drempel: **0 FM's** met `|Δ scenario| > max(TotalWErr, 5%×TotalW)` **of** median < 0.01 (slice 67).
- Optioneel: parse falen5 baseline — na fix, regeneratie moet C1-actie-count **≤ 1** (afronding).

### Issue 03 — Rapportage

- Vast document: `.scratch/rcm-desktop-slice68-parity-run-alignment/ANALYSE_VALIDATIE_FALEN5.md` (of `docs/analysis/`) met tabellen uit terminal-analyse, uitschieters, conclusie bug vs model-keuze.
- Geen secrets; fixture-xlsx blijft in `tests/fixtures/`.

### Issue 04 — A1 UX

- **Module:** `failure_validation_export_service` cause allocation / `recommended_action` voor dominante factor **residu** + cause A1.
- Actietekst: **“Accepteren: vergelijk met AW-band (TotalW ± TotalWErr); geen softwarefix”** i.p.v. impliciete fail-markering als enige handvat.
- Celmarkering: A1+binnen-band → geen rood op `ef_actual` (informatief groen/grijs).

### Issue 5 — B3 hint (optioneel, laag)

- Waar `audit_input_parity` InitialAge-mismatch + B3 code: export-actie **“Optioneel: harmoniseer leeftijd met AW InitialAge (invoer)”**.
- Geen auto-write naar PBS-leeftijd.

## Testing Decisions

### Wat maakt een goede test

- Test **gedrag via publieke adapter/core seams**: `run_service.run` → `FMResult.expected_failures` → validation report rijen.
- Geen assert op private import-helpers; wel op **Δ scenario** en **recommended_action** teksten waar UX-scope.
- Falen5 als **optionele baseline snapshot** (parse xlsx), niet als golden file voor alle kolommen.

### Test-seams (hoog → laag)

| Prioriteit | Seam | Assertie |
|------------|------|----------|
| **1** | `run_service.run` + Gaarkeuken + import overlay | Alle FM's: `|ef_actual − ef_cm_overlay| < 0.01` |
| **2** | `run_service.run` zonder expliciete overlay (validate-pad) | Zelfde als (1) — bewijst default materialisatie |
| **3** | `build_failure_validation_report` na (1) | Geen rij met actie “Run met CM-overlay materialiseren” |
| **4** | `allocate_validation_causes` / export | A1-dominant → band-acceptatie actie |
| **5** | `test_gaarkeuken_parity_gate` | Geen explosies; fail_count ≤ 128 (residu) |

**Check met gebruiker:** deze seams zijn bewust **adapter/core** (geen Qt-smoke). Als je een smoke-test validate→export in de UI wilt, kan die als optionele issue-06 follow-up.

### Prior art

- `tests/test_slice67_parity_rekenbugs.py` — `materialize_cm_overlay_project` + analytical (unit-only gap)
- `tests/test_desktop_run_service.py` — `test_run_service_materializes_overlay_disabled_pm`
- `tests/test_import_overlay_seed.py` — `PlanningOverlayState.from_import_settings`
- `tests/test_failure_validation_export.py` — export + marking
- `tests/fixtures/Modellering door Delta Pi_validatie_falen5.xlsx` — falen5 baseline

### Acceptatie-drempels

- Issue 01+02: **C1-actie-count = 0** op verse Gaarkeuken run + export (135 FM's)
- Issue 04: ≥ 90% A1-dominante rijen (mock of falen5 parse) krijgen band-acceptatie actie
- Issue 05: B3-hint alleen waar InitialAge-mismatch; geen side effects op project JSON

## Out of Scope

- **Volledige MC-parity** (79 A1-FM's) — band blijft voldoende per ADR-0008.
- **Cost-parity fail_count verlagen onder 128** — rest is A1/A2/A4 residu; geen stretch ≤40 uit slice 67 PRD in deze slice.
- **Automatische leeftijd-harmonisatie** (B3 mass update).
- **Nieuwe CM-taken in AWB** of REV-scenario wijzigingen in AW.
- **Portfolio-merge gate** (slice 64).
- **Qt-smoke validatie-export dialoog** (tenzij expliciet toegevoegd als issue 06).

## Further Notes

### Relatie slice 67

Slice 67 bewees CM-overlay alignment **in tests** via `materialize_cm_overlay_project(project)` vóór `run_analytical`, maar falen5 toont dat **de analist-run** nog 25× C1 kan produceren. Slice 68 sluit de **productie-run-keten**.

### Falen5 uitschieters (C1 vóór fix)

| FM | Δ scenario | Notitie |
|----|------------|---------|
| 06H-350.3.5.9.1.A.1 | −120.8 | mastenveroudering, mult=114 |
| 06H-350.3.3.7.1.A.1 | +40.9 | SCADA, leeftijd=12, MTTF=7 |
| 06H-350.3.13.4.1.A.1 | +28.6 | niveaumeetsysteem |

Na issue 01 moeten deze Δ scenario ≈ 0 worden op verse run.

### Over-aged ef_actual = 0 (10 FM's)

Weibull survival → 0 verwachte falen wanneer leeftijd >> MTTF. AW MC kan andere conventie hebben. **Geen motorfix** in slice 68; vermelden in rapport + optioneel footnote in export-legenda.

### Analist playbook (post slice 68)

1. Herimport AW Excel.
2. Run (validate of werkruimte — beide CM-aligned).
3. Validatie-export: verwacht **~79× band-accepteren (A1)**, **~0× CM-overlay materialiseren**, **~15× Parity OK**.
4. Optioneel: `aw_mc_lifecycle_horizon` voor A2-residu (slice 67 playbook).

### Risico's

- **Dubbele materialisatie** als overlay actief én import-default — run-resolutie moet what-if overlay laten prevaleren.
- **Cache stale results** — bump + overlay in cache key.
- **Validate vs workspace** gedrag — centraliseer in `run_service`, niet in views.
