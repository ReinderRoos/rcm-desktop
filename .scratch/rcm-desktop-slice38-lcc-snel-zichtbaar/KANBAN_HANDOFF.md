# Slice 38 — LCC snel zichtbaar — KANBAN HANDOFF

**Datum:** 2026-05-21  
**Status:** klaar voor handmatige validatie

## Wat is gebouwd

| Issue | Omschrijving | Status |
|-------|--------------|--------|
| 01 | LCC curve-cache key zonder `calendar_year` | done |
| 02 | Curve-builder dedup (reconcile + inactive overlay) | done |
| 03 | LTAP PM cost series (light path) | done |
| 04 | Lazy jaardetail render-split in werkruimte | done |
| 05 | LCC achtergrond-warmup na run | done |
| 06 | Perf-contract slice 38 + handoff | done |

## Belangrijkste wijzigingen

- **`lcc_render_cache_service.py`**: gescheiden `curve_key` / `detail_key`; `lcc_render_scope` voor detail-only rerender.
- **`lcc_planning_service.py`**: inactive-overlay fast path; één reconciliatie; light path via `build_ltap_pm_cost_series`.
- **`ltap_pm_cost_series.py`**: PM-totalen per jaar zonder `LTAPTaskDetail`.
- **`lcc_warmup_runner.py`**: achtergrond-warmup default LCC-curve na run.
- **`results_workspace_window.py`**: curve-key split, detail-only jaarklik, warmup na run, render-index reset na run.

## Tests

```bash
# Unit / adapter (zonder perf-mark)
pytest tests/test_desktop_lcc_render_cache.py \
       tests/test_desktop_lcc_year_click_cache.py \
       tests/test_desktop_lcc_curve_builder_dedup.py \
       tests/test_desktop_ltap_pm_cost_series.py \
       tests/test_desktop_lcc_warmup_runner.py \
       tests/test_desktop_lcc_year_detail_curve.py \
       tests/test_slice28_lcc_planning.py

# Perf-contracten slice 38
pytest -m perf tests/perf/test_slice38_regression.py
```

## Handmatige Haarlem-checklist

Fixture: `tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json`

1. **Run + LCC open** — na analyse naar Tijdsplot; grafiek + jaartabel binnen enkele seconden.
2. **Jaarklik 3×** — wissel tussen jaren; geen merkbare pauze door curve-herbouw.
3. **Toon alle jaren** — detail leeg; grafiek blijft.
4. **What-if + shift** — toggle aan, jaar selecteren, één taak verschuiven; curve en detail consistent.
5. **Filter toggle** — CM/REV uit/aan; curve herbouwt; jaarklik daarna nog snel.
6. **Regressie** — Bijdragen/FM-detail/run-flow nog responsief (slice 36/37).

## Verwachte winst

- Jaarklik: 0 curve-rebuilds (cache-hit).
- Inactive overlay: 1 light-path LTAP-build per curve (was 2 full LTAP).
- Plot-build: geen `LTAPTaskDetail`-allocatie; jaardetail blijft full LTAP-view.
- Warmup: LCC vaak warm vóór eerste modusbezoek na run.
