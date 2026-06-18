# Kanban handoff — slice 56 (werkruimte A/B-scenariovergelijking)

**Status:** done (2026-06-02)  
**Parent PRD:** `.scratch/rcm-desktop-slice56-workspace-ab-compare/PRD.md`  
**ADR:** `docs/adr/ADR-0007-workspace-ab-compare.md`

## Delivered

| Issue | Inhoud |
|-------|--------|
| 01 | ADR-0007 workspace A/B vs legacy ValidateWindow compare |
| 02 | `CompareSlotState`, seeding, invalidatie, slot-labels |
| 03 | Run → A/B, `CompareRunService` / `CompareRunRunner`, scenario-combo |
| 04 | Toggle *Vergelijk A ↔ B*, Top10 side-by-side |
| 05 | Tijdsplot gestapeld, `shared_lcc_y_max`, gesynchroniseerd kalenderjaar |
| 06 | Regressie-gates + pytest smoke |

### Architectuur-deepening (post-review)

- `planning_run_service.execute_planning_run` — compare-runs
- `CompareSlotSnapshot.from_motor_run`, `resolve_overlay_for_seed`, `compare_slot_to_render_index`
- `lcc_presentatie_service.materialize_lcc_curve` — per-slot LCC-cache

## Regressie-commando

```bash
python -m pytest \
  tests/test_slice56_workspace_ab_compare.py \
  tests/test_slice56_workspace_ab_compare_smoke.py \
  tests/test_compare_*.py \
  tests/test_planning_run_service.py \
  tests/test_lcc_presentatie_service.py \
  tests/test_slice53_issue07_legacy_pr7a.py \
  tests/test_desktop_results_workspace_window.py \
  -q
```

## Handmatige acceptatie (analist)

1. Run → A (of seed A) met referentie-overlay  
2. Overlay wijzigen, Run → B (of seed B)  
3. Toggle *Vergelijk A ↔ B* — Top10 en Tijdsplot tonen beide slots; filters/PBS updaten beide zonder motorrun  

## Open (bewust buiten slice 56)

- Delta-tabel A/B/Δ  
- FM-detail split compare  
- Persistente A/B-slots op schijf  
- `RunRunner` → `planning_run_service` (single-run seam)  
- Werkruimte-orchestratie uit god-window (arch #1)
