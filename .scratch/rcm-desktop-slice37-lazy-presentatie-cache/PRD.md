# Slice 37 — Lazy presentatie-cache per modus

**Triage:** ready-for-agent  
**Type:** AFK (adapter/UI; geen motorwijziging)  
**Parent:** slice 36 follow-up (PRD out-of-scope v1: lazy presentatie-cache)  
**Versie:** 1.0  
**Datum:** 2026-05-21  
**Referentie-fixture:** `tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json`

## Problem Statement

Na een analyse-run bouwt `build_project_total_presentation` **monolithisch** LCC + NB + PM (×2) + Bijdragen, terwijl de werkruimte-UI alleen **`contribution_rows`** uit de presentatie-cache leest. LCC gebruikt `build_lcc_planning_curve_reconciled` via `WorkspaceRenderIndex`; NB/PM-blokken zijn legacy (slice 33).

De post-run **Presentatie…**-fase is daardoor onnodig zwaar — vooral LTAP/LCC-builds die de UI niet consumeert.

## Solution

1. **Contribution-only post-run:** RunRunner en PresentationRebuildRunner bouwen standaard alleen het Bijdragen-blok.
2. **Cache schema v3:** `built_modi` + contribution-payload; backward-compat load v2.
3. **Verwijder dode builds:** geen NB/PM/`build_single_run_lcc_input` in hot path.
4. **Lazy LCC:** eerste LCC-render via bestaande `WorkspaceRenderIndex` + LTAP-cache (slice 36); geen sync LCC in run-worker.
5. **Perf-contracts:** call-count guardrails in `tests/perf/`.

## User Stories

1. Als analist wil ik na run **snel Top 10/Bijdragen** zien zonder wachten op ongebruikte LCC/NB/PM-builds.
2. Als analist wil ik **LCC pas bij modusbezoek** zwaar werk triggeren, niet in post-run fase.
3. Als maintainer wil ik **v2 presentatie-cache** nog laden na upgrade.
4. Als maintainer wil ik **pytest call-count contracts** op post-run presentatie.

## Out of Scope

- Volledige async LCC-render op achtergrondthread (UI blijft sync render bij moduswissel).
- Wijziging LCC business rules of planning-overlay.
- `CACHE_INPUTS_VERSION` bump (geen motorwijziging).

## Issues

| # | Titel |
|---|--------|
| 01 | Contribution-only post-run |
| 02 | Cache schema v3 + partial validatie |
| 03 | Verwijder dode NB/PM/LCC presentatie-builds |
| 04 | Lazy LCC warmup via render_index |
| 05 | Perf-contract slice 37 |
