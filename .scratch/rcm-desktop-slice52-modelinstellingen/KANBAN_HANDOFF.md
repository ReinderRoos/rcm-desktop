# Kanban-handoff — slice 52 Modelinstellingen

**Status slice:** **done** (reconcile slice 53 issue 01, 2026-05-27)

## Issues

| # | Titel | Triage | Bewijs |
|---|--------|--------|--------|
| 01 | Project + horizon E2E | **done** | `tests/test_slice52_modelinstellingen.py` (metadata, digest, dialog smoke) |
| 02 | default_sigma_fraction live | **done** | `effective_sigma(config)`; `CACHE_INPUTS_VERSION` 106 |
| 03 | Veroudering defaults + apply | **done** | `TestApplyDefaultAging`, model_settings_dialog UI |
| 04 | Direct herberekenen + import | **done** | `test_commit_with_direct_rerun_returns_run_result`, `test_prefill_from_description` |

## Pytest

```powershell
python -m pytest tests/test_slice52_modelinstellingen.py -q
```
