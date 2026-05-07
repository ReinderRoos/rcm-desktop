# PRD — RCM2 desktop slice 7 (Faalwijzen-grid via tabulaire editing-pipeline)

**Status:** ready-for-agent  
**Versie:** 1.0  
**Triage-labels:** zie `../../AGENTS.md`

## Bron / context

- Project README en agent-/contextdocumentatie in de repo-root.
- Domeinvocabulaire: **RCMProject**, **PBSItem**, **Faalwijze**, **Functie**,
  **Editing schema registry**, **Tabulaire editing-pipeline**,
  **schema-backed FK** vs **project-backed FK**.
- Relevante kernlagen:
  - `rcm_core.editing.schemas.ENTITY_SCHEMAS["faalwijzes"]` (canoniek bewerk-
    contract, FK-regels, type-coercion).
  - `rcm_core.editing.validation.validate_entity_rows`
    (per-rij/per-cel-validatie, incl. `mttf_jaar > 0`).
  - `rcm_core.editing.state` (init/apply/validate session-dict).
  - `rcm_core.editing.pipeline` (build canoniek `RCMProject` uit
    edit-state).
- Voorgaande slices:
  - Slice 1 — validate-flow.
  - Slice 2 — projectpreview.
  - Slice 3 — run-contract en `RunRunner` op QThread.
  - Slice 4 — FM-resultatentabel.
  - Slice 5 — platte PBS-resultatentabel met DFS-aggregatie.
  - Slice 6 — read-only PBS-resultatenboom.
- Design-interview (slice 7): zie *Implementation decisions*.

## Problem statement

Na slices 1 t/m 6 kan een analist een project laden, valideren, runnen en
resultaten op meerdere niveaus inspecteren. Wat ontbreekt is de **bewerkbare
schakel**: faalwijze-invoer (zoals `mttf_jaar`, `sigma_jaar`, `cost_cm_eur`,
`functie_id`) kan in de huidige UI alleen vooraf in JSON worden bewerkt. Dat
breekt de **tracer-bullet-keten** "fixture laden → faalwijze aanpassen → run →
resultaat verschuiven", die het hart vormt van het pedagogisch effect én de
dagelijkse RCM-workflow.

De **kern** levert hier alles voor: de tabulaire editing-pipeline kent al
typecoercion, FK-resolutie en domeinregels. Wat ontbreekt is een
**adapter-/UI-laag** die deze pipeline op een ergonomische `QTableView`-
ervaring binnenhaalt, zonder de `rcm_core`-discipline te breken (geen Qt in de
kern, geen `editing.*`-imports in views).

## Solution

Voeg een verticale slice toe die **faalwijzen** bewerkbaar maakt in
`validate_window`, gekoppeld aan de bestaande editing-pipeline:

1. **Deep adaptermodule `faalwijzen_edit_service`** — single waarheid voor de
   slice 7-bewerkbare contractlaag boven de pipeline. Stelt rijen, edits,
   per-cel-errors en run-materialisatie als één smal interface beschikbaar.
2. **Qt-grid (`QTableView`)** met een **dunne** `FaalwijzenTableModel`-facade en
   **delegates per kolomtype** (text, FK-combobox, numeriek, read-only).
3. **Per-cel feedback** voor validator-errors uit de pipeline: rode
   highlight + tooltip met de Nederlandstalige foutboodschap.
4. **Run-knop gating** — Run --full kan niet starten zolang de edit-buffer
   errors heeft.
5. **Lazy materialisatie** — pas bij Run --full wordt een **vers
   `RCMProject`-snapshot** uit de edit-buffer gebouwd en aan `RunRunner`
   gegeven. `last_project` (laatst-gevalideerde basis) blijft tussen runs
   onveranderd.
6. **In-memory only** — wijzigingen worden in deze slice **niet** naar schijf
   geschreven; de architectuur ondersteunt een latere expliciete Save-slice.
7. **Harde reset** van edits bij padwijziging of nieuwe validate; een
   dirty-flow met "weet je het zeker?" is bewust uitgesteld.
8. **Plaatsing** — nieuwe `QGroupBox` "Faalwijzen bewerken" boven de
   FM-resultatentabel, onder run/preview-paneel; alleen zichtbaar onder de
   bestaande validate-poort.

## User stories

### Analist — bewerken en run-impact

1. Als reliability-analist wil ik na een succesvolle validate een tabel met
   faalwijzen zien, zodat ik snel kan zien waarop ik kan ingrijpen.
2. Als analist wil ik per faalwijze de **MTTF (`mttf_jaar`)** en
   **sigma (`sigma_jaar`)** kunnen wijzigen, zodat ik veroudering en spreiding
   gericht kan kalibreren.
3. Als analist wil ik **CM-kosten (`cost_cm_eur`)** kunnen wijzigen, zodat ik
   kostenscenario's kan doorrekenen zonder de JSON te bewerken.
4. Als analist wil ik **`p_ongewenste_gebeurtenis`** kunnen wijzigen, zodat ik
   gevolgkansen direct in de UI kan kalibreren.
5. Als analist wil ik de **`faalwijze_omschrijving`** kunnen aanpassen, zodat
   nuance in de tekstuele beschrijving meteen in mijn analyse landt.
6. Als analist wil ik **`functie_id` (FK)** kunnen wijzigen via een
   keuzelijst gevuld uit de functies van het project, zodat ik geen typo's
   maak en alleen geldige verwijzingen kies.
7. Als analist wil ik dat **id-velden** (`fm_id`, `pbs_id`) **read-only**
   zijn in deze slice, zodat ik per ongeluk geen FK-koppelingen breek.
8. Als analist wil ik na het bewerken van een faalwijze op **Run --full**
   klikken en zien dat het resultaat verschuift, zodat ik direct effect zie
   van mijn aanpassing.
9. Als analist wil ik dat mijn edits **niet automatisch naar schijf** gaan,
   zodat ik vrij kan experimenteren zonder bronbestanden per ongeluk te
   wijzigen.

### Analist — validatie-feedback

10. Als analist wil ik dat foutieve cellen (bv. `mttf_jaar ≤ 0`)
    **rood gemarkeerd** worden, zodat ik fouten direct herken.
11. Als analist wil ik bij het hoveren over een foutieve cel een **tooltip**
    met de uitleg zien, zodat ik weet hoe ik het moet repareren.
12. Als analist wil ik dat **typefouten** (bv. een woord in een numeriek
    veld) als zodanig worden gemarkeerd via dezelfde kanalen.
13. Als analist wil ik dat **FK-fouten** (`functie_id` verwijst naar
    onbekende functie) automatisch onmogelijk zijn doordat ik alleen via een
    keuzelijst kan kiezen.
14. Als analist wil ik dat **Run --full** geblokkeerd is zolang er nog
    edit-errors zijn, zodat ik niet per ongeluk een ongeldig snapshot run.

### Analist — werkflow en consistentie

15. Als analist wil ik dat het grid pas **zichtbaar** is na een geldige
    validate met geladen project, zodat de UI niet bewerkbaar oogt op
    momenten waar de keten niet rond is.
16. Als analist wil ik dat **padwijziging** of **nieuwe validate** mijn
    edits hard reset, zodat ik nooit edits van het ene project op een ander
    project meeneem.
17. Als analist wil ik dat de **FM-resultatentabel** en **PBS-paneel** uit
    eerdere slices ongewijzigd in gedrag blijven, zodat deze slice alleen
    een nieuw bewerkpaneel toevoegt.
18. Als analist wil ik dat ik **alleen bestaande** faalwijzen kan
    bewerken (geen add/delete in deze slice), zodat ik me kan focussen op
    parametervariatie zonder schema-uitbreidingen.

### Analist — UX-klein

19. Als gebruiker wil ik dat **NL-decimaalkomma** (bv. `1,5`) ook
    geaccepteerd wordt in numerieke velden, zodat de UI bij Nederlandstalige
    invoer past.
20. Als gebruiker wil ik dat de **FK-combobox** voor `functie_id` toont
    welke functies beschikbaar zijn (id + omschrijving), zodat ik snel een
    correcte keuze maak.
21. Als gebruiker wil ik een **lege** `functie_id` kunnen selecteren als
    "geen functie", tenzij de validator dat verbiedt; ik volg dan exact wat
    de validator zegt.

### Ontwikkelaar — architectuur en testbaarheid

22. Als ontwikkelaar wil ik dat **alle business-logica** voor het grid in een
    pure adaptermodule (`faalwijzen_edit_service`) zit, zodat ik gedrag los
    van Qt kan unit-testen.
23. Als ontwikkelaar wil ik dat het Qt-grid een **dunne facade** is op de
    adapter, zodat refactor van indexing of delegates de pipeline niet
    raakt.
24. Als ontwikkelaar wil ik dat **`RunRunner` ongewijzigd** blijft (slice 3),
    en dat materialisatie buiten de runner gebeurt, zodat slice 3-tests niet
    breken.
25. Als ontwikkelaar wil ik dat **geen view direct** uit `rcm_core.editing.*`
    importeert, zodat de UI/kern-decoupling intact blijft.
26. Als ontwikkelaar wil ik dat de adapter-API **stabiel genoeg** is om
    later add/delete en Save additief toe te voegen zonder bestaande
    methodes te breken.

### Forward compatibility

27. Als productowner wil ik dat een latere slice **expliciete Save-knop**
    kan toevoegen op basis van een dirty-flag in de adapter, zonder de
    bestaande publieke methodes te wijzigen.
28. Als productowner wil ik dat een latere slice **add/delete** van
    faalwijzen kan toevoegen, zonder de slice-7-edits te breken.
29. Als productowner wil ik dat een latere slice **meer kolommen
    bewerkbaar** kan maken (bv. `failure_type`, `repair_quality`,
    `is_evident`, `library_ref`) zonder dat de adapter-API breekt.

### Randgevallen

30. Als ontwikkelaar wil ik vastgelegd gedrag voor **lege FK** (`functie_id`
    leeg): we volgen wat `editing.validation` retourneert. Als leeg geldig
    is, worden geen errors getoond; als leeg ongeldig is, krijgt de cel een
    rode highlight.
31. Als ontwikkelaar wil ik dat **NL-decimaalcoercion** wordt opgevangen aan
    de adapter-zijde voor zover de bestaande `coerce_value` dat niet doet;
    een eventuele kleine helper hoort in de adapter, niet in de view.
32. Als ontwikkelaar wil ik dat **tracé van errors** zichtbaar blijft per
    rij en per veld via een vast contract op de service, zodat het Qt-model
    geen eigen ErrorBag hoeft te beheren.

## Implementation decisions

- **Deep module — `faalwijzen_edit_service`** (definitieve naam in code):
  smalle, stabiele facade boven `editing.state` / `editing.validation` /
  `editing.pipeline`. Verantwoordelijkheden:
  - **Init/reset** uit een `RCMProject` (laatst-gevalideerd snapshot).
  - **Read** een lijst rijen-DTOs voor de slice 7-kolommen, inclusief
    per-cel-errors.
  - **Write** een edit per (rij, veld, raw-value); voert coercion +
    `validate_entity_rows("faalwijzes", ...)` minimaal voor de geraakte
    rij, maar mag (bij eenvoud) ook over alle rijen draaien als performance
    geen probleem geeft op realistische projectomvang.
  - **Status**: `has_errors`, `error_count`, `changed`-callback (signaal in
    Qt-laag of pure callable in pure laag, te kiezen tijdens implementatie).
  - **Materialize** voor Run: voert `validate_all_entities` +
    `build_project_from_state` uit en levert een **vers
    `RCMProject`-snapshot** of een **typed error** als er edit-errors zijn.
  - Geen Qt-imports.

- **Bewerkbare kolomset (slice 7):** `faalwijze_omschrijving`,
  `functie_id`, `mttf_jaar`, `sigma_jaar`, `cost_cm_eur`,
  `p_ongewenste_gebeurtenis`. **Read-only** kolommen voor context:
  `fm_id`, `pbs_id`. **Niet getoond** in deze slice: `failure_type`,
  `repair_quality`, `is_evident`, `library_ref`.

- **Editors per kolom (delegates):**
  - **Text** (`faalwijze_omschrijving`) → `QLineEdit`.
  - **Numeric** (`mttf_jaar`, `sigma_jaar`, `cost_cm_eur`,
    `p_ongewenste_gebeurtenis`) → `QLineEdit` met coercion via de
    pipeline; NL-decimaalkomma toegestaan.
  - **FK** (`functie_id`) → `QComboBox` gevuld uit `RCMProject.functies`
    (display = `id — omschrijving`; lege keuze toegestaan).
  - **Read-only** (`fm_id`, `pbs_id`) → niet bewerkbaar; alleen
    DisplayRole.
  - Eén **delegate per kolomtype** voor herbruikbaarheid en testbaarheid.

- **Validatie & feedback:** **on-edit**, via dezelfde
  `editing.validation`-laag als de huidige validate-flow. Foute cellen
  krijgen rode highlight + tooltip met `ErrorObj.message`. Run --full is
  geblokkeerd zolang `has_errors()` true is.

- **Run-pad:** `_start_run` haalt het project via
  `materialize_for_run()` uit de edit-service en geeft dat aan
  `RunRunner`. `RunRunner` blijft ongewijzigd. Bij errors wordt run niet
  gestart en toont de UI een modal (consistent met huidige `_show_run_error`
  flow, zonder daadwerkelijk runner te raken).

- **Reset-discipline:** harde reset van de edit-service bij:
  - padwijziging,
  - start nieuwe validate,
  - succesvolle validate (re-init op nieuw `last_project`),
  - klaarzetten van een nieuw run-resultaat: edits blijven, alleen run-
    panelen veranderen (geen reset van edits zodra het project verder loopt).

- **Plaatsing in `validate_window`:** nieuwe `QGroupBox`
  "Faalwijzen bewerken" tussen `run_group` en `result_table_group`. Zichtbaar
  alleen wanneer de bestaande Run-poort waar is (laatste validate
  `valid` / `valid_with_warnings` + project geladen). Anders verborgen.

- **AppState-impact:** zo klein mogelijk; de service is owner van de
  edit-buffer. Eventuele lichte signalen (`edit_changed`) mogen in
  `AppState` om de Run-knop-gating elegant te bedraden, mits geen kennis
  over kolommen lekt.

- **Threading:** edits en materialisatie zijn synchroon op de UI-thread
  (klein qua data). `RunRunner` blijft, zoals nu, op een werkthread.

- **Architectuurregels:** views importeren `editing.*` **niet**
  rechtstreeks; alle bindings via de service en bestaande adaptertypes.
  Geen Qt-imports in `rcm_core.*`.

- **Issue-split (drie issues, alle AFK):**
  - **Issue D — Pure adapter `faalwijzen_edit_service`** + unit-tests.
    Geen Qt.
  - **Issue E — Qt-grid `FaalwijzenTableModel` + delegates** + tests met
    `pytest.importorskip("PySide6")`. **Blocked by D.**
  - **Issue F — `validate_window`-integratie + run-pad** + flow-tests.
    **Blocked by E.**

### Beslissingsschema (uit grill-me, samengevat)

```
Persistentie       : in-memory only (Save = latere slice)
Reset bij path/val : harde reset, geen modal
Zichtbaarheid      : alleen onder Run-poort (valid + project)
Read-only kolommen : fm_id, pbs_id
Bewerkbare kolommen: faalwijze_omschrijving, functie_id, mttf_jaar,
                     sigma_jaar, cost_cm_eur, p_ongewenste_gebeurtenis
Validatie          : on-edit, via editing.validation
Run-gating         : disabled bij has_errors()
Materialisatie     : lazy, bij Run, buiten RunRunner
Editors            : text, fk-combobox, numeric, readonly (delegates)
Rij-acties         : alleen edits, geen add/delete
Plaatsing          : QGroupBox boven FM-tabel
Adapter-API        : init/rows/apply_change/has_errors/error_count/
                     changed/materialize_for_run/reset
Issue-split        : D (pure) → E (Qt) → F (UI+run-pad)
```

## Testing decisions

- **Goede tests** bewijzen **extern gedrag** via de service-API en de
  Qt-modelfacade; niet privé-state of indexing.

- **Pure adapter (issue D):**
  - `init` op een fixture-`RCMProject` levert juiste rijen voor de slice 7-
    kolommen en geen errors bij ongewijzigde input.
  - `apply_change` voor numeriek met geldige waarde update de rij en heeft
    geen errors.
  - `apply_change` voor `mttf_jaar = 0` produceert een
    `FM_MTTF_NONPOSITIVE`-error op de juiste cel; `has_errors()` true.
  - `apply_change` voor `functie_id` met onbekende waarde produceert een
    FK-error (verwacht via pipeline); `has_errors()` true.
  - `apply_change` met NL-decimaalkomma `"1,5"` levert intern een float
    `1.5` op of een gecontroleerde policy-fout — minimaal vastleggen
    welke variant.
  - `materialize_for_run()` retourneert een nieuw `RCMProject` waarvan
    de FM-objecten de gewijzigde waarden dragen; werkt alleen wanneer
    `has_errors()` false is.
  - `reset` brengt service terug op originele rijen.

- **Qt-grid (issue E):**
  - `rowCount`/`columnCount`/`headerData` consistent met de slice 7-
    kolomset.
  - `data(DisplayRole)` toont gecoerce waarden (NL-formattering waar
    passend voor display, raw waarde voor edit).
  - `flags()` markeert `fm_id`/`pbs_id` als niet-bewerkbaar; andere
    kolommen wel.
  - Foutindicator (`Qt.BackgroundRole` of equivalent) en tooltiprol
    (`Qt.ToolTipRole`) bevatten de juiste boodschap voor gemarkeerde
    cellen.
  - Combobox-delegate biedt de in `RCMProject.functies` aanwezige IDs
    (plus lege keuze).

- **Flow (issue F):**
  - Onder Run-poort verschijnt het grid; daarbuiten verborgen.
  - Padwijziging en nieuwe validate resetten de edits zonder modal.
  - Edit met error → Run-knop gaat uit; error wegnemen → Run-knop weer
    aan.
  - Run --full op gewijzigd grid levert een `RunResult` waarvan de
    metrics/rows zichtbaar verschuiven t.o.v. baseline (via fake
    `run_incremental_analysis` zoals in slice 3-tests).

- **Prior art:** patronen uit `test_desktop_*` en
  `test_editing_layer.py` / `test_editing_pipeline.py` voor pure
  pipeline-aspecten.

## Out of scope

- **Persistentie naar schijf**, **Save-knop**, **dirty-flag**,
  **confirm-bij-pad-switch**, **undo/redo** — staan op de Save-slice.
- **Add/delete** van faalwijzen.
- **Bewerken van andere entiteiten** (`pbs`, `pm_tasks`,
  `effect_klassen`).
- **Bewerken van schema-velden buiten de slice 7-set**
  (`failure_type`, `repair_quality`, `is_evident`, `library_ref`).
- **Bewerken van id-velden** (`fm_id`, `pbs_id`).
- **Bulk-paste**, **CSV-import**, **Excel-import**.
- **Cross-entity validatie** of cascades naar `pm_tasks`/effect-links.
- **Performance-optimalisatie** voor zeer grote projecten (lat. >5000 FMs)
  bovenop wat de pipeline al levert.
- **Wijziging aan `RunRunner`** of `IncrementalRunResult`-contract.
- **PM/CM-scenario-uitsplitsing** of nieuwe KPI-kolommen.

## Further Notes

- Risico: dirty edits kunnen verwarrend zijn zonder Save-knop; in deze
  slice mitigeren we dat met **harde reset** bij path/validate. De latere
  Save-slice voegt een dirty-flag + bevestigingen toe.
- Risico: `editing.validation` accepteert mogelijk geen NL-decimaalkomma
  rechtstreeks. Issue D kan een minimale coercie-helper toevoegen (bv. `,`
  → `.` in numerieke velden) **in de adapter**, om de kern niet te raken.
- Risico: zonder dirty-tracking kan een gebruiker een edit verliezen door
  een onbedoelde validate. Dit is een **bewuste** kost in slice 7;
  documentatie/tooltip op de Validate-knop kan in een latere UX-slice
  helpen.
- Forward-compat: de adapter-API is gekozen zodat add/delete, save,
  undo/redo en uitbreiding van bewerkbare kolommen **additief** kunnen
  zonder de huidige methodes te breken.
