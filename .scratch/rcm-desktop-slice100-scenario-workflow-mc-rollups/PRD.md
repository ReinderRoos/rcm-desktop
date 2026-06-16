# PRD — Slice 100: Scenario-workflow v2 + MC P50-rollups

**Status:** done  
**Versie:** 1.0  
**Datum:** 2026-06-13  
**Triage:** `done`  
**Type:** Feature (adapter + view; geen schema-drift op `RCMProject`)  
**Parent:** grill-with-docs sessie post-HILT98 (2026-06-13); slice 98 (MC engine v1); slice 56 (A/B compare v1); slice 95 (dual-project compare)  
**Supersedes (gedeelte):** ADR-0018 presentatie v1 (“Top 10/LCC analytisch”); ADR-0007 v1-scope (“FM-detail single-run”; Run → A/B workflow)  
**Companion docs (zelfde grill):** ADR-0018 amendement, ADR-0007 amendement, CONTEXT.md (Run-modus, scenariovergelijking)

> Synthese van **10 grill-besluiten** (2026-06-13) na GO met kanttekening voor slice 98.
> Geen her-interview — dit document is de implementatiebron voor scenario-workflow,
> MC P50 in aggregate views, en uitbreiding van vergelijking naar FM-resultaten.

---

## Problem Statement

Slice 98 leverde een werkende **Monte Carlo run-modus** met **FM-onzekerheidsbanden**
(P10/P50/P90), maar de dagelijkse analisten-workflow blijft gefragmenteerd:

- **MC-run vult alleen FM-resultaten.** Top 10 en LCC blijven leeg of analytisch
  terwijl de analist in MC-modus werkt — inconsistent met Availability Workbench,
  waar een MC-run de volledige resultatenpresentatie voedt.
- **Run → A / Run → B** (slice 56) is een technisch A/B-model dat niet aansluit op
  het mentale model “eerst één analyse, dan optioneel een variant, dan vergelijken”.
  In MC-modus start Run A/B wel MC, maar aggregate views tonen nog geen MC-uitkomsten.
- **Vergelijk A ↔ B** is een losse toggle naast **Start analyse**; analisten moeten
  zelf onthouden wanneer een run “live” is vs “bevroren scenario”.
- **FM-vergelijking** ontbreekt — ADR-0007 sloot FM-detail bewust uit v1, maar
  analisten willen naast Top 10 en LCC ook **FM-resultaten** side-by-side vergelijken
  (metric-gestuurd: kosten, downtime/NB, faalmomenten).
- **Gemengde run-modus** (scenario 1 analytisch, scenario 2 Monte Carlo) is vandaag
  niet expliciet ondersteund in compare-presentatie.

Zonder herziening blijft MC een FM-only experiment; scenariovergelijking blijft
ontkoppeld van Run-modus en van de gewenste “Start analyse → Extra scenario →
Vergelijk scenario's”-flow.

## Solution

Herontwerp de **resultatenwerkruimte-runflow** en breid MC-presentatie uit:

1. **MC-run = volledige run-workflow (v1: P50)** — na geslaagde MC-run vullen
   **Top 10**, **LCC** en **FM-resultaten** vanuit MC; aggregate views gebruiken
   **P50** per FM (zelfde grafieken/tabelstructuur als analytisch). FM-detail
   blijft banden tonen (P50 kolom + P10/P90 tooltip).
2. **Nieuwe scenario-knoppen** — vervang Run → A/B en Vergelijk A ↔ B door:
   - **Start analyse** — draait huidige config (analytisch of MC); ververst
     **live run**; overschrijft **niet** bevroren scenario-slots.
   - **Extra scenario** — bevriest huidige live run als **scenario 1**, opent
     volledige pre-run config voor **scenario 2** (scope, overlay, what-if,
     passieve taken, Run-modus, MC-params).
   - **Vergelijk scenario's** — opt-in toggle; split in Top 10, LCC (metric-gestuurd)
     en FM-resultaten (metric-gestuurd kolommen).
   - **Wis vergelijking** — wist scenario-slots; zichtbaar zodra ≥1 slot gevuld.
3. **Twee scenario's (v1)** — referentie + variant; Extra scenario overschrijft
   altijd scenario 2.
4. **Gemengde run-modus** — elk scenario bewaart eigen run-modus; vergelijking
   normaliseert naar één getal per metric (MC → P50, analytisch → punt).
5. **Dual-project compare blijft apart** — *Vergelijk modellen…* (twee `.rcm.json`)
   is gescheiden product van *Vergelijk scenario's* (zelfde project).

**Fase 2 (expliciet later):** onzekerheidsbanden (P10/P90) in Top 10/LCC
aggregate views — niet in deze slice.

---

## User Stories

### MC-run als volledige workflow

1. As a reliability-analist, I want a Monte Carlo run to populate **Top 10** after
   completion, so that I see ranked failure modes without switching to analytical mode.
2. As a reliability-analist, I want a Monte Carlo run to populate the **LCC-plot**
   after completion, so that lifecycle curves reflect my stochastic analysis.
3. As a reliability-analist, I want Top 10 and LCC to use **MC P50** per faalwijze
   in v1, so that aggregate views stay comparable to analytical presentation.
4. As a reliability-analist, I want FM-resultaten to continue showing **P10/P50/P90
   bands** in MC mode, so that FM-level uncertainty remains visible.
5. As a reliability-analist, I want switching Run-modus without re-run to preserve
   both analytical and MC result namespaces, so that I can flip modes without losing work.
6. As a trainer, I want clear labeling when Top 10/LCC show MC P50 vs analytical
   point values, so that users are not misled during mixed workflows.

### Start analyse (live run)

7. As a reliability-analist, I want **Start analyse** always visible after validate,
   so that I have one obvious action to run the current configuration.
8. As a reliability-analist, I want Start analyse to respect the selected **Run-modus**
   (analytical or Monte Carlo), so that I do not need separate MC-only buttons.
9. As a reliability-analist, I want Start analyse to update only the **live run**
   (Top 10, LCC, FM for current view), so that I can iterate without disturbing
   frozen scenario slots.
10. As a reliability-analist, I want **Herbereken analyse** when modelinstellingen
    or pre-run config changed since last run, so that stale results are obvious.
11. As a reliability-analist, I want MC runs to show progress, seed, and cancel in
    the status strip, so that long simulations remain controllable (unchanged from slice 98).
12. As a reliability-analist, I want a cancelled MC run to leave live views empty
    without corrupting frozen scenarios, so that partial results never persist.

### Extra scenario (bevriezen + variant-config)

13. As a reliability-analist, I want **Extra scenario** enabled after at least one
    successful live run, so that I cannot compare before I have a baseline.
14. As a reliability-analist, I want clicking Extra scenario to **freeze the current
    live run as scenario 1**, so that scenario 1 captures what I just analyzed.
15. As a reliability-analist, I want Extra scenario to open **full pre-run config**
    for scenario 2 (PBS-scope, planning-overlay, what-if, passieve taken, Run-modus,
    `monte_carlo_n` / `monte_carlo_seed`), so that I can explore meaningful variants.
16. As a reliability-analist, I want no separate Project/CM/PM dropdown in Extra
    scenario, so that scenario differences go via overlay/LCC-presets as today.
17. As a reliability-analist, I want scenario snapshots to store **run-modus,
    overlay, scope, and run result** at freeze/run moment, so that labels explain
    what each scenario represents.
18. As a reliability-analist, I want a readable **scenario label** (e.g. “Scenario 1
    — PM-baseline, analytisch”, “Scenario 2 — 3 REV passief, MC N=10k”), so that
    split panels are self-explanatory.
19. As a reliability-analist, I want overlay or scope changes **after** a scenario
    is frozen **not** to alter that scenario’s stored results, so that comparison
    stays trustworthy until explicit re-run.
20. As a reliability-analist, I want Extra scenario always to target **scenario 2**,
    so that v1 stays a simple referentie + variant model.

### Vergelijk scenario's

21. As a reliability-analist, I want **Vergelijk scenario's** enabled only when
    **both** scenario 1 and scenario 2 are filled, so that I never see a half-empty compare.
22. As a reliability-analist, I want Vergelijk scenario's as an **opt-in toggle**
    (default off), so that single-run UX remains the norm.
23. As a reliability-analist, I want compare mode in **Top 10** to show two columns
    (scenario 1 | scenario 2) with shared PBS scope and filters, so that ranking
    differences are scannable.
24. As a reliability-analist, I want compare mode in **LCC** to follow the **global
    metric** (kosten → kosten/jaar; faalmomenten → faalmomenten/jaar; NB → NB-proxy/jaar),
    so that LCC comparison matches Top 10 and FM semantics.
25. As a reliability-analist, I want compare mode in **FM-resultaten** as a **horizontal
    split** (scenario 1 | scenario 2) with **metric-driven columns** (NB → downtime,
    Faalmomenten → failures, Kosten → cost), so that FM comparison aligns with the
    selected metric toggle.
26. As a reliability-analist, I want MC scenarios in compare to show **P50 values**
    in FM split columns (bands only in tooltip as today), so that compare stays numeric.
27. As a reliability-analist, I want **mixed run-mode compare** (scenario 1 analytical,
    scenario 2 MC) to work by comparing **point vs P50** per metric, so that I can
    contrast deterministic baseline with stochastic variant.
28. As a reliability-analist, I want **one PBS selection** and **one taaktype-filterset**
    to drive both scenario panels, so that navigation stays unified.
29. As a reliability-analist, I want PBS/filter changes in compare mode to **re-render
    both scenarios without a new motor run**, so that exploration stays fast.
30. As a reliability-analist, I want **synchronized calendar year** and **shared Y-axis
    max** in stacked LCC compare, so that visual comparison is fair (extend slice 56 behavior).
31. As a reliability-analist, I want an empty scenario slot to show a placeholder
    (“Start analyse, daarna Extra scenario”), so that next steps are obvious.
32. As a reliability-analist, I want **Wis vergelijking** when ≥1 scenario slot is
    filled, so that I can reset without reloading the project.

### Knoppen en deprecatie slice 56 UX

33. As a reliability-analist, I want **Run → A** and **Run → B** removed from the
    toolbar, so that one mental model replaces dual slot-run buttons.
34. As a reliability-analist, I want **Vergelijk A ↔ B** replaced by **Vergelijk
    scenario's**, so that wording matches the Extra-scenario workflow.
35. As a reliability-analist, I want **Zet huidige run als A/B** seed-knoppen removed
    or folded into Extra scenario, so that seeding is not a separate confusing path.
36. As a reliability-analist, I want Run-modus to remain in the **validatiestrip**
    for the next Start analyse, so that mode selection stays visible during iteration.

### Lifecycle en invalidatie

37. As a reliability-analist, I want scenario slots cleared on **project path change,
    validate/import success, and empty project**, so that stale cross-project compare
    cannot occur (extend slice 56 rules).
38. As a reliability-analist, I want scenario data **session-only** (no disk persistence
    in v1), so that complexity stays bounded.
39. As a reliability-analist, I want a failed run on scenario 2 to leave scenario 1
    intact, so that partial failures are recoverable.
40. As a developer, I want legacy **CompareRunner** and ValidateWindow compare UI
    untouched, so that ADR-0006 legacy stack remains isolated.

### Dual-project compare (slice 95)

41. As a reliability-analist, I want **Vergelijk modellen…** (two `.rcm.json` files,
    balanced FM diff) to remain a **separate menu action**, so that cross-project
    review is not conflated with same-project scenario compare.
42. As a product owner, I want no attempt to merge dual-project and scenario compare
    in v1, so that scope stays deliverable.

### Regressie en parity

43. As a developer, I want analytical-only workflows (no Extra scenario) to behave
    like today’s single-run UX after this change, so that existing users are not disrupted.
44. As a developer, I want MC seeded parity tests (P50 ≈ analytical point) to remain
    green when building P50 rollups, so that MC integration stays credible.
45. As a trainer, I want documentation (CONTEXT, ADRs) updated to reflect MC Top 10/LCC
    and new scenario buttons, so that agents and humans share one vocabulary.

---

## Implementation Decisions

### Product / state machine

- **Live run** — `ProjectSession.run` (analytical) and/or `ProjectSession.mc_run`
  (MC); driven by Start analyse; powers default (non-compare) views.
- **Scenario slots** — reuse binary slot model (`scenario_1`, `scenario_2`; may map
  internally to existing `CompareSlotState` keys A/B with renamed UI labels).
- **Freeze trigger** — scenario 1 is **not** auto-frozen after first Start analyse;
  freeze happens **only** on Extra scenario click (current live run → scenario 1 snapshot).
- **Scenario snapshot** must capture: `run_mode`, frozen `RunResult` or MC-derived
  presentation payload, overlay/planning state, scope id, optional label metadata,
  timestamp/summary for UI.
- **Start analyse without Extra scenario** — refreshes live run only; scenario 1/2
  snapshots unchanged.
- **Extra scenario** — (1) freeze live → scenario 1 if not already in “variant editing”
  state; (2) present full pre-run config UI for scenario 2; (3) next successful run
  fills scenario 2; user may run via Start analyse while in variant-editing mode.
- **Compare toggle** — `compare_mode` (or renamed `scenario_compare_mode`) gates split
  layout in Top 10, LCC, and **FM-resultaten** (extends ADR-0007).
- **Max scenarios** — exactly **two** in v1; no slot list UI.

### MC P50 rollups (aggregate views)

- Introduce adapter conversion **MC → synthetic analytical-shaped run** for presentation:
  P50 per FM for failures, downtime, cost; reuse existing Top 10 / LCC / PBS rollup
  pipeline (`build_run_result` or parallel `build_run_result_from_mc_p50`).
- **`top10_lcc_reads_analytical_slot`** (and related guards) change semantics: live
  view reads **active run source** — analytical slot when Run-modus analytical and
  completed; **MC P50 rollup** when Run-modus MC and MC completed.
- FM-detail in MC mode remains **`mc_bands`** source (unchanged band presentation).
- Single-run MC without prior analytical run must populate Top 10/LCC (fixes HILT98
  kanttekening empty aggregate views).
- **Out of scope v1:** P10/P90 envelopes on Top 10 bars or LCC stacked bands (fase 2).

### Mixed-mode compare normalization

- Compare view service accepts per-slot either analytical `RunResult` or MC snapshot.
- For Top 10/LCC/FM compare columns, extract **scalar per metric**:
  - analytical → existing point fields;
  - MC → P50 from `FMMCResult` / rollup row.
- FM compare in MC-only slot: show P50 column + band tooltip (same as single-run MC).

### UI / chrome

- Toolbar button set (visibility rule **D** from grill):
  - **Start analyse** — always after validate;
  - **Extra scenario** — enabled after ≥1 successful live run;
  - **Vergelijk scenario's** — enabled when both scenarios filled; toggles compare layout;
  - **Wis vergelijking** — visible when ≥1 scenario filled.
- Remove: Run → A, Run → B, Vergelijk A ↔ B, Zet huidige run als A/B (unless retained
  hidden for migration — prefer remove + test update).
- Run-modus combo stays in validation strip (applies to next Start analyse).
- Hide duplicate MC-only Start analyse hiding logic from slice 98 HILT fix — **one**
  Start analyse button for both modes.

### Module boundaries (adapter-first)

- Extend **`CompareSlotSnapshot`** / **`CompareSlotState`** to hold run-modus + unified
  result reference (merge or coordinate with **`CompareMcSlotState`** — prefer single
  slot state type to avoid parallel A/B MC vs analytical stores).
- New or extended **`ScenarioWorkflowService`** (name TBD): freeze live, put scenario 2,
  clear, labels, `both_filled`, invalidation hooks.
- Extend **`simulation_workspace_service`**: run-source resolution for Top 10/LCC/FM.
- Extend **`CompareViewService`** + **`CompareSplitLayoutService`**: FM split + metric
  column selection; mixed-mode scalars.
- Extend **`ResultsWorkspaceOrchestrator`**: FM compare branch (today FM excluded from
  compare in v1).
- Extend **`ResultsWorkspaceWindow`** + binding modules: button wiring, compare toggle,
  Extra scenario config dialog/sheet (reuse existing overlay/planning/meekoppel UI pieces).
- **`CompareRunRunner`** / **`SimulationRunner`**: Start analyse dispatches analytical or
  MC based on Run-modus; scenario 2 run uses frozen config from Extra scenario session.

### ADR / glossary (companion, same slice epic)

- Amend **ADR-0018**: MC-run feeds Top 10/LCC via P50; FM bands unchanged; fase 2 bands
  called out.
- Amend **ADR-0007**: scenario workflow supersedes Run → A/B; FM compare in scope;
  metric-driven LCC compare.
- Update **CONTEXT.md** Run-modus and scenariovergelijking entries accordingly.

### Schema / core

- **No `RCMProject` schema changes.**
- P50 rollup is adapter presentation; optional lightweight DTO for MC rollup rows in
  adapter layer only.

---

## Testing Decisions

### Test seams (hoogste bruikbare laag)

De implementatie wordt getest op deze seams — **adapter unit/integration first**,
minimale Qt smoke in `ResultsWorkspaceWindow`:

| Seam | Wat wordt bewezen |
|------|-------------------|
| **`simulation_workspace_service`** | Run-modus → juiste bron voor Top 10/LCC/FM; MC-only session populates aggregates; mode flip zonder rerun behoudt namespaces |
| **MC P50 rollup factory** (bijv. `build_run_result_from_mc_p50`) | P50 FM rows → `RunResult`-vormige metrics/rows; parity binnen tolerantie t.o.v. analytisch; PBS/Top10 ranking werkt |
| **`CompareSlotState` / scenario workflow** | freeze on Extra scenario; Start analyse raakt slots niet; clear/invalidate; both_filled; mixed run_mode metadata |
| **`CompareViewService`** | scalar normalization (point vs P50); metric-gestuurde FM kolommen; LCC metric mapping; empty slot placeholders |
| **`ResultsWorkspaceOrchestrator`** | compare_mode → split plan voor Top 10, LCC, **FM**; geen compare plan zonder both_filled |
| **`ResultsWorkspaceWindow` smoke** | knoppen zichtbaarheid D; geen Run A/B; Vergelijk scenario's toggle; regressie single-run |

### Testprincipes

- Test **observeerbaar gedrag** via publieke adapter-interfaces; geen Qt-widget internals.
- Gebruik bestaande fixtures (`sample_project`, seeded MC `n=200`) voor determinisme.
- Mock motor alleen waar run-duur irrelevant is; één integratiepad met echte
  `SimulationEngine` voor P50 rollup sanity.
- Regressie: legacy ValidateWindow compare niet in workspace source; slice 98 MC tests
  blijven groen.

### Modules met tests (verplicht)

| Module | Type | Prior art |
|--------|------|-----------|
| MC P50 rollup + workspace run-source | unit | `tests/test_slice98_simulation_run_binding.py`, `tests/test_slice98_monte_carlo.py` |
| Scenario workflow / slot state | unit | `tests/test_compare_slot_state.py`, `tests/test_compare_mc_slot_state.py` (indien merged) |
| CompareViewService (FM + mixed mode) | unit | `tests/test_compare_view_service.py` |
| ResultsWorkspaceOrchestrator | unit | `tests/test_results_workspace_orchestrator.py` |
| ResultsWorkspaceWindow | smoke | `tests/test_desktop_results_workspace_window.py`, `tests/test_slice56_workspace_ab_compare_smoke.py` |

### Regressie-gates

- Analytical single-run (geen scenario) gedrag equivalent aan pre-slice-100 baseline.
- Slice 98: FM bands, cancel, seed reproducibility ongewijzigd.
- Slice 56: LCC Y-max sync + kalenderjaar sync blijven werken in scenario compare.
- Dual-project compare (`Vergelijk modellen…`) tests ongewijzigd groen.

---

## Out of Scope

- **P10/P90 banden in Top 10 of LCC** aggregate views (fase 2 — aparte grill/PRD).
- **Delta-tabel** (B − A per FM) — latere slice.
- **Meer dan twee scenario's** of scenario-lijst UI.
- **Persistente scenario-slots op schijf** over app-sessies.
- **PR3/PR4 MC** — stochastische kosten/downtime/gevolgkosten sampling.
- **Samenvoegen** van dual-project compare en scenario compare.
- **ValidateWindow** compare UI wijzigingen of retirement (fase E blijft apart).
- **Automatische dubbele run** (CM+PM in één klik).
- **Stale-badges** na FM-edit zonder validate.

---

## Further Notes

- Deze PRD **herziet** slice 98 presentatiekeuze (“Top 10/LCC analytisch”) en slice 56
  UX (Run → A/B) op basis van post-HILT98 grill — implementatie pas na companion
  ADR-amendementen en CONTEXT.md sync.
- **Relatie slice 98:** MC engine, job-pad, FM bands, background cancel blijven;
  deze slice wijzigt vooral **presentation routing** en **scenario workflow**.
- **Relatie slice 56:** hergebruik `CompareSlotState`, split layout, compare view
  service — generaliseer van “A/B run buttons” naar “Extra scenario / Vergelijk scenario's”.
- **Relatie slice 95:** `Vergelijk modellen…` blijft parallel; geen shared UI state.
- **Implementatie-volgorde (suggestie):** ADR/CONTEXT → MC P50 rollup + live view routing
  → scenario state machine → toolbar/compare UI → FM compare split → smoke/regressie.
- **Risico:** P50 rollup moet presentation-scale, NB-filter, and NMF/RF enrichment
  consistent toepassen zoals analytische FM rows — centraliseer in één adapter helper.
- **Risico:** Extra scenario “full pre-run config” moet bestaande overlay/meekoppel
  UI hergebruiken zonder duplicate state — orchestrator snapshot discipline (slice 61).
- Uitvoering in kleine issues via `to-issues` skill aanbevolen na PRD-review.
