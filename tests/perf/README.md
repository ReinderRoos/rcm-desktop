# Performance tests (`tests/perf/`)

Standaard draaien **niet** mee in `pytest` (zie `addopts = "-m 'not perf'"` in `pyproject.toml`).

## Slice 36 contracten

```bash
pytest -m perf tests/perf/test_slice36_regression.py
```

Wat wordt gecontroleerd (geen wall-clock timing in CI):

| Contract | Drempel (`baseline.json` → `slice36_contracts`) |
|----------|--------------------------------------------------|
| Cache-hit run | `recalculated_fm_count == 0` |
| LCC-planningcurve | ≤ 2 LTAP-view builds |
| LCC chart + jaardetail | ≤ 2 LTAP **builds**; 0 curve-rebuilds bij injected curve |
| Metric-toggle Bijdragen | geen LCC in `required_detail_builders` |

## Handmatige Haarlem-benchmark

Referentie-fixture: `tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json`

Timing uit `baseline.json` (pre-slice-24, handmatig gemeten):

- Volledige run ~120 s
- Herhaalde run met geldige cache ~5 s

Na code-upgrade: één langzame run bij digest-mismatch is normaal; daarna cache-snelheid.

## Overige perf-tests

```bash
pytest -m perf tests/perf/
```

- `test_normal_fast_micro.py` — micro-benchmarks normaalverdeling-helpers
- `test_slice24_regression.py` — placeholder slice 24 (legacy pad)
