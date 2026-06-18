# PRD — RCM2 desktop slice 57 (gestandaardiseerde werkruimte-rapportage)

**Status:** ready-for-agent  
**Versie:** 1.0  
**Triage-labels:** ready-for-agent  
**Type:** Feature (adapter + view; geen schema-drift op `RCMProject`)  
**Parent:** grill-me sessie rapportage (2026-06-02); bouwt voort op slice 23 (werkruimte), slice 33 (Top10-modi), slice 56 (A/B-compare), slice 52 (projectmetadata, optioneel)  
**Relatie:** ADR-0007 (bevroren A/B-slots); NB-jaarproxy-disclaimer zoals slice 23/33  
**Datum:** 2026-06-02

## Problem Statement

**Assetmanagers** en **maintenance engineers** moeten analyse-uitkomsten kunnen **delen en archiveren** buiten de live werkruimte: een vergelijking tussen scenario A en B (of een enkele analyse) met dezelfde views die ze in de app kennen — Top10, tijdsplot, PBS-bijdragen, KPI’s — plus **korte, feitelijke uitleg** die niet handmatig hoeft te worden getypt.

Vandaag ontbreekt export volledig: geen Word, geen PDF, geen gestandaardiseerd rapport. Analisten maken screenshots of kopiëren tabellen, wat **niet reproduceerbaar**, **niet auditbaar** en **niet vergelijkbaar** is tussen projecten. Slice 56 levert stabiele A/B-slots; die waarde komt pas volledig tot leven wanneer een **een-klik-rapport** de bevroren runs, labels en overlays vastlegt.

Randgevallen die nu pijn doen:

- Werkruimte-filters (PBS-scope, taaktypes) kunnen stiekem de “waarheid” veranderen; een rapport moet **expliciete standaarden** volgen tenzij de gebruiker bewust een dee-dive kiest.
- Niet-beschikbaarheid over kalenderjaren is een **presentatie-proxy**; rapporten moeten de bestaande disclaimer overnemen.
- Grote projecten hebben veel **functies**; zonder drempel worden rapporten onbruikbaar lang.

## Solution

Introduceer **“Rapport genereren…”** in de resultatenwerkruimte:

1. **Eén content-pipeline** (Qt-vrij) bouwt een immutable **rapportmodel** (secties, tabellen, grafiek-PNG’s, regelgebaseerde teksten) uit project + run(s).
2. **Word (.docx)** is het primaire artefact (bewerkbaar); **PDF** optioneel (default aan) via dezelfde bron (docx → PDF-conversie).
3. **Single-run** zodra minstens één geldige `done`-run beschikbaar is; **compare** wanneer A/B-slots beide gevuld zijn (slice 56-contract: bevroren overlay per slot).
4. **Gelaagde structuur:** voorblad → KPI (+ Δ) → projectbrede tijdsplotten → per-functie hoofdstukken (NB, daarna kosten indien van toepassing) → appendix.
5. **Dialoog** met pad, drempels, optionele PBS-dee-dive, preview van pagina-aantallen, busy state tijdens generatie.

Geen AI-tekst; deterministische regels + templates (auditbaar, testbaar).

## User Stories

### Toegang en voorwaarden

1. Als assetmanager wil ik vanuit de **resultatenwerkruimte** op **Rapport genereren…** kunnen klikken, zodat ik niet naar een apart menu hoef te zoeken.
2. Als analist wil ik de knop **disabled** zien zonder geldige `done`-run, zodat ik geen leeg rapport krijg.
3. Als analist wil ik bij **één geldige run** een single-run rapport kunnen maken, zodat vergelijking niet verplicht is.
4. Als analist wil ik bij **gevulde A- en B-slots** automatisch compare-kolommen en Δ in KPI’s, zodat scenario-effect zichtbaar is.
5. Als analist wil ik tijdens generatie een **voortgang/busy state** zien, zodat ik weet dat grote projecten tijd kosten.
6. Als analist wil ik na succes **Word geopend** krijgen, zodat ik direct kan annoteren.
7. Als analist wil ik bij **PDF-fout** alsnog het docx + een waarschuwing, zodat werk niet verloren gaat.

### Generatie-dialoog

8. Als analist wil ik het **outputpad** kunnen kiezen met een verstandig voorstel (`{projectmap}/rapporten/{naam}_{datum}.docx`), zodat archivering eenvoudig is.
9. Als analist wil ik **PDF genereren** kunnen aan/uitzetten (default aan), zodat ik snel alleen Word kan maken.
10. Als analist wil ik **drempels** kunnen instellen voor NB-functies (default 1% project) en kosten-functies (default 2%), zodat het rapport focust op materiële functies.
11. Als analist wil ik optioneel **functies onder de drempel** kunnen meenemen, zodat diepgaande reviews mogelijk blijven.
12. Als analist wil ik een **read-only preview** zien (single vs compare, aantal NB-/kosten-functiepagina’s), zodat ik weet wat ik krijg vóór ik genereer.
13. Als analist wil ik **Beperk tot geselecteerd PBS-onderdeel** kunnen aanvinken (default uit), zodat ik een dee-dive kan maken zonder de standaard projectbrede rapportage te verliezen.
14. Als analist wil ik dat bij PBS-dee-dive drempels **relatief aan de subtree** zijn, zodat percentages kloppen.

### Scope en filters in het rapport

15. Als assetmanager wil ik dat het rapport **standaard het hele project** gebruikt, zodat scenario’s vergelijkbaar blijven.
16. Als analist wil ik dat **taaktype-filters uit de UI niet stiekem** worden overgenomen, zodat het rapport niet per ongeluk een gefilterde werkelijkheid toont.
17. Als maintenance engineer wil ik **Top10 op component** (niet faalwijze) in functie-hoofdstukken, zodat het rapport management-vriendelijk blijft.
18. Als analist wil ik **lifecycle NB %** en **lifecycle kosten EUR** als standaard metrics in functie-secties, zodat ze aansluiten op KPI-taal.

### Structuur en inhoud

19. Als assetmanager wil ik een **voorblad** met projectnaam (of bestandsnaam-fallback), modelleur, datum, scenario-labels en overlay-samenvatting, zodat het document traceerbaar is.
20. Als assetmanager wil ik een **KPI-pagina** met lifecycle faalmomenten, NB %, lifecycle kosten EUR en PM-taken actief, zodat ik in één oogopslag vergelijk.
21. Als assetmanager wil ik bij compare **Δ (absoluut)** op NB % en kosten zien, zodat scenario-effect kwantitatief is.
22. Als assetmanager wil ik **projectbrede tijdsplotten** voor NB en kosten (A en B), zodat ik de “hele plaat” heb vóór detail per functie.
23. Als maintenance engineer wil ik **per functie** (gesorteerd op impact) een NB-sectie met Top10, functie-tijdsplot, PBS Top10+rest en uitlegtekst, zodat ik per systeemfunctie kan handelen.
24. Als maintenance engineer wil ik voor dezelfde functie — indien van toepassing — een **kosten-sectie** met dezelfde drie view-typen, zodat NB en kosten bij elkaar blijven.
25. Als analist wil ik in de functiekop de **gekoppelde effectklassen** (`beschikbaarheid` / `kosten`) zien, zodat OTG-context duidelijk is.
26. Als analist wil ik een **appendix** met NB-proxy-disclaimer, methodiek en footnote over weggelaten functies, zodat lezers de beperkingen kennen.

### PBS-opbouw en grafieken

27. Als analist wil ik PBS-opbouw als **Top 10 componenten + rest-regel**, zodat Pareto-leesbaarheid behouden blijft.
28. Als analist wil ik bij compare **A en B onder elkaar** (niet side-by-side) voor PBS-tabellen, zodat Word/PDF smal blijft leesbaar.
29. Als analist wil ik grafieken als **ingesloten PNG** in Word/PDF, zodat layout stabiel is.
30. Als analist wil ik de **zelfde chart-builders** als de werkruimte gebruiken (NB-jaarproxy, LCC-curve), zodat cijfers niet divergeren.

### Narratief (regelgebaseerd)

31. Als assetmanager wil ik op de KPI-pagina **2–4 zinnen feitelijke interpretatie** (delta, materieel verschil), zodat ik niet alles zelf moet formuleren.
32. Als maintenance engineer wil ik per functie tekst over **dominante componenten** en functie-aandeel t.o.v. project, zodat prioritering duidelijk is.
33. Als auditor wil ik dat dezelfde input **altijd dezelfde tekst** oplevert, zodat regressietests mogelijk zijn.
34. Als analist wil ik **geen advieszinnen** (“u moet…”), zodat het rapport feitelijk blijft.
35. Als analist wil ik een **waarschuwing** wanneer A en B verschillende scenario-keys hebben, zodat ik geen valse appels-peren-vergelijking lees.

### Functie-selectie

36. Als assetmanager wil ik standaard alleen functies met **beschikbaarheids-effectklassen** in het NB-deel, zodat irrelevante functies wegblijven.
37. Als assetmanager wil ik standaard alleen functies met **kosten-effectklassen** (of kosten-drempel) in het kostendeel, zodat het kostenverhaal gefocust is.
38. Als analist wil ik op de KPI-pagina zien **hoeveel functies onder drempel** zijn weggelaten, zodat niets “verdwenen” lijkt.

### Integratie A/B (slice 56)

39. Als analist wil ik dat het rapport **bevroren `overlay_at_run` en slot-labels** per scenario gebruikt, niet de live workspace-overlay.
40. Als ontwikkelaar wil ik **CompareSlotSnapshot** als bron voor A/B-runs, zodat het rapport hetzelfde contract volgt als compare-views.
41. Als analist wil ik bij single-run de **huidige run of enkel gevuld slot** kunnen gebruiken volgens vastgelegde prioriteit (documenteer in UI), zodat seed-workflows werken.

### Metadata en slice 52

42. Als assetmanager wil ik **projectnaam** en **modelleur** op het voorblad wanneer beschikbaar (slice 52), zodat rapporten herkenbaar zijn.
43. Als analist wil ik **LCC-periode** en **modeljaar** op de KPI-pagina als context, zodat jaarschalen interpreteerbaar zijn.

### Fouten en randgevallen

44. Als analist wil ik bij **mislukte PDF-conversie** het docx behouden, zodat ik handmatig kan exporteren.
45. Als analist wil ik bij **geen functies boven drempel** een kort rapport met KPI + projectplots + footnote, zodat het niet crasht.
46. Als analist wil ik dat **projecttotaal-NB >100%** (parallelle functies) in footnote/appendix wordt genoemd, zodat verwarring wordt voorkomen.

### Architectuur en onderhoud

47. Als ontwikkelaar wil ik een **Qt-vrije materialisatie-service**, zodat unit-tests zonder GUI de rapportinhoud valideren.
48. Als ontwikkelaar wil ik **geen tweede PDF-pipeline** naast docx, zodat onderhoud beperkt blijft.
49. Als ontwikkelaar wil ik bestaande view-services **hergebruiken** (contributions, KPI, NB-chart, LCC), zodat drift minimaal is.
50. Als ontwikkelaar wil ik **ReportRunner** op de achtergrond, zodat de UI niet blokkeert.
51. Als ontwikkelaar wil ik **Nederlandse copy** via message constants, zodat consistentie met de werkruimte behouden blijft.

### Toegankelijkheid en copy

52. Als gebruiker wil ik tooltips die uitleggen dat het rapport **standaard projectbreed** is en filters **niet** uit de UI volgt, zodat verwachtingen kloppen.
53. Als gebruiker wil ik dat **NB-jaarverdeling** de bestaande proxy-disclaimer bevat, zodat technische eerlijkheid behouden blijft.

## Implementation Decisions

### ADR en afbakening

- **Geen nieuwe ADR vereist** voor rapportage zelf; **ADR-0007** blijft de bron voor A/B-slot-semantiek (bevroren overlay, labels).
- Rapportage is **read-only export**; geen wijziging aan `RCMProject`, run-cache of slot-lifecycle.
- **ValidateWindow** krijgt geen rapportknop in v1 (canoniek entrypoint = resultatenwerkruimte).

### Diepe modules (Qt-vrij tenzij anders vermeld)

- **`ReportOptions` (immutable)**  
  Outputpad, `generate_pdf`, `scope_id` (None = heel project), drempels NB/kosten (%), `include_below_threshold`, bron-runs (`single` | `compare`), referenties naar slot-keys of `last_run`.

- **`ReportEligibilityService`**  
  `can_generate(session, compare_slots) → bool + reason`; `preview_counts(options, project, runs) → {nb_pages, cost_pages, mode}` voor dialoog.

- **`ReportMaterializationService` (deep module)**  
  Input: `RCMProject`, één of twee `(RunResult, PlanningOverlayState, label, scenario_key)` tuples, `ReportOptions`.  
  Output: **`ReportDocument`** — geneste secties met titels, metadata, `ReportTable` rijen, `ReportFigure` (PNG bytes + caption), `ReportParagraph` (NL tekst).  
  Orkestreert bestaande builders met **vaste presentatie-defaults** (lifecycle, component Top10, top_n=10), niet workspace-snapshot filters.

- **`ReportFunctieSelectionService`**  
  Bepaalt welke `Functie`-ids een NB- en/of kosten-hoofdstuk krijgen (effectklasse-categorie + drempel t.o.v. project of subtree); levert sorteerorde op impact.

- **`ReportNarrativeService` (deep module)**  
  Regelset + templates: KPI-samenvatting, per-functie NB/kosten, waarschuwing bij verschillende scenario-keys, proxy-disclaimer injectie. Pure functies op aggregate cijfers; geen vrije LLM.

- **`ReportChartRenderer`**  
  Zet bestaande chart-input DTO’s om naar PNG (bijv. matplotlib Agg backend of bestaande plot-hulp indien aanwezig) — **geen Qt widgets** in exportpad.

- **`ReportDocxWriter`**  
  Mapping `ReportDocument` → `.docx` (python-docx of equivalent); vaste huisstijl (koppen, tabellen, figuren).

- **`ReportPdfExporter`**  
  docx → PDF (LibreOffice headless of platform-gedocumenteerde converter); failures als `UserFacingError`, geen stille skip.

- **`ReportRunner` (Qt)**  
  Background worker roept materialisatie + writers aan; signalen `progress`, `finished(paths)`, `failed`.

### Dunne UI-laag

- **`ReportGenerationDialog`** — velden uit user stories; roept `ReportEligibilityService.preview` bij wijziging.
- **`ResultsWorkspaceWindow`** — toolbar-knop, opent dialoog, start runner, opent Word via OS.

### Hergebruik bestaande view/builder-seams

- KPI: uitbreiden `build_kpi_table` of nieuwe `build_kpi_compare_table` met meerdere `scenario_keys` + Δ-kolommen.
- Top10: `build_contribution_rows` met vaste `ContributionPresentation` (lifecycle, metric NB/kosten).
- NB-tijd: `build_unavailability_chart_input` per `scope_id = functie.pbs_id`.
- Kosten-tijd: `materialize_lcc_curve` / LCC-presentatie met bevroren overlay per slot.
- PBS-opbouw: aggregatie over PBS-items in functie-subtree, Top10 + rest-regel (nieuwe kleine helper of hergebruik contribution-buckets met `SOURCE_PBS`).

### Single-run bron-prioriteit (vastleggen in service)

```text
if compare_slots.both_filled → use A + B
elif compare_slots.has(A) only → use A as single
elif last_run.done → use last_run + live overlay_at_run only if no slot (document: prefer slot when seeded)
else → ineligible
```

### KPI-uitbreiding (compare)

```text
KPITable.scenario_keys = ("A", "B")  # labels from slot
Optional row or column: delta_abs for pct and eur keys only
Metadata block: scenario_key, overlay summary strings (passive PM count etc.)
```

### Documentstructuur (vast)

1. Cover/metadata  
2. KPI + narrative + context (lifecycle_years, modeljaar, generated_at)  
3. Project NB chart A/B stacked; project LCC chart A/B stacked  
4. For each functie (NB sort): NB Top10, NB charts, PBS table, narrative  
5. For each functie (cost sort): idem kosten metric  
6. Appendix: disclaimers, below-threshold count, methodology bullets  

### Dependencies

- **python-docx** (of team-goedgekeurde equivalent) — nieuwe dependency, documenteren in README/dev-setup.
- **PDF converter** — expliciete prerequisite (LibreOffice); fallback = alleen docx.

### Relatie slice 52

- Voorblad gebruikt `projectnaam` / `modelleur` wanneer velden op `RCMProject` beschikbaar zijn; anders fallback bestandsnaam uit sessie.

## Testing Decisions

### Wat is een goede test

- Test **observeerbaar rapport-inhoud**: sectievolgorde, aanwezigheid van tabellen/figuren, drempel-filtering, narrative zinnen bij bekende fixtures — **niet** interne docx-XML-details tenzij smoke.
- Golden-file tests: vergelijk **ReportDocument** serialisatie (JSON/tuple) of hash van sectie-lijst; docx smoke = “bestand bestaat + minimaal N secties”.
- Geen tests op LibreOffice aanwezigheid in CI — PDF-export **gemockt** of `pytest.mark` optional.

### Modules met tests (aanbevolen)

| Module | Type |
|--------|------|
| `ReportEligibilityService` | unit |
| `ReportFunctieSelectionService` | unit |
| `ReportMaterializationService` | unit (fixtures: `sample_project`, bench demo subset) |
| `ReportNarrativeService` | unit (regel triggers, deterministic text) |
| `ReportChartRenderer` | unit (PNG bytes non-empty, dimensions) |
| `ReportDocxWriter` | unit/smoke (temp file, parsable) |
| `ReportPdfExporter` | mock only in CI |
| `ResultsWorkspaceWindow` | smoke — knop disabled/enabled, dialoog preview |

### Prior art

- `tests/test_compare_view_service.py` — multi-slot presentatie  
- `tests/test_desktop_kpi_table_service.py` — KPI aggregatie  
- `tests/test_desktop_contribution_horizon_value_service.py` — NB metrics  
- `tests/test_slice56_workspace_ab_compare_smoke.py` — toolbar smoke patroon  
- `tests/test_unavailability_chart_service.py` (indien aanwezig) of NB adapter tests  

### Regressie-gates

- Compare-views en single-run UX **ongewijzigd** wanneer geen rapport wordt gegenereerd.
- Rapport gebruikt **bevroren slot overlay** — unit test: live overlay wijziging na run verandert rapport niet zonder re-run.

## Out of Scope

- Excel/CSV-export van rapportdata.
- Door gebruiker beheerbaar Word-template (.dotx) of huisstijl-editor in app.
- Vrije sectie-keuze (“alleen KPI”) — drempels/dee-dive volstaan.
- **Faalwijze-Top10** in hoofdrapport (optionele appendix later).
- Rapportgeschiedenis / versiebeheer in de applicatie.
- Geplande of headless batch-rapporten zonder UI.
- Hyperlinks terug naar live workspace-selectie.
- Meertaligheid (niet-NL).
- AI-gegenereerde samenvattingen.
- Monte Carlo-bandbreedtes in rapport.
- Risico-metrics en extra KPI-splits (CM/PM) op KPI-pagina — latere slice.
- ValidateWindow-rapportknop.
- Organisatie-logo / branding pack v1.

## Further Notes

- Deze PRD codificeert de grill-me sessie rapportage (2026-06-02).
- **Implementatie-volgorde (suggestie):** `ReportDocument` + `ReportMaterializationService` (unit-tested) → narrative + chart PNG → docx writer → dialog + runner → PDF exporter → smoke.
- **Risico:** PDF op Windows vereist documentatie; CI test alleen docx.
- **Risico:** Chart-rendering zonder Qt kan nieuwe matplotlib-afhankelijkheid introduceren — isoleren in `ReportChartRenderer`.
- **Risico:** `projectnaam`/`modelleur` mogelijk nog niet op alle projecten — fallback is verplicht.
- Uitvoering in kleine issues via `to-issues` aanbevolen na issue-aanmaak.
