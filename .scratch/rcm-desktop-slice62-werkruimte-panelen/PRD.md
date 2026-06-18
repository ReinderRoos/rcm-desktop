# PRD — RCM2 desktop slice 62 (werkruimte-panel-extractie)

**Status:** done (PR4 af)  
**Versie:** 1.0  
**Type:** Architectuur-verdieping (geen nieuwe eindgebruikersfeatures)  
**Parent:** `/improve-codebase-architecture` review (2026-06-05); slice **61** (orchestrator done, line budget ≤2000 niet gehaald)  
**Datum:** 2026-06-05

## Problem Statement

Slice 61 verdiepte **snapshot → plan** via `ResultsWorkspaceOrchestrator`, maar `results_workspace_window.py` blijft een **shallow monolith** (~3000 regels): widget-constructie, event-handlers en bind-logica zitten nog in één module. Het PRD-stretchdoel **≤2000 regels** is niet haalbaar zonder mechanische panel-extractie.

## Solution

Extracteer domeinmodus-panelen naar `rcm_desktop/views/panels/`. Het venster blijft **bind-only shell**: orchestrator-plannen toepassen, panel-referenties aliassen op `self` waar nodig voor bestaande tests.

| PR | Levert | View-winst |
|----|--------|------------|
| **PR0** | Dode adapter-shims verwijderen; `run_decision` → `run_policy` | Hygiene, geen misleidende seams |
| **PR1** | `BijdragenWorkspacePanel` + `workspace_table_policy` | ~25 regels; patroon voor volgende PRs |
| **PR2** | `FmDetailWorkspacePanel` | FM-tabel + inspector (~80 regels) |
| **PR3** | `LccWorkspacePanel` (what-if bar, meekoppel, chart, compare) | Grootste winst (~200 regels) |
| **PR4** | Line budget gate ratchet; CONTEXT.md orchestrator-termen | Meetbaar shrink |

## Constraints

- Geen UX-wijziging; attribuutnamen op `self` stabiel houden voor pytest-qt.
- Panel-modules mogen **views → views/widgets** importeren; geen adapter→view leakage.
- Meekoppel **handlers** blijven in venster tot slice 54/55 workflow-seam.
- `_sync_lcc_chrome` blijft view-side (slice 61 besluit).

## Test seams

- `tests/test_slice62_panel_gate.py` — panel-module aanwezig, shims weg, line ratchet
- Bestaande: `test_slice61_orchestrator_gate.py`, `test_desktop_results_workspace_window.py`, `test_slice56_workspace_ab_compare_smoke.py`

## Volgorde na slice 62

1. Slice **55** → **54** (meekoppel discovery rollup + workflow-seam)
2. Presentatie-cache merge (slice 53 deferred)
3. Slice **60** (FM-editor hardening)
