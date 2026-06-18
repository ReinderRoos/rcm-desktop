# HILT105 — Handcheck werkruimte UX-polish

**Issue:** slice 105 issue 13  
**Laatste sessie:** 2026-06-18 re-HILT batch II op master (issues 26–33)  
**Status:** **GO**

## Doel

Visuele QA na slice 105: FM-editor, FM-inspector/diagram, faalwijze-diagram,
shell/navigatie, LCC-presentatie.

## Voorbereiding

1. `python -m rcm_desktop.main`
2. Open `tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json`
3. **Start analyse**

---

## Sessie 2026-06-18 re-check — sessie 2 (issues 24–29)

| Pad | Uitkomst | Notities |
|-----|----------|----------|
| Waarschuwingen toolbar vs tabel | **fix** | Optie B: strip alleen Output → issue 24 |
| Vul effecten/preventief | **gap** | Picker nog "Bron-faalwijze" → issue 25 |
| Chrome cleanup | **open** | Componenten, Top10 Output, Toon hele project, Run-modus → 26–29 |

### Open gaps (sessie 2)

| ID | Onderwerp | Issue | Type |
|----|-----------|-------|------|
| major | Vul effecten/preventief picker UX | 25 | AFK |
| minor | PBS "Componenten" label | 26 | AFK |
| minor | Top10-subbar Output FM-views | 27 | AFK |
| minor | "Toon hele project" knop | 28 | AFK |
| minor | Run-modus naar toolbar | 29 | AFK |
| i | Validatiestrip op Input | 24 | AFK **done** |

---

## Sessie 2026-06-18 re-check — na issues 16–22

| Pad | Uitkomst | Notities |
|-----|----------|----------|
| Voorbereiding | OK | App + analyse |
| A — FM-editor sidebar | **OK** | Zijbalk visueel duidelijk (f) |
| B — FM-inspector | **GO met gap** | Zichtbaar; sluiten werkt niet / knop ontbreekt (d) — analist accepteert met gap |
| C — Faalwijze-diagram | **OK** | Font uniform (g) |
| D — What-if menu | **OK** | Navigeert + overlay (a) |
| D — Shell polish | **deels** | Dropdowns + Project-dropdown OK (b,e); **Top10 nog op Input** (c) |
| E — LCC-presentatie | **OK** | Eenheden, kleuren, filters |
| A+ — Vul van… | **gap** | Knop altijd faalwijze-scope; moet per tab (Basis/Effecten/Preventief) → issue 23 |

### Open gaps (re-check)

| ID | Onderwerp | Issue | Type |
|----|-----------|-------|------|
| d | FM-inspector sluiten | 19 | AFK (re-open) |
| c | Top10-subbar op Input | 18 | AFK (re-open) |
| h | Vul van… per sectie-tab | 23 | AFK |

---

## Sessie 2026-06-18 — GO met kanttekeningen

| Pad | Uitkomst | Notities |
|-----|----------|----------|
| A — FM-editor sidebar | **OK** | Effecten/Preventief bereikbaar; polish gewenst (f) |
| B — FM-inspector | **OK** | Sluiten na openen ontbreekt (d) |
| C — Faalwijze-diagram | **OK** | Font/size nog niet uniform (g) |
| D — Shell & navigatie | **OK*** | What-if menu zonder effect (a); dropdowns groot (b); Top10 op Input (c); Project-dropdown (e) |
| E — LCC-presentatie | **OK** | Eenheden, kleuren, filters OK |

### Kanttekeningen (follow-up slice 105 issues 16–22)

| ID | Onderwerp | Issue | Type |
|----|-----------|-------|------|
| a | What-if menubalk + shortcut zonder zichtbaar effect | 16 | AFK |
| b | Dropdown-menu's nog te groot / onoverzichtelijk | 17 | AFK |
| c | Top 10-subbar onder Input verwijderen | 18 | AFK |
| d | FM-inspector sluiten na openen | 19 | AFK |
| e | Dropdown “Project” (CM/PM) verwijderen | 20 | AFK |
| f | FM-editor sidebar visueel duidelijker | 21 | AFK |
| g | Diagram font en fontsize uniformeren | 22 | AFK |

---

## Sessie 2026-06-17 — resultaten

| Pad | Uitkomst | Notities |
|-----|----------|----------|
| Voorbereiding | OK | App + analyse klaar |
| A — FM-editor tabs | **NOK** | Zelfde blocker als 2026-06-16 |
| B — FM-inspector diagram | OK + **productwens** | Zichtbaar werkt; analist wil **default verborgen**, pas na aanroep |
| C — Faalwijze-diagram | OK | Geen streepjes, waarden in/op balk, breedte OK |
| D — Shell & navigatie | **NOK** | Meerdere punten (details hieronder) |
| E — LCC-presentatie | OK | Eenheden, grid, kleuren, CM terugzetten OK deze sessie |

---

## Pad A — FM-editor tabs (issue 01) — BLOCKING

| # | Check | OK | NOK | Notities |
|---|-------|----|-----|----------|
| A1 | Dubbelklik FM opent editor | x | | |
| A2 | Tab **Effecten** zichtbaar + bruikbaar | | x | Tabbladen niet in tabbalk |
| A3 | Tab **Preventief** zichtbaar + bruikbaar | | x | Tabbladen niet in tabbalk |

**Analist:** incremental widget-fix (scrollButtons/expanding) **niet voldoende** → behandelen als **(her)ontwikkeling** editor-shell, niet alleen bugfix.

**Code-seams:** `rcm_desktop/views/fm_editor_dialog.py` (QTabWidget), tests `tests/test_slice105_fm_editor_tabs_robust.py`

---

## Pad B — FM-inspector (issue 02) — PRODUCTBESLUIT

| # | Check | OK | NOK | Notities |
|---|-------|----|-----|----------|
| B1 | Inspector zichtbaar in diagram | x | | Functioneel OK |
| B2 | Compare diagram | | | Niet getest 2026-06-17 |

**Productwens (analist):** FM-inspector **default niet zichtbaar** → meer ruimte voor Top X/diagram; toggle of menu om te tonen.  
**Tegenstrijdig met:** issue 02 AC (“persistent zichtbaar”). Grill/slice-106 nodig.

**Code-seams:** `WorkspaceChromeProfile.shows_fm_inspector`, `FmToolbarPlan.fm_inspector_visible`, `workspace_toolbar_sync.apply_fm_toolbar`, snapshot `fm_view_mode`

---

## Pad C — Faalwijze-diagram (issue 03) — OK

| # | Check | OK | NOK | Notities |
|---|-------|----|-----|----------|
| C1 | Geen streepjes | x | | |
| C2 | Waarden in/op balk | x | | |
| C3 | Balken breed genoeg | x | | |
| C4 | Typografie labels | | | Polish: faalwijze/component niet dikgedrukt; eerste regel zelfde font als tweede |

**Code-seams:** `rcm_desktop/views/widgets/faalwijze_compare_bar_chart.py`

---

## Pad D — Shell & navigatie (issues 04–06, 09) — BLOCKING

| # | Check | OK | NOK | Notities |
|---|-------|----|-----|----------|
| D1 | Content-marges | x | | OK |
| D2 | **What-if** topniveau | | x | Analist: nog niet op verwacht topniveau (werkruimte-modus, niet alleen menu-item) |
| D3 | Geen scenario CM/PM **menu** | | ? | Tests zeggen menu weg; analist ziet CM/PM nog (toolbar-combo? ADR-0007) — verifiëren UI vs menu |
| D4 | Dropdown compact; pijltjes | | x | Te groot; pijltjes slecht leesbaar |

**Analist:** What-if + FM-editor → **(her)ontwikkeling**, niet incremental patch.

**Code-seams:** `workspace_menu_spec.py` (whatif-sectie), `results_workspace_window.py` (`_toggle_lcc_whatif_from_menu`), `rcm_desktop/theme/rcm2.qss`, scenario-toolbar in `scenario_workflow_binding.py`

---

## Pad E — LCC-presentatie (issues 07–08)

| # | Check | OK | NOK | Notities |
|---|-------|----|-----|----------|
| E1 | Aslabels met eenheden | x | | |
| E2 | Grid/maatstreepjes | x | | |
| E3 | PM ≠ CM kleuren | x | | |
| E4 | CM-filter terugzetten | x | | OK 2026-06-17 |

### LCC PM-type filter (analist eerdere feedback, niet apart HILT-stap) — BLOCKING REKEN

**Symptoom:** Alleen REV aan = zelfde profiel als alleen TST = zelfde als REV+IN+TST samen.  
**Vermoedelijke oorzaak:** `rcm_desktop/adapter/lcc_planning_service.py` ~regel 208–209: `filtered_preventief=scaled_prev` (ongefilterd) zonder actieve what-if overlay.

**Tests:** nog geen slice105-test; toevoegen na fix.

---

## Blockers voor volgende agent (prioriteit)

### P0 — Blocking (HILT NO-GO)

| ID | Onderwerp | Type | Waar beginnen |
|----|-----------|------|----------------|
| B1 | FM-editor: Effecten/Preventief niet in tabbalk | Feature/herontwikkeling | `fm_editor_dialog.py` — layout/shell v2 |
| B2 | What-if niet als verwacht topniveau UX | Feature/herontwikkeling | Menu + workspace-modus/chroom; niet alleen `whatif.toggle` |
| B3 | Shell: dropdowns te groot, pijltjes onleesbaar | UX/QSS | `rcm2.qss`, view-dropdown |
| B4 | Scenario CM/PM nog zichtbaar voor analist | Verifiëren | Menu vs toolbar-combo (`scenario_workflow_binding`); product afstemmen ADR-0007 |
| B5 | LCC PM-type filter (REV/TST/…) geen effect op curve | Bug/reken | `lcc_planning_service.py` `apply_curve` / `filtered_preventief` |

### P1 — Productbesluit vóór implementatie

| ID | Onderwerp | Besluit nodig |
|----|-----------|----------------|
| P1 | FM-inspector default **verborgen** i.p.v. persistent | Grill: toggle in toolbar? menu? default in snapshot? |
| P2 | What-if als **werkruimte-modus** vs menu-toggle | Grill met analist |

### P2 — Polish (niet blocking voor eerste GO)

| ID | Onderwerp |
|----|-----------|
| K1 | Diagram: faalwijze/component labels niet bold; consistent font |
| K2 | LCC: aslabels overlappen grid (indien nog zichtbaar) |
| K3 | LCC PM-subtypes apart kleuren (backlog issue 08) |

---

## Akkoord

| Analist | Uitkomst | Datum |
|---------|----------|-------|
| Reinder | **NO-GO** | 2026-06-16 |
| Reinder | **NO-GO** — B1, D2–D4 open; B5 uit eerdere feedback | 2026-06-17 |
| Reinder | **GO** — kanttekeningen a–g → issues 16–22 | 2026-06-18 |
| Reinder | **GO met kanttekening** — gaps c,d,h → issues 18, 19, 23 | 2026-06-18 |
| Reinder | **GO** — batch II (26–33) + validatiestrip/rail/libraries op master | 2026-06-18 |

## Sessie 2026-06-18 — re-HILT batch II op master (103–105 combi)

| Pad | Uitkomst | Notities |
|-----|----------|----------|
| Issue 30 | **OK** | Validatiestrip nergens zichtbaar |
| Issue 31 | **OK** | View-navigatie via rechter rail |
| Issues 32–33 | **OK** | Effectklassen- + REV-library in FM-editor |
| Issues 26–29 | **OK** | Run-modus toolbar, geen Top10-subbar Output, geen Toon hele project, geen PBS Componenten |

## Agent-handoff (copy-paste)

```
HILT105 GO (2026-06-18) — follow-up volgorde:

1. 18 Top10 Input-subbar weg
2. 20 Project/CM/PM dropdown weg
3. 19 FM-inspector sluiten
4. 21 FM-editor sidebar QSS
5. 22 Diagram font uniform
6. 17 Dropdown compact v2
7. 16 What-if menu merkbaar effect (+ optioneel grill P2 voor volledige modus)

Fixture: tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json
Daarna: slice 106 issue 02
```
