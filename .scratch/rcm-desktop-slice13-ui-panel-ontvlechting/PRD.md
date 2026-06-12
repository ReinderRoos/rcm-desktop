# PRD — RCM2 desktop slice 13 (UI-panelen ontvlechten: op aanvraag + resizable)

**Status:** ready-for-agent  
**Versie:** 1.0  
**Triage-labels:** ready-for-agent

## Problem Statement

De huidige desktop-UI voelt te vol, waardoor gebruikers te weinig focus houden op
de actieve taak. In de praktijk leidt dit tot:

- te veel gelijktijdig zichtbare deelvensters;
- beperkte werkruimte voor het paneel dat op dat moment relevant is;
- hogere cognitieve belasting bij schakelen tussen validate/run/compare/LTAP.

Voor de Maintenance Engineer en Assetmanager is dit een rem op snelheid en
beslisbaarheid. De behoefte is een interface waarbij panelen op aanvraag kunnen
worden geopend en/of in grootte kunnen worden aangepast, zonder verlies van
bestaande functionaliteit.

## Solution

Implementeer een hybride paneelmodel dat de UI ontlast:

1. **Kernpanelen resizable** via splitters.
2. **Secundaire panelen op aanvraag** via compacte toggles (toon/verberg).
3. **Gebalanceerde standaardlayout** bij opstarten.
4. **Automatische keuze van actief resultatenpaneel** met handmatige override.
5. **Persistente layout- en zichtbaarheidsvoorkeuren** tussen sessies.
6. **Harde recovery** met “Reset layout” naar balanced defaults.

Het model moet per fase AFK uitrolbaar zijn en na elke fase zelfstandig
verifieerbaar blijven via bestaande en uitgebreide pytest-qt flowtests.

## User Stories

1. Als Maintenance Engineer wil ik meer ruimte voor mijn actieve paneel, zodat ik sneller kan analyseren.
2. Als Maintenance Engineer wil ik resultatenpanelen in hoogte kunnen aanpassen, zodat ik focus kan leggen op wat nu relevant is.
3. Als Maintenance Engineer wil ik niet-relevante panelen kunnen verbergen, zodat de UI rustiger wordt.
4. Als Maintenance Engineer wil ik verborgen panelen op aanvraag kunnen openen, zodat informatie niet verloren gaat.
5. Als Maintenance Engineer wil ik dat LTAP als kernpaneel zichtbaar en resizable blijft, zodat planning centraal blijft.
6. Als Maintenance Engineer wil ik slechts één actief resultatenpaneel tegelijk als kern zien, zodat ik geen concurrerende visuele ruis heb.
7. Als Assetmanager wil ik snel tussen resultatencontexten kunnen wisselen, zodat ik beslissingen op meerdere KPI-hoeken kan toetsen.
8. Als Assetmanager wil ik dat de UI een gebalanceerde default heeft, zodat ik niet telkens handmatig hoef te herindelen.
9. Als gebruiker wil ik dat de UI slim een actief resultatenpaneel kiest, zodat ik minder handmatig hoef te klikken.
10. Als gebruiker wil ik een handmatige override op die keuze, zodat ik controle houd wanneer de automatische keuze niet past.
11. Als gebruiker wil ik dat die handmatige keuze “sticky” blijft zolang de context niet wezenlijk verandert, zodat de UI niet springerig voelt.
12. Als gebruiker wil ik dat panelen zichtbaar/verborgen consistent reageren op workflow-events, zodat gedrag voorspelbaar blijft.
13. Als gebruiker wil ik dat het verbergen van panelen geen functionele acties uitschakelt, zodat de workflow compleet blijft.
14. Als gebruiker wil ik dat hidden panelen geen onnodige lege ruimte reserveren, zodat beschikbare ruimte echt wordt benut.
15. Als gebruiker wil ik dat panel-layout bij herstart wordt hersteld, zodat ik mijn werkomgeving niet telkens opnieuw hoef in te richten.
16. Als gebruiker wil ik een “Reset layout”-actie, zodat ik altijd kan herstellen van een kapotte of onhandige indeling.
17. Als gebruiker wil ik dat reset terugzet naar een gebalanceerde baseline, zodat herstel direct bruikbaar is.
18. Als gebruiker wil ik dat toggles duidelijk aangeven welke panelen open zijn, zodat status direct zichtbaar is.
19. Als gebruiker wil ik dat toggles en splitters ook tijdens actieve run/compare-ervaring bruikbaar blijven, zodat ik niet vastloop.
20. Als gebruiker wil ik geen merkbare lag bij tonen/verbergen of resizen in normale projecten, zodat interactie prettig blijft.
21. Als ontwikkelaar wil ik zichtbaarheid- en layoutbeslissingen centraliseren, zodat regressierisico bij UI-wijzigingen afneemt.
22. Als ontwikkelaar wil ik paneelmetadata expliciet modelleren, zodat gedrag per paneel declaratief en testbaar wordt.
23. Als ontwikkelaar wil ik auto-selectie en override-logica los van Qt-widgetdetails kunnen testen, zodat logica stabiel blijft.
24. Als tester wil ik gedragstests op publieke UI-acties, zodat tests refactorbestendig zijn.
25. Als tester wil ik flowtests voor panel-toggles, splittergedrag en state-transities, zodat ontvlechting aantoonbaar veilig is.
26. Als tester wil ik tests voor persist/restore en reset layout, zodat herstelpaden geborgd zijn.
27. Als productowner wil ik de uitrol in kleine AFK-fases, zodat elke stap reviewbaar en rollback-vriendelijk blijft.
28. Als productowner wil ik dat elke fase zelfstandig demo-baar is, zodat voortgang zichtbaar blijft.

## Implementation Decisions

- **Bedienmodel:** hybride (splitter + op-aanvraag panelen).
- **Standaarddichtheid:** balanced.
- **Succesprioriteit:** meer werkruimte voor actieve taak > focusduidelijkheid > minder standaard zichtbare panelen.
- **Kernpanelen:** LTAP + één actief resultatenpaneel als resizable kern.
- **Secundaire panelen:** preview, faalwijzen, compare en niet-actieve resultatencontext op aanvraag.
- **Actief resultatenpaneel:** automatische selectie op context, met handmatige override.
- **Override-policy:** gebruikerkeuze blijft sticky totdat context wezenlijk wijzigt.
- **Recovery-policy:** expliciete “Reset layout” zet zichtbaarheid en splitterverhoudingen terug naar balanced defaults.
- **State-policy:** paneelzichtbaarheid en splittergroottes worden persistent opgeslagen tussen sessies.
- **Performance-policy:** geen harde millisecond-SLA in deze slice; wel eis van geen merkbare lag in normale projecten.
- **Architectuur:** centraliseer paneelorchestratie in de desktop-viewlaag; geen impact op `rcm_core`.
- **Deep module kans 1:** panel-state orchestrator met kleine interface voor visibility/profile/override-regels.
- **Deep module kans 2:** layout-preferences service voor persist/restore/reset van UI-layoutstate.
- **Uitrolstrategie:** AFK in afzonderlijke fases, elk met eigen green test-gate.

## Testing Decisions

- **Wat een goede test is:** test observeerbaar gedrag via publieke UI-interactie (toggle, resize, paneelkeuze, reset), niet interne widget-implementatie.
- **Te testen modules/gebieden:**
  - paneelorchestratie (zichtbaarheid/profielen/override);
  - layoutpersistency en resetgedrag;
  - end-to-end validate-window flow bij dynamische paneelstaten.
- **Verplichte testgedragingen:**
  1. secundaire panelen zijn op aanvraag toonbaar/verbergbaar;
  2. kernpanelen zijn resizable en blijven bruikbaar in workflow;
  3. actief resultatenpaneel volgt auto-selectie met handmatige override;
  4. persist/restore werkt over sessies;
  5. reset layout herstelt balanced baseline.
- **Prior art:** bestaande pytest-qt flows rond panel visibility, LTAP-flow en run/compare statuswissels.
- **Kwaliteitsgate:** elke fase sluit af met regressietests op relevante UI-flow en bestaande kritieke tests.

## Out of Scope

- Herontwerp van domeinlogica of berekeningen in `rcm_core`.
- Nieuwe analysemethoden of KPI-definities.
- Grote visuele redesign buiten paneel-ontvlechting (styling/theming).
- Harde performancebenchmarks met strikte timing-SLA’s.
- Multi-window docking-architectuur.
- Portfolioniveau dashboards.

## Further Notes

- Deze slice is een UX-structuurverbetering: functionele scope blijft gelijk, bedienbaarheid verbetert.
- Gefaseerde AFK-uitrol minimaliseert regressierisico in een UI-gevoelig gebied.
- Sticky override + reset layout zijn cruciaal om “springerig” of “vastgelopen” UI-ervaring te voorkomen.
