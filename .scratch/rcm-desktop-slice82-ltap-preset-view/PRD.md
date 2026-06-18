# PRD — Slice 82: LTAP als preset-view op het LCC-panel (+ ADR)

**Status:** ready-for-agent
**Voorganger:** slice 79 (view-registry)
**Datum:** 2026-06-11
**Triage:** `ready-for-agent`

> Synthese van de `/grill-with-docs`-sessie (2026-06-11), besluit 3.
> Inclusief een **ADR** die afbakent waarom dit géén scrub-list-schending is.

---

## Problem Statement

De analist wil naast de LCC-plot een **LTAP-weergave**: dezelfde
tijdgrafiek, maar **zonder correctief onderhoud** — het lange-termijn
assetplanningsbeeld dat alleen de geplande (preventieve) lasten toont. Die
weergave bestaat niet; CM uitfilteren kan vandaag alleen indirect en
foutgevoelig via handmatige filters die per ongeluk weer aangezet worden. De
oude `ltap_light`-functionaliteit uit RCM1 staat bovendien op de scrub-list,
dus "gewoon terugporten" is geen optie zonder expliciet besluit.

## Solution

Vanuit de gebruiker gezien:

- Onder Output verschijnt de view **LTAP** (naast LCC-plot) in dropdown en
  menu Beeld.
- LTAP toont **hetzelfde LCC-panel**, maar met **CM hard uitgeschakeld**: de
  curves/staafdelen voor correctief onderhoud zijn weg en de CM-bediening is
  binnen LTAP niet bedienbaar (geen aan-uit-vinkje dat "per ongeluk" CM
  terugbrengt).
- Wisselen tussen LCC-plot en LTAP verandert verder niets aan metric, jaren
  of filters — het is dezelfde plot met een vaste CM-uitsluiting.

---

## Zoom-out: modulekaart

```
   View-registry (slice 79)
        │  view_id: lcc_plot          view_id: ltap (preset)
        ▼                                  ▼
   Werkruimte-orchestrator  ── LccToolbarVisibilityPlan + preset-vlag
        ▼
   LCC-panel (één implementatie)  ── CM-reeksen + CM-bediening
```

Betrokken seams (domeintaal → module):

- **View-registry** (slice 79) — LTAP is een tweede registry-entry die op
  hetzelfde paneel wijst, met een **preset**: `cm_enabled=False`,
  niet-overrulebaar.
- **Werkruimte-orchestrator** (`results_workspace_orchestrator`) — het
  LCC-toolbar-plan krijgt de preset als input: CM-gerelateerde toggles
  verborgen/disabled in LTAP; CM-reeksen uitgesloten van de plotopbouw.
- **LCC-panel** (`lcc_workspace_panel`) — geen fork: één paneel, gedrag
  gestuurd door het plan.

## Implementation Decisions

- **LTAP = preset-view, geen port** (besluit 3): er komt geen tweede
  plot-implementatie en geen port van `ltap_light` uit RCM1. LTAP is het
  bestaande LCC-panel met een hard preset `CM uit`.
- **Hard uit = niet bedienbaar**: binnen LTAP is de CM-bediening afwezig of
  disabled; de preset kan niet vanuit de UI worden opgeheven. Terug naar
  LCC-plot herstelt de gewone CM-toestand (de LCC-plot-state wordt door LTAP
  niet overschreven).
- **Sticky per zijde** (slice 79) geldt ook hier: LTAP is een eigen view-id;
  wie in LTAP stond komt daar terug.
- **ADR verplicht**: "LTAP als preset-view" — legt vast (1) waarom dit geen
  scrub-list-schending is (`ltap_light` blijft out; alleen een
  presentatie-preset op bestaande functionaliteit), (2) de trade-off
  preset-view vs aparte implementatie, (3) de grens: zodra LTAP eigen
  rekenregels nodig heeft, is een nieuw besluit nodig.
- **Geen motorwijziging**: CM-uitsluiting gebeurt op presentatieniveau
  (reeksopbouw), niet in `rcm_core`; geen `CACHE_INPUTS_VERSION`-verhoging.
- **CONTEXT.md**: term *LTAP (preset-view)* toevoegen.

## User Stories

1. Als RCM-analist wil ik onder Output een LTAP-view kiezen, zodat ik het
   planningsbeeld zonder correctief onderhoud zie.
2. Als analist wil ik dat LTAP exact dezelfde plot is als de LCC-plot minus
   CM, zodat de twee beelden direct vergelijkbaar zijn.
3. Als analist wil ik dat CM binnen LTAP niet aan te zetten is, zodat het
   planningsbeeld nooit vervuild raakt.
4. Als analist wil ik dat metric-, jaar- en filterkeuzes gewoon doorwerken in
   LTAP, zodat ik niet opnieuw hoef in te stellen.
5. Als analist wil ik dat terugschakelen naar LCC-plot mijn oude CM-toestand
   herstelt, zodat LTAP geen sporen achterlaat.
6. Als analist wil ik LTAP via dropdown, menu Beeld en `Ctrl+Alt+n` bereiken,
   net als elke andere Output-view.
7. Als beheerder van de architectuur wil ik een ADR die LTAP afbakent t.o.v.
   de scrub-list, zodat `ltap_light` niet sluipenderwijs terugkeert.

## Testing Decisions

Goede tests toetsen extern gedrag aan de orchestrator-seam, niet aan
plot-pixels.

- **Primaire seam (Qt-vrij): de werkruimte-orchestrator.**
  1. Plan voor view-id `ltap`: CM-reeksen uitgesloten, CM-bediening
     verborgen/disabled.
  2. Wissel LTAP → LCC-plot: plan herstelt de eerdere CM-toestand.
- **View-registry golden** (slice 79-tests uitbreiden): LTAP-entry bestaat
  met preset.
- **pytest-qt (venster):** in LTAP zijn CM-curves afwezig en is de
  CM-bediening niet bedienbaar; terugwisselen herstelt.
- **Prior art:** `tests/test_results_workspace_orchestrator.py`
  (toolbar-plannen), LCC-toolbar-visibility-tests van slice 71/76.

## Out of Scope

- Port van `ltap_light` of RCM1-LTAP-rapportages.
- Eigen LTAP-rekenregels, bundeling of optimalisatie (zie scrub-list).
- LTAP-specifieke export.
- Wijzigingen aan de LCC-plot zelf buiten de preset-doorvoer
  (asbenamingen: slice 85).

## Further Notes

- De ADR hoort bij deze slice (niet uitstellen): het besluit is
  moeilijk-omkeerbaar zodra gebruikers LTAP-gedrag verwachten.
- Implementatievolgorde binnen de slice: registry-entry + orchestrator-plan
  (test-first), dan venster-bedrading, dan ADR + CONTEXT.md.
