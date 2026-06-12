# Slice 65 — RCM-Cost modelcontrole (parity)

**Triage:** done  
**Type:** AFK (kern Qt-vrij) + desktop dialoog  
**Parent:** ADR-0008; epic `.scratch/rcm-desktop-epic-parity-portfolio-mc/`

## Problem

Na import uit RCM-Cost wil de analist controleren of RCM2-resultaten binnen de
AW-onzekerheidsband vallen (`TotalCost`, `TotalTdt`). Benchmark-waarden zaten
niet volledig in `import_settings`; er was geen vergelijkings-UI.

## Solution

1. Import uitbreiden: `TotalCost`, `TotalTdt`, … in `isograph_causes`.
2. `rcm_core/rcm_cost_benchmark.py` — pass/fail/informatief per FM.
3. Adapter + dialoog + toolbar-knop **Modelcontrole AW** in werkruimte.

## Status

done — issues 01–03 (import, core, UI)
