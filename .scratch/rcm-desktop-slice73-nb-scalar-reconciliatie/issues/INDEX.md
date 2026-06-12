# Slice 73 — issues

**PRD:** [PRD.md](../PRD.md)  
**ADR:** [ADR-0010](../../../docs/adr/ADR-0010-nb-reconciliatie-bucketreeks-restpost.md)  
**Status:** goedgekeurd (lokale tracker)

| # | Title | Type | Triage | Blocked by | User stories |
|---|-------|------|--------|------------|--------------|
| [00](00.md) | Read-only baseline: verschil-factor lege vs gevulde filter (~60×) | AFK | ready-for-agent | — | diagnose-borging |
| [01](01.md) | NB-bucketreeks-spine (Optie C) + Bug 1-fix | AFK | ready-for-agent | 00 | 1, 2, 3, 7, 8, 13 |
| [02](02.md) | Reconciliatie-contract: verborgen-NB-restpost + RF-clamp + PM-eenheid | AFK | ready-for-agent | 01 | 4, 5, 5b, 6 |
| [03](03.md) | Bug 3: per-FM `downtime_hr` in `aggregate` | AFK | ready-for-agent | — | 9 |
| [04](04.md) | Effectfilter-leesbaarheid: combobreedte, popup, tooltips | AFK | ready-for-agent | 02 | 10, 11, 12 |

## Implementatievolgorde

1. **00** (baseline vastpinnen, read-only)
2. **01** (spine + Bug 1)
3. **02** (reconciliatie-contract op de spine)
4. **04** (UX, na restpost uit 02)
5. **03** parallel grijpbaar (raakt Effectimpact-tabel, niet de Top 10-keten)

## Start

```
/tdd slice 73 issue 00
```
