# PRD — RCM2 desktop slice 3 (`run --full` vanuit UI)

**Status:** ready-for-agent
**Versie:** 1.0
**Triage-labels:** zie `../../AGENTS.md`

## Bron / context

- `../../README.md`
- `../../AGENTS.md`
- `../../CONTEXT.md`
- `../../../rcm/.scratch/rcm2-restart-reference/RCM2_REFERENTIE.md`
- Voorgaande slices:
  - `../rcm-desktop-slice1-validate/` (validate vanuit UI)
  - `../rcm-desktop-slice2-preview/PRD.md` (project-preview na validate)
- Design-interview (vastgelegde beslissingen): zie sectie *Implementation
  decisions*.

## Problem statement

Na slice 1 + slice 2 kan de analist een projectbestand selecteren, valideren
en een minimale **project-preview** zien (tellingen + top-5 faalwijzen). Wat
nog ontbreekt is de **inhoudelijke berekening**: de gebruiker kan vanuit de
desktop-UI nog geen analytische run uitvoeren. Daardoor is de tool nog geen
zelfstandig bruikbare desktop-variant van RCM2 — voor élke berekening moet de
gebruiker terugvallen op de CLI (`python -m rcm_core.cli run ... --full`).
De feedbackloop voelt afgehakt: validate + preview zonder de natuurlijke
vervolgstap "doe nu een run en laat me zien wat eruit komt".

## Solution

Voeg een verticale slice toe die `run --full` rechtstreeks vanuit de desktop-
UI mogelijk maakt, met een minimale maar inhoudelijk zinvolle uitkomst:

1. **Aparte `run_service` in de adapter**, los van validate en preview, met
   een eigen contract en eigen mapping van fouten.
2. **Eigen `RunRunner`** op een `QThread` (zelfde patroon als
   `ValidateRunner`); UI blijft responsief.
3. **Run-knop naast Validate-knop**; alleen enabled als de laatste validate
   de status `valid` of `valid_with_warnings` had én er een geladen project
   in `AppState` aanwezig is.
4. **Resultaatpaneel onderaan** met status, korte samenvatting en drie
   inhoudelijke kerncijfers: `#FM-results`, totale lifecycle-faalmomenten en
   totale kosten (€).
5. **Project-hergebruik**: de run pakt het bij validate al geladen
   `RCMProject` uit `AppState` — geen tweede disk-read; `path` blijft mee
   voor cache-koppeling.
6. **Reset-discipline**: het run-paneel wordt geleegd bij elke wijziging
   van het bestandspad, bij elke nieuwe validate én bij elke nieuwe run.
7. **Vocabulaire**: in alle UI-strings hanteren we **"faalmomenten"** (niet
   "falingen") en **"niet-beschikbaarheid"** (niet "onbeschikbaarheid"),
   consistent met de domeintaal.

## User stories

1. Als analist wil ik na een geslaagde validate met één klik een volledige
   analytische run starten, zodat ik zonder CLI-omweg de berekening krijg.
2. Als analist wil ik dat de Run-knop alleen actief is als het project
   geldig is (eventueel met waarschuwingen), zodat ik geen onbruikbare
   runs tegen kapotte projecten start.
3. Als analist wil ik dat de UI tijdens de run niet bevriest, zodat ik kan
   zien dat er iets gebeurt en de app niet hoef af te schieten.
4. Als analist wil ik dat de Run-knop tijdens een lopende run uitstaat,
   zodat ik niet per ongeluk twee runs achter elkaar trigger.
5. Als analist wil ik na een succesvolle run direct zien hoeveel
   faalwijzen meegerekend zijn, hoeveel faalmomenten over de lifecycle
   verwacht worden, en wat de totale kosten zijn, zodat ik in één
   oogopslag kan inschatten of de uitkomst plausibel is.
6. Als analist wil ik dat er een duidelijk run-status-label (bijv.
   "Run geslaagd" of "Run mislukt") naast de cijfers staat, zodat ik
   onmiddellijk zie of de berekening is gelukt.
7. Als analist wil ik dat het run-resultaat verdwijnt zodra ik het
   projectbestandspad wijzig, opnieuw valideer of opnieuw run, zodat ik
   nooit per ongeluk naar een verouderd resultaat kijk.
8. Als analist wil ik bij een mislukte run een begrijpelijke melding zien
   (preconditie niet voldaan vs. interne fout), zodat ik weet of ik
   eerst moet valideren of dat er iets dieper aan de hand is.
9. Als analist wil ik dat een eerder validate-/preview-resultaat zichtbaar
   blijft naast het run-resultaat, zodat ik context (welk project,
   hoeveel items) niet kwijtraak tijdens analyse.
10. Als ontwikkelaar wil ik een pure `run_service.run(project, path)` met
    een vast `RunResult`-contract, zodat de UI-laag altijd hetzelfde shape
    krijgt en er één plek is om mappings te onderhouden.
11. Als ontwikkelaar wil ik dat `run_service` de echte engine via een
    dunne seam aanroept (`rcm_core.incremental_run.run_incremental_analysis`
    met `full_recompute=True`), zodat de bestaande test-seam (zie
    `AGENTS.md`) intact blijft.
12. Als ontwikkelaar wil ik dat `RunRunner` precies dezelfde status-codes
    gebruikt als `ValidateRunner` (`idle`, `busy`, `done`, `error`),
    zodat de view één rendering-pattern hoeft te onderhouden.
13. Als ontwikkelaar wil ik dat het geladen project in `AppState`
    bewaard wordt (`last_project` + `project_changed`), zodat de
    Run-knop-gating en de run-input zonder verborgen state werken.
14. Als reviewer wil ik dat de adapter/views-decoupling uit `AGENTS.md`
    gerespecteerd blijft (geen directe `rcm_core`-imports in views,
    behalve typing), zodat de architectuurregels niet eroderen.
15. Als reviewer wil ik dat de Qt-tests netjes skippen wanneer `PySide6`
    niet beschikbaar is, zodat de testsuite ook in headless/CI-omgevingen
    consistent draait.

## Implementation decisions

- **Aparte `run_service` in `rcm_desktop.adapter`**.
  Run is een eigen domeinconcept; we mengen het niet met validate of
  preview. Validate blijft single-purpose; run krijgt een eigen contract.

- **Adapter roept de kern direct in-process aan**:
  - Aanroep: `rcm_core.incremental_run.run_incremental_analysis(project,
    project_path, full_recompute=True, parallel=False)`.
  - Geen subprocess, geen extra wrapper-laag in `rcm_core`. Dit blijft op
    de bestaande **test-seam** uit `AGENTS.md` (patch op
    `rcm_core.incremental_run as ir`).

- **`RunResult`-contract** (adapter-niveau dataclass):
  - `status`: één van `done` of `error`.
  - `summary`: korte NL-samenvatting (1-2 regels).
  - `metrics`: drie kerncijfers
    - `fm_result_count` (aantal `FMResult`-rijen)
    - `total_lifecycle_faalmomenten` (som over `expected_failures` van alle
      `FMResult`s; in UI getoond als **"faalmomenten"**)
    - `total_cost_eur` (som over `total_cost_eur` van alle `FMResult`s)
  - `error: UserFacingError | None` met code uit
    `{RUN_PRECONDITION_NOT_MET, RUN_INTERNAL_ERROR}`.
  - Mode-parameter (`full_recompute`) zit in het service-contract zodat
    later incrementele/parallel-modi kunnen worden toegevoegd zonder
    API-breuk.

- **Trigger-regel run**: `run_service.run` mag alleen lopen als de caller
  een geldig `RCMProject` aanlevert. De UI bewaakt zelf de gate
  (`last_result.status in {valid, valid_with_warnings}` én
  `last_project is not None`). Bij ontbrekende gate wordt geen run gestart
  en geeft de service `RUN_PRECONDITION_NOT_MET` terug als een caller dit
  toch doet.

- **Threading-strategie**:
  - Eigen `RunRunner` op `QThread` (analoog aan `ValidateRunner`).
  - Statussen: `idle`, `busy`, `done`, `error` (uniform).
  - Re-entrancy-guard in de runner; daarnaast UI-zijdig knop-disable
    tijdens `busy`.
  - Geen cancel-pad in deze slice (engine biedt geen cancellation-hook).

- **Parallel-default deze slice**: `parallel=False`. Het contract houdt de
  parameter open; een latere slice kan een toggle of default-flip
  introduceren zonder API-breuk.

- **AppState-uitbreidingen**:
  - Nieuw veld `last_project: RCMProject | None`, gevuld vanuit het
    validate/preview-pad.
  - Nieuw signaal `project_changed(RCMProject | None)`.
  - Nieuw veld `last_run: RunResult | None`.
  - Nieuw signaal `run_changed(RunResult | None)`.
  - Bestaande `last_result`/`result_changed` en `last_preview`/
    `preview_changed` blijven gedragsgelijk aan slice 1/2.

- **UI-plaatsing**:
  - Run-knop staat **naast** de Validate-knop in dezelfde knoppenrij
    bovenaan.
  - Run-resultaat wordt onderaan getoond, **onder** het preview-paneel,
    in een eigen `QGroupBox` ("Analyseresultaat") met:
    - statuslabel (NL-tekst uit `messages.py`)
    - samenvattingsregel
    - drie value-rijen voor de kerncijfers (`QFormLayout`)

- **Reset-gedrag run-paneel** (`last_run = None` + visueel leeg):
  - bij wijziging van het pad-input,
  - bij start van een nieuwe validate-run,
  - bij start van een nieuwe analytische run.

- **Foutpaden run** (deze slice):
  - `RUN_PRECONDITION_NOT_MET`: project of geldige validate-status
    ontbreekt op het moment van aanroep.
  - `RUN_INTERNAL_ERROR`: onverwachte exception uit
    `run_incremental_analysis`.
  - Bewust **niet** in scope: aparte `RUN_PROCESS_FAILURE` voor
    `BrokenProcessPool` (parallel-pad komt later).

- **Vocabulaire / messages-module**:
  - Alle nieuwe NL-strings (knoplabel "Run analyse", statuslabels,
    kerncijfer-labels, foutdialog-teksten) komen in
    `rcm_desktop/messages.py`.
  - Termen: **"faalmomenten"** (niet "falingen"),
    **"niet-beschikbaarheid"** (niet "onbeschikbaarheid").

- **Architectuurregels**:
  - Views importeren uitsluitend uit `rcm_desktop.adapter` en `rcm_desktop.
    messages` (en typing van `rcm_core` waar nodig).
  - Adapter blijft de enige plek met run-orchestratielogica; geen
    Qt-imports in `rcm_core`.

- **Issue-split** (vertikaal TDD):
  - **Issue 09** — Pure `run_service` + `RunResult`-contract + `AppState`-
    uitbreidingen voor `last_project` en `last_run` (geen Qt-UI).
    Inclusief unit-tests met mock op `run_incremental_analysis`.
  - **Issue 10** — `RunRunner` + Run-knop in window + result-paneel +
    reset-gedrag + Qt-signaaltest + view-rendertest.

## Testing decisions

- **Goede tests**: dekken extern gedrag (input → output, signaalflow,
  reset-gedrag), niet intern Qt-mechanisme of widget-internals.

- **Pure unit-tests** op `run_service.run`:
  - happy path (mock op `rcm_core.incremental_run.run_incremental_analysis`
    levert een vooraf samengestelde `IncrementalRunResult`):
    `RunResult.status == "done"` en de drie metrics worden correct
    berekend uit de FM-results.
  - precondition-foutpad: aanroep zonder valide project ⇒
    `RUN_PRECONDITION_NOT_MET`.
  - interne fout: mock werpt exception ⇒ `RUN_INTERNAL_ERROR`.
  - mode-parameter: bij `full_recompute=True` wordt de juiste kwarg aan
    de kern doorgegeven.

- **Adapter-runner Qt-tests** (analoog aan `test_desktop_qt_flow.py`):
  - `RunRunner` emit `state_changed` (`busy` → `idle`) en `result_ready`
    bij happy path.
  - Re-entrancy-guard: tweede `start()` tijdens lopende run wordt
    afgewezen (`False`), eerste run gaat door.
  - Bij interne fout in service ontvangt UI een `RunResult` met
    `status == "error"` en `RUN_INTERNAL_ERROR`.

- **AppState-tests**:
  - `last_project` + `project_changed` werken onafhankelijk van bestaande
    `last_result`/`last_preview`.
  - `last_run` + `run_changed` worden gezet/leeg via dezelfde set-pattern.

- **View-rendertests** (Qt, met `pytest.importorskip("PySide6")`):
  - Run-knop is disabled bij start (geen `last_result`/`last_project`).
  - Na simulatie van geldige validate + project: Run-knop is enabled.
  - Na simulatie van `run_changed` met `done`-result: cijfers en status
    staan in het paneel.
  - Bij start van een nieuwe validate-/run-actie wordt het run-paneel
    eerst leeg.

- **Prior art**:
  - `tests/test_desktop_validate_service.py` (pure adapter-mapping).
  - `tests/test_desktop_preview_service.py` (pure transformatietests).
  - `tests/test_desktop_qt_flow.py` (signaalflow + view-rendering +
    `pytest.importorskip("PySide6")`-skip-strategie).

- **Regressiegate**: volledige `python -m pytest` blijft groen, inclusief
  de geporteerde kerntests en de slice-1/2-tests.

## Acceptance criteria

- [ ] Nieuwe `rcm_desktop.adapter.run_service` levert een `RunResult` met
      `status`, `summary`, `metrics`, en optioneel `error`.
- [ ] `run_service` roept `run_incremental_analysis(..., full_recompute=
      True, parallel=False)` aan en mapt het resultaat correct.
- [ ] `AppState` heeft `last_project` + `project_changed` en `last_run` +
      `run_changed`; bestaande `last_result`/`last_preview`-paden blijven
      gedragsgelijk.
- [ ] `RunRunner` bestaat en gebruikt status-codes `idle`, `busy`, `done`,
      `error`; tijdens `busy` wordt de Run-knop disabled en is een tweede
      `start()`-call defensief afgewezen.
- [ ] Run-knop is alleen enabled als `last_result.status in {valid,
      valid_with_warnings}` én `last_project is not None`.
- [ ] Run-resultaatpaneel wordt geleegd bij wijziging pad-input, nieuwe
      validate én nieuwe run.
- [ ] Run-resultaatpaneel toont na `done`: status-tekst, samenvatting,
      en de drie kerncijfers (`#FM-results`, totale **faalmomenten**
      lifecycle, totale kosten in euro), met labels uit `messages.py`.
- [ ] Run-foutpad toont bij `RUN_PRECONDITION_NOT_MET` en
      `RUN_INTERNAL_ERROR` een begrijpelijke NL-melding (inline status +
      modaal dialog), gebruikmakend van `ERROR_DIALOG_TITLE`.
- [ ] Alle nieuwe NL-strings staan gecentraliseerd in
      `rcm_desktop/messages.py`; vocabulaire **"faalmomenten"** en
      **"niet-beschikbaarheid"** wordt consistent gebruikt.
- [ ] Geen views importeren rechtstreeks uit `rcm_core` (behalve typing
      waar strikt nodig).
- [ ] Qt-tests skippen netjes met `pytest.importorskip("PySide6")` als
      `PySide6` niet beschikbaar is.
- [ ] `python -m pytest` is volledig groen.

## Out of scope

- Incrementele runs vanuit UI (bewust uitgesteld; mode-parameter blijft
  in contract).
- Parallel-toggle of `RUN_PROCESS_FAILURE`-mapping (komt later samen met
  parallel-pad).
- Cancel-knop voor een lopende run (engine biedt geen cancellation-hook;
  separate slice nodig).
- Volledige resultaattabellen, sortering, filtering of export
  (`FMResult`/`PBSResult` per rij in de UI komt later).
- Persistente opslag van `RunResult` in een sessiebestand.
- Killer/olifant-classificatie of andere RCM1-rangordening (bewust
  geschrapt; zie `CONTEXT.md`/`RCM2_REFERENTIE`).
- Voortgangsindicator (progress bar / fasen): `busy`-label volstaat.

## Comments

- **Risico — lange runtime**: op grote fixtures kan een `--full` run
  meetbaar duren. UI-feedback in deze slice beperkt zich tot een
  `busy`-statuslabel en disabled Run-knop. Een echte progress-UI vergt
  een aparte slice waarin de kern eerst hooks krijgt voor fasevoortgang.
- **Risico — parallel uit voor compatibiliteit**: `parallel=False` is
  conservatief gekozen om Qt + multiprocessing-interacties te vermijden.
  Wanneer parallel-pad nodig is, eerst de `RUN_PROCESS_FAILURE`-mapping
  invoeren en een UI-toggle toevoegen.
- **Risico — verouderd run-resultaat**: het run-paneel reset bij elke
  validate, run en pad-wijziging om misleidende stale-data te voorkomen.
  Dat is bewuster strikter dan strikt nodig en kan in latere iteraties
  worden versoepeld als gebruikers daar feedback op geven.
- **Cache-bijeffect**: hoewel we expliciet `full_recompute=True` draaien,
  schrijft de kern de cache bij. Dit is acceptabel: `--full` overschrijft
  de cache-snapshot eenduidig met het verse resultaat. Geen UI-actie
  nodig.
