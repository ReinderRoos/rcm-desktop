# PRD — Slice 85: Effect-filter pruning + plaatsing; LCC-plot asbenamingen

**Status:** ready-for-agent
**Voorganger:** slice 80 (NMF-kolom), slice 81 (filterrij), slice 74 (NB-effectfilter FM-detail)
**Datum:** 2026-06-11
**Triage:** `ready-for-agent`

> Synthese van de `/grill-with-docs`-sessie (2026-06-11), besluiten 11 en 12.

---

## Problem Statement

Het NB-effectfilter toont alle effectklassen, ook klassen die voor de totale
PBS **nergens** bijdragen aan kosten, faalmomenten of downtime — selecteren
daarvan levert een leeg beeld zonder uitleg. Daarnaast staat de
effectfilter-dropdown niet bij de andere bedieningsknoppen, en bestaat er nog
een aparte NMF/alle/evident-dropdown die sinds de NMF-kolom (slice 80)
dubbelt met tabelisfiltering. Tot slot missen de assen van de LCC-plot
expliciete benamingen: de analist moet raden of de y-as faalmomenten, uren
of euro's toont.

## Solution

Vanuit de gebruiker gezien:

- In het effectfilter zijn klassen **zonder bijdrage** voor de totale PBS
  (geen kosten, geen faalmomenten, geen downtime) **uitgegrijsd** met een
  tooltip die uitlegt waarom — ze blijven zichtbaar zodat de volledige
  indeling herkenbaar blijft, maar zijn niet selecteerbaar.
- De effectfilter-dropdown staat **naast de andere knoppen** in de toolbar.
- De **NMF/alle/evident-dropdown verdwijnt**: hetzelfde onderscheid loopt nu
  via de NMF-kolom + filterrij in FM-resultaten.
- De **LCC-plot** krijgt expliciete asbenamingen per metric:
  x-as **kalenderjaren**; y-as **aantal keer falen** (faalmomenten),
  **niet-beschikbaarheid (uren of %)** (NB) of **EUR** (kosten).

---

## Zoom-out: modulekaart

```
   Run-resultaten (totale PBS)
        │  bijdrage per effectklasse (kosten/faalmomenten/downtime)
        ▼
   Effect-presentatieplan (Qt-vrij)  ── per klasse: selecteerbaar? + reden
        ▼
   NbEffectFilterCombo (view)  ── uitgegrijsde items + tooltip
   ─────────────────────────────────────────────
   LCC-plot-builder  ── aslabels per metric (Qt-vrij bepaald)
```

Betrokken seams (domeintaal → module):

- **Effect-presentatie** (`EffectPresentation` / adapter rond het
  NB-effectfilter, slice 71/74) — wordt uitgebreid met
  per-klasse-beschikbaarheid: bijdrage-bepaling over de **totale PBS**
  (niet de huidige PBS-selectie), inclusief reden-tekst voor de tooltip.
- **NbEffectFilterCombo** (view) — rendert disabled items + tooltip;
  bind-only.
- **Werkruimte-toolbarplannen** (`results_workspace_orchestrator`) —
  plaatsing van de dropdown naast de overige knoppen; verwijdering van de
  evident-dropdown uit de plannen.
- **LCC-plot-opbouw** (LCC-panel/adapter) — aslabel-bepaling als pure
  functie: metric → (x-label, y-label + eenheid), labels via `messages`.

## Implementation Decisions

- **Uitgrijzen, niet verbergen** (besluit 11): klassen zonder bijdrage
  blijven in de lijst (volledige partitie zichtbaar) maar zijn disabled, met
  tooltip "geen bijdrage in kosten, faalmomenten of downtime voor de totale
  PBS". Bepaling op **totale-PBS-niveau**, onafhankelijk van de actieve
  boomselectie.
- **Reeds geselecteerde klasse die bijdrageloos wordt** (na een nieuwe run):
  selectie blijft geldig maar het item toont de disabled-stijl; het filter
  forceert geen stille deselectie.
- **Plaatsing**: de effectfilter-dropdown verhuist naar de gedeelde
  knoppenrij (zelfde rij als metric-combo/schaal-toggle), zodat alle
  presentatiebediening bij elkaar staat.
- **Evident-dropdown vervalt** (besluit 11): functionaliteit is gedekt door
  de NMF-kolom (slice 80) + filterrij (slice 81). Verwijder widget, state en
  bijbehorende plan-velden; migreer eventueel persistente instellingen stil.
- **Aslabels per metric** (besluit 12): één pure mapping metric → aslabels;
  geen ontwerpfork van de plot. Labels: x = "Kalenderjaren"; y =
  "Aantal keer falen", "Niet-beschikbaarheid (uren)" of "(%)" conform de
  bestaande NB-presentatie-eenheid, "Kosten (EUR)".
- Bijdrage-bepaling hergebruikt bestaande run-uitvoer (effect-bijdragen per
  klasse); geen motorwijziging, geen `CACHE_INPUTS_VERSION`-bump.

## User Stories

1. Als RCM-analist wil ik dat effectklassen zonder enige bijdrage uitgegrijsd
   zijn, zodat ik geen lege filterresultaten kan kiezen.
2. Als analist wil ik via een tooltip zien waaróm een klasse uitgegrijsd is,
   zodat ik begrijp dat de klasse leeg is en niet kapot.
3. Als analist wil ik de volledige effectindeling blijven zien (ook lege
   klassen), zodat het overzicht van de partitie intact blijft.
4. Als analist wil ik dat de uitgrijzing over de **totale PBS** gaat, zodat
   een klasse niet ten onrechte uitgegrijsd is omdat mijn huidige
   boomselectie toevallig leeg is.
5. Als analist wil ik de effectfilter-dropdown naast de andere knoppen, zodat
   alle presentatiebediening op één plek staat.
6. Als analist wil ik dat de NMF/alle/evident-dropdown verdwijnt, zodat er
   één manier (NMF-kolom + filter) overblijft en geen dubbele bediening.
7. Als analist wil ik op de x-as van de LCC-plot "Kalenderjaren" zien, zodat
   de tijdsas eenduidig is.
8. Als analist wil ik op de y-as de metric met eenheid zien (aantal keer
   falen / niet-beschikbaarheid in uren of % / kosten in EUR), zodat ik
   waarden correct interpreteer.
9. Als analist wil ik dat de aslabels live meewisselen met de metric-keuze,
   zodat plot en bediening nooit tegenspreken.

## Testing Decisions

Goede tests toetsen extern gedrag aan Qt-vrije plannen; widgets zijn
bind-only.

- **Primaire seam (Qt-vrij): het effect-presentatieplan.**
  1. Klasse met 0 kosten, 0 faalmomenten, 0 downtime over de totale PBS →
     niet-selecteerbaar + reden; klasse met enige bijdrage → selecteerbaar.
  2. Bepaling negeert de actieve PBS-selectie.
  3. Geselecteerde klasse die bijdrageloos wordt → blijft geselecteerd,
     gemarkeerd disabled.
- **Aslabel-mapping (Qt-vrij):** golden per metric (incl. NB-eenheid
  uren vs %).
- **Orchestrator:** evident-dropdown ontbreekt in alle toolbarplannen;
  effectfilter staat in de gedeelde knoppenrij.
- **pytest-qt (venster):** uitgegrijsd item is niet aanklikbaar en heeft de
  tooltip; metric-wissel ververst aslabels; de evident-dropdown bestaat niet
  meer.
- **Prior art:** slice 71/74-tests (NB-effectfilter, `EffectPresentation`),
  `tests/test_results_workspace_orchestrator.py`.

## Out of Scope

- Wijziging van de filter-semantiek zelf (welke rijen/series het filter
  beperkt) — alleen selecteerbaarheid, plaatsing en de evident-sloop.
- Pruning op basis van de actieve PBS-selectie (bewust totale-PBS).
- Plot-herontwerp, legenda-werk of extra series.
- Verwijderen van `is_evident` uit het domeinmodel (alleen de dropdown gaat
  weg).

## Further Notes

- Sloopvolgorde: eerst NMF-kolom + filterrij gemerged (slices 80/81), dán de
  evident-dropdown weg — geen functionaliteitsgat.
- Let op tests die de evident-dropdown of oude aslabels asserteren.
- De disabled-reden hoort als data in het plan (string uit `messages`), niet
  hardcoded in de combo.
