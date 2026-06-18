# Slice 71 — KANBAN handoff

**Status:** done (lokaal, issues niet op GitHub gepubliceerd)

## Wat is gebouwd

| Issue | Deliverable |
|-------|-------------|
| 00 | `test_slice71_cm_overlay_kosten.py`, `KOSTEN_DIAGNOSE.md` |
| 01 | `EffectNbFilterSet`, `nb_scalar_for_fm`, `nb_yearly_series`, `list_nb_effect_klassen` |
| 02 | `build_contribution_rows` + `effect_nb_filter` |
| 03 | Workspace state, legacy normalize, cache key |
| 04 | Top 10 UI: 3 metrics, NB-filter combo, geen Effectklasse-knop |
| 05 | `tijdsplot_curve_service` metric-gedreven curve |
| 06 | Tijdsplot deelt metric + NB-filter via top10_subbar |
| 07 | `CONTEXT.md`, test-migratie, `test_slice71_*.py` |
| 08 | Functierapport via `aggregate` i.p.v. `SOURCE_EFFECTKLASSE` |

## Kosten-diagnose (issue 00)

Gaarkeuken: overlay **154 M** vs raw **172 M** — overlay actief. ~60 M past niet bij projecttotaal; zie `KOSTEN_DIAGNOSE.md`.

## Tests

```powershell
pytest tests/test_slice71_cm_overlay_kosten.py tests/test_slice71_nb_effectfilter.py tests/test_slice71_top10_nb_filter.py tests/test_slice70_regression.py tests/test_slice68_parity_run_alignment.py -q
```

## GitHub

Issues staan in `.scratch/rcm-desktop-slice71-nb-effectfilter-workspace-ux/issues/` — publicatie door analist.
