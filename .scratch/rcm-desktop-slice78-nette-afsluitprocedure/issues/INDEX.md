# Slice 78 — issues

**PRD:** [PRD.md](../PRD.md)
**Status:** goedgekeurd (lokale tracker)

| # | Title | Type | Triage | Blocked by | User stories |
|---|-------|------|--------|------------|--------------|
| [01](01.md) | Qt-vrije Afsluit-planner (`plan_shutdown` → `ShutdownPlan`) | AFK | ready-for-agent | — | 1, 5, 7 |
| [02](02.md) | `closeEvent`-bedrading: grid-dirty + busy-cancel-wait | AFK | ready-for-agent | 01 | 2, 3, 4, 6, 8 |
| [03](03.md) | `main.py` `aboutToQuit`-teardown (runner-vangnet) | AFK | ready-for-agent | 02 | 6 |

## Implementatievolgorde

1. **01** (beslislogica, test-first)
2. **02** (venster-bedrading)
3. **03** (vangnet)

## Start

```
/tdd slice 78 issue 01
```
