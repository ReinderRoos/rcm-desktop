# Slice 71 — issues

**PRD:** [PRD.md](../PRD.md)  
**Status:** **goedgekeurd** — GitHub publicatie pending ([GITHUB_PUBLISH.md](../GITHUB_PUBLISH.md))

| # | Title | Type | Triage | Blocked by | GitHub |
|---|--------|------|--------|------------|--------|
| [00](00.md) | Lifecycle-kosten regressie CM-overlay | AFK | ready-for-agent | slice 70 | done lokaal |
| [01](01.md) | EffectNbFilterSet + NB-seam EffectImpactService | AFK | ready-for-agent | 00 | done lokaal |
| [02](02.md) | Gefilterde Top 10 aggregatie | AFK | ready-for-agent | 01 | done lokaal |
| [03](03.md) | Workspace state + verwijder hybrid UX | AFK | ready-for-agent | 02 | done lokaal |
| [04](04.md) | Top 10 UI metric 3-way + NB-effectfilter | AFK | ready-for-agent | 03 | done lokaal |
| [05](05.md) | NB-jaarreeks + Tijdsplot dataseam | AFK | ready-for-agent | 01, 03 | done lokaal |
| [06](06.md) | Tijdsplot UI gedeelde metric + NB-curve | AFK | ready-for-agent | 05 | done lokaal |
| [07](07.md) | Regressie, CONTEXT.md, test-migratie | AFK | ready-for-agent | 04, 05, 06 | done lokaal |
| [08](08.md) | Functierapport smoke | AFK | ready-for-agent | 03 | done lokaal |

## Implementatievolgorde

1. **00** (blocker — kosten-diagnose)
2. **01** → **02** → **03**
3. **04** (Top 10 UI)
4. **05** → **06** (Tijdsplot; kan 08 parallel na 03)
5. **07** afronding + KANBAN_HANDOFF

## GitHub publiceren

```powershell
gh auth login
.\.scratch\rcm-desktop-slice71-nb-effectfilter-workspace-ux\publish-issues.ps1
```

## Start

```
/tdd slice 71 issue 00
```
