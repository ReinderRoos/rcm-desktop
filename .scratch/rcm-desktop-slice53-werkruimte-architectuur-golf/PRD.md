# PRD — RCM2 desktop slice 53 (resultatenwerkruimte architectuur-golf)

**Status:** ready-for-agent  
**Versie:** 1.0  
**Triage-labels:** ready-for-agent  
**Type:** Meta-uitvoering + AFK-verdieping (geen nieuwe eindgebruikersfeatures)  
**Parent:** grill-me architectuur + kanban (2026-05-27); slice **50** (roadmap/reconcile); slice **41** (view-layer deepening); **ADR-0006** (compare legacy-only)  
**Datum:** 2026-05-27

## Problem Statement

De **resultatenwerkruimte** is het primaire analistenvenster, maar blijft een **integratiehub** (~2300 regels view-code) die run, presentatie-cache, modus-rendering (FM-detail, Bijdragen, Tijdsplot/LCC), meekoppelkansen, editing en import in één laag mengt. Slice **41** en **50** hebben de richting vastgelegd (`ProjectSession`, modus-builders, FM-spine, `EditingHost`), maar:

1. **Kanban en code lopen uit sync** — slices **51** en **52** staan op `ready-for-agent` terwijl motor, modelinstellingen en tests al in de repo kunnen staan; agents pakken verkeerde prioriteit of dubbel werk.
2. **Decoupling is half af** — modus-builders bestaan, maar de view roept nog **`loaded.core()`** aan voor render, run, Modelinstellingen en FM-editor; dat schendt het UI/kern-contract (views → adapter → kern).
3. **Test-seams lekken** — adapter-modules importeren **views** voor monkeypatch-dispatch (presentatie-builders); adapter-TDD en AGENTS.md-laagrichting worden ondermijnd.
4. **Orchestratie en cache zijn verspreid** — run → presentatie-rebuild → lazy LCC warmup zit deels in de view, deels over meerdere cache-façades; bugs en invalidatie zijn moeilijk te lokaliseren.
5. **Parallel productwerk vergroot regressierisico** — nieuwe toolbar/panel-logica in hetzelfde venster tijdens refactor verhoogt merge-conflicten en pytest-qt-last.

Ontwikkelaars en agents ervaren trage iteratie en onbetrouwbare “done”-status; analisten merken het indirect via regressies bij modus-wissel en run.

## Solution

Voer een **vaste uitvoeringsgolf** uit in zeven fasen (issues 01–07). **Geen nieuwe productfeatures** in het resultatenwerkruimte-venster tot **PR1a** (issue 03) gemerged is — behalve slice-53-opruiming en orthogonale motor-slices (**42** parallel; **51** alleen buiten dat venster).

| Fase | Doel |
|------|------|
| **01 Reconcile** | Sync triage 46/49/51/52; documenteer sessie A/B/C in handoff |
| **02 Gate 50-05** | Pytest FM-spine-subset + checklist; geen aparte meeting |
| **03 PR1a** | Geen `core()` in render/bind (FM-detail, Bijdragen, LCC) |
| **04 PR1b** | Run, save, Modelinstellingen, FM-editor via `ProjectSession`/adapter-DTO’s |
| **05 Presentatie-seams** | Injecteerbare builders; adapter importeert geen views |
| **06 Orchestrator** | Run→presentatie→modus; dirty guard in adapter; `EditingHost` per venster; presentatie-cache samenvoegen bij voorkeur hier |
| **07 Legacy PR7-A** | Dode scenario/compare-paden werkruimte weg; ADR-0006 intact |

**Merge-freeze (hele golf):** geen nieuwe productlogica in het resultatenwerkruimte-venster tot issue **03** klaar is.

## User Stories

### Coördinatie en kanban

1. Als **product owner** wil ik één slice (**53**) met vaste volgorde, zodat agents niet parallel tegenstrijdige refactors doen op hetzelfde venster.
2. Als **ontwikkelaar** wil ik **reconcile eerst**, zodat issues alleen `done` zijn na acceptance + tests.
3. Als **ontwikkelaar** wil ik sessie-werk **A/B/C** (batch-knop FM-detail, Tijdsplot-collapse defaults, Haarlem fixture) in een handoff, zodat het niet “onzichtbaar” blijft.
4. Als **ontwikkelaar** wil ik een **KANBAN_HANDOFF** voor slice 53, zodat koude sessies niet de grill-chat hoeven te lezen.

### Gate en kwaliteit

5. Als **ontwikkelaar** wil ik dat **50-05** een **zelf-check** is (pytest-subset + checklist), zodat ik niet wacht op een formele meeting tenzij tests rood zijn.
6. Als **ontwikkelaar** wil ik na elke fase een **gedocumenteerde pytest-subset**, zodat regressie snel herhaalbaar is.
7. Als **reliability-analist** wil ik dat **FM-detail, Bijdragen en LCC** na PR1a **visueel identiek** blijven, zodat verdieping geen stille UX-wijziging is.

### PR1a — render/bind zonder kern in view

8. Als **ontwikkelaar** wil ik dat **modus-rendering** geen `loaded.core()` in de view gebruikt, zodat het UI/kern-decoupling-contract geldt voor de hot path.
9. Als **ontwikkelaar** wil ik dat **inspectors en tabellen** data krijgen via **workspace modus-builders** en DTO’s, zodat tests zonder Qt de presentatie-logica raken.
10. Als **ontwikkelaar** wil ik dat **`WorkspaceStateSnapshot`** het modus/scope-contract blijft, zodat bestaande orchestrator-state-tests geldig blijven.
11. Als **ontwikkelaar** wil ik **PR1a als merge-gate** voor het opheffen van de merge-freeze op nieuwe UI in het venster, zodat de volgorde afdwingbaar is.

### PR1b — overige paden via ProjectSession

12. Als **ontwikkelaar** wil ik dat **run, open/save, Modelinstellingen en FM-editor openen** projectdata via **`ProjectSession`** en adapter krijgen, zodat geen tweede toegangspoort tot `RCMProject` in de view blijft.
13. Als **ontwikkelaar** wil ik dat **`set_last_project` / session-setters** gesynchroniseerd blijven met legacy callers, zodat ValidateWindow en tests niet breken tijdens migratie.
14. Als **ontwikkelaar** wil ik dat **LoadedProject** de façade is voor wat de view nog nodig heeft, zodat kernvormwijzigingen gelokaliseerd blijven.

### Presentatie-seams (na PR1b)

15. Als **ontwikkelaar** wil ik **geen adapter→view imports** voor presentatie-builders, zodat pytest adapter-modules patchet, niet view-namen.
16. Als **ontwikkelaar** wil ik **injecteerbare builders** in de adapter, zodat slice 41-#4 testbaar is zonder `results_workspace_window` te monkeypatchen.
17. Als **ontwikkelaar** wil ik dat **LCC lazy warmup** hetzelfde gedrag houdt, zodat slice 37-winst behouden blijft.

### Orchestrator-golf

18. Als **ontwikkelaar** wil ik **één adapter-module** die run-klaar → presentatie-rebuild → modus-bind orkestreert, zodat het venster vooral Qt-widgets en signalen doet.
19. Als **ontwikkelaar** wil ik **grid-dirty-beleid** in de adapter (pure beslissing) en **QMessageBox** alleen in de view, zodat AGENTS.md-laagrichting klopt.
20. Als **ontwikkelaar** wil ik **`EditingHost` per venster** (werkruimte vs legacy ValidateWindow), zodat geen process-global host twee vensters koppelt.
21. Als **ontwikkelaar** wil ik **presentatie-cache** bij voorkeur in dezelfde PR als de orchestrator, zodat invalidatie en warmup op één plek zitten.
22. Als **ontwikkelaar** wil ik dat een te grote diff (**>~400 regels netto**) gesplitst wordt (orchestrator eerst, cache-merge binnen 48u), zodat review beheersbaar blijft.

### Parallel werk (beperkt)

23. Als **ontwikkelaar** wil ik **slice 42** (LCC CM-jaar) **parallel** met PR1a mogen doen, zodat motor-correctheid niet blokkeert op view-refactor.
24. Als **ontwikkelaar** wil ik **slice 51** alleen buiten het resultatenwerkruimte-venster (motor, schema, FM-editor, batch-grid), zodat de freeze niet wordt omzeild.
25. Als **ontwikkelaar** wil ik **geen ValidateWindow-commit** in deze golf, zodat legacy-pad bij **41 PR7** blijft.

### Legacy en ADR

26. Als **product owner** wil ik dat **compare/scenario** alleen legacy ValidateWindow blijft (**ADR-0006**), zodat de werkruimte niet opnieuw scenario-split krijgt.
27. Als **ontwikkelaer** wil ik **PR7 fase A**: dode workspace-paden weg, zodat agents geen dode code volgen.
28. Als **product owner** accepteer ik dat **ValidateWindow inkrimpen** een **latere slice** is, zodat deze golf niet maanden blokkeert.

### Randvoorwaarden

29. Als **ontwikkelaer** wil ik **AGENTS.md** volgen (views → adapter → kern; geen `rcm_core` in views).
30. Als **ontwikkelaer** wil ik **incrementele run** blijven testen via patch op **`rcm_core.incremental_run`**, zodat de bestaande seam behouden blijft.
31. Als **ontwikkelaer** wil ik **geen `rcm_core`-wijziging** in deze slice tenzij unblock voor 42/51 buiten scope ligt, zodat geen onnodige cache-bump.
32. Als **analist** wil ik **geen functionele regressie** in FM-editor, batch-grid en Modelinstellingen na deze golf, zodat slice 44/49/52-winst behouden blijft.

## Implementation Decisions

### Uitvoeringsvolgorde (hard)

```
01 Reconcile → 02 Gate 50-05 → 03 PR1a → 04 PR1b → 05 Presentatie-seams → 06 Orchestrator → 07 Legacy PR7-A
```

Parallel (niet op god-window): **42**; **51** beperkt tot grid/editor/motor.

### Diepe modules (bouwen of verdiepen)

| Module | Rol | Fase |
|--------|-----|------|
| **Reconcile-proces** | Triage + handoff sync | 01 |
| **ProjectSession** + **LoadedProject** | View-facing aggregate; geen `RCMProject` in view na PR1b | 03–04 |
| **workspace_view_service** | `build_fm_detail_view`, `build_bijdragen_view`, `build_lcc_view` → data-DTO’s | 03 (afronden PR1a) |
| **Presentatie-builder registry** (injecteerbaar) | Vervangt adapter→view monkeypatch | 05 |
| **ResultsWorkspaceOrchestrator** (uitbreiding controller) | run-klaar → cache → modus-bind | 06 |
| **WorkspacePresentationSession** (conceptueel) | Samenvoeging cache + lazy LCC + render-index | 06 |
| **DirtyPolicy** (adapter, Qt-vrij) | Mag editor/grid/run; view toont dialoog | 06 |
| **EditingHost** (per venster) | Geen process-global singleton | 06 |
| **Legacy cleanup** | Dode scenario/compare in werkruimte | 07 |

### PR1a acceptance (conceptueel)

- View: geen `loaded.core()` in `_rerender_detail_for_current_scope` en bind-paden (inspectors, tabelvulling, chart-data binding).
- Builders leveren alle FM/Bijdragen/LCC rijen en inspector-velden.
- Selectieherstel en `messages.*` blijven view.

### PR1b acceptance (conceptueel)

- Run starten, project opslaan, Modelinstellingen openen, FM-editor openen: data via `ProjectSession` + adapter; view roept geen `core()` aan.
- Legacy `set_last_project` blijft synchroon met session.

### Presentatie-seams

- Verwijder runtime-import van resultatenwerkruimte uit lazy/view services.
- Tests patchen adapter registry of injected callables.

### Orchestrator-PR

- View verliest o.a. `_load_presentation_cache` en run-complete wiring waar mogelijk.
- **Dirty-session-coordinator shim** verwijderd; adapter exporteert policy.
- **Cache-merge:** bij voorkeur zelfde PR als orchestrator; anders vervolg-PR binnen 48u zonder tussentijdse features op het venster.

### FM-commit en ValidateWindow

- **commit_fm_edit** façade blijft voor werkruimte-editor/grid; **ValidateWindow save** expliciet **out of scope** (41 PR7 later).

### Architectuurprincipes

- Views → adapter only; geen `rcm_core.*` in views (typing-only OK).
- Adapter TDD met pytest-qt waar Qt nodig is; modus-builders unit-testbaar zonder GUI.
- Composeer bestaande seams (`lcc_view_service`, `presentation_cache_service`, `fm_verification_service`, `model_settings_service`) — niet opnieuw uitvinden.

### Relatie andere slices

| Slice | Relatie |
|-------|---------|
| **50** | Reconcile + gate; 50-01..04 done; 53 voert 50-05 + 41-uitvoering uit |
| **41** | PRD blijft bron voor PR2–7 (meekoppel, import, charts); **53** is uitvoeringsgolf PR1 + orchestrator + PR7-A |
| **46/49** | Reconcile in 01; geen nieuw FM-spine-werk |
| **51/52** | Reconcile in 01; implementatie alleen als gap na reconcile |
| **42** | Parallel motor; geen conflict met freeze |

## Testing Decisions

### Wat is een goede test

- Test **gedrag via publieke adapter-interface** (builders, orchestrator, dirty policy, commit-resultaat), niet private view-methoden.
- **Modus-presentatie:** unit-tests op `build_*_view` met fixture-project + `WorkspaceStateSnapshot`; assert rijen, inspector-velden, lege-staat.
- **PR1a-gate:** statische of integratietest dat resultatenwerkruimte geen `loaded.core()` aanroept in render/bind-pad (allowlist voor PR1b-paden tot issue 04 klaar is).
- **Regressie:** bestaande `test_desktop_results_workspace_window`, `test_slice32_*`, `test_slice37_*`, FM-spine-subset na elke issue.
- **Incrementele run:** patch `rcm_core.incremental_run as ir` in adapter-tests (AGENTS.md).

### Modules met tests

| Module | Testtype |
|--------|----------|
| Reconcile | Geen code; handoff + triage |
| workspace_view_service | Unit (pytest, geen Qt) |
| Presentatie-builder registry | Unit + bestaande lazy/cache tests |
| Orchestrator | Unit + smalle pytest-qt smoke |
| DirtyPolicy | Unit |
| EditingHost per venster | Unit (`test_editing_host` uitbreiden) |
| Legacy PR7-A | Unit + geen dode import-paden werkruimte |

### Prior art

- `tests/test_architecture_deepening.py`
- `tests/test_desktop_fm_edit_services.py`, `tests/test_slice49_fm_editor_ux.py`
- `tests/test_slice37_regression.py`
- `tests/test_workspace_modus_ui_ab.py`
- Slice 50 handoff pytest-commando’s

## Out of Scope

- Nieuwe eindgebruikersfeatures in resultatenwerkruimte tijdens freeze (tot PR1a merged).
- **ValidateWindow** inkrimpen (PR7 fase B); **ValidateWindow** `commit_fm_edit`-adoptie.
- **41 PR2–PR5** (meekoppel service extract, import flow, chart widgets move, BackgroundRunner — runner bestaat al).
- Monte Carlo UI; subset-export Excel (slice 35 latere werk).
- Kernwijzigingen en `CACHE_INPUTS_VERSION` bump (tenzij orthogonale slice 42/51 dat vereist).
- Opportunistisch opruimen van ondiepe adapter-shims (`run_decision`, import dialog re-export) — tenzij touched door issue 06.

## Further Notes

- **Grill-conventie:** `x` = volg aanbeveling in architectuur-grill-sessies.
- **Demo-handmatig:** na PR1a Haarlem/demo `.rcm.json` door drie modi (FM-detail, Bijdragen, Tijdsplot).
- **Issue tracker:** `issues/01.md` … `issues/07.md`; start altijd bij **01** tenzij reconcile al `done` is.
- **Slice 41 PRD** blijft leidend voor meekoppel/import/charts; na issue **07** vervolg met 41 PR2 volgens oorspronkelijke volgorde.
