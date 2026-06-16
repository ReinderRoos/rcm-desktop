# PRD — Slice 102: RCM2 presentatielaag v1

**Status:** done  
**Versie:** 1.0  
**Datum:** 2026-06-16  
**Triage:** `done` (slice 102 afgerond 2026-06-16)  
**Type:** Cross-cutting presentatie (adapter + views; geen schema-drift op `RCMProject`)  
**Parent:** grill-with-docs sessie slice 102 (2026-06-16); slice 100 (scenariovergelijking); slice 101 (MC FM horizon-pariteit)  
**Companion docs:** ADR-0019 (RCM2 presentatielaag v1), ADR-0007 (scenario compare), CONTEXT.md (RCM2 presentatielaag, Faalwijze-analyse)

> Synthese van **20 grill-besluiten**: Delta Pi-huisstijl en layout-shell over de
> hele resultatenwerkruimte (102-A), plus Faalwijze-analyse-interacties voor
> FM-resultaten tijdens scenariovergelijking (102-B1 tabel, 102-B2 diagram).
> Rekeneenheden en adapter-DTO's blijven leidend; geen parallel mock-datamodel.
> **ValidateWindow** blijft buiten scope tot slice 99.

---

## Problem Statement

Slice 100/101 leverden functionele **scenariovergelijking** (Top 10, LCC, FM) en
MC-presentatie-pariteit, maar de resultatenwerkruimte ziet er nog uit als een
generieke Qt-app:

- Geen **Delta Pi-huisstijl** (navy topbar, scenario-kleuren, typografie).
- Geen spec-conforme **layout-shell** (App-wordmark, StatusStrip, Werkruimte-footer).
- **FM-resultaten compare** toont volledige multi-kolom tabellen per scenario,
  zonder metric-gestuurde kolomkeuze, uitlijning, highlight of tabel↔diagram-switch
  uit de RCM2 UI-spec (Faalwijze-analyse).

Analisten die scenario's side-by-side vergelijken op faalwijzeniveau missen daarmee
de bedoelde scan- en highlight-UX; trainers missen visuele herkenning (scenario-kleur)
over compare-views heen.

---

## Solution

Twee tranches binnen één slice:

### 102-A — Reskin / shell

1. **Centraal Qt-thema** — Delta Pi-tokens + QSS, venster-breed op Input én Output.
2. **Layout-shell** — App-wordmark (tekst v1), StatusStrip (persistent), footer
   (transient), KPI-overzicht gethemed en **standaard ingeklapt**.
3. **Scenario-kleur** — scenario 1 rood / scenario 2 magenta in Top 10, LCC en FM compare.

### 102-B — Faalwijze-analyse (FM compare)

**B1 — Tabelregels**

- Uitgelijnde scenario-rijen (S1 ∪ S2, sort op S1-waarde actieve metriek).
- Metric-gestuurde kolomkeuze; optionele NMF/RF (toggle, default uit).
- Highlight `|S1−S2|/S1 > 20%` met S1>0-guards.
- FM-inspector uit in compare v1; geen kolomfilters (PBS-scope volstaat).

**B2 — Diagram**

- Exclusieve **Tabel↔diagram-weergave**; gepaard horizontaal staafdiagram (S1/S2).
- Zelfde aligned DTO en highlight als tabel; default tabel.

### HILT-checkpoints

Drie handchecks: **HILT102-A** (na 102-A), **HILT102-B1** (na B1), **HILT102-B2**
(na B2). B2 start pas na B1 GO.

---

## User Stories

### 102-A — Delta Pi shell

1. As a reliability-analist, I want Delta Pi branding across the entire results
   workspace (Input and Output), so that editing and analysis feel like one product.
2. As a reliability-analist, I want organisation identity (App-wordmark) in the
   topbar, so that RCM2 is recognisable as a Delta Pi tool.
3. As a reliability-analist, I want persistent validation and MC status in the
   StatusStrip, so that run state remains visible during analysis.
4. As a reliability-analist, I want transient messages (save, export, run complete)
   in the footer, separate from persistent status.
5. As a reliability-analist, I want the KPI overview collapsed by default, so that
   the workbook stays central.

### 102-A — Scenario-kleur

6. As a reliability-analist, I want fixed scenario colours (red / magenta) in compare
   mode, so that scenario 1 and 2 are instantly distinguishable.
7. As a trainer, I want scenario colours in Top 10, LCC and FM compare, so that
   comparison uses the same visual language everywhere.

### 102-B — Faalwijze-analyse

8. As a reliability-analist, I want only the active metric column beside FM identity
   in compare mode, so that side-by-side scanning stays simple.
9. As a reliability-analist, I want optional NMF/RF columns in FM compare (default
   off), so that detail is available without clutter.
10. As a reliability-analist, I want aligned rows (same failure mode on the same
    row in both columns), so that differences are easy to compare.
11. As a reliability-analist, I want highlight when relative difference exceeds 20%
    (with guards), so that large deviations stand out.
12. As a reliability-analist, I want to switch exclusively between table and paired
    bar chart, so that I can scan patterns visually.
13. As a reliability-analist, I accept that the FM-inspector is unavailable during
    scenario comparison in v1 (drilldown via single-run FM).
14. As a reliability-analist, I filter FM compare via PBS scope; column filters are
    out of scope for v1.

---

## Grill-besluiten (samenvatting)

| # | Onderwerp | Keuze |
|---|-----------|-------|
| 1 | Doel | Reskin werkruimte + gericht FM-compare |
| 2 | Planning | Eén slice, tranches A / B |
| 3 | Thema | Centraal tokens + QSS |
| 4 | Layout | Spec-topbar, QMenuBar blijft, StatusStrip + footer |
| 5 | Tranche B | B1 tabel → B2 diagram |
| 6 | Highlight | `\|S1−S2\|/S1 > 20%`, S1>0, matched rows only |
| 7 | Compare-kleuren | Rood/magenta overal |
| 8 | Logo | Tekst-wordmark v1 |
| 9 | Kolommen | Alleen actieve metriek + id |
| 10 | NMF/RF | Toggle, default uit |
| 11 | Rijen | Union uitgelijnd, sort S1 |
| 12 | Diagram | Exclusieve tabel↔diagram |
| 13 | HILT | Drie checkpoints |
| 14 | FM-inspector | Uit in compare v1 |
| 15 | Docs | ADR-0019 |
| 16 | KPI | Thema + default ingeklapt |
| 17 | Footer | Transient QStatusBar |
| 18 | Filters | Geen kolomfilters compare |
| 19 | Fonts | Calibri + Segoe UI fallback |
| 20 | Dekking | Venster-breed; ValidateWindow buiten scope |

---

## Issue-index

| Issue | Titel | Type | Blocked by |
|-------|-------|------|------------|
| 01 | ADR-0019 RCM2 presentatielaag v1 | AFK | — |
| 02 | Delta Pi theme + werkruimte-shell (102-A) | AFK | 01 |
| 03 | Scenario-kleur in scenariovergelijking | AFK | 02 |
| 04 | HILT102-A reskin handcheck | HITL | 02, 03 |
| 05 | Faalwijze-analyse tabelregels (102-B1) | AFK | 04 |
| 06 | HILT102-B1 tabel handcheck | HITL | 05 |
| 07 | Faalwijze-analyse diagram (102-B2) | AFK | 06 |
| 08 | HILT102-B2 diagram handcheck | HITL | 07 |

---

## Out of scope (v1)

- ValidateWindow theming (slice 99 retirement).
- Logo-asset (tekst-wordmark volstaat; asset = latere drop-in).
- Kolomfilters in FM-compare.
- FM-inspector tijdens scenariovergelijking.
- Font-bestanden bundelen in repo.
- Onzekerheidsbanden in Top 10/LCC aggregate (slice 100 fase 2).

---

## Further Notes

- Implementatie volgt **adapter-first TDD**; views geen directe `rcm_core`-imports.
- Na HILT102-B2 GO: PRD status → `done`.
- Roadmap na slice 102: slice 96 → 97 → 99.
