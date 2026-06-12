# Kanban-handoff — slice 46 FM-bewerken fase 2 (2026-05-26)

**Slice-status:** **af** — 01–09 done

**Slice 41:** uitgesteld tot **46-09** done + HITL **50-05**.

---

## Kanban-status (issues)

| # | Titel | Triage | Opmerking |
|---|--------|--------|-----------|
| 01 | `failure_type` + NMF + bulk | **done** | contract + `apply_bulk_change` + panel delegates |
| 02 | Must-kolommen | **done** | `faalwijzen_grid_contract` must+should |
| 03 | Filters, zoek, bulk zichtbaar | **done** | `FaalwijzenFilterProxy` + panel; publieke `row_view` **te checken bij 03-touch** |
| 04 | `ValidateFaalwijzenPanel` | **done** | host-neutraal; Validate + werkruimte |
| 05 | `replace_fm_scope` | **done** | adapter + unit tests |
| 06 | `FmEditBundleAssembler` | **done** | `fm_edit_bundle_assembler.py` |
| 07 | RunRunner + dirty guard | **done** | `FmEditCommitRunner`; `dirty_session_coordinator` (Qt in adapter = debt) |
| 08 | Gedeelde sessie + orchestratie | **done** | `EditingHost` + `commit_grid_edits`; Qt dirty guard in views; tests `test_editing_host.py` |
| 09 | Workspace grid-host | **done** | menu batch-grid + registry verwijderd; smoke in werkruimte-test |

**Eerste open issue:** — *(geen; slice 46 afgerond)*

---

## Tests (reconcile 2026-05-26)

```powershell
python -m pytest tests/test_desktop_results_workspace_window.py `
  tests/test_desktop_validate_faalwijzen_panel.py `
  tests/test_editing_host.py -q
# 58 passed, 7 DeprecationWarnings (filter proxy)
```

---

## 41-tech-debt (minimaal 4 items)

1. Presentation test-dispatchers → `PresentationBuilderRegistry` (slice 41)
2. ~~`load_fm_edit_scope`~~ → slice **50-03** done
3. ~~`commit_fm_edit` façade~~ → slice **50-04** done (ValidateWindow save nog legacy `materialize_for_save`)
4. ~~`EditingHost` i.p.v. registry~~ → **done** (46-08/09)
5. ~~Qt dirty-dialog uit adapter~~ → **done** (`views/grid_dirty_guard.py`)
6. Werkruimte-orchestratie / presentatie-cache (slice 41)
7. Legacy validate/compare (ADR-0006, slice 41 PR7)

---

*Laatst bijgewerkt: 2026-05-26 — reconcile via slice 50-02.*
