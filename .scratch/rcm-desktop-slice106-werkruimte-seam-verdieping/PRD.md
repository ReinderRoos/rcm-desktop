# PRD — Slice 106: Werkruimte seam-verdieping (architectuurreview Strong)

**Status:** done (issues 01–04)  
**Versie:** 1.0  
**Datum:** 2026-06-18  
**Triage:** `done`  
**Type:** Architectuur-verdieping (geen nieuwe eindgebruikersfeatures)  
**Parent:** `/improve-codebase-architecture` review 2026-06-18 (candidates 1–4, strength **Strong**); slice 105 (UX-polish, gedeeltelijke binding-extractie); slice 104 (FM single-run presentatie); slice 61 (ResultsWorkspaceOrchestrator); slice 79 (view-registry); slice 98/103 (MC-presentatie)  
**Companion docs:** CONTEXT.md (Resultatenwerkruimte, View-registry, Faalwijze-analyse, Adapter Qt, Chrome-profiel), ADR-0012 (LTAP preset), ADR-0018 (Monte Carlo run-modus), ADR-0019 (RCM2 presentatielaag)

> Bundelt de vier **Strong** deepening candidates uit de architectuurreview in één
> uitvoerbare slice. Doel: **locality** en **leverage** aan bestaande adapter-seams;
> de **interface wordt de test surface**; views binden alleen Qt-widgets.

---

## Problem Statement

Na slices 61, 79, 98, 103–105 is de **resultatenwerkruimte** functioneel rijk maar
architecturaal nog **shallow** op vier plekken. Ontwikkelaars en agents moeten voor
één gedrag (navigatie, FM-presentatie, venster-tick, MC-run) tussen meerdere modules
bouncen; bugs zitten in orchestratie tussen adapter-plannen en view-bindings, niet in
de domeinkern.

### 1 — Dubbele navigatie-identiteit (`view_id` ↔ legacy `modus`)

De analist kiest views via dropdown, Beeld-menu of sneltoetsen (`view_id` in de
view-registry). Onder water leven nog **legacy `MODE_*`-strings**, `legacy_modus`
lookup in de registry, en detail-pagina's die op **modus** i.p.v. `view_id` zijn
gekeyed. LTAP (`output.ltap`) en LCC-plot (`output.lcc_plot`) delen één LCC-pagina
terwijl presets verschillen. Begrijpen "welke view is actief?" vereist state +
registry + venster tegelijk — **geen locality**.

### 2 — Gesplitste Faalwijze-presentatiepipeline

Compare- en single-run FM volgen **verschillende** orchestrator-outputs:
compare levert soms voorgebouwde panels; single-run levert ruwe `FMDetailView`-rijen.
`fm_detail_workspace_binding` bouwt presentatie alsnog via
`faalwijze_analyse_service` (metric, NMF/RF, sort, highlight). Presentatiebugs kunnen
in adapter **of** view binding zitten; `RenderPlan` is geen volledige test surface voor
FM-ticks. Dit wijkt af van ADR-0019 (adapter levert aligned-row DTO; views mappen alleen).

### 3 — Resultatenwerkruimte-venster als passthrough-monolith

Slice 62/105 extraheerde **werkruimte-panelen** en deels bindings, maar
`ResultsWorkspaceWindow` blijft ~3000 regels met **100+ eenregelige forwards**
(`_sync_fm_*` → `bind_sync_fm_*`). Een workspace-tick loopt:
state → orchestrator → `_apply_ui_sync` / `_apply_render_plan` → passthrough → binding.
De **deletion test** faalt op wrappers; bindings bevatten wél echte logica. CONTEXT.md
beschrijft het venster als bind-only shell — huidige vorm is overgangsarchitectuur.

### 4 — Simulatie-run-orchestratie in views

Monte Carlo dispatch, compare-slot MC-routing, P50-attach en live-run snapshot zitten
in `simulation_run_binding` (views), terwijl run-complete planning in
`ResultsWorkspaceController` (adapter) zit. `plan_render` krijgt `run_mode` via
`WorkspaceRenderContext` die het venster uit views terugleest. AGENTS.md schrijft
adapter test-first voor; tests op view-binding zijn de verkeerde seam (ADR-0018
functionele MC-regels horen in adapter).

**Indirecte analist-impact:** geen nieuwe knoppen of schermen; wel minder regressies
bij FM/MC-wijzigingen en snellere agent-iteratie.

---

## Solution

Vier tranches in **vaste volgorde** (elk mergebaar, UX-pariteit verplicht):

| Tranche | Doel | Primaire seam |
|---------|------|----------------|
| **106-A** | `active_view_id` canoniek; modus afgeleid of intern | `ResultsWorkspaceState` + view-registry |
| **106-B** | Faalwijze-presentatie volledig in `RenderPlan` | `ResultsWorkspaceOrchestrator` + `faalwijze_analyse_service` |
| **106-C** | Passthroughs weg; domein-bind coordinators | FM/LCC/simulation bind coordinators + dun venster |
| **106-D** | MC/analytisch start + resultaat in adapter | `SimulationWorkspaceController` (nieuw of uitbreiding controller) |

**Pariteit:** alle bestaande HILT103/104/105-gedrag blijft; pytest-regressieset slice
61/79/98/103–105 blijft groen per tranche.

**Line budget:** `results_workspace_window` blijft onder slice-62-gate na 106-C
(statische gate in tests).

---

## User Stories

### Coördinatie en kwaliteit

1. Als product owner wil ik slice 106 als **één tracker** met vier issues, zodat architectuurverdieping niet versnipperd over ad-hoc refactors loopt.
2. Als ontwikkelaar wil ik **tranche-volgorde A → B → C → D**, zodat navigatie-identiteit stabiel is vóór bind-coordinators en FM-bundle.
3. Als ontwikkelaar wil ik **geen `rcm_core`-schema-wijzigingen**, zodat domeinmodel en tabulaire editing-pipeline onaangetast blijven.
4. Als ontwikkelaar wil ik dat **views alleen via adapter** de kern raken, zodat AGENTS.md-discipline intact blijft.
5. Als ontwikkelaar wil ik per tranche een **pytest-subset** in KANBAN_HANDOFF, zodat regressie snel herhaalbaar is.
6. Als auditor wil ik dat **ADR-0006/0007** (compare in werkruimte) functioneel gelijk blijven, zodat scenariovergelijking niet regressieert.

### 106-A — Navigatie: `view_id` canoniek

7. Als analist wil ik met **Ctrl+1/Ctrl+2** nog steeds tussen Input- en Output-zijde wisselen met **sticky view per zijde**, zodat navigatiegewoonte behouden blijft.
8. Als analist wil ik **LTAP** en **LCC-plot** als aparte views in Beeld-menu, zodat preset-gedrag (ADR-0012) expliciet blijft ook als ze dezelfde onderliggende panelen delen.
9. Als ontwikkelaar wil ik dat **`set_active_view(view_id)`** de enige mutatie is voor view-wissel, zodat dropdown, menu en sneltoetsen één pad delen.
10. Als ontwikkelaar wil ik **`modus` afgeleid** uit view-registry (`legacy_modus` of mapping), zodat orchestrator en venster niet twee bronnen lezen.
11. Als ontwikkelaar wil ik **detail-pagina's keyed by `view_id`** (of registry-groep), zodat LTAP/LCC-plot niet per ongeluk dezelfde sticky state delen waar presets verschillen.
12. Als ontwikkelaar wil ik **input-views** (`input.faalwijzen`, entity grids) zonder legacy modus-string, zodat Input-zijde alleen `active_view_id` gebruikt.
13. Als ontwikkelaar wil ik dat **`normalize_modus`** en verwijderde modi (bv. `bijdragen`) migratie behouden, zodat oude tests en persisted state niet breken.
14. Als ontwikkelaar wil ik **statische gates** dat nieuwe code geen `set_modus` direct aanroept buiten compat-laag, zodat dual identity niet terugkeert.

### 106-B — Faalwijze-presentatiebundle in RenderPlan

15. Als analist wil ik **FM single-run** tabel en diagram identiek gedrag houden (metric, horizon, NMF/RF, highlight), zodat slice 104/105 UX intact blijft.
16. Als analist wil ik **FM scenario compare** (tabel + diagram) identiek gedrag houden, zodat HILT103 compare-pariteit behouden blijft.
17. Als analist wil ik **MC P10/P50/P90** kolommen in FM-detail nog steeds horizon-conform (slice 103), zodat ADR-0018-presentatie niet regressieert.
18. Als ontwikkelaar wil ik **`FaalwijzePresentationBundle`** (of gelijkwaardige naam) op `RenderPlan` voor FM-kind, zodat single-run en compare dezelfde adapter-outputstructuur gebruiken.
19. Als ontwikkelaar wil ik dat **`plan_render`** alle calls naar `build_faalwijze_*_presentation` doet, zodat presentatielogica niet in views leeft.
20. Als ontwikkelaar wil ik dat **`fm_detail_workspace_binding` alleen mapt** bundle → `FMSingleRunTableModel` / `FMCompareTableModel` / chart widgets, zodat de binding shallow wordt.
21. Als ontwikkelaar wil ik **geen fallback-rebuild** in binding wanneer orchestrator-veld `None` is, zodat ontbrekende data een expliciete lege/toestand is (testbaar).
22. Als ontwikkelaar wil ik **view-mode** (`tabel`/`diagram`) en **NMF/RF-toggle** nog in `WorkspaceStateSnapshot`, zodat UI-sync en render dezelfde snapshot lezen.
23. Als ontwikkelaar wil ik dat **inspector-selectie** na rerender view-side blijft (zoals slice 61), zodat Qt-focus niet in adapter belandt.

### 106-C — Bind coordinators; venster dunner

24. Als ontwikkelaar wil ik **geen eenregelige `_sync_*` / `_set_*` forwards** meer op het venster, zodat deletion test op wrappers slaagt.
25. Als ontwikkelaar wil ik **`FmDetailBindCoordinator`** (of module-equivalent) die `RenderPlan` + `WorkspaceUiSyncPlan` op FM-widgets toepast, zodat FM-tick locality op één plek zit.
26. Als ontwikkelaar wil ik **LCC- en simulation-bind** op dezelfde coordinator-vorm, zodat het patroon herhaalbaar is (niet verplicht één mega-class).
27. Als ontwikkelaar wil ik dat **`_apply_render_plan` en `_apply_ui_sync`** coordinators aanroepen i.p.v. 20 losse bind-imports, zodat het venster leesbaar blijft.
28. Als ontwikkelaar wil ik **widget-referenties** in coordinators of panel-constructie, niet verspreid over 100 venster-attributen waar mogelijk, zodat binding-locality verbetert.
29. Als ontwikkelaar wil ik **slice-62 line gate** gehaald na cleanup, zodat monolith-shrink meetbaar is.
30. Als ontwikkelaar wil ik **statische import-gates** dat `build_faalwijze_*` niet in views voorkomt, zodat 106-B niet teruglekt.

### 106-D — SimulationWorkspaceController

31. Als analist wil ik **Run** nog steeds analytisch of MC starten afhankelijk van run-modus, zodat dagelijks gedrag gelijk blijft.
32. Als analist wil ik **Run A/B** in MC-modus compare-slots vullen zonder live analytical session, zodat slice 103 compare-MC belofte intact blijft.
33. Als analist wil ik **annuleren en voortgang** ongewijzigd in de UI, zodat alleen orchestratie verhuist.
34. Als ontwikkelaar wil ik **`plan_start_analyse(ctx)`** Qt-vrij die `StartAnalysePlan` levert (analytical | monte_carlo, compare_slot optioneel), zodat dispatch getest wordt zonder venster.
35. Als ontwikkelaar wil ik **`plan_mc_result_apply(ctx, mc_result)`** voor P50-attach, store-update en rerender-trigger metadata, zodat resultaat-routing locality in adapter zit.
36. Als ontwikkelaar wil ik dat **views alleen `SimulationRunner`-signalen wiren** en plannen uitvoeren, zodat AGENTS.md-seam klopt.
37. Als ontwikkelaar wil ik **`WorkspaceRenderContext.run_mode`** uit sessie/snapshot, niet uit view-combo direct, zodat render en start-run dezelfde bron lezen.
38. Als ontwikkelaar wil ik bestaande **`simulation_workspace_service`** en **`simulation_engine_service`** hergebruiken, zodat geen duplicate MC-motor-logica ontstaat.
39. Als ontwikkelaar wil ik **pytest op controller** i.p.v. `test_slice98_simulation_run_binding` als primaire seam (binding-test mag blijven als dunne smoke), zodat interface de test surface is.

### Regressie en acceptatie

40. Als ontwikkelaar wil ik dat **`test_results_workspace_orchestrator`** uitgebreid wordt voor FM-bundle en navigatie, zodat plannen regressievrij blijven.
41. Als ontwikkelaar wil ik dat **`test_desktop_results_workspace_state`** view_id-migratie dekt, zodat sticky navigatie getest blijft.
42. Als ontwikkelaar wil ik dat **slice 103/104/105 FM-tests** groen blijven per tranche, zodat presentatie-pariteit bewaakt wordt.
43. Als product owner wil ik **HILT-handcheck** alleen na 106-B/C/D indien FM/MC-touch, zodat menselijke acceptatie niet elke tranche blokkeert.

---

## Implementation Decisions

### Tranche-volgorde en afhankelijkheden

```
106-A (navigatie) → 106-B (FM bundle) → 106-C (coordinators)
                      ↘
                       106-D (simulation) — kan parallel na 106-A, merge na 106-B aanbevolen
```

- **106-A** eerst: orchestrator en detail-routing lezen daarna één sleutel.
- **106-B** vóór **106-C**: coordinators krijgen stabiele `RenderPlan`-vorm.
- **106-D** kan na **106-A** starten; conflicten met venster-runners oplossen vóór **106-C**.

### Modules (bouwen / wijzigen)

| Module | Tranche | Actie |
|--------|---------|-------|
| **ResultsWorkspaceState** | A | `active_view_id` canoniek; `modus` afgeleid; deprecate directe `set_modus` |
| **View-registry** | A | `legacy_modus` wordt afleiding, geen tweede navigatie-API |
| **ResultsWorkspaceOrchestrator** | A, B | Routing op `view_id`; `RenderPlan` + presentation bundle |
| **Faalwijze-analyse service** | B | Bundle-builder; geen nieuwe presentatie in views |
| **RenderPlan** (FM-tak) | B | Unified bundle i.p.v. raw rows + optionele compare rebuild |
| **Fm-detail workspace binding** | B, C | Alleen map; logic naar adapter/coordinator |
| **FmDetailBindCoordinator** | C | Apply FM ui_sync + render |
| **LccBindCoordinator**, **SimulationBindCoordinator** | C | Zelfde patroon waar passthroughs nu zitten |
| **ResultsWorkspaceWindow** | C | Construct panels, subscribe state, delegate apply |
| **SimulationWorkspaceController** | D | `plan_start_analyse`, `plan_mc_result_apply` |
| **ResultsWorkspaceController** | D | Optioneel: run-complete + simulation controller samenvoegen of delegatie |
| **Simulation run binding** | D | Dun: runner signals → execute plan |
| **WorkspaceRenderContext** | D | `run_mode` uit sessie/snapshot |

### Interface-beslissingen (conceptueel)

**106-A — Navigatie**

```python
# Canoniek
state.set_active_view(view_id: str) -> None

# Afgeleid (read-only op snapshot)
snapshot.effective_modus  # voor orchestrator branches die nog modus-achtig denken
registry.modus_for_view(view_id) -> str | None
```

Detail-page stack: `view_id` (of `page_key` uit registry) i.p.v. `MODE_*` alleen.

**106-B — Presentation bundle**

```python
@dataclass(frozen=True)
class FaalwijzePresentationBundle:
    mode: Literal["single_run", "compare"]
    single: FaalwijzeSingleRunPresentation | None
    compare: FaalwijzeComparePresentation | None
    # chart payloads indien niet afgeleid uit table models

@dataclass(frozen=True)
class RenderPlan:
    kind: ...
    fm_bundle: FaalwijzePresentationBundle | None  # wanneer kind == "fm" | vergelijkbaar
```

Binding: `apply_fm_render(plan.fm_bundle, widgets)` — geen `build_faalwijze_*` import.

**106-C — Coordinator**

```python
class FmDetailBindCoordinator:
    def apply_ui_sync(self, plan: FmToolbarPlan | None, snapshot: WorkspaceStateSnapshot) -> None: ...
    def apply_render(self, plan: RenderPlan, snapshot: WorkspaceStateSnapshot) -> None: ...
```

Venster houdt coordinator-instanties; geen `def _sync_fm_*` forwards.

**106-D — Simulation**

```python
@dataclass(frozen=True)
class StartAnalysePlan:
    mode: Literal["analytical", "monte_carlo"]
    compare_slot: str | None
    planning_overlay: ...
    force_recompute: bool

class SimulationWorkspaceController:
    @staticmethod
    def plan_start_analyse(ctx: WorkspaceRunContext) -> StartAnalysePlan | None: ...
    @staticmethod
    def plan_mc_result_apply(ctx: WorkspaceRunContext, result: MCRunResult) -> McResultApplyPlan: ...
```

Views: `runner.start(plan)` / `controller.apply_mc_result(plan)` — geen `_start_monte_carlo` in views.

### Architectuurprincipes (onveranderd)

- UI/kern-decoupling: views → adapter → `rcm_core`.
- Adapter Qt-vrij waar plannen; Qt alleen in views/coordinator apply.
- Geen scrub-list terugkeer zonder ADR.
- ADR-0019: presentatie in adapter + theme; views mappen.
- ADR-0018: MC-regels en slot-routing in adapter.

### Schema / API

- Geen wijziging aan `RCMProject`, `ENTITY_SCHEMAS`, of `.rcm.json`-vorm.
- Geen nieuwe CLI-subcommando's.

---

## Testing Decisions

### Wat maakt een goede test

- Test **gedrag over de seam**: gegeven snapshot + context → plan/bundle; geen assert op private helpers.
- **Geen pytest-qt** voor adapter-plannen tenzij onvermijdelijk (venster-smoke blijft beperkt).
- **Pariteit**: bestaande orchestrator/state tests uitbreiden, niet vervangen.
- Per tranche: subset groen vóór merge; volledige `test_results_workspace_orchestrator` + slice 103–105 FM/MC na 106-B/D.

### Test-seams (hoogste mogelijke)

| Tranche | Seam | Module onder test | Prior art |
|---------|------|-------------------|-----------|
| **106-A** | `set_active_view` / snapshot | `ResultsWorkspaceState`, view-registry | `test_desktop_results_workspace_state`, `test_slice79_*` |
| **106-B** | `plan_render` → `fm_bundle` | `ResultsWorkspaceOrchestrator`, faalwijze-analyse | `test_results_workspace_orchestrator`, `test_slice104_*`, `test_slice105_fm_*` |
| **106-C** | Coordinator apply met mock widget bag | FM bind coordinator | `test_slice105_fm_detail_binding` (herstructureer naar coordinator) |
| **106-D** | `plan_start_analyse`, `plan_mc_result_apply` | `SimulationWorkspaceController` | `test_slice98_*`, `test_slice100_mc_*` |

**Geen nieuwe seem** tenzij coordinator apply niet testbaar is zonder Qt — dan mock widget namespace (bestaand patroon in slice 105 binding tests).

### Gates (statisch)

- Geen `build_faalwijze_*` in `rcm_desktop/views/` (106-B/C).
- Geen `set_modus(` buiten state compat-laag (106-A).
- `results_workspace_window` line count ≤ gate (106-C).
- Geen `dispatch_start_analyse` business logic in views na 106-D (alleen plan execute).

---

## Out of Scope

- **Candidate 5** (single `WorkspaceChromePlan` per tick) — slice 105 issue 11 / vervolg backlog.
- **Candidate 6** (FM policy/table consolidatie, wide `FMResultsTableModel` deprecatie) — aparte cleanup-slice na 106-B bewezen.
- Nieuwe eindgebruikersfeatures (rapportage, import, validate-window).
- `rcm_core`-motor, cache-vingerafdruk, Monte Carlo-algoritme wijzigingen.
- ValidateWindow-retirement (ADR-0017).
- Visuele reskin boven ADR-0019 (nieuwe tokens/QSS) — alleen architectuur.
- FM-editor UX (slice 105 blockers) — tenzij coordinator-extractie editor raakt.
- Numerieke MC vs analytisch gelijkheid (ADR-0018 expliciet geen belofte).

---

## Further Notes

- Deze PRD is **bewust agent-ready**: issues 01–04 mappen 1:1 op tranches.
- **HILT**: na 106-B minimaal FM single-run + compare smoke; na 106-D MC compare-slot.
- Overlap met slice 105 PRD (binding extractie) wordt hier **afgerond**; 105 leverde eerste binding-module, 106 maakt seam diep en testbaar.
- Bij conflict met oude `MODE_*` tests: migreer tests naar `view_id`, behoud één release compat-shim in state.
- Toekomstige ADR optioneel: "view_id is enige navigatiesleutel" als 106-A landt — alleen aanbieden als grill sessie load-bearing reason geeft.
