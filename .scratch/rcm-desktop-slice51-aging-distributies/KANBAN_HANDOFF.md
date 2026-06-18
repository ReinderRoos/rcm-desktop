# Kanban-handoff — slice 51 aging-distributies

**Status slice:** **done** (reconcile slice 53 issue 01, 2026-05-27)

## Issues

| # | Titel | Triage | Bewijs |
|---|--------|--------|--------|
| 01 | Weibull 2p E2E | **done** | `tests/test_slice51_aging_distributions.py` |
| 02 | truncated_normal_0 E2E | **done** | idem (`test_truncated_normal_has_zero_mass_below_zero`) |
| 03 | Backwards compat + schema | **done** | `test_legacy_faalwijze_defaults_to_normal_distribution`; `CACHE_INPUTS_VERSION` 106 |
| 04 | Haarlem AWZI + Weibull subset | **done** | `test_haarlem_*` in slice51 + `test_haarlem_fixture_import_ready.py` |
| 05 | UI polish editor/grid | **done** | FM-editor + `validate_faalwijzen_panel` combo’s |

## Gap (geen blocker)

- Dedicated **Monte Carlo ↔ analytisch Weibull parity**-test ontbreekt; gedekt door closed-form + sampling-tests in `test_slice51_aging_distributions.py`.

## Pytest

```powershell
python -m pytest tests/test_slice51_aging_distributions.py -q
```
