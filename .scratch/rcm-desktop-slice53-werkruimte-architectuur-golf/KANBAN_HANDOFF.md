# Kanban-handoff — slice 53 resultatenwerkruimte architectuur-golf

**Doel:** Uitvoering grill-me plan (2026-05-27). Lees `PRD.md` + dit bestand.

**Repo:** `rcm-desktop`  
**Slice-map:** `.scratch/rcm-desktop-slice53-werkruimte-architectuur-golf/`  
**Parent slices:** 50 (roadmap), 41 (view deepening), 46/49 (FM-spine, reconcile)

---

## Kanban-status (issues)

| # | Titel | Triage | Opmerking |
|---|--------|--------|-----------|
| 01 | Reconcile + A/B/C doc | **done** | 2026-05-27 — zie reconcile-sectie |
| 02 | Gate 50-05 | **done** | 2026-05-27 — zie Gate 50-05-sectie |
| 03 | PR1a render/bind | **done** | 2026-05-28 — visuele check bevestigd |
| 04 | PR1b ProjectSession | **done** | 2026-05-27 — `workspace_session_service` |
| 05 | Presentatie-seams | **done** | 2026-05-28 — adapter injecteerbare seams |
| 06 | Orchestrator + cache + host | **done** | 2026-05-28 — orchestrator/dirty/host afgerond |
| 07 | Legacy PR7-A | **done** | 2026-05-28 — workspace legacy paden opgeschoond |

---

## Reconcile (issue 01, 2026-05-27)

### Slices 46 / 49

Al **done** vóór slice 53 (geen wijziging).

### Slices 51 / 52

Triage → **done**; handoffs:

- `.scratch/rcm-desktop-slice51-aging-distributies/KANBAN_HANDOFF.md`
- `.scratch/rcm-desktop-slice52-modelinstellingen/KANBAN_HANDOFF.md`

### Sessie A / B / C (productwerk al in repo)

| Item | Gedrag | Tests |
|------|--------|-------|
| **A** | Knop “Faalwijzen batch-bewerken” alleen in **FM-detail** | `test_batch_faalwijzen_button_only_visible_in_fm_detail` |
| **B** | **Tijdsplot (LCC):** KPI, meekoppel, what-if start **ingeklapt** | `test_entering_lcc_modus_collapses_kpi_meekoppel_and_whatif`, `test_lcc_modus_starts_with_collapsed_panels` |
| **C** | **Haarlem** demo import-klaar (Weibull defaults, validatie groen) | `test_haarlem_fixture_validates_without_errors`, `test_haarlem_config_has_weibull_aging_defaults_for_import` |

### Reconcile pytest-gate

```powershell
python -m pytest tests/test_slice53_issue01_reconcile_gate.py -q
```

Subset (48 tests, 2026-05-27 groen): `test_workspace_modus_ui_ab`, `test_haarlem_fixture_import_ready`, `test_desktop_fm_edit_services`, `test_slice49_fm_editor_ux`, `test_slice52_modelinstellingen`, `test_slice51_aging_distributions`.

---

## Gate 50-05 (issue 02, 2026-05-27)

**Slice 50 issue 05** → **done** via AFK zelf-check (geen aparte meeting; tests groen).

### FM-spine pytest

```powershell
python -m pytest tests/test_slice53_issue02_gate50_05.py -q
```

| Subset | Tests | Status |
|--------|-------|--------|
| `test_desktop_fm_edit_services.py` + `test_slice49_fm_editor_ux.py` | 26 | groen |
| `test_editing_host.py` | 3 | groen |

### Checklist (slice 50 post-46)

- [x] **`load_fm_edit_scope`** — `rcm_desktop/adapter/fm_edit_scope_loader.py`; gedekt door `test_load_fm_edit_scope_project_matches_session`
- [x] **`commit_fm_edit`** — `rcm_desktop/adapter/fm_edit_commit_facade.py`; gedekt door `test_commit_fm_edit_*`
- [x] **`EditingHost`** — `rcm_desktop/adapter/editing_host.py`; gedekt door `test_editing_host.py`

**Slice 41 PR1:** **GO** voor issue 03 (PR1a render/bind) — merge-freeze op nieuwe productlogica in het venster blijft tot PR1a merged.

---

## PR1a render/bind (issue 03, 2026-05-27)

Codepad voor render/bind gebruikt geen mutatieproject-toegang meer in `_sync_pbs_tree_for_state`:

- `wss.build_navigation_tree_model_for_session(session)`
- `wss.build_pbs_structure_tree_for_session(session)`

Nieuwe gate-test:

```powershell
python -m pytest tests/test_slice53_issue03_pr1a_gate.py -q
```

Uitgevoerde regressie:

- `python -m pytest tests/test_slice53_issue03_pr1a_gate.py tests/test_desktop_results_workspace_window.py tests/test_slice32_workspace_ux_prios.py -q` → **61 passed**
- `python -m pytest tests/test_workspace_session_service.py tests/test_slice53_pr1b_workspace_session.py tests/test_slice53_issue03_pr1a_gate.py -q` → **6 passed**

Status: **done** (handmatige visuele check bevestigd op 2026-05-28).

---

## Presentatie-seams (issue 05, 2026-05-28)

Adapter-presentatiepad gebruikt geen runtime view-imports meer:

- `rcm_desktop/adapter/presentation_lazy_service.py`
- `rcm_desktop/adapter/workspace_view_service.py`

Testseams lopen via adapter-symbolen (monkeypatch op `presentation_lazy_service` / `workspace_view_service`), niet meer via `results_workspace_window`.

Uitgevoerde regressie:

- `python -m pytest tests/test_desktop_results_workspace_window.py tests/test_workspace_view_service.py tests/test_desktop_presentation_lazy_service.py tests/test_architecture_deepening.py tests/perf/test_slice37_regression.py -q` → **67 passed**

---

## Orchestrator + dirty guard + host (issue 06, 2026-05-28)

Uitgevoerd:

- `ResultsWorkspaceController` uitgebreid met Qt-vrije run/validate planning (`plan_after_successful_run`, `plan_after_validate`).
- View gebruikt geen `_load_presentation_cache` meer; post-run en post-validate volgen controller-plan.
- Dirty-guard policy verplaatst naar adapter (`rcm_desktop/adapter/dirty_guard_policy.py`); view (`grid_dirty_guard`) toont alleen dialoog en vertaalt user-choice.
- `EditingHost` nu per venster gebruikt in `ResultsWorkspaceWindow` en `ValidateWindow` (geen gedeelde process-host in deze paden).

Nieuwe test:

- `tests/test_slice53_issue06_orchestrator.py` (dirty policy, controller-plan, twee vensters/twee hosts, geen legacy helper in workspace-view).

Regressie:

- `python -m pytest tests/test_slice53_issue06_orchestrator.py tests/test_architecture_deepening.py tests/test_desktop_results_workspace_window.py tests/test_editing_host.py tests/test_desktop_run_service.py tests/perf/test_slice37_regression.py -q` → **73 passed**

Cache-merge status:

- **Vervolg-PR nodig**: volledige consolidatie van `presentation_cache_service`, `workspace_presentation_cache`, `presentation_lazy_service` is bewust **niet** in deze PR meegenomen (diff-grootte beheerst gehouden).

---

## Legacy PR7-A cleanup (issue 07, 2026-05-28)

Uitgevoerd:

- Gate toegevoegd: `tests/test_slice53_issue07_legacy_pr7a.py`.
- Werkruimte-view verwijst niet meer naar legacy `workspace_split_layout` / scenario-padnamen.
- ADR-0006 bevestigd in codepad: `CompareRunner` blijft alleen in legacy `ValidateWindow`.

Regressie:

- `python -m pytest tests/test_slice53_issue07_legacy_pr7a.py tests/test_desktop_results_workspace_window.py tests/test_desktop_scenario_compare_service.py -q` → **groen**

---

## Merge-freeze

Tot issue **03** merged: **geen nieuwe productlogica** in resultatenwerkruimte-venster.

**Parallel toegestaan:** slice **42** (motor); slice **51** alleen buiten dat venster (grid/editor/motor) — slice 51 zelf is **done**.

---

## Pytest-subsets (per fase)

```powershell
# 01 Reconcile (gate)
python -m pytest tests/test_slice53_issue01_reconcile_gate.py -q

# 02 Gate 50-05
python -m pytest tests/test_slice53_issue02_gate50_05.py -q

# 04 PR1b
python -m pytest tests/test_slice53_pr1b_workspace_session.py tests/test_workspace_session_service.py tests/test_slice52_modelinstellingen.py tests/test_desktop_fm_edit_services.py -q

# 03 PR1a
python -m pytest tests/test_slice53_issue03_pr1a_gate.py tests/test_desktop_results_workspace_window.py tests/test_slice32_workspace_ux_prios.py tests/test_workspace_modus_ui_ab.py -q

# 05 Presentatie-seams
python -m pytest tests/test_desktop_results_workspace_window.py tests/test_workspace_view_service.py tests/test_desktop_presentation_lazy_service.py tests/test_architecture_deepening.py tests/perf/test_slice37_regression.py -q

# 06 Orchestrator
python -m pytest tests/test_slice53_issue06_orchestrator.py tests/test_architecture_deepening.py tests/test_desktop_results_workspace_window.py tests/test_editing_host.py tests/test_desktop_run_service.py tests/perf/test_slice37_regression.py -q

# 07 Legacy PR7-A
python -m pytest tests/test_slice53_issue07_legacy_pr7a.py tests/test_desktop_results_workspace_window.py tests/test_desktop_scenario_compare_service.py -q
```

---

## Aanbevolen volgorde

01 → 02 → 03 → 04 → 05 → 06 → 07

Daarna: slice **41** PR2 (meekoppel panel service) volgens oorspronkelijke 41-PRD.

---

## Tijdelijke commit-notitie (issue 07)

Voor later handmatig commit/pushen van alleen de issue-07 cleanup:

**Bestanden**

- `rcm_desktop/views/results_workspace_window.py`
- `tests/test_slice53_issue07_legacy_pr7a.py`
- `.scratch/rcm-desktop-slice53-werkruimte-architectuur-golf/issues/07.md`
- `.scratch/rcm-desktop-slice53-werkruimte-architectuur-golf/KANBAN_HANDOFF.md`

**Testcommando**

```powershell
python -m pytest tests/test_slice53_issue07_legacy_pr7a.py tests/test_desktop_results_workspace_window.py tests/test_desktop_scenario_compare_service.py -q
```

---

## PR1b — ProjectSession sync (issue 04)

- View: geen `loaded.core()` / `_session_core`; gebruik `workspace_session_service` + `ProjectSession`.
- `AppState.set_last_project` blijft bron voor `LoadedProject` → `project_session` (ValidateWindow + tests ongewijzigd).
- Dialoog/runners krijgen kern via `wss.editing_project(session)` alleen in adapter-laag.

*Issue 01 afgerond: 2026-05-27. Issue 02 afgerond: 2026-05-27. Issue 03 afgerond: 2026-05-28. Issue 04 afgerond: 2026-05-27. Issue 05 afgerond: 2026-05-28. Issue 06 afgerond: 2026-05-28. Issue 07 afgerond: 2026-05-28.*
