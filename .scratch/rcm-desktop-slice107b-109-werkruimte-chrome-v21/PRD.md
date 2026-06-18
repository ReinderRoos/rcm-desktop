# PRD — Slice 107-B / 108 / 109: Werkruimte chrome v2.1 + FM-inspectiemodus

**Status:** ready-for-agent  
**Versie:** 1.0  
**Datum:** 2026-06-18  
**Triage:** `ready-for-agent`  
**Type:** UX-layout + adapter-orchestratie + FM-validatie  
**Parent:** HILT107 grill (post slice 107); ADR-0021; amends ADR-0020 footer/rail  
**Companion docs:** ADR-0021 (werkruimte chrome v2.1 + FM-inspectiemodus), ADR-0020 (chrome-layout v2 — footer/rail deels superseded), ADR-0019 (presentatielaag), slice 34 (FM-verificatie), slice 104 (Top bijdragen single-run diagram), slice 107 (navigatierail + chrome-footer), CONTEXT.md (View-titel, FM-inspector, Faalwijze-editor openen)

> Verfijnt slice 107 na HILT107: **view-titel** boven inhoud, **twee-zone footer**,
> **bredere Input-rail**, en een herontworpen **FM-inspectiemodus** met LCC-plot per
> faalwijze. Herstructureert **faalwijze-editor-ingangen**: Input primair, Output
> via inspector-knop. Drie vertical tracer bullets: **107-B** (layout) → **108**
> (inspector + plot) → **109** (editor-paden).

---

## Problem Statement

Slice 107 leverde navigatierail en chrome-footer, maar HILT107 toonde vier structurele
problemen:

1. **Oriëntatie:** het view-label («Top bijdragen», «LCC-plot») staat te klein links in
   de footer. Analisten willen een prominente kop **boven** de inhoud; de footer is
   bedoeld voor bediening, niet voor context.
2. **Input-navigatie:** rail-labels voor Input-views zijn te compact; leesbare
   bedieningslabels (Faalwijzen, REV, Effect, …) passen niet in ~144px.
3. **FM-validatie:** de FM-inspector toont een jaartabel; analisten willen op
   faalwijze-niveau een **LCC-plot** (faalmomenten, NB, kosten CM+PM) gekoppeld aan
   dezelfde metric/horizon/NB-filters als de hoofdtabel — om simulatie te nagelopen.
4. **Verwarrende ingangen:** enkele selectie opent de inspector; dubbelklik op Top
   bijdragen opent de editor. Tegelijk opent dubbelklik op Input → Faalwijzen **niet**
   de editor. Analyse (Output) en bewerken (Input) lopen door elkaar.

---

## Solution

Implementeer ADR-0021 in drie vertical slices:

### Slice 107-B — Chrome v2.1 (layout)

```
[view-titel — volledig registry-label]
[detail_zone inhoud]
[chrome-footer: midden (gedeelde chrome) | rechts (~120px filters)]
[PBS | center_column | navigatierail ~160px]
```

- **View-titel** boven `detail_zone`; overlay-status (what-if actief) blijft in footer
  of statusstrip, niet in de titel.
- **Footer:** verwijder linker context-zone; midden + rechts blijven zoals slice 107.
- **Navigatierail:** ~160px; groter lettertype; Output houdt compacte codes (KPI, LCC,
  LTAP, TopX); Input krijgt bedieningslabels (Faalwijzen, REV, Effect, Taakgroep,
  Correctief).

### Slice 108 — FM-inspectiemodus + LCC-plot

Alleen in **Top bijdragen → tabelweergave**:

| Actie | Gedrag |
|-------|--------|
| Dubbelklik op rij | Opent inspectiemodus |
| Enkele selectie | Opent inspector **niet** |
| Tabel | Contextvenster max. 3 rijen (boven · geselecteerd · onder); geen placeholders |
| Pijl omhoog/omlaag | Vorige/volgende FM in gefilterde lijst |
| Sluiten | Volledige gefilterde tabel terug |
| Diagram-toggle | Sluit inspectiemodus automatisch |
| Inspector-onder | Lifecycle, reconcile, hash, **LCC-plot faalwijze-niveau**, knop **Bewerken…** |

Plot-semantiek (zelfde filters als hoofdtabel):

- **Faalmomenten / NB:** enkelvoudige reeks per kalenderjaar
- **Kosten:** CM + PM gestapeld per jaar (PM-serie via adapter)

Top bijdragen-diagram (Top-N staafdiagram) blijft naast tabel via toggle; polish waar
HILT diagram-view miste.

### Slice 109 — Faalwijze-editor ingangen

| Pad | Actie |
|-----|--------|
| Input → Faalwijzen | Dubbelklik → faalwijze-editor |
| Top bijdragen → FM-inspector | Knop **Bewerken…** → editor |
| Top bijdragen dubbelklik | Inspectiemodus only (**geen** directe editor) |

Overige Input-views: grid-only tot entity-editors bestaan.

---

## User Stories

### View-titel en chrome v2.1 (107-B)

1. As a maintenance engineer, I want het volledige view-label prominent boven mijn inhoud, so that ik direct weet welke view actief is zonder in de footer te kijken.
2. As a maintenance engineer, I want «Top bijdragen» in groot lettertype boven tabel of diagram, so that de view-naam scanbaar is tijdens analyse.
3. As a maintenance engineer, I want de view-titel bij elke Output- en Input-view, so that oriëntatie consistent is over KPI, LCC, LTAP, Top bijdragen en invoer-tabellen.
4. As a maintenance engineer, I want overlay-status (what-if actief) **niet** in de view-titel, so that de titel stabiel blijft terwijl sessiestatus elders zichtbaar is.
5. As a maintenance engineer, I want de chrome-footer zonder view-naam links, so that de footer puur bediening blijft.
6. As a maintenance engineer, I want metric, horizon, NB-filter en what-if-knoppen nog in het midden van de footer, so that bekende controls op één plek blijven.
7. As a maintenance engineer, I want LCC-maatregeltypes verticaal rechts in de footer, so that het filtergedrag van slice 107 behouden blijft.
8. As a maintenance engineer, I want de rechter footer-kolom gereserveerd (~120px) ook als een view geen rechter-filters heeft, so that de layout niet springt bij view-wissel.
9. As a maintenance engineer, I want Input-rail-labels leesbaar (Faalwijzen, REV, Effect, Taakgroep, Correctief), so that ik invoer-views herken zonder afgekapte tekst.
10. As a maintenance engineer, I want Output-rail-labels compact (KPI, LCC, LTAP, TopX), so that de smalle codes scanbaar blijven.
11. As a maintenance engineer, I want een bredere navigatierail (~160px), so that Input-labels passen zonder ellipsis.
12. As a maintenance engineer, I want groter lettertype op rail-tabs, so that navigatie comfortabeler is na HILT-feedback.
13. As a maintenance engineer, I want formele view-labels nog in Beeld-menu en tooltips, so that ik bij twijfel «REV-taken» vs rail-label «REV» kan verifiëren.
14. As a maintenance engineer, I want Delta Pi huisstijl op view-titel en rail-polish, so that het visueel aansluit op slice 102/107.
15. As a maintenance engineer, I want view-wissel de titel direct bij te werken, so that ik nooit een verkeerde kop zie.

### FM-inspectiemodus — openen en navigatie (108)

16. As a maintenance engineer, I want inspectiemodus alleen in tabelweergave, so that diagram en inspector elkaar niet overlappen.
17. As a maintenance engineer, I want inspectiemodus openen met dubbelklik op een FM-rij, so that enkele selectie vrij blijft voor tabel-navigatie.
18. As a maintenance engineer, I want enkele rij-selectie de inspector **niet** automatisch te openen, so that ik door de tabel kan bladeren zonder steeds het detailpaneel te activeren.
19. As a maintenance engineer, I want bij open inspectiemodus maximaal drie rijen in de tabel (boven · geselecteerd · onder), so that ik context zie zonder de hele lijst te verliezen.
20. As a maintenance engineer, I want geen placeholder-rijen aan de rand van de gefilterde lijst, so that lege rijen niet als kapotte data voelen.
21. As a maintenance engineer, I want bij één of twee rijen totaal alle beschikbare rijen te zien, so that kleine scopes nog bruikbaar zijn.
22. As a maintenance engineer, I want pijl omhoog/omlaag naar vorige/volgende FM in de gefilterde lijst, so that ik snel door kandidaten kan stappen.
23. As a maintenance engineer, I want sluiten de volledige gefilterde tabel terug te brengen, so that ik na validatie verder kan met ranking-analyse.
24. As a maintenance engineer, I want schakelen naar Top bijdragen-diagram inspectiemodus automatisch te sluiten, so that diagram en inspector niet tegelijk actief zijn.
25. As a maintenance engineer, I want terugschakelen naar tabelweergave zonder actieve inspectiemodus, so that ik een schone tabelstart heb na diagram-gebruik.
26. As a maintenance engineer, I want inspectiemodus te behouden bij filter-wijziging alleen wanneer de geselecteerde FM nog in de gefilterde lijst zit, so that ik niet onverwacht in een lege staat beland.
27. As a maintenance engineer, I want inspectiemodus te sluiten wanneer de geselecteerde FM uit filter valt, so that context en data consistent blijven.
28. As a maintenance engineer, I want scope-wissel (PBS) inspectiemodus te resetten, so that ik geen FM uit vorige scope valideer.

### FM-inspectiemodus — inhoud en plot (108)

29. As a maintenance engineer, I want onder de context-tabel lifecycle-totalen van de geselecteerde FM, so that ik snel totalen zie vóór de tijdreeks.
30. As a maintenance engineer, I want reconcile-status en FM-invoerhash in het inspector-paneel, so that ik invoer en motor-resultaat kan verifiëren (slice 34-pariteit).
31. As a maintenance engineer, I want een LCC-plot op faalwijze-niveau i.p.v. de jaartabel, so that ik de simulatie visueel kan nagelopen.
32. As a maintenance engineer, I want de FM-LCC-plot dezelfde metric te volgen als de hoofdtabel (faalmomenten, NB, kosten), so that ik geen dubbele filterkeuzes hoef te onthouden.
33. As a maintenance engineer, I want de FM-LCC-plot dezelfde horizon te volgen (lifecycle / per jaar), so that tabel en plot consistent zijn.
34. As a maintenance engineer, I want de FM-LCC-plot het NB-effectfilter te respecteren, so that NB-validatie op dezelfde deelselectie gebeurt.
35. As a maintenance engineer, I want faalmomenten als enkelvoudige reeks per kalenderjaar in de FM-plot, so that ik faalfrequentie over de horizon zie.
36. As a maintenance engineer, I want niet-beschikbaarheid als enkelvoudige reeks per kalenderjaar, so that ik downtime per jaar kan verifiëren.
37. As a maintenance engineer, I want kosten als CM + PM gestapeld per jaar in de FM-plot, so that ik beide kostencomponenten zie (niet alleen CM).
38. As a maintenance engineer, I want kalenderjaar-mapping identiek aan project-LCC (modeljaar + horizonindex), so that er geen tweede jaarberekening ontstaat.
39. As a maintenance engineer, I want presentatie-proxy data (geen tweede motor-run), so that validatie snel en deterministisch blijft.
40. As a maintenance engineer, I want een duidelijke melding wanneer plot-data ontbreekt (geen run, geen profiel), so that ik weet waarom de plot leeg is.
41. As a maintenance engineer, I want een knop **Bewerken…** in het inspector-paneel, so that ik na validatie bewust naar de editor kan.

### Top bijdragen-diagram (108)

42. As a maintenance engineer, I want Top bijdragen-diagram beschikbaar via tabel/diagram-toggle, so that ik ranking visueel én tabellarisch kan bekijken.
43. As a maintenance engineer, I want het Top-N staafdiagram ranking op de actieve metric, so that het diagram aansluit op sortering en metric-keuze.
44. As a maintenance engineer, I want diagram-view zonder actieve inspectiemodus, so that het scherm overzichtelijk blijft.
45. As a maintenance engineer, I want metric/horizon/NB-filters in diagramweergave via footer-chrome, so that ik het diagram kan sturen zoals de tabel.

### Faalwijze-editor ingangen (109)

46. As a maintenance engineer, I want dubbelklik op Input → Faalwijzen de faalwijze-editor te openen, so that bewerken logisch start bij invoer.
47. As a maintenance engineer, I want dubbelklik op Top bijdragen **geen** editor te openen, so that Output gereserveerd blijft voor analyse.
48. As a maintenance engineer, I want **Bewerken…** in FM-inspector de editor te openen voor de geïnspecteerde FM, so that ik na validatie kan bijsturen.
49. As a maintenance engineer, I want de editor de juiste FM-scope te laden ongeacht ingang, so that bewerken consistent is (slice 44-pariteit).
50. As a maintenance engineer, I want overige Input-views (REV, Effect, Taakgroep, Correctief) nog grid-only zonder dubbelklik-editor, so that er geen half-werkende editors verschijnen.
51. As a maintenance engineer, I want compare-modus dubbelklik-gedrag ongewijzigd pariteit te houden waar van toepassing, so that vergelijking niet regressie krijgt.

### Regressie en pariteit

52. As a maintenance engineer, I want sticky view per zijde behouden, so that terug naar Input mijn laatste tabel herstelt.
53. As a maintenance engineer, I want sneltoetsen (`Ctrl+1`/`Ctrl+2`, `Ctrl+Alt+…`) intact, so that mijn workflow niet verandert.
54. As a maintenance engineer, I want KPI/LCC/LTAP-footer-gedrag van slice 107 intact, so that alleen layout en FM-flow wijzigen.
55. As a maintenance engineer, I want vergelijkingswerkruimte FM-chrome pariteit te behouden waar ADR-0021 single-run scoped is, so that compare niet onbedoeld breekt.

---

## Implementation Decisions

### Vertical slice-volgorde

| Slice | Scope | Afhankelijkheid |
|-------|--------|-----------------|
| **107-B** | View-titel, footer twee zones, rail ~160px + Input-labels + QSS | slice 107 merged |
| **108** | Inspectiemodus state machine, 3-rijen-filter, FM-LCC-plot, diagram-sluit-inspector, Bewerken-knop UI | 107-B |
| **109** | Input dubbelklik → editor; Top bijdragen dubbelklik → inspector only; wiring Bewerken… | 108 |

### Chrome v2.1 (107-B)

- **View-titel plan** — Orchestrator levert `view_title` (volledig registry-label) en
  `view_title_visible` per actieve view; venster bindt label boven `detail_zone`.
  Geen context in `WorkspaceChromeFooterPlan.context_label` (veld deprecate of leeg).
- **Footer zones** — Verwijder `chrome_footer_context_label` uit layout of permanent
  hidden; `build_chrome_footer_zones` wordt twee-zone (midden + rechts).
- **Registry** — Input-entries krijgen `rail_label` bedieningslabels; constante
  `WORKSPACE_NAV_RAIL_WIDTH_PX` → ~160.
- **QSS** — ObjectName voor view-titel (`WorkspaceViewTitle`); rail font-size bump;
  tokens via `dp_tokens.py`.

### FM-inspectiemodus state (108)

- **Snapshot-velden** (uitbreiding `WorkspaceStateSnapshot`):
  - `fm_inspector_mode: bool` — inspectiemodus actief (vs alleen dismissed-flag)
  - `fm_inspector_fm_id: str | None` — geïnspecteerde FM
  - Bestaand `fm_inspector_dismissed` herinterpreteren of vervangen door mode-flag
- **Open trigger** — `doubleClicked` op FM-tabel; verwijder
  `selectionChanged → refresh_fm_inspector` als auto-open.
- **3-rijen-filter** — Adapter-service `filter_fm_table_context_rows(filtered_rows,
  selected_fm_id) → tuple[row,…]` (max 3, geen placeholders); proxy of
  tijdelijk model op view-laag.
- **Navigatie** — Key handler ↑/↓ roept state `step_fm_inspector(-1|+1)` aan over
  gefilterde `fm_id`-volgorde.
- **Diagram** — `set_fm_view_mode(DIAGRAM)` zet `fm_inspector_mode=False` en
  herstelt volledige tabel-proxy.
- **Orchestrator** — `fm_inspector_visible` alleen als `fm_inspector_mode and
  fm_view_mode==TABLE and not compare`; update `FmToolbarPlan`.

### FM-LCC-plot (108)

- **Nieuwe adapter-service** — bv. `build_fm_lcc_plot_series(project, run, fm_id,
  presentation, nb_filter) → FmLccPlotSeries` met jaar-as, enkelvoudige reeks
  (faalmomenten/NB) of CM+PM stacks (kosten). Presentatie-proxy; hergebruik
  horizon-mapping uit `contribution_horizon_value_service` / LCC-kalenderjaar-logica.
- **Widget** — Hergebruik `LCCStackedBarChartWidget` of dedicated FM-variant in
  inspector-paneel; vervang `fm_inspector_year_table_view` als primaire viz (tabel
  mag verwijderd of achter feature-flag/debug).
- **Binding** — `fm_inspector_binding` voedt plot vanuit service + snapshot filters;
  metric/horizon/NB-wijziging → plot refresh.

### Top bijdragen-diagram (108)

- Bestaande `FaalwijzeCompareBarChartWidget` / single-run diagram binding behouden;
  fix zichtbaarheid wanneer HILT diagram-view ontbrak (toggle + orchestrator plan).
- Inspector-container **niet** zichtbaar in diagram-modus (invert slice 105.02
  gedrag).

### Faalwijze-editor ingangen (109)

- **Input** — `entity_grid_binding` of venster-handler: `doubleClicked` op
  `input.faalwijzen` → bestaande `_open_fm_editor(fm_id)` (slice 44-pad).
- **Output** — `_on_fm_table_double_clicked` wijzigt van editor-open naar
  `open_fm_inspector_mode(fm_id)`; editor alleen via inspector **Bewerken…**.
- **Compare** — Compare-tabel dubbelklik: behoud editor of inspector volgens
  bestaande compare-spec; documenteer in issue.

### Modules (indicatief)

| Laag | Wijzigingen |
|------|-------------|
| `workspace_view_registry` | Input rail_labels, rail width constant |
| `results_workspace_state` | inspector mode + fm_id; step/nav API |
| `results_workspace_orchestrator` | view title plan, footer plan zonder context, fm inspector visibility |
| `faalwijze_analyse_service` / nieuw FM-LCC service | context-row filter, plot series |
| `fm_inspector_binding`, `fm_detail_workspace_*` | plot, Bewerken-knop, geen auto-select open |
| `results_workspace_window` | view title widget, double-click handlers, key nav |
| `workspace_chrome_footer_binding` | twee zones |
| `entity_grid_binding` / input handlers | Faalwijzen double-click editor |
| `dp_tokens`, `rcm2.qss` | view-titel + rail typography |

---

## Testing Decisions

**Principe:** test extern gedrag op de **hoogst mogelijke seam**; pytest-qt alleen
waar widget-zichtbaarheid of events nodig zijn. Geen pixel/QSS-kleur asserts (HILT).

### Voorgestelde seams

| Seam | Wat testen | Prior art |
|------|------------|-----------|
| `workspace_view_registry` | Input `rail_label` bedieningslabels; rail width ~160 | `test_slice107_view_registry_rail.py` |
| `results_workspace_state` | `fm_inspector_mode`, open/close/step, diagram reset | `test_slice105_fm_view_state.py` |
| `results_workspace_orchestrator` | `view_title` in UI-plan; footer zonder context; inspector alleen table+mode | `test_slice107_chrome_footer_plan.py`, `test_slice105_chrome_toolbar.py` |
| FM context-row service | 3-rijen-filter, randen, 1–2 rijen | nieuw — pure adapter tests |
| FM-LCC plot service | metric→reeks type; kosten CM+PM; NB-filter doorgeven; horizon | `test_contribution_horizon_*`, LCC adapter tests |
| Venster (pytest-qt) | view-titel tekst per view; footer geen context label; dubbelklik opent inspector niet bij select; diagram sluit inspector | `test_desktop_results_workspace_window.py`, `test_slice105_fm_inspector_diagram.py` (invert/update) |
| Input grid | Faalwijzen double-click → editor dialog | `test_slice83_entity_grid.py`, `test_slice103_fm_detail_ui.py` |
| Top bijdragen | double-click opent geen editor; Bewerken… wel | `test_fm_double_click_opens_editor_only_in_fm_detail` (update) |

### Nieuwe testbestanden (voorstel)

| Bestand | Slice | Focus |
|---------|-------|-------|
| `test_slice107b_view_title_plan.py` | 107-B | orchestrator view title + footer zonder context |
| `test_slice107b_layout_shell.py` | 107-B | venster: titel zichtbaar, footer twee zones |
| `test_slice107b_input_rail_labels.py` | 107-B | registry + rail breedte |
| `test_slice108_fm_inspector_mode.py` | 108 | state open/close/step/diagram-reset |
| `test_slice108_fm_context_rows.py` | 108 | 3-rijen-filter adapter |
| `test_slice108_fm_lcc_plot_series.py` | 108 | plot data per metric |
| `test_slice108_fm_inspector_window.py` | 108 | pytest-qt dubbelklik, pijltjes, diagram |
| `test_slice109_input_faalwijzen_editor.py` | 109 | Input double-click editor |
| `test_slice109_topx_editor_paths.py` | 109 | Top bijdragen geen editor; Bewerken… wel |

**Regressie:** bestaande slice 107-tests blijven groen; `test_slice105_fm_inspector_diagram.py`
 wordt aangepast (inspector **niet** zichtbaar in diagram). `selectionChanged`-inspector
 tests verwijderen of omkeren.

**Seam-check (verwachting):** adapter/state/orchestrator voor layout en inspector-logica;
 venster voor dubbelklik, titel-widget en diagram-toggle. Geen tests op interne
 splitter-marges.

---

## Out of Scope

- Inklapbare navigatierail.
- View-titel in vergelijkingswerkruimte redesign (alleen pariteit single-run).
- Entity-editors voor REV/Effect/Taakgroep/Correctief (dubbelklik).
- Volledige what-if-werkruimte-modus (slice 105 backlog).
- Filter in Top bijdragen-diagram (needs-triage 105.15) — tenzij HILT-blokker.
- FM-inspector in compare-modus (tenzij expliciet later).
- Jaartabel in inspector als alternatieve weergave (vervangen door plot).
- ValidateWindow retirement.
- Portfolio/bibliotheek fase F.

---

## Further Notes

- **Blocked by:** slice 107 merge/afronding; geen harde technische blocker op 107-B.
- **ADR-0020:** footer drie zones → twee zones; context → view-titel; rail 144→160px.
- **ADR-0021:** bron van waarheid voor inspector-gedrag en editor-paden.
- **HILT108/109:** visuele check view-titel typografie, 3-rijen-context, FM-LCC-plot
  filter-koppeling, Input dubbelklik editor, Top bijdragen dubbelklik ≠ editor.
- **Line budget:** view-titel in dedicated panel/binding; FM-LCC service houdt
  `faalwijze_analyse_service` / inspector-binding dun.
- **Deletion:** `fm_inspector_year_table_view` primary path; `selectionChanged` auto-open;
  footer context label; Top bijdragen double-click → editor.
