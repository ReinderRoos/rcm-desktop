# ADR-0020: Werkruimte chrome-layout v2

**Status:** accepted (footer context-zone superseded by ADR-0021)  
**Date:** 2026-06-18  
**Parent:** slice 107 grill 107-A (grill-with-docs)

## Context

Slice 105.31 verving de view-dropdown door verticale view-tabs in een horizontale
`subnav_row` boven het werkblad. Dat werkt functioneel, maar kost verticale
ruimte en splitst view-chrome over `subnav_row`, `top10_subbar`, LCC-filterbalk
boven de grafiek en dynamische `relocate_fm_metric_chrome`. Analisten willen
meer chart-/tabelhoogte, navigatie aan de zijkant van het resultaatgebied, en
één onderbalk voor filters en bediening (LCC-maatregeltypes onder elkaar
rechtsonder).

ADR-0019 regelde presentatielaag v1 (thema, StatusStrip, KPI als ingeklapte
overlay). Deze ADR regelt de **layout-shell v2** van de resultatenwerkruimte.

## Decision

### Drie zones in het werkblad

```
[PBS-zijbalk | detail_zone (inhoud + chrome-footer) | navigatierail]
```

- **PBS-zijbalk** blijft links (scope-selectie).
- **Navigatierail** rechts van `detail_zone`, vaste breedte ~144px v1 (niet
  inklapbaar in v1).
- **Werkruimte-chrome-footer** alleen onder `detail_zone`, niet onder PBS of rail.

### Navigatierail

- Bovenaan: **Werkruimte-zijde** (Input / Output) **onder elkaar**.
- Daaronder: view-tabs uit de view-registry voor de actieve zijde.
- Registry krijgt per entry een **rail-label** (smalle kolom) naast het bestaande
  **view-label** (Beeld-menu, tooltips).

| view_id | view-label | rail-label |
|---------|------------|------------|
| `output.kpi_overview` | KPI-overzicht | KPI |
| `output.lcc_plot` | LCC-plot | LCC |
| `output.ltap` | LTAP | LTAP |
| `output.fm_results` | Top bijdragen | TopX |
| `input.faalwijzen` | Faalwijzen | Faalw. |
| `input.rev_tasks` | REV-taken | REV |
| `input.effecten` | Effecten | Effect |
| `input.taakgroepen` | Taakgroepen | Groep |
| `input.correctief` | Correctief onderhoud | CM |

### KPI-overzicht = Output-view

- Nieuwe registry-entry `output.kpi_overview`; geen globale `kpi_panel`-rij meer.
- Geen `kpi_collapsed_in_lcc`-state; navigatie via rail, Beeld → Output of
  `Ctrl+K`.
- `toolbar_family: none` (lege chrome-footer).

Dit **wijzigt** ADR-0019 §KPI-overzicht (ingeklapte overlay): KPI is voortaan
een view, geen toggle boven alle modi.

### TopX vs Top 10 (slice 104)

- **TopX** is analist-taal en rail-label voor `output.fm_results` (sorteerbare
  faalwijze-tabel: grootste bijdragen vinden, rij openen om te bewerken).
- View-label in menu: **Top bijdragen** (geen «FM-resultaten» in de UI).
- `output.top_10` (Bijdragen-grafiek) blijft **gepensioneerd** (slice 104); TopX
  heractiveert die view niet.

### Werkruimte-chrome-footer

Eén footer onder `detail_zone`; orchestrator levert één plan (vervangt
`top10_subbar` + view-specifieke filterbalken + `relocate_fm_metric_chrome`).

**Drie vaste zones:**

| Zone | Inhoud |
|------|--------|
| Links | Context (view-label, overlay-status) |
| Midden | Gedeelde chrome per `toolbar_family` (metric, horizon, NB, what-if-knoppen) |
| Rechts | ~120px gereserveerd; LCC-maatregeltype-checkboxes **verticaal** bij `metric=kosten`; leeg bij andere views (geen verspringen) |

**LCC-planning split:**

- Footer: lichte bediening (what-if aan/uit, reset, presets) + maatregeltypes.
- Inhoud: meekoppelkansen-tabel collapsible boven grafiek; jaarverschuiving
  bij grafiekselectie blijft bij de grafiek.

## Alternatives considered

| Optie | Reden afgewezen |
|-------|-----------------|
| Rail links (tussen PBS en inhoud) | Botst met PBS-boom-mentaliteit; scope vs navigatie vermengd |
| Footer over volledige vensterbreedte | Filters onder PBS semantisch onjuist |
| KPI als overlay houden | Dubbele seam (toggle + views); blijft verticale ruimte kosten |
| TopX = herleven `output.top_10` | Slice 104-besluit; FM-tabel dekt ranking + bewerking in één view |
| Inklapbare rail v1 | Extra UX-complexiteit; v1 eerst stabiele vaste rail |
| Horizontale Input/Output in rail | Te krap bij 144px; labels afgekapt |

## Consequences

- `workspace_view_registry`: `rail_label` op `WorkspaceViewEntry`; KPI-entry;
  `output.fm_results` label → «Top bijdragen».
- Layout: `subnav_row` en globale `top10_subbar` verdwijnen; middenkolom =
  `detail_stack` + footer; rail uit `workspace_navigation_panel`.
- State/orchestrator: verwijder `kpi_collapsed_in_lcc`, `_plan_kpi_collapse`,
  `relocate_fm_metric_chrome`; nieuw `WorkspaceChromeFooterPlan`.
- Beeld-menu: checkable KPI-toggle vervalt; KPI via Output-submenu.
- Glossary in `CONTEXT.md` (Werkruimte-navigatierail, chrome-footer, rail-label,
  KPI als view, Top bijdragen/TopX).
- Implementatie na open HILT 103–105 (slice 107 in planning).

## References

- ADR-0019 — presentatielaag v1 (KPI-overlay hier superseded voor layout)
- ADR-0012 — LTAP preset-view (zelfde LCC-panel, rail-label LTAP)
- ADR-0005 — meekoppel in LCC-inhoud
- Slice 104 PRD — Top 10-afbouw (blijft van kracht; TopX ≠ Top 10)
- **ADR-0021** — chrome v2.1 (view-titel, footer zonder context, FM-inspectiemodus)
