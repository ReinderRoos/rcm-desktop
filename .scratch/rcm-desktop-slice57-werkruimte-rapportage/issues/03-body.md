## Parent

https://github.com/ReinderRoos/rcm-desktop/issues/9

## What to build

Voeg projectbrede tijdsplotten toe aan het rapport als ingesloten PNG's via een Qt-vrije `ReportChartRenderer` (bijv. matplotlib Agg). NB-jaarproxy en LCC-curve gebruiken dezelfde builders als de werkruimte, met bevroren overlay per slot bij compare. Layout: bij compare gestapeld (A boven, B onder). NB-proxy-disclaimer in caption of appendix-seed.

## Acceptance criteria

- [ ] `ReportChartRenderer` levert non-empty PNG bytes zonder Qt-widgets
- [ ] Rapport bevat projectbrede NB- en LCC-plotsecties (single en compare)
- [ ] Compare gebruikt per-slot bevroren overlay bij chart-build
- [ ] NB-disclaimer zichtbaar bij jaarverdeling-proxy
- [ ] Unit-tests: PNG smoke, materialisatie bevat projectplot-secties

## Blocked by

https://github.com/ReinderRoos/rcm-desktop/issues/11
