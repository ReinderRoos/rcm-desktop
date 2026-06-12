# PRD — RCM2 desktop slice 50 (architectuur-roadmap: reconcile, FM-spine, view-deepening)

**Status:** ready-for-agent  
**Versie:** 1.0  
**Triage:** ready-for-agent  
**Type:** Meta-coördinatie + AFK-verdieping (geen nieuwe eindgebruikersfeatures)  
**Parent:** `/improve-codebase-architecture` + grill-me (2026-05-26)  
**Relatie:** slice **46** (FM batch-grid + orchestratie, issues 01–09), slice **49** (editor UX/waarschuwingen), slice **41** (view-layer deepening, **uitgesteld** tot 46-09), `ARCHITECTURE_DEFERRED.md` (slice 45), **ADR-0006** (compare legacy-only)  
**Datum:** 2026-05-26

## Problem Statement

Na slice 44/45/49 en gedeeltelijke implementatie van slice 46 ontstaat **architectuurfrictie** die agents en ontwikkelaars vertraagt:

1. **Kanban en code lopen uit sync** — issues 46-01..09 en 49-01..05 staan op `ready-for-agent` terwijl contracten, panel, `replace_fm_scope`, consistency en grid-contract al in de repo staan. Zonder reconcile ontstaat **dubbel werk** of verkeerde prioriteit.
2. **Twee FM-bewerkingspaden zonder één orchestratie-seam** — **faalwijze-editor** (volledige scope) en **batch faalwijzen-grid** (schema-gedreven subset) delen de **tabulaire editing-pipeline** nog niet consequent; globale **grid-registry** en Qt in de adapter (`dirty_session_coordinator`) maken gedrag moeilijk te testen en te volgen.
3. **Shallow en lekkende seams** — dubbele FM-bundle-loaders (project vs. sessie), adapter→view **test-dispatchers** voor presentatie-builders, en een **resultatenwerkruimte** die nog te veel orchestratie bevat t.o.v. slice 41-doelen.
4. **Parallelle slices botsen op dezelfde bestanden** — slice 41 (view deepening) en slice 46 raken dezelfde vensters en editing-paden; zonder vaste volgorde stijgen merge-conflicten en regressierisico.

Analisten merken dit indirect (trage iteratie, regressies bij grid+editor); ontwikkelaars en agents merken het direct (geen betrouwbare “done”-status, onduidelijke seam om te mocken).

## Solution

Formaliseer en voer een **vaste uitvoeringsroadmap** uit in vier fasen — **geen** nieuw productoppervlak, wel **locality** en **leverage** aan bestaande seams:

| Fase | Doel | Primaire tracker |
|------|------|------------------|
| **0 — Reconcile** | Sync Kanban met code + tests voor slice **49** en **46** | `KANBAN_HANDOFF.md` per slice; issue-triage |
| **1 — FM-spine (46)** | Milestones 46→47→48 via bestaande issues 01–09 | `.scratch/rcm-desktop-slice46-fm-edit-fase2/` |
| **2 — Post-46 verdieping** | Unified FM-scope loader + commit-façade | Nieuwe tracers na 46-09 (onder deze PRD of slice 41) |
| **3 — View-deepening (41)** | Presentatie-seam, orchestratie, cache, legacy validate | `.scratch/rcm-desktop-slice41-view-layer-deepening/` |

**Parallel werk (toegestaan):** orthogonale slices (**42** LCC-CM-correctheid, **35** import) — **niet** 44/45 of paden die `faalwijzen_*`, `fm_edit_*`, gedeelde **EditingSession** of resultatenwerkruimte-editing raken.

**Architectuurkandidaten → planning (grill-me 2026-05-26):**

| # | Verdieping | Wanneer |
|---|------------|---------|
| 1 | Eén **FM-edit scope**-loader (project \| sessie) | Na **46-08/09** |
| 2 | **Commit-façade** (draft → pipeline → validate → materialize → incrementele run) | Incrementeel in **46-07/08**; volledige façade na **46-09** |
| 3 | **EditingHost** i.p.v. globale grid-registry | **46-08** introductie; **46-09** registry weg |
| 4 | Presentatie-builders zonder adapter→view test-dispatch | **Slice 41** |
| 5 | Resultatenwerkruimte-orchestratie | **Slice 41** |
| 6 | Presentatie-cache / lazy façade samenvoegen | **Slice 41** |
| 7 | Publieke rij-API tabulaire model (filter-proxy) | **46-03** |
| 8 | Legacy validate / compare opruimen | **Slice 41** PR7; **ADR-0006** |

Tijdens fase 1: **geen opportunistische** wijzigingen aan #4–#6/#8; alleen *unblock*-fixes met vermelding in **41-tech-debt** in slice-46-handoff.

## User Stories

### Roadmap en coördinatie

1. Als product owner wil ik een **eenduidige volgorde** (reconcile → 46 → post-46 → 41), zodat agents niet parallel tegenstrijdige refactors doen.
2. Als ontwikkelaar wil ik **KANBAN_HANDOFF** per actieve slice, zodat een koude sessie niet de hele chat hoeft te lezen.
3. Als ontwikkelaar wil ik dat slice **49** na reconcile op **`done`** staat als tests groen zijn, zodat geen dubbele UX-werk onder 49 loopt tijdens 46.
4. Als ontwikkelaar wil ik dat slice **46** issues alleen **`done`** worden na acceptance + tests, zodat het bord betrouwbaar is.
5. Als ontwikkelaar wil ik **41-tech-debt** vastgelegd zien (test-seams, unified loader, commit-façade), zodat post-46 werk niet vergeten wordt.

### Fase 0 — Reconcile

6. Als ontwikkelaar wil ik per issue **46-01..09** acceptance criteria afvinken tegen de repo, zodat gaps expliciet zijn.
7. Als ontwikkelaar wil ik per issue **49-01..05** hetzelfde doen, zodat batch 1/2 status helder is.
8. Als ontwikkelaar wil ik een **pytest-subset** per slice documenteren in handoff, zodat regressie snel te herhalen is.
9. Als ontwikkelaar wil ik het **eerste echte open** 46-issue na reconcile kennen, zodat implementatie niet bij 01 begint als 01–04 al klaar zijn.

### Fase 1 — FM-spine (bestaande slice 46 PRD)

10. Als analist wil ik **failure_type** en **NMF** in het batch-grid kunnen corrigeren, zodat homogene modelfouten niet per editor hoeven (46-01).
11. Als analist wil ik **must-kolommen** (MTTF, sigma, omschrijving, functie, repair_quality) in het grid, zodat batch-herstel uitbreidt (46-02).
12. Als analist wil ik **snelfilters, zoek en bulk op zichtbare rijen**, zodat grote projecten beheersbaar blijven (46-03).
13. Als ontwikkelaar wil ik dat de filter-proxy **geen private model-API** gebruikt, zodat refactors veilig zijn (arch #7 in 46-03).
14. Als ontwikkelaar wil ik **ValidateFaalwijzenPanel** host-neutraal, zodat ValidateWindow en werkruimte hetzelfde panel delen (46-04).
15. Als ontwikkelaar wil ik **`replace_fm_scope`** als canonieke FM-scope apply, zodat splice-logica op één plek zit (46-05).
16. Als ontwikkelaar wil ik **FmEditBundleAssembler** in de adapter, zodat de editor geen entity-splice doet (46-06).
17. Als analist wil ik dat editor-OK via **RunRunner** loopt en niet de UI bevriest, zodat grote projecten bruikbaar blijven (46-07).
18. Als analist wil ik een **dirty guard** als het grid dirty is en ik de editor open, zodat stille overschrijving wordt voorkomen (46-07).
19. Als analist wil ik dat grid-wijzigingen in de **gedeelde EditingSession** zichtbaar zijn in de editor, zodat één waarheid geldt (46-08).
20. Als ontwikkelaar wil ik een expliciete **EditingHost** i.p.v. globale registry, zodat hosts geen verborgen koppeling hebben (46-08, arch #3).
21. Als analist wil ik het batch-grid ook vanuit de **resultatenwerkruimte** kunnen openen, zodat ValidateWindow niet verplicht is (46-09).
22. Als ontwikkelaar wil ik de **grid-registry** verwijderen na host-introductie, zodat geen twee parallelle waarheden blijven (46-09).
23. Als ontwikkelaar wil ik **Qt-dialogen voor dirty-check** in views, niet in adapter, zodat adapter Qt-vrij blijft waar mogelijk (46-08/09).

### Fase 2 — Post-46 verdieping

24. Als ontwikkelaar wil ik **één interface** om FM-edit scope te laden uit project of edit-sessie, zodat drift tussen twee loaders verdwijnt (arch #1).
25. Als ontwikkelaar wil ik **één commit-façade** voor editor en grid-save, zodat validate→materialize→incrementele run niet dubbel in views staat (arch #2).
26. Als ontwikkelaar wil ik dat post-46 modules **pytest-adapter** testbaar zijn zonder Qt, zodat de interface de test surface is.

### Fase 3 — View-deepening (slice 41, na 46-09)

27. Als ontwikkelaar wil ik **ProjectSession** en modus-builders als enige seam voor project+run in de werkruimte, zodat views geen `RCMProject` importeren (41 PR1).
28. Als ontwikkelaar wil ik **injecteerbare presentatie-builders** (LCC, bijdragen) zonder adapter→view import, zodat tests niet monkeypatchen op view-namen (arch #4).
29. Als ontwikkelaar wil ik **werkruimte-orchestratie** uit het god-window, zodat run→presentatie-rebuild op één plek zit (arch #5).
30. Als ontwikkelaar wil ik **één presentatie-cache-module**, zodat lazy warmup niet over twee façades verspreid is (arch #6).
31. Als product owner wil ik dat **compare/scenario** alleen legacy ValidateWindow blijft, zodat ADR-0006 geldt (arch #8).

### Randvoorwaarden en kwaliteit

32. Als ontwikkelaar wil ik dat alle wijzigingen **AGENTS.md** volgen (views → adapter → kern), zodat scrub-list en ADR’s intact blijven.
33. Als ontwikkelaar wil ik bij registry-wijzigingen **editing schema parity** groen houden, zodat geen drift ontstaat.
34. Als ontwikkelaar wil ik incrementele run blijven testen via patch op **`rcm_core.incremental_run`**, zodat de bestaande seam behouden blijft.
35. Als analist wil ik **geen functionele regressie** in FmEditorDialog of FM-detail na architectuurwerk, zodat slice 49-winst behouden blijft.

## Implementation Decisions

### Diepe modules (bouwen, uitbreiden of consolideren)

| Module | Rol | Diepte | Fase |
|--------|-----|--------|------|
| **Reconcile-proces** (geen code-module) | Issue-triage + handoff sync | — | 0 |
| **FaalwijzenGridContract** + **FaalwijzenEditService** | Schema-gedreven kolommen; `apply_change` / `apply_bulk_change` | Hoog | 1 (46) |
| **FaalwijzenTableModel** | Publieke `row_view` (of equivalent) voor filter | Medium | 1 (46-03) |
| **FaalwijzenFilterProxy** | Dun; alleen Qt-filter op publieke model-API | Laag | 1 |
| **ValidateFaalwijzenPanel** | Host-neutraal grid UI | Medium | 1 |
| **EditingSession.replace_fm_scope** | Atomische FM-bundle in sessie | Hoog | 1 |
| **FmEditBundleAssembler** | Draft → **FmEditBundle** | Hoog | 1 |
| **FmEditCommitService** / **RunRunner**-pad | Async commit; incrementele run | Hoog | 1 |
| **DirtySessionCoordinator** → view + **EditingHost** | Dirty guard; expliciete host i.p.v. registry | Hoog | 1→2 |
| **EditingHost** | Sessie, save-handler, actieve grid; geen globals | Hoog | 1 (08–09) |
| **FmEditScopeLoader** (nieuw) | `load_fm_edit_scope(source: Project \| Session, fm_id)` | Hoog | 2 |
| **FmEditCommitFacade** (nieuw) | Eén entry: draft/bundle → pipeline → run policy | Hoog | 2 |
| **PresentationBuilderRegistry** (nieuw) | Injecteerbare LCC/bijdragen-builders | Medium | 3 (41) |
| **ResultsWorkspaceOrchestrator** (verdieping controller) | Run-result → cache rebuild → modus side-effects | Hoog | 3 (41) |
| **WorkspacePresentation** (merge lazy + cache) | Eén module voor warmup/rebuild-beslissing | Medium | 3 (41) |

### Fase 0 — Reconcile (gedrag)

- Doorloop **49-01..05** en **46-01..09** acceptance vs. repo.
- Update `issues/NN.md`: triage `done` of open gap; vink acceptance `[x]` waar bewezen.
- Werk `KANBAN_HANDOFF.md` bij (bestaan al voor 46 en 49).
- Documenteer pytest-commando’s en **eerste open issue** voor 46.
- Geen nieuwe features onder **49** tijdens 46-spine; gaps → **46-issue** of bugfix.

### Fase 1 — Bindend aan slice 46 PRD

- Implementatie **niet** herdefiniëren in deze PRD — volg `.scratch/rcm-desktop-slice46-fm-edit-fase2/PRD.md` en issues 01–09.
- **Verplicht uit grill-me:** publieke rij-API in **46-03**; **EditingHost** in **08**, registry weg in **09**; geen opportunistische 41-werkzaamheden.

### Fase 2 — Post-46 (na issue 09)

**FmEditScopeLoader** — interface (conceptueel):

```text
load_fm_edit_scope(
  source: LoadedProject | EditingSession,
  fm_id: str,
) -> FmEditBundle
```

- Intern: één graph-walk; adapters voor bron zijn implementatiedetail.
- Vervangt parallelle `load_bundle` / `load_bundle_from_session` als enige publieke seam.

**FmEditCommitFacade** — interface (conceptueel):

```text
commit_fm_edit(
  session: EditingSession,
  bundle: FmEditBundle,
  *,
  path: Path | None,
  save_to_disk: bool,
  run_policy: RunPolicy,  # blocking | RunRunner callback
) -> FmEditCommitResult
```

- Editor en grid-materialize roepen dezelfde façade aan.
- View levert alleen draft/widgets; geen handmatige `session["edit_current"]` patches voor consistency (blijft read-only **FmEditConsistencyService** op rijen).

### Fase 3 — Bindend aan slice 41 PRD

- Start **pas na 46-09 done** en post-46 tracers of expliciete defer daarvan.
- **PresentationBuilderRegistry:** constructor-injectie op `WorkspacePresentationCache` / lazy warmup — **geen** runtime import van views-module voor monkeypatch-detectie.
- **ADR-0006:** geen compare/scenario in resultatenwerkruimte; legacy validate mag compare houden.

### Architectuur-principes

- **UI/kern-decoupling:** views → **adapter Qt** → **rcm_core**; typing-only uitzondering.
- **Interface = test surface:** diepe modules testen via publieke seam, niet private `_row_at` of globals.
- **Deletion test:** shallow pass-throughs (dubbele loaders, registry zonder host) moeten na refactor complexiteit **concentreren**, niet verplaatsen naar N callers.

### CONTEXT.md

- Bij afronding fase 1: verifieer dat **batch faalwijzen-grid**, **faalwijze-editor** en **EditingHost** in CONTEXT.md eenduidig staan (geen tweede waarheid in ARCHITECTURE_DEFERRED).

## Testing Decisions

**Goede tests** beschrijven **gedrag aan publieke seams**: bulk all-or-nothing; filter laat niet-zichtbare rijen ongewijzigd; `replace_fm_scope` equivalent aan bestaande bundle-scope; editor+grid delen sessie; dirty guard blokkeert editor; commit triggert incrementele run voor gewijzigde FM-invoerhash — **niet** widget-hierarchie of globale registry-internals.

| Module / fase | Testtype | Prior art |
|---------------|----------|-----------|
| Reconcile | Handmatig + pytest subset in handoff | `KANBAN_HANDOFF.md` slice 36/37 |
| FaalwijzenEditService + bulk | Unit | `test_desktop_faalwijzen_edit_service.py` |
| Panel + filter | pytest-qt smoke | `test_desktop_validate_faalwijzen_panel.py` (32 passed 2026-05-26) |
| replace_fm_scope / assembler | Unit | `test_desktop_fm_edit_services.py` |
| Slice 49 UX | Unit | `test_slice49_fm_editor_ux.py` (13 passed 2026-05-26) |
| FM-detail preserve | Integration | `test_desktop_results_workspace_window.py` |
| EditingHost + geen registry | Unit + integration | nieuw na 46-08/09 |
| FmEditScopeLoader | Unit | bundle equivalence tests |
| FmEditCommitFacade | Unit + pytest-qt | run service + workspace editor tests |
| PresentationBuilderRegistry | Unit | `test_desktop_presentation_lazy_service.py` |

**Verplichte gates:**

- **Fase 0:** geen issue `done` zonder groene tests voor genoemde acceptance; handoff bijgewerkt.
- **Fase 1:** milestones 46–48 acceptance uit slice 46 PRD.
- **Fase 2:** loader equivalence (project vs. sessionzelfde bundle); façade deelt pad met bestaande commit tests.
- **Fase 3:** bestaande slice 41 test-gates per PR; geen regressie slice 37 perf-contracten.

**Modules met voorkeur voor tests (grill-me default):** alle **nieuwe diepe adapter-modules** (EditingHost, ScopeLoader, CommitFacade, PresentationBuilderRegistry) — **unit-first**; Qt alleen waar dialog/runner onvermijdelijk is.

## Out of Scope

- Nieuwe eindgebruikersfeatures buiten slice 46/49/41 (Monte Carlo, killer/olifant, nieuwe FailureTypes).
- **Volledige verwijdering** van ValidateWindow of compare vóór slice 41 PR7.
- **Scenario-split** of compare UI in resultatenwerkruimte (**ADR-0006**).
- Opportunistische refactor van presentatie-test-seams **tijdens** fase 1 (alleen 41-tech-debt noteren).
- **Unified loader** en **volledige commit-façade** vóór 46-09 (tenzij reconcile bewijst dat 09 al done is en team expliciet fase 2 start).

## Further Notes

### Bestaande trackers (geen duplicatie)

| Slice | Rol |
|-------|-----|
| **46** | Implementatie FM batch-grid + orchestratie (issues 01–09) |
| **49** | Editor UX + modelwaarschuwingen (reconcile → done) |
| **41** | View-layer deepening (start na 46-09) |
| **42, 35** | Parallel orthogonaal werk toegestaan |

### Handoffs

- `.scratch/rcm-desktop-slice46-fm-edit-fase2/KANBAN_HANDOFF.md`
- `.scratch/rcm-desktop-slice49-fm-editor-model-waarschuwingen/KANBAN_HANDOFF.md`

### Volgende stap voor agents

1. **Slice 50 issue 01** — reconcile slice 49.
2. **Slice 50 issue 02** — reconcile slice 46; noteer eerste open **46-issue**.
3. Implementeer open **46-01..09** via slice 46 tracker.
4. **Slice 50 issues 03–04** — post-46 loader + commit-façade (na 46-09).
5. **Slice 50 issue 05** — HITL start-gate slice 41 PR1.

Issues: `.scratch/rcm-desktop-slice50-architectuur-roadmap-uitvoering/issues/01.md` … `05.md`.

### ARCHITECTURE_DEFERRED.md

- Slice 45-deferred items zijn **gemapt** op slice 46 issues; historische tabel niet opnieuw als waarheid gebruiken — deze PRD + slice 46 PRD leiden.
