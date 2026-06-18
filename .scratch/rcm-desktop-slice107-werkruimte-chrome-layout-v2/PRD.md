# PRD — Slice 107: Werkruimte chrome-layout v2

**Status:** ready-for-agent  
**Versie:** 1.0  
**Datum:** 2026-06-18  
**Triage:** `ready-for-agent`  
**Type:** UX-layout + adapter-orchestratie  
**Parent:** grill 107-A (2026-06-18); `/improve-codebase-architecture` advies werkruimte-navigatie; slice 105.31 (view-tabs in `subnav_row`); slice 104 (Top 10-afbouw, FM single-run); slice 106 (view_id canoniek, bind coordinators)  
**Companion docs:** ADR-0020 (werkruimte chrome-layout v2), ADR-0019 (presentatielaag v1 — KPI-overlay superseded), ADR-0012 (LTAP preset), ADR-0005 (meekoppel in LCC-inhoud), CONTEXT.md (Werkruimte-navigatierail, chrome-footer, rail-label, KPI-overzicht, Top bijdragen/TopX)

> Verplaatst view-navigatie naar een **rechter navigatierail**, bundelt view-chrome in één
> **chrome-footer** onder het inhoudsgebied, en maakt **KPI-overzicht** een gewone Output-view.
> Doel: meer verticale ruimte voor grafieken/tabellen, één bedieningslaag, Delta Pi huisstijl.

---

## Problem Statement

Na slice 105.31 werken Input/Output-view-tabs functioneel, maar de horizontale `subnav_row`
boven het werkblad kost waardevolle verticale ruimte. View-chrome is verspreid over meerdere
rijen (`subnav_row`, `top10_subbar`, LCC-filterbalk boven de grafiek, dynamische
`relocate_fm_metric_chrome`). Analisten moeten bij LCC eerst Output kiezen, dan LCC, en
daarna elders maatregeltypes filteren — niet intuïtief en niet gestapeld zoals gewenst.

KPI-overzicht leeft als globale overlay met een aparte Beeld-toggle (`kpi_collapsed_in_lcc`),
terwijl het inhoudelijk een Output-weergave is. Dat dubbele navigatiemodel kost ruimte en
complexiteit in state en orchestrator.

De maintenance engineer gebruikt de FM-resultatenview om **grootste bijdragen** te vinden;
de huidige naam «FM-resultaten» en het ontbreken van rail-labels maken de navigatie minder
scanbaar dan nodig.

---

## Solution

Implementeer ADR-0020: drie zones in het werkblad

```
[PBS-zijbalk | detail_zone (inhoud + chrome-footer) | navigatierail]
```

1. **Navigatierail** rechts van `detail_zone` (~144px, v1 niet inklapbaar): Input/Output
   **onder elkaar**, daaronder view-tabs met **rail-labels** (KPI, LCC, LTAP, TopX, …).
2. **Chrome-footer** alleen onder `detail_zone` met drie vaste zones (context | gedeelde
   chrome | rechterstack ~120px voor verticale LCC-maatregeltypes).
3. **KPI-overzicht** wordt `output.kpi_overview`; geen globale `kpi_panel`-rij meer.
4. **Top bijdragen** (`output.fm_results`) krijgt rail-label **TopX**; `output.top_10`
   blijft gepensioneerd.
5. Lichte LCC-planning (what-if aan/uit, reset, presets) + maatregeltypes in footer;
   meekoppelkansen-tabel blijft collapsible in het inhoudsgebied.

Visueel onderscheidend via Delta Pi tokens (`dp_tokens`, `rcm2.qss`); navigatierail en
footer zijn geen generieke Qt-defaults.

---

## User Stories

### Navigatierail en layout

1. As a maintenance engineer, I want view-tabs rechts naast mijn resultaten, so that ik meer hoogte overhoud voor grafieken en tabellen.
2. As a maintenance engineer, I want Input en Output duidelijk onder elkaar in de rail, so that ik snel zie welke zijde actief is zonder afgekapte labels.
3. As a maintenance engineer, I want korte rail-labels (KPI, LCC, LTAP, TopX), so that ik views in één oogopslag herken in de smalle kolom.
4. As a maintenance engineer, I want het volledige view-label in het Beeld-menu en tooltips, so that ik bij twijfel de volledige naam zie (bv. «Top bijdragen»).
5. As a maintenance engineer, I want de PBS-boom links en view-navigatie rechts gescheiden, so that scope-selectie en view-wissel niet door elkaar lopen.
6. As a maintenance engineer, I want de navigatierail een vaste breedte, so that de inhoud niet springt bij view-wissel.
7. As a maintenance engineer, I want sticky view per zijde behouden, so that terugschakelen naar Input mijn laatste invoertabel herstelt.
8. As a maintenance engineer, I want `Ctrl+1` / `Ctrl+2` nog steeds Input/Output te schakelen, so that mijn gewoontes werken.
9. As a maintenance engineer, I want view-sneltoetsen (`Ctrl+Alt+…`) nog te werken, so that ik snel naar LCC, LTAP of TopX kan.
10. As a maintenance engineer, I want de rail visueel in Delta Pi huisstijl, so that de werkruimte consistent aanvoelt met de rest van RCM2.

### Chrome-footer

11. As a maintenance engineer, I want alle view-filters en metric/horizon-bediening in één onderbalk, so that ik niet meer omhoog hoef te zoeken.
12. As a maintenance engineer, I want de footer alleen onder mijn actieve view-inhoud, so that filters niet onder de PBS-boom verschijnen.
13. As a maintenance engineer, I want links in de footer context (view-naam, overlay-status), so that ik weet welke view ik bedien.
14. As a maintenance engineer, I want in het midden gedeelde chrome (metric, horizon, NB-filter, what-if-knoppen), so that bekende controls op één plek blijven.
15. As a maintenance engineer, I want rechts een vaste smalle kolom, so that de layout niet verspringt als een view geen rechter-filters heeft.
16. As a maintenance engineer, I want LCC-maatregeltype-checkboxes verticaal gestapeld rechtsonder, so that ik snel PM/CM/REV/etc. kan aan- en uitzetten.
17. As a maintenance engineer, I want LCC what-if aan/uit, reset en presets in de footer, so that lichte planningbediening altijd bereikbaar is.
18. As a maintenance engineer, I want de meekoppelkansen-tabel boven de LCC-grafiek te houden, so that ik complexe koppelingen in context van de curve zie.
19. As a maintenance engineer, I want jaarverschuiving bij grafiekselectie bij de grafiek te blijven, so that cause-effect dicht bij de data staat.
20. As a maintenance engineer, I want TopX (FM-resultaten) metric, horizon, NB en inspector-chrome in de footer, so that ik bijdragen kan sorteren zonder aparte subbar.
21. As a maintenance engineer, I want Input-grid-views geen overbodige footer-chrome te tonen, so that tabellen maximaal ruimte krijgen.
22. As a maintenance engineer, I want LTAP dezelfde LCC-footer te gebruiken met CM preset uit, so that LTAP-gedrag (ADR-0012) behouden blijft.

### KPI als Output-view

23. As a maintenance engineer, I want KPI-overzicht als gewone Output-view (rail-label KPI), so that ik het net als LCC of TopX kan kiezen.
24. As a maintenance engineer, I want `Ctrl+K` naar KPI-overzicht te navigeren, so that mijn sneltoets behouden blijft.
25. As a maintenance engineer, I want geen aparte «KPI zichtbaar»-toggle meer in Beeld, so that er één navigatiemodel is.
26. As a maintenance engineer, I want KPI geen extra footer-chrome te tonen, so that de compacte tabel de ruimte krijgt.
27. As a maintenance engineer, I want vanuit KPI naar LCC te kunnen zonder overlay-gedrag, so that view-wissel voorspelbaar is.

### Top bijdragen / TopX

28. As a maintenance engineer, I want de Output-view «Top bijdragen» te heten in menu's, so that duidelijk is dat ik grootste bijdragers zoek.
29. As a maintenance engineer, I want rail-label TopX voor deze view, so that de smalle rail scanbaar blijft.
30. As a maintenance engineer, I want vanuit TopX een rij te openen en te bewerken, so that ranking en editing in één workflow blijven (slice 104-gedrag).
31. As a maintenance engineer, I want geen terugkeer van de oude Top-10-grafiekview, so that slice 104-besluit intact blijft.

### Input-views

32. As a maintenance engineer, I want Input-rail-labels Faalw., REV, Effect, Groep, CM, so that invoertabellen compact navigeerbaar zijn.
33. As a maintenance engineer, I want Faalwijzen-view de FM-input-chrome in de footer, so that nieuw/verwijderen/batch-acties bereikbaar blijven.

### Regressie en pariteit

34. As a developer, I want bestaande orchestrator-chrome-profielen hergebruikt, so that view-specifiek gedrag declaratief blijft.
35. As a developer, I want `subnav_row` en globale `top10_subbar` verwijderd, so that er één chrome-pad is.
36. As a developer, I want `kpi_collapsed_in_lcc` en `relocate_fm_metric_chrome` verwijderd, so that state en views eenvoudiger worden.
37. As a QA analyst, I want pytest-regressie op adapter-plannen en venster-layout, so that layout-refactor veilig mergebaar is.
38. As a QA analyst, I want een HILT-handcheck voor rail, footer en KPI-navigatie, so that visuele Delta Pi-kwaliteit bevestigd wordt.

### Randgevallen

39. As a maintenance engineer, I want bij vergelijkingsmodus dezelfde layout-shell, so that A/B-werk niet afwijkt (pariteit met enkel-model).
40. As a maintenance engineer, I want bij smalle vensterbreedte de rail leesbaar te houden, so that ik op laptop kan werken.
41. As a maintenance engineer, I want disabled/retired views niet in de rail, so that `output.top_10` niet terugkomt.
42. As a maintenance engineer, I want overlay-status (run, validatie) in footer-context zichtbaar waar relevant, so that ik run-state zie zonder extra rijen.

---

## Implementation Decisions

### Tranche-volgorde

| Tranche | Doel | Primaire modules |
|---------|------|------------------|
| **107-A** | Grill + ADR | ADR-0020, CONTEXT.md — **done** |
| **107-B** | View-registry + KPI-entry | `workspace_view_registry`, `messages` |
| **107-C** | State + menu | `results_workspace_state`, `workspace_menu_spec`, binding |
| **107-D** | Chrome-footer plan | `ResultsWorkspaceOrchestrator`, `WorkspaceChromeFooterPlan` |
| **107-E** | Layout-shell | `results_workspace_window`, detail-zone compositie |
| **107-F** | Navigatierail UI | `workspace_navigation_panel`, QSS tokens |
| **107-G** | Footer panel + bindings | nieuw footer-panel; migreer top10/LCC/FM chrome |
| **107-H** | LCC rechterstack + what-if licht | LCC footer zones, verticale checkboxes |
| **107-I** | HILT + regressie | handcheck, pytest subset |

### View-registry

- `WorkspaceViewEntry` krijgt optioneel `rail_label: str`.
- Nieuwe entry `output.kpi_overview`: order vóór LCC, shortcut `Ctrl+K`, `toolbar_family: none`.
- `output.fm_results`: view-label → «Top bijdragen», `rail_label` → «TopX».
- Rail-labels volgens ADR-0020-tabel; Input: Faalw., REV, Effect, Groep, CM.
- `enabled_views_for_side` en menu-spec genereren uit registry; retired `output.top_10` blijft `enabled=False`.

### State en navigatie

- Verwijder `kpi_collapsed_in_lcc`, `set_kpi_collapsed_in_lcc`, `_plan_kpi_collapse`.
- `Ctrl+K` en oude `view.kpi_overview_visible` routen naar `set_active_view("output.kpi_overview")` + Output-zijde.
- Sticky per zijde via bestaande `active_view_id`-mechanisme (slice 106).
- Default Output-view kan `output.fm_results` blijven; KPI is expliciete navigatie.

### Orchestrator

- Nieuw `WorkspaceChromeFooterPlan` (of uitbreiding `UiSyncPlan`) met:
  - `footer_visible: bool`
  - `context_label: str`
  - `toolbar_family` + bestaande `plan_chrome_toolbar` output (metric, horizon, NB, FM, LCC)
  - `right_stack: LccMeasureTypeStack | EmptyRightStack` — verticale PM-type filters bij LCC/LTAP + metric=kosten
  - `what_if_light: WhatIfLightPlan | None` — toggle/reset/presets in footer
- Verwijder `top10_subbar_visible`, `_plan_top10_subbar_visible` uit publieke plan.
- Meekoppel-panel visibility blijft inhoudsplan (`meekoppel_panel_visible`), niet footer.

### Layout-shell (views)

- `main_splitter`: `[pbs_sidebar | center_column | navigatierail]`.
- `center_column`: verticaal `[detail_stack (stretch=1) | chrome_footer]`.
- Verwijder `subnav_row`, globale `top10_subbar`, globale `kpi_panel` uit outer layout.
- `relocate_fm_metric_chrome` vervalt; FM metric/horizon permanent in footer via plan.

### Navigatierail UI

- Hergebruik `workspace_navigation_panel` concept; layout **verticaal**: side buttons stacked, view tabs stacked.
- `objectName`/`QSS`: `WorkspaceNavRail`, `WorkspaceSideTab`, `WorkspaceViewTab` — Delta Pi accent voor actieve tab.
- Vaste `minimumWidth`/`maximumWidth` ~144px op rail-widget.

### Chrome-footer UI

- Nieuw panel (bv. `workspace_chrome_footer_panel`) met drie zones; bindings in dedicated binding-module.
- Migreer widgets uit `top10_subbar_panel` en LCC filter bar (licht deel) naar footer zones.
- Rechterstack: `QVBoxLayout` met maatregeltype-checkboxes; alleen zichtbaar bij LCC-plan; kolom blijft gereserveerd.

### Menu en messages

- Verwijder checkable `view.kpi_overview_visible` uit `workspace_menu_spec`; KPI onder Beeld → Output.
- Update `messages` voor «Top bijdragen», rail-labels waar niet hardcoded in registry.

### QSS / thema

- Tokens voor rail-achtergrond, actieve tab, footer-scheiding; consistent met slice 102 presentatielaag.
- Geen nieuwe kleuren buiten `dp_tokens.py`.

---

## Testing Decisions

**Principe:** test extern gedrag op de **hoogst mogelijke seam**; views alleen waar layout-zichtbaarheid Qt vereist.

| Seam | Wat testen | Prior art |
|------|------------|-----------|
| `workspace_view_registry` | `rail_label` aanwezig; KPI-entry; Top bijdragen label; enabled/retired | `test_slice79_view_registry.py` |
| `results_workspace_state` | geen `kpi_collapsed_in_lcc`; `Ctrl+K` → `output.kpi_overview` | `test_desktop_results_workspace_state.py`, `test_slice106_view_id_canonical.py` |
| `workspace_menu_spec` | geen KPI-toggle; KPI in Output-submenu | `test_slice76_workspace_menu_spec.py` |
| `ResultsWorkspaceOrchestrator` | `WorkspaceChromeFooterPlan` per view; LCC rechterstack; FM footer; KPI leeg | `test_slice105_chrome_toolbar.py`, `test_results_workspace_orchestrator.py` |
| Venster (pytest-qt) | geen `subnav_row`/`top10_subbar`/`kpi_panel` in layout; rail + footer zichtbaar; view-wissel update footer | `test_desktop_results_workspace_window.py`, `test_slice102_theme_shell.py` |
| LCC footer | verticale checkboxes rechts; what-if licht in midden | `test_slice105_lcc_pm_type_filter.py` |

**Nieuwe testbestanden (voorstel):**

- `test_slice107_view_registry_rail.py` — registry + rail_label
- `test_slice107_chrome_footer_plan.py` — orchestrator plan
- `test_slice107_layout_shell.py` — venster widget-tree + zichtbaarheid
- `test_slice107_kpi_as_view.py` — navigatie + menu migratie

**Geen tests op:** exacte pixelposities, interne layout-marges, QSS-kleurwaarden (HILT).

**Regressie-gate per tranche:** zie `KANBAN_HANDOFF.md`.

---

## Out of Scope

- Inklapbare navigatierail (v2-backlog).
- Rail links van inhoud (afgewezen ADR-0020).
- Footer over volledige vensterbreedte (afgewezen).
- Herintroductie `output.top_10` / Bijdragen-grafiek.
- Volledige what-if-werkruimte-modus (grill P2 slice 105 issue 14–15).
- FM-inspector visuele polish (needs-triage 105.14).
- Filter in diagramweergave (needs-triage 105.15).
- Vergelijkingswerkruimte layout-redesign (alleen pariteit behouden).
- ValidateWindow retirement tranche 2.
- Portfolio/bibliotheek fase F.

---

## Further Notes

- **Blocked by:** open HILT re-checks slice 103–105 aanbevolen vóór merge; geen harde technische blocker op 107-B start.
- **ADR-0019:** KPI-overlay-paragraaf is superseded voor layout; thema/KPI-tabel-inhoud blijft.
- **Slice 106:** `active_view_id` canoniek — 107 bouwt daarop; geen terugkeer naar modus-first navigatie.
- **Line budget:** `results_workspace_window` mag krimpen door verwijderen subnav/top10/kpi; nieuwe footer/rail in panelen.
- **HILT107:** visuele check rail (144px, labels, actieve staat), footer drie zones, LCC verticale stack, KPI als view, TopX label.
