# ADR-0017: ValidateWindow retirement — tranche 1 (parity + deprecate-pad)

**Status:** proposed (retirement-kandidaat)  
**Date:** 2026-06-13  
**Parent:** slice 95 PRD — strategische roadmap juni 2026

## Context

`ValidateWindow` (`--legacy-validate` / `RCM_LEGACY_VALIDATE=1`) was de oorspronkelijke
projectcockpit: valideren, run, LTAP/PM what-if, batch-grid en CM/PM-scenario-compare.
De **resultatenwerkruimte** (`rcm_desktop.main`) is sinds slice 23+ de default startup.
Analisten moeten niet blijven schakelen tussen twee hoofdvensters zonder expliciet
parity-bewijs.

ADR-0006 en ADR-0007 regelen dat **scenario-slot compare** en **LTAP what-if** bewust
legacy-only blijven tot een expliciet besluit. Retirement tranche 1 documenteert parity
en legt het pad vast; **geen verwijdering uit default startup** in deze tranche.

## Decision

1. **Parity-checklist** (`HILT14_PARITY_CHECKLIST.md`) is het werkdocument voor
   feature-parity tussen werkruimte en ValidateWindow.
2. **`--legacy-validate` blijft** beschikbaar voor regressie en gaps die nog niet
   gepariteerd zijn (LTAP, CM/PM-scenario-compare).
3. **Default startup** blijft `ResultsWorkspaceWindow`; ValidateWindow-verwijdering
   vereist ADR-update naar *accepted* + volledig afgevinkte parity + HILT-handcheck.
4. **Gefaseerd deprecate-pad:**
   - Tranche 1 (nu): checklist + ADR + geen code-removal.
   - Tranche 2: parity-gaps sluiten (LTAP/what-if in werkruimte of expliciete ADR voor
     permanent legacy-only).
   - Tranche 3: ValidateWindow uit default docs verwijderen; `--legacy-validate` alleen
     voor regressie tot test-suite migrated.
   - Tranche 4: ValidateWindow-code verwijderen wanneer parity + tests groen.

## Consequences

- Agents verwijderen ValidateWindow niet zonder ADR-promotie en HILT14-bewijs.
- Nieuwe features die alleen in ValidateWindow landen vereisen expliciete parity-issue
  of ADR-uitzondering.
- CompareRunner / LTAP-bundle blijven bestaan zolang legacy actief is (ADR-0006).

## References

- `docs/adr/ADR-0006-compare-legacy-validate-only.md`
- `.scratch/rcm-desktop-slice95-strategic-roadmap-juni2026/HILT14_PARITY_CHECKLIST.md`
- `CONTEXT.md` — vier FM-edit-paden
