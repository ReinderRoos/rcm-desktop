## Problem Statement

De **resultatenwerkruimte** is na slice 53 nog steeds een shallow view-monolith: bij elke workspace-snapshot-tick regelt de view zelf toolbar-sync én modus-routing naar presentatie-builders. Run-complete planning zit Qt-vrij in `ResultsWorkspaceController`, maar snapshot → presentatie niet.

## Solution

Introduceer **`ResultsWorkspaceOrchestrator`** in de adapter: Qt-vrije `plan_ui_sync`, `plan_render`, en `plan_workspace_tick`. De view bindt alleen widgets. Drie AFK child-issues in vaste volgorde: UiSync → Render → cleanup/gates.

Geen eindgebruikers-UX-wijziging. Meekoppel-semantiek (ADR-0005) en legacy compare (ADR-0006) ongewijzigd. A/B compare placeholders (ADR-0007) blijven functioneel identiek.

## Child issues

| PR | Titel | Volgorde |
|----|-------|----------|
| 01 | UiSync-plan voor resultatenwerkruimte | Eerst |
| 02 | Render-plan voor resultatenwerkruimte | Na 01 |
| 03 | Orchestrator gates en view cleanup | Na 02 |

## PRD

`.scratch/rcm-desktop-slice61-werkruimte-orchestrator/PRD.md`

## Test seams

1. `ResultsWorkspaceOrchestrator.plan_ui_sync` — unit, geen Qt
2. `ResultsWorkspaceOrchestrator.plan_render` — unit + render_index reset
3. `ResultsWorkspaceOrchestrator.plan_workspace_tick` — compose
4. Statische view-gate (PR3) — geen modus-builders in view render-pad
5. Bestaande pytest-qt workspace tests — regressie only

## Labels

`ready-for-agent`
