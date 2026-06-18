# GitHub publicatie — slice 70

**Status:** goedgekeurd 2026-06-05 — klaar voor publicatie  
**Repo:** `ReinderRoos/rcm-desktop`  
**Label:** `ready-for-agent`

## Publiceren

```powershell
gh auth login   # eenmalig
.\.scratch\rcm-desktop-slice70-effectcategorie-resultaten\publish-issues.ps1
```

Het script:

1. Maakt parent epic aan
2. Publiceert 13 child issues in dependency-volgorde (blocked-by URLs ingevuld)
3. Sluit issue **01** direct (HITL done)
4. Print alle URLs — plak die in `issues/INDEX.md` en lokale `NN.md` bestanden

## Issue bodies

| # | Titel | Body |
|---|-------|------|
| P | Effectcategorie-resultaten (parent) | `issues/gh-parent.md` |
| 01 | Effect-metrics semantics spike + ADR | `issues/gh-01.md` → **close** |
| 02 | Motor CM/PM split effectbijdragen | `issues/gh-02.md` |
| 03 | Deep module EffectImpactService | `issues/gh-03.md` |
| 04 | Top 10 bron Effectklasse | `issues/gh-04.md` |
| 05 | Metric Effectimpact per effectcategorie | `issues/gh-05.md` |
| 06 | FM-inspector leesbare effectresultaten | `issues/gh-06.md` |
| 07 | KPI-tabel & PBS effectkolommen | `issues/gh-07.md` |
| 08 | Functierapport effect-aware scope | `issues/gh-08.md` |
| 09 | Tijdsplot per-effect jaargang | `issues/gh-09.md` |
| 10 | AW-pariteit EffectCost (informatief) | `issues/gh-10.md` |
| 11 | Import effect-taxonomie | `issues/gh-11.md` |
| 12 | Validatie-export effecttab | `issues/gh-12.md` |
| 13 | Regressie & motor-smoke | `issues/gh-13.md` |

## Start implementatie (zonder GitHub)

```
/tdd slice 70 issue 02
```

Parallel: `/tdd slice 70 issue 11`
