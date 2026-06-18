# PRD — Slice 103: MC-presentatie afronding (HILT103)

**Status:** ready-for-human  
**Versie:** 1.0  
**Datum:** 2026-06-16  
**Triage:** `ready-for-human`  
**Type:** HILT-gedreven closure + gerichte adapter-fixes  
**Parent:** slice 100 (MC P50-rollups + scenario-workflow); slice 101 (FM horizon-pariteit); slice 98 (MC engine v1)  
**Companion docs:** ADR-0018 (MC presentatie v1.3), CONTEXT.md (MC-presentatie-pariteit), HILT100/101 handchecks  
**Grill:** `/grill-with-docs` slice 103 (2026-06-16)

> Synthese van grill-besluiten: **HILT103 gecombineerd** (HILT100 + HILT101) vóór
> fixes; alleen bevestigde blockers in adapter; RF-kolom conditional; lifecycle
> MC-totalen ≠ analytisch punt is **acceptabel** mits gedocumenteerd.

---

## Problem Statement

Slices 100–101 brachten MC P50-rollups, scenario-vergelijking en FM
horizon-pariteit. Code-fixes en regressietests zijn grotendeels geland, maar
handchecks zijn **niet afgerond met GO**:

| Bron | Status | Open punt |
|------|--------|-----------|
| **HILT100** | NO-GO / overslagen | LCC/NB-jaarcurves vlak na MC-run |
| **HILT101** | NO-GO / overslagen | LCC MC-plot leeg zonder prior analytical; lifecycle FM vs analytisch; RF-kolom (non-blocking) |

Analisten kunnen scenario-vergelijking en MC-live views niet vertrouwen zolang
de gecombineerde presentatieketen (aggregate LCC → FM-detail → compare slots)
niet visueel is bevestigd.

### Waarom nu

- Slices 98–102 zijn gecommit; MC is productfeature, geen stub meer.
- Adapter-fixes (o.a. `horizon_profile` synthese, `resolve_compare_slot_run`)
  zijn **niet hervalideerd** door analist na laatste commits.
- Zonder HILT103-GO blijft slice 100/101 technisch `done` maar productief
  `unverified`.

---

## Solution

**HILT-first closure:** één gecombineerde handcheck (HILT103) over drie
workflow-paden; daarna **alleen adapter-fixes** voor bevestigde blockers.

### Proces

```text
Issue 01  ADR-0018 v1.3 + CONTEXT glossary (docs-poort)
Issue 02  HILT103 handcheck (ready-for-human)
Issue 03  MC LCC/NB-jaarcurves — single-run + scenario compare (pad A/B)
Issue 04  Mixed compare LCC-slot zonder analytical session (pad C)
Issue 05  RF-kolom align (conditional op HILT D1)
```

### HILT103 workflow-matrix (verplicht)

| Pad | Views | Kritieke checks |
|-----|-------|-----------------|
| **Single-run MC** | Top 10, LCC, FM-detail | Niet-vlakke LCC/NB-jaarcurves (aging-FM); FM default **Ø per jaar** |
| **Scenario compare** (S1+S2 MC) | LCC compare, FM compare | Aggregate LCC compare; geen vlakke jaarcurves |
| **Mixed compare** (S1 analytisch, S2 MC) | FM, LCC | FM Ø-per-jaar plausibel; LCC MC-slot **zonder** prior analytical run |

### Presentatie-beloftes (na slice 103)

| Onderwerp | Belofte |
|-----------|---------|
| **Ø per jaar (default)** | MC FM-kolommen volgen `ContributionPresentation` — plausibel dichtbij analytisch |
| **LCC/NB jaarcurves** | Niet-vlak voor aging-FM; random-FM mag vlak blijven (motor-gedrag) |
| **Compare slots** | MC LCC/FM rebuild uit slot-run ook zonder live analytical session |
| **Lifecycle-totalen** | MC P50 **≠** analytisch punt — **geen numerieke parity-belofte**; band-uitleg voldoende |
| **RF-kolom FM-detail** | Alleen fixen als HILT bevestigt verwarring (presentatie-gap, geen modelinput) |

### Technische grens

- **Adapter-only** (`rcm_desktop/adapter/`).
- Geen `rcm_core`-motorwijzigingen; geen MC fase 2 (P10/P90 aggregate banden).
- Geen ValidateWindow retirement / LTAP-parity.

---

## User Stories

1. As a reliability-analist, I want MC LCC/NB-jaarcurves te tonen zoals
   analytisch (aging-vorm, geen vlakke plateau), so that tijdsplots
   interpreteerbaar blijven na MC-run.
2. As a reliability-analist, I want scenario-vergelijking MC↔MC en mixed
   MC↔analytisch visueel plausibel, so that ik scenario-workflow kan vertrouwen.
3. As a reliability-analist, I want LCC compare voor een MC-slot te werken
   zonder eerst een analytische run te draaien, so that mixed compare niet
   afhangt van verborgen session-state.
4. As a reliability-analist, I want te begrijpen dat MC lifecycle-totalen
   kunnen afwijken van analytische puntschattingen, so that ik discrete
   banden (P10/P50/P90) niet verwar met een bug.
5. As a developer, I want HILT103-GO vóór merge van blocker-fixes, so that
   we geen speculative adapter-wijzigingen shippen.
6. As a developer, I want regressietests uit te breiden alleen voor
   bevestigde blockers, so that CI de handcheck-bevindingen vastlegt.

---

## Implementation Decisions

### Grill-besluiten (2026-06-16)

| # | Onderwerp | Besluit |
|---|-----------|---------|
| 1 | **Primaire scope** | MC-presentatie afronden (HILT100/101 follow-up) |
| 2 | **Proces** | HILT103 gecombineerd → fixes alleen voor blockers |
| 3 | **Lifecycle-pariteit** | Drempel vastleggen **na** HILT; fallback = documenteren + accepteren |
| 4 | **AFK-scope** | Adapter-only; RF-kolom conditional |
| 5 | **HILT-workflows** | Single-run + scenario compare + mixed compare |
| 6 | **Out of scope** | Strikt closure — geen MC fase 2, ValidateWindow, PR3 stochastiek |

### Bekende pre-HILT code-locaties (indien blocker bevestigd)

| Bevinding | Locatie | Prior art |
|-----------|---------|-----------|
| Vlakke LCC-curves | `simulation_engine_service.fm_results_from_mc_p50` | `test_slice100_mc_p50_rollups.py` |
| LCC compare leeg (MC slot) | `compare_view_service.resolve_compare_slot_run` | `test_slice101_mc_lcc_compare_without_analytical.py` |
| RF-kolom MC | `simulation_engine_service.build_mc_fm_rows` vs `result_view_service.enrich_fm_rows_with_nmf_rf` | HILT101 non-blocking |

### Known gaps (geaccepteerd, niet slice 103)

- Knop **Herbereken analyse** i.p.v. **Start analyse** bij FM-cache op disk (slice 36).
- Geen visuele freeze-feedback bij **Extra scenario** (slice 100).
- P10/P90-envelop in Top 10/LCC aggregate (MC fase 2).

---

## Testing Decisions

| Seam | Wat |
|------|-----|
| HILT103 | Visuele GO op Haarlem demo (`awzi_haarlem_waarderpolder_demo.rcm.json`) |
| `fm_results_from_mc_p50` | Aging-FM: non-flat LCC buckets; random-FM: flat OK |
| Compare slot LCC | MC slot zonder `session.run` |
| FM presentation scale | Default horizon ratio guard (<3×) — bestaande slice 101 tests |
| RF align (conditional) | MC RF == analytische `_resolve_rf_for_fm` per rij |

**Geen nieuwe tests** voor aangenomen-fixed paden tot HILT103 bevestigt blocker.

---

## Out of Scope

- P10/P90-banden in Top 10/LCC aggregate (slice 100/102 fase 2).
- Onafhankelijke stochastische kosten/downtime (ADR-0018 PR3).
- ValidateWindow retirement / LTAP-parity (fase E).
- `rcm_core`-motorwijzigingen.
- Aging conditional SSOT fase 2.

---

## Further Notes

### Issue-volgorde

```text
01  Docs-poort (ADR-0018 v1.3, CONTEXT MC-presentatie-pariteit)
02  HILT103 (ready-for-human) — start met /hilt 103
03  LCC/NB-jaarcurves (blocked by 02 pad A/B)
04  Mixed compare LCC-slot (blocked by 02 pad C)
05  RF-kolom (blocked by 02 D1)
```

### Relatie HILT100/101

HILT103 **supersedes** open items uit HILT100 en HILT101; geen aparte
hervalidatie-sessies nodig na GO.

### Follow-up slice 104 (2026-06-16)

Analist-wensen uit HILT103-sessie (niet MC-blockers):

- Single-run FM: tabel/diagram-toggle + beknopte metric-tabel (zoals compare)
- Top 10-modus verwijderen
- FM-editor: effecten + onderhoud direct bewerkbaar

Zie `.scratch/rcm-desktop-slice104-fm-single-run-presentatie/PRD.md`.
HILT103-checks A3/B2 (Top 10) worden niet meer uitgevoerd.

### Definition of done

Slice 103 = **done** wanneer:

- [ ] HILT103 = **GO**
- [ ] Alle HILT-blockers gefixt (issues 03–05 waar van toepassing) + regressietests groen
- [ ] ADR-0018 v1.3 + CONTEXT glossary gepubliceerd
- [ ] RF-fix alleen indien HILT conditional trigger
