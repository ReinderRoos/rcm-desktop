# Kanban-handoff — slice 59 FM-editor create-workflow

**Doel:** End-to-end FM aanmaken en opbouwen in FM-detail. Lees `PRD.md` + dit bestand.

**Repo:** `rcm-desktop`  
**Slice-map:** `.scratch/rcm-desktop-slice59-fm-editor-create-workflow/`  
**GitHub parent:** https://github.com/ReinderRoos/rcm-desktop/issues/22

---

## Kanban-status (issues)

| # | Titel | Triage | Opmerking |
|---|--------|--------|-----------|
| 01 | Create FM + toolbar | **done** | `fm_create_service`, `seed_create_bundle`, `insert_fm_scope`, werkruimte-knop |
| 02 | Opslaan-lifecycle | **done** | Opslaan / Opslaan en sluiten / Annuleren + buffer reload |
| 03 | Vul van… | **done** | `fm_field_copy_service` + picker in dialog |
| 04 | Preventief taakgroep UX | **done** | `task_group_catalog_service`, `pm_measure_link_service` |
| 05 | Tab Resultaten | **done** | `fm_editor_results_view_service` + verversing na Opslaan |

**Slice 59:** functioneel **af** voor PRD v1.

---

## Wat werkt

### Gebruikersflow

1. Modus **FM-detail** → selecteer **leaf-PBS** in sidebar.
2. **Nieuwe faalwijze** → editor in create-modus (`pbs_id` vast, auto `FM-###`).
3. Vul minimaal omschrijving + MTTF > 0 → **Opslaan** of **Opslaan en sluiten**.
4. Optioneel **Vul van…** (Basis + Correctief), PM/taken op tab Preventief, **Koppel aan bestaande maatregel…** / **Nieuwe taakgroep…**.
5. Tab **Resultaten** na run (lege staat: “Opslaan om resultaten te berekenen”).

### Architectuur

```
Werkruimte (FM-detail)
  → FmEditorDialog (create | edit)
  → FmCreateService / seed_create_bundle / insert_fm_scope
  → commit_fm_edit → incrementele run
  → FmEditorResultsViewService (read-only tab)
```

---

## Pytest-subset

```powershell
python -m pytest tests/test_slice59_fm_create.py tests/test_slice59_services.py `
  tests/test_slice59_fm_editor_dialog.py tests/test_workspace_modus_ui_ab.py::test_new_fm_button_only_visible_in_fm_detail -q
```

Regressie FM-edit:

```powershell
python -m pytest tests/test_desktop_fm_edit_services.py tests/test_slice49_fm_editor_ux.py `
  tests/test_editing_host.py -q
```

---

## Belangrijkste bestanden

| Pad | Rol |
|-----|-----|
| `rcm_desktop/adapter/fm_create_service.py` | Allocate id, defaults, minimumvalidatie |
| `rcm_desktop/adapter/fm_edit_scope_loader.py` | `seed_create_bundle` |
| `rcm_desktop/adapter/fm_edit_commit_service.py` | `insert_fm_scope`, `apply_fm_scope` |
| `rcm_desktop/adapter/fm_field_copy_service.py` | Vul van… |
| `rcm_desktop/adapter/task_group_catalog_service.py` | Taakgroep-picker |
| `rcm_desktop/adapter/pm_measure_link_service.py` | Koppel PM aan groep |
| `rcm_desktop/adapter/fm_editor_results_view_service.py` | Tab Resultaten DTO |
| `rcm_desktop/views/fm_editor_dialog.py` | UI: tabs, knoppen, lifecycle |
| `rcm_desktop/views/results_workspace_window.py` | Nieuwe faalwijze-knop |

---

*Laatst bijgewerkt: 2026-06-04 — slice 59 afgerond.*
