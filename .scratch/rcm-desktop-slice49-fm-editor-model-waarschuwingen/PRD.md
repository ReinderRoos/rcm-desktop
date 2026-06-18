# PRD — RCM2 desktop slice 49 (FM-editor UX & modelwaarschuwingen)

**Status:** ready-for-agent  
**Versie:** 1.0  
**Triage:** ready-for-agent  
**Type:** AFK (adapter-deep modules) + beperkte view-wijzigingen  
**Parent:** grill-me na slice 44/45/46 (productvalidatie optie B, 2026-05-23)  
**Relatie:** slice 44 (`FmEditorDialog`), slice 34 (FM-detail werkruimte), slice 43 (taakgroep-dedup motor), `validate_project` in kern  
**Datum:** 2026-05-23

## Problem Statement

Analisten gebruiken de **faalwijze-editor** in de **resultatenwerkruimte** (modus FM-detail) om individuele faalwijzen te corrigeren na import of modellering. In de praktijk levert dat **frictie en verkeerde conclusies** op:

1. **Taakgroep op preventieve taken** — Lege of ontbrekende `task_group_id` wordt als de string `"None"` getoond en opgeslagen, wat **FK-validatie** triggert (`task_group_id 'None' bestaat niet`) in plaats van een begrijpelijke keuze.
2. **MTTF en sigma** — Gebruikers verwachten dat **sigma** meeschalen met **MTTF** volgens de standaard **15%-regel** (zoals `Faalwijze.effective_sigma` in het domain model), terwijl de spinboxes onafhankelijk blijven tenzij de gebruiker sigma bewust heeft afgestemd.
3. **Werkruimte-modus na OK** — Na een geslaagde editor-commit springt de werkruimte terug naar **Top 10** omdat project-refresh de workspace-state reset; de analist verliest **FM-detail** terwijl hij net één FM heeft afgestemd.
4. **Modelkeuzes zonder begeleiding** — Combinaties zoals **veroudering (aging)** zonder **REV**-taak, of **REV** bij niet-verouderingsfaalmodellen, en **dezelfde PM-maatregel op verschillende PBS-componenten** zonder **taakgroep**, zijn niet zichtbaar vóór run/save. Bestaande `validate_project`-regels (bv. exponentieel + sigma > 0) zijn **hard** en niet als **begeleidende waarschuwing** in de editor gepositioneerd.

## Solution

Twee **AFK-batches** (kleine, testbare vertical slices):

| Batch | Doel | User-visible winst |
|-------|------|-------------------|
| **Batch 1 — Directe UX-fixes** | Taakgroep-dropdown, MTTF→sigma-gedrag, FM-detail behouden | Minder validatiefouten; voorspelbare parameters; blijven in FM-detail na OK |
| **Batch 2 — Modelwaarschuwingen v1** | Niet-blokkerende inconsistentie-signalen in editor | Vroeg zicht op waarschijnlijk inconsistente modelkeuzes; uitbreidbaar later |

**Rolverdeling (vast):**

- **FmEditorDialog** = plek voor waarschuwingen en PM-taakgroep-UI; geen nieuwe validate-window-features.
- **`validate_project`** = blijft authoritative voor **blokkerende** projectvalidatie bij materialiseren/run; slice 49 voegt **geen** duplicaat van bestaande error-codes toe in de UI tenzij als read-only hint (batch 2 scope: **alleen nieuwe** waarschuwingen).

## User Stories

### Batch 1 — Taakgroep & validatie

1. Als analist wil ik bij een preventieve taak **taakgroep** kiezen via een **dropdown** met bestaande taakgroepen en expliciet **“(geen)”**, zodat ik geen `"None"`-string invoer die FK-validatie breekt.
2. Als analist wil ik dat een lege taakgroep intern **`null`** is in de editing-buffer, zodat materialiseren en incrementele run niet onnodig falen.
3. Als analist wil ik dat bestaande taakgroepen uit het project (of de actieve **EditingSession**) in de dropdown staan, zodat ik kan koppelen zonder ID te onthouden.
4. Als ontwikkelaar wil ik normalisatie van `"None"`, `"null"` en lege string naar lege FK bij het inlezen van tabelcellen, zodat legacy data uit imports geen regressie veroorzaakt.

### Batch 1 — MTTF en sigma

5. Als analist wil ik dat bij wijziging van **MTTF** het veld **sigma** automatisch wordt gezet op **15% van MTTF**, zodat het scherm overeenkomt met de standaardregel in het domain model.
6. Als analist wil ik dat **sigma niet wordt overschreven** als ik sigma **bewust** heb afgesteld (afwijking van 15% van de huidige MTTF), zodat handmatige spreiding behouden blijft.
7. Als analist wil ik bij eerste openen van de editor sigma te zien zoals opgeslagen (inclusief 0 = “gebruik 15% in motor”), zodat ik weet wat er in het project staat.
8. Als ontwikkelaar wil ik een kleine tolerantie (epsilon) voor “afwijkende sigma”, zodat float-afronding geen vals “handmatig”-signaal geeft.

### Batch 1 — FM-detail behouden

9. Als analist wil ik na **OK** in de faalwijze-editor **in modus FM-detail** blijven met dezelfde scope, zodat ik direct verder kan verifiëren in het inspectorpaneel.
10. Als analist wil ik dat alleen bij **echt ander project** (nieuw bestand, andere load) de werkruimte-state reset naar defaults, zodat een incrementele FM-edit geen modus-wissel veroorzaakt.
11. Als analist wil ik dat na editor-commit de **incrementele run** en FM-inspector verversen, zodat cijfers kloppen zonder handmatig opnieuw te navigeren.

### Batch 2 — REV / aging

12. Als analist wil ik een **niet-blokkerende waarschuwing** als `failure_type` **aging** is en er **geen REV**-PM-taak op deze faalwijze staat, zodat ik weet dat verouderingsmodel en onderhoud mogelijk niet kloppen.
13. Als analist wil ik een **niet-blokkerende waarschuwing** als er **wel REV**-taken zijn maar het faaltype **geen aging** is, zodat ik inconsistente combinaties zie.
14. Als analist wil ik deze waarschuwingen op de **Basis**- of **Preventief**-tab zien (context-nabij), zodat ik ze tijdens invoer ziet, niet pas na run.
15. Als analist wil ik **OK** kunnen gebruiken ondanks waarschuwingen, zodat tussenstanden en bewuste afwijkingen mogelijk blijven.

### Batch 2 — Taakgroep-bundelhint (cross-component)

16. Als analist wil ik een **niet-blokkerende hint** als een **niet-REV** preventieve taak **geen taakgroep** heeft terwijl **bijna dezelfde maatregel** op een **ander PBS-component** voorkomt, zodat ik bundeling (inspectieronde, smeren, etc.) kan overwegen.
17. Als analist wil ik **geen hint** voor **REV**-taken zonder taakgroep, omdat REV typisch **individueel** wordt afgesteld en niet in een taakgroep hoort.
18. Als analist wil ik dat “bijna dezelfde maatregel” betekent: gelijk **taak_type**, gelijk genormaliseerde **taak_omschrijving**, en **interval_jaar** binnen **10%**, op een faalwijze met **ander `pbs_id`**, zodat toevallige tekstgelijkenis met ander interval geen ruis geeft.
19. Als analist wil ik in de hint zien **hoeveel andere componenten** matchen, zodat ik de ernst inschat.

### Batch 2 — Minimale consistentie (geen apart controles-tab)

20. Als analist wil ik **geen apart “Controles”-tabblad** in v1, zodat de editor overzichtelijk blijft.
21. Als product owner wil ik dat **bestaande** `validate_project`-fouten **niet** opnieuw als editor-lijst worden gebouwd in v1, zodat er één waarheid blijft bij save/run.
22. Als ontwikkelaar wil ik een **uitbreidbaar** waarschuwings-API (findings-lijst per FM-scope), zodat latere screenshot-regels (initial age, mission failure, enz.) kunnen worden toegevoegd zonder UI-refactor.
23. Als analist wil ik dat waarschuwingen **live** meebewegen bij wijziging van faaltype, MTTF, PM-tabel of taakgroep, zodat feedback direct is.

### Randgevallen

24. Als analist bewerk ik een faalwijze via een **gedeelde EditingSession** (grid + editor); waarschuwingen moeten op **edit_current**-data gebaseerd zijn, niet op verouderd baseline-project.
25. Als analist annuleert de editor, wil ik **geen** workspace- of waarschuwings-state mutatie, zodat Annuleren veilig blijft.

## Implementation Decisions

### Leveringsvolgorde

- **Batch 1** eerst (must): taakgroep-dropdown + normalisatie, MTTF→sigma-koppeling, FM-detail behouden.
- **Batch 2** daarna (should): `FmEditConsistencyService` + waarschuwingslabels in editor.

### Deep modules (nieuw of uitbreiden)

| Module | Verantwoordelijkheid | Interface (conceptueel) |
|--------|---------------------|-------------------------|
| **`PmTaskGroupCellEditor`** (view helper of delegate factory) | Dropdown `(geen)` + taakgroep-IDs voor PM-tabelkolom | `build_delegate(task_group_ids) -> QStyledItemDelegate` |
| **`normalize_optional_fk(value) -> str \| None`** | Map `""`, `"None"`, `"null"` → `None` voor project-backed FK | Pure functie in adapter; hergebruik bij table read en bundle assemble |
| **`FmSigmaCoupling`** | Bepaal of sigma “handmatig” is; bereken voorgestelde sigma bij MTTF-wijziging | `is_sigma_manual(mttf, sigma, *, epsilon) -> bool`; `coupled_sigma(mttf) -> float` |
| **`WorkspaceProjectRefreshPolicy`** | Onderscheid editor-commit vs. nieuwe project-load voor workspace reset | `should_reset_workspace(modus, reason: Literal["editor_commit","file_load",...]) -> bool` — of equivalent signaal op `AppState` |
| **`FmEditConsistencyService`** | Niet-blokkerende findings voor één `fm_id` uit edit-buffer + project | `findings(session \| project, fm_id) -> list[FmEditFinding]` met `code`, `severity=warning`, `message_nl`, optioneel `tab_hint` |
| **`PmMeasureSimilarityIndex`** | Vind PM-taken op andere `pbs_id` met zelfde maatregel-sleutel | `find_cross_component_matches(pm_row, all_pm_rows, fm_rows_by_id) -> list[Match]`; sleutel = `(taak_type, normalize_omschrijving, interval_bucket)` |

**`FmEditFinding` (dataclass, adapter-only):**

```text
code: str          # bv. "AGING_WITHOUT_REV", "REV_WITHOUT_AGING", "PM_BUNDLE_SUGGEST"
message_nl: str
tab_hint: "basis" | "preventief" | None
related_pm_id: str | None
peer_count: int | None   # voor cross-component hint
```

### REV / aging-regels (batch 2)

- **`AGING_WITHOUT_REV`:** `failure_type == aging` en geen PM op deze FM met `taak_type == REV` (interval > 0).
- **`REV_WITHOUT_AGING`:** minstens één REV op FM en `failure_type != aging`.
- Gebruik `TaskType` / `FailureType` enums; geen string-vergelijking buiten coerce-laag.

### Cross-component taakgroep-hint (batch 2)

- **Component** = `pbs_id` van parent-faalwijze.
- Alleen evalueren voor **huidige** PM-rij: `taak_type != REV`, lege `task_group_id`.
- Match peer PM waar parent-FM **`pbs_id` verschillend** is en maatregel-sleutel gelijk (type + genormaliseerde omschrijving + interval binnen 10%).
- Bestaande **`count_faalwijzen_for_task_group`** blijft voor **reeds gekoppelde** taakgroep; geen merge met bundle-hint.

### MTTF → sigma (batch 1)

- Bij `mttf` valueChanged: als **niet** `is_sigma_manual`, zet `sigma` op `0.15 * mttf` (spinbox-waarde; motor blijft `effective_sigma` gebruiken bij `sigma_jaar == 0`).
- Bij laden editor: respecteer opgeslagen `sigma_jaar`; koppel alleen op gebruikerswijziging MTTF.
- **Epsilon:** bijv. `max(1e-6, 0.001 * mttf)` voor manual-detectie.

### FM-detail behouden (batch 1)

- **`ResultsWorkspaceState.reset_for_new_project()`** niet aanroepen wanneer `set_last_project` volgt uit **FM-editor-commit** op hetzelfde project-pad /zelfde digest.
- Wel: presentatiecache / render-index refresh en `_refresh_fm_inspector` zoals nu na run.
- Implementatie-voorkeur: **call-site** in werkruimte (dubbelklik-handler) of `AppState` refresh-reason enum — geen brede refactor van alle `project_changed`-listeners.

### View-wijzigingen (minimaal)

- **FmEditorDialog:** sigma-koppeling signalen; waarschuwings-`QLabel` per tab (bestaand `_tg_warn`-patroon uitbreiden); PM-tabel `task_group_id`-delegate.
- **Geen** wijziging aan batch-grid contract (slice 46) in deze slice.

### Kern (`rcm_core`)

- **Geen** wijziging aan motor of `validate_project` verplicht voor slice 49.
- Optioneel vangnet: `normalize_key` in editing FK-validatie behandelt `"none"` als leeg — alleen als batch 1 nog import-leak ziet; niet vervanging van UI-normalisatie.

### Berichten

- Nieuwe strings in `messages.py` (NL) voor alle findings en dropdown “(geen)”.

### Architectuur

- **UI/kern-decoupling:** alle regels in `rcm_desktop.adapter`; views alleen tonen findings en delegates.
- **ADR-0006:** geen compare-stack in werkruimte.

## Testing Decisions

**Wat is een goede test:** observeerbaar gedrag via adapter-API’s en commit-flow; geen assert op interne QLabel-tekst of delegate-subklassen.

| Module | Te testen | Prior art |
|--------|-----------|-----------|
| `normalize_optional_fk` | `"None"` → `None`, `""` → `None`, geldige id blijft | `tests/test_editing_validation.py`, FK-tests |
| `FmSigmaCoupling` | manual-detectie + coupled waarde | `tests/test_models.py` (`effective_sigma`) |
| `FmEditConsistencyService` | aging/REV/cross-component scenario’s op fixture-project | `tests/test_aging_rev_integration.py`, slice 44 commit-tests |
| `PmMeasureSimilarityIndex` | interval 10%-grens, andere pbs_id, REV uitgesloten | nieuwe unit-tests |
| Workspace refresh policy | editor-commit reset **geen** modus wijziging | `pytest-qt` op adapter of werkruimte-state unit-test zonder volledige UI indien mogelijk |
| `FmEditCommitService` / integratie | commit met lege taakgroep geen FK `"None"` | bestaande slice 44 tests uitbreiden |

**Niet testen:** volledige `FmEditorDialog` layout (conventie AGENTS.md: pure UI niet test-gestuurd).

**Batch 1 tests** zijn must vóór merge; **batch 2** findings-service must, view smoke handmatig.

## Out of Scope

- Uitbreiding batch-grid (slice 46) met `failure_type`/NMF-kolommen — al elders.
- Nieuwe screenshot-regels niet in RCM2 (initial age, mission failure, exponentieel vs. vraag-falen, enz.) — expliciet TODO in service, geen v1-UI.
- Blokkerende OK bij waarschuwingen.
- Apart tabblad “Modelcontroles” of projectbrede findings-lijst in ValidateWindow.
- Fuzzy matching op `taak_omschrijving`.
- Automatisch aanmaken of voorstellen van taakgroep-IDs (alleen hint).
- Wijziging `CACHE_INPUTS_VERSION` (geen JSON-vormwijziging).
- Herziening van `validate_project`-regels in kern (bv. `FM_RANDOM_SIGMA_NONZERO` blijft zoals is).

## Further Notes

- **Grill-me bron:** productvalidatie na slice 46; optie B (kleine foutjes) vóór Kanban-vervolg.
- **Bestaand gedrag:** `Faalwijze.effective_sigma` — bij `sigma_jaar == 0` gebruikt de motor al 15% × MTTF; slice 49 synchroniseert vooral de **editor-UX** met die verwachting.
- **Taakgroep-domein:** taakgroep = logische bundel van PM-kosten (inspectieronde, smeren); REV meestal **zonder** taakgroep.
- **Vervolg (niet in PRD):** `/to-issues` verticale tracers batch 1 (3 issues) + batch 2 (2 issues); optioneel `KANBAN_HANDOFF.md` na implementatie.
- **PR na slice 46:** implementatie kan op bestaande FM-edit-fase2-branch of `main` na merge; geen harde branch-eis in dit document.
