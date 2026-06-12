# PRD — RCM2 desktop slice 59 (FM-editor: aanmaken, PM/taakgroep-koppeling, resultaten-tab)

**Status:** done  
**Versie:** 1.0  
**Triage:** done  
**Type:** AFK + UI (adapter deep modules + beperkte view-wijzigingen; geen `rcm_core` schema-drift)  
**Parent:** grill-me sessie FM-detail workflow (2026-06-02)  
**Relatie:** slice 44 (`FmEditorDialog`, commit + incrementele run), slice 49 (taakgroep-dropdown, modelwaarschuwingen), slice 34 (FM-inspector / `fm_verification_service`), slice 43 (taakgroep-deduplicatie motor), slice 7 (faalwijzen-grid — geen FM add/delete)  
**Datum:** 2026-06-02  
**Issue tracker:** https://github.com/ReinderRoos/rcm-desktop/issues/22

### Child issues (slice 59)

| # | Issue | Blocked by |
|---|-------|------------|
| 59.1 | https://github.com/ReinderRoos/rcm-desktop/issues/23 | — |
| 59.2 | https://github.com/ReinderRoos/rcm-desktop/issues/24 | #23 |
| 59.3 | https://github.com/ReinderRoos/rcm-desktop/issues/25 | #24 |
| 59.4 | https://github.com/ReinderRoos/rcm-desktop/issues/26 | #24 |
| 59.5 | https://github.com/ReinderRoos/rcm-desktop/issues/27 | #24 |

## Problem Statement

**Maintenance engineers** en reliability-analisten kunnen in modus **FM-detail** bestaande faalwijzen **bewerken** (slice 44), maar niet **nieuwe faalwijzen aanmaken** vanuit de resultatenwerkruimte. PM-taken en taakgroep-koppelingen zijn wel CRUD-baar in tab **Preventief**, maar het pad om een complete FM op te bouwen — nieuwe faalwijze → PM toevoegen → koppelen aan gedeelde taakgroep → resultaat controleren — vereist nu JSON-handwerk, legacy **ValidateWindow**, of kopiëren buiten de editor.

Daarnaast ontbreekt een **samenvattend resultaten-overzicht** in de editor zelf: lifecycle-totalen (faalmomenten, niet-beschikbaarheid CM+PM, PM-taaktellingen per type, eerste uitvoeringsjaar per taak) staan deels in het **inspectorpaneel** rechts, maar niet geïntegreerd in de bewerk-flow. Analisten moeten de dialoog sluiten om te zien of invoer klopt, of dubbelklikken na elke wijziging.

Cross-FM-koppeling van maatregelen gebeurt impliciet via **`task_group_id`**, maar zonder duidelijke UX om een PM aan een **bestaande taatgroep/maatregel** te koppelen of te zien welke andere faalwijzen dezelfde groep delen. Een persistente FM↔FM-relatie in het datamodel is **niet** gewenst in v1.

## Solution

Breid het FM-detail pad uit met een **end-to-end create- en opbouwworkflow** binnen en naast de bestaande **`FmEditorDialog`**:

1. **Nieuwe faalwijze** — toolbar-knop in FM-detail; `pbs_id` vooraf ingevuld vanuit geselecteerde **leaf-PBS** in de sidebar; create-modus met auto-`fm_id`, minimumvalidatie, incrementele run na opslaan.
2. **Opslaan zonder sluiten** — knoppen **Opslaan** (commit + run, editor blijft open, buffer reset) en **Opslaan en sluiten**; **Annuleren** sluit zonder extra commit (eerdere opslagen blijven).
3. **Vul van…** — optioneel sjabloon bij create én edit: kopieer alleen **Basis + Correctief** van een andere faalwijze (bevestiging bij overschrijven); geen persistente cross-FM-link.
4. **Preventief uitbreiden** — naast “Rij toevoegen”: **Koppel aan bestaande maatregel…** (picker op taakgroep/PM), **Nieuwe taakgroep…** (inline), preview van andere FM’s op dezelfde taakgroep.
5. **Tab Resultaten** (read-only) — FM-lifecycle-totalen uit laatste run + PM-subtabel (type, interval, taakgroep, **eerste uitvoeringsjaar** via LTAP-schedule); lege staat vóór eerste run; initiële leeftijd blijft op tab **Basis** (PBS-`bouwjaar`).

Geen nieuwe FM↔FM-relatie in `RCMProject`. Cross-component koppeling blijft **`task_group_id`** + copy-UX.

Ruggengraat: Qt-vrije deep modules voor create-insert, field-copy, taakgroep-picker/preview, resultaten-presentatie; dunne view-laag.

## User Stories

### Toegang en create

1. Als maintenance engineer wil ik in modus **FM-detail** op **Nieuwe faalwijze** kunnen klikken, zodat ik zonder JSON een FM kan toevoegen.
2. Als analist wil ik dat **Nieuwe faalwijze** alleen in FM-detail zichtbaar is, zodat Top 10 en Tijdsplot overzichtelijk blijven.
3. Als analist wil ik dat de knop **geblokkeerd** is met duidelijke melding als geen **leaf-PBS** in de sidebar geselecteerd is, zodat FM’s niet op verkeerd boomniveau ontstaan.
4. Als analist wil ik dat **`pbs_id` vast** staat op de geselecteerde leaf-PBS in create-modus, zodat locatie-fouten worden voorkomen.
5. Als analist wil ik dat **`fm_id` automatisch** wordt gegenereerd (`FM-###`, uniek), zodat FK-validatie niet faalt op handmatige IDs.
6. Als analist wil ik bij create minimaal **faalwijze_omschrijving**, **functie_id** en **mttf_jaar > 0** moeten invullen vóór opslaan, zodat lege FM’s niet in het project komen.
7. Als analist wil ik dat **functie_id** default de functie van de eerste bestaande FM op hetzelfde PBS krijgt, anders de eerste projectfunctie, zodat ik snel kan starten.
8. Als analist wil ik dat tabs **Effecten**, **Correctief** en **Preventief** leeg mogen zijn bij eerste opslaan, zodat ik incrementeel kan opbouwen.
9. Als analist wil ik na eerste opslaan van een nieuwe FM een **incrementele run** voor die `fm_id`, zodat resultaten beschikbaar komen zonder volledige recompute.

### Bewerken bestaande FM (ongewijzigd + uitbreiding)

10. Als analist wil ik in FM-detail nog steeds via **dubbelklik** de editor openen, zodat het bestaande pad behouden blijft.
11. Als analist wil ik na opslaan **in modus FM-detail** blijven (slice 49), zodat ik direct kan verifiëren.
12. Als analist wil ik de titelbalk met **fm_id**, omschrijving en PBS/bouwdeel blijven zien, zodat context duidelijk is.

### Opslaan, sluiten, annuleren

13. Als analist wil ik **Opslaan** kunnen gebruiken zonder de dialoog te sluiten, zodat ik PM’s kan toevoegen en daarna tab **Resultaten** kan bekijken.
14. Als analist wil ik **Opslaan en sluiten** voor het vertrouwde “klaar”-gedrag, zodat één actie volstaat na een kleine wijziging.
15. Als analist wil ik dat **Opslaan** geblokkeerd is bij validatiefouten, zodat geen inconsistent project wordt weggeschreven.
16. Als analist wil ik dat na **Opslaan** de edit-buffer wordt **herladen** uit de sessie/project, zodat de UI niet divergeert van opgeslagen staat.
17. Als analist wil ik dat na **Opslaan** tab **Resultaten** ververst met de nieuwste run, zodat ik feedback in dezelfde sessie krijg.
18. Als analist wil ik bij **Annuleren** een melding als er **niet-opgeslagen** wijzigingen sinds laatste Opslaan zijn, zodat ik weet wat verloren gaat.
19. Als analist wil ik dat **Annuleren** eerdere **Opslaan**-acties **niet** terugdraait, zodat tussentijds opgeslagen werk betrouwbaar blijft.
20. Als analist wil ik dat **Annuleren** zonder dirty buffer de dialoog gewoon sluit, zodat geen onnodige prompts verschijnen.

### Vul van… (sjabloon, smal)

21. Als analist wil ik bij **Nieuwe faalwijze** optioneel een **sjabloon-FM** kunnen kiezen, zodat ik faalmodel en CM-scenario kan overnemen.
22. Als analist wil ik bij een **bestaande FM** **Vul van…** kunnen gebruiken, zodat ik Basis + Correctief van een andere FM kan overnemen.
23. Als analist wil ik vóór overschrijven een **bevestiging**, zodat ik per ongeluk geen invoer verlies.
24. Als analist wil ik dat **Vul van…** alleen **Basis + Correctief** kopieert (faaltype, MTTF, sigma, NMF, omschrijving, CM-kosten, hersteltijd, scenario-teksten), zodat effecten en PM bewust blijven.
25. Als analist wil ik dat **Vul van…** **`fm_id`**, **`pbs_id`** en **`pm_id`’s** niet kopieert, zodat FK’s uniek blijven.
26. Als analist wil ik dat **Vul van…** geen **taakgroep-koppelingen** kopieert, zodat bundeling een bewuste keuze blijft.
27. Als analist wil ik dat **Vul van…** alleen faalwijzen uit het **zelfde project** toont, zodat FK’s naar functies/effectklassen kloppen.
28. Als analist wil ik dat **Vul van…** geen motor-run triggert tot ik **Opslaan** kies, zodat performance licht blijft.

### Preventief — PM en taakgroep

29. Als analist wil ik **PM-taken** kunnen toevoegen, wijzigen en verwijderen (bestaand slice 44), zodat het onderhoudsprogramma compleet is.
30. Als analist wil ik naast **Rij toevoegen** **Koppel aan bestaande maatregel…** kunnen gebruiken, zodat ik snel aan een bestaande **taakgroep** kan hangen.
31. Als analist wil ik bij koppelen een **picker** zien op taakgroepen/PM-taken in het project, zodat ik niet hoef te gissen naar `task_group_id`.
32. Als analist wil ik bij selectie van een taakgroep een **preview** zien welke **andere faalwijzen** dezelfde groep gebruiken, zodat gedeelde wijzigingen bewust zijn.
33. Als analist wil ik **Nieuwe taakgroep…** inline kunnen aanmaken (id, interval, kosten, duur, onbeschikbaarheid), zodat ik niet buiten de editor hoef te werken.
34. Als analist wil ik dat nieuwe taakgroep-IDs **automatisch uniek** worden, zodat validatie niet faalt.
35. Als analist wil ik **taakgroep-eigenschappen** inline kunnen bewerken wanneer een groep geselecteerd is (bestaand slice 44), met waarschuwing bij gedeeld gebruik.
36. Als analist wil ik **PM-effectlinks** per taak blijven beheren (bestaand slice 44), zodat PM-gevolgen traceerbaar zijn.
37. Als analist wil ik dat koppelen aan taakgroep **gedeelde interval/kosten/duur** uit de groep laat erven volgens bestaande motordocumentatie, zodat deduplicatie klopt.

### Tab Resultaten (read-only)

38. Als analist wil ik een tab **Resultaten** in de editor, zodat ik totalen zie zonder het inspectorpaneel te verlaten.
39. Als analist wil ik **verwacht aantal falen** (`expected_failures`) zien, zodat faalmodel + PM-effect samen beoordeeld kunnen worden.
40. Als analist wil ik **totale niet-beschikbaarheid** zien als som van correctieve downtime + PM-downtime over de lifecycle, zodat NB CM en PM samen zichtbaar zijn.
41. Als analist wil ik **aantallen IN / SVO / TST / REV**-taken voor deze FM zien, zodat het onderhoudsprogramma in één oogopslag klopt.
42. Als analist wil ik **initiële leeftijd** niet dubbel bewerken op tab Resultaten, zodat PBS-`bouwjaar` op tab Basis de enige invoer blijft.
43. Als analist wil ik per PM-taak in een subtabel **eerste uitvoeringsjaar** (horizon-index → kalenderjaar) zien via LTAP-semantiek, zodat planning leesbaar is.
44. Als analist wil ik dat **eerste uitvoeringsjaar** read-only is (geen planning-overlay-ankers in v1), zodat scope beheersbaar blijft.
45. Als analist wil ik vóór de eerste run een **duidelijke lege staat** (“Opslaan om resultaten te berekenen”), zodat ik niet denk dat data ontbreekt.
46. Als analist wil ik dat tab **Resultaten** na elke geslaagde **Opslaan** ververst, zodat cijfers actueel zijn.
47. Als analist wil ik dat het **inspectorpaneel** rechts na sluiten van de editor beschikbaar blijft, zodat snelle vergelijking zonder editor mogelijk is.

### Validatie, run, architectuur

48. Als analist wil ik **Nederlandse validatiefouten** vóór opslaan, zodat ik fouten kan corrigeren (bestaand slice 44).
49. Als analist wil ik na opslaan **incrementele analyse** (`full_recompute=False`), zodat grote projecten snel blijven.
50. Als analist wil ik bij run-fout na opslaan het project **wel opgeslagen** houden met melding, zodat invoer niet verloren gaat.
51. Als ontwikkelaar wil ik **views zonder `rcm_core`-imports** (behalve typing), zodat ADR UI/kern-decoupling geldt.
52. Als ontwikkelaar wil ik create/copy/resultaten-logica in **Qt-vrije adapter-modules** met pytest, zodat TDD op de seam blijft.
53. Als ontwikkelaar wil ik **geen nieuwe entiteit** in `RCMProject` voor FM↔FM-koppeling, zodat hash, import en validators stabiel blijven.
54. Als ontwikkelaar wil ik FM-insert via de **bestaande tabulaire editing-pipeline** (`faalwijzes` in schema registry), zodat één validate/materialize-pad geldt.

### Relatie bestaande UI

55. Als analist wil ik **ValidateWindow** niet nodig hebben voor nieuwe FM’s, zodat FM-detail het standaardpad wordt.
56. Als analist wil ik dat het **faalwijzen-grid** (slice 7/46) blijft werken voor homogene batch-correcties, zodat legacy niet breekt.
57. Als trainer wil ik in documentatie kunnen beschrijven: PBS selecteren → Nieuwe faalwijze → Opslaan → PM → Opslaan → Resultaten, zodat onboarding klopt.

### Randgevallen

58. Als analist wil ik dat **Nieuwe faalwijze** niet werkt zonder geladen project, zodat er geen lege sessie ontstaat.
59. Als analist wil ik na create dat de **nieuwe FM-rij** zichtbaar is in de FM-tabel (eventueel geselecteerd), zodat ik context behoud.
60. Als analist wil ik bij **Vul van…** op edit-modus dat **Effecten** en **Preventief** ongewijzigd blijven, zodat alleen Basis + Correctief worden geraakt.
61. Als analist wil ik bij **gedeeld PBS** (bouwjaar) nog steeds de bestaande waarschuwing (slice 44), zodat side-effects zichtbaar blijven.
62. Als analist wil ik dat **Opslaan** tijdens een lopende commit-run **geblokkeerd** is, zodat race conditions worden vermeden.

## Implementation Decisions

### Leveringsvolgorde (tracer bullets)

| Fase | Doel |
|------|------|
| **1 — Create FM** | Toolbar, create-modus editor, insert in editing-pipeline, incrementele run, FM-tabel refresh |
| **2 — Opslaan / lifecycle** | Opslaan vs Opslaan en sluiten, buffer-reset na commit, Annuleren-semantiek |
| **3 — Vul van… (smal)** | FM-picker + copy adapter + bevestigingsdialoog |
| **4 — Preventief UX** | Nieuwe taakgroep, koppel-picker, gedeeld-gebruik-preview |
| **5 — Tab Resultaten** | Read-only presentatie + PM-subtabel LTAP |

Fases 3 en 4 kunnen na fase 2 parallel; fase 5 hangt af van commit/run (fase 2).

### Deep modules (nieuw of uitbreiden)

| Module | Verantwoordelijkheid | Interface (conceptueel) |
|--------|---------------------|-------------------------|
| **`FmCreateService`** | Allocate uniek `fm_id`; bouw default faalwijze-rij voor `pbs_id`; resolve default `functie_id` | `allocate_fm_id(project\|session) -> str`; `default_faalwijze_row(pbs_id, functie_id) -> dict` |
| **`FmEditScopeLoader`** (uitbreiden) | Naast load by id: **seed empty bundle** voor create | `seed_create_bundle(session, pbs_id) -> FmEditBundle` |
| **`FmEditCommitService`** (uitbreiden) | **Insert** FM-scope (niet alleen replace); na commit buffer reload hook | `insert_fm_scope(session, bundle) -> None` (parallel aan `replace_fm_scope`) |
| **`FmFieldCopyService`** | Smalle kopie Basis + Correctief tussen FM-rows | `copy_fields(source_row, target_row, sections=("basis","correctief")) -> dict` |
| **`TaskGroupCatalogService`** | Lijst taakgroepen + reverse index FM’s per groep | `list_groups(session) -> ...`; `fms_for_group(group_id) -> tuple[str,...]` |
| **`PmMeasureLinkService`** | Resolve “koppel aan maatregel”: zoek PM/tg, stel `task_group_id` + gedeelde velden in | `apply_task_group_link(pm_draft, group_id, catalog) -> dict` |
| **`FmEditorResultsViewService`** | Bouw read-only resultaten-tab uit `FMResult` + project + PM-rijen | `build_editor_results_view(project, fm_id, fmr) -> FmEditorResultsView` |
| **`FmEditorResultsView`** (dataclass) | FM-totalen + `tuple[PmResultRow]` met type-counts en first execution year | Frozen presentatie-DTO, Qt-vrij |
| **`ResultsWorkspaceWindow`** (view) | Toolbar “Nieuwe faalwijze”; enable/disable op PBS-selectie | Dunne wiring naar dialog factory |
| **`FmEditorDialog`** (view) | Create vs edit mode; knoppen Opslaan / Opslaan en sluiten; tabs + Vul van… + Resultaten | Geen businesslogica |

### Create-modus contract

```text
fm_id          := auto FM-### (uniek in project/sessie)
pbs_id         := vast uit sidebar leaf-selectie (create only)
functie_id     := default sibling-FM op PBS, else eerste projectfunctie
failure_type   := "random"
mttf_jaar      := default 10.0, verplicht > 0
omschrijving   := verplicht non-empty
overige velden := schema-defaults; Effecten/Preventief mogen leeg
```

Insert-pad: seed bundle → user edits → validate → materialize → `insert_fm_scope` → incrementele run → affected bevat nieuwe `fm_id`.

### Opslaan-semantiek (state machine)

```text
OPEN → (Opslaan | Opslaan en sluiten) → COMMITTING → COMMITTED → OPEN (buffer reload)
OPEN → Annuleren → CLOSED (discard uncommitted delta only)
```

- **Opslaan en sluiten** = Opslaan + `accept()` / close.
- Geen undo-stack voor eerdere commits in v1.

### Vul van… (smal)

Velden gekopieerd: `failure_type`, `mttf_jaar`, `sigma_jaar`, `aging_distribution`, `beta_jaar`, `is_evident`, `repair_quality`, `faalwijze_omschrijving` (optioneel prefix “(kopie van {fm_id})”), `cost_cm_eur`, `downtime_per_failure`, `notes`, `aanname_cm_kosten`, `aanname_downtime`, `eindgevolg`, `p_ongewenste_gebeurtenis`.

Niet gekopieerd: ids, `pbs_id`, effectlinks, PM-taken, taakgroepen, `library_ref` (tenzij expliciet gewenst — default niet).

Picker: filter op `fm_id` + omschrijving; exclude huidige FM in edit-modus.

### Preventief — taakgroep UX

- **Nieuwe taakgroep…**: mini-form → rij in `task_groups` + set `task_group_id` op geselecteerde PM-rij.
- **Koppel aan bestaande maatregel…**: picker op unieke `task_group_id`’s met preview (omschrijving, interval, `# FM’s`).
- **Preview gedeeld gebruik**: hergebruik patroon slice 44 waarschuwing (`count_faalwijzen_for_task_group_in_edit`); uitbreiden met FM-id lijst in picker.

Geen wijziging aan motordeduplicatie (slice 43).

### Tab Resultaten

- FM-niveau: `expected_failures`, `expected_raw_downtime_hr + expected_detection_delay_hr` (CM NB), `expected_pm_downtime_hr`, `pm_cost_eur`, `expected_cm_cost_eur`, `total_cost_eur` — uit `FMResult` / `build_fm_verification_view`-equivalent.
- PM-tellingen: group `pm_tasks` by `taak_type` → counts IN/SVO/TST/REV.
- Per PM-rij: `pm_id`, type, interval, `task_group_id`, **first execution horizon year** via `ltap_executions_by_year(task, lifecycle_years, anchor_year=0)` → min year key → `calendar_year_for_horizon_index(modeljaar, year)`.
- `profile_missing` / geen `FMResult`: lege staat met instructie.
- Planning-overlay `anchor_years` **niet** in editor v1 (altijd 0).

### Schema / kern

- **Geen** nieuwe dataclasses in `RCMProject`.
- FM-insert via bestaande `faalwijzes` entity in editing schema (key `fm_id` nieuw).
- `task_groups` insert via bestaande registry (indien nog niet volledig in bundle-commit — align met slice 44 `replace_fm_scope`).

### UI-teksten

Alle labels via `rcm_desktop.messages` (Nederlands): o.a. `FM_EDITOR_SAVE`, `FM_EDITOR_SAVE_AND_CLOSE`, `FM_EDITOR_NEW_FM`, `FM_EDITOR_FILL_FROM`, `FM_EDITOR_TAB_RESULTATEN`, `FM_EDITOR_LINK_MEASURE`, `FM_EDITOR_NEW_TASK_GROUP`, `FM_EDITOR_RESULTS_EMPTY`.

## Testing Decisions

### Wat maakt een goede test

- Test **extern gedrag** en contracts: geen widget-internals, geen private method-names als orakel.
- Pure adapter: gegeven project/sessie + actie → verwachte rijen, validatiestatus, affected `fm_id`’s.
- View: smoke via pytest-qt — knop zichtbaar in FM-detail, create flow opent dialog, Opslaan triggert commit-runner (gemockt waar zwaar).

### Modules met tests (prioriteit)

| Module | Testtype | Prior art |
|--------|----------|-----------|
| **`FmCreateService`** | Unit | `tests/test_editing_layer.py`, `tests/test_fm_edit_*.py` |
| **`FmFieldCopyService`** | Unit | Field-level asserts op row-dicts |
| **`insert_fm_scope` / commit create** | Unit | `tests/test_fm_edit_commit_service.py` |
| **`TaskGroupCatalogService`** | Unit | `tests/test_fm_edit_bundle_service.py` (count helpers) |
| **`FmEditorResultsViewService`** | Unit | `tests/test_fm_verification_service.py`, `tests/test_ltap_*` |
| **`PmMeasureLinkService`** | Unit | PM row + group FK asserts |
| **Create toolbar + dialog smoke** | pytest-qt | `tests/test_desktop_results_workspace_window.py`, FM editor tests |

### Niet testen in v1

- Pixel-layout van nieuwe dialoogknoppen.
- Performance van FM-picker (O(n) over faalwijzen is acceptabel; geen benchmark-test).

## Out of Scope

- **Faalwijze verwijderen** (delete FM) — niet besproken in grill-me; apart slice indien gewenst.
- **Persistente FM↔FM-relatie** of PM↔PM-link buiten `task_group_id`.
- **Vul van… breed** (effecten + PM + taakgroep behouden) — expliciet afgewezen.
- **Planning-overlay-ankers** (`anchor_years`) bewerken in editor.
- **Live motor-preview** bij elke celwijziging (alleen na Opslaan).
- **Undo/redo** over meerdere Opslaan-acties in één sessie.
- **Add/delete faalwijzen** via batch-grid (slice 7 blijft zonder add/delete).
- **Nieuwe effectklasse** aanmaken in editor.
- **ValidateWindow** als parallel create-pad.
- **Meekoppelkansen** (ADR-0005) — blijft werkruimte LCC/what-if.
- **Rapportgeneratie** (slice 57) — geen overlap.

## Further Notes

### Risico’s

- **Buffer-reset na Opslaan**: zonder reload kunnen PM-rijen en sessie divergeren; verplicht onderdeel fase 2.
- **Create + gedeelde EditingSession** (grid + editor): insert moet op `edit_current` zitten, niet op stale project-only clone.
- **Eerste uitvoeringsjaar** met `anchor_year=0` wijkt af van what-if overlay — documenteer in UI-tooltip.
- **Vul van… op edit**: bevestiging essentieel; anders dataverlies Basis/Correctief.

### Documentatie

Na merge: korte sectie in gebruikershandleiding (`docs/gebruiker/HANDLEIDING.md`) — Deel B workflow “Nieuwe faalwijze opbouwen” (optioneel follow-up issue).

### Relatie slice 49

Batch 2 waarschuwingen (REV/aging, taakgroep-hint) blijven gelden; tab **Resultaten** is **geen** “Controles”-tab (slice 49 besluit blijft).
