# Kanban-handoff — slice 66 REV-segment survival fix

**Status slice:** **done** (issues 01–03, 2026-06-05)  
**PRD:** `PRD.md`  
**Parent:** ADR-0008 (modelcontrole AW); slice 65 (parity-gate); slice 52 (`aw_mc_lifecycle_horizon`); slice 51 (REV-segmenten)

## Root cause en fix

In `_conditional_failures_with_rev_segments` (`rcm_core/distributions.py`) werd de conditionele overlevingskans `survival = 1 − F(effective_age)` **één keer** aan studiestart berekend en als **noemer voor elk REV-segment** hergebruikt. Na een REV-rejuvenatie daalde de effectieve leeftijd, maar de noemer bleef extreem klein (~2·10⁻⁷ voor oud asset). Het quotiënt `(f_hi − f_lo) / survival` explodeerde naar honderdduizenden `expected_failures` — zichtbaar op anker-FM `06H-350.2.12.2.1.A.1` (leeftijd 44 jr, MTTF 25, REV elke 20 jr).

**Fix (issue 01):** herbereken `survival_seg` aan het begin van **elk** REV-segment op de actuele `age` na eerdere rejuvenaties. `CACHE_INPUTS_VERSION` → 107.

## Causaliteit bug ↔ AW MC-horizon

```
aw_mc_lifecycle_horizon=True  (slice 52; handmatig inschakelen)
  → studiehorizon = current_age + lifecycle_years (langere kalender)
  → oude assets doorlopen meerdere REV-cycli
  → stale survival-noemer in REV-segmenten (latente bug sinds slice 51)
  → expected_failures ×10⁵–10⁶ → total_cost / downtime explodeert
  → ADR-0008 parity-gate: 128/135 fail (baseline vóór fix)
```

**Na fix:** REV-survival-explosies verdwijnen (`expected_failures_rcm > 10⁴` → 0 FMs). Parity `fail_count` blijft **128** op Gaarkeuken — residuele AW-gaps (MC vs analytisch, import, scenario) buiten scope slice 66.

**Config:** `aw_mc_lifecycle_horizon` default blijft **`False`** in `RCMConfig`; analist schakelt bewust in voor parity-werk na deze fix.

## Issues

| # | Titel | Triage | Bewijs |
|---|--------|--------|--------|
| 01 | REV-segment survival kernfix | **done** | `tests/test_rev_segment_survival.py`; `CACHE_INPUTS_VERSION` 107 |
| 02 | Gaarkeuken parity-gate regressie | **done** | `tests/test_gaarkeuken_parity_gate.py` |
| 03 | Documentatie + causaliteit | **done** | dit bestand; `tests/test_slice66_handoff.py` |

## Reproduceerbare parity-check (Gaarkeuken)

Fixture: `tests/fixtures/RCMCostdata export_Gaarkeuken.rcm.json` (135 FM's, `aw_mc_lifecycle_horizon=True` in project).

```python
from pathlib import Path
from rcm_core.engine import run_analytical
from rcm_core.persistence import load_project
from rcm_core.rcm_cost_benchmark import build_parity_report

fixture = Path("tests/fixtures/RCMCostdata export_Gaarkeuken.rcm.json")
project = load_project(fixture)
fm_results, _ = run_analytical(project, parallel=False)
report = build_parity_report(project, fm_results)
print(report.summary)  # vóór fix: fail_count=128; geen ef_rcm > 10⁴ na fix
```

```powershell
python -m pytest tests/test_gaarkeuken_parity_gate.py tests/test_rev_segment_survival.py tests/test_slice66_handoff.py -q
```

## Anker-FM (regressie)

| Veld | Waarde |
|------|--------|
| FM | `06H-350.2.12.2.1.A.1` |
| lifecycle=70 | `expected_failures` ≈ 2 (OK) |
| lifecycle=90 vóór fix | `expected_failures` ≈ 450.603 (BUG) |
| na fix | `expected_failures_rcm` < 50; geen ×10⁵ kostenfactor |

## Verwijzingen

- **ADR-0008** — modelcontrole AW; gate die 128/135 baseline signaleerde
- **Slice 65** — parity-gate UI + `build_parity_report`
- **Slice 52** — `aw_mc_lifecycle_horizon` modelinstelling
- **Slice 51** — REV-segmentatie in aging-distributies
