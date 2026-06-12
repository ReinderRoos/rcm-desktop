## Problem Statement

Na slice 70 is effectimpact technisch beschikbaar, maar de resultatenwerkruimte UX is verwarrend (bron Effectklasse + metric Effectimpact naast totale NB). Lifecycle-kosten lijken gestegen (~60 M → ~160 M). Analist wil: twee bron-knoppen, drie metrics, NB-effectfilter (multi-select) gedeeld tussen Top 10 en Tijdsplot.

## Solution

1. Issue 00: kosten-diagnose CM-overlay (blocker)
2. Verdiep `EffectImpactService` met NB-filter seam
3. `EffectNbFilterSet` in workspace state; verwijder `SOURCE_EFFECTKLASSE` / `METRIC_EFFECTIMPACT`
4. Top 10 + Tijdsplot UI vereenvoudigen
5. Regressie + CONTEXT.md

## Child issues

| # | Titel | Type | Blocked by |
|---|-------|------|------------|
| 00 | Lifecycle-kosten regressie CM-overlay | AFK | slice 70 |
| 01 | EffectNbFilterSet + NB-seam EffectImpactService | AFK | 00 |
| 02 | Gefilterde Top 10 aggregatie | AFK | 01 |
| 03 | Workspace state + verwijder hybrid UX | AFK | 02 |
| 04 | Top 10 UI metric 3-way + NB-effectfilter | AFK | 03 |
| 05 | NB-jaarreeks + Tijdsplot dataseam | AFK | 01, 03 |
| 06 | Tijdsplot UI gedeelde metric + NB-curve | AFK | 05 |
| 07 | Regressie, CONTEXT.md, test-migratie | AFK | 04, 05, 06 |
| 08 | Functierapport smoke | AFK | 03 |

## PRD

`.scratch/rcm-desktop-slice71-nb-effectfilter-workspace-ux/PRD.md`

## Labels

`ready-for-agent`
