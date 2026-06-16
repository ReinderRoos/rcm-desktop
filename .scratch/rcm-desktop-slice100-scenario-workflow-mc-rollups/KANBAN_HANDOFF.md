# KANBAN handoff — Slice 100 scenario workflow + MC rollups

## Batch-voortgang (AFK-batch)

**Gestart:** 2026-06-14  
**Laatste update:** 2026-06-14

### Afgerond

| Issue | Outcome | Tests |
|-------|---------|-------|
| 01 | ADR/CONTEXT docs | n/a (docs) |
| 02 | MC P50 rollup live routing | test_slice100_mc_p50_rollups.py |
| 03 | Unified Start analyse | test_slice100_unified_start_analyse.py |
| 04 | ScenarioWorkflowService + invalidation + MC slot merge | test_slice100_scenario_workflow.py, test_slice100_scenario_invalidation.py |
| 05 | Extra scenario + variant scenario 2 | test_slice100_extra_scenario.py |
| 06 | Toolbar regel D | test_slice100_scenario_toolbar.py, test_slice56_workspace_ab_compare_smoke.py |
| 07 | Mixed compare Top10/LCC | test_slice100_compare_mixed_fm.py, test_compare_view_service.py |
| 08 | FM compare split | test_slice100_compare_mixed_fm.py |

### Overgeslagen / afgesloten

| Issue | Reden |
|-------|-------|
| 09 | HILT100 — overgeslagen (productbesluit 2026-06-16); slice AFK af |

### Blockers

Geen.

### Volgende stap

Slice 100 afronden: PRD-status → `done`. Daarna slice 102 (RCM2 presentatielaag) grillen/specificeren.
