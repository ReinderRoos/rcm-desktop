## Problem Statement

Na slice 69 staan effecten per faalwijze en preventieve maatregel correct in het RCM2-project (FM/PM effectlinks, RF). De analytische motor berekent `effect_bijdragen` en `effect_bijdragen_per_jaar`. De **resultatenwerkruimte** gebruikt die data vrijwel niet: Top 10 toont alleen totale downtime; effectklassen (VGM, Schutten, …) zijn niet rankbaar of vergelijkbaar met AWB.

## Solution

Presentatie- en aggregatieslice die effectdata first-class maakt:

1. Semantiek vastgelegd (HITL spike — **done**)
2. Motor split CM/PM raw bijdragen
3. Deep module `EffectImpactService` (SSOT voor aggregatie)
4. Top 10 bron Effectklasse + metric Effectimpact (hybride)
5. Inspector, KPI, PBS, functierapport, tijdsplot, AW-pariteit, validatie-export
6. Regressie golden cause + CM-fixture end-to-end

Geen wijziging aan slice 69 importregels (behalve genormaliseerde effect-taxonomie issue 11).

## Child issues

| # | Titel | Type | Blocked by |
|---|-------|------|------------|
| 01 | Effect-metrics semantics spike + ADR | HITL (**done**) | slice 69 |
| 02 | Motor: CM/PM split effectbijdragen | AFK | 01 |
| 03 | Deep module EffectImpactService | AFK | 02 |
| 04 | Top 10 bron Effectklasse | AFK | 03 |
| 05 | Metric Effectimpact per effectcategorie | AFK | 03, 04 |
| 06 | FM-inspector leesbare effectresultaten | AFK | 03 |
| 07 | KPI-tabel & PBS effectkolommen | AFK | 03, 05 |
| 08 | Functierapport effect-aware scope | AFK | 03 |
| 09 | Tijdsplot per-effect jaargang | AFK | 02, 03 |
| 10 | AW-pariteit EffectCost (informatief) | AFK | 01, 03 |
| 11 | Import effect-taxonomie | AFK | 01 |
| 12 | Validatie-export effecttab | AFK | 03, 05, 10 |
| 13 | Regressie & motor-smoke in resultaten | AFK | 04–06 |

## PRD & spike

- PRD: `.scratch/rcm-desktop-slice70-effectcategorie-resultaten/PRD.md`
- Semantics spike (leidend): `.scratch/rcm-desktop-slice70-effectcategorie-resultaten/EFFECT_METRICS_SEMANTICS_SPIKE.md`

## Golden cause

`06H-350.1.1.1.1.1.A.1` — vier effectrijen met RF 0,1 / 0,9 / 1,0 / 0,5

## Labels

`ready-for-agent` (child issues); issue 01 sluiten na publicatie (HITL done)
