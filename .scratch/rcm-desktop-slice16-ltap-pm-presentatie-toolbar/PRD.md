# PRD — RCM2 desktop slice 16 (LTAP PM-presentatie, kostenstyling, werkbalktooltips)

**Status:** ready-for-agent  
**Versie:** 1.0  
**Triage-labels:** ready-for-agent

## Problem Statement

Gebruikers van de ValidateWindow zien in LTAP vaak **PM-kosten van €0**. Dat kan
kloppen (kosten op **Taakgroep** in het domain model, of een onderbouwd nulpunt),
maar het kan ook een **ontbrekende invoer** zijn. Zonder visuele nuance voelt alles
gelijk — scans worden traag en fouten blijven lang onopgemerkt.

De **PM-identiteit in de LTAP-detailtabel** is nu een combinatie van canonieke
`pm_id` en bracket-labels voor taaktype, taakgroep en WET-status. Dat is lastig te
lezen en inconsistent met gewenste werkvolgorde (compact label, globale nummering).

De **primaire werkbalkacties** (“valideren”, volledige analyse, scenariovergelijking)
sluiten niet goed aan op de mentale workflow “bestand klaarzetten → rekenen →
vergelijken”. Ontbrekende **tooltips** en één generieke “busy”-tekst maken de
volgorde en het verschil tussen acties onduidelijk.

## Solution

1. **LTAP kosten per rij:** introduceer een **driedeling** (normaal / bewuste nul /
   waarschuw bij vermoedelijke ontbrekende invoer) en vertaal die naar **kleur en
   gewicht** in de detailtabel — zonder de analytische motor of JSON-schema te
   wijzigen.

2. **LTAP PM-weergavelabel:** vervang het bracket-label door een **vast patroon**
   met **globale volgorde over alle PM-taken** in het project; behoud de canonieke
   `pm_id` als sleutel en toon die **in een tooltip** op de PM-cel.

3. **Werkbalk:** hernoem “Valideer project” naar **“Project inladen”** (tooltip
   legt laden + validatie uit); voeg **tooltips** toe voor volledige analyse en
   scenariovergelijking (volgorde en verschil in uitkomst).

4. **Busy-feedback:** splits **“Bezig met laden…”** (project laden/valideren) en
   **“Bezig met analyseren…”** (run en scenariovergelijking) zodat statusregels de
   juiste taak beschrijven.

## User Stories

1. Als Maintenance Engineer wil ik **bewuste €0-kosten** visueel **rustiger**
   (muted) zien, zodat echte bedragen opvallen.
2. Als Maintenance Engineer wil ik **vermoedelijk ontbrekende PM-kosten** direct als
   probleem herkennen, zodat ik het JSON-model kan aanvullen.
3. Als Maintenance Engineer wil ik **_PM-groepsleden met €0 op regelniveau_
   begrijpen als “kosten elders”, zodat ik niet denk dat de motor iets vergist.
4. Als Maintenance Engineer wil ik een **compact, consistent PM-label** lezen,
   zodat ik minder kolommen en haakjes hoef te interpreteren.
5. Als Maintenance Engineer wil ik **één doorlopende nummering** voor alle PM-taken,
   zodat ik niet per taaktype opnieuw moet tellen.
6. Als Maintenance Engineer wil ik bij een gefilterde LTAP-weergave **dezelfde nummers**
   zien als zonder filter, zodat ik niet verdwaal tussen contexten.
7. Als Maintenance Engineer wil ik het **canonieke project-ID (`pm_id`)** nog steeds
   kunnen terugvinden, zodat ik JSON, logs en issues kan koppelen.
8. Als Maintenance Engineer wil ik **taaktype in het label** herkennen met dezelfde
   codes als in het domain model (`SVO`, `IN`, `TST`, `REV`), zodat er geen tweede
   woordenlijst ontstaat.
9. Als Maintenance Engineer wil ik **WET** alleen in het label zien **wanneer van
   toepassing** (zelfde detectieregel als bestaande LTAP-shiftbaarheid op
   omschrijving), zodat het label niet opgeblazen wordt.
10. Als Maintenance Engineer wil ik **TG** alleen in het label zien wanneer de taak
    aan een **Taakgroep** hangt, zodat bundelcontext direct zichtbaar is.
11. Als Assetmanager wil ik met stakeholders over LTAP praten met **leesbare codes**
    (`PM_REV_TG_03`), zodat schermdelen eenduidig zijn.
12. Als gebruiker wil ik op **“Project inladen”** begrijpen dat het bestand wordt
    ingelezen én inhoudelijk gecontroleerd, zodat ik niet denk dat er niet gevalideerd wordt.
13. Als gebruiker wil ik bij **volledige analyse** via tooltip weten **wat er berekend wordt**
    en **welke resultaten** gevuld worden, zodat ik de knop correct inzet.
14. Als gebruiker wil ik bij **scenariovergelijking** via tooltip weten dat er **twee scenario’s**
    (CM-only vs PM-scenario) worden doorgerekend, zodat ik dat niet verwar met één enkele run.
15. Als gebruiker wil ik in tooltips de **aanbevolen volgorde** (eerst laden, daarna analyse of vergelijking)
    herkennen, zodat ik minder trial-and-error hoeft te doen.
16. Als gebruiker wil ik tijdens wachten **“laden” vs “analyseren”** kunnen onderscheiden in statusteksten,
    zodat ik weet welk proces loopt.
17. Als gebruiker wil ik dat LTAP-header- en selectietooltips **het nieuwe labelcontract**
    beschrijven, zodat onboarding consistenter is.
18. Als tester wil ik **adaptergedrag** op LTAP-view-data testen zonder Qt-detailimplementatie,
    zodat regressies snel zichtbaar zijn.
19. Als maintainer wil ik **geen wijziging aan `rcm_core`** voor deze slice nodig hebben,
    zodat kernpuurheid behouden blijft en risico laag is.
20. Als maintainer wil ik **bestaande selectie- en bundelflow** op canonieke `pm_id`
    ongewijzigd laten, zodat geen verborgen regressie in LTAP ontstaat.

## Implementation Decisions

- **Architectuurgrens:** wijzigingen in **adapter-presentatie** (LTAP-view opbouwen en
  rij-metadata) en **Qt-view** (kleuren, tooltips, knoplabels, busy-teksten).
  **Geen** wijzigingen aan `RCMProject`-schema, motor (`compute_pm_totals`), of
  cache-contract.

- **Deep module — LTAP rij-semantiek:** centraliseer classificatie van PM-kostenregels
  voor detailrijen in één plek naast `LTAPTaskDetail`-constructie:
  - drie waarden: normaal / bewuste nul / waarschuw ontbrekend;
  - **bewuste nul** als `task_group_id` gezet is **of** `cost_eur == 0` en
    `PMTask.effective_aanname_kosten(project)` niet leeg is;
  - **waarschuw** bij `cost_eur == 0` zonder voorgaande redenen (inclusief het geval
    alleen `library_ref` / `cm_kosten_als_basis` zonder effectieve aanname-tekst).

- **Deep module — PM-weergavelabel:** bouw een stabiele **globale volgorde**: sorteer
  canonieke `pm_id`-sleutels, wijs sequenties `$1..N$`. Formatteer het zichtbare label als:
  `PM_<TaskType>_<optioneel WET>_<optioneel TG>_<seq twee cijfers>` waarbij `TaskType`
  exact de enumwaarde volgt (`TST`, niet `TEST`). **Zelfde seq** ongeacht REV-filter.

- **Presentatie vs sleutel:** `LTAPTaskDetail.pm_id` blijft de **domain sleutel**;
  `pm_label` wordt puur display; Qt-cellen zetten **tooltip** met canonieke `pm_id`.

- **WET-detectie:** ongewijzigd concept t.o.v. bestaande LTAP-shiftbaarheid:
  substring **`WET`** in `taak_omschrijving` (case-insensitive).

- **Werkbalkcopy:** primaire knoptekst **“Project inladen”**; aparte tooltipconstanten
  voor laden, volledige analyse en scenariovergelijking (Nederlands, uitleg volgorde
  en verschil CM/PM-run).

- **Busy-copy:** twee gebruikerszichtbare busy-staten — laden vs analyseren —
  i.p.v. één generieke string voor alle achtergrondtaken.

- **UI-stylingbeslissing:** bewuste nul — muted via paletrol (`PlaceholderText` of
  gelijkwaardig themavriendelijk grijs); waarschuw — **vet + donkeroranje** voorgrond
  op het kosten-tablewidgetitem.

- **UI-laag:** alleen de LTAP-detailtabel-kolom “Kosten” en gerelateerde headers/tooltips;
  geen brede restyling van andere panelen in deze slice.

## Testing Decisions

- **Goede test:** observeerbare **uitvoer van adapter/build-functies** — bv.
  `cost_semantics` per detailregel, `pm_label`-patroon en stabiele nummering bij
  filter — **zonder** asserts op interne helpernamen of Qt-widgetklassen.
- **Modules onder test:** LTAP-view-builder / task-detail shaping (adapter-laag).
- **Prior art:** bestaande pytest-tests voor LTAP (`build_ltap_view`,
  `format_ltap_pm_label`-achtige contracten); uitbreiden met scenarios voor
  taakgroep-leden, `effective_aanname_kosten`, en globale volgorde.

## Out of Scope

- **LTAP jaarsommen / staafgrafiek:** opname van **Taakgroep-kosten** in jaaraggregaten;
  allocatie van groepskosten over jaren of dubbeltelling voorkomen — apart product-/motorisch werk.
- **Wijziging canonieke `pm_id` in projectbestanden** of migratie-scripts.
- **Nieuw veld `is_wet`** of andere domain uitbreidingen — blijft bij heuristiek op omschrijving.
- **Brede ValidateWindow UX-redesign** (zie slice 15); deze slice is gericht op LTAP-PM-presentatie,
  kostenstyling en werkbalktooltips/copy.

## Further Notes

- Risico voor eindgebruikers: **jaartotalen in LTAP** kunnen nog afwijken van motor-totalen
  zolang groepskosten niet in aggregaat zitten; communicatie via tooltip/docs kan later, maar is
  niet verplicht onder deze slice.
- Scenariovergelijking en volledige analyse blijven **parallel beschikbaar na geldig laden**;
  tooltips moeten dat helder maken zonder nieuwe enforced wizard-flow.
