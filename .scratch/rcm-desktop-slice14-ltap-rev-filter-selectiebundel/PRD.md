# PRD - RCM2 desktop slice 14 (LTAP REV-filter, verrijkt PM-label, bundelen via tabelselectie)

**Status:** ready-for-agent  
**Versie:** 1.0  
**Triage-labels:** ready-for-agent

## Problem Statement

De LTAP-flow ondersteunt al jaarselectie, detailweergave en bundelverschuiving, maar
mist drie cruciale bedienings- en interpretatielaagverbeteringen:

- gebruikers kunnen niet snel focussen op alleen REV-onderhoud;
- de PM-id kolom mist compacte metadata over taaktype, taakgroepstatus en wettelijke status;
- bundeltoepassing is nog niet strikt gekoppeld aan de zichtbare selectie in de detailtabel.

Daardoor ontstaat extra cognitieve belasting, meer kans op bedienfouten en minder
voorspelbaar gedrag tijdens what-if-planning in de ValidateWindow.

## Solution

Breid de bestaande LTAP-interactie in de ValidateWindow uit met drie samenhangende
verbeteringen:

1. Een expliciete 2-stand REV-toggle die de LTAP-view consistent filtert.
2. Een hard PM-labelcontract in de PM-id kolom met type/groep/WET-status.
3. Een selectie-gedreven bundelpad: alleen zichtbare geselecteerde tabelregels vormen de bundelbasis.

Deze uitbreiding blijft volledig binnen de bestaande LTAP/ValidateWindow-flow en
respecteert bestaande bundelvalidatieregels (inclusief all-or-nothing bij
niet-verschuifbare taken).

## User Stories

1. Als Maintenance Engineer wil ik met een knop alleen REV-taken tonen, zodat ik snel op revisieplanning kan focussen.
2. Als Maintenance Engineer wil ik met dezelfde knop terug kunnen naar alle taken, zodat ik context niet verlies.
3. Als Maintenance Engineer wil ik dat de LTAP-grafiek meefiltert op REV, zodat jaarbalken alleen relevante kosten tonen.
4. Als Maintenance Engineer wil ik dat de detailtabel meefiltert op REV, zodat tabelinhoud en grafiek consistent zijn.
5. Als Maintenance Engineer wil ik dat jaarselectie in gefilterde modus blijft werken zoals nu, zodat mijn workflow herkenbaar blijft.
6. Als Maintenance Engineer wil ik "Toon alle jaren" kunnen blijven gebruiken binnen de actieve filtercontext, zodat ik snel reset naar overzicht.
7. Als Maintenance Engineer wil ik in PM-id direct zien welk taaktype geldt, zodat ik minder kolommen hoef te scannen.
8. Als Maintenance Engineer wil ik in PM-id zien of een taak in een taakgroep valt, zodat ik bundelimpact beter kan inschatten.
9. Als Maintenance Engineer wil ik in PM-id zien of een taak wettelijk is, zodat ik direct weet of verschuiving gevoelig is.
10. Als Assetmanager wil ik een vast en compact labelpatroon in de PM-id kolom, zodat interpretatie consistent blijft over projecten.
11. Als gebruiker wil ik dat bundelen alleen werkt op de rijen die ik zichtbaar en expliciet selecteer, zodat de actie volledig voorspelbaar is.
12. Als gebruiker wil ik een duidelijke foutmelding krijgen als ik bundel zonder geldige selectie, zodat ik direct weet hoe ik verder moet.
13. Als gebruiker wil ik geen fallback naar handmatige PM-id invoer bij bundelen, zodat er geen verborgen tweede pad ontstaat.
14. Als gebruiker wil ik dat niet-verschuifbare taken in selectie de hele bundelactie blokkeren, zodat er geen stille partial updates plaatsvinden.
15. Als gebruiker wil ik bij blokkade zien welke PM-id's en redenen de bundel tegenhouden, zodat ik gericht kan corrigeren.
16. Als gebruiker wil ik dat mijn jaarselectie sticky blijft na filter-toggle of bundelactie zolang die selectie nog geldig is, zodat ik in context blijf.
17. Als gebruiker wil ik gecontroleerde fallback naar "alle jaren" als de gekozen jaarcontext niet meer geldig is, zodat de UI niet in ongeldige staat komt.
18. Als tester wil ik filtergedrag als observeerbaar gedrag testen, zodat tests refactorbestendig blijven.
19. Als tester wil ik labelopbouw als contract testen, zodat regressies in notatie direct zichtbaar zijn.
20. Als tester wil ik selectie-gedreven bundelgedrag end-to-end testen in pytest-qt, zodat gebruikersgedrag betrouwbaar is.
21. Als productowner wil ik dat de slice klein en AFK-uitvoerbaar blijft, zodat implementatie en review kort-cyclisch blijven.
22. Als productowner wil ik nul functionele regressie op bestaande LTAP-interacties, zodat eerdere slices stabiel blijven.

## Implementation Decisions

- **Scopebeslissing:** uitsluitend uitbreiding van de bestaande ValidateWindow/LTAP-flow; geen nieuw scherm, wizard of alternatieve bundel-UI.
- **Filtercontract:** REV-filter is een centrale view-filtercontext met twee toestanden (`all` en `rev-only`) die zowel grafiek als detailweergave aanstuurt.
- **Filterbediening:** expliciete toggleknop met duidelijke toestandstekst (alleen REV vs alle taken) en directe rerender.
- **Datastroombeslissing:** filtercontext wordt in de vieworchestratie en adapteruitkomst consequent toegepast, zodat chart/detail altijd dezelfde dataset representeren.
- **PM-labelcontract:** PM-id kolom vervangt de huidige losse identifierweergave door exact:
  `<PM-ID> [<TYPE>] [<TG|GEEN-TG>] [<WET|NIET-WET>]`.
- **Typecontract:** type komt uit het domain model en wordt compact gerenderd als `REV`, `SVO`, `IN`, `TST`.
- **Groepcontract:** `TG` bij aanwezige taakgroepkoppeling; anders `GEEN-TG`.
- **WET-contract:** `WET` wanneer wettelijke status van toepassing is; anders `NIET-WET`.
- **Bundelbroncontract:** de bundelinput wordt uitsluitend afgeleid van op dat moment zichtbare en geselecteerde detailrijen.
- **Foutpadcontract:** geen geldige selectie betekent hard blokkerende validatiefout; geen fallback naar handmatige PM-id invoer.
- **All-or-nothing contract:** zodra 1 geselecteerde taak niet verschuifbaar is (bijv. SVO/WET), wordt de volledige bundelactie afgekeurd met expliciete redenen.
- **Statecontract:** jaarselectie blijft sticky na bundelen/filteren indien nog geldig in de actieve filtercontext; anders gecontroleerde fallback naar "alle jaren".
- **Architectuurgrens:** UI-kerndecoupling blijft intact; viewlaag gebruikt adapterlaag en introduceert geen Qt-kennis in `rcm_core`.
- **Deep module kans 1:** centrale LTAP filter/selection orchestrator met kleine, testbare interface voor rendercontext en selectie-extractie.
- **Deep module kans 2:** gecentraliseerde PM-label formatter als enkel bronpunt voor labelcontract in tabelrendering en tests.

## Testing Decisions

- **Wat een goede test is:** test uitsluitend extern observeerbaar gedrag (zichtbare dataset, tabelinhoud, foutmeldingen, actie-uitkomst), niet interne widgetimplementatie.
- **Te testen gebieden:**
  - adapterlogica voor REV-filtercontext en PM-labelopbouw;
  - validate-window flow voor filtertoggle, selectiegedreven bundelacties en foutpaden;
  - regressie op bestaande LTAP-interactie (jaarselectie, "toon alle jaren", reset overlay).
- **Verplichte testgedragingen:**
  1. REV-toggle filtert grafiek en detailtabel consistent;
  2. PM-id labels volgen exact het afgesproken vaste format;
  3. bundel zonder selectie geeft hard blokkerende, begrijpelijke foutmelding;
  4. bundel met niet-verschuifbare selectie faalt all-or-nothing met reden;
  5. bundel met geldige selectie verschuift alleen geselecteerde zichtbare taken;
  6. sticky jaarselectie blijft behouden of valt gecontroleerd terug naar alle jaren.
- **Prior art:** bestaande pytest-qt LTAP flowtests en adaptertests rond LTAP-viewopbouw/bundle-validatie.
- **Kwaliteitsgate:** relevante LTAP-regressiesuite blijft groen naast nieuwe tests.

## Out of Scope

- Nieuwe LTAP-visualisatietypen buiten de bestaande grafiek/list fallback.
- Nieuwe domeinregels voor shiftability buiten het bestaande SVO/WET en bundelbeleid.
- Wijziging van kernmodellen of cachingbeleid anders dan strikt nodig voor deze UI/adapteruitbreiding.
- Herontwerp van algemene ValidateWindow layout of paneelarchitectuur buiten LTAP-bediening.
- Bulkacties buiten de zichtbare tabelselectiecontext.

## Further Notes

- Deze slice formaliseert expliciete gebruikersintentie: wat zichtbaar en geselecteerd is, is de enige bron voor bundelwijziging.
- Het vaste PM-labelcontract is zowel UX-verbetering als testcontract.
- De gekozen aanpak houdt de slice smal, sluit aan op eerdere LTAP-slices en minimaliseert regressierisico.
