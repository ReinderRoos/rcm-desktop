# Kanban-handoff — slice 49 FM-editor UX & modelwaarschuwingen (2026-05-26)

**Slice-status:** **af** (reconcile slice 50-01, 2026-05-26)

**Geen nieuw werk onder slice 49** tijdens slice **46-spine** (gaps → 46-issue of bugfix).

---

## Kanban-status (issues)

| # | Titel | Triage |
|---|--------|--------|
| 01 | Taakgroep-dropdown + `normalize_optional_fk` | **done** |
| 02 | MTTF→sigma (15%, tenzij handmatig) | **done** |
| 03 | FM-detail behouden na editor OK | **done** |
| 04 | `FmEditConsistencyService` aging/REV | **done** |
| 05 | Cross-component taakgroep-hint | **done** |

---

## Tests (reconcile 2026-05-26)

```powershell
python -m pytest tests/test_slice49_fm_editor_ux.py `
  tests/test_desktop_results_workspace_window.py::test_fm_editor_ok_updates_mttf_and_triggers_incremental_run -q
# 14 passed
```

---

## Code-ankers

- `fk_normalization.py`, `pm_task_group_delegate.py`, `fm_sigma_coupling.py`, `fm_edit_consistency.py`
- `app_state.py` (`preserve_workspace_ui`), `fm_editor_dialog.py`, `results_workspace_window.py`
- Test-seams: `presentation_lazy_service.py`, `workspace_view_service.py`
