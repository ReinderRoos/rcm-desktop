# PRD — RCM2 desktop slice 19 (respons na project inladen)

**Status:** done  
**Versie:** 1.0  
**Triage-labels:** done

## Problem Statement

Na **Project inladen** ervaart de gebruiker het proces als **zeer traag** of het venster **hangt** even. Dat komt vaak niet primair door het JSON-bestand zelf (parsen gebeurt op een workerthread), maar door **zwaar werk op de UI-thread** direct daarna: onder andere het vullen van **grote tabellen**, **`resizeRowsToContents`** bij ingeschakelde **tekstomloop**, en het tonen van **alle LTAP-detailregels over alle jaren** tegelijk. Daardoor wordt het primaire doel — snel verder kunnen werken na een geldige load — ondermijnd.

## Solution

Optimaliseer voor **minimaal blokkeren van de hoofd-UI** tot een **bruikbare basistoestand** na geslaagde validatie:

1. **LTAP**: toon na load **standaard slechts één jaar** in de detailtabel (het **vroegste** jaar in de huidige jaarlijst); het samengevoegde overzicht over **alle jaren** blijft beschikbaar via de **bestaande expliciete actie** daarvoor (geen automatische “alle jaren”-fill bij elke load).
2. **Tekstomloop / rijhoogtes**: behoud het gebruikersvoordeel van omloop, maar pas **`resizeRowsToContents`** niet blind toe op enorme roosters: **vaste drempels per view** in code; **boven de drempel** wordt automatische rijhoogte-update **overgeslagen** (documenteerbaar gedrag).
3. **Faalwijzen**: het paneel staat standaard verborgen — **koppel het Qt-tabelmodel en uitvoer zware tabel-layout pas** wanneer de gebruiker het **Faalwijzen-paneel voor het eerst zichtbaar** maakt. De **bewerkings-/bindlaag** naar het domain model blijft **direct na geldige load** actief zodat **analyse, opslaan en validatie** niet breken.
4. **Rendering**: waar nuttig mag **puur visueel zwaar werk** (zoals LTAP-grafiek of aanvullende kolomafhandeling) **één event-loop tik worden uitgesteld** (`QTimer.singleShot(0, …)`), zonder de geladen projectstaat te veranderen — zodat status en knoppen eerder reageren.

## User Stories

1. Als **analist** wil ik dat het venster na **Project inladen** **snel weer reageert**, zodat ik niet denk dat de applicatie vastloopt.
2. Als **analist** wil ik na inladen **direct** status en primaire acties kunnen gebruiken, zonder te wachten op zware tabellen die ik nog niet open.
3. Als **analist** wil ik **LTAP-details per jaar** kunnen bekijken zonder dat standaard **alle jaren tegelijk** als enorme tabel worden opgebouwd.
4. Als **analist** wil ik het **vroegste planningjaar** standaard zien na load, zodat ik een voorspelbaar startpunt heb.
5. Als **analist** wil ik **alle jaren in één detailoverzicht** nog steeds kunnen opvragen wanneer ik dat **bewust** kies.
6. Als **analist** wil ik **tekstomloop** kunnen laten aanstaan zonder dat **zeer grote** tabellen de UI minuten blokkeren.
7. Als **analist** wil ik bij **extreem grote** roosters nog steeds een **bruikbare** (evt. vaste) rijhoogte zien in plaats van een freeze.
8. Als **analist** die Faalwijzen bewerkt wil ik dat **bewerkingslogica en runs** werken **direct na load**, ook als ik het Faalwijzen-paneel nog niet heb geopend.
9. Als **analist** accepteer ik een **korte opbouwfase** de **eerste keer** dat ik het Faalwijzen-rooster open, als de rest van het venster daarvoor sneller bruikbaar is.
10. Als **maintainer** wil ik **duidelijke drempelconstanten** (per view) om gedrag te testen en te tunen.
11. Als **maintainer** wil ik regressietests op **LTAP-jaarselectie na load** en op **lazy Faalwijzen-grid**.
12. Als **product owner** wil ik dat **geen** wijziging aan het **domain model** of **JSON-schema** nodig is voor deze UX-winst.

## Implementation Decisions

- **ValidateWindow-orchestratie**: herschikken van werk dat nu synchronisch bij `project_changed` gebeurt — splitsen in **minimaal noodzakelijke staat** eerst, **zware views** daarna of bij eerste zichtbaarheid.
- **Faalwijzen**: scheiding tussen **service-/edit-reset direct na load** versus **`QTableView.setModel` + kolom/rij-layout** bij **eerste panel-visible** (via bestaande paneeltoggles / zichtbaarheidshooks).
- **LTAP**: na succesvolle sync geen automatische “alle jaren”-populate van de detailtabel; **default selectie = min(jaren)**; behoud bestaande gebruikersactie voor alle-jaren-weergave.
- **Tabelpresentatie-module**: uitbreiden met **drempelconstanten per datatable-type** en een kleine **policy-helper** (“mag `resizeRowsToContents`?”) die door de vensterlogica wordt gebruikt — één plek voor drempels, geen verspreide magic numbers.
- **Deferred render**: optioneel **één** `singleShot(0)` voor LTAP-grafiek en/of andere niet-kritische paints; geen ingewikkelde job-queue in deze slice.
- **Architectuur**: geen imports vanuit views naar `rcm_core` behalve typing-only (bestaand contract); adapter/UI-laag blijft eigenaar van Qt-timing.

## Testing Decisions

- Tests beschrijven **observeerbaar gedrag**: na load is LTAP-detail **één jaar** (rij-count / geselecteerd jaar-contract); Faalwijzen-model is **niet** gekoppeld aan de view tot paneel zichtbaar wordt (via signals of publieke vensterstatus waar nodig).
- Drempel-logica: unittests op de policy-helper (rijenaantal onder/boven drempel → wel/geen resize-aanroep).
- Prior art: bestaande `pytest` + PySide6-flowtests voor `ValidateWindow`, LTAP-toggle/selectie, paneel-zichtbaarheid.

## Out of Scope

- Versnellen van `json.load` / `RCMProject.from_dict` / kernvalidators zelf (tenzij afzonderlijke profiling daar bottleneck toont).
- Persistente gebruikersvoorkeur voor **laatst gekozen LTAP-jaar** (`QSettings`) — later mogelijk.
- Viewport-gebaseerde incrementele rijhoogtes — later mogelijk als drempels onvoldoende zijn.
- Waarschuwingsdialogen bij “alle jaren” bij extreme grootte — later mogelijk.

## Further Notes

- Drempeldefaults moeten op **representatieve klantprojecten** worden **gemeten** en zo nodig bijgesteld.
- Eerste opening Faalwijzen-paneel: verwacht **korte** warm-up; bijacceptatie vastgelegd in user stories.
- Issues: `issues/01.md`, `issues/02.md`, `issues/03.md` in deze map.
