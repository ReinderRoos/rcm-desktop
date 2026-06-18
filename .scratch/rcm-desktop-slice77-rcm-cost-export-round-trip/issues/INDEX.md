# Slice 77 — issues

**PRD:** [PRD.md](../PRD.md)
**ADR:** [ADR-0011](../../../docs/adr/ADR-0011-rcm-cost-export-round-trip.md)
**Status:** goedgekeurd (lokale tracker)

| # | Title | Type | Triage | Blocked by | User stories |
|---|-------|------|--------|------------|--------------|
| [01](01.md) | AW-bron-sidecar bewaren bij import + `source_workbook_path` | AFK | ready-for-agent | — | 7, 11 |
| [02](02.md) | Export-mapper: patch must-v1 sheets op bestaande rijen | AFK | ready-for-agent | 01 | 1, 2, 3, 4, 12 |
| [03](03.md) | Append nieuwe rijen + warn op ontbrekende bron-rijen | AFK | ready-for-agent | 02 | 5, 6 |
| [04](04.md) | Export-actie in UI + block/locate + samenvatting | AFK | ready-for-agent | 02 | 8, 9, 10 |

## Implementatievolgorde

1. **01** (sidecar-behoud — fundament)
2. **02** (patch bestaande rijen — kern round-trip)
3. **03** (append + warn-delete)
4. **04** (UI + block/locate)

## Start

```
/tdd slice 77 issue 01
```
