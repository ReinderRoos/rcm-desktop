# ADR-0012 — LTAP als preset-view

## Status

Accepted (2026-06-11).

## Datum

2026-06-11

## Context

RCM-analisten willen naast de LCC-plot een **LTAP-weergave**: dezelfde
tijdgrafiek zonder correctief onderhoud (CM). In RCM1 bestond hiervoor
`ltap_light` en gerelateerde LTAP-rapportages; die staan op de scrub-list.
Terugporten zonder expliciet besluit zou de scrub-list schenden.

Slice 82 levert LTAP als **preset-view** op het bestaande LCC-panel: geen
tweede plot-implementatie, geen motorwijziging.

## Beslissing

### LTAP = preset-view op LCC-panel

- Registry-entry `output.ltap` wijst op hetzelfde paneel als `output.lcc_plot`
  (`legacy_modus = lcc`) met preset `cm_enabled=False`.
- CM-uitsluiting gebeurt op **presentatieniveau** (`effective_lcc_filters`);
  `snapshot.lcc_filters` blijft de door de gebruiker gekozen LCC-toestand.
- Binnen LTAP is CM-bediening verborgen/disabled; de preset is niet
  overrulebaar vanuit de UI.
- Terugschakelen naar LCC-plot herstelt de opgeslagen CM-toestand.

### Geen scrub-list-schending

- `ltap_light` en RCM1-LTAP-rapportages blijven **out**.
- LTAP is uitsluitend een presentatie-preset op bestaande LCC-functionaliteit
  (type-filters, metric, what-if-overlay) — geen port van LTAP-rekenregels,
  bundeling of optimalisatie.

### Trade-off preset-view vs aparte implementatie

| Optie | Voor | Tegen |
|-------|------|-------|
| **Preset-view (gekozen)** | Eén paneel, direct vergelijkbaar met LCC-plot; geen dubbele plot-code; geen motor/cache-impact | LTAP deelt LCC-toolbar en collapse-gedrag; preset-gedrag moet expliciet in orchestrator/plan |
| Aparte implementatie / `ltap_light`-port | Volledige RCM1-pariteit | Scrub-list-schending; dubbele presentatielaag; hoger onderhoud |

### Grens — wanneer opnieuw beslissen

Zodra LTAP **eigen rekenregels** nodig heeft (bundeling, optimalisatie,
afwijkende LTAP-aggregatie, rapportage-export), is een **nieuw ADR** en
expliciet scrub-list-besluit vereist. Tot die tijd blijft LTAP een
presentatie-preset.

## Gevolgen

- `LccViewPreset` en `effective_lcc_filters` in de adapterlaag.
- `LccToolbarVisibilityPlan` krijgt CM-control-zichtbaarheid vanuit preset.
- Geen `CACHE_INPUTS_VERSION`-bump; `rcm_core` ongewijzigd.
