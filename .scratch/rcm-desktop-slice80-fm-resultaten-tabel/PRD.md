# PRD — Slice 80: FM-resultaten-tabel (kolommen, sortering, schaal)

**Status:** ready-for-agent
**Voorganger:** slice 79 (view-registry), slice 74 (NB-effectfilter FM-detail), slice 75 (kolom-fit)
**Datum:** 2026-06-11
**Triage:** `ready-for-agent`

> Synthese van de `/grill-with-docs`-sessie (2026-06-11), besluiten 4, 5, 6 en 8
> (+ de NMF-kolom uit besluit 11).

---

## Problem Statement

De FM-resultaten-tabel (was: FM-detail) toont vandaag een vaste kolomset
(FM-id, Faalwijze, PBS-Id, Bouwdeel, Faalmomenten, Downtime, Kosten) zonder
NMF- of RF-informatie, sorteert niet automatisch op de gekozen metric, en
schaalt niet mee met de per-jaar/per-LCC-presentatie. De analist moet PBS-Id
(zelden relevant) wegdenken, kan niet zien welke faalwijzen NMF zijn zonder
de aparte evident-dropdown, en moet handmatig sorteren om de grootste
bijdragers te vinden.

## Solution

Vanuit de gebruiker gezien:

- **Kolomvolgorde**: FM-id, Bouwdeel, Faalwijze, NMF, RF, Faalmomenten,
  Downtime, Kosten. **PBS-Id is default verborgen** maar via een kolomkeuze
  terug te halen.
- **NMF-kolom**: toont of de faalwijze niet-zichtbaar falen betreft
  (vervangt op termijn de evident-dropdown, zie slice 85).
- **RF-kolom**: toont de risicofractie passend bij het actieve
  NB-effectfilter.
- **Default sortering volgt de metric**: NB → Downtime aflopend,
  Faalmomenten → Faalmomenten aflopend, Kosten → Kosten aflopend. De
  metric-combo is in FM-resultaten zichtbaar.
- **Schaal-toggle (per jaar / per LCC)** is in FM-resultaten zichtbaar;
  Faalmomenten, Downtime én Kosten schalen mee.

---

## Zoom-out: modulekaart

```
   metric-combo + schaal-toggle (toolbar, zichtbaar in FM-resultaten)
            │
            ▼
   ContributionPresentation (gedeelde state)      NB-effectfilter (slice 74)
            │                                            │
            ▼                                            ▼
   FM-resultaten-viewbuilder  ── rijen incl. NMF + RF-bepaling
            │
            ▼
   FM-resultaten-tabelmodel + sort-proxy  ── kolomvolgorde, default sort
            │
            ▼
   FM-resultaten-view (kolomkeuze, PBS-Id verborgen)
```

Betrokken seams (domeintaal → module):

- **Resultaat-viewbuilder** (`result_view_service`, `build_fm_detail_view` /
  `FMResultRow`) — rijen krijgen NMF- en RF-velden; schaal toegepast volgens
  `ContributionPresentation`.
- **FM-resultaten-tabelmodel** (`fm_results_table_model`, `_COLUMNS` /
  `_HEADERS`) — nieuwe kolomvolgorde + kolommen.
- **Sort-proxy** (`FMResultsSortProxy`) — default sortkolom afgeleid van de
  actieve metric.
- **Werkruimte-orchestrator** (`FmToolbarPlan`) — metric-combo en
  schaal-toggle zichtbaar in FM-resultaten.
- **Presentatie-state** (`ContributionPresentation`) — bestaande, gedeelde
  horizon-schaal-state; geen tweede toggle-bron.

---

## Implementation Decisions

- **Metric-gestuurde default sort** (besluit 4): bij binnenkomst in
  FM-resultaten en bij metric-wissel sorteert de tabel aflopend op de
  metric-kolom (NB → Downtime, Faalmomenten → Faalmomenten, Kosten → Kosten).
  Handmatig hersorteren door de gebruiker blijft mogelijk en wint tot de
  volgende metric-wissel.
- **RF-kolom volgt het NB-effectfilter** (besluit 5): precies één
  effectklasse geselecteerd → de `fractie` van de `FMEffectLink` naar die
  klasse; leeg of meervoudig → de **hoogste** fractie over de geselecteerde
  (of alle) klassen, met een tooltip die alle klassen + fracties opsomt.
- **Kolomvolgorde en zichtbaarheid** (besluit 6): FM-id, Bouwdeel, Faalwijze,
  NMF, RF, Faalmomenten, Downtime, Kosten; PBS-Id default verborgen,
  terughaalbaar via kolomkeuze (header-contextmenu of menu Beeld);
  zichtbaarheidskeuze persistent via `QSettings`.
- **NMF-kolom**: boolean-weergave op basis van `is_evident` van de
  faalwijze (NMF = niet-evident); filterbaar via de filterrij (slice 81).
- **Gedeelde schaal-state** (besluit 8): de per-jaar/per-LCC-toggle en de
  jaar-combo hergebruiken `ContributionPresentation`; geen aparte
  FM-resultaten-state. Faalmomenten, Downtime en Kosten schalen alle drie mee.
- **Geen motorwijziging**: alles is presentatie; `rcm_core` blijft
  onaangeraakt, geen `CACHE_INPUTS_VERSION`-verhoging.
- Kolom-fit-gedrag van slice 75 (Passend/Bijgesneden) blijft werken met de
  nieuwe kolomset.

## User Stories

1. Als RCM-analist wil ik de tabel default aflopend gesorteerd op de actieve
   metric, zodat de grootste bijdragers bovenaan staan.
2. Als analist wil ik de metric-combo in FM-resultaten zien, zodat ik
   sortering/inhoud wissel zonder eerst naar een andere view te gaan.
3. Als analist wil ik een NMF-kolom, zodat ik niet-zichtbaar falen direct in
   de tabel herken (zonder aparte dropdown).
4. Als analist wil ik een RF-kolom die het NB-effectfilter volgt, zodat ik de
   relevante risicofractie per faalwijze zie.
5. Als analist wil ik bij meervoudige effectselectie een tooltip met alle
   klassen + fracties, zodat ik weet waar de getoonde (hoogste) RF vandaan komt.
6. Als analist wil ik de kolomvolgorde FM-id, Bouwdeel, Faalwijze, NMF, RF,
   Faalmomenten, Downtime, Kosten, zodat identificatie links staat en
   resultaten rechts.
7. Als analist wil ik PBS-Id default verborgen, zodat de tabel compact blijft.
8. Als analist wil ik verborgen kolommen via een kolomkeuze terughalen, zodat
   ik niets definitief kwijt ben.
9. Als analist wil ik dat mijn kolomkeuze bewaard blijft tussen sessies.
10. Als analist wil ik de per-jaar/per-LCC-toggle in FM-resultaten, zodat
    Faalmomenten, Downtime en Kosten in de gewenste schaal staan.
11. Als analist wil ik dat de schaal-keuze gedeeld is met Top 10, zodat beide
    views nooit in verschillende schalen staan zonder dat ik dat zie.
12. Als analist wil ik handmatig op elke kolom kunnen sorteren, waarbij mijn
    keuze blijft staan tot ik de metric wissel.

## Testing Decisions

Goede tests toetsen extern gedrag, geen implementatiedetails.

- **Primaire seam (Qt-vrij): de resultaat-viewbuilder.**
  1. Rijen bevatten NMF en RF; RF-bepaling: één klasse → die fractie;
     meervoudig/leeg → max + tooltip-payload met alle klassen+fracties.
  2. Schaal per jaar vs per LCC schaalt Faalmomenten, Downtime en Kosten
     consistent.
- **Tabelmodel/sort-proxy (pytest-qt, headless):** kolomvolgorde golden;
  default sortkolom per metric; PBS-Id default verborgen.
- **Orchestrator:** `FmToolbarPlan` toont metric-combo + schaal-toggle in
  FM-resultaten.
- **pytest-qt (venster):** metric-wissel hersorteert; kolomkeuze toont/verbergt
  PBS-Id en persisteert.
- **Prior art:** `tests/test_result_view_service*.py`,
  `tests/test_results_workspace_orchestrator.py`, slice 74-tests voor het
  NB-effectfilter op FM-detail.

## Out of Scope

- De filterrij zelf (slice 81) — deze slice levert wel de NMF/RF-kolommen
  waar de filterrij op werkt.
- Verwijderen van de evident-dropdown (slice 85, samen met effectfilter-werk).
- Wijzigingen aan de berekening van downtime/kosten in de motor.
- Kolomkeuze voor andere tabellen dan FM-resultaten (Input-tabellen: slice 83).

## Further Notes

- De RF-tooltip is presentatie-data: lever haar als veld op de rij
  (viewbuilder), niet als Qt-logica in het model.
- "NMF" volgt de bestaande domeinterm (niet-merkbaar falen); label via
  `messages`.
- Let op bestaande tests die op de oude kolomvolgorde of de zichtbare PBS-Id
  asserteren.
