# HILT103 — Handcheck MC-presentatie (gecombineerd HILT100 + HILT101)

**Issue:** slice 103 issue 02  
**Datum:** 2026-06-16  
**Status:** NO-GO (2026-06-16)

## Doel

Visuele QA van de **volledige MC-presentatieketen** op Haarlem demo: aggregate
LCC/NB-jaarcurves, FM horizon-presentatie, scenario compare en mixed compare.
Supersedes open items uit HILT100 en HILT101.

## Voorbereiding

1. Start resultatenwerkruimte: `python -m rcm_desktop.main`
2. Open demo-project: `tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json`
3. Run-modus **Monte Carlo**; `monte_carlo_n` ≥ 1000; seed 42 indien reproduceerbaar gewenst

## Pad A — Single-run MC

| # | Check | OK | NOK | Notities |
|---|-------|----|-----|----------|
| A1 | **Start analyse** (MC) voltooid; voortgang + seed zichtbaar | x | | |
| A2 | FM-resultaten: default **Ø per jaar** (geen lifecycle-totalen in kolommen) | x | | |
| A3 | Top 10 toont P50-waarden | | | **Overslaan** — slice 104 verwijdert Top 10 |
| A4 | **LCC CM-jaarcurve** — aging-FM toont vorm (niet vlak constant per jaar) | x | | HILT100 blocking |
| A5 | **NB-jaarcurve** — variatie over horizon (niet vlak) | x | | HILT100 blocking |
| A6 | Horizon **Levensduur** → MC FM toont lifecycle P50; afwijking t.o.v. analytisch **begrijpelijk** (band/discreet) | x | | Geen numerieke parity vereist |
| A7 | Band-tooltips P10/P90 consistent bij horizon-wissel | x | | |

## Pad B — Scenario compare (S1 + S2 MC)

| # | Check | OK | NOK | Notities |
|---|-------|----|-----|----------|
| B1 | **Extra scenario** → scenario 2 MC-run voltooid | x | | |
| B2 | **Vergelijk scenario's** — Top 10 compare werkt | | | **Overslaan** — slice 104 |
| B3 | LCC compare: **jaarcurves niet vlak** (beide scenario's) | x | | HILT100 blocking |
| B4 | FM compare: waarden plausibel per rij | | x | **Blocking:** S2 gewijzigd (iteraties + REV-taken) maar FM compare exact gelijk; LCC compare wel verschil |

## Pad C — Mixed compare (S1 analytisch, S2 MC)

| # | Check | OK | NOK | Notities |
|---|-------|----|-----|----------|
| C1 | Wis vergelijking; schakel run-modus **Analytisch** | | | |
| C2 | **Start analyse** (analytisch) — scenario 1 | | | |
| C3 | **Extra scenario**; schakel **Monte Carlo**; run scenario 2 | | | |
| C4 | **Vergelijk scenario's** — FM **Ø per jaar**: geen ~60× verschillen | | | HILT101 |
| C5 | LCC compare: **MC-slot plot zichtbaar zonder** eerdere MC-run op live session | | | HILT101 blocking |
| C6 | Geen foutmeldingen in terminal bij lege-test-stappen | | | |

## Optioneel — RF-kolom (conditional slice 103 issue 05)

| # | Check | OK | NOK | Notities |
|---|-------|----|-----|----------|
| D1 | FM-detail RF-kolom: MC vs analytisch — **verwarrend verschil?** | | | Alleen fixen als NOK + analist wil fix |

## Known gaps (geaccepteerd — niet blocking)

- Knop **Herbereken analyse** bij bestaande FM-cache (slice 36)
- Geen freeze-visualisatie bij Extra scenario (slice 100)

## Akkoord

| Analist | Uitkomst | Datum |
|---------|----------|-------|
| ReinderRoos | **NO-GO** | 2026-06-16 |

## Blockers (invullen bij NO-GO)

1. **B4 — FM compare geen verschil na scenario-2 wijziging:** iteraties (`monte_carlo_n`) gewijzigd + alle REV-taken dis/enabled; FM compare exact gelijk tussen S1 en S2; LCC compare toont wel verschil. Verdacht: FM compare-panel leest verkeerde slot/state of presenteert beide scenario's identiek.
2. Pad C (mixed compare) niet uitgevoerd — sessie gestopt na B4.
