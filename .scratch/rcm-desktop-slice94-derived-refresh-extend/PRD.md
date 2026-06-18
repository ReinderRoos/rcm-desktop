# PRD: Derived refresh extend (slice 94)

**Triage-label:** `done`

## Problem Statement

`refresh_contribution_year_combo` in `top10_workspace_binding.py` berekent
kalenderjaren inline via `wss.calendar_years_for_session`. Net als slice 92 voor
het NB-filter hoort deze derived-state berekening in de adapterlaag.

## Solution

Breid `workspace_derived_refresh.py` uit met `plan_contribution_year_refresh`.
De binding delegeert de jaarberekening; widget-update blijft in de binding.

## Out of Scope

- Overige derived-state producers (PBS-boom, KPI-tabel).
