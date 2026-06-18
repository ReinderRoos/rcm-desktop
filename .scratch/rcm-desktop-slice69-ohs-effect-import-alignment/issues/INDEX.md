# Slice 69 — issues (goedgekeurd)

**PRD:** [PRD.md](../PRD.md)  
**Status:** **done** (issues 01–08, 2026-06-05)

| # | Title | Type | Triage | Blocked by |
|---|--------|------|--------|------------|
| [01](01.md) | Semantiek-spike + ADR-supplement | HITL | ready-for-human | — |
| [02](02.md) | EffectIds parser + import-audit | AFK | ready-for-agent | 01 |
| [03](03.md) | FM-effectlink regressie & completeness | AFK | ready-for-agent | 01 |
| [04](04.md) | PM-resolutie SubIndex-fallback | AFK | ready-for-agent | 01 |
| [05](05.md) | PM dual-scope (PEnable + IEnable) | AFK | ready-for-agent | 04 |
| [06](06.md) | RedundancyFactor → PMEffectLink.fractie | AFK | ready-for-agent | 01 |
| [07](07.md) | Golden cause + CM-fixture + motor-smoke | AFK | ready-for-agent | 04, 05, 06 |
| [08](08.md) | Importrapport + FM-verificatie UX | AFK | ready-for-agent | 02, 07 |

## Implementatievolgorde

1. **01** (HITL) — `EFFECT_SEMANTICS_SPIKE.md` + ADR-0004 aanvulling
2. **02**, **03**, **04**, **06** parallel na 01
3. **05** na 04
4. **07** na 04+05+06 (incl. motor-smoke)
5. **08** na 02+07

## Start

`/tdd slice 69 issue 01`
