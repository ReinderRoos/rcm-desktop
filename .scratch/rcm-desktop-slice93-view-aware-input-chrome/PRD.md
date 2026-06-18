# PRD: View-aware input chrome (slice 93)

**Triage-label:** `done`

## Problem Statement

Na slice 79/91 deelt `output.fm_results` legacy modus `fm_detail` met oude
FM-detail-chrome. De knop **Nieuwe faalwijze** en het menu-item **Faalwijzen-grid**
verschijnen daardoor op de FM-resultatentabel (output), terwijl ze bij
`input.faalwijzen` horen. Kolom-bijsnijden (`column_crop`) werd ten onrechte aan
`new_fm_visible` gekoppeld.

## Solution

Orchestrator plant FM/input-chrome op `active_view_id` (niet alleen `modus`):
- `input.faalwijzen` → `new_fm_visible`, `batch_faalwijzen_visible`
- `output.fm_results` → `column_crop_visible`, FM-inspector, NB-filter-subbar
- Ontkoppel `column_crop` van `new_fm_visible` in `workspace_toolbar_sync`.

## Testing

- `tests/test_slice93_view_aware_input_chrome.py` (orchestrator + UI)
- Update `tests/test_workspace_modus_ui_ab.py`
- Update `tests/test_results_workspace_orchestrator.py` waar nodig
