# Kanban-handoff — slice 36 werkruimte run/presentatie performance (2026-05-21)

**Doel:** Vastlegging voor een schone vervolgsessie. Lees dit bestand + `PRD.md` vóór je het kanban-bord oppakt.

**Repo:** `rcm-desktop`  
**Slice-map:** `.scratch/rcm-desktop-slice36-werkruimte-run-presentatie-performance/`  
**Parent:** performance-onderzoek AWZI Haarlem Waarderpolder; follow-up slice 25 + slice 27  
**Referentie-fixture:** `tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json`

---

## Kanban-status (issues)

| # | Titel | Triage | Opmerking |
|---|--------|--------|-----------|
| 01 | Incrementele run + parallel | **done** | `run_decision.py`; RunRunner `force_recompute`; parallel default true |
| 02 | LTAP presentatie-cache | **done** | `ltap_view_cache.py`; geïntegreerd in `lcc_planning_service` |
| 03 | LCC jaardetail hergebruikt curve | **done** | `planning_curve` param in `build_lcc_year_detail` |
| 04 | Modus-gescopeerde rerender | **done** | `workspace_detail_render_scope.py`; slice 25 gap dicht |
| 05 | Motor horizon_profile bij run | **done** | `build_fm_horizon_profile` in `compute_fm_result`; CACHE v100 bewust |
| 06 | Performance-regressietests | **done** | `tests/perf/test_slice36_regression.py`; `slice36_contracts` in baseline |

**Slice status:** tracer-bullet **af**. **Follow-up:** slice 37 lazy presentatie-cache (post-run alleen Bijdragen-blok).

---

## Wat werkt (geverifieerd)

### Performance-flows

1. **Project laden** → `hydrate_run_from_cache` toont resultaten zonder motor.
2. **Start analyse** (geen cache) → incrementeel pad, parallel motor.
3. **Herbereken analyse** (cache aanwezig) → `full_recompute=True`.
4. **Moduswissel / metric-toggle** → alleen actieve modus-adapter (slice 04).
5. **LCC jaarselectie** → hergebruikt planningcurve + LTAP-cache.

### Run/cache-semantiek

- Knop **Start** vs **Herbereken** gekoppeld aan `fm_cache_available`.
- Geen cross-project cache-contaminatie — digest per `<project>.rcm.cache.json`.

### Fixtures

| Bestand | Gebruik |
|---------|---------|
| `tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json` | Performance referentie (~100 FM, 60j) |
| `tests/fixtures/one_fm_planning.rcm.json` | Slice 36 perf contract tests |
| `tests/fixtures/sample_project.rcm.json` | Adapter unit tests |

### Tests (relevante subset)

```powershell
cd rcm-desktop
.\.venv\Scripts\python.exe -m pytest tests/test_desktop_run_decision.py tests/test_desktop_run_runner.py `
  tests/test_desktop_ltap_view_cache.py tests/test_desktop_lcc_year_detail_curve.py `
  tests/test_workspace_detail_render_scope.py tests/test_horizon_profile_run.py `
  tests/test_desktop_fm_results_table_model.py tests/test_desktop_results_workspace_window.py -q
.\.venv\Scripts\python.exe -m pytest -m perf tests/perf/test_slice36_regression.py -q
```

**Laatste run (2026-05-21):** slice 36 subset + perf — **groen**; handmatig Haarlem OK (gebruiker).

**Repo HEAD:** `15b5d5c` — `feat(desktop): slice 36 werkruimte run/presentatie performance`

---

## Sessie-fixes (buiten issue-tekst)

### 1. FM-inspector reageert niet na re-render

- **Symptoom:** Inspector werkt kort, daarna geen update bij rijselectie.
- **Oorzaak:** `selectionChanged` één keer gewired; bij `setModel()` nieuw selection model.
- **Fix:** Permanente `FMResultsSortProxy`; selectie op `fm_id` bewaren.
- **Test:** `test_fm_inspector_selection_after_scope_rerender`

### 2. FM-tabel numerieke kolommen sorteren verkeerd

- **Symptoom:** Kolommen 4–6 sorteren niet numeriek.
- **Fix:** `FMResultsSortProxy.lessThan()` met expliciete float-vergelijking.
- **Test:** `test_sort_proxy_orders_downtime_numerically_not_lexically`

---

## Architectuur (kort)

```
Start/Herbereken
  → run_decision.resolve_run_execution
  → run_service.run (incremental, parallel)
  → build_project_total_presentation (slice 26; slice 37 → contribution-only)
  → attach_presentation_to_cache

UI navigatie
  → workspace_detail_render_scope (slice 04)
  → ltap_view_cache (slice 02)
  → workspace_render_index (LCC live pad)
```

**Regels:** UI → adapter → kern; geen `rcm_core` in views (typing ok).

---

## Bekend gedrag / acceptabel voorlopig

- **`CACHE_INPUTS_VERSION=100`:** horizon_profile verrijkt FMResult-output; oude cache → legacy fallback tot Herbereken.
- **Post-run presentatie-fase** bouwt nog monolithisch vier blokken (NB/PM/LCC ongebruikt in UI) — **slice 37** adresseert dit.
- **Handmatige Haarlem-baseline:** ~120 s cold, ~5 s cache-hit (`tests/perf/baseline.json`).

---

## Aanbevolen volgende kanban-kaarten

1. **Slice 37:** lazy presentatie-cache — contribution-only post-run.
2. **Slice 35 follow-up:** Gaarkeuken-fixture verversen.
3. **Nieuwe slice:** subset-export Excel.

---

## Belangrijkste bestanden

| Pad | Rol |
|-----|-----|
| `rcm_desktop/adapter/run_decision.py` | Run-beslissingsmodule |
| `rcm_desktop/adapter/run_runner.py` | Motor + presentatie op worker |
| `rcm_desktop/adapter/ltap_view_cache.py` | LTAP memoization |
| `rcm_desktop/adapter/lcc_planning_service.py` | LCC curve + jaardetail reuse |
| `rcm_desktop/adapter/workspace_detail_render_scope.py` | Modus-gescopeerde rerender |
| `rcm_core/engine.py` | horizon_profile bij run |
| `rcm_desktop/adapter/fm_results_table_model.py` | FMResultsSortProxy |
| `tests/perf/test_slice36_regression.py` | Performance contracts |

---

*Laatst bijgewerkt: 2026-05-21 — slice 36 af; commit 15b5d5c; follow-up slice 37 lazy presentatie.*
