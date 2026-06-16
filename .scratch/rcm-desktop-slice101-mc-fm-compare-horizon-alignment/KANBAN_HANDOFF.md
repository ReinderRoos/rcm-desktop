# Kanban-handoff — slice 101 MC FM horizon alignment

**Datum:** 2026-06-16  
**Status:** AFK 01–08 done; HILT101 overgeslagen (productbesluit 2026-06-16)

## Afgerond (AFK-batch HILT101 follow-up)

| Issue | Onderwerp | Tests |
|-------|-----------|-------|
| 01 | `apply_presentation_scale_to_mc_rows` helper | `test_slice101_mc_fm_presentation_scale.py` (5) |
| 02 | Single-run MC FM pad | `test_slice101_mc_fm_single_run_scale.py` (1) |
| 03 | Compare MC FM slot | `test_slice101_mc_fm_compare_scale.py` (1) |
| 04 | Mixed compare regressie | `test_slice101_mixed_fm_compare_horizon.py` (1) |
| 06 | Lifecycle / per-year parity (HILT101 blocking) | `test_slice101_lifecycle_fm_parity.py` (2) |
| 07 | LCC MC compare zonder analytical (HILT101 blocking) | `test_slice101_mc_lcc_compare_without_analytical.py` (2) |
| 08 | RF-kolom MC ↔ analytisch | `test_slice101_mc_rf_column.py` (1) |

## Kernwijzigingen (batch 2)

1. **`simulation_engine_service._horizon_profile_for_mc_p50_fm`:** `cor_eur` niet meer geschaald naar MC CM-totalen — behoud analytische bucket-spine voor `kosten_scalar_for_fm` (per-year parity).
2. **`result_view_service.apply_presentation_scale_to_mc_rows`:** band-denominators uit synthetische `FMResult` (niet ruwe MC P50) — correcte lifecycle-presentatie.
3. **`compare_view_service`:** `resolve_compare_slot_run` + `run_mode=snap.run_mode` voor LCC compare — MC-slot bouwt LCC uit `mc_run.fm_results` ook zonder live analytical run.
4. **`build_mc_fm_rows`:** RF via `_resolve_rf_for_fm` (zelfde als analytisch).

## HILT101 (was NO-GO)

| Check | Was | Fix |
|-------|-----|-----|
| Ø per jaar MC FM | ✅ | — |
| Lifecycle MC vs analytisch | ❌ | issue 06 — profile + band denominators |
| LCC MC zonder prior analytical | ❌ | issue 07 — compare slot run resolve |
| RF kolom | ⚠️ | issue 08 |

Zie `HILT101_HANDCHECK.md`.

## Open

Geen — slice 101 afgesloten (2026-06-16).

## Batch-voortgang (AFK-batch 2026-06-16)

| Issue | Outcome | Tests |
|-------|---------|-------|
| (docs) | ADR-0018 §Presentatie v1.2 — FM MC horizon-pariteit | n/a |

Regressie: `pytest tests/test_slice100_*.py tests/test_slice101_*.py` — 54 passed

## Regressie (batch)

`pytest tests/test_slice101_*.py` — 13 passed
