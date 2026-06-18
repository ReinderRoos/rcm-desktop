# PRD — Slice 96: Modelvergelijking v1

**Status:** ready-for-agent  
**Versie:** 1.0  
**Datum:** 2026-06-18  
**Triage:** `ready-for-agent`  
**Type:** Feature (adapter + vergelijkingswerkruimte-UI)  
**Parent:** slice 95 PRD Fase B (modelvergelijking); slice 95 issues 04–07 (prototype done)  
**Companion docs:** ADR-0016 (vergelijkingsbeleid), ADR-0007 (A/B op één project — hergebruik seam), CONTEXT.md (Vergelijkingswerkruimte, FM-uitlijning, Invoerverschil, Resultaatverschil)

> **Charter (grill 2026-06-18):** Rond slice 95 dual-project compare-prototype af in
> `CompareModelsWindow` + styling-polish. **Geen** shell-integratie in
> `ResultsWorkspaceWindow`. Compare v1 blijft read-only; uniformeren hoort bij slice 97.

---

## Problem Statement

Slice 95 leverde een **werkend prototype** van de vergelijkingswerkruimte: dual-project
load, FM-uitlijning, invoer- en resultaatdiffs, en een balanced split in
`CompareModelsWindow`. Dat prototype is **niet product-klaar**:

| Aspect | Prototype (slice 95) | Doel compare v1 (slice 96) |
|--------|----------------------|----------------------------|
| Uniformeren-UI | Zichtbaar (slice 95 #10) | **Verborgen** — read-only compare |
| FM-uitlijning | Basis id-paar | Id eerst, dan `fm_technical_fingerprint` fallback |
| Invoerverschillen | Deels ad hoc | Schema-gedreven uit editing registry + vaste exclusions |
| Resultaatverschillen | Stub / deels | Cache-hydrate bij load + Run A / B / both (analytisch) |
| US16-metrics | Niet consistent side-by-side | `total_cost_eur`, `expected_total_downtime_hr`, `risk_contribution` altijd A/B |
| Visuele taal | Functioneel, weinig polish | A/B-kleuren, match-badges, diff-highlight, run/cache-strip |
| Acceptatie | Geen slice-gate | **HILT96** op twee klantprojecten |

Analisten moeten twee willekeurige `.rcm.json`-bestanden ad hoc kunnen vergelijken
(baseline A, scenario B) **zonder** portfolio-merge, **zonder** stille modelwijziging,
en **zonder** de dagelijkse enkel-model werkruimte te vervangen (ADR-0016).

### Relatie slice 95

Slice 95 issues **04–07** leverden de adapter-kern en UI-skelet:

- **04** — `CompareSession` dual-project load  
- **05** — FM-uitlijning + invoerdiffs (basis)  
- **06** — `ComparePresentation` + resultaatdiffs (basis)  
- **07** — `CompareModelsWindow` balanced split  

Slice 96 **hardent en polish** dat pad; het verplaatst compare **niet** naar
`ResultsWorkspaceWindow` (ADR-0007 blijft scenario A/B op één project).

---

## Solution

### 1. Read-only vergelijkingswerkruimte (v1)

- **Uniformeren-UI verbergen** in `CompareModelsWindow`: geen
  `NormalizationProposal`-review, geen patch/rollback-acties in compare v1.
- Uniformeren-pipeline blijft in adapter (slice 95 #09–10) voor slice 97; UI niet
  tonen tot fase C.

### 2. FM-uitlijning

Canoniek volgorde (CONTEXT.md **FM-uitlijning**):

1. Koppel op gelijke `fm_id`  
2. Voor unmatched: fallback op **technische fingerprint** (`fm_technical_fingerprint`)  
3. Resterende unmatched → alleen-in-A / alleen-in-B  

Geen handmatige mapping-UI in v1.

### 3. Schema-gedreven invoerverschillen

- Diff over faalwijze-invoervelden uit **editing schema registry**  
- **Exclusions:** `fm_id`, `library_ref`, `notes`, `aanname_*`, `downtime_per_failure`  
- Classificatie: inhoud | terminologie | structuur | parameterisatie  
- PM-taken (cross-entity) vallen buiten compare v1  

### 4. Resultaatverschillen + runs

- **Cache-hydrate** bij load wanneer analytische cache voor A en/of B beschikbaar is  
- **Run A / Run B / Run both** — uitsluitend **analytisch** (geen MC dual-project)  
- **US16-set** side-by-side per FM wanneer data beschikbaar:
  - `total_cost_eur`
  - `expected_total_downtime_hr`
  - `risk_contribution`  
- Status-strip: cache vs fresh run per kant  

### 5. Compare-visuele taal

- Consistente **A/B-kleuren** en labels (baseline vs scenario)  
- **Match-badges** (id | fingerprint | unmatched_a | unmatched_b)  
- **Diff-highlight** op invoer- en resultaatvelden  
- **Run/cache-statusstrip** boven balanced detail  

### 6. HILT96 acceptance gate

Handmatige QA op twee echte klantprojecten vóór slice = done (analist GO/NO-GO).

### Technische grens

- Primair `rcm_desktop/adapter/` + `CompareModelsWindow`; geen `rcm_core`-schema-wijziging  
- Views alleen via adapter; compare use-cases Qt-vrij en unit-testbaar  
- **Geen** menu-entry of modus in `ResultsWorkspaceWindow` in deze slice  

---

## User Stories

*(Nummering uit slice 95 PRD — modelvergelijking)*

12. As a reliability-analist, I want twee willekeurige projectbestanden (baseline A,
    scenario B) naast elkaar te laden, so that ik geen portfolio-merge nodig heb voor
    een snelle vergelijking.
13. As a reliability-analist, I want per faalwijze **invoer én resultaten** even
    zichtbaar in een balanced split, so that ik zowel keuzes als effect kan beoordelen
    zonder view-wissels.
14. As a reliability-analist, I want duidelijk te zien **welke FM's alleen in A,
    alleen in B, of in beide** zitten, so that structurele vs parameterverschillen
    snel zichtbaar zijn.
15. As a reliability-analist, I want parameterverschillen (MTTF, faaltype, aging,
    PM-koppeling) per FM gemarkeerd, so that modelleerkeuzes snel zichtbaar worden.
16. As a reliability-analist, I want resultaatverschillen (kosten, NB, bijdragen)
    naast invoerverschillen per FM, so that afgeleide effecten de invoer bevestigen.
17. As a reliability-analist, I want mapping/terminologieverschillen (zelfde FM,
    andere namen) herkenbaar gescheiden van echte parameterverschillen, so that ik
    niet verkeerde conclusies trek.
18. As a reliability-analist, I want vergelijking te bouwen op bestaande A/B-run-
    slots waar mogelijk, so that ik referentie en variant kan bevriezen zonder
    dubbele run-flows.
19. As a developer, I want compare-logica Qt-vrij in adapter use-cases, so that
    FM-diff en presentatie unit-testbaar blijven.

---

## Implementation Decisions

| # | Onderwerp | Besluit |
|---|-----------|---------|
| 1 | **Entrypoint** | Alleen `CompareModelsWindow`; geen shell-integratie werkruimte |
| 2 | **Read-only v1** | Uniformeren-UI verborgen; slice 97 owns uniformeren |
| 3 | **FM-uitlijning** | `fm_id` → `fm_technical_fingerprint` → unmatched A/B |
| 4 | **Invoerdiffs** | Editing registry; exclusions: fm_id, library_ref, notes, aanname_*, downtime_per_failure |
| 5 | **Resultaatdiffs** | US16-set; cache-hydrate + Run A/B/both (analytisch only) |
| 6 | **Visuele taal** | A/B-kleuren, badges, diff-highlight, status-strip |
| 7 | **Acceptatie** | HILT96 vóór done |

---

## Issue-volgorde

```text
01  Read-only scope: verberg uniformeren-UI
02  FM-uitlijning met fingerprint-fallback
03  Schema-gedreven invoerverschillen
04  Analytische run + cache-hydrate + US16-resultaatverschillen
05  Compare-visuele taal (styling-polish)
06  HILT96 acceptance gate (ready-for-human)
```

**Aanbevolen uitvoering:** 01 → 02 → 03 (parallel mogelijk met 02 na alignment-API stabiel) → 04 → 05 → 06.

Issue 05 wacht op 01, 02, 04 zodat styling op definitieve data en scope rust.

---

## Testing Decisions

| Seam | Wat |
|------|-----|
| `test_slice96_compare_read_only_scope.py` | Geen uniformeren-widgets/acties zichtbaar |
| `test_slice96_fm_alignment_fingerprint.py` | Id-match; fingerprint fallback; unmatched A/B |
| `test_slice96_schema_input_diffs.py` | Registry-velden; exclusions; difference_class |
| `test_slice96_result_diffs_run_cache.py` | Cache-hydrate; Run A/B/both; US16 side-by-side |
| `test_slice96_compare_visual_presentation.py` | DTO bevat A/B labels, match_kind, diff flags |
| Regressie | `test_slice95_*` compare-session/alignment/presentation tests |

GUI-smoke alleen waar geen lagere seam het contract dekt; HILT96 dekt visuele QA.

---

## Out of Scope

- **Shell-integratie** — compare modus/menu in `ResultsWorkspaceWindow`
- **Uniformeren-functionaliteit** — review, patch, audit (slice 97)
- **Handmatige FM-mapping** UI
- **MC dual-project** — Monte Carlo op twee projecten tegelijk
- **PM cross-entity diffs** — pm_tasks buiten compare v1
- **Persistente compare-sessie** over app-restarts
- **Delta-tabel 20 rijen** A/B/Δ (slice 56 out-of-scope hergebruikt)
- **Scenario chart parity** — LCC/FM-diagram compare uit werkruimte

---

## Definition of done

Slice 96 = **done** wanneer:

- [ ] CompareModelsWindow is read-only (geen uniformeren-UI)
- [ ] FM-uitlijning: id → fingerprint → unmatched
- [ ] Invoerverschillen schema-gedreven met vaste exclusions
- [ ] Resultaatverschillen: cache-hydrate + Run A/B/both; US16-metrics side-by-side
- [ ] Compare-visuele taal consistent (A/B, badges, diff-highlight, status-strip)
- [ ] HILT96 = GO
- [ ] Slice-specifieke regressietests groen
