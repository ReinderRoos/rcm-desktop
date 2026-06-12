# PRD — RCM2 desktop slice 41 (view-layer deepening: ProjectSession, modus-builders, flows)

**Status:** ready-for-agent  
**Versie:** 1.0  
**Triage-labels:** ready-for-agent

## Problem Statement

Na eerdere adapter-deepening (o.a. `LoadedProject`, `lcc_view_service`,
`EditingSession`, unified presentation cache) blijft de **view-laag te veel
orchestratie** doen die thuishoort in Qt-vrije adapter-modules. Concreet:

- **`Resultatenwerkruimte`** (~2200+ regels) dispatcht modi (FM-detail,
  Bijdragen, LCC), beheert cache-keys, render-index en meekoppel-flow inline;
  alleen LCC gaat al via een dedicated adapter-seam.
- **Views importeren nog direct `RCMProject`** terwijl `LoadedProject` bestaat
  maar nergens in views wordt gebruikt — het decoupling-contract uit slice 9 is
  niet afgerond.
- **Meekoppel UX** (sync, anker-dialoog, preview/apply) mengt adapter-logica
  met Qt-widgets en message-opbouw in één venster.
- **Import-flow** heeft een Qt-dialog in de adapter (`isograph_import_dialog`)
  en gedupliceerde validatie tussen open-flow en validate-service.
- **Chart widgets** leven als private nested classes bovenaan het
  werkruimte-venster; hergebruik en navigatie zijn lastig.
- **Vijf background runners** dupliceren hetzelfde `QThread` + `_Worker` +
  cleanup-patroon (~300 regels totaal).
- **ValidateWindow (legacy)** gebruikt een parallelle editing-pipeline via
  `FaalwijzenEditService` i.p.v. de bestaande `EditingSession`-seam; scenario/
  compare-paden bevatten dode code buiten het legacy venster.

Voor ontwikkelaars en agents leidt dit tot: moeilijk testbare view-bestanden,
regressierisico bij modus-wijzigingen, en schending van het architectuurprincipe
**UI/kern-decoupling via adapter** (views → adapter → kern, geen directe
`rcm_core`-imports in views).

## Solution

Voer een **gefaseerde view-layer deepening** uit in zeven onafhankelijke PRs,
Resultatenwerkruimte eerst, ValidateWindow daarna:

1. **ProjectSession + workspace modus-builders** — centrale view-facing seam
   voor geladen project + run; Qt-vrije builders per modus leveren data-DTOs;
   view bindt alleen Qt-modellen, i18n, selectieherstel.
2. **Meekoppel panel service** — sync/preview/apply als adapter-module;
   anker-dialoog en message boxes blijven in de view.
3. **Import open-flow service** — Qt-vrije orchestratie; wizard-dialog verhuist
   naar views; validation orchestrator unificeert file- en in-memory-validatie.
4. **Chart widget extractie** — mechanische verplaatsing naar `views/widgets/`.
5. **Gedeelde BackgroundRunner** — onder `adapter/qt/`; bestaande runner-API's
   blijven ongewijzigd voor views.
6. **EditingSession-adoptie** — `FaalwijzenEditService` composeert
   `EditingSession`.
7. **Legacy compare opruimen** — dode workspace-scenario-paden weg; compare
   blijft alleen voor legacy ValidateWindow; ADR-notitie.

Elke PR is zelfstandig mergebaar met eigen test-gate; geen functionele
feature-wijziging voor eindgebruikers — alleen betere structuur en testbaarheid.

## User Stories

### ProjectSession en modus-builders (PR 1)

1. Als ontwikkelaar wil ik dat de Resultatenwerkruimte **nooit direct
   `RCMProject` importeert**, zodat het UI/kern-decoupling-contract wordt
   nageleefd.
2. Als ontwikkelaar wil ik een **`ProjectSession` aggregate** op AppState
   (pad + `LoadedProject` + `RunResult`), zodat views één seam hebben voor
   project+run-context.
3. Als ontwikkelaar wil ik dat **`set_last_project` en session-setters
   gesynchroniseerd blijven**, zodat legacy callers (ValidateWindow, tests)
   niet breken tijdens migratie.
4. Als ontwikkelaar wil ik dat de Resultatenwerkruimte **strikt via
   `project_session` leest**, zodat adoptie eenduidig en afdwingbaar is.
5. Als ontwikkelaar wil ik een **`workspace_view_service` met drie builders**
   (`build_fm_detail_view`, `build_bijdragen_view`, `build_lcc_view`), zodat
   modus-dispatch testbaar buiten Qt staat.
6. Als ontwikkelaar wil ik dat **`build_lcc_view` de bestaande LCC-seam
   hergebruikt**, zodat geen dubbele LCC-logica ontstaat.
7. Als ontwikkelaar wil ik dat builders **data-DTOs** teruggeven (rijen,
   inspector-velden, cache-keys, render-scope), zodat de view dun blijft.
8. Als ontwikkelaar wil ik dat **cache-key logic en render-index warming in
   builders** zitten, zodat `_rerender_detail_for_current_scope` geen
   adapter-beslissingen meer neemt.
9. Als ontwikkelaar wil ik dat de view **`QAbstractTableModel`-instanties,
   i18n en selectieherstel** doet, zodat Qt-specifiek gedrag op de juiste laag
   blijft.
10. Als reliability-analist wil ik dat **FM-detail, Bijdragen en LCC na PR 1
    identiek renderen** als vóór de refactor, zodat er geen regressie in
    presentatie is.
11. Als ontwikkelaar wil ik **unit-tests op elke builder** met fixture-project
    + snapshot, zodat modus-wijzigingen zonder pytest-qt view-tests
    verifieerbaar zijn.
12. Als ontwikkelaar wil ik dat **`WorkspaceStateSnapshot` ongewijzigd** als
    modus/scope/filter-contract blijft, zodat bestaande orchestrator-tests
    geldig blijven.

### Meekoppel panel service (PR 2)

13. Als ontwikkelaar wil ik een **`meekoppel_panel_service`** met `sync`,
    `preview` en `apply`, zodat meekoppel-orchestratie testbaar is zonder Qt.
14. Als ontwikkelaar wil ik dat **`sync` een `MeekoppelPanelView` DTO**
    teruggeeft (rijen, enable/visible flags), zodat de view alleen bindt.
15. Als ontwikkelaar wil ik dat **anker-dialoog (`QDialog` + radio's) in de
    view blijft**, zodat interactieve UX op de view-laag blijft.
16. Als ontwikkelaar wil ik dat **preview/apply de anchor van de view
    ontvangen**, zodat adapter geen Qt-dialogen nodig heeft.
17. Als ontwikkelaar wil ik dat **message-opbouw via `messages.*` in de view
    blijft**, consistent met het data-DTO-patroon uit PR 1.
18. Als maintenance engineer wil ik dat **meekoppel in LCC what-if-modus
    identiek werkt** na extractie, zodat bundel-shift en preview ongewijzigd
    blijven (ADR-0005).
19. Als tester wil ik **adapter-tests voor sync/preview/apply** met planning
    overlay-fixtures, zodat meekoppel-regressies vroeg worden gevangen.
20. Als ontwikkelaar wil ik dat **bestaande `discover_meekoppel_locations`,
    `preview_meekoppel_location`, `apply_meekoppel_location`** worden
    gecomposeerd, niet gedupliceerd.

### Import open-flow (PR 3)

21. Als ontwikkelaar wil ik een **Qt-vrije `import_flow_service`**, zodat de
    adapter-laag geen `QDialog` meer bevat (ADR-0004).
22. Als ontwikkelaar wil ik dat de **import-wizard verhuist naar
    `views/import_wizard_dialog.py`**, zodat Qt-code alleen in views staat.
23. Als ontwikkelaar wil ik een **validation orchestrator** die file-based en
    in-memory validatie unificeert, zodat import en validate dezelfde regels
    gebruiken.
24. Als gebruiker wil ik dat **Excel-import via RCM-Cost identiek werkt** na
    refactor, zodat bestaande import-matrix en PM-semantiek intact blijven.
25. Als ontwikkelaar wil ik dat **`isograph_open_flow_service` de nieuwe
    service composeert**, zodat entry points niet vermenigvuldigen.
26. Als tester wil ik **adapter-tests op import-stappen** (pad-selectie,
    validatie-resultaat, project-materialisatie) zonder GUI, zodat import-flow
    stabiel blijft bij UI-wijzigingen.
27. Als ontwikkelaar wil ik dat **foutmeldingen en blocking states als DTOs**
    uit de service komen, zodat de view alleen toont wat de adapter beslist.

### Chart widget extractie (PR 4)

28. Als ontwikkelaar wil ik **`LCCStackedBarChartWidget` en
    `ContributionBarChartWidget` in `views/widgets/`**, zodat het
    werkruimte-venster korter en navigeerbaarder wordt.
29. Als ontwikkelaar wil ik **mechanische extractie zonder adapter-wijzigingen**,
    zodat PR 4 puur view-structuur is en laag risico heeft.
30. Als ontwikkelaar wil ik dat widgets **dezelfde publieke API** houden
    (data-in, paint/update-out), zodat bind-code minimaal wijzigt.
31. Als ontwikkelaar wil ik een **`views/widgets/` package**, zodat toekomstige
    chart/component-extracties een vaste plek hebben.
32. Als tester wil ik dat **bestaande werkruimte pytest-qt tests groen blijven**,
    zodat extractie geen gedragswijziging introduceert.

### Background worker runner (PR 5)

33. Als ontwikkelaar wil ik een **gedeelde `BackgroundRunner` onder
    `adapter/qt/`**, zodat QThread-boilerplate op één plek staat.
34. Als ontwikkelaar wil ik dat **bestaande runners (`ValidateRunner`,
    `RunRunner`, `PresentationRebuildRunner`, `LCCWarmupRunner`,
    `CompareRunner`) dunne wrappers blijven**, zodat view-connecties
    (`state_changed`, `result_ready`) identiek blijven.
35. Als ontwikkelaar wil ik **thread lifecycle (start, cancel, cleanup) centraal**,
    zodat resource-leaks en dubbele-starts op één plek worden afgehandeld.
36. Als tester wil ik **pytest-qt tests op minstens één runner** die de shared
    implementatie gebruikt, zodat threading-regressies worden afgevangen.
37. Als ontwikkelaar wil ik dat **runner-API's backward compatible** blijven,
    zodat geen view-wijzigingen nodig zijn in PR 5.

### EditingSession in ValidateWindow (PR 6)

38. Als ontwikkelaar wil ik dat **`FaalwijzenEditService` `EditingSession`
    composeert**, zodat de tabulaire editing-pipeline één seam heeft.
39. Als ontwikkelaar wil ik dat **materialisatie via `EditingSession.build_project`**
    loopt, zodat validate/run/import dezelfde keten delen.
40. Als ontwikkelaar wil ik dat **bestaande faalwijzen-grid API's intact blijven**,
    zodat ValidateWindow-view geen wijziging nodig heeft.
41. Als tester wil ik **adapter-tests op edit → validate → build_project** via
    `FaalwijzenEditService`, zodat editing-parity met `EditingSession` bewezen
    is.
42. Als ontwikkelaar wil ik dat **parity-tests (`test_editing_schemas_parity`)**
    groen blijven, zodat schema-drift wordt uitgesloten.

### Legacy compare opruimen (PR 7)

43. Als ontwikkelaar wil ik **dode workspace-scenario-paden verwijderen**
    (`ScenarioSlotState` in split layout waar `scenario_mode` altijd false is),
    zodat misleidende code verdwijnt.
44. Als ontwikkelaar wil ik dat **`CompareRunner` alleen legacy ValidateWindow
    bedient**, zodat compare-scope expliciet is.
45. Als ontwikkelaar wil ik een **ADR-notitie "compare = legacy validate only"**,
    zodat toekomstige agents niet opnieuw scenario-slots in workspace bouwen.
46. Als ontwikkelaar wil ik dat **`scenario_compare_facade` geminimaliseerd**
    wordt tot wat ValidateWindow nodig heeft, zodat dead code weg is.
47. Als productowner wil ik dat **Resultatenwerkruimte-scenario's (slice 23+)**
    niet geraakt worden door PR 7, zodat alleen legacy-paden worden opgeruimd.
48. Als tester wil ik dat **legacy validate compare-flow tests groen blijven**
    zolang `--legacy-validate` bestaat.

### Cross-cutting (alle PRs)

49. Als agent wil ik **kleine, reviewbare PRs** met duidelijke grenzen, zodat
    elke merge zelfstandig verifieerbaar is.
50. Als ontwikkelaar wil ik **geen wijzigingen in `rcm_core`**, zodat de kern
    puur blijft en cache/version bumps niet nodig zijn.
51. Als ontwikkelaar wil ik dat **adapter-modules Qt-vrij blijven** behalve
    expliciete `adapter/qt/` subtree, zodat TDD op adapter zonder GUI blijft.
52. Als ontwikkelaar wil ik **domain-vocabulaire uit CONTEXT.md** in interfaces
    en DTO-namen, zodat agents en domeinexperts eenduidig praten.
53. Als ontwikkelaar wil ik dat **bestaande deepening-seams (`LoadedProject`,
    `lcc_view_service`, presentation cache, planning overlay) worden
    gecomposeerd**, niet opnieuw uitgevonden.
54. Als tester wil ik een **groene regressiesuite na elke PR**, zodat
    deepening geen stille gedragswijziging introduceert.

## Implementation Decisions

### Volgorde en scope

- **Sequentie:** PR 1 → PR 2 → PR 3 → PR 4 → PR 5 → PR 6 → PR 7.
- **Prioriteit:** Resultatenwerkruimte (PR 1–5) vóór ValidateWindow (PR 6–7).
- **Geen user-facing feature-wijziging:** gedrag en UX blijven gelijk; alleen
  structuur en testbaarheid verbeteren.

### PR 1 — ProjectSession + workspace_view_service

- **`ProjectSession`** (frozen dataclass): `path: Path | None`, `loaded:
  LoadedProject`, `run: RunResult | None`.
- **`AppState.project_session`**: nieuwe property; `set_last_project` /
  `set_last_run` / `set_last_project_and_run` vullen session synchroon met
  legacy `_last_project` / `_loaded_project` / `_last_run`.
- **Resultatenwerkruimte:** leest uitsluitend via `project_session`; geen
  `from rcm_core.models import RCMProject` in view.
- **`workspace_view_service`:** drie entrypoints:
  - `build_fm_detail_view(session, snapshot, render_index, ...) -> FMDetailView`
  - `build_bijdragen_view(session, snapshot, render_index, ...) -> BijdragenView`
  - `build_lcc_view(...)` — delegeert aan bestaande `lcc_view_service.build_lcc_view`
    met `session.loaded.core()` intern.
- **DTO's** bevatten: gefilterde rijen, inspector-velden, cache_modus_key,
  render_scope, lege-staat hints — **geen** Qt-types.
- **View `_rerender_detail_for_current_scope`:** dunne modus-switch die builder
  aanroept en resultaat bindt; selectieherstel en `messages.*` blijven view.
- **Niet in PR 1:** meekoppel, import, chart extractie.

### PR 2 — meekoppel_panel_service

- **`MeekoppelPanelView` DTO:** tabelrijen, kolom-metadata, panel zichtbaar/
  enabled flags afgeleid van snapshot (LCC what-if actief).
- **`sync(session, snapshot, window_years) -> MeekoppelPanelView`**
- **`preview(session, overlay, anchor, location_id) -> PreviewResult`**
- **`apply(session, overlay, anchor, location_id) -> ApplyResult`**
- View: anker-`QDialog`, `QMessageBox`, `_sync_meekoppel_panel` roept `sync` aan
  en bindt tabel.
- Composeert bestaande meekoppel adapter-functies; geen duplicatie van
  planning-overlay motor.

### PR 3 — import_flow_service + validation orchestrator

- **`import_flow_service`:** stappen als enum/state machine:
  selecteer bestand → parse → validate in-memory → materialiseer project →
  return `ImportFlowResult` (success | blocked | errors).
- **`validation_orchestrator`:** één entry voor validate-from-path en
  validate-from-project; delegeert naar bestaande validate-service waar mogelijk.
- **`isograph_import_dialog`:** verplaats naar `views/import_wizard_dialog.py`;
  adapter exporteert alleen Qt-vrije flow.
- **`isograph_open_flow_service`:** refactored to compose import_flow_service.

### PR 4 — chart widgets

- Mechanische move: `_LCCStackedBarChartWidget` → `LCCStackedBarChartWidget`,
  `_ContributionBarChartWidget` → `ContributionBarChartWidget`.
- Package: `rcm_desktop/views/widgets/` met `__init__.py` re-exports.
- Geen adapter layout-DTOs in deze PR.

### PR 5 — BackgroundRunner

- Locatie: `rcm_desktop/adapter/qt/background_runner.py`.
- Interface (conceptueel):

```python
class BackgroundRunner(QObject):
    state_changed = Signal(str)  # idle | running | ...
    result_ready = Signal(object)
    error_ready = Signal(str)

    def run(self, fn: Callable[[], T]) -> None: ...
    def cancel(self) -> None: ...
```

- Bestaande `*Runner` classes: intern `BackgroundRunner` gebruiken; publieke
  methoden en signal-namen ongewijzigd.

### PR 6 — FaalwijzenEditService + EditingSession

- `FaalwijzenEditService` houdt private `EditingSession` instance.
- `load`, `apply_rows`, `validate`, `build_project` delegeren naar session.
- Geen wijziging aan view-facing method signatures waar mogelijk.

### PR 7 — legacy compare cleanup

- Verwijder dode paden waar `compute_split_layout` / `ScenarioSlotState` no-op
  zijn buiten ValidateWindow.
- Minimaliseer `scenario_compare_facade` tot legacy scope.
- **`CompareRunner` blijft** zolang `--legacy-validate` bestaat.
- Nieuwe ADR of ADR-0004/0005 aanvulling: compare-stack is legacy-only.

### Architectuurprincipes (hard contract)

- Views → adapter only; geen `rcm_core.*` in views (typing-only OK).
- Adapter TDD met pytest-qt; pure view-refactors zonder gedragswijziging niet
  test-gestuurd tenzij regressie-test bestaat.
- `rcm_core` ongewijzigd; geen `CACHE_INPUTS_VERSION` bump.

### Deep modules (samenvatting)

| Module | Interface | Encapsuleert |
|--------|-----------|--------------|
| `ProjectSession` | path + loaded + run | view-facing project/run aggregate |
| `workspace_view_service` | 3× build_*_view | modus dispatch, cache, render-index |
| `meekoppel_panel_service` | sync / preview / apply | LCC what-if meekoppel UX data |
| `import_flow_service` | run_import_flow | Excel open + validate + materialize |
| `validation_orchestrator` | validate_* | unified validation entry |
| `BackgroundRunner` | run / cancel | QThread lifecycle |
| `EditingSession` (adoptie) | load / apply / validate / build | tabulaire editing-pipeline |

## Testing Decisions

### Wat een goede test is

- Test **observeerbaar gedrag en DTO-vorm** op adapter-grenzen — niet private
  view-methodes of widget-internals.
- Given fixture project + `WorkspaceStateSnapshot` + `ProjectSession`, when
  builder draait, then DTO bevat verwachte rijen/scope/cache-key.
- pytest-qt alleen waar threading of bestaande view-regressies dat vereisen.
- Na elke PR: volledige relevante testsuite groen; geen stille UX-wijziging.

### Te testen modules (TDD / unit)

| PR | Modules | Prior art |
|----|---------|-----------|
| 1 | `ProjectSession`, `workspace_view_service` builders | `test_lcc_view_service`, `test_fm_verification_service`, presentation cache tests |
| 2 | `meekoppel_panel_service` | `test_desktop_meekoppel_workspace`, planning overlay tests |
| 3 | `import_flow_service`, `validation_orchestrator` | slice 35 import tests, `test_validate_service` |
| 4 | — (mechanische move) | bestaande werkruimte pytest-qt |
| 5 | `BackgroundRunner` + één wrapper | bestaande `*Runner` pytest-qt tests |
| 6 | `FaalwijzenEditService` | `test_editing_schemas_parity`, faalwijzen adapter tests |
| 7 | compare facade (indien logic overblijft) | legacy validate compare tests |

### View-laag

- Geen nieuwe pytest-qt tests voor pure bind-refactors tenzij bestaande tests
  al dekken — die moeten groen blijven.
- Handmatige smoke: Resultatenwerkruimte modi wisselen, meekoppel flow, import
  wizard, legacy validate compare (PR 7).

## Out of Scope

- Volledige herschrijving of verwijdering van **ValidateWindow**.
- Nieuwe analysefeatures, KPI's, modi of UX-redesign.
- **PBS graph index** unificatie (`_collect_subtree_ids` dedup) — aparte slice.
- **Presentation cache graph** verder uitbreiden beyond bestaande compose.
- **LCC bucket builder unificatie** — aparte slice.
- Scenario-slot model wijzigingen in Resultatenwerkruimte (slice 23 contract).
- Verwijderen van `CompareRunner` zolang legacy validate actief is.
- Wijzigingen aan `rcm_core.models` of editing schemas.
- Performance-SLA's of benchmark-hunting in deze slice.

## Further Notes

- Deze slice is de **operationalisering** van de `/grill-me` sessie over
  view-layer deepening; zeven PRs komen overeen met de overeengekomen
  beslissingentabel.
- **Resterende risico's:**
  - PR 1 raakt ~20 `last_project`-referenties in werkruimte — zorgvuldige
    setter-sync voorkomt ValidateWindow-regressies.
  - PR 3 import-refactor: slice 35 (`KANBAN_HANDOFF.md`) bevat sessie-fixes;
    import-flow moet die semantiek respecteren.
  - PR 5: threading regressies zijn subtiel — minstens één cancel/reentrancy
    test toevoegen.
- **Afhankelijkheden:** PR 2 en PR 3 bouwen voort op PR 1 (`ProjectSession`);
  PR 4–5 zijn grotendeels onafhankelijk; PR 6–7 zijn sequentieel na PR 5.
- Agents: start PR 1 met TDD op `workspace_view_service`; view-migratie pas
  na groene adapter-tests.
