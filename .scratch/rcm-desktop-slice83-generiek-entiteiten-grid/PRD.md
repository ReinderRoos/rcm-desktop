# PRD — Slice 83: Generiek entiteiten-grid + vijf Input-views

**Status:** ready-for-agent
**Voorganger:** slice 79 (view-registry), slice 81 (filterrij-seam)
**Datum:** 2026-06-11
**Triage:** `ready-for-agent`

> Synthese van de `/grill-with-docs`-sessie (2026-06-11), besluit 9.
> Veralgemening van het bestaande Faalwijzen-grid naar alle entiteiten in de
> Editing schema registry.

---

## Problem Statement

De Input-zijde van de werkruimte (slice 79) heeft nog geen inhoud. De analist
wil de invoertabellen — Faalwijzen, REV-taken, Effecten, Taakgroepen en
Correctief onderhoud — direct in de werkruimte bekijken en bewerken, met per
tabel de belangrijkste kolommen zichtbaar, overige kolommen toevoegbaar, en
elke kolom filterbaar. Vandaag bestaat alleen het Faalwijzen-batchgrid
(`ValidateFaalwijzenPanel`) in het Validate-venster; voor de andere
entiteiten is er niets tabulair, en vijf losse grids bouwen zou vijf keer
dezelfde kolom-, validatie- en commit-logica dupliceren.

## Solution

Vanuit de gebruiker gezien:

- Onder **Input** zijn vijf views kiesbaar: **Faalwijzen**, **REV-taken**,
  **Effecten**, **Taakgroepen**, **Correctief onderhoud**.
- Elke view is een **bewerkbaar grid** op de betreffende entiteit, met
  dezelfde editing-regels als bestaande bewerkingen (FK-validatie,
  dirty-markering, ongedaan maken via de normale projectflow).
- Per tabel zijn de **belangrijkste kolommen default zichtbaar**; overige
  kolommen zijn via een kolomkeuze toe te voegen. De keuze is persistent.
- Elke kolom heeft de **filterrij** van slice 81.
- **Correctief onderhoud** is geen eigen entiteit maar een **projectie** van
  de faalwijzen-entiteit met de CM-kolomset (o.a. CM-kosten, downtime per
  faling, hersteld-gedrag); bewerken werkt door op de faalwijze.

---

## Zoom-out: modulekaart

```
   View-registry (Input-zijde, slice 79)
        │  vijf view-entries
        ▼
   Entiteiten-grid (generiek, NIEUW)
        │  geconfigureerd per entiteit:
        │  schema (ENTITY_SCHEMAS) + kolompreset + projectie
        ├── Tabulaire editing-pipeline (bestaand: parse/validate/commit)
        ├── Filter-proxy (slice 81)
        └── Kolomkeuze + persistentie
```

Betrokken seams (domeintaal → module):

- **Editing schema registry** (`rcm_core/editing/schemas.py`,
  `ENTITY_SCHEMAS`) — de bron voor kolommen, typen, verplichte velden en
  FK-regels: `faalwijzes`, `pm_tasks`, `effect_klassen`, `task_groups` (en
  de link-entiteiten waar de views ze nodig hebben).
- **Tabulaire editing-pipeline** (bestaand) — parse/validate/commit van
  celwijzigingen; het grid mag hier niets van dupliceren.
- **Entiteiten-grid (NIEUW)** — één generiek, schema-gedreven grid
  (veralgemening van `ValidateFaalwijzenPanel`), geconfigureerd met:
  entiteit, kolompreset (default zichtbaar), optionele **projectie**
  (kolomsubset + rijfilter) en filterrij.
- **Kolompresets (Qt-vrij)** — per view een declaratieve lijst
  default-zichtbare kolommen; valideerbaar tegen het schema.

## Implementation Decisions

- **Eén generiek grid, schema-gedreven** (besluit 9): kolommen, typen en
  validatie komen uit `ENTITY_SCHEMAS`; per view alleen configuratie
  (kolompreset, projectie). Geen vijf grid-implementaties.
- **"Correctief onderhoud" = projectie** (besluit 9): dezelfde
  faalwijzen-entiteit, andere kolomset (CM-velden zoals `cost_cm_eur`,
  `downtime_per_failure`, `repair_quality`, aannames). Een bewerking in de
  projectie is een bewerking van de faalwijze — één bron van waarheid.
- **REV-taken** = de `pm_tasks`-entiteit met REV-relevante kolompreset;
  afgeleide PM-kolommen (eerste jaar, aantal executies) komen in slice 84.
- **Bewerken via de bestaande pipeline**: het grid hergebruikt de tabulaire
  editing-pipeline (zoals `ValidateFaalwijzenPanel`); schema-backed en
  project-backed FK's gedragen zich zoals elders.
- **Kolomkeuze persistent** per view via `QSettings`; default-presets staan
  in code (Qt-vrij) en zijn golden-getest.
- **Filterrij hergebruikt** (slice 81): kolomtypen uit het schema bepalen
  het filtertype (tekst → deelstring, bool → ja/nee, numeriek → expressie).
- **Validate-venster blijft bestaan**: dit grid vervangt het Validate-grid
  niet in deze slice; het deelt er de pipeline mee.
- **CONTEXT.md**: term *Entiteiten-grid* toevoegen.
- Geen motorwijziging; bewerkingen lopen via de bestaande dirty/run-flow
  (globale digest en FM-invoerhash doen hun normale werk).

## User Stories

1. Als RCM-analist wil ik onder Input de tabel Faalwijzen openen, zodat ik
   faalwijzen in de werkruimte kan bekijken en bewerken.
2. Als analist wil ik onder Input REV-taken zien, zodat ik het preventieve
   programma tabulair kan beoordelen.
3. Als analist wil ik onder Input Effecten zien, zodat ik effectklassen en
   hun eigenschappen kan controleren.
4. Als analist wil ik onder Input Taakgroepen zien, zodat ik bundeling van
   taken kan beheren.
5. Als analist wil ik onder Input een Correctief-onderhoud-tabel, zodat ik
   alle CM-parameters per faalwijze bij elkaar zie.
6. Als analist wil ik dat een wijziging in de Correctief-tabel de
   onderliggende faalwijze wijzigt, zodat er nooit twee waarheden zijn.
7. Als analist wil ik per tabel de belangrijkste kolommen default zichtbaar,
   zodat het beeld overzichtelijk start.
8. Als analist wil ik extra kolommen kunnen toevoegen via een kolomkeuze,
   zodat ik bij detailvelden kan zonder permanente drukte.
9. Als analist wil ik dat mijn kolomkeuze per tabel bewaard blijft tussen
   sessies.
10. Als analist wil ik elke kolom kunnen filteren (deelstring/ja-nee/
    expressie), zodat ik snel de relevante rijen vind.
11. Als analist wil ik dezelfde validatie en foutmarkering als in het
    Faalwijzen-grid, zodat ik geen ongeldige invoer kan committen.
12. Als analist wil ik dat bewerkingen het project dirty markeren en in de
    normale save/run-flow meelopen, zodat resultaten nooit stil verouderen.
13. Als ontwikkelaar wil ik een nieuwe entiteiten-view kunnen toevoegen met
    alleen een registry-entry + kolompreset, zodat uitbreiden goedkoop is.

## Testing Decisions

Goede tests toetsen extern gedrag aan de bestaande editing-pipeline en de
nieuwe Qt-vrije presets — niet aan widget-internals.

- **Primaire seam (Qt-vrij): kolompresets + projectie-definities.**
  1. Golden: elke Input-view heeft een preset; alle presetkolommen bestaan
     in het schema.
  2. Correctief-projectie: kolomsubset klopt; mapping wijst naar
     faalwijze-velden.
- **Editing-pipeline (bestaand niveau):** celwijziging in het generieke grid
  → zelfde parse/validate/commit-resultaat als in `ValidateFaalwijzenPanel`
  (regressie via bestaande pipeline-tests + entiteit-parametrisatie).
- **pytest-qt (venster):** elke Input-view opent met preset-kolommen;
  kolomkeuze toont extra kolom en persisteert; filterrij werkt; bewerking in
  Correctief-projectie wijzigt de faalwijze.
- **Parity-bewaking:** `tests/test_editing_schemas_parity.py` blijft groen
  (schema's worden gelezen, niet gewijzigd).
- **Prior art:** tests rond `ValidateFaalwijzenPanel` (slice 7/15), de
  tabulaire-editing-tests, slice 81-filtertests.

## Out of Scope

- Afgeleide PM-kolommen (eerste jaar, interval-totalen, executies) —
  slice 84.
- PBS-items als Input-view (PBS blijft de boom; volgorde-werk in slice 86).
- Vervanging of sloop van het Validate-venster.
- Nieuwe entiteiten of schemavelden in `rcm_core`.
- Rijen toevoegen/verwijderen als dat de huidige pipeline niet al ondersteunt
  (alleen celbewerking is vereist voor deze slice).

## Further Notes

- Let op het regelbudget van venster/panel-modules: het generieke grid hoort
  in een eigen module met dunne per-view-configuratie.
- De Correctief-projectie deelt het dirty-mechanisme met Faalwijzen: een
  wijziging in de ene view is direct zichtbaar in de andere.
- REV-taken vs PM-taken: gebruik de bestaande domeinterm REV in labels
  (`messages`), het schema blijft `pm_tasks`.
