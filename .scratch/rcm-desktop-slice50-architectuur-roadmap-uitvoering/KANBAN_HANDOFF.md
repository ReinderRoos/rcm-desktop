# Kanban-handoff — slice 50 architectuur-roadmap (2026-05-26)

**Doel:** Coördinatie reconcile → 46-spine → post-46 → slice 41 gate. Lees `PRD.md` + dit bestand.

**Repo:** `rcm-desktop`  
**Slice-map:** `.scratch/rcm-desktop-slice50-architectuur-roadmap-uitvoering/`

---

## Kanban-status (slice 50 issues)

| # | Titel | Triage | Opmerking |
|---|--------|--------|-----------|
| 01 | Reconcile slice 49 | **done** | 49-01..05 `done`; 45 tests groen (subset) |
| 02 | Reconcile slice 46 | **done** | 46-01..07 `done`; 46-08/09 open gap |
| 03 | Unified `load_fm_edit_scope` | **done** | `fm_edit_scope_loader.py`; compat wrappers in bundle service |
| 04 | `commit_fm_edit` façade | **done** | `fm_edit_commit_facade.py`; editor + werkruimte-grid |
| 05 | Start-gate slice 41 PR1 | **done** | 2026-05-27 — AFK via slice 53 issue 02; **GO** PR1a |

---

## Reconcile-resultaten

### Slice 49 — **af**

Alle acceptance criteria bewezen; tests groen. **Geen verder werk onder slice 49** tijdens 46-spine.

```powershell
python -m pytest tests/test_slice49_fm_editor_ux.py `
  tests/test_desktop_results_workspace_window.py::test_fm_editor_ok_updates_mttf_and_triggers_incremental_run -q
# 14 passed (2026-05-26, slice 50-01)
```

### Slice 46 — **deels af**

| Issues | Status |
|--------|--------|
| 01–07 | **done** |
| 08 | **done** — `EditingHost`; grid→editor in `test_editing_host.py`; registry nog compat (09) |
| 09 | **done** — werkruimte batch-grid host + registry verwijderd |

**Eerste open 46-issue voor implementatie:** — *(geen; 46 afgerond).*

```powershell
python -m pytest tests/test_desktop_faalwijzen_edit_service.py `
  tests/test_desktop_validate_faalwijzen_panel.py `
  tests/test_desktop_fm_edit_services.py -q
# 32 passed (2026-05-26, slice 50-02)
```

---

## Post-46 verdieping (50-03 / 50-04)

- **Loader:** `rcm_desktop/adapter/fm_edit_scope_loader.py` — `load_fm_edit_scope(project | EditingSession, fm_id)`
- **Commit:** `rcm_desktop/adapter/fm_edit_commit_facade.py` — `commit_fm_edit(session, bundle | None, …)`
- Editor: `fm_editor_dialog.py`; async: `fm_edit_commit_runner.py`; werkruimte grid-sluiten: `results_workspace_window.py`

```powershell
python -m pytest tests/test_desktop_fm_edit_services.py tests/test_slice49_fm_editor_ux.py -q
# 27 passed (2026-05-26, slice 50-03/04)
```

---

## 41-tech-debt (voor slice 41)

1. Test-dispatchers `presentation_lazy_service` / `workspace_view_service` → injecteerbare builders (slice 41)
2. ~~Unified FM loader~~ → **done** (50-03)
3. ~~Commit-façade~~ → **done** (50-04); grid validate-window save-pad nog `materialize_for_save` (legacy)
4. ~~`EditingHost` i.p.v. `faalwijzen_grid_registry`~~ → **done** (46-08/09)
5. `DirtySessionCoordinator` Qt uit adapter naar views (46-08)
6. `ResultsWorkspaceOrchestrator` / presentatie-cache merge (slice 41)
7. Legacy validate/compare opruiming (ADR-0006)

---

## Aanbevolen volgorde (bijgewerkt)

1. ~~50-01 → 50-02~~ **done**
2. ~~46-08 → 46-09~~ **done** (FM-spine afgerond)
3. ~~50-03 → 50-04~~ **done**
4. ~~**50-05** HITL → slice **41** PR1~~ **done** (2026-05-27, slice 53 gate)

### 50-05 afgerond (slice 53 issue 02)

- **GO** voor slice 41 / slice 53 PR1a (render/bind zonder `core()` in view).
- Gate: `python -m pytest tests/test_slice53_issue02_gate50_05.py -q` (29 tests: FM-spine + EditingHost).
- Handoff checklist: scope loader, commit façade, EditingHost — zie slice 53 `KANBAN_HANDOFF.md`.

---

*Laatst bijgewerkt: 2026-05-27 — 50-05 AFK gate afgerond.*
