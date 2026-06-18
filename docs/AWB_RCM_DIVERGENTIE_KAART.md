# AWB ↔ RCM-desktop: metriekkaart en divergentiepunten

**Datum:** 2026-06-18  
**Branch:** `feat/workspace-rapportage-slice58`  
**Methode:** Parallelle agent-analyse van `rcm_core/engine.py`, `simulation_engine.py`,
`lcc_profile.py`, `failure_parity_validation.py`, `fm_parity_diagnostics.py`,
en alle fixture/Excel-referentiedata.

AWB = Isograph RCM-Cost (Monte Carlo simulatie).  
RCM-desktop = analytische motor (`rcm_core/engine.py`).

---

## 1. Gedeelde metriekkaart

| AWB kolom | RCM-desktop veld | Berekeningslocatie | Tolerantie | Gegateerd? |
|-----------|------------------|--------------------|------------|------------|
| `TotalW` | `FMResult.expected_failures` | `engine.py:compute_fm_result()` + `distributions.py:expected_failures_lifecycle()` | `TotalWErr` (absoluut) | Nee (diagnostisch) |
| `OutageFrequency` × 8760 × lifecycle | `expected_failures` (fallback) | Zelfde als boven; gebruikt als `TotalW` ontbreekt | — | Nee |
| `TotalCost` | `FMResult.total_cost_eur` | `cm_cost_eur + pm_cost_eur` | `max(TotalCostErrAbs, TotalCostErrPc% × TotalCost)` | **Ja** |
| `TotalTdt` | `expected_total_downtime_hr + expected_pm_downtime_hr` | `engine.py:compute_fm_result()` lijnen 244, 250–253 | `TotalTdtErr%` (indien aanwezig) | Als err aanwezig |
| `CTdt` | `expected_total_downtime_hr` (alleen CM) | `raw_downtime + detection_delay_hr` | — | Nee (informatief) |
| `PTdt` | `expected_pm_downtime_hr` | `compute_pm_totals()` | — | Nee (informatief) |
| `InitialAge` (uur) | `current_age` = `modeljaar − PBS.bouwjaar` (jaar) | `engine.py:compute_fm_result()`, invoer | 0,05 jaar | Nee (audit B3) |
| `FmMttf` (uur) | `Faalwijze.mttf_jaar` (jaar) | Import → `isograph_pm_import_rules.py` | 0,001 jaar | Nee (audit B4) |
| `effect_cost` | `EffectImpactService` output | `effect_impact_service.py` | — | Nee (v1 informatief) |
| `ITdt` | **— (niet berekend)** | — | — | Gap: code E3 |

---

## 2. Metriek alleen in RCM-desktop (geen AWB-tegenhanger)

| Veld | Berekening | Doel |
|------|-----------|------|
| `p_failure_lifecycle` | `distributions.py:p_failure_by_age()` | Kans ≥1 falen; risico-dashboard |
| `risk_contribution` | `expected_failures × p_ongewenste_gebeurtenis` | Risicoweging |
| `expected_raw_downtime_hr` | `downtime_per_failure × expected_failures` | CM-doorlooptijd voor LTAP |
| `expected_detection_delay_hr` | `min(IN/TST-interval)/2 × expected_failures` | NMF-verborgen uitval |
| `horizon_profile.hidden_nb_hr` | Verdeeld over detectievenster | LTAP NMF-restpost (ADR-0010) |
| `expected_cm_cost_eur` / `pm_cost_eur` | Kostendecompositie CM vs PM | AWB geeft alleen totaal |
| `effect_bijdragen` per klasse | `expected_failures × fractie` per EffectLink | NB/veiligheid/kosten per klasse |
| MC-banden P10/P50/P90 | `simulation_engine.py:SimulationEngine.run()` | Onzekerheidsmarge |
| `fm_effect_bijdragen_per_jaar` | Distributie over horizonbuckets | LTAP-tijdreeks |

---

## 3. Metriek alleen in AWB (geen RCM-tegenhanger)

| AWB kolom | Betekenis | Actiecode |
|-----------|-----------|-----------|
| `ITdt` | Inspectiestilstand (IN-taken) | E3: RCM2 behandelt IN als kostenpost, geen aparte uitvaltelling |
| `OperationalCost` | Operationele kosten (niet-maintenance) | Niet gemapped; toekomstige extensie |

---

## 4. Alle divergentiepunten

### A — Algoritme (structureel architectuurverschil)

**A1 · Analytisch vs Monte Carlo** (79 FMs in Gaarkeuken-fixture)  
- AWB: stochastische sampling → verwachting via MC-gemiddelde  
- RCM2: Weibull-survival-integraal via SSOT-lus (`distributions.py:expected_aging_lifecycle_faalmomenten_ssot()`)  
- Gevolg: structureel andere uitkomst bij scheefverdeelde Weibull; acceptatiecriterium = waarde binnen AWB-band `TotalW ± TotalWErr`  
- **Geen bug; band-acceptatie is de juiste grens**

**A2 · Lifecycle-horizonsemantics** (`aw_mc_lifecycle_horizon`, `config.py` regel 15)  
- AWB MC: studievenster = `lifecycle_years` jaar vooruit vanaf `t=0` (vaste forward-window)  
- RCM2 oud: studievenster eindigde op absolute leeftijd `lifecycle_years` (ceiling)  
- Fix: default gewijzigd naar `True` in slice 67 → beide nu hetzelfde  
- Divergentiepunt: projecten aangemaakt vóór slice 67 kunnen nog `False` hebben in config  
- Meetbaar effect: `delta_horizon = ef_horizon_forward − ef_cm_overlay` per FM

**A3 · Distributieparametrisatie** (Weibull / Normal / Truncated Normal)  
- AWB importeert `FmDistribution`, `FmStd`, `FmMttf` en past ze intern toe  
- RCM2 gebruikt `aging_distribution`, `sigma_jaar`, `beta_jaar`; conversie via `isograph_pm_import_rules.py`  
- Mogelijke afwijking bij truncated-normal-0 (afgeknipte verdeling; AWB implementatie verschilt)  
- Diagnostiek: `FMParityDiagnostics.distribution_type` vs AWB-kolom `FmDistribution`

**A4 · Random falen — MC-variantie** (13 FMs)  
- AWB simuleert exponentieel-verdeelde interfaalstijden (Poisson-telproces)  
- RCM2: deterministische `(studieduur / MTTF) × multipliciteit`  
- Verwacht: uitkomsten gelijk in verwachting; MC-variantie valt binnen `TotalWErr`  
- **Geen bug; MTTF/multipliciteit controleren is enige actie**

---

### B — Invoermapping (datakoppelingsproblemen)

**B1 · Reparatiekwaliteit default** (was bug vóór slice 67)  
- AWB: exporteert repair_quality niet; AW-default = 1,0 (as-new)  
- RCM2 vóór fix: import-default = 1,0 → 128/135 kostenpariteitsfouten  
- RCM2 na fix (slice 67): import-default = 0,0 (as-old) → correct  
- Divergentiepunt: projecten geïmporteerd vóór de fix kunnen `repair_quality=1,0` hebben  
- Controle: `import_settings.repair_quality_source` moet `"missing_default_0"` zijn

**B2 · REV aging_effect_pct niet geëxporteerd**  
- AWB exporteert `aging_effect_pct` niet (AW-intern 100%)  
- RCM2: `PMTask.from_dict()` defaultt REV-taken altijd op 100% → correct  
- Geen afwijking tenzij RCM2-gebruiker handmatig <100% instelt

**B3 · InitialAge vs PBS bouwjaar** (27 FMs in Gaarkeuken)  
- AWB: `InitialAge` in uren op FM-niveau  
- RCM2: `current_age = modeljaar − PBS.bouwjaar` (jaar); PBS is bovenliggende node  
- Typisch conflict: AWB `InitialAge=44 jr`, RCM2 `bouwjaar` niet ingesteld → `current_age=0`  
- Gevolg: survivalfunctie begint op verkeerde leeftijd → sterk afwijkende ef bij hoge leeftijds/MTTF-ratio  
- Niet gegateerd; gedocumenteerd via `audit_input_parity()` / code B3

**B4 · MTTF/sigma/distributie import** (geen bekende bugs)  
- Afstemming bevestigd: `FmMttf` (uren) → `mttf_jaar` (jaar) binnen 0,001 jaar  
- `FmStd` → `sigma_jaar`; conversiefactor uren/8760 consistent  
- **Geen actie nodig**

**B5 · Multipliciteit/Quantity cascadering**  
- AWB: `Quantity` op FM-niveau, direct gebruikt  
- RCM2: `effective_multiplicity()` cascadeert via PBS-boomhiërarchie (ouder-multipliciteiten × eigen multipliciteit)  
- Divergentiepunt: als PBS-hiërarchie anders geconstrueerd is dan AWB verwacht, wijkt `eff_multiplicity` af  
- Controle: `FMParityDiagnostics.eff_multiplicity` vs AWB `Quantity`

**B6 · TotalW vs OutageFrequency bronselectie**  
- Voorkeur: gebruik `TotalW` als primaire benchmark  
- Fallback: `OutageFrequency × 8760 × lifecycle_years` indien `TotalW` ontbreekt  
- Risico: fallback geeft ander resultaat voor aging FMs (MC-gemiddelde ≠ frequentie × duur)

---

### C — Scenariomismatch (welk scenario wordt berekend)

**C1 · Run ≠ CM-overlay scenario** (25 FMs in Gaarkeuken)  
- AWB-export bevat CM-overlay (235 PM-taken uitgeschakeld via `aw_disabled_pm_ids`)  
- RCM2: als run is uitgevoerd zonder overlay te materialiseren, is `ef_actual ≠ ef_cm_overlay`  
- Meetbaar: `delta_scenario = ef_actual − ef_cm_overlay`; bij |Δ| > 0,5 = actieverpunt  
- Actie: `materialize_cm_overlay_project()` uitvoeren vóór run

**C2 · REV uitgeschakeld in AWB-scenario maar actief in run** (88 FMs)  
- CM-overlay schakelt REV impliciet uit samen met andere PM-taken  
- Als `aw_disabled_pm_ids` REV-taken bevat maar run die niet uitsluit → Δ REV-effect zichtbaar  
- Diagnose: `RevDiagnostics.active_moments` vs `structural_moments`  
- **Secundair signaal; volgt automatisch uit correcte C1-fix**

**C3 · ScheduledTasks-contractfout bij PM-import**  
- AWB exporteert `RcmScheduledTasks`-blad; importregel controleert kolom-contract  
- Schending → taken niet geïmporteerd → PM-kosten te laag, uitval te hoog  
- Controle: `isograph_export_contract.py` validaties bij import

**C4 · Handmatica planning overlay gedrift**  
- Gebruiker heeft overlay handmatig aangepast t.o.v. import-seed  
- Fix: overlay resetten naar `import_settings`-seed

---

### D — REV-motor

**D1 · REV TaskInterval discrepantie**  
- AWB `TaskInterval` ≠ `PMTask.interval_jaar` in RCM2  
- Gevolg: REV-momenten op andere tijdstippen → leeftijdsreset op verkeerde punten  
- Controle: `RevDiagnostics.active_intervals_years` vs AWB `TaskInterval` (uren/8760)

**D2 · REV-motor algoritme** (segment-survival post-slice 66)  
- RCM2 slice 66+: `compute_fm_faalmomenten_per_bucket()` gebruikt segment-survival per REV-interval  
- Mogelijk anders dan AWB's interne renewal-behandeling  
- Gedocumenteerd als architectuurverschil; testverdekking in `test_aging_monte_carlo.py` (5% band)

**D4 · REV op random FM (ongeldig gebruik)**  
- AWB staat REV op exponentieel-verdeelde FM toe; heeft geen effect (memoryless)  
- RCM2 past REV niet toe op `failure_type=random` → uitkomst gelijk  
- **Geen actie nodig**

---

### E — Effectmetriek

**E1 · Effect-metadata niet geïmporteerd**  
- `EffectKlasse`-gegevens ontbreken in import → bijdragen niet berekend  
- Actie: effectklasse-data importeren via desktop-import

**E2 · Eenheid/metriek mismatch**  
- AWB `effect_cost` in EUR; RCM2 `effect_bijdragen` in incidenten of uren afhankelijk van `EffectKlasse.categorie`  
- Conversie vereist eenheidskosten per effectklasse  
- **Informatief in v1 (ADR-0008 / slice 70)**

**E3 · ITdt — inspectiestilstand ontbreekt in RCM2**  
- AWB berekent IN-taken (Inspection) als aparte uitvaltijd  
- RCM2 behandelt IN-taken als kostenpost; geen `ITdt`-equivalent  
- Structureel gat; geen workaround beschikbaar in huidige versie

---

### F — Residuele MC-variantie

**F1 · Uitkomst binnen TotalWErr-band**  
- Verwacht MC-ruis; acceptatiecriterium is band-membership  
- **Geen actie nodig**

**F\* · Overig residu** (sigma/NMF/ongedocumenteerd)  
- Dieper onderzoek nodig; typisch sigma-instelling, NMF-tastinterval, of distributieparameter  
- Advies: `FMParityDiagnostics` uitvoeren en A3/B4-checklist doorlopen

---

## 5. Divergentietelling (Gaarkeuken-fixture, 135 FMs)

| Code | Beschrijving | # FMs | Actieverpunt? |
|------|-------------|-------|---------------|
| A1 | Analytisch vs MC (residual) | 79 | Nee — band-acceptatie |
| A2 | Lifecycle-horizon (nu gefixed) | historisch | Nee — default op True |
| A4 | Random falen MC-variantie | 13 | Nee |
| B1 | Repair quality (nu gefixed) | historisch | Nee — default op 0,0 |
| B3 | InitialAge vs bouwjaar conflict | 27 | Optioneel — invoer harmoniseren |
| C1 | Run ≠ CM-overlay scenario | 25 | **Ja** — overlay materialiseren |
| C2 | REV in overlay uitgeschakeld | 88 | Volgt uit C1-fix |
| E3 | ITdt niet berekend | alle FMs met IN | Structureel gat v1 |
| F* | Overig residu | ~10 | Dieper onderzoek per FM |

**Enige harde actieverpunten:** C1 (25 FMs — overlay materialiseren) en B3 (27 FMs — optioneel bouwjaar harmoniseren).

---

## 6. Gating-logica samengevat

```
ParityVerdict per FM:
  PASS          → TotalCost binnen tolerantie EN TotalTdt binnen TdtErr (indien aanwezig)
  FAIL          → ≥1 gegateerde metriek buiten band
  INFORMATIVE   → geen gegateerde metriek of TdtErr afwezig
  MISSING_BM    → geen AWB-data voor deze FM

Tolerantie TotalCost:
  tol = max(TotalCostErrAbs, TotalCostErrPc/100 × |TotalCost|)
  pass ↔ |actual − AW| ≤ tol

Primaire diagnostische drempel expected_failures:
  pass ↔ |actual − TotalW| ≤ TotalWErr
```

---

## 7. Belangrijkste toegangspunten voor validatierun

| Stap | Locatie | Doel |
|------|---------|------|
| Materialize overlay | `rcm_desktop/adapter/rcm_cost_parity_service.py:materialize_cm_overlay_project()` | C1/C2 elimineren |
| Analytische run | `engine.py:compute_fm_result()` → `FMResult` | expected_failures, costs, downtime |
| MC-run | `simulation_engine.py:SimulationEngine.run()` → `dict[str, FMMCResult]` | P10/P50/P90 bands |
| Parity-check | `failure_parity_validation.py:validate_fm_parity()` | ParityVerdict per FM |
| Diagnostiek | `fm_parity_diagnostics.py:build_fm_parity_diagnostics()` | Counterfactuals per code |
| Invoeraudit | `input_parity_audit.py:audit_input_parity()` | B3/B4/B5 documenteren |
