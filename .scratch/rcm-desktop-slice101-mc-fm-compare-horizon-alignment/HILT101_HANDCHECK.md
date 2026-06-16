# HILT101 — Handcheck MC FM horizon/presentatie-alignment

**Issue:** slice 101 issue 05  
**Datum:** 2026-06-13  
**Status:** completed (HILT overgeslagen — productbesluit 2026-06-16; oorspronkelijk NO-GO)

## Doel

Visuele QA van slice 101 op Haarlem demo: MC FM-resultaten volgen
`ContributionPresentation` (default Ø per jaar, lifecycle-switch), mixed compare
plausibel, band-tooltips consistent.

## Voorbereiding

1. App: `python -m rcm_desktop.main`
2. Project: `tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json`
3. Run-modus Monte Carlo; `monte_carlo_n` ≥ 1000

## Stappen

| # | Check | Uitkomst |
|---|-------|----------|
| 1 | App + project laden | ✅ OK |
| 2 | MC run → FM default **Ø per jaar** (geen lifecycle-totalen) | ✅ OK |
| 3 | Horizon **Levensduur** → MC ≈ lifecycle P50 | ❌ MC wijkt sterk af van analytische lifecycle |
| 4 | Mixed compare (analytisch vs MC) FM **Ø per jaar** | ✅ FM-waarden plausibel dichtbij; LCC-plot MC leeg zonder eerdere analytische run |
| 5 | Band-tooltips P10/P90 bij horizon-wissel | ✅ Waarden en tooltips passen |

## Bevindingen

### Blocking — lifecycle MC vs analytisch (stap 3)

Bij horizon **Levensduur** wijkt MC FM sterk af van analytische lifecycle-waarden.
Slice 101 fixt vooral default Ø-per-jaar-presentatie; lifecycle-parity is niet
bevestigd door analist.

### Blocking — LCC MC-plot zonder prior analytical run (stap 4)

In mixed scenario compare: LCC-plot voor MC-slot blijft leeg wanneer nog geen
analytische run is gedraaid. Na analytische run verschijnt de plot wel. Terminal
toont foutmeldingen in lege-toestand.

### Non-blocking — RF-kolom analytisch vs MC (stap 5)

| Modus | RF kolom |
|-------|----------|
| Analytisch | overal 1,0 |
| MC | overal 0,75 |

**Diagnose:** RF is modelinput (`FMEffectLink.fractie`), niet run-mode-afhankelijk.
Analytisch pad gebruikt `enrich_fm_rows_with_nmf_rf` → `_resolve_rf_for_fm`
(hoogste fractie binnen NB-filter). MC pad zet RF eenmalig in `build_mc_fm_rows`
als `links[0].fractie` zonder filter/sortering. **Presentatie-gap**, geen andere
modelinput.

**Locatie:** `simulation_engine_service.py` (`build_mc_fm_rows`) vs
`result_view_service.py` (`enrich_fm_rows_with_nmf_rf`).

## Akkoord

| Analist | Uitkomst | Datum |
|---------|----------|-------|
| ReinderRoos | **NO-GO** | 2026-06-13 |

## Vervolg

1. Lifecycle-parity MC vs analytisch onderzoeken (stap 3)
2. LCC MC-plot zonder prior analytical run fixen
3. Optioneel: RF-kolom MC alignen met analytische `_resolve_rf_for_fm`
