# PRD — RCM2 desktop slice 12 (LTAP als LCC-achtige tijdgrafiek met klikbare jaardetails)

**Status:** ready-for-agent  
**Versie:** 1.0  
**Triage-labels:** ready-for-agent

## Problem Statement

De huidige LTAP-functionaliteit biedt wel een tabel met jaarregels en bundel-simulatie,
maar nog geen visuele tijdas zoals gebruikers die uit een LCC-grafiek kennen.
Daardoor kost het meer cognitieve moeite om kostenpieken, kostenverschuivingen en
jaareffecten van bundelacties snel te begrijpen.

Gebruikers willen per lifecycle-jaar direct de totale onderhoudskosten kunnen zien en
bij klik op een jaar onmiddellijk de uit te voeren werkzaamheden met bijbehorende kosten
kunnen inzien. Zonder die interactie blijft de LTAP minder beslisgericht dan gewenst.

## Solution

Voeg een LCC-achtige LTAP-tijdgrafiek toe op basis van **PM-kosten per jaar** met
interactieve selectie:

1. Een staafdiagram per lifecycle-jaar met twee reeksen:
   - baseline PM-kosten;
   - what-if PM-kosten.
2. Klik op een jaar activeert een jaarfilter.
3. Onder de grafiek verschijnt een detailtabel met **what-if werkzaamheden** voor dat
   geselecteerde jaar.
4. Boven de detailtabel staat een compacte jaar-samenvatting met:
   - baseline jaarbedrag;
   - what-if jaarbedrag;
   - delta.
5. Actie “Toon alle jaren” heft het jaarfilter op en herstelt totaaloverzicht.
6. Bij bundeltoepassing blijft geselecteerd jaar behouden (indien binnen range).
7. Bij reset keert selectie terug naar totaaloverzicht.
8. Als een jaar geen werkzaamheden bevat, wordt een expliciete empty-state getoond.
9. Als chartcomponent niet beschikbaar is, degradeert LTAP naar lijstselectie met
   dezelfde detailtabel en interactiegedrag.

## User Stories

1. Als Maintenance Engineer wil ik PM-kosten per lifecycle-jaar als staafdiagram zien, zodat ik kostenpieken sneller herken.
2. Als Maintenance Engineer wil ik baseline en what-if per jaar naast elkaar zien, zodat ik bundeleffecten direct kan vergelijken.
3. Als Maintenance Engineer wil ik op een jaar kunnen klikken, zodat ik direct de werkzaamheden van dat jaar zie.
4. Als Maintenance Engineer wil ik in de detailtabel de what-if werkzaamheden met kosten zien, zodat ik uitvoerbaarheid concreet kan beoordelen.
5. Als Maintenance Engineer wil ik aantallen uitvoeringen per taak in de detailtabel zien, zodat ik werkbelasting juist interpreteer.
6. Als Maintenance Engineer wil ik ook downtime per taak zien, zodat planningsimpact op beschikbaarheid zichtbaar blijft.
7. Als gebruiker wil ik boven de tabel baseline/what-if/delta voor het geselecteerde jaar zien, zodat ik niet hoef te rekenen.
8. Als gebruiker wil ik een duidelijke “Toon alle jaren”-actie, zodat ik snel terug kan naar totaaloverzicht.
9. Als gebruiker wil ik dat klik op een jaar een harde filter is, zodat het gedrag voorspelbaar is.
10. Als gebruiker wil ik dat de geselecteerde jaarcontext behouden blijft na een bundelactie, zodat itereren sneller gaat.
11. Als gebruiker wil ik dat reset naar baseline ook de selectie reset, zodat de UI-consistentie behouden blijft.
12. Als gebruiker wil ik bij jaren zonder werkzaamheden een expliciete melding zien, zodat ik weet dat de selectie gelukt is.
13. Als Assetmanager wil ik kostenverschuiving tussen baseline en what-if visueel zien, zodat budgetimpact per jaar inzichtelijk is.
14. Als Assetmanager wil ik per jaar de delta snel kunnen interpreteren, zodat besluitvorming over bundeling versnelt.
15. Als gebruiker wil ik dat de LTAP in deze slice PM-only blijft, zodat scope en betekenis helder zijn.
16. Als gebruiker wil ik dat SVO/WET zichtbaar blijven in details, zodat governance-taken niet verdwijnen.
17. Als gebruiker wil ik dat niet-verschuifbare taken in detail herkenbaar zijn, zodat ik selectie-fouten voorkom.
18. Als gebruiker wil ik dat grafiek en detailtabel synchroon blijven, zodat de gekozen jaarcontext nooit ambigu is.
19. Als gebruiker wil ik dat de interactie ook zonder QtCharts werkt, zodat LTAP bruikbaar blijft in beperktere runtime-omgevingen.
20. Als gebruiker wil ik geen blokkerende fout door ontbrekende chartmodule, zodat analysewerk kan doorgaan.
21. Als ontwikkelaar wil ik de jaar-kostentijdreeks via een stabiel adaptercontract krijgen, zodat UI-code simpel blijft.
22. Als ontwikkelaar wil ik selectie- en filterstate expliciet modelleren, zodat regressies in UI-flow beperkt blijven.
23. Als ontwikkelaar wil ik dat de grafieklaag dun blijft bovenop bestaande LTAP-bouwlogica, zodat duplicatie van domeinregels wordt vermeden.
24. Als tester wil ik gedrag testen via publieke UI-acties (klik/filter/reset), zodat tests robuust blijven bij refactoring.
25. Als tester wil ik baseline-vs-what-if rendergedrag valideren, zodat grafiekinformatie betrouwbaar is.
26. Als tester wil ik fallbackgedrag zonder chartcomponent valideren, zodat runtime-robuustheid gewaarborgd is.
27. Als productowner wil ik deze slice zonder export afronden, zodat focus op besliskern en interactie blijft.
28. Als productowner wil ik de slice klein en demo-baar houden, zodat vervolgslices (CM-integratie/export) additief blijven.

## Implementation Decisions

- **Scopebesluit:** deze slice visualiseert uitsluitend PM-kosten per jaar (geen CM-integratie).
- **Visualisatiebesluit:** staafdiagram per lifecycle-jaar (discrete jaarbedragen), geen lijnplot.
- **Vergelijkingsbesluit:** baseline en what-if worden als twee parallelle jaarreeksen getoond.
- **Interactiecontract:** klik op jaar activeert harde jaarfilter voor detailweergave.
- **Detailcontract:** tabel toont what-if werkzaamheden van geselecteerd jaar; jaar-samenvatting toont baseline/what-if/delta.
- **Herstelactie:** expliciete “Toon alle jaren” om filter op te heffen en totaaloverzicht te herstellen.
- **State-policy:** geselecteerd jaar blijft behouden na bundeltoepassing; reset naar baseline herstelt defaultselectie.
- **Empty-state policy:** bij jaar zonder werkzaamheden duidelijke tekstuele empty-state in plaats van stille lege tabel.
- **Runtime policy:** als chartmodule ontbreekt, degradeert UI naar lijstselectie met identiek filter- en detailgedrag.
- **Architectuurprincipe:** domeinberekening blijft in adapterlaag; view voegt alleen presentatie- en selectieorchestratie toe.
- **Deep module kans 1:** een kleine presentatie-adapter die LTAP-view omzet naar chart- en detail-ready jaarmodellen.
- **Deep module kans 2:** een selectie-state helper voor jaarfiltering en resetgedrag, los testbaar zonder Qt-widgets.
- **Niet-doen in deze slice:** geen persistent “apply to project”, geen export, geen kalenderjaar-migratie.

## Testing Decisions

- **Wat een goede test is:** test observeerbaar gedrag via publieke interfaces en UI-flow; test geen interne widget-implementatie of private helpers.
- **Te testen gedrag in adapter/presentatielaag:**
  - correcte baseline/what-if jaarreeksen voor visualisatie;
  - correcte detaildataset voor geselecteerd jaar;
  - correcte empty-state output voor jaren zonder taken.
- **Te testen gedrag in UI-flow (`pytest-qt`):**
  - baseline + what-if visualisatie wordt getoond in LTAP-tijdweergave;
  - klik/selectie van jaar filtert detailtabel;
  - “Toon alle jaren” herstelt totaaloverzicht;
  - selectiebehoud na bundelactie en resetgedrag;
  - fallback zonder chartmodule blijft functioneel met lijst + detail.
- **Teststijl:** gedragsgedreven namen in domeinvocabulaire (LTAP, lifecycle-jaar, bundel, baseline, what-if).
- **Prior art:** bestaande `pytest-qt` flowpatronen en adapter-first tests in de desktoplaag.

## Out of Scope

- Integratie van CM-kosten in de jaarreeks.
- Export (CSV/Excel/PDF) van jaardetails of grafiekdata.
- Kalenderjaar-as in plaats van relatieve lifecycle-jaren.
- Geavanceerde taakniveau-diff baseline vs what-if in één samengestelde detailtabel.
- Optimizer voor automatische bundelvoorstellen.
- Portfolio-aggregatie over meerdere projecten.

## Further Notes

- Deze slice maakt LTAP meer beslisgericht zonder de bestaande PM-what-if architectuur te verlaten.
- Door baseline en what-if naast elkaar te tonen, wordt de impact van bundelen per jaar direct leesbaar.
- De fallbackstrategie voorkomt afhankelijkheid van één UI-module en houdt de workflow operationeel.
