# PRD — Slice 84: PM-schedule-helper + afgeleide PM-kolommen

**Status:** ready-for-agent
**Voorganger:** slice 83 (entiteiten-grid)
**Datum:** 2026-06-11
**Triage:** `ready-for-agent`

> Synthese van de `/grill-with-docs`-sessie (2026-06-11), besluit 10.

---

## Problem Statement

Bij de preventieve-onderhoudstabellen (REV-taken) wil de analist per taak
direct zien: **eerste jaar van uitvoering**, **interval**, **kosten per
uitvoering**, en **totaal aantal uitvoeringen binnen de LCC-periode** — plus
optioneel downtime-bij-OH per effect/RF, repair quality en herstelduur.
Interval en kosten zijn invoervelden, maar eerste-jaar en aantal-executies
zijn **afgeleiden** van de planningslogica in de motor. Die logica in de
UI-laag nabouwen zou twee waarheden creëren (UI-schatting vs motor-planning)
die bij elke motorwijziging uit elkaar lopen; wachten op een volledige run om
ze te tonen maakt de Input-tabel traag en stale-gevoelig.

## Solution

Vanuit de gebruiker gezien:

- De REV-taken-tabel (slice 83) toont per taak extra kolommen:
  **Eerste jaar uitvoering**, **Interval (jaar)**, **Kosten taak (EUR)** en
  **Aantal uitvoeringen in LCC-periode**.
- Optioneel toe te voegen via de kolomkeuze: **downtime bij OH** (per
  effect en RF-factor), **repair quality** en **herstelduur**.
- De afgeleide waarden zijn altijd actueel: een gewijzigd interval of
  startjaar is direct zichtbaar, zonder dat eerst een run nodig is.

---

## Zoom-out: modulekaart

```
   rcm_core (puur, geen Qt)
        │  pm_schedule-helper (NIEUW): taak + horizon → executiejaren
        │  óók gebruikt door de motor (zelfde planningsregels)
        ▼
   Adapter: REV-taken-viewconfig  ── afgeleide kolommen uit de helper
        ▼
   Entiteiten-grid (slice 83)  ── toont invoer- + afgeleide kolommen
```

Betrokken seams (domeintaal → module):

- **PM-schedule-helper (NIEUW, `rcm_core`)** — pure functie(s): gegeven een
  PM-taak (startlogica, interval) en de projecthorizon → eerste
  uitvoeringsjaar en de reeks/telling van uitvoeringen. De **motor gebruikt
  dezelfde helper** voor de PM-planning, zodat UI en motor per constructie
  dezelfde waarheid delen.
- **Adapter-viewconfig** — markeert de afgeleide kolommen als read-only en
  betrekt ze uit de helper (geen rekenlogica in views).
- **Cache-versiebeleid** (`rcm_core/cache.py`) — als het verplaatsen van
  planningslogica naar de helper het motorgedrag ook maar potentieel raakt
  zonder JSON-vormwijziging: `CACHE_INPUTS_VERSION` verhogen (AGENTS.md).

## Implementation Decisions

- **Pure helper in `rcm_core`, gedeeld met de motor** (besluit 10): de
  bestaande PM-planningslogica wordt geëxtraheerd/ontsloten als pure functie;
  de motor roept dezelfde functie aan. Geen duplicatie in de adapter, geen
  run nodig voor de Input-kolommen, nooit stale.
- **Refactor-discipline**: extractie mag het motorresultaat niet wijzigen.
  Bestaat er twijfel of de extractie gedragsneutraal is →
  `CACHE_INPUTS_VERSION` verhogen en parity-/golden-runs draaien.
- **Afgeleide kolommen zijn read-only** in het grid; invoerkolommen
  (interval, kosten, startjaar-invoer) blijven bewerkbaar en triggeren
  directe herberekening van de afgeleiden (pure functie, goedkoop).
- **Optionele kolommen** (downtime bij OH per effect/RF, repair quality,
  herstelduur) zijn bestaande velden/koppelingen (`PMTask`,
  `PMEffectLink.fractie`); ze komen via de kolomkeuze, default verborgen.
- **Horizonbron**: dezelfde projecthorizon als de motor (LCC-periode), geen
  aparte UI-aanname.
- Geen JSON-vormwijziging; geen schema-wijziging in `ENTITY_SCHEMAS`
  (afgeleide kolommen zijn presentatie, geen entiteit-velden).

## User Stories

1. Als RCM-analist wil ik per REV-taak het eerste uitvoeringsjaar zien, zodat
   ik weet wanneer de taak in de planning start.
2. Als analist wil ik per taak het interval in jaren zien, zodat ik de
   frequentie direct kan beoordelen.
3. Als analist wil ik de kosten per uitvoering zien, zodat ik kosten en
   frequentie samen kan wegen.
4. Als analist wil ik het totaal aantal uitvoeringen binnen de LCC-periode
   zien, zodat ik de totale onderhoudslast per taak ken.
5. Als analist wil ik dat deze afgeleiden direct bijwerken als ik interval of
   startjaar wijzig, zodat ik niet eerst een run hoef te draaien.
6. Als analist wil ik erop kunnen vertrouwen dat de getoonde planning exact
   de motor-planning is, zodat Input-tabel en LCC-plot nooit tegenspreken.
7. Als analist wil ik optioneel downtime-bij-OH per effect en RF-factor als
   kolommen kunnen toevoegen, zodat ik beschikbaarheidseffecten van OH zie.
8. Als analist wil ik optioneel repair quality en herstelduur kunnen tonen,
   zodat ik herstelgedrag per taak kan controleren.
9. Als analist wil ik afgeleide kolommen herkenbaar read-only, zodat ik niet
   per ongeluk een berekende waarde probeer te bewerken.
10. Als ontwikkelaar wil ik één planningsfunctie die motor én UI delen, zodat
    een toekomstige planningswijziging maar op één plek hoeft.

## Testing Decisions

Goede tests toetsen extern gedrag van de pure helper; de grid-integratie is
dunne configuratie.

- **Primaire seam (Qt-vrij, `rcm_core`): de pm_schedule-helper.**
  1. Tabelgedreven: (startlogica, interval, horizon) → eerste jaar + telling;
     randgevallen: interval 0/negatief, start buiten horizon, interval >
     horizon, eenmalige taken.
  2. **Consistentietest**: de telling van de helper == het aantal
     PM-executies dat de motor voor dezelfde taak inplant (zelfde input).
- **Motor-regressie:** bestaande motor-/parity-tests blijven groen na de
  extractie; bij gedragstwijfel golden-vergelijking vóór/ná.
- **pytest-qt (grid):** afgeleide kolommen tonen helperwaarden; wijziging van
  interval ververst ze direct; kolommen zijn read-only.
- **Prior art:** motor-tests rond PM-planning/LCC, `tests/test_editing_*`
  voor grid-gedrag, parity-tests als vangnet.

## Out of Scope

- Wijzigingen aan de planningssemantiek zelf (alleen extractie + ontsluiting).
- What-if/overlay-doorwerking in de Input-kolommen (afgeleiden tonen de
  basisplanning, niet scenario A/B).
- Bundeling/taakgroep-optimalisatie.
- Nieuwe entiteit-velden of JSON-vormwijzigingen.

## Further Notes

- AGENTS.md-regel is hier expliciet van toepassing: *motorwijziging zonder
  JSON-vormwijziging → `CACHE_INPUTS_VERSION` verhogen*. Beoordeel dit bij de
  extractie; pure verplaatsing zonder gedragswijziging kan zonder bump, maar
  documenteer die afweging in de PR.
- De helper is ook de natuurlijke plek voor toekomstige
  planningsvisualisaties (bijv. executiejaren-tooltip); houd de API daarom op
  reeks-niveau (jaren), met telling als afgeleide.
