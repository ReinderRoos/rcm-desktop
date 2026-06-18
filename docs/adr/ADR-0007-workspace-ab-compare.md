# ADR-0007: Workspace A/B-scenariovergelijking

**Status:** accepted  
**Date:** 2026-06-02  
**Parent:** slice 56 PRD — resultatenwerkruimte A/B-scenariovergelijking (GitHub issue #2)

## Context

ADR-0006 verbood scenario/compare-UI in de resultatenwerkruimte ten gunste van single-run
what-if (`last_run` + `planning_overlay`). Reliability-analisten moeten twee **bevroren**
motorruns naast elkaar kunnen houden (referentie A vs variant B) terwijl PBS-scope en
taaktype-filters **één keer** worden bediend.

Legacy `CompareRunner`, `scenario_compare_service` KPI-flow en vaste CM/PM-scenario-slots
blijven nodig voor `ValidateWindow` (`--legacy-validate`).

## Decision

- **Workspace A/B compare** is **toegestaan** in `ResultsWorkspaceWindow` via generieke
  slots `A` en `B` (`CompareSlotState`), niet via oude `ScenarioSlotState` cm/pm-keys.
- **Opt-in** toggle `compare_mode` (default uit); single-run UX op `last_run` blijft norm.
- **Legacy compare-stack** (`CompareRunner`, KPI-vergelijkingstabel, CM/PM-dubbelrun-UI)
  blijft **ValidateWindow-only** — ADR-0006 blijft geldig voor die stack.
- `compute_split_layout` / `CompareSplitLayoutService` mag A/B-split leveren voor Top10
  (horizontaal) en Tijdsplot (verticaal) wanneer `compare_mode` aan is.
- v1 (slice 56): Top10 + Tijdsplot only; FM-detail single-run; sessie-only slots.
- **v1.1 (slice 100):** UX **Start analyse → Extra scenario → Vergelijk scenario's**
  vervangt Run → A/B; FM-resultaten compare (split, metric-gestuurd); LCC compare
  volgt globale metric; gemengde run-modus (analytisch vs MC P50) toegestaan;
  dual-project *Vergelijk modellen…* blijft gescheiden product.

## Consequences

- Agents implementeren A/B via `CompareSlotState` / `CompareViewService`, niet via
  `CompareRunner` in de werkruimte.
- ADR-0006 wordt **niet** ingetrokken; alleen aangevuld: workspace-uitzondering voor het
  nieuwe A/B-model.
- Regressietests bewijzen dat legacy compare-UI niet terugkeert in de werkruimte.
