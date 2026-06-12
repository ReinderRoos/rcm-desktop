# Slice 43 — parallel taakgroep-PM-deduplicatie (handoff)

**Status:** afgerond (issues 01–03)  
**Datum:** 2026-05-23

## Besluiten (grill-me)

| Code | Besluit |
|------|---------|
| F1 | Motorfix; parallel blijft mogelijk |
| I1 | Post-pass na `ProcessPoolExecutor` |
| S1 | Alleen `rcm_core` + tests; geen desktop parallel inschakelen |
| K1 | Strikte per-FM parity: `total_cost_eur`, `pm_cost_eur`, `expected_pm_downtime_hr` |
| T1 | `CACHE_INPUTS_VERSION` 103 → **104** |

## Wat is gebouwd

- `deduplicate_parallel_fm_pm_costs` in `rcm_core/engine.py` — project-brede `counted_group_ids`, zelfde FM-volgorde als sequentieel.
- Post-pass alleen na echte parallel pool (`parallel=True` en ≥8 FM's).
- Tests: `tests/test_parallel_task_group_dedup.py` (mini 8-FM + Haarlem).
- Inflatie-test verwijderd uit `tests/test_run_metrics_baseline.py`.

## Testcommando's

```powershell
cd c:\Users\rroos\claude-workspace\rcm-desktop
python -m pytest tests/test_parallel_task_group_dedup.py -v
python -m pytest tests/test_run_metrics_baseline.py -v
python -m pytest tests/test_lcc_cm_shape.py tests/test_haarlem_fixture_aging_flip.py -q
```

## Verwacht gedrag na upgrade

- Scenario-runs (`SCENARIO_RUN_POLICY`, `parallel=True`) kunnen **lagere** PM/totaal tonen na Herbereken — correct, geen regressie.
- Oude `.rcm.cache.json` met parallel-FM hits → cache-miss door versie 104.

## Vervolg op kanban

1. **S2** — Desktop Start analyse parallel (`RunPolicy.allow_parallel`) + perf-contract.
2. **D3** — Import-audit `failure_type` RCM-Cost/Isograph.

## Niet in scope

- `horizon_profile` PM-jaarverdeling, adapter/run-policy, views.
