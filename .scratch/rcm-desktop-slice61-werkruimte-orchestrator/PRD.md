# PRD — RCM2 desktop slice 61 (resultatenwerkruimte-orchestrator, slice A)

**Status:** ready-for-agent  
**Versie:** 1.0  
**Triage-labels:** ready-for-agent  
**Type:** Architectuur-verdieping (geen nieuwe eindgebruikersfeatures)  
**Parent:** `/improve-codebase-architecture` grill-sessie (2026-06-05); slice **53** issue 06 (deel orchestrator done); slice **58** (bewust géén venster-orchestratie); **ADR-0007** (A/B compare in werkruimte)  
**Datum:** 2026-06-05

## Problem Statement

De **resultatenwerkruimte** is na slice 53 PR1 en issue 06 nog steeds een **shallow view-monolith** (~3000 regels): bij elke `WorkspaceStateSnapshot`-tick moet een onderhouder `_on_workspace_state_changed` (toolbar-zichtbaarheid, modus-sync) én `_rerender_detail_for_current_scope` (modus-routing, compare placeholders, aanroep modus-builders) lezen. Run-complete planning zit wél Qt-vrij in `ResultsWorkspaceController`, maar **snapshot → presentatie** niet.

Gevolgen:

1. **Geen locality** — begrijpen “modus LCC + compare_mode + scope-wissel” vereist honderden regels view-code; bugs zitten in orchestratie, niet in builders.
2. **Interface is geen test surface** — modus-builders zijn unit-testbaar, maar de beslisboom wanneer ze worden aangeroepen alleen via pytest-qt of handmatig klikken.
3. **Seam leakage** — view importeert tientallen adapter-modules direct naast `workspace_session_service`; PR1a-gates vereisen builders expliciet **in** `_rerender` (moet na deze slice omgekeerd worden).

Ontwikkelaars willen slice A uit de architectuur-review: een **diepe orchestrator-module** die UI-sync-plannen en render-plannen levert; de view bindt alleen Qt-widgets.

## Solution

Introduceer **`ResultsWorkspaceOrchestrator`** in de adapter: composeert bestaande `ResultsWorkspaceController` (run/validate blijft daar), levert Qt-vrije plannen voor workspace-ticks. Lever in **drie PRs**:

| PR | Levert | View-winst |
|----|--------|------------|
| **PR1** | `plan_ui_sync` + geneste `WorkspaceUiSyncPlan` | `_on_workspace_state_changed` → `_apply_ui_sync` |
| **PR2** | `plan_render` + `plan_workspace_tick` + `RenderPlan` | `_rerender_detail_for_current_scope` → `_apply_render_plan` |
| **PR3** | Dode `_sync_*` helpers verwijderen; statische gates | Line budget ≤2000; builders uit view render-pad |

Geen wijziging aan eindgebruikers-UX, meekoppel-semantiek (ADR-0005), of legacy compare (ADR-0006). A/B compare placeholders en single-run modi blijven functioneel identiek.

## User Stories

### Coördinatie

1. Als **product owner** wil ik slice **61** als **slice A** na slice 53/58, zodat orchestratie-verdieping niet wacht op meekoppel- of LCC-cache-merge.
2. Als **ontwikkelaar** wil ik **vaste PR-volgorde** (UiSync → Render → cleanup), zodat elke merge reviewbaar blijft en regressies gelokaliseerd zijn.
3. Als **ontwikkelaar** wil ik dat **ResultsWorkspaceController** ongewijzigd blijft qua run/validate-interface, zodat slice 53 issue 06 tests groen blijven.

### UI-sync (PR1)

4. Als **ontwikkelaar** wil ik **`plan_ui_sync(prev, current)`** Qt-vrij, zodat moduswissel-toolbar-gedrag zonder GUI getest wordt.
5. Als **ontwikkelaar** wil ik **geneste panel-plannen** (`BijdragenToolbarPlan`, `LccToolbarVisibilityPlan`, `FmToolbarPlan`, `CompareChromePlan`, `CollapsePanelsPlan`), zodat `_on_workspace_state_changed` leesbaar blijft per domeinmodus.
6. Als **analist** wil ik bij wissel **Bijdragen ↔ LCC ↔ FM-detail** dezelfde toolbar-zichtbaarheid als vandaag, zodat geen UX-regressie optreedt.
7. Als **ontwikkelaar** wil ik **`refresh_kpi: bool`** in het sync-plan wanneer PBS-scope wijzigt, zodat KPI-tabel-gedrag behouden blijft zonder KPI-build in de orchestrator (view roept nog `build_kpi_table_for_session`).
8. Als **ontwikkelaar** wil ik dat **`_ensure_whatif_for_meekoppel()`** view-side blijft, zodat Qt-side-effect niet in de adapter belandt.
9. Als **ontwikkelaar** wil ik dat **meekoppel tabeldata** (`sync_meekoppel_panel`) **buiten** PR1 blijft, zodat ADR-0005 discovery niet mee verhuist.

### Render (PR2)

10. Als **ontwikkelaar** wil ik **`plan_render(current, ctx)`** die bestaande modus-builders aanroept, zodat geen presentatielogica gedupliceerd wordt.
11. Als **ontwikkelaar** wil ik **`RenderPlan`** als tagged union met bestaande DTOs (`FMDetailView`, `BijdragenView`, `LCCView`, compare panels), zodat view `_bind_*` / `_render_lcc_view` behoudt.
12. Als **analist** wil ik bij **compare_mode** zonder gevulde slots **placeholders** zien, zodat A/B UX (ADR-0007) intact blijft.
13. Als **ontwikkelaar** wil **`plan_render`** bij `split_depth == all_splits` zelf **`render_index.on_workspace_state_reset()`** aanroepen, zodat cache-invalidatie locality bij render-planning zit.
14. Als **ontwikkelaar** wil ik dat **`on_slot_updated`** bij compare-run **in de view** blijft (vóór `plan_render`), zodat event-gedreven en snapshot-gedreven flows gescheiden blijven.
15. Als **ontwikkelaar** wil ik **`plan_workspace_tick`** als compose van ui_sync + render voor `_on_workspace_state_changed`, zodat één call site overblijft.
16. Als **ontwikkelaar** wil ik dat **`_on_compare_slot_result_ready`** en **`_on_presentation_rebuild_result_ready`** alleen **`plan_render`** aanroepen, zodat geen hacky `prev=current` nodig is.
17. Als **analist** wil ik **FM-rijselectie-restore** na rerender zoals vandaag, zodat FM-detail inspecteur-gedrag gelijk blijft (view-side na bind).

### LCC chrome (bewust view-side)

18. Als **ontwikkelaar** wil ik **`_sync_lcc_chrome`** (overlay-knoppen, statuslabel; needs session) gekoppeld houden aan LCC bind, zodat het niet in `WorkspaceUiSyncPlan` verdwijnt.

### Cleanup & gates (PR3)

19. Als **ontwikkelaar** wil ik **statische gates** dat `build_fm_detail_view` / `build_bijdragen_view` / `build_lcc_view` **niet** meer in het view render-pad staan, zodat leakage niet terugkeert.
20. Als **ontwikkelaar** wil ik **`test_slice53_issue03_pr1a_gate`** omdraaien (builders in orchestrator, niet in `_rerender`), zodat CI de nieuwe seam bewaakt.
21. Als **ontwikkelaar** wil ik **line budget ≤2000** voor `results_workspace_window`, zodat monolith-shrink meetbaar is.
22. Als **ontwikkelaar** wil ik dode **`_sync_kpi_panel_visibility`** e.d. verwijderen na orchestrator-wire, zodat geen dubbele paden bestaan.

### Niet-functioneel

23. Als **auditor** wil ik **geen `rcm_core`-wijzigingen**, zodat domeinmodel en tabulaire editing-pipeline onaangetast blijven.
24. Als **ontwikkelaar** wil ik **views → adapter only** handhaven, zodat AGENTS.md-discipline intact blijft.
25. Als **ontwikkelaar** wil ik **Nederlandse copy** via bestaande message constants, zodat geen nieuwe UI-strings in orchestrator komen.

## Implementation Decisions

### Modules (bouwen/wijzigen)

| Module | Actie | Diepte |
|--------|-------|--------|
| **ResultsWorkspaceOrchestrator** | Nieuw in adapter | **Diep**: `plan_ui_sync`, `plan_render`, `plan_workspace_tick` |
| **ResultsWorkspaceController** | Ongewijzigd (run/validate) | Orchestrator delegeert run-complete; geen merge |
| **WorkspaceUiSyncPlan** + geneste plannen | Nieuw frozen dataclasses | Beschrijft visibility/checked/index per panel |
| **RenderPlan** | Nieuw tagged union | Wrapt bestaande modus-DTOs + `kind` + compare placeholder |
| **WorkspaceRenderContext** | Nieuw context-dataclass | `session`, `compare_slots`, `project_total_presentation`, `render_index`, `prev_lcc_snapshot` |
| **workspace_detail_render_scope** | Hergebruik | `split_depth` blijft; orchestrator roept aan |
| **workspace_view_service** modus-builders | Hergebruik | Orchestrator roept `build_*_view` aan — geen duplicate |
| **CompareWorkspaceController** | Hergebruik | Compare-run complete blijft; view → slot update → `plan_render` |
| **Resultatenwerkruimte-view** | Dunner | `_apply_ui_sync`, `_apply_render_plan`; geen routing in `_rerender` |

### Publieke interface (beslissingsvorm)

Drie methodes op orchestrator (geen monolithische tick-only API):

```python
@dataclass(frozen=True)
class WorkspaceRenderContext:
    session: ProjectSession | None
    compare_slots: CompareSlotState
    project_total_presentation: PresentationProjectTotal | None
    render_index: WorkspaceRenderIndex  # mutable; builders gebruiken get_or_build
    prev_lcc_snapshot: WorkspaceStateSnapshot | None

class ResultsWorkspaceOrchestrator:
    @staticmethod
    def plan_ui_sync(
        previous: WorkspaceStateSnapshot | None,
        current: WorkspaceStateSnapshot,
    ) -> WorkspaceUiSyncPlan: ...

    @staticmethod
    def plan_render(
        current: WorkspaceStateSnapshot,
        ctx: WorkspaceRenderContext,
        *,
        split_depth: RenderSplitDepth | None = None,
    ) -> RenderPlan: ...

    @staticmethod
    def plan_workspace_tick(
        previous: WorkspaceStateSnapshot | None,
        current: WorkspaceStateSnapshot,
        ctx: WorkspaceRenderContext,
    ) -> WorkspaceTickPlan: ...  # ui_sync + render + afgeleide split_depth
```

**WorkspaceUiSyncPlan** (conceptueel genest):

```python
@dataclass(frozen=True)
class WorkspaceUiSyncPlan:
    detail_page_modus: str
    modus_button: str
    source_toggle: str
    metric_combo_index: int
    bijdragen: BijdragenToolbarPlan | None
    lcc_toolbar: LccToolbarVisibilityPlan | None
    fm_toolbar: FmToolbarPlan | None
    compare: CompareChromePlan
    collapse: CollapsePanelsPlan
    refresh_kpi: bool
```

**RenderPlan** (conceptueel):

```python
@dataclass(frozen=True)
class RenderPlan:
    kind: Literal[
        "empty", "compare_placeholder",
        "fm", "bijdragen", "lcc",
        "bijdragen_compare", "lcc_compare",
    ]
    fm: FMDetailView | None = None
    bijdragen: BijdragenView | None = None
    lcc: LCCView | None = None
    compare_panels: ... | None = None
```

Orchestrator roept bij `all_splits` **`ctx.render_index.on_workspace_state_reset()`** vóór builders. **`on_slot_updated`** blijft caller-side (compare handler).

### PR-volgorde (hard)

```
PR1 plan_ui_sync → view _apply_ui_sync
PR2 plan_render + plan_workspace_tick → view _apply_render_plan
PR3 delete dead helpers + gates + line budget
```

Geen parallelle PRs op dezelfde view-handlers.

### ADR- en slice-relaties

- **ADR-0007:** Compare placeholders en A/B-slots via bestaande compare view services; geen `CompareRunner` in werkruimte.
- **ADR-0006:** Legacy compare blijft ValidateWindow-only.
- **ADR-0005:** Meekoppel preview/apply handlers blijven view-side; alleen collapse/zichtbaarheid via UiSyncPlan.
- **Slice 53 issue 06:** Run-complete controller blijft; deze slice verdiept snapshot-tick.
- **Slice 58:** Pad/rapport-seams onafhankelijk; geen conflict.

## Testing Decisions

### Test-seams (hoogste eerst — bevestig vóór implementatie)

| Seam | Wat getest wordt | Waarom hoog |
|------|------------------|-------------|
| **`ResultsWorkspaceOrchestrator.plan_ui_sync`** | Gegeven prev/current snapshots → toolbar/collapse/compare chrome plan | Pure adapter; geen Qt |
| **`ResultsWorkspaceOrchestrator.plan_render`** | Modus, compare, scope, split_depth → RenderPlan kind + DTOs | Gedrag achter view routing |
| **`ResultsWorkspaceOrchestrator.plan_workspace_tick`** | Compose ui + render + afgeleide split_depth | Eén tick zoals state-changed |
| **Statische view-gate (PR3)** | Geen `build_*_view` in view render-pad; orchestrator import aanwezig | Voorkomt seam leakage |
| **Bestaande pytest-qt / window tests** | Regressie only | Geen nieuwe UI-features |

Geen tests op private `_apply_*` method-volgorde; wel op orchestrator **interface** (given → plan fields).

### Wat is een goede test

- Test **extern gedrag** via orchestrator-interface: snapshot(s) + context → plan-velden (visibility flags, `RenderPlan.kind`, DTO presence).
- Gebruik **fixture-project + WorkspaceStateSnapshot** builders; geen `QApplication` voor orchestrator unit tests.
- **Render index:** vul cache vóór tick met scope-change → assert cache leeg na `plan_render` met `all_splits`.
- View: bestaande smokes blijven groen; geen assert op regeltelling in runtime tests (alleen statische gate PR3).

### Modules met tests

| Module | Testbestand | Prior art |
|--------|-------------|-----------|
| ResultsWorkspaceOrchestrator | `test_results_workspace_orchestrator.py` (nieuw) | `test_slice53_issue06_orchestrator.py`, `test_workspace_detail_render_scope.py` |
| View gate PR3 | `test_slice61_orchestrator_gate.py` (nieuw) | `test_slice53_issue03_pr1a_gate.py` (omdraaien) |
| Regressie | bestaande workspace tests | `test_desktop_results_workspace_window.py`, `test_slice37_*` |

### CI-gate (na elke PR)

```text
python -m pytest tests/test_results_workspace_orchestrator.py tests/test_slice53_issue06_orchestrator.py tests/test_desktop_results_workspace_window.py tests/test_slice37_* -q
```

PR3 extra:

```text
python -m pytest tests/test_slice61_orchestrator_gate.py -q
```

## Out of Scope

- Meekoppel workflow consolidatie (discovery → apply in één service); slice 54/55/E uit architectuur-review.
- LCC presentatie-cache stack merge (`LccPresentationService`); aparte candidate.
- `FmEditCommitPipeline` / faalwijze-editor controller extractie.
- `CompareRunPipeline` delen legacy/workspace.
- `workspace_session_service` façade opruimen.
- Widget-constructie splitsen (`LccWorkspacePanel` e.d.).
- `_sync_lcc_chrome` verplaatsen naar orchestrator.
- Meekoppel tabeldata (`sync_meekoppel_panel`) in orchestrator.
- Run-complete / validate-hydrate herschrijven (blijft `ResultsWorkspaceController`).
- Line budget `<1500` (stretch; gate is ≤2000).
- Wijzigingen aan modus-builder implementaties (`build_*_view` internals).
- ValidateWindow orchestratie.

## Further Notes

- **Grill-sessie 2026-06-05:** Alle implementatiebeslissingen hierboven zijn expliciet gekozen (scope B, module B, RenderPlan B, UiSyncPlan B, API B, delivery C, acceptance B, render_index D).
- **Architectuur HTML-review:** Top recommendation was resultatenwerkruimte-orchestrator; deze PRD is slice A daarvan.
- **CONTEXT.md:** Na merge optioneel termen *ResultsWorkspaceOrchestrator*, *WorkspaceTickPlan*, *WorkspaceUiSyncPlan* toevoegen onder Adapter Qt.
- **Agent-volgorde:** PR1 → PR2 → PR3; geen feature-werk op het venster tussen PR2 en PR3.
