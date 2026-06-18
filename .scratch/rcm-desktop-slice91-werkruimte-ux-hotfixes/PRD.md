# PRD — Slice 91: Werkruimte UX-hotfixes

**Status:** done  
**Versie:** 1.0  
**Datum:** 2026-06-13  
**Triage:** `ready-for-agent`  
**Parent:** architectuurplan juni 2026 (NB-filter, Input-default, toolbar-side)  
**Voorganger:** slice 85 (effectfilter pruning), slice 79 (view-registry navigatie), slice 90 (consolidatie)

---

## Problem Statement

Na recente werkruimte-wijzigingen (slice 79–90) zijn drie gerelateerde UX-regressies zichtbaar:

1. **NB-effectfilter volledig uitgegrijsd** — het filter wordt opgebouwd uit `fm_core_results`.
   Bij project-load refresht het filter wanneer run-resultaten nog leeg zijn; alle
   effectklassen worden `selectable=False`. Na een voltooide analytische run wordt het
   filter niet opnieuw opgebouwd.
2. **Output-toolbar blijft zichtbaar op Input-zijde** — input-views hebben geen
   `legacy_modus`; bij switch naar Input blijft `modus` hangen (bv. `MODE_LCC`).
   Toolbar-plannen kijken alleen naar `modus`, niet naar `werkruimte-zijde` /
   `active_view_id`.
3. **Default Input → Faalwijzen klopt niet altijd** — `DEFAULT_VIEW_BY_SIDE` is correct,
   maar sticky state (`QSettings`) en sessie-gedrag overrulen: eerste keuze Input in een
   nieuwe sessie of na nieuw project opent niet gegarandeerd `input.faalwijzen`.

Analisten zien daardoor een onbruikbaar effectfilter, verwarrende output-chrome boven
invoergrids, en een verkeerde startview op Input.

## Solution

Drie dunne **tracer bullets**, elk end-to-end met tests:

| Issue | Focus |
|-------|--------|
| **01** | NB-effectfilter refresh na run-complete (+ cache-hydrate) |
| **02** | Toolbar-plannen side-aware (Input verbergt output-chrome) |
| **03** | Navigatiepolicy: eerste Input-bezoek + nieuw project → Faalwijzen |

Geen architectuur-herschrijving; geen `workspace_derived_refresh`-module (slice 92).
Geen wijziging aan motor, editing-pipeline of scrub-list.

## User Stories

1. Als analist wil ik na een voltooide run effectklassen met bijdrage kunnen
   selecteren in het NB-effectfilter, zodat filtering weer werkt.
2. Als analist wil ik op de Input-zijde geen output-toolbar (metric, NB-filter)
   zien boven het invoergrid.
3. Als analist wil ik de eerste keer Input in een sessie (of na nieuw project)
   standaard op Faalwijzen landen; daarna sticky gedrag binnen Input behouden.

## Issue-volgorde

| # | Titel | Blocked by |
|---|-------|------------|
| 01 | NB-effectfilter refresh na run | — |
| 02 | Toolbar side-aware op Input | — |
| 03 | Navigatiepolicy Input → Faalwijzen | — |

Issues 01–03 zijn onderling paralleliseerbaar; geen harde dependency.

## Testcommando

```powershell
python -m pytest tests/test_slice85_effectfilter_pruning.py tests/test_slice79_workspace_navigation_state.py tests/test_results_workspace_orchestrator.py tests/test_slice91_nb_filter_run_refresh.py tests/test_slice91_toolbar_input_side.py tests/test_slice91_navigation_policy.py -q
```

(Nieuwe testmodules per issue; bestaande tests blijven groen.)

## Randvoorwaarden

- AGENTS.md: views → adapter; geen `rcm_core`-imports in views.
- Geen wijziging aan effect-presentatieplan-logica (slice 85) behalve refresh-timing.
- `results_workspace_window.py` ratchet (slice 62) niet opblazen — minimale diffs.
