# ADR-0018: Monte Carlo run-modus v1 (werkruimte)

**Status:** accepted  
**Date:** 2026-06-14  
**Parent:** slice 95 PRD fase D → slice 98 implementatie  
**Supersedes:** geen; extend epic `GRILL_DECISIONS.md` §3 met productkeuzes v1

## Context

Slice 95 leverde run-modus UI-stub (`analytical` | `monte_carlo`), job-DTO's en
gescheiden result-slots. De analytische motor is default; AW MC-run is referentie.
GRILL_DECISIONS §3 definieert motor-scope (PR1–PR4); slice 98 moet het eerste
bruikbare MC-product opleveren zonder Top 10/LCC te herontwerpen.

## Decision

### Product (analist)

- **Run-modus** op werkruimte-sessie: MC **vervangt** analytische run zolang MC
  geselecteerd is; terug naar analytisch = normale deterministische run.
- **Presentatie v1 (slice 98):** **FM-resultaten** tonen onzekerheid als **P10 /
  P50 / P90** per metriek (kosten, downtime, faalgebeurtenissen).
- **Presentatie v1.1 (slice 100):** na MC-run vullen **Top 10** en **LCC** via
  **P50-rollups** per faalwijze (zelfde grafiekstructuur als analytisch). FM-detail
  blijft banden; aggregate views tonen P50-puntwaarden (geen P10/P90-envelop in
  Top 10/LCC — **fase 2**).
- **Presentatie v1.2 (slice 101):** FM MC-kolommen (single-run en compare) respecteren
  de gedeelde **`ContributionPresentation`**-horizon (default Ø per jaar) — dezelfde
  schaalpipeline als analytische FM via synthetische `FMResult`-rollups; P10/P90
  tooltips schalen mee.
- **Presentatie v1.3 (slice 103):** HILT103 is acceptance gate voor de volledige
  MC-presentatieketen (single-run, scenario compare, mixed compare). **Belofte:**
  horizon-conforme FM-kolommen (v1.2), niet-vlakke LCC/NB-jaarcurves via synthetisch
  `horizon_profile` op P50-rollups, compare-slots die MC LCC/FM zonder live analytical
  session kunnen opbouwen. **Geen belofte:** numerieke gelijkheid tussen MC P50
  lifecycle-totalen en analytische puntschattingen — P50 is verdeling-median,
  analytisch is punt; afwijking is productgedrag, geen presentatie-bug.
- **N** via modelinstellingen (`monte_carlo_n`, default 10.000). **Seed** via
  `monte_carlo_seed` (leeg = willekeurig per run); getoond in statusstrip.
- **UI:** MC op **achtergrondthread** met voortgang; **annuleren** stopt job en
  gooit partial resultaten weg.

### Motor-scope v1

- **Must (PR1+PR2):** volledige FM-lifecycle-stochastiek met **parity aan
  analytische run** — faalmomenten, CM, alle `aging_distribution`-varianten,
  PM/REV/CN en task-group dedup.
- **Buiten scope v1 (PR3):** stochastische sampling van kosten/downtime uit
  `import_settings` (`TotalCostErrPc`, …); per simulatiepad blijven kosten/
  downtime deterministisch gegeven getrokken faalmomenten.
- **Buiten scope v1 (PR4):** gevolgkosten / effect-sampling.

### Architectuur

- Job-pad: `SimulationRequest → SimulationJob → SimulationEngine →
  ResultStore → Presentation` — **niet** in `_on_state_*` derived-refresh-flow.
- `FMMCResult` (of equivalent) **naast** `FMResult`; aparte cache-namespace
  (reeds voorbereid in `SimulationResultStore`).
- Adapter-only: views via `simulation_job_service` / toekomstige engine-facade;
  geen Qt in `rcm_core`.

## Consequences

- Slice 98 PRD/issues kunnen tracer bullets schrijven voor engine, FM-tabel
  percentielen, background job + cancel, en regressietests (seeded parity waar
  deterministisch).
- HILT slice 98: MC-run, voortgang, annuleren, P10/P50/P90 in FM-resultaten.
- Slice 100: MC P50 in Top 10/LCC; dual namespace (analytisch + MC) blijft.
- PR3/PR4 en MC-banden (P10/P90) in Top 10/LCC aggregate views: fase 2 (grill + PRD).
