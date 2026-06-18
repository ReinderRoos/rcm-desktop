# Kanban-handoff — slice 96 Modelvergelijking v1

**Datum:** 2026-06-18  
**Status:** slice 96 GO — issues 01–06 done (HILT96 2026-06-18)

## Sessie — AFK batch 01–05

### Gedaan

| Issue | Omschrijving | Tests |
|-------|--------------|-------|
| 01 | Uniformeren-UI verwijderd uit `CompareModelsWindow` | `test_slice96_compare_read_only_scope.py` |
| 02 | FM-uitlijning: id → fingerprint (stable sorted greedy) → unmatched | `test_slice96_fm_alignment_fingerprint.py` |
| 03 | Schema-gedreven invoerdiffs via `ENTITY_SCHEMAS["faalwijzes"]` + exclusions | `test_slice96_schema_input_diffs.py` |
| 04 | `compare_results_service`: cache-hydrate + Run A/B/both; US16 side-by-side | `test_slice96_result_diffs_run_cache.py` |
| 05 | A/B-kleuren, match-badges, diff-highlight, run/cache-strip | `test_slice96_compare_visual_presentation.py` |

### Belangrijkste bestanden

- `rcm_desktop/adapter/compare_align_service.py` — fingerprint fallback
- `rcm_desktop/adapter/compare_diff_service.py` — registry fields + US16 result diffs
- `rcm_desktop/adapter/compare_results_service.py` — cache/run orchestration
- `rcm_desktop/adapter/compare_visual_presentation_service.py` — DTO visual flags
- `rcm_desktop/adapter/compare_workspace_presentation_service.py` — badges + run status
- `rcm_desktop/views/compare_models_window.py` — read-only UI + run buttons + strip

### Regressie

Slice 95 compare/uniformeren tests aangepast en groen:
- `test_slice95_compare_chain.py`
- `test_slice95_compare_workspace_ui.py`
- `test_slice95_uniformeren.py` (UI-test: normalization hidden)

## HILT96 (2026-06-18)

**Besluit:** GO op twee klantprojectparen.

**Kanttekening:** resultaten/vergelijking in detailpaneel lastig te interpreteren
(non-blocking voor v1).

**Productbesluit (analist):** apart veld `library_id` op faalwijze — niet
`library_ref`. Stabiel meekopiëren; primair match-key voor compare/uniformeren
(slice 97+). Zie CONTEXT.md **Library-ID (faalwijze)**.

## Volgende stap

- Slice 96 committen + PR
- Slice 97: `library_id` in domein + copy-regels + compare-alignment + uniformeren
