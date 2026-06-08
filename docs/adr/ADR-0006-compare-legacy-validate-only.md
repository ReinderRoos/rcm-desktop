# ADR-0006: Compare-stack is legacy ValidateWindow only

**Status:** accepted  
**Date:** 2026-05-23

## Context

Slice 23 introduceerde scenario-slots in de resultatenwerkruimte; slice 29
deprecieerde CM/PM-split in de werkruimte ten gunste van what-if +
`last_run`. `CompareRunner` en `scenario_compare_service` blijven nodig voor
`ValidateWindow` (`--legacy-validate`).

## Decision

- **Compare / scenario-slot UI** is **legacy-only** — alleen
  `ValidateWindow`, niet de resultatenwerkruimte.
- `compute_split_layout` retourneert altijd single-run layout; geen nieuwe
  workspace-scenario-paden toevoegen zonder expliciet ADR.
- `CompareRunner` blijft bestaan zolang legacy validate actief is.

## Consequences

- Agents implementeren geen CM/PM-scenario-split in
  `results_workspace_window.py`.
- Opruimen van dode scenario-slot wiring in workspace is toegestaan; compare
  service blijft voor legacy.
