# Kanban-handoff — slice 62 werkruimte-panel-extractie

**Doel:** Monolith-shrink naar line budget ≤2000 via mechanische panel-extractie.  
**PRD:** `PRD.md`

## Kanban-status

| PR | Titel | Status |
|----|-------|--------|
| 0 | Hygiene — dode shims + run_policy | **done** |
| 1 | BijdragenWorkspacePanel | **done** |
| 2 | FmDetailWorkspacePanel | **done** |
| 3 | LccWorkspacePanel | **done** |
| 4 | Gate ratchet + CONTEXT.md | **done** |

## PR1 testcommando

```powershell
python -m pytest tests/test_slice62_panel_gate.py tests/test_slice61_orchestrator_gate.py tests/test_desktop_run_decision.py -q
```

## PR2 resultaat

- `fm_detail_workspace_panel.py` — FM-tabel + inspector widget tree
- Event-connecties blijven venster-side (PR1-callbackpatroon)
- `results_workspace_window.py`: 3015 → **2957** regels (−58)

## PR3 resultaat

- `lcc_workspace_panel.py` — what-if bar, meekoppel widget tree, chart/tables, compare pane
- Event-connecties + workflow-state blijven venster-side
- Fix: `_sync_lcc_chrome` leest live snapshot + blokkeert what-if signalen (stale render na meekoppel-expand)
- `results_workspace_window.py`: 2957 → **2823** regels (−134)

## PR4 resultaat

- Gate ratchet: baseline **2823** regels (was 3033 vóór slice 62); cumulatieve shrink-gate
- `CONTEXT.md`: sectie **Resultatenwerkruimte** (orchestrator-plannen + werkruimte-panelen)
- Nieuwe gates: `test_context_documents_orchestrator_terms`, `test_context_documents_workspace_panels`, `test_all_workspace_panel_modules_exist`

## Testcommando (slice 62 af)

```powershell
python -m pytest tests/test_slice62_panel_gate.py tests/test_slice61_orchestrator_gate.py tests/test_desktop_run_decision.py -q
```

## Volgende slices (na 62)

1. Slice **55** → **54** — meekoppel discovery rollup + workflow-seam
2. Presentatie-cache merge (slice 53 deferred)
3. Slice **60** — FM-editor hardening
