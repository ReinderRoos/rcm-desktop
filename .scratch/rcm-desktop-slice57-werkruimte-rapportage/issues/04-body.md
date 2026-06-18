## Parent

https://github.com/ReinderRoos/rcm-desktop/issues/9

## What to build

Per-functie niet-beschikbaarheids-hoofdstukken: `ReportFunctieSelectionService` kiest functies met beschikbaarheids-effectklassen boven drempel (default 1% project; opt-in onder drempel), gesorteerd op impact. Per functie in het rapport: gekoppelde effectklassen in kop, Top10 op component (lifecycle NB %), functie-tijdsplot, PBS Top10+rest (bij compare A en B onder elkaar), regelgebaseerde uitleg (dominante componenten, aandeel t.o.v. project).

Vaste presentatie-defaults; geen overname van werkruimte taaktype-filters. Geen functies boven drempel → kort rapport (KPI + projectplots + footnote), geen crash.

## Acceptance criteria

- [ ] Drempel en effectklasse-filter bepalen NB-functiepagina's
- [ ] Per functie: Top10 component, tijdsplot, PBS-tabel, narrative
- [ ] Compare: A/B onder elkaar in PBS-tabellen
- [ ] Sorteer op impact binnen functie-scope
- [ ] Leeg boven drempel: footnote, geen exception
- [ ] Unit-tests: drempel-filtering, sectievolgorde, PBS rest-regel, narrative triggers

## Blocked by

https://github.com/ReinderRoos/rcm-desktop/issues/12
