# Kanban handoff — Slice 106: Werkruimte seam-verdieping

**PRD:** `.scratch/rcm-desktop-slice106-werkruimte-seam-verdieping/PRD.md`  
**Triage:** `done` — alle issues 01–04 afgerond (2026-06-18)  
**Volgorde:** 01 → 02 → 03; 04 parallel na 01 (merge na 02 aanbevolen)

## Batch-voortgang (AFK-batch 2026-06-18)

| Issue | Status | Tests |
|-------|--------|-------|
| 01 Navigatie view_id canoniek | done | `test_slice106_view_id_canonical.py` |
| 02 Faalwijze presentation bundle | done | `test_slice106_faalwijze_bundle.py` |
| 03 Bind coordinators | done | `test_slice106_bind_coordinators.py` |
| 04 SimulationWorkspaceController | done | `test_slice106_simulation_controller.py` |

### Slice 105 HILT-blockers (zelfde batch)

| Blocker | Status | Tests |
|---------|--------|-------|
| B1 FM-editor shell v2 (sidebar nav) | done | `test_slice105_fm_editor_tabs_robust.py` |
| B3 QSS dropdown/pijltjes | done | `rcm2.qss` compact combobox |
| B5 LCC PM-type filter | done (was al OK) | `test_slice105_lcc_pm_type_filter.py` |

### Slice 105 HILT105 GO — follow-up (2026-06-18)

| Issue | Kanttekening | Status |
|-------|--------------|--------|
| 16 | What-if menu effect | done |
| 17–22 | b–g polish | done |

**Volgorde na 106-01:** 18 → 20 → 19 → 21 → 22 → 17 → 16, dan **106-02**

## Issues

| # | Tranche | Start |
|---|---------|-------|
| 01 | 106-A Navigatie `view_id` canoniek | `/tdd slice 106 issue 01` |
| 02 | 106-B Faalwijze presentation bundle | `/tdd slice 106 issue 02` |
| 03 | 106-C Bind coordinators + venster cleanup | `/tdd slice 106 issue 03` |
| 04 | 106-D SimulationWorkspaceController | `/tdd slice 106 issue 04` |

## Pytest subset per tranche

```bash
# 01
pytest tests/test_desktop_results_workspace_state.py tests/test_slice79_view_registry.py tests/test_slice79_workspace_navigation_state.py -q

# 02
pytest tests/test_results_workspace_orchestrator.py tests/test_slice104_fm_single_run_compact_table.py tests/test_slice105_fm_detail_binding.py -q

# 03
pytest tests/test_slice62_panel_gate.py tests/test_desktop_results_workspace_window.py tests/test_slice105_fm_detail_binding.py -q

# 04
pytest tests/test_slice98_fm_run_mode_switch.py tests/test_slice100_mc_p50_rollups.py tests/test_slice103_fm_detail_ui.py -q
```

## Bron

Architectuurreview 2026-06-18 — candidates 1–4 (strength **Strong**).
