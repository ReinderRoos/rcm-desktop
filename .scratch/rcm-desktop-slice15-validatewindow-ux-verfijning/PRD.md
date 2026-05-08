# PRD - RCM2 desktop slice 15 (ValidateWindow UX-verfijning: taakgericht, leesbaar, voorspelbaar)

**Status:** ready-for-agent  
**Versie:** 1.0  
**Triage-labels:** ready-for-agent

## Problem Statement

De ValidateWindow bevat functioneel de juiste bouwstenen (validate, run, compare,
faalwijzen-edit, LTAP what-if), maar de gebruikerservaring is nog relatief druk en
uniform in visuele nadruk. Daardoor:

- kost het meer tijd om de juiste actie op het juiste moment te vinden;
- is de betekenis van knoppen en statussen niet altijd direct intuïtief;
- ontstaan sneller bedienfouten bij LTAP-bundelen en contextwissels;
- wordt besluitvorming vertraagd door beperkte visuele hiërarchie in tekst, kleur en layout.

Voor Maintenance Engineers en Assetmanagers is een taakgerichte, rustiger
interactie noodzakelijk om sneller van data naar besluit te gaan.

## Solution

Verfijn de ValidateWindow naar een taakgerichte UX met duidelijke hiërarchie en
state-feedback, zonder kernlogica te wijzigen:

1. **Taakfasering in de UI** (invoer/validatie, analyse/resultaat, LTAP what-if).
2. **Heldere, consistente NL-terminologie** voor primaire acties en resetpaden.
3. **Verbeterde visuele hiërarchie** in typografie, spacing en paneelprioriteit.
4. **Consistente semantische kleurtoepassing** voor status en actie.
5. **Guided LTAP-interactie** (jaar -> selectie -> shift -> toepassen -> impact).
6. **Betere tabelscanbaarheid** voor PM/FM/PBS-overzichten.
7. **Expliciete state-indicatoren** (filtermodus, jaarcontext, what-if actief).
8. **Toegankelijkheidsbasis** (leesbaarheid, klikdoelen, keyboard-flow, tooltips).

De slice blijft binnen bestaande architectuurprincipes: UI-gedrag in de viewlaag,
domeinlogica in adapter/core onaangetast.

## User Stories

1. Als Maintenance Engineer wil ik per taakfase alleen relevante panelen zien, zodat ik focus houd.
2. Als Maintenance Engineer wil ik snel kunnen wisselen tussen fases, zodat ik geen tijd verlies.
3. Als gebruiker wil ik dat primaire acties duidelijk gelabeld zijn in natuurlijke taal, zodat ik minder hoef te interpreteren.
4. Als gebruiker wil ik dat technische termen alleen zichtbaar zijn waar functioneel nodig, zodat de UI rustiger wordt.
5. Als gebruiker wil ik dat reset-acties ondubbelzinnig benoemd zijn, zodat ik geen verkeerde reset uitvoer.
6. Als gebruiker wil ik dat koppen, kernwaarden en detailteksten visueel verschillen, zodat ik sneller scan.
7. Als gebruiker wil ik voldoende witruimte tussen blokken, zodat secties niet in elkaar overlopen.
8. Als gebruiker wil ik dat numerieke data in tabellen consequent uitgelijnd is, zodat vergelijken eenvoudiger is.
9. Als gebruiker wil ik dat statuskleuren consistent semantisch zijn, zodat fout/waarschuwing/succes direct herkenbaar is.
10. Als gebruiker wil ik dat chartreeksen duidelijk contrasteren, zodat baseline en what-if niet verward raken.
11. Als gebruiker wil ik dat LTAP-stappen impliciet worden geleid, zodat bundelen minder foutgevoelig wordt.
12. Als gebruiker wil ik dat "bundel toepassen" alleen actief is bij geldige selectie, zodat fouten preventief worden voorkomen.
13. Als gebruiker wil ik live zien hoeveel taken geselecteerd zijn, zodat ik zeker weet waarop de bundel werkt.
14. Als gebruiker wil ik de actieve filtermodus duidelijk zien, zodat contextwissels begrijpelijk blijven.
15. Als gebruiker wil ik actieve jaarcontext expliciet zien, zodat detailtabel en chart logisch aanvoelen.
16. Als gebruiker wil ik herkennen of what-if actief is, zodat ik baseline en overlay niet door elkaar haal.
17. Als Assetmanager wil ik kern-KPI's prominenter dan detailwaarden zien, zodat beslissingen sneller te nemen zijn.
18. Als Assetmanager wil ik minder visuele ruis in standaardweergave, zodat bespreking met stakeholders rustiger verloopt.
19. Als gebruiker wil ik consistente knopgroottes en klikdoelen, zodat bediening comfortabel blijft.
20. Als gebruiker wil ik keyboard-navigatie voor LTAP-kerntaken, zodat ik efficiënter kan werken.
21. Als gebruiker wil ik tooltips op specialistische termen (SVO/WET/TG), zodat betekenis direct duidelijk is.
22. Als tester wil ik UX-contracten op observeerbaar gedrag toetsen, zodat refactors veilig blijven.
23. Als tester wil ik regressies op bestaande LTAP- en resultatenflows voorkomen, zodat eerdere slices stabiel blijven.
24. Als productowner wil ik de UX-verfijning in dunne AFK-slices kunnen uitrollen, zodat elk deel reviewbaar blijft.
25. Als productowner wil ik dat functionele output gelijk blijft terwijl bedienbaarheid verbetert, zodat scope beheersbaar blijft.

## Implementation Decisions

- **Scopegrens:** deze slice is UX- en interactieverfijning van bestaande ValidateWindow; geen nieuw venster, geen nieuw domeinmodel.
- **Architectuurgrens:** UI-kern-decoupling blijft leidend; wijzigingen zitten primair in viewlaag en eventueel adapter-presentatie, niet in `rcm_core`-logica.
- **Taakmodelbeslissing:** UI wordt gepositioneerd rond drie taakfases (validate, analyse, LTAP what-if) met duidelijke paneelprioriteit.
- **Terminologiebeslissing:** actie- en statuslabels worden geharmoniseerd naar eenduidige NL-werkwoorden en domeintermen.
- **Resetbeslissing:** reset van layout en reset van LTAP-baseline krijgen expliciet verschillende benamingen en context.
- **Hiërarchiebeslissing:** vaste tekstniveaus (paneeltitel, KPI-kernwaarde, detailtekst) en consistente spacing-richtlijnen in de window.
- **Kleurbeslissing:** semantische kleurset (succes/waarschuwing/fout/primair accent) als herbruikbaar UI-contract.
- **LTAP-flowbeslissing:** in-paneel microflow wordt expliciet gemaakt via statevolle controls en duidelijke feedbackmomenten.
- **Preventieve validatie:** bundelactie blijft selectie-gedreven en wordt aanvullend in de UI ondersteund met enable/disable en selectiestatus.
- **State-signalen:** actieve filter, jaarselectie en what-if-status worden zichtbaar als compacte contextindicatoren.
- **Tabelcontract:** scanbaarheid verbeteren via uitlijning, rijhoogte, kolomprioriteit en consistente renderregels.
- **Toegankelijkheidsbeslissing:** minimale leesbaarheid/klikdoelen en keyboardtoegankelijkheid als basis, zonder volledige redesign.
- **Deep module kans 1:** kleine presentatie-state module voor UX-statuslabels/badges (filter, jaar, overlay, selectiecount).
- **Deep module kans 2:** gecentraliseerde UI-tekstcatalogus met semantische actiebenamingen en tooltipteksten.
- **Uitrolstrategie:** iteratieve verticale slices met directe demo-waarde, in volgorde: taal + hiërarchie -> LTAP guidance -> toegankelijkheid/polish.

## Testing Decisions

- **Wat een goede test is:** test zichtbare gebruikersuitkomst (labels, zichtbaarheid, enabled-state, statusfeedback, interactieresultaat), niet interne widgetimplementatie.
- **Te testen modules/gebieden:**
  - ValidateWindow-interactie rond fasegerichte panelgedrag;
  - LTAP guided controls (selectie-feedback, knop-state, contextbadges);
  - tekstcontracten en semantische statusweergave;
  - regressie op bestaande validate/run/compare/LTAP-kernflow.
- **Prior art:** bestaande pytest-qt flowtests voor panel visibility, LTAP-selectie/bundeling, en runresultaatweergave.
- **Kwaliteitsgate:**
  1. geen functionele regressie in bestaande LTAP- en resultatenflows;
  2. nieuwe UX-contracttests slagen voor teksten/status/enablement;
  3. fallbackgedrag (bijv. zonder QtCharts) blijft bruikbaar en consistent.
- **Testfocus:** eerst high-impact gedrag (action discoverability, LTAP foutpreventie, state-duidelijkheid), daarna cosmetische details met lage regressiekans.

## Out of Scope

- Nieuwe analysemodellen, KPI-formules of aanpassingen in `rcm_core`-berekeningen.
- Volledige visuele redesign of thema-engine.
- Nieuwe multi-window docking-architectuur.
- Internationale meertaligheid buiten huidige NL-hoofdtaal.
- Performancebenchmark-SLA's op pixel- of millisecondenniveau.
- Functionele uitbreiding buiten ValidateWindow/gerelateerde bestaande panelen.

## Further Notes

- Deze slice optimaliseert mens-machine interactie op bestaande functionaliteit; het doel is sneller en zekerder beslissen, niet extra rekenfunctionaliteit.
- LTAP-bundeling blijft een risicovolle interactie; UX moet hier primair op foutpreventie en contextduidelijkheid sturen.
- Geadviseerde implementatievolgorde:
  1) terminologie + hiërarchie,
  2) LTAP guided flow + statebadges,
  3) tabelscanbaarheid + toegankelijkheidspolish.
