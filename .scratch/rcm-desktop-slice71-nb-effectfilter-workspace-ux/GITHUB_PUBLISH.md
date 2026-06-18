# GitHub publicatie — slice 71

**Status:** goedgekeurd 2026-06-05 — klaar voor publicatie  
**Repo:** `ReinderRoos/rcm-desktop`  
**Label:** `ready-for-agent`

## Publiceren

```powershell
gh auth login   # eenmalig
.\.scratch\rcm-desktop-slice71-nb-effectfilter-workspace-ux\publish-issues.ps1
```

Het script:

1. Maakt parent epic aan
2. Publiceert 9 child issues (00–08) in dependency-volgorde
3. Print alle URLs — plak die in `issues/INDEX.md` en lokale `NN.md` bestanden

## Issue bodies

| # | Titel | Body |
|---|-------|------|
| P | NB-effectfilter & workspace UX (parent) | `issues/gh-parent.md` |
| 00 | Lifecycle-kosten regressie CM-overlay | `issues/gh-00.md` |
| 01 | EffectNbFilterSet + NB-seam | `issues/gh-01.md` |
| 02 | Gefilterde Top 10 aggregatie | `issues/gh-02.md` |
| 03 | Workspace state + verwijder hybrid UX | `issues/gh-03.md` |
| 04 | Top 10 UI | `issues/gh-04.md` |
| 05 | NB-jaarreeks + Tijdsplot dataseam | `issues/gh-05.md` |
| 06 | Tijdsplot UI | `issues/gh-06.md` |
| 07 | Regressie + CONTEXT.md | `issues/gh-07.md` |
| 08 | Functierapport smoke | `issues/gh-08.md` |

## Start implementatie (zonder GitHub)

```
/tdd slice 71 issue 00
```
