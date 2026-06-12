# Slice 74 — issues

**PRD:** [PRD.md](../PRD.md)
**Status:** goedgekeurd (lokale tracker)

| # | Title | Type | Triage | Blocked by | User stories |
|---|-------|------|--------|------------|--------------|
| [01](01.md) | Qt-vrije FM-rij-filter-helper + `build_fm_detail_view`-wiring | AFK | ready-for-agent | — | 1, 3, 4, 8 |
| [02](02.md) | NB-combo zichtbaar + gedeeld in FM-detail-modus | AFK | ready-for-agent | 01 | 2, 6, 7 |
| [03](03.md) | FM-inspector reflecteert NB-filter (lifecycle + jaarreeks) | AFK | ready-for-agent | 01 | 5 |

## Implementatievolgorde

1. **01** (rekenkundige seam + render-pad)
2. **02** (bediening zichtbaar maken)
3. **03** (inspector consistent)

## Start

```
/tdd slice 74 issue 01
```
