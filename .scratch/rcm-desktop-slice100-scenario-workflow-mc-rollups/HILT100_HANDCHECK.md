# HILT100 — Handcheck scenario-workflow v2 + MC P50-rollups

**Issue:** slice 100 issue 09  
**Datum:** 2026-06-13  
**Status:** completed (HILT overgeslagen — productbesluit 2026-06-16; oorspronkelijk NO-GO LCC-curves)

## Doel

Visuele QA van slice 100 op demo-project: unified **Start analyse**, **Extra scenario**,
**Vergelijk scenario's**, MC P50 in Top 10/LCC/FM-resultaten, en verwijdering Run A/B.

## Voorbereiding

1. Start resultatenwerkruimte (`python -m rcm_desktop.main`).
2. Open demo-project: `tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json`.
3. Run-modus **Monte Carlo**; `monte_carlo_n` ≥ 1000 (modelinstellingen).

## Stappen

1. **App laden**
   - [x] Project opent zonder foutmelding
2. **Start analyse** (MC-modus)
   - [x] MC-run voltooid; FM-resultaten tonen P50 + banden (P10/P90 tooltip)
   - [x] Top 10 en LCC tonen waarden (P50-rollup)
   - [ ] **BLOCKING:** LCC/NB jaarlijkse curves vlak (zelfde waarde elk jaar); analytische runs tonen normale aging-curves
3. **Extra scenario**
   - [x] Scenario 1 bevroren; scenario 2 pre-run config geopend
4. **Scenario 2 run** (MC)
   - [x] Run voltooid; live run = scenario 2
5. **Vergelijk scenario's**
   - [x] Top 10 vergelijking werkt
   - [x] LCC vergelijking werkt (maar jaarcurves vlak — zie blocking)
   - [x] FM-resultaten vergelijking werkt
6. **Wis vergelijking**
   - [x] Scenario-slots gewist; vergelijking uit
7. **Run A/B verwijderd**
   - [x] Geen Run → A / Run → B knoppen

## Blocking issue

**LCC/NB jaarlijkse distributie vlak na MC-run**

| Observatie | Analytisch | MC P50 |
|------------|------------|--------|
| LCC CM jaarcurve | Aging-curves (piek rond MTTF) | Vlak (constant per jaar) |
| NB jaarcurve | Variatie over horizon | Vlak |

**Diagnose:** `fm_results_from_mc_p50` in `simulation_engine_service.py` bouwt synthetische
`FMResult`-rijen uit MC P50-banden (faalmomenten, downtime, kosten) maar **vult geen
`horizon_profile`**. LCC/NB views lezen bucket-data via `build_cm_eur_per_bucket` /
`build_cor_eur_per_bucket` in `rcm_core/lcc_profile.py`, die `horizon_profile.cor_eur`
verwachten op `FMResult`. Zonder profiel valt de keten terug op proportionele verdeling
of lege buckets → vlakke presentatie.

**Root cause-locatie:** `rcm_desktop/adapter/simulation_engine_service.py` —
`fm_results_from_mc_p50` (geen `horizon_profile` op synthetische `FMResult`).

## Known gaps (non-blocking, geaccepteerd)

- Knop toont **Herbereken analyse** i.p.v. **Start analyse** wanneer FM-cache op disk
  bestaat (slice 36 gedrag; geen slice-100 regressie)
- **Extra scenario** geeft geen visuele freeze-feedback voor scenario 1 (functioneel OK)

## Wat werkte (OK)

- App load op Haarlem demo
- Scenario-workflow: Extra scenario → run scenario 2 → Vergelijk scenario's
- Vergelijking in Top 10, LCC, FM-resultaten
- Wis vergelijking reset
- Run A/B knoppen verwijderd
- MC FM-resultaten met P10/P50/P90 banden

## Aanbevolen volgende stap

**TDD-fix:** vul `horizon_profile` op MC P50 synthetische `FMResult`-rijen.

1. Tracer-bullet test: MC P50 rollup → `FMResult` met `horizon_profile` →
   non-flat LCC jaar-buckets voor aging-FM (of reconcile met P50 CM-totaal)
2. Implementatie in `fm_results_from_mc_p50`: horizonprofiel uit analytische
   jaartoerekening-SSOT, geschaald naar P50 lifecycle-totalen
3. Architectuurkeuze (later): MC-engine per-bucket band-data vs. analytische-shape-schaal

## Akkoord

| Analist | Datum | GO / NO-GO | Opmerkingen |
|---------|-------|------------|-------------|
| ReinderRoos | 2026-06-13 | NO-GO | MC aggregate views OK; LCC/NB jaarcurves vlak — horizon_profile gap |
