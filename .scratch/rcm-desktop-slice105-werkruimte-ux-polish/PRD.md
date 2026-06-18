# PRD — Slice 105: Werkruimte UX-polish + presentatie-verdieping

**Status:** ready-for-agent (HILT105 GO; follow-up 16–22 open)  
**HILT105:** GO 2026-06-18 — zie `HILT105_HANDCHECK.md` kanttekeningen a–g
**Versie:** 1.0  
**Datum:** 2026-06-17  
**Triage:** `ready-for-agent`  
**Type:** Cross-cutting UX + adapter-architectuur (geen `rcm_core`-schema)  
**Parent:** slice 104 (FM single-run presentatie, HILT104 NO-GO → editor-blockers → re-HILT); slice 102 (Faalwijze-analyse, RCM2-shell); slice 95 (Chrome-profiel)  
**Companion docs:** CONTEXT.md (FM-resultaten, Faalwijze-analyse, LCC-plot, Werkruimte-menubalk, Chrome-profiel), ADR-0007 (scenario compare), ADR-0012 (LTAP preset), ADR-0019 (RCM2 presentatielaag)

> Synthese van **11 HILT104/re-HILT feedbackpunten**, zoom-out module-kaart
> (resultatenwerkruimte → orchestrator → panelen → presentatie-seams) en
> architectuurreview **deepening candidates 1, 3 en 5**. Doel: analist-UX
> afronden én presentatielogica concentreren achter testbare adapter-seams.

---

## Problem Statement

Na slice 104 (single-run FM-pariteit, Top 10-afbouw, FM-editor fixes) blijft
**re-HILT104** drie categorieën problemen melden:

### A — FM-resultaten UX (blockers + polish)

| # | Feedback | Huidige situatie |
|---|----------|------------------|
| 1 | Effecten-/Preventief-tab in FM-editor nog niet zichtbaar | Scroll/layout-fix uit slice 104 issue 03 faalt op sommige schermen/DPI |
| 2 | FM-inspector verdwijnt in diagramweergave | Inspector zit in tabel-splitter; bij diagram-toggle wordt chrome verborgen |
| 3 | Faalwijze-diagram: streepjes, rechts uitgelijnde waarden, smalle balken | `FaalwijzeCompareBarChartWidget` tekent `—` voor ontbrekend S2 en waarden rechts van de balk |

### B — LCC-presentatie

| # | Feedback | Huidige situatie |
|---|----------|------------------|
| 6 | LCC-aslabels zonder eenheden; metrieken moeilijk te onderscheiden | `lcc_plot_axis_labels` levert tekst zonder expliciete eenheid per metric |
| 7 | Maatregeltypes niet visueel onderscheidend (PM vs CM) | LCC-stacked chart gebruikt generieke kleuren; geen Delta Pi-token mapping per type |

### C — Navigatie en shell

| # | Feedback | Huidige situatie |
|---|----------|------------------|
| 8 | What-if te diep in menu's | `run.toggle_whatif` zit onder **Run**, LCC what-if bar alleen zichtbaar op LCC-view |
| 9 | Scenario CM/PM menu overbodig | `run.scenario_cm` / `run.scenario_pm` zijn legacy shortcuts naast toolbar-scenariovergelijking |
| 10 | Tekst/figuren tegen vensterrand | RCM2-shell margins onvoldoende op content-gebied |
| 11 | Dropdown-menu's te groot; pijltjes slecht leesbaar | View-dropdown + QMenu styling niet gecompacteerd |

### D — Uitgesteld (expliciet "voor later")

| # | Feedback | Besluit |
|---|----------|---------|
| 4 | FM-inspector visueel mooier | **Out of scope** slice 105 → backlog issue 14 |
| 5 | Tabel-filterrij ook in diagram | **Out of scope** slice 105 → backlog issue 15 |

### Architecturale frictie (zoom-out + review)

Presentatielogica voor FM-resultaten is **verspreid**:

- **Faalwijze-analyse** DTO in adapter, maar view-mode (`tabel`/`diagram`), NMF/RF-toggle en inspector-zichtbaarheid leven op `ResultsWorkspaceWindow` (niet in snapshot).
- **RenderPlan**-binding voor FM-detail zit nog grotendeels in het venster (~3.6k LOC); panel-extractie (slice 62) verplaatste widget-bomen, niet bind-logica.
- **Chrome-profiel** bestaat, maar toolbar-planning gebruikt nog handgeschreven `_plan_*_toolbar` i.p.v. declaratieve regels.

Dit belemmert testbaarheid en maakt UX-fixes (inspector in diagram, diagram-labels) duur en regressiegevoelig.

---

## Solution

Drie tranches in één slice — **product-UX eerst**, architectuur als enabler:

### 105-A — FM-resultaten polish (HILT-blockers)

1. **FM-editor tabs robuust** — minimum dialooghoogte, tab-strip altijd zichtbaar, scroll-area sizing onafhankelijk van DPI; regressietest met `show()` + zichtbaarheid op alle drie tabs.
2. **FM-inspector persistent** — inspector blijft zichtbaar in single-run én compare, ook bij diagramweergave; selectie uit tabel/diagram blijft inspector vullen.
3. **Faalwijze-diagram v2** — geen `—` voor ontbrekend scenario (alleen S1-balk of lege S2-rij); waarden **in** of **aan uiteinde** van balk; bredere rij-/balkhoogte; geen aparte rechter waardekolom.

### 105-B — LCC + navigatie

4. **LCC as-labels met eenheden** — faalmomenten (#/jaar), niet-beschikbaarheid (uur/jaar of %), kosten (€/jaar); tooltip of secundaire as waar nodig.
5. **LCC maatregeltype-kleuren** — CM, PM, REV, overig uit `dp_tokens`; PM visueel onderscheidend van CM (Delta Pi-huisstijl).
6. **What-if op topniveau** — eigen **What-if**-menu (of Analyse-submenu) met PM-taak toggle + sneltoets; niet alleen onder Run/LCC-panel.
7. **Verwijder scenario CM/PM** — menu-items en handlers weg; scenariovergelijking blijft via toolbar (Start analyse → Extra scenario → Vergelijk).
8. **Shell-marges** — content-padding op centraal werkgebied, footer en chart-containers.
9. **Menu/dropdown compactheid** — max-height view-dropdown, menu-item padding, submenu-pijl contrast in QSS.

### 105-C — Presentatie-architectuur (deepening)

10. **Faalwijze-analyse view-state in snapshot** — `fm_view_mode` (tabel|diagram), `fm_inspector_visible`, `fm_show_nmf_rf` in `WorkspaceStateSnapshot`; orchestrator plant chrome; venster bindt alleen.
11. **FM-detail workspace binding** — `fm_detail_workspace_binding` module: alle `_apply_fm_*` / `_render_fm_*` Qt-mutatie uit venster; venster delegeert vanuit `_apply_render_plan`.
12. **Chrome-profiel toolbar-plan** — declaratieve toolbar-regels per `view_id`; `_plan_*_toolbar` consolideren; `workspace_toolbar_sync` zonder venster-introspectie.

### HILT

**HILT105** na issues 01–03 en 04–09 (minimaal A+B); architectuur-issues 10–12 mogen parallel maar zijn geen HILT-blocker.

---

## User Stories

### FM-resultaten

1. As a reliability-analist, I want **Effecten- en Preventief-tabs altijd bereikbaar** in de FM-editor, so that ik FM-koppelingen kan bewerken op elk schermformaat.
2. As a reliability-analist, I want de **FM-inspector zichtbaar te houden in diagramweergave**, so that ik lifecycle- en jaarreeksdetails kan lezen terwijl ik balken vergelijk.
3. As a reliability-analist, I want **diagramwaarden in of op de balk** i.p.v. rechts uitgelijnd, so that ik waarden direct bij de visuele vergelijking zie.
4. As a reliability-analist, I want **geen streepjes voor ontbrekend scenario 2** wanneer alleen S1 data heeft, so that het diagram niet rommelig oogt.
5. As a reliability-analist, I want **bredere diagrambalken**, so that kleine verschillen beter zichtbaar zijn.

### LCC

6. As a reliability-analist, I want **LCC-aslabels met eenheden**, so that ik faalmomenten, NB en kosten direct kan interpreteren.
7. As a reliability-analist, I want **onderscheidende kleuren per maatregeltype** (PM vs CM), so that ik de LCC-curve kan uitlezen zonder legenda te gokken.

### Navigatie en shell

8. As a reliability-analist, I want **What-if-planning op menu-topniveau**, so that ik PM-scenario's kan wisselen zonder eerst naar LCC te navigeren.
9. As a reliability-analist, I want **geen aparte CM/PM-scenario-menu's** meer, so that de menustructuur overeenkomt met de toolbar-workflow.
10. As a reliability-analist, I want **voldoende marge rond content**, so that tekst en grafieken niet tegen de vensterrand kleven.
11. As a reliability-analist, I want **compacte, leesbare dropdown-menu's**, so that navigatie overzichtelijk blijft.

### Architectuur (ontwikkelaar)

12. As a developer, I want **FM view-state in de workspace-snapshot**, so that orchestrator-plannen en tests niet afhangen van venster-private velden.
13. As a developer, I want **FM RenderPlan-binding in een aparte module**, so that FM-UX-wijzigingen locality krijgen en het venster onder de 2000-regel-gate kan.
14. As a developer, I want **toolbar-zichtbaarheid uit Chrome-profiel**, so that nieuwe views geen orchestrator-surgery vereisen.

---

## Implementation Decisions

| # | Onderwerp | Besluit |
|---|-----------|---------|
| 1 | **FM-editor** | Min. dialooghoogte 520px; `QTabWidget` tabBar altijd zichtbaar; Effecten/Preventief in scroll met `minimumHeight` op page |
| 2 | **Inspector in diagram** | Inspector-splitter blijft in layout; alleen tabel/diagram-stack wisselt — geen `setVisible(False)` op inspector bij diagram |
| 3 | **Diagram labels** | Tekst in balk (wit/contrast) of aan bar-end; `_VALUE_WIDTH` kolom schrappen; `_ROW_HEIGHT` verhogen (44→56) |
| 4 | **Ontbrekend S2** | Geen `—` tekenen; S2-balk overslaan als `s2 is None`; rij toont alleen S1 |
| 5 | **LCC eenheden** | Via bestaande `lcc_plot_axis_labels`-seam; geen kern-wijziging |
| 6 | **LCC kleuren** | Nieuwe tokens in `dp_tokens` voor CM/PM/REV/NMF; chart bindt via presentatie-DTO |
| 7 | **What-if menu** | Nieuw top-level menu **What-if** (`menu_id="whatif"`) vóór Run; bevat toggle + eventueel "Ga naar LCC-plot" |
| 8 | **CM/PM menu** | Verwijder `run.scenario_cm` / `run.scenario_pm`; bindings en handlers opruimen; ADR-notitie in issue |
| 9 | **Margins** | Centrale `QVBoxLayout` contentMargins 12–16px; chart-widgets `contentsMargins` consistent |
| 10 | **View-state** | Snapshot-velden + orchestrator `FmToolbarPlan` uitbreiden; migratie default: tabel + inspector aan |
| 11 | **Binding module** | Patroon: `simulation_workspace_binding.py`; venster houdt signal wiring |
| 12 | **Chrome toolbar** | `WorkspaceChromeProfile.toolbar_widgets` declaratief; gefaseerd: FM + LCC eerst |
| 13 | **Slice 104 relatie** | Issue 03 slice 104 blijft done; slice 105 issue 01 is robuustheidsfix |
| 14 | **ADR-0006 legacy** | Scenario CM/PM menu-verwijdering = expliciete deprecatie legacy compare-stack shortcut |

---

## Testing Decisions

| Seam | Wat | Prior art |
|------|-----|-----------|
| `test_slice105_fm_editor_tabs_robust.py` | Alle tabs zichtbaar na resize + show | `test_slice104_fm_editor_tabs.py` |
| `test_slice105_fm_inspector_diagram.py` | Inspector zichtbaar bij diagram single + compare | `test_slice103_fm_detail_ui.py` |
| `test_slice105_faalwijze_diagram_labels.py` | Geen `—`; waarden in balk; bredere rijen | `test_slice102_faalwijze_compare.py` |
| `test_slice105_lcc_axis_units.py` | Aslabels bevatten eenheid | `test_slice85_*` |
| `test_slice105_lcc_measure_colors.py` | PM ≠ CM kleur uit tokens | `test_slice102_*` theming |
| `test_slice105_menu_whatif.py` | What-if topmenu; geen scenario_cm/pm | `test_slice76_*`, `test_slice79_view_menu*` |
| `test_slice105_workspace_margins.py` | Content margins > 0 | smoke op window layout |
| `test_slice105_fm_view_state.py` | Snapshot bevat fm_view_mode; orchestrator plan | `test_desktop_results_workspace_state.py` |
| `test_slice105_fm_detail_binding.py` | Binding module past RenderPlan toe | `test_slice61_orchestrator_gate.py` |
| Regressie | `test_slice104_*`, `test_slice102_*`, `test_desktop_results_workspace_window` | — |

**Testprincipe:** gedrag via orchestrator-plannen en zichtbare UI-state; geen assert op private venster-attributen na issue 10.

---

## Issue-volgorde

```text
01  FM-editor tabs robuust (HILT-blocker)
02  FM-inspector persistent in diagramweergave
03  Faalwijze-diagram: labels in balk, geen streepjes, bredere balken
04  Werkruimte content-marges
05  What-if menu topniveau
06  Verwijder scenario CM/PM menu-items
07  LCC as-labels met eenheden
08  LCC maatregeltype-kleuren (Delta Pi)
09  Menu/dropdown compactheid + pijltjes
10  Faalwijze-analyse view-state in snapshot
11  FM-detail workspace binding extractie
12  Chrome-profiel declarative toolbar
13  HILT105 handcheck (ready-for-human)
14  [backlog] FM-inspector visuele polish
15  [backlog] Tabel-filter in diagramweergave
```

**Aanbevolen uitvoering:**

- **HILT-pad:** 01 → 02 → 03 → 13 (parallel: 04–09)
- **Architectuur-pad:** 10 vóór 11; 12 parallel met 07–09
- Issues 14–15: `needs-triage`, niet in slice-DoD

---

## Out of Scope

- FM-inspector kolom-layout en kleuren (feedback #4) — backlog issue 14
- Tabel-filterrij in diagramweergave (feedback #5) — backlog issue 15
- Volledige `modus` → `active_view_id` unificatie (architectuur candidate 2)
- Vergelijkingswerkruimte (twee `.rcm.json`, ADR-0016) — aparte slice
- `rcm_core` schema- of motorwijzigingen
- ValidateWindow retirement

---

## Definition of done

Slice 105 = **done** wanneer:

- [ ] HILT105 = GO op issues 01–03 + steekproef 04–09
- [ ] FM-inspector + diagram UX conform feedback
- [ ] LCC eenheden + maatregelkleuren zichtbaar
- [ ] What-if topmenu; geen scenario CM/PM menu
- [ ] FM view-state in snapshot; FM binding module actief
- [ ] Regressietests groen

---

## Module-kaart (zoom-out referentie)

```text
WorkspaceStateSnapshot
  → ResultsWorkspaceOrchestrator.plan_workspace_tick
      → WorkspaceUiSyncPlan (toolbar, chrome)
      → RenderPlan (fm | fm_compare | lcc | …)
  → ResultsWorkspaceWindow._apply_*   ← te verkleinen (issue 11)
      → fm_detail_workspace_panel
      → FaalwijzeCompareBarChartWidget
      → fm_inspector_binding
      → LccWorkspacePanel / lcc_stacked_bar_chart
  → workspace_menu_spec / workspace_view_menu
```

**Top architectuuraanbeveling:** issue 11 (binding extractie) ontgrendelt locality voor FM-UX; issue 10 (view-state) maakt inspector/diagram-gedrag testbaar zonder venster-mocks.
