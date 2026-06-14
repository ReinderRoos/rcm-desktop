# PRD — Slice 98: Monte Carlo engine v1

**Status:** ready-for-human (AFK 01–11 done; HILT 12 open)  
**Versie:** 1.0  
**Datum:** 2026-06-14  
**Triage:** `ready-for-human`  
**Parent:** slice 95 (run-modus stub, job-DTO's) / ADR-0018  
**Epic:** `.scratch/rcm-desktop-epic-parity-portfolio-mc/GRILL_DECISIONS.md` §3 (PR1+PR2)  
**Voorganger:** slice 95 issues 11–12 (`simulation_job_service`, status-strip stub)  
**Referentie:** ADR-0018, CONTEXT.md (Run-modus, FM-onzekerheidsband)

> Synthese van de **grill-sessie slice 98** (2026-06-14): alle 9 besluiten
> geaccepteerd (aanbeveling A). Geen her-interview — dit document is de
> implementatiebron voor engine, adapter-job, FM-presentatie en achtergrond-UI.

---

## Problem Statement

Slice 95 leverde een **Run-modus**-keuze (`analytical` | `monte_carlo`) in de
resultatenwerkruimte, job-DTO's (`SimulationJob`, `SimulationResultStore`,
`SimulationPresentation`) en een statusstrip-stub — maar **geen werkende
Monte Carlo-motor**. Analisten kunnen vandaag alleen een **analytische**
(deterministische) run uitvoeren; faalmomenten worden als verwachtingswaarden
berekend, niet als verdeling over simulatiepaden.

Daardoor ontbreekt het kernproduct dat Availability Workbench MC-runs bieden:
**FM-onzekerheidsbanden** (P10/P50/P90) per faalwijze voor kosten, downtime
en faalgebeurtenissen. Modelinstellingen `monte_carlo_n` en `monte_carlo_seed`
staan in `RCMConfig` en worden bij RCM-Cost-import gevuld, maar zijn in de UI
nog disabled en worden niet gebruikt bij run.

Zonder slice 98 blijft de Run-modus een cosmetische schakelaar; analisten
kunnen onzekerheid in faalmomenten niet beoordelen in de dagelijkse
werkruimte-workflow.

## Solution

Lever **Monte Carlo run-modus v1** end-to-end:

1. **Motor (PR1+PR2):** Qt-vrije MC-engine in `rcm_core` die N
   simulatiepaden per faalwijze trekt (volledige FM-lifecycle-stochastiek:
   faalmomenten, CM, alle `aging_distribution`-varianten, PM/REV/CN,
   task-group dedup met parity aan analytische run). Kosten en downtime per
   pad blijven **deterministisch** gegeven getrokken faalmomenten (geen PR3).
2. **Resultaatmodel:** `FMMCResult` (of equivalent) naast `FMResult`, met
   P10/P50/P90 per FM-metriek; aparte cache-/result-namespace (reeds
   voorbereid in `SimulationResultStore`).
3. **Adapter-job:** `SimulationRequest → SimulationJob → SimulationEngine →
   ResultStore → Presentation` — **niet** in derived-refresh-flow; MC-run
   **vervangt** analytische run zolang MC-modus geselecteerd is.
4. **Presentatie v1:** alleen **FM-resultaten** tonen **FM-onzekerheidsband**
   (P10/P50/P90 voor kosten, downtime, faalgebeurtenissen). Top 10 en LCC
   blijven analytisch.
5. **UI:** achtergrondthread met voortgang en seed in statusstrip; annuleren
   stopt job en gooit partial resultaten weg; modelinstellingen `monte_carlo_n`
   (default 10.000) en `monte_carlo_seed` (leeg = willekeurig per run)
   worden bewerkbaar.

---

## User Stories

### Run-modus en analist-workflow

1. As a reliability-analist, I want Monte Carlo as an optional **Run-modus**
   next to the analytical run in the same **werkruimte**, so that I do not
   switch context to assess uncertainty.
2. As a reliability-analist, I want MC mode to **replace** the analytical run
   while selected, so that FM-resultaten show MC bands instead of point
   estimates during MC work.
3. As a reliability-analist, I want switching back to **analytical** Run-modus
   to restore a normal deterministic run, so that I can compare point estimates
   after exploring uncertainty.
4. As a reliability-analist, I want **Top 10** and **LCC** to stay analytical
   in v1, so that I am not misled by partial MC integration in aggregate views.
5. As a reliability-analist, I want to start MC from the same **Start analyse**
   action when MC Run-modus is active, so that muscle memory from daily runs
   carries over.
6. As a reliability-analist, I want a clear indication when FM-resultaten show
   MC bands vs analytical point values, so that I never confuse the two modes.
7. As a trainer, I want onboarding text to distinguish “analytical default”
   from “MC opt-in uncertainty”, so that new users understand Run-modus.

### FM-onzekerheidsband (presentatie)

8. As a reliability-analist, I want **P10 / P50 / P90** per faalwijze for
   **kosten**, so that I see cost uncertainty bands in FM-resultaten.
9. As a reliability-analist, I want P10/P50/P90 per faalwijze for
   **downtime**, so that availability uncertainty is visible alongside cost.
10. As a reliability-analist, I want P10/P50/P90 per faalwijze for
    **faalgebeurtenissen** (lifecycle faalmomenten), so that failure-count
    uncertainty is explicit.
11. As a reliability-analist, I want P50 to align with the “typical” path
    (median over N simulations), so that I can sanity-check against intuition.
12. As a reliability-analist, I want band columns to respect the existing
    **per jaar / per LCC** schaal-toggle where applicable, so that presentation
    stays consistent with analytical FM-resultaten.
13. As a reliability-analist, I want the **NB-effectfilter** to continue
    working on downtime presentation in analytical mode; in MC mode v1 bands
    reflect total FM downtime (filter semantics documented if simplified).
14. As a reliability-analist, I want **NMF** and **RF** columns unchanged in
    FM-resultaten during MC mode, so that identity columns stay stable while
    metric columns show bands.

### Modelinstellingen (N en seed)

15. As a reliability-analist, I want to set **N** via modelinstellingen
    (`monte_carlo_n`, default 10.000), so that I can trade accuracy vs runtime.
16. As a reliability-analist, I want to set an optional **seed**
    (`monte_carlo_seed`; empty = random per run), so that I can reproduce a
    MC run for review or debugging.
17. As a reliability-analist, I want MC settings changes to require **Herbereken**
    when they affect the next run, so that I am not shown stale bands.
18. As a reliability-analist, I want validation that `monte_carlo_n >= 100`,
    so that degenerate runs are blocked (existing validator `CFG_MC_N`).
19. As a maintainer, I want RCM-Cost-import values for `RcmNoSimulations` and
    `RcmRandomNoSeed` to continue populating `monte_carlo_n` / `monte_carlo_seed`,
    so that round-trip projects start with sensible MC defaults.

### Achtergrond-run, voortgang en annuleren

20. As a reliability-analist, I want MC to run on a **background thread**, so
    that the werkruimte stays responsive during long N.
21. As a reliability-analist, I want **progress** visible during MC (e.g.
    percentage of iterations), so that I know the run is advancing.
22. As a reliability-analist, I want the active **seed** shown in the status
    strip during/after MC, so that I can record it for reproducibility.
23. As a reliability-analist, I want to **cancel** a running MC job, so that
    I can stop an accidentally large N.
24. As a reliability-analist, I want cancel to **discard partial results**, so
    that I never see half-finished bands in FM-resultaten.
25. As a reliability-analist, I want the UI blocked from starting a second MC
    run while one is busy, so that jobs do not overlap corrupting state.
26. As a reliability-analist, I want filter/navigation changes during MC **not**
    to restart the job, so that exploring views does not waste compute.

### Motor-scope (PR1+PR2)

27. As a domain expert, I want **random** faalwijzen sampled with exponential
    inter-arrival semantics consistent with analytical hazard, so that MC matches
    AW-style lifecycle simulation for random failure.
28. As a domain expert, I want **aging** faalwijzen with **normal**,
    **truncated_normal_0**, and **weibull_2p** distributions stochastically
    sampled, so that all supported aging variants participate in MC.
29. As a domain expert, I want **REV** schedules and **repair_quality**
    rejuvenation in the MC path, so that aging assets with overhaul behave like
    the analytical engine.
30. As a domain expert, I want **PM**, **REV**, and **CN** tasks to affect each
    simulation path the same way as analytically (executions, downtime, costs),
    so that maintenance strategy uncertainty is reflected in bands.
31. As a domain expert, I want **task-group dedup** in MC with the same
    semantics as the analytical post-pass, so that shared PM groups are not
    double-counted per path.
32. As a domain expert, I want **CM costs** and **downtime per failure** to be
    deterministic given drawn failure counts on each path, so that v1 does not
    falsely imply cost-parameter uncertainty (PR3 explicitly out).
33. As a domain expert, I want **multiplicity** and **effective bouwjaar** from
    PBS hierarchy applied per path, so that structural FM parameters match
    analytical runs.
34. As a domain expert, I want **aw_mc_lifecycle_horizon** respected in MC
    horizon calculation, so that AW MC-horizon projects behave consistently.

### Parity, cache en architectuur

35. As a maintainer, I want **seeded parity** where MC with deterministic inputs
    converges to analytical `FMResult` metrics (e.g. sigma→0 or controlled N=1
    paths), so that the MC engine does not drift from the analytical SSOT.
36. As a maintainer, I want MC results stored in a **separate namespace** from
    analytical `RunResult`, so that switching Run-modus does not corrupt
    analytical cache slots.
37. As a developer, I want MC orchestration **outside** `_on_state_*` derived
    refresh, so that KPI/tree refresh does not couple to simulation lifecycle.
38. As a developer, I want views to reach MC only via **adapter** facades, so
    that `rcm_core` stays Qt-free and AGENTS.md decoupling holds.
39. As a developer, I want a clear **`SimulationEngine`** facade callable from
    adapter workers, so that `RunRunner` and future CLI can share the same core.
40. As a maintainer, I want aging MC cross-checks to extend prior art
    (`test_aging_monte_carlo`), so that calendar-bucket stochasticity stays
    aligned with analytical SSOT functions in `distributions`.
41. As a maintainer, I want `CACHE_INPUTS_VERSION` bumped if MC motor inputs
    affect shared analytical cache keys, so that stale cache cannot mask engine
    bugs (follow AGENTS.md convention).

### Regressie en kwaliteit

42. As a product owner, I want **HILT** on a demo project: MC run, progress,
    cancel, P10/P50/P90 visible in FM-resultaten, Top 10/LCC unchanged, before
    merge (ADR-0018).
43. As a maintainer, I want slice-specific pytest subsets documented, so that CI
    gates stay fast.
44. As a maintainer, I want cancel tests to assert **no** MC result attached to
    session after abort, so that partial aggregation bugs are caught early.
45. As a maintainer, I want Run-modus switch tests to assert analytical run still
    works after an MC cancel, so that session state recovers cleanly.

---

## Implementation Decisions

### Vastgelegde productbesluiten (grill slice 98 — alle A)

| # | Onderwerp | Besluit |
|---|-----------|---------|
| 1 | Minimale success v1 | P10/P50/P90 alleen in **FM-resultaten**; Top 10/LCC analytisch |
| 2 | Run-gedrag | MC **vervangt** analytische run while selected |
| 3 | Presentatie | P10/P50/P90 per FM-metriek: kosten, downtime, faalgebeurtenissen |
| 4 | N | `monte_carlo_n` in modelinstellingen, default 10.000 |
| 5 | Motor v1 | Volledige FM-lifecycle PR1+PR2; PR3/PR4 **uit** |
| 6 | Annuleren | Stop job; **gooi partial resultaten weg** |
| 7 | Seed | `monte_carlo_seed`; leeg = random; tonen in statusstrip |
| 8 | UI | Achtergrondthread + voortgang |
| 9 | Kosten-onzekerheid | **Uit scope v1** — kosten/downtime deterministisch per pad |

### Architectuur — job-pad (ADR-0018)

```text
SimulationRequest (project, path, n, seed, cancel_token)
    → SimulationJob (lifecycle: pending → running → done | cancelled)
    → SimulationEngine (rcm_core: N paths × all FM)
    → SimulationResultStore (analytical_run_id | mc_job_id slots)
    → SimulationPresentation + FM-onzekerheidsband rows
```

- MC orchestration **niet** in `ResultsWorkspaceOrchestrator` derived refresh;
  dedicated `SimulationRunner` (adapter Qt) composed with `BackgroundRunner`
  (prior art: `RunRunner`, `ValidateRunner`).
- Werkruimte-sessie houdt **Run-modus** (`RunMode` enum, slice 95) en optioneel
  actieve `SimulationJob`; analytische `RunResult` blijft in bestaande session
  slot wanneer MC niet actief of na terugkeer naar analytisch.

### Kern — `FMMCResult` en percentielaggregatie

Introduceer Qt-vrij resultaat naast `FMResult`:

```python
@dataclass(frozen=True)
class MetricBand:
    p10: float
    p50: float
    p90: float

@dataclass(frozen=True)
class FMMCResult:
    fm_id: str
    pbs_id: str
    failures: MetricBand      # lifecycle faalmomenten
    downtime_hr: MetricBand   # CM + detectie (+ PM downtime in totaal)
    total_cost_eur: MetricBand  # CM + PM per pad
    n_completed: int          # paden meegeteld (0 bij cancel vóór aggregate)
    seed: int                 # effectieve seed van de run
```

- Percentielen via numpy `percentile` over N pad-scalars per FM (10/50/90).
- `SimulationEngine.run(project, *, n, seed, progress_cb, cancel_check)` →
  `dict[str, FMMCResult]`; **geen** Qt, **geen** disk I/O in core.
- Per simulatiepad: hergebruik bestaande FM-berekeningsbouwstenen waar mogelijk
  (`compute_pm_totals`, task-group dedup volgorde, `effective_lifecycle_end_age`,
  `build_rev_schedule`, distributie-samplers in `distributions`) — **nieuwe**
  stochastic path simulator i.p.v. `expected_failures_lifecycle` enkelvoud.

### Motor-scope PR1+PR2 (GRILL_DECISIONS §3)

**Must implement:**

- Stochastic failure drawing for **random** and **aging** (all
  `AgingDistribution` variants).
- CM cost/downtime/detection delay from drawn failure counts × FM parameters.
- PM/REV/CN executions per path; **task-group dedup** with same ordering as
  analytical `deduplicate_parallel_fm_pm_costs` semantics applied **per path**
  after all FM paths for that iteration (or equivalent single-pass dedup per
  iteration).
- Respect `RCMConfig.aw_mc_lifecycle_horizon`, `modeljaar`, multiplicity,
  planning overlay materialization hook if analytical run uses it (MC run uses
  same materialized project as `run_service._resolve_run_project`).

**Explicitly not in v1:** sampling `TotalCostErrPc` / downtime error columns
from `import_settings` (PR3); effect/consequence cost sampling (PR4).

### Adapter — services to build/extend

| Module (concept) | Verantwoordelijkheid |
|------------------|---------------------|
| `simulation_job_service` (extend) | `SimulationRequest`, cancel token, progress on `SimulationJob`, `MCRunResult` wrapper, presentation builders |
| `simulation_engine_service` (new) | Thin adapter over `rcm_core` MC entry; maps errors to `UserFacingError` |
| `simulation_result_service` (new) | Attach MC results to session; separate from `RunResult`; `build_mc_fm_rows` with bands |
| `SimulationRunner` (new, Qt) | `BackgroundRunner` worker; progress signals; cooperative cancel |
| `run_service` / werkruimte wiring | Branch Start analyse: `RunMode.MONTE_CARLO` → MC runner, else existing analytical |
| `model_settings_service` + dialog | Enable edit `monte_carlo_n` / `monte_carlo_seed`; validate; `requires_rerun` |
| `result_view_service` / FM table | `FMMCResultRow` or band fields on row DTO; column headers P10/P50/P90 per metric |
| `simulation_workspace_binding` | Replace stub job seed=42 with live job from runner; cancel control; progress label |

Type shape — adapter presentation row (prototype):

```python
@dataclass(frozen=True)
class FMMCResultRow:
    fm_id: str
    faalwijze_omschrijving: str
    bouwdeel_naam: str
    failures_band: MetricBand
    downtime_band: MetricBand
    cost_band: MetricBand
    is_nmf: bool
    rf: float
```

### Run-modus switch semantics

- **Analytical selected + Start analyse:** existing `RunRunner` →
  `run_service.run` → `RunResult` → FM point values.
- **MC selected + Start analyse:** `SimulationRunner` → MC engine →
  `MCRunResult` stored in MC slot; FM-resultaten view reads MC rows; Top 10/LCC
  continue reading analytical session run (last analytical `RunResult` or empty
  if never run — document empty-state in UI).
- **Switch MC → analytical without re-run:** show last analytical results if
  present; do not auto-run.
- **Switch analytical → MC without re-run:** show last MC bands if present; do
  not auto-run.
- **Cancel MC:** clear MC slot; status `cancelled`; FM-resultaten in MC mode show
  empty/“geannuleerd” state.

### Seed policy

- `monte_carlo_seed is None` → draw random 32-bit seed at job start; persist
  effective seed on `SimulationJob` and `FMMCResult` aggregate for display.
- Fixed seed → deterministic MC across runs with same project + N.
- Show effective seed in statusstrip via `SimulationPresentation.status_label`.

### Cache namespace

- Analytical FM cache (`.rcm.cache.json`) **unchanged** by MC runs in v1.
- MC results live in session + optional future `.rcm.cache.mc.json` — v1 may
  keep MC **session-only** (no disk cache) to reduce scope; if so, document in
  issues. `SimulationResultStore.mc_job_id` tracks in-memory job identity.
- Do **not** write MC aggregates into analytical cache payload.

### UI integration points

- Enable MC fields in modelinstellingen dialog (remove disabled state + tooltip
  “coming soon”).
- Status strip: progress %, seed, cancel button when `SimulationRunner.busy`.
- FM-resultaten table: in MC mode show band columns (layout choice: triplets
  P10|P50|P90 per metric or compact “band” display — prefer **visible P50 with
  P10–P90 tooltip** or **three sub-columns per metric**; implementer chooses
  minimal readable v1 aligned with slice 80 column patterns).
- Remove slice-95 stub that fabricates `create_simulation_job(seed=42,
  iterations=100)` on combo change without a real run.

### Performance v1

- Sequential N iterations acceptable for v1; parallel path-per-FM **out of
  scope** unless needed for N=10k on large projects (note in issues if slow).
- Cooperative cancel: check `cancel_check` between iterations (and optionally
  between FM batches).

---

## Testing Decisions

Good tests assert **observable behavior** at the highest seam that covers the
contract — no widget internals, no private planner names. Prefer Qt-free adapter
and core tests; pytest-qt only where thread lifecycle is the contract.

### Seam 1 — Core MC engine (Qt-free, highest value)

| Test focus | Behavior |
|------------|----------|
| Seeded single-FM random | Fixed seed + small N → stable P50; failure counts integer on paths |
| Aging distribution parity | Extend `test_aging_monte_carlo` pattern: MC mean failures ≈ analytical `expected_failures` within tolerance (normal, truncated, weibull) |
| REV + repair_quality | MC with REV schedule matches analytical bucket totals within band (reuse slice 24 tolerance ~5%) |
| Task-group dedup | Two FM, one task group: MC PM cost per path ≤ sum of undeduplicated upper bound; matches analytical PM total when failures fixed |
| Deterministic limit | sigma→0 or equivalent controlled setup: P50 ≈ analytical `FMResult` metrics |
| Cancel mid-run | `cancel_check` True after k iterations → engine returns partial **or** raises; adapter must not aggregate partial into `FMMCResult` for UI |

**Modules:** new `rcm_core` MC entry + samplers; `distributions`, `engine` PM helpers.

**Prior art:** `tests/test_aging_monte_carlo.py`, `tests/test_validators.py`
(`CFG_MC_N`), analytical parity tests in slice 66/68.

### Seam 2 — Adapter simulation job lifecycle (Qt-free)

| Test focus | Behavior |
|------------|----------|
| `SimulationJob` transitions | pending → running → done; cancel → cancelled |
| `SimulationResultStore` | analytical_run_id preserved when mc_job_id updated |
| `build_simulation_presentation` | seed, progress %, status_label for running/done/cancelled |
| `simulation_engine_service` | maps core output to `MCRunResult`; UserFacingError on validation failure |
| `build_mc_fm_rows` | P10 ≤ P50 ≤ P90 ordering for sane inputs; row count = FM count |

**Prior art:** `tests/test_slice95_monte_carlo.py` (extend, do not replace).

### Seam 3 — Run-modus integration (Qt-free adapter)

| Test focus | Behavior |
|------------|----------|
| Run branch | Given `RunMode.MONTE_CARLO`, start handler invokes MC service not `run_service.run` |
| Mode switch | MC cancel → switch analytical → last analytical `RunResult` still available |
| Session slots | MC result does not overwrite analytical `RunResult.fm_core_results` |
| Derived refresh | Changing NB filter during idle does not spawn `SimulationJob` |

**Prior art:** `tests/test_results_workspace_orchestrator.py`, slice 92 derived refresh tests.

### Seam 4 — Background runner + cancel (pytest-qt)

| Test focus | Behavior |
|------------|----------|
| `SimulationRunner` progress | Emits progress updates during mocked slow engine |
| Cancel | `cancel()` → job cancelled, no `result_ready` with done MC payload |
| Busy guard | Second `start()` returns False while busy |

**Prior art:** `tests/test_background_runner.py`, `RunRunner` patterns in slice 3.

### Seam 5 — UI smoke (minimal pytest-qt)

| Test focus | Behavior |
|------------|----------|
| MC mode status strip | After mocked MC complete, status label contains seed |
| FM table MC mode | At least one band value visible when session holds `MCRunResult` (mock adapter) |

**Prior art:** `tests/test_slice95_monte_carlo.py` (`test_workspace_shows_mc_seed_in_status_label`).

### CI subset (suggested)

```text
pytest tests/test_slice98_monte_carlo.py tests/test_slice95_monte_carlo.py \
  tests/test_aging_monte_carlo.py tests/test_background_runner.py -q
```

(Add core MC module tests in `test_slice98_*` or `test_monte_carlo_engine.py`.)

### Principles

- Test **gedrag**, not MC internal loop variable names.
- No full GUI suite as gate; HILT covers visual band layout.
- Bump `CACHE_INPUTS_VERSION` only if analytical input hashing changes — MC-only
  code paths should not require bump unless shared FM analytical inputs change.

---

## Out of Scope

**Explicit v1 exclusions (grill + ADR-0018 + epic PR3/PR4):**

- **PR3:** Stochastic sampling of cost/downtime uncertainty from `import_settings`
  (`TotalCostErrPc`, `TotalDownTimeErrPc`, …).
- **PR4:** Gevolgkosten / effect-sampling / consequence cost bands.
- **FM-onzekerheidsband in Top 10** — Top 10 blijft analytische ranking.
- **FM-onzekerheidsband in LCC** — LCC-grafiek blijft analytisch.
- **Portfolio MC**, library dedup MC, server scan — epic §4/§5.
- **Parallel MC** across iterations or ProcessPool per path (performance follow-up).
- **Persistent MC disk cache** — optional follow-up; v1 may be session-only.
- **CLI `run --mc`** — adapter/desktop first; CLI seam may follow in thin slice.
- **Compare slot / A/B MC** — slice 56 compare blijft analytisch.
- **AW parity gate automation** — slice 65 parity blijft analytisch; MC vs AW band
  check is HILT/informative v1, not blocking CI unless spike exists.
- **ValidateWindow MC** — werkruimte only.
- **Scrub-list resurrection** — geen Streamlit MC port.

**Deferred to follow-up PRD/issues:**

- PR3 cost uncertainty bands.
- PR4 consequence sampling.
- MC bands in Top 10/LCC.
- MC cache persistence and incremental MC.

---

## Further Notes

### Voorgestelde tracer bullets (`to-issues`)

Implementatie in dependency order — each independently mergeable with tests:

| # | Tracer | Inhoud |
|---|--------|--------|
| **98a** | Core MC engine | Path simulator, `FMMCResult`, seeded tests, aging/REV parity |
| **98b** | Task-group + PM per path | Dedup semantics per iteration; synthetic 2-FM fixture |
| **98c** | Adapter MC service + session | `SimulationEngine` facade, `MCRunResult`, result store wiring |
| **98d** | SimulationRunner + cancel | Background thread, progress, cooperative cancel, discard partial |
| **98e** | FM-resultaten bands UI | `FMMCResultRow`, table columns, Run-modus branch on Start analyse |
| **98f** | Modelinstellingen N/seed | Enable fields, validate, requires_rerun |
| **98g** | HILT checklist | Demo project MC run, cancel, bands visible, Top 10/LCC unchanged |

### Relatie bestaande code

- **Slice 95:** `RunMode`, `SimulationJob`, `SimulationResultStore`,
  `SimulationPresentation`, status-strip stub — **extend**, do not rewrite enum.
- **Slice 35 import:** `monte_carlo_n` / `monte_carlo_seed` already mapped from
  AW `Project` sheet.
- **Slice 24 / `test_aging_monte_carlo`:** SSOT cross-check for aging buckets;
  MC engine must call same distribution primitives.
- **Slice 43:** Task-group dedup ordering — MC must mirror per path.
- **ADR-0018:** Product and architecture SSOT for this PRD.
- **Parent PRD slice 95:** Fase D roadmap item; compare (slice 96) precedes MC
  per strategic ordering — satisfied before slice 98.

### Risico's

| Risico | Mitigatie |
|--------|-----------|
| N=10k × many FM too slow | Progress + cancel; sequential v1; profile on Gaarkeuken fixture |
| MC/analytical drift | Seeded parity tests; reuse distributions SSOT |
| Partial results after cancel | Adapter discards; test asserts empty MC slot |
| Top 10 shows stale analytical | Document that MC mode does not refresh Top 10 |
| UI column explosion (3× metrics × 3 percentiles) | P50 primary + tooltip or compact band formatter |

### HILT (vóór merge)

1. Open demo project (Haarlem or Gaarkeuken).
2. Set Run-modus Monte Carlo; set N=1000, fixed seed in modelinstellingen.
3. Start analyse — progress and seed visible.
4. FM-resultaten shows P10/P50/P90 for kosten, downtime, faalmomenten.
5. Cancel mid-run — no bands shown; status cancelled.
6. Re-run to completion — bands stable on second run with same seed.
7. Switch to analytical — point estimates from last analytical run.
8. Top 10 and LCC unchanged (analytical numbers).
