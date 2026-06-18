# PRD — RCM2 desktop slice 2 (project-preview na validate)

**Status:** ready-for-agent
**Versie:** 1.0
**Triage-labels:** zie `../../AGENTS.md`

## Bron / context

- `../../README.md`
- `../../AGENTS.md`
- `../../CONTEXT.md`
- `../../../rcm/.scratch/rcm2-restart-reference/RCM2_REFERENTIE.md`
- Voorgaande slice: `../rcm-desktop-slice1-validate/PRD.md`
- Design-interview (vastgelegde beslissingen): zie sectie *Implementation decisions*.

## Problem statement

Slice 1 levert een werkende validate-flow met status, samenvatting en details,
maar de gebruiker krijgt **geen inhoudelijke bevestiging** dat het juiste
projectbestand is geladen. Bij een uitkomst `Geldig` of
`Geldig met waarschuwingen` is op het scherm niet zichtbaar of er één faalwijze
of duizend in het project zit, of welke. Daardoor blijft de feedbackloop ondiep
en is de flow nog niet bruikbaar als zelfstandige desktoptool.

## Solution

Voeg na een geslaagde validate een minimale **project-preview** toe die direct
laat zien dat het bestand correct is ingelezen:

1. **Tellerkaart** met `#PBS-items`, `#functies`, `#faalwijzen`, `#PM-taken`
   uit het geladen `RCMProject`.
2. **Top-5 faalwijzen** in invoervolgorde uit het project, met `fm_id` en
   `faalwijze_omschrijving`.
3. **Aparte preview-service in de adapter**, los van validate, zodat het
   contract zuiver blijft en preview later herbruikbaar is.
4. **Eén disk-read per run**: validate deelt het geladen `RCMProject` met de
   preview, zodat er geen race-condities of dubbele I/O ontstaan.
5. **Asynchrone uitvoering** op de bestaande validate-worker; UI blijft
   responsief.

## User stories

1. Als analist wil ik direct na validate zien hoeveel PBS-items, functies,
   faalwijzen en PM-taken er in mijn project zitten, zodat ik in één oogopslag
   bevestig dat het juiste bestand is geladen.
2. Als analist wil ik de eerste vijf faalwijzen (id + omschrijving) zien,
   zodat ik snel herken of dit het verwachte project is.
3. Als analist wil ik dat de preview alleen verschijnt als het project
   structureel geldig is (`valid` of `valid_with_warnings`), zodat ik bij
   `invalid` of `error` niet word afgeleid door mogelijk misleidende
   gedeeltelijke content.
4. Als analist wil ik dat de preview bij elke nieuwe validate-run vervangen
   wordt door verse data, zodat ik geen oude inhoud per ongeluk lees.
5. Als analist wil ik dat een leeg project (0 faalwijzen) expliciet zichtbaar
   is via een placeholder, zodat ik niet hoef te twijfelen of er iets misging.
6. Als analist wil ik dat de UI tijdens validate + preview-bouw responsief
   blijft, zodat de app niet bevriest tijdens het laden.
7. Als ontwikkelaar wil ik een pure `preview_service.build(project)`-functie
   die eenvoudig in unit-tests is te dekken, zodat regressies in tellingen of
   top-5 vroeg zichtbaar worden.
8. Als ontwikkelaar wil ik dat preview-state apart wordt bijgehouden in
   `AppState` (eigen veld + signaal), zodat validate- en preview-contracten
   onafhankelijk evolueren.
9. Als ontwikkelaar wil ik dat de adapter zowel het `ValidateResult` als de
   gebouwde `ProjectPreview` in één signaalflow naar de UI brengt, zodat de
   view geen extra coördinatielogica nodig heeft.
10. Als reviewer wil ik dat de preview-architectuur de UI/kern-decoupling
    respecteert (views praten alleen via `rcm_desktop.adapter`), zodat de
    architectuurregels uit `AGENTS.md` blijven gelden.

## Implementation decisions

- **Aparte preview-service in `rcm_desktop.adapter`**.
  De preview is een eigen domeinconcept, niet een uitbreiding van het
  validate-contract. Validate blijft single-purpose (status/summary/details).

- **Pure transformatie zonder I/O**: `preview_service.build(project) ->
  ProjectPreview` is een pure functie over een geladen `RCMProject`. Geen disk-
  of netwerk-zijeffecten in preview.

- **API-aanpassing van `validate_service.run`**:
  - Retourtype wordt uitgebreid met het optioneel geladen `RCMProject`.
  - Bij geslaagd laden geeft de service zowel het `ValidateResult` als het
    `RCMProject` terug; bij `error`/parse-fouten is het project `None`.
  - Dit is bewust een breaking change t.o.v. slice 1 en vereist meeneem-update
    van de bestaande `ValidateRunner` en bijbehorende tests.

- **Trigger-regel preview**: preview wordt alleen gebouwd als
  `ValidateResult.status` één van `{valid, valid_with_warnings}` is. Bij
  `invalid`/`error` is `last_preview` leeg.

- **Threading-strategie**:
  - Preview-bouw gebeurt op de bestaande validate-worker-thread, **na**
    validate en **voor** de finale signaalflow naar de UI.
  - Eén signaalpaar (`result_ready` + nieuw `preview_ready`) wordt vanaf de
    runner geëmit; UI-thread doet enkel rendering.

- **AppState-uitbreiding**:
  - Nieuw veld `last_preview: ProjectPreview | None`.
  - Nieuw signaal `preview_changed(ProjectPreview | None)`.
  - `last_result` blijft ongemoeid; preview is een tweede, onafhankelijke
    state.

- **`ProjectPreview`-contract** (adapter-niveau dataclass):
  - `counts`: numerieke tellingen voor `pbs_items`, `functies`, `faalwijzes`,
    `pm_tasks`.
  - `top_faalwijzes`: lijst van maximaal 5 items, elk met `fm_id` en
    `faalwijze_omschrijving`, in invoervolgorde uit het project.
  - Geen analytische ranking (geen MTTF-, kosten- of severity-sortering).

- **UI-plaatsing**:
  - Preview-paneel staat **onder** de samenvatting en **boven** het
    details-paneel in de bestaande validate-window.
  - Layout: één `QGroupBox` met daarbinnen een `QFormLayout` voor de tellingen
    en een `QListWidget` voor de top-5.

- **Lege-state UX**:
  - Bij 0 faalwijzen blijven tellingen + listwidget staan; de lijst toont een
    enkele placeholderregel “(geen faalwijzen)”.
  - Bij `invalid`/`error` wordt het hele preview-paneel ofwel verborgen ofwel
    leeggemaakt (analoog aan de bestaande summary/details-reset).

- **Reset-gedrag bij nieuwe run**:
  - `_clear_result_view` wordt uitgebreid zodat ook de preview-secties leeg
    gaan bij start van elke run.
  - Pas na het succesvol ontvangen van `preview_ready` worden tellingen en
    top-5 ingevuld.

- **i18n / messages-module**:
  - Alle nieuwe NL-strings (kop tellerkaart, koppen tellingen, kop top-5,
    placeholder leeg) komen in `rcm_desktop/messages.py`, consistent met
    slice 1.

- **Issue-split**:
  - **Issue 07** — Pure `preview_service` + adaptercontract `ProjectPreview`
    + unit-tests, plus minimale aanpassing van `validate_service` zodat het
    geladen project beschikbaar wordt.
  - **Issue 08** — Runner/`AppState`/view-integratie + Qt-signaaltest +
    view-rendertest.

## Testing decisions

- **Goede tests**: dekken extern gedrag (input → output, signaalflow), niet
  intern Qt-mechanisme of widget-internals.
- **Pure unit-tests** op `preview_service.build`:
  - happy path met realistische `RCMProject`-stub of fixture.
  - 0-faalwijzen edge case.
  - >5 faalwijzen → exact 5 in invoervolgorde, geen herordening.
  - tellingen kloppen met de inhoud van het project.
- **Adapter-runner Qt-test** (analoog aan slice-1 `test_desktop_qt_flow.py`):
  - bij `valid` en `valid_with_warnings` worden zowel `result_ready` als
    `preview_ready` geëmit.
  - bij `invalid` en `error` wordt `preview_ready` geëmit met `None` (of niet
    geëmit; gedrag wordt vastgelegd in test).
  - re-entrancy-guard van de runner blijft werken.
- **View-rendertest** (Qt, met `pytest.importorskip("PySide6")` net als slice 1):
  - na `preview_changed`-signaal staan tellingen in het formulier.
  - top-5 lijst bevat exact de verwachte regels.
  - bij start van een nieuwe run worden tellingen + lijst eerst leeg.
- **Prior art**:
  - `tests/test_desktop_validate_service.py` (pure adapter-mapping).
  - `tests/test_desktop_qt_flow.py` (signaalflow + view-rendering).
- **Regressiegate**: volledige `python -m pytest` blijft groen, inclusief de
  geporteerde kerntests.

## Acceptance criteria

- [ ] `validate_service.run` retourneert zowel `ValidateResult` als (optioneel)
      het geladen `RCMProject`, met meeverhuisde tests voor de bestaande
      validate-mappings.
- [ ] `preview_service.build(project)` levert een `ProjectPreview` met correcte
      tellingen en top-5 in invoervolgorde, gedekt door pure unit-tests.
- [ ] `AppState` heeft `last_preview` en `preview_changed`; `last_result` en
      `result_changed` blijven onveranderd qua gedrag.
- [ ] `ValidateRunner` emit `preview_ready` op de juiste momenten (alleen bij
      `valid`/`valid_with_warnings`), gedekt door een Qt-signaaltest.
- [ ] Validate-window toont onder de samenvatting een tellerkaart en top-5,
      die bij elke nieuwe run eerst leeg gaan en daarna gevuld worden.
- [ ] Bij 0 faalwijzen toont de top-5 een placeholderregel “(geen
      faalwijzen)”; tellingen blijven zichtbaar.
- [ ] Bij `invalid`/`error` is geen preview-content zichtbaar.
- [ ] Alle nieuwe NL-strings staan in `rcm_desktop/messages.py`.
- [ ] `python -m pytest` is volledig groen; Qt-tests skippen netjes als
      `PySide6` ontbreekt.

## Out of scope

- Analytische ranking van faalwijzen (op MTTF, kosten, severity, etc.).
- Volledige domeintabellen met sortering, filtering of export.
- Persistente preview-state op disk; preview leeft alleen in de huidige
  sessie.
- Ranking/markering van killer/olifant-classificaties — bewust geschrapt
  (zie `CONTEXT.md`/RCM2_REFERENTIE).
- Preview voor de uitvoer van `run --full`; deze slice raakt alleen validate.
- Caching van geladen `RCMProject` over meerdere runs (bijv. op `path+mtime`).

## Comments

- **Risico — top-5 zonder ranking**: invoervolgorde is duidelijk maar
  inhoudelijk arbitrair. Migratie naar betekenisvolle ranking (MTTF, cost) is
  later eenvoudig: alleen sorteer-stap in `preview_service` aanpassen,
  contract blijft gelijk.
- **Risico — lange omschrijvingen**: `faalwijze_omschrijving` kan layout
  uitrekken; eliding/word-wrap is bewust uitgesteld tot er feedback uit
  gebruik komt.
- **Defensieve afhandeling van `preview_service.build`**: in principe pure
  data-transformatie zonder fout-paden, maar runner moet defensief omgaan met
  een onverwachte exception (resultaat als `None`-preview + log).
- **API-breaking change**: validate-runner en tests uit slice 1 moeten in
  issue 07 mee worden bijgewerkt; dit is geen toevoeging maar een uitbreiding
  van het bestaande contract.
