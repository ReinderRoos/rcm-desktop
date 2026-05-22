# Kanban-handoff — slice 37 lazy presentatie-cache (2026-05-21)

**Doel:** Vastlegging voor vervolgsessie. Lees dit + `PRD.md`.

**Repo:** `rcm-desktop`  
**Slice-map:** `.scratch/rcm-desktop-slice37-lazy-presentatie-cache/`  
**Parent:** slice 36 follow-up

---

## Kanban-status (issues)

| # | Titel | Triage | Opmerking |
|---|--------|--------|-----------|
| 01 | Contribution-only post-run | **done** | RunRunner + PresentationRebuildRunner |
| 02 | Cache schema v3 | **done** | `PRESENTATION_CACHE_VERSION=3`; v2 backward load |
| 03 | Verwijder dode NB/PM/LCC builds | **done** | Hot path alleen `build_contribution_presentation` |
| 04 | Lazy LCC via render_index | **done** | `presentation_lazy_service.warm_lcc_render_index` |
| 05 | Perf-contract slice 37 | **done** | `test_slice37_regression.py` |

**Slice status:** tracer-bullet **af**.

---

## Wat werkt

1. Post-run **Presentatie…** bouwt alleen Bijdragen-blok (~LTAP-vrij).
2. LCC eerste bezoek → `WorkspaceRenderIndex`; tweede bezoek cache-hit.
3. v2 presentatie-cache laadt nog (legacy velden optioneel).

### Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_desktop_presentation_cache_service.py `
  tests/test_desktop_presentation_lazy_service.py tests/test_desktop_run_runner_presentation.py -q
.\.venv\Scripts\python.exe -m pytest -m perf tests/perf/test_slice37_regression.py tests/perf/test_slice36_regression.py -q
```

---

## Belangrijkste bestanden

| Pad | Rol |
|-----|-----|
| `rcm_desktop/adapter/presentation_cache_service.py` | v3 schema; contribution-only build |
| `rcm_desktop/adapter/presentation_lazy_service.py` | Lazy LCC + rebuild-beslissing |
| `rcm_desktop/adapter/run_runner.py` | Post-run contribution |
| `rcm_desktop/views/results_workspace_window.py` | warm_lcc_render_index |
| `tests/perf/test_slice37_regression.py` | Call-count contracts |

---

*Laatst bijgewerkt: 2026-05-21 — slice 37 lazy presentatie af.*
