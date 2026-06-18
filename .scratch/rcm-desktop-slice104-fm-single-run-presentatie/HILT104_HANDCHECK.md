# HILT104 — Handcheck FM single-run presentatie + Top 10-afbouw

**Issue:** slice 104 issue 05  
**Datum:** 2026-06-18 (re-HILT op master)  
**Status:** **GO**

## Doel

Visuele QA van de vernieuwde **single-run FM-resultatenview**, afwezigheid Top 10,
en direct bewerkbare FM-editor tabs.

## Voorbereiding

1. Start resultatenwerkruimte: `python -m rcm_desktop.main`
2. Open demo-project: `tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json`
3. Draai **Start analyse** (analytisch of MC)

## Pad A — Single-run FM presentatie

| # | Check | OK | NOK | Notities |
|---|-------|----|-----|----------|
| A1 | Startup opent op **FM-resultaten** (geen Top 10) | x | | |
| A2 | Tabel is **beknopt**: één metric-kolom + id/bouwdeel | x | | Re-HILT 2026-06-18 |
| A3 | Metric-wissel (Faalmomenten/NB/Kosten) werkt in tabel | x | | |
| A4 | **NMF/RF** standaard uit; toggle toont kolommen | x | | |
| A5 | **Tabel / diagram** toggle werkt | x | | |
| A6 | Diagram volgt actieve metric + horizon (Ø per jaar) | x | | |
| A7 | Horizon **Levensduur** + jaarkiezer werken in tabel én diagram | x | | |

## Pad B — Geen Top 10

| # | Check | OK | NOK | Notities |
|---|-------|----|-----|----------|
| B1 | Geen **Top 10** modus-knop in toolbar | x | | |
| B2 | Scenario compare: geen Top 10 compare-view | x | | |

## Pad C — FM-editor tabs

| # | Check | OK | NOK | Notities |
|---|-------|----|-----|----------|
| C1 | Dubbelklik FM opent editor (single-run + compare) | x | | Re-HILT 2026-06-18: compare-modus OK |
| C2 | Tab **Effecten**: link toevoegen/wijzigen + opslaan | x | | |
| C3 | Tab **Preventief**: PM-taak bewerken + opslaan | x | | |

## Akkoord

| Analist | Uitkomst | Datum |
|---------|----------|-------|
| Reinder | **NO-GO** | 2026-06-17 |
| Reinder | **GO** | 2026-06-18 |

## Blockers (historisch — opgelost)

1. FM-editor Effecten/Preventief-tabs — opgelost via slice 105/106; re-HILT GO.
2. Dubbelklik FM in vergelijk-scenario-modus — opgelost; re-HILT GO.
