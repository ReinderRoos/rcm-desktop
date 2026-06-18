# PRD — RCM2 desktop slice 60 (FM-editor invoer, REV-opslaan, A/B-baseline)

**Status:** ready-for-agent  
**Versie:** 1.0  
**Triage-labels:** ready-for-agent  
**Type:** Feature (adapter deep modules + beperkte view; beperkte `rcm_core` motor-hardening)  
**Parent:** grill-me sessie post-slice-59 (2026-06-04); bouwt voort op slice 56 (A/B-vergelijking), slice 59 (FM create + preventief CRUD), slice 49 (modelwaarschuwingen)  
**Datum:** 2026-06-04  
**Issue tracker:** lokaal `.scratch/rcm-desktop-slice60-fm-editor-compare-hardening/issues/` (GitHub `gh` niet beschikbaar op setup-machine)

## Problem Statement

Na slice 59 kunnen analisten faalwijzen aanmaken en PM-taken/taakgroepen in de **faalwijze-editor** bewerken, maar drie pijnpunten blokkeren dagelijks werk:

1. **REV-taken** — Opslaan met een nieuwe REV-maatregel op een niet-aging faalwijze levert vaak **“Incrementele analyse mislukt”** zonder bruikbare oorzaak; de echte exception wordt in de commit-service weggestopt.
2. **Taakgroep- en PM-invoer** — “Nieuwe taakgroep” vraagt alleen interval en kosten; verplichte schema-velden (`taak_type`, `omschrijving`, duur, notities) ontbreken in de UX. “Rij toevoegen” voor PM-taken maakt kale IN-rijen; REV en taakgroep-koppeling gaan stilletjes mis.
3. **A/B-scenariovergelijking** — Run → A/B vult slots al na een run, maar de aparte knoppen **“Zet huidige run als A/B”** verwarren de workflow. Analisten willen een **baseline in slot A na eerste geslaagde analyse na inladen**, zonder handmatige seed-knoppen.

Daarnaast moet **inconsistente maar geldige projectdata** (bv. REV op exponentieel falen na import) de **motor niet laten crashen** — alleen de editor blokkeert nieuwe inconsistente invoer tijdelijk hard.

## Solution

Vier samenhangende verbeteringen in vaste volgorde:

1. **REV + incrementele run** — FM-editor **blokkeert opslaan** bij REV op niet-aging faalwijze (bestaande waarschuwing wordt harde validatie). Overige incrementele failures tonen **echte fouttekst**. Motor/`incremental_run` blijft **robust** bij REV op niet-aging in geladen project (geen crash; REV-schedule niet toegepast of veilig genegeerd).
2. **A/B-baseline** — Na **eerste geslaagde run** na project inladen/valideren: **automatisch slot A** vullen met die `last_run`. Verwijder seed-knoppen A/B en bijbehorende handlers/teksten. Run → A / Run → B blijven voor expliciete scenario-runs.
3. **Taakgroep-editor** — Modaal formulier bij “Nieuwe taakgroep…”: voorgesteld `group_id` (type + bestaande groepen, **overschrijfbaar**), `taak_type`, interval, kosten, duur, omschrijving, notities; validatie via `task_groups` editing-schema vóór rij in sessie.
4. **PM-taak-editor** — Zelfde dialoog bij **“Rij toevoegen”** en **dubbelklik** op PM-rij: volledige velden en type-afhankelijke defaults (REV: o.a. `aging_effect_pct`); tabel blijft overzicht.

Ruggengraat: Qt-vrije adapter-services + pytest; views alleen via adapter (`AGENTS.md`).

## User Stories

### REV en opslaan

1. Als analist wil ik dat opslaan **geblokkeerd** wordt wanneer een PM-taak type REV is en de faalwijze `failure_type` geen aging is, zodat ik geen kapotte analyse krijg.
2. Als analist wil ik bij die blokkade een **duidelijke Nederlandse fout** (geen “Incrementele analyse mislukt”), zodat ik weet wat ik moet aanpassen.
3. Als analist wil ik bij andere incrementele-runfouten de **werkelijke foutmelding** zien, zodat debugging mogelijk is zonder terminal.
4. Als analist wil ik dat een project met REV op exponentieel/random (bv. na import) **nog laadt en analyseert**, zodat legacy/import-data de motor niet breekt.
5. Als analist wil ik dat REV op niet-aging in geladen data **geen crash** veroorzaakt, zodat ik het in de editor kan corrigeren na openen.

### A/B-baseline (supersedes slice 56 seed-UX)

6. Als analist wil ik dat na **eerste geslaagde analyse** na inladen **slot A automatisch** de huidige `last_run` bevat, zodat ik direct een baseline heb voor vergelijking.
7. Als analist wil ik **geen** knoppen “Zet huidige run als A/B” meer zien, zodat de toolbar eenvoudiger is.
8. Als analist wil ik **Run → A** en **Run → B** ongewijzigd kunnen gebruiken voor scenario-runs, zodat variant B na FM-wijziging expliciet wordt berekend.
9. Als analist wil ik dat auto-seed A **alleen** gebeurt als slot A nog leeg is, zodat een bewust gedraaide Run → A niet wordt overschreven door een latere validate-run.
10. Als analist wil ik dat slot A/B **gewist** blijven bij padwijziging en leeg project (slice 56 lifecycle), zodat auto-seed opnieuw geldt na nieuw project.

### Taakgroep-editor

11. Als analist wil ik bij “Nieuwe taakgroep…” een **formulier** met alle relevante velden, zodat ik geen incomplete groepen aanmaak.
12. Als analist wil ik een **voorgesteld group_id** op basis van maatregeltype en bestaande groepen, zodat naamgeving consistent is.
13. Als analist wil ik het voorgestelde ID **kunnen overschrijven**, zodat import- en projectconventies blijven werken.
14. Als analist wil ik maatregeltype (IN/REV/TST/…) in de dialoog kiezen, zodat schema-validatie slaagt.
15. Als analist wil ik **duur** (waarde + eenheid) en **notities** kunnen invullen, zodat het domeinmodel volledig wordt benut.
16. Als analist wil ik validatiefouten **vóór** toevoegen aan de PM-sessie zien, zodat de commit-service geen vage fouten geeft.

### PM-taak-editor

17. Als analist wil ik bij “Rij toevoegen” een **dialoog** met volledige PM-velden, zodat REV en taakgroep niet per ongeluk minimaal blijven.
18. Als analist wil ik via **dubbelklik** op een PM-rij hetzelfde dialoog openen, zodat bewerken en aanmaken één pad hebben.
19. Als analist wil ik dat bij taaktype REV defaults voor **aging_effect_pct** en verplichte velden kloppen, zodat incrementele run niet faalt op null/ontbrekend.
20. Als analist wil ik **taakgroep** in de dialoog kunnen kiezen (FK naar project-backed `task_groups`), zodat koppeling expliciet is.
21. Als analist wil ik de tabel in tab Preventief als **overzicht** houden, zodat snelle scan mogelijk blijft na dialoog-invoer.

### Regressie en integratie

22. Als analist wil ik dat bestaande **Opslaan / Opslaan en sluiten** in de FM-editor werken met de nieuwe validatie, zodat slice 59-gedrag behouden blijft.
23. Als analist wil ik dat **Vergelijk A ↔ B** werkt met auto-gevulde A en Run → B, zodat de grill-me-workflow (baseline vs scenario) standaard is.
24. Als onderhouder wil ik dat FM-edit-commit tests de **zichtbare exception** asserten bij gemockte motorfout, zodat regressie op foutmaskering wordt voorkomen.

## Implementation Decisions

### 1. REV-validatie (editor)

- Uitbreiding **`fm_edit_consistency`** (of equivalent pre-commit checklist): finding `REV_WITHOUT_AGING` wordt **blocking** in `FmEditCommitService` / facade vóór `run_incremental_analysis`.
- Bestaande waarschuwingstekst in `messages` hergebruiken of scherpen tot foutniveau.
- Geen wijziging aan `failure_type` automatisch (geen auto-correct naar aging).

### 2. Incrementele foutweergave

- `FmEditCommitService.commit_edits`: bij exception uit `run_incremental_analysis`, return `errors` met **type + message** (of traceback-samenvatting), niet alleen generieke string.
- Logging optioneel op adapter-niveau voor support; UI toont eerste regel leesbaar NL waar mogelijk.

### 3. Motor-hardening (kern)

- In **`build_rev_schedule`** / aanroeppad in motor: als `failure_type` geen aging is, **geen schedule** of lege schedule — **geen raise**.
- Unit test in `rcm_core` met fixture: FM aging-type random/exponential + REV-taak → run voltooit.
- Geen `CACHE_INPUTS_VERSION`-bump tenzij JSON-vorm wijzigt (verwacht niet).

### 4. A/B auto-seed baseline

- Hook na **validate-success** of eerste **`set_last_run`** / run-complete in resultatenwerkruimte: als compare-slot A leeg en run geslaagd → `seed_from_last_run` equivalent voor slot A alleen.
- Verwijder `seed_slot_a_button`, `seed_slot_b_button`, `_seed_current_run_as_a/b`, gerelateerde `messages` en toolbar-layout entries.
- Update slice 56 tests die seed-knoppen asserten; vervang door auto-seed-scenario.
- Documenteer in slice 60 handoff: user story 4–5 slice 56 PRD **gedeeltelijk superseded** (seed-knoppen weg; auto-baseline nieuw).

### 5. Taakgroep-editor (adapter + view)

- Nieuw **`TaskGroupDraftService`**: allocate voorgesteld id (type-prefix + sequentie), bouw row-dict, `validate_entity_rows("task_groups", ...)`.
- Nieuw **`TaskGroupEditorDialog`** (view): roept draft service aan; bij OK → rij in `_task_group_rows` + optioneel PM `task_group_id` op geselecteerde rij.
- Vervang `_on_new_task_group` QInputDialog-pad.

### 6. PM-taak-editor (adapter + view)

- Nieuw **`PmTaskDraftService`**: defaults per `taak_type`, merge met bestaande rij bij edit, validatie `pm_tasks` schema.
- Nieuw **`PmTaskEditorDialog`**: open vanuit `_add_pm_task_row` en dubbelklik-handler op PM-tabel.
- `_build_draft` leest volledige rij uit sessie-dict, niet alleen zes tabelkolommen (tabel kan subset tonen).

### 7. Architectuur

- **Geen** `RCMProject` schema-drift.
- Views importeren geen `rcm_core` behalve typing.
- Alle nieuwe teksten via **`rcm_desktop.messages`**.

## Testing Decisions

### Test seams (graag bevestigen vóór implementatie)

| Seam | Wat wordt getest | Waarom hoog |
|------|------------------|-------------|
| **`FmEditCommitService.commit_edits`** | Mock `run_incremental_analysis` raise → error string bevat exception; REV+non-aging → geen call naar motor | Bestaande slice 44/59 seam; geen Qt |
| **`fm_edit_consistency` / pre-commit** | REV op random FM → blocking finding | Pure functie |
| **`run_incremental_analysis` / motor** | Project met REV + exponential FM → success | `rcm_core` unit; patch `ir` waar nodig |
| **`CompareWorkspaceController` / slot state** | Na simulate “first run” → slot A gevuld; seed knoppen afwezig in smoke | pytest-qt op werkruimte-window |
| **`TaskGroupDraftService`** | Incomplete row → validation errors; suggested id uniek | Adapter unit |
| **`PmTaskDraftService`** | REV defaults include `aging_effect_pct`; edit roundtrip | Adapter unit |

Geen nieuwe seam in views behalve smoke (dialoog opent, OK roept service aan met mock).

### Wat maakt een goede test

- Assert op **gedrag**: commit-result status, error-tekst bevat substring, slot A snapshot aanwezig, validatie faalt vóór rij in buffer.
- Geen assert op interne widget-structuur.

### Prior art

- `tests/test_slice59_fm_editor_dialog.py`, `tests/test_slice59_services.py`
- `tests/test_slice56_workspace_ab_compare_smoke.py`
- `tests/test_fm_edit_commit_service.py` (indien aanwezig) / `tests/test_desktop_results_workspace_window.py`
- `tests/test_editing_schemas_parity.py` bij schema-touch (niet verwacht)

## Out of Scope

- **Undo/redo** in FM-editor.
- **Faalwijze verwijderen** of batch-grid add/delete.
- **Auto-correct** failure_type naar aging bij REV.
- **Permanente** UI-blokkade voor REV op niet-aging in **geladen** project buiten editor (alleen editor-blok bij nieuwe wijziging).
- **Planning-overlay-ankers** in PM/taakgroep-dialoog.
- **ValidateWindow** wijzigingen.
- **GitHub issue aanmaken** in deze slice (lokaal tracker alleen; handmatig upstreamen indien gewenst).
- **Matt Pocock skills installatie** (aparte sessie).

## Further Notes

### Implementatievolgorde (afgesproken)

1. REV + fouttekst + motor  
2. A/B auto-seed + seed-knoppen weg  
3. Taakgroep-dialoog  
4. PM-taak-dialoog  

### Child issues

| # | Bestand | Onderwerp |
|---|---------|-----------|
| 60.1 | `issues/01.md` | REV-blok + incrementele fout + motor |
| 60.2 | `issues/02.md` | A/B auto-baseline, seed-knoppen weg |
| 60.3 | `issues/03.md` | Taakgroep-editor |
| 60.4 | `issues/04.md` | PM-taak-editor |

### Triage

Alle child issues: **`ready-for-agent`**. Geen extra triage nodig (grill-me + codebase-analyse afgerond).
