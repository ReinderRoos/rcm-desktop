# Slice 69 — OHS effect-import alignment (handoff)

**Status:** done (issues 01–08)  
**Tests:** `tests/test_slice69_ohs_effect_import.py` + updates in `test_isograph_*`

## Before / after (CM-fixture)

| Metriek | Slice 35 (voor) | Slice 69 (na) |
|---------|-----------------|---------------|
| FM effect links | 224 | 224 |
| PM effect links | 54 | **>54** (fallback + dual-scope) |
| PM unresolved warnings | 15 | **≤12** (was 5 in laatste run) |
| PM `fractie` | altijd 1.0 | **RF uit assignment** |
| Golden cause PM-links | 0 | **1** (`Schutten 0-20%` → `REV\|0`) |

## Besluiten

- `EFFECT_SEMANTICS_SPIKE.md` — RF op PM, dual-scope, SubIndex-fallback
- ADR-0004 aangevuld
- `EffectsIds` kolom (AW) naast `EffectIds` voor audit
- `CACHE_INPUTS_VERSION` → **110**

## Analist playbook

1. Herimport `RCMCostdata export_*.xlsx`
2. Lees `result.warnings` + `result.warning_summary`
3. FM-verificatie toont nu ook `pm_effect_links`
4. Cause `06H-350.1.1.1.1.1.A.1`: 4 FM-links; PM alleen waar AW `PEnable`/`IEnable` true
