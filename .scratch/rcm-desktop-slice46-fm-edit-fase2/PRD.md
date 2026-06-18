# PRD — RCM2 desktop slice 46 (FM-bewerken fase 2: batch-grid, contract, orchestratie)

**Status:** ready-for-agent  
**Versie:** 1.0  
**Triage:** ready-for-agent  
**Type:** AFK (adapter + ValidateWindow-panel) + beperkte UI; optioneel `rcm_core` registry  
**Parent:** grill-me op `ARCHITECTURE_DEFERRED.md` na slice 44/45 (2026-05-23)  
**Relatie:** slice 7 (faalwijzen-grid), slice 44 (FmEditorDialog), slice 45 (quick wins), ADR-0006 (legacy compare)  
**Datum:** 2026-05-23

## Problem Statement

Slice 44 leverde de **modale faalwijze-editor** in de resultatenwerkruimte (volledige FM-scope via **FmEditBundle** en geïsoleerde **EditingSession**). Slice 45 repareerde twee kleine gaten (save-seam legacy grid, session-tellers voor waarschuwingen).

Analisten hebben nu **twee bewerkingspaden** met verschillende mogelijkheden:

- De **editor** dekt basis-, effect-, correctief- en preventief-tabs, maar geen batch over veel rijen.
- Het **faalwijzen-grid** in **ValidateWindow** dekt slechts een **subset** van velden (geen `failure_type`, geen NMF/`is_evident`) en kent geen echte bulk-acties — terwijl import- of modelleringsfouten vaak **homogeen** zijn (“alle foutief op exponentieel”, “alle onterecht NMF”).

Tegelijkertijd zijn architectuur-aanbevelingen uitgesteld: bundle-assemblage in de view, handmatige `apply_bundle_scope`, dubbele run-paden (editor synchroon vs. werkruimte **RunRunner**), en geen gedeelde **tabulaire editing-pipeline** tussen grid en editor. Dat verhoogt regressierisico en maakt stille overschrijving mogelijk als grid en editor parallel dirty zijn.

## Solution

Fase 2 brengt **één tabulaire contract** voor `faalwijzes`-bewerking (schema-gedreven kolommen en validatie), een **batch-grid** als complement op de editor, en geleidelijke consolidatie van commit/run-sessies.

**Drie milestones** (thematisch; implementatie via **verticale AFK-tracers** issues 01–09):

| Milestone | Doel | User-visible winst | Issues |
|-----------|------|-------------------|--------|
| **46 — Batch-grid contract** | Uitgebreid grid, snelfilters, bulk API, panel-extract | Filter + herstel massale modelfouten in ValidateWindow | 01–04 |
| **47 — FM-editor hardening** | `replace_fm_scope`, bundle→adapter, `RunRunner`, dirty guard | Editor commit robuust; geen stille conflicten met grid | 05–07 |
| **48 — Sessie & orchestratie** | Gedeelde sessie, run-unificatie, workspace grid-host | Eén waarheid; grid in werkruimte | 08–09 |

**Rolverdeling (vast):**

- **FmEditorDialog** = canoniek voor volledige FM-scope (tabs, effecten, PM, CM-split).
- **Faalwijzen-grid** = batch-herstel voor homogene fouten op `faalwijzes`-velden; geen pariteit met effect/PM-tabs.

**Kolom-prioriteit grid (MoSCoW):**

- **Must (C):** `failure_type`, `mttf_jaar`, `sigma_jaar`, `is_evident` (NMF), `faalwijze_omschrijving`, `functie_id`, `repair_quality`
- **Should (B):** + `cost_cm_eur`, `p_ongewenste_gebeurtenis` (huidige grid-velden)
- **Could (A):** alleen `failure_type`, NMF, `mttf_jaar`, `sigma_jaar` als C te lang duurt

**Niet in batch-grid:** PBS `bouwjaar`, effectlinks, PM-taken, taakgroepen, CM-materiaal/arbeid-split (blijven editor).

## User Stories

### Strategie editor vs. grid

1. Als analist wil ik in de **werkruimte** via dubbelklik de **volledige** faalwijze bewerken, zodat complexe scenario’s op één plek blijven.
2. Als analist wil ik in **ValidateWindow** een **grid** gebruiken om **veel vergelijkbare** faalwijzen snel te corrigeren, zodat importfouten niet één-voor-één in de editor hoeven.
3. Als analist wil ik dat het grid **niet** alle editor-tabs vervangt, zodat scope beheersbaar blijft.
4. Als product owner wil ik dat **ADR-0006** gerespecteerd blijft (compare/LTAP legacy validate), zodat geen scenario-split in de werkruimte terugkomt.

### Batch-grid — kolommen en modelfouten

5. Als analist wil ik **`failure_type`** (exponentieel/veroudering) in het grid zien en wijzigen, zodat verkeerde faalmodellen batch-fixbaar zijn.
6. Als analist wil ik **NMF** (ja/nee ↔ `is_evident`) in het grid zien en wijzigen, zodat onterecht verborgen falen batch-fixbaar zijn.
7. Als analist wil ik **MTTF** en **sigma** in het grid bewerken, zodat parameters bij type-wijziging mee kunnen.
8. Als analist wil ik **faalwijze_omschrijving**, **functie_id** en **repair_quality** in het grid bewerken (must-set C), zodat documentatie en functie-koppeling mee corrigeren.
9. Als analist wil ik optioneel **cost_cm_eur** en **p_ongewenste_gebeurtenis** in het grid houden (should B), zodat bestaande slice-7-workflows blijven werken.
10. Als analist wil ik **geen bouwjaar** in het batch-grid, zodat gedeeld-PBS-risico bewust via de editor blijft.

### Batch-grid — filteren

11. Als analist wil ik **snelfilters** op `failure_type` en NMF boven het grid, zodat ik snel de foutset zie.
12. Als analist wil ik een **zoekveld** op `fm_id` en omschrijving, zodat ik binnen een gefilterde set kan versmallen.
13. Als analist wil ik gefilterde rijen **sorteren** (proxy-model), zodat ik patronen herken.

### Batch-grid — bulk-acties

14. Als analist wil ik **meerdere rijen selecteren** en één veldwaarde toepassen, zodat geselecteerde FM’s in één actie gelijk worden getrokken.
15. Als analist wil ik een actie **op alle zichtbare (gefilterde) rijen** kunnen toepassen, zodat ik na filter niet handmatig hoef te selecteren.
16. Als analist wil ik dat bulk-wijzigingen dezelfde **validatie** doorlopen als enkelvoudige celwijzigingen, zodat geen stille ongeldige staat ontstaat.
17. Als analist wil ik bij validatiefouten na bulk **duidelijke foutmeldingen** per rij/veld, zodat ik kan bijsturen.

### Tabulaire contract (schema)

18. Als ontwikkelaar wil ik dat **bewerkbare grid-kolommen** uit **Editing schema registry** (`ENTITY_SCHEMAS["faalwijzes"]`) worden afgeleid, zodat er geen tweede veldlijst divergeert.
19. Als analist wil ik dat de editor **faalwijze-velden** dezelfde coercion/validatie gebruikt als het grid, zodat opslaan hetzelfde gedrag geeft.
20. Als ontwikkelaar wil ik **`apply_bulk_change(fm_ids, field, value)`** op de faalwijzen-edit façade, zodat UI dun blijft.

### Grid-locatie en panel

21. Als analist wil ik het batch-grid **eerst** in **ValidateWindow** (bestaand panel), zodat levering snel is.
22. Als ontwikkelaar wil ik een **host-neutraal** faalwijzen-panel (widget + adapter-hooks), zodat de werkruimte later dezelfde grid kan hosten zonder fork.
23. Als ontwikkelaar wil ik **ValidateWindow** te ontleden door alleen het **faalwijzen-panel** te extraheren, zodat compare/LTAP niet in dezelfde refactor zitten.

### Grid ↔ editor — dirty conflict (milestone 47)

24. Als analist wil ik een **waarschuwing** als ik de editor open terwijl het grid **ongeslagen wijzigingen** heeft, zodat ik geen stille overschrijving krijg.
25. Als analist wil ik kunnen kiezen: **grid opslaan**, **grid verwerpen**, of **editor annuleren**, zodat ik bewust verder ga.
26. Als analist wil ik dezelfde waarschuwing als de werkruimte-editor opent terwijl Validate-grid dirty is (zelfde project), zodat beide entrypoints veilig zijn.

### FM-editor commit & run (milestone 47)

27. Als analist wil ik na **OK** in de editor **voortgang** zien bij grote projecten, zodat de UI niet bevriest.
28. Als analist wil ik een **incrementele run** na editor-opslaan (alleen gewijzigde **FM-invoerhash**), zodat slice-44-gedrag behouden blijft.
29. Als analist wil ik waar mogelijk **annuleren** tijdens run (via **RunRunner**), zodat ik lange runs kan stoppen.
30. Als ontwikkelaar wil ik **bundle-assemblage** (widgets → **FmEditBundle**) in de adapter, zodat de view geen domeinlogica meer assembleert.
31. Als ontwikkelaar wil ik **`EditingSession.replace_fm_scope(bundle)`** i.p.v. losse splice-logica, zodat FM-scope één geteste methode is.

### Schema downtime (milestone 47–48)

32. Als ontwikkelaar wil ik **`downtime_per_failure`** in `ENTITY_SCHEMAS` als expliciet veld (dict-vorm in edit-buffer), zodat het tabulaire contract compleet is.
33. Als ontwikkelaar wil ik **gedeelde row-mappers** voor downtime (uren ↔ dict) in de adapter, zodat editor en toekomstig grid niet dupliceren.
34. Als ontwikkelaar wil ik later optioneel **`time_duration`-coercion** in de registry (milestone 48), zodat nested types consistent worden zonder big-bang nu.

### Gedeelde sessie (milestone 48)

35. Als analist wil ik op termijn **één project-EditingSession** voor grid én editor, zodat er geen dubbele buffers zijn.
36. Als analist wil ik het batch-grid **later** in de **resultatenwerkruimte** kunnen gebruiken, zodat ik niet naar legacy validate hoef voor batch-fix.
37. Als ontwikkelaar wil ik **grid-run** en **editor-run** via dezelfde **run-orchestratie** aanroepen, zodat presentatie-cache en foutafhandeling gelijk zijn.

### Validatie, save, analyse

38. Als analist wil ik in het grid **Opslaan** en **Analyse** blijven gebruiken via bestaande Validate-flow, zodat gewoontes blijven.
39. Als analist wil ik dat grid-wijzigingen **materialize_for_save/run** blijven blokkeren bij validatiefouten, zodat geen foute motorinvoer wordt weggeschreven.
40. Als analist wil ik na grid-save een **incrementele** herberekening, zodat grote projecten haalbaar blijven.

### Foutafhandeling en randgevallen

41. Als analist wil ik bij bulk op zeer veel rijen een **duidelijke UX** (progress of waarschuwing), zodat ik weet dat de actie bezig is.
42. Als analist wil ik dat **failure_type**-wijziging validatieregels voor sigma/MTTF respecteert, zodat aging/random consistent blijven.
43. Als analist wil ik dat **functie_id** FK-validatie blijft (project-backed), zodat ongeldige functies worden geweigerd.

### Documentatie en onderhoud

44. Als ontwikkelaar wil ik **CONTEXT.md** bijwerken met de drie lagen (grid batch vs. editor vs. verificatie), zodat agents de juiste seam kiezen.
45. Als ontwikkelaar wil ik **ARCHITECTURE_DEFERRED** afsluiten met verwijzing naar deze PRD, zodat geen dubbele waarheid in .scratch blijft.

## Implementation Decisions

### Diepe modules (bouwen/uitbreiden)

| Module | Rol | Diepte |
|--------|-----|--------|
| **FaalwijzenEditService** (of opvolger façade) | Project-brede `faalwijzes`-EditingSession; `apply_change`, **`apply_bulk_change`**; schema-gedreven `EDITABLE_FIELDS` / kolommetadata; `materialize_for_run/save` | Hoog — centrale batch-contract |
| **FaalwijzenGridPanel** | Host-neutraal Qt-panel: tabel, snelfilters, zoek, bulk-acties; geen directe `rcm_core`-imports | Medium — UI; logic via service |
| **EditingSession.replace_fm_scope** | Vervangt handmatige multi-entity splice voor één **FmEditBundle** | Hoog — getest in isolatie |
| **FmEditBundleAssembler** (adapter) | Widgets/DTO → **FmEditBundle**; CM-split, downtime-dict, PM-merge | Hoog — verplaatst uit view |
| **FmEditRowMappers** | `downtime_per_failure` uren ↔ dict; hergebruik **CmCostSplitMapper** | Laag — puur |
| **FmEditCommitService** / **RunOrchestration** | Eén pad naar valideren → save → `run_incremental_analysis`; editor stap 1 via **RunRunner** | Hoog — verenigt #8 |
| **DirtySessionCoordinator** | Detecteert grid-dirty vs. editor-open; waarschuwing/dialog flow | Medium — desktop-only |
| **Editing schema registry** | `downtime_per_failure` in `field_types`; later `time_duration` type | Medium — parity-tests |

### Milestone 46 — Batch-grid contract

- Afleid bewerkbare kolommen uit **`ENTITY_SCHEMAS["faalwijzes"]`** met expliciete allowlist voor grid (must C, fallback B/A gedocumenteerd in issue).
- Implementeer **`apply_bulk_change`** op dezelfde pipeline als `apply_change` (coercion via bestaande `_adapt_raw_for_coerce` / entity validation).
- UI: snelfilters (`failure_type`, NMF), zoek op fm_id/omschrijving, Qt proxy voor zichtbare rijen.
- Bulk: contextmenu of toolbar — “pas toe op selectie” en “pas toe op alle zichtbare”.
- Extract **`ValidateFaalwijzenPanel`** uit ValidateWindow; shell houdt signals voor run/save/dirty.
- **Host-neutrale** interface: panel krijgt service + project-ref; geen compare/LTAP-logica in panel.
- Grid blijft **alleen ValidateWindow** in deze milestone; geen workspace-dock.

**Fallback C→B→A:** in issue 46 opnemen — B als bool/NMF-delegates + ≥3 nieuwe kolommen niet in één sprint passen; A als alleen type+NMF+MTTF/sigma.

### Milestone 47 — FM-editor hardening

- **`EditingSession.replace_fm_scope(bundle)`** —zelfde gedrag als huidige `apply_bundle_scope`; module-functie blijft dunne wrapper of deprecated.
- **`FmEditBundleAssembler`** — verhuist `_collect_bundle`-logica uit view; view bindt alleen widgets.
- **`downtime_per_failure`** opnemen in registry als **dict** (JSON-vorm `{value, unit}`); geen `TimeDuration`-class in edit-buffer tot milestone 48.
- **FmEditorDialog** commit via **RunRunner** (progress, cancel waar ondersteund); resultaat terug naar werkruimte zoals nu **FmEditCommitResult**.
- **DirtySessionCoordinator**: bij open editor (werkruimte of vanuit validate) — if `FaalwijzenEditService.is_dirty()` → modal met opslaan/verwerpen/annuleren.
- Geen gedeelde sessie yet — editor houdt geïsoleerde sessie; alleen conflict-guard.

### Milestone 48 — Sessie & orchestratie fase 2

- **Gedeelde project-EditingSession**: `FaalwijzenEditService` en editor gebruikenzelfde buffer; editor opent FM-scope view i.p.v. clone (besluit grill 5C).
- **RunOrchestration** gedeeld: grid save/run en editor commit viazelfde adapter-entry; **RunRunner** overal waar UI async nodig is.
- Optioneel: **FaalwijzenGridPanel** hosten in resultatenwerkruimte (dock of modus-specifiek) — achter feature-flag of expliciet menu indien scope knelt.
- Registry: **`time_duration`** coercion (alleen als parity + validation story helder); anders dict blijven.
- ValidateWindow: compare/LTAP-panelen pas splitsen als actief onderhouden (ADR-0006).

### API-contracten (gedrag, geen bestandsnamen)

```text
apply_bulk_change(fm_ids: Sequence[str], field: str, raw_value: Any) -> BulkChangeResult
  # errors per fm_id/field; geen partial apply tenzij expliciet gedocumenteerd — default: all-or-nothing per call

replace_fm_scope(bundle: FmEditBundle) -> None
  # atomisch binnen session: faalwijzes rij + pbs + fm/pm links + pm tasks + task_groups + effect_klassen in scope

commit_fm_edits(session, *, path, save_to_disk, run_policy: RunPolicy) -> FmEditCommitResult
  # RunPolicy: blocking | via RunRunner callback
```

### Architectuur-principes (AGENTS.md)

- Views → alleen via **adapter**; geen `rcm_core` in views (typing-only ok).
- Adapter: **test-first** met pytest-qt waar Qt nodig is; pure services met unit tests.
- Incrementele run-seam: patch **`rcm_core.incremental_run`** in tests.
- Bij registry-wijziging die `models.py`/`schemas.py` raakt: **`test_editing_schemas_parity`** groen houden.

### ADR-0006

- Geen compare/scenario-slot UI in werkruimte.
- ValidateWindow mag wel faalwijzen-panel en compare houden; split compare/LTAP niet verplicht in 46–47.

## Testing Decisions

**Goede tests** beschrijven **gedrag aan publieke seams**: bulk past N rijen aan en validatie faalt voor hele call; schema-gedreven kolommen matchen registry; `replace_fm_scope` materieel gelijk aan huidige splice; editor commit triggert incremental run voor hash-gewijzigde FM’s; dirty-guard opent dialog — niet interne Qt-widget-hierarchie.

| Module | Testtype | Prior art |
|--------|----------|-----------|
| **FaalwijzenEditService** + bulk | Unit | `tests/test_desktop_faalwijzen_edit_service.py` |
| **EditingSession.replace_fm_scope** | Unit | `tests/test_desktop_fm_edit_services.py` (`apply_bundle_scope`) |
| **FmEditBundleAssembler** / row mappers | Unit | `tests/test_desktop_fm_edit_services.py`, CM-split tests |
| **Schema registry** | Parity | `tests/test_editing_schemas_parity.py` |
| **RunOrchestration / commit + RunRunner** | Unit + pytest-qt smoke | `tests/test_desktop_run_service.py`, workspace run tests |
| **DirtySessionCoordinator** | pytest-qt | `tests/test_desktop_results_workspace_window.py` |
| **FaalwijzenGridPanel** | Smoke — filter + bulk op fixture | slice 7 validate tests indien aanwezig |

**Verplichte tests (milestones):**

- 46: `apply_bulk_change` (happy + validation block); kolomset bevat minstens `failure_type` + `is_evident`; filter “zichtbare rijen” gedrag.
- 47: `replace_fm_scope` equivalentie; assembler round-trip bundle; editor commit met gepatchte incremental run; dirty guard minstens één pad.
- 48: gedeelde sessie integration (grid edit zichtbaar in editor scope); run orchestration één entry (smoke).

**Geen verplichte tests** voor compare/LTAP-split of workspace grid-host tenzij milestone 48 die feature levert.

## Out of Scope

- Nieuwe **FailureType**-motorwaarden (falen op vraag, tijdens missie).
- **Aanmaken** van nieuwe effectklassen vanuit grid of editor.
- **Volledige herberekening** als standaard na grid/editor save.
- **Verwijderen** van ValidateWindow of compare-stack (ADR-0006).
- **PBS bouwjaar** in batch-grid; gedeelde-PBS bulk-edit.
- **Effectlinks / PM-taken / taakgroepen** in batch-grid.
- **Excel import/export** van bulk-wijzigingen.
- **CACHE_INPUTS_VERSION**-bump tenzij motor-JSON van `faalwijzes`/`downtime` serialization wijzigt.
- **FM-hash PBS-refinement** (optionele follow-up uit slice 44).
- **Parallel run policy** (slice 43).
- Compare/LTAP-panel extract in milestone 46–47 (tenzij expliciet 48+ en apart issue).

## Further Notes

### Relatie andere slices

| Slice | Relatie |
|-------|---------|
| 44 | Editor blijft canoniek; deze PRD hardent commit/sessie |
| 45 | Quick wins done; deferred items hier opgepakt |
| 7 | Oorspronkelijk smal grid — wordt uitgebreid, niet vervangen |
| 23 | Editor host; workspace grid-host in 48 |
| 27 | NMF-copy consistent (`is_evident`) |
| ADR-0006 | Legacy compare blijft in ValidateWindow |

### Risico’s en mitigatie

| Risico | Mitigatie |
|--------|-----------|
| C→B→A scope creep | Expliciete fallback in issue 46; must = type+NMF+MTTF/sigma |
| Bulk op 1000+ FM’s UI-freeze | Milestone 48 RunRunner; 46 mag waarschuwing bij >N rijen |
| Dubbele buffer tot 48 | Dirty guard 47 |
| Registry dict vs. TimeDuration drift | Mappers gecentraliseerd; 48 coercion |
| Grid/ editor validatie verschil | Eén ENTITY_SCHEMAS bron |

### Issues (verticale AFK-tracers, gepubliceerd 2026-05-23)

| # | Titel | Type | Milestone | Blocked by |
|---|--------|------|-----------|------------|
| 01 | Tracer: `failure_type` + NMF + `apply_bulk_change` (selectie) | AFK | 46 | — |
| 02 | Tracer: must-kolommen C + celbewerking | AFK | 46 | 01 |
| 03 | Tracer: snelfilters, zoek + bulk zichtbare rijen | AFK | 46 | 02 |
| 04 | Tracer: ValidateFaalwijzenPanel + dunne shell | AFK | 46 | 03 |
| 05 | Tracer: `replace_fm_scope` + downtime dict + editor correctief | AFK | 47 | — (aanbevolen na 04) |
| 06 | Tracer: FmEditBundleAssembler | AFK | 47 | 05 |
| 07 | Tracer: RunRunner editor + dirty guard | AFK | 47 | 06 |
| 08 | Tracer: gedeelde EditingSession + run-orchestratie | AFK | 48 | 04, 07 |
| 09 | Tracer: workspace grid-host + optioneel `time_duration` | AFK | 48 | 08 |

**Implementatievolgorde:** `01 → 02 → 03 → 04` ‖ `05 → 06 → 07` → `08 → 09` (46 en 47 parallel mogelijk na 01).

*Supersedes horizontale issues (schema-only / panel-only splits).*

### Supersedes

Vervangt de open items in `.scratch/rcm-desktop-slice45-fm-edit-hardening/ARCHITECTURE_DEFERRED.md` — zie bijgewerkt bestand met link naar deze PRD.
