# PRD — Slice 104: FM single-run presentatie + Top 10-afbouw

**Status:** ready-for-agent  
**Versie:** 1.0  
**Datum:** 2026-06-16  
**Triage:** `ready-for-agent`  
**Type:** Feature (adapter + werkruimte-UI)  
**Parent:** slice 103 (MC-presentatie afronding); slice 102 (faalwijze-diagram compare); slice 33/72 (Top 10 UX); slice 44/46 (FM-editor)  
**Companion docs:** CONTEXT.md (modi, FM-presentatie), ADR-0007 (compare-presentatie)

> Productbesluiten uit HILT103-feedback en analist-wensen (2026-06-16): single-run
> FM-resultaten krijgen dezelfde tabel/diagram-UX als scenario-vergelijking; Top 10
> verdwijnt; FM-editor opent direct bewerkbare tabs voor effecten en onderhoud.

---

## Problem Statement

Na slices 100–103 werkt MC-presentatie op FM-niveau, maar de **single-run
FM-resultatenview** blijft achter bij **scenario-vergelijking**:

| Aspect | Scenario compare (FM) | Single-run FM |
|--------|----------------------|---------------|
| Tabel / diagram | ✅ toggle | ❌ alleen brede tabel |
| Beknopte tabel (één metric) | ✅ default | ❌ alle kolommen tegelijk |
| NMF / RF optioneel | ✅ toggle | ❌ altijd zichtbaar (indien aan) |
| Metric volgt filter | ✅ | ❌ |
| Horizon + Ø per jaar | ✅ (na slice 103 fix) | ✅ (deels) |

Parallel bestaat **Top 10** als aparte modus voor ranking op component/faalwijze.
Analisten willen die aggregatie niet meer apart: de **FM-resultatenview** met
tabel/diagram dekt het dagelijkse gebruik. Top 10 is redundant en verwarrend
naast de vergelijk-UX.

Bij **dubbelklik op een faalwijze** opent de FM-editor op tab **Basis**. Tabs
**Effecten** en **Preventief** bestaan al, maar analisten verwachten die direct
te kunnen bewerken zonder extra stappen of beperkingen.

### Relatie slice 103

Slice 103 blijft **MC-presentatie closure** (HILT103 LCC/NB-curves, mixed compare).
Slice 104 start **na** slice 103 issue 02 (HILT103) of parallel aan issues 03–05
wanneer HILT geen blockers meldt op FM-horizon — geen overlap met adapter-only
MC-curve fixes.

HILT103-checks op **Top 10** (A3, B2) worden **superseded** door slice 104
(Top 10-verwijdering).

---

## Solution

### 1. Single-run FM = compare-UX (één kolom)

Hergebruik compare-presentatie waar mogelijk:

- **Beknopte tabel:** één metric-kolom (Faalmomenten / Niet-beschikbaarheid /
  Kosten) gesynchroniseerd met metric-filter in toolbar — zelfde semantiek als
  `FMCompareTableModel` / compare-toolbar.
- **NMF / RF:** standaard **verborgen**; optioneel via toggle (zoals
  `fm_compare_nmf_rf_toggle`).
- **Tabel / diagram:** toggle-knoppen in FM-toolbar (single-run); diagram
  hergebruikt `FaalwijzeCompareBarChartWidget` in **single-series** modus.
- **Horizon + jaar:** bestaande horizon-knoppen en `contribution_year_combo`
  blijven; default **Ø per jaar** (slice 101/103).

### 2. Top 10 verwijderen

- Modus **Top 10** (`MODE_BIJDRAGEN`) uit navigatie, view-registry en
  presentatie-cache-defaults.
- **Startup-default:** **FM-resultaten** (`MODE_FM_DETAIL`).
- Rapportage/export die Top 10-secties gebruikt: migreren naar FM-diagram of
  expliciet deprecaten in slice 104 (zie issue 04).
- State-migratie: opgeslagen `bijdragen` → `fm_detail` in workspace-state.

### 3. FM-editor: effecten + onderhoud direct bewerkbaar

- Tabs **Effecten** en **Preventief** blijven; UX-gaten sluiten:
  - Effect-links en PM-taken **direct bewerkbaar** (toevoegen/verwijderen/wijzigen).
  - Geen extra dialoog of read-only gate tenzij businessregel (NMF, validatie).
- Optioneel: bij openen vanuit FM-tabel **laatst gebruikte tab** onthouden
  (nice-to-have; niet blocking).

### Technische grens

- Primair `rcm_desktop/adapter/` + `rcm_desktop/views/`; geen `rcm_core`-schema.
- Generaliseer compare-componenten; geen derde parallelle tabel/diagram-implementatie.

---

## User Stories

1. As a reliability-analist, I want **tabel en diagram** te wisselen in
   single-run FM-resultaten, so that ik dezelfde workflow heb als bij
   scenario-vergelijking.
2. As a reliability-analist, I want een **beknopte FM-tabel** met alleen de
   actieve metric, so that ik niet door brede kolommen hoef te scrollen.
3. As a reliability-analist, I want **NMF en RF optioneel**, so that de default
   weergave overzichtelijk blijft.
4. As a reliability-analist, I want **geen aparte Top 10-modus** meer, so that
   ik niet hoef te kiezen tussen twee ranking-views.
5. As a reliability-analist, I want bij openen van een faalwijze **effecten en
   onderhoud direct te bewerken** in aparte tabs, so that ik niet alleen Basis
   kan aanpassen.
6. As a developer, I want compare- en single-run-FM-presentatie te delen, so that
   fixes op één plek landen.

---

## Implementation Decisions

| # | Onderwerp | Besluit |
|---|-----------|---------|
| 1 | **Top 10** | Verwijderen uit werkruimte-modi |
| 2 | **Default modus** | FM-resultaten na openen project |
| 3 | **Metric-sync** | Zelfde filter-combobox als compare (Faalmomenten/NB/Kosten) |
| 4 | **Diagram** | Hergebruik `FaalwijzeCompareBarChartWidget` (single-run variant) |
| 5 | **FM-editor** | Effecten + Preventief tabs direct bewerkbaar; geen nieuwe tabs |
| 6 | **Slice 103** | HILT Top 10-checks (A3/B2) niet meer uitvoeren |

---

## Issue-volgorde

```text
01  Adapter: single-run FM compact table + metric-sync (generaliseer compare model)
02  UI: tabel/diagram-toggle + single-run diagram widget
03  FM-editor: effecten + preventief direct bewerkbaar (UX-gaten sluiten)
04  Top 10 verwijderen + default modus FM + state-migratie
05  HILT104 handcheck (ready-for-human)
```

**Aanbevolen uitvoering:** 01 → 02 → 03 (parallel mogelijk met 01) → 04 → 05.

Issue 04 heeft brede test-impact; pas uitvoeren als 01–02 groen zijn.

---

## Testing Decisions

| Seam | Wat |
|------|-----|
| `test_slice104_fm_single_run_compact_table.py` | Eén metric-kolom; NMF/RF default uit |
| `test_slice104_fm_single_run_diagram.py` | Toggle zichtbaar; diagram rendert FM-rijen |
| `test_slice104_top10_removal.py` | Geen Top 10-modus; startup = FM-detail |
| `test_slice104_fm_editor_tabs.py` | Effecten/PM rijen bewerkbaar na open |
| Regressie | `test_slice102_*`, `test_slice103_*`, `test_desktop_results_workspace_window` |

---

## Out of Scope

- PBS/component-aggregatie als vervanger van Top 10 (geen nieuwe ranking-modus).
- MC P10/P90 in FM-diagram (MC fase 2).
- ValidateWindow retirement (fase E roadmap).
- Nieuwe FM-editor tabs (Correctief blijft op Basis-tab velden).

---

## Definition of done

Slice 104 = **done** wanneer:

- [ ] Single-run FM heeft tabel/diagram-toggle + beknopte metric-tabel
- [ ] Top 10-modus verwijderd; default = FM-resultaten
- [ ] FM-editor Effecten + Preventief direct bewerkbaar (HILT bevestigd)
- [ ] HILT104 = GO
- [ ] Regressietests groen
