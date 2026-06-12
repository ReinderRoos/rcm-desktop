# KANBAN handoff — slice 67 (parity-rekenbugs)

**Status:** afgerond (golf 1–7)  
**Parent:** ADR-0008; slice 66 (REV-survival); slice 65 (validatie-export)

## Probleem (baseline vóór slice 67)

Gaarkeuken-fixture: **128/135** cost-parity fails; validatie-export **114/139** # falen-fails. Dominante oorzaakcodes: **B1** (repair_quality=1.0 default), **A2** (horizon), **A1** (MC-residu).

## Oplossingen per golf

| Golf | Issue | Wijziging |
|------|-------|-----------|
| 1 | 01 | `repair_quality` fallback **0.0** (as-old) wanneer AW-kolom ontbreekt; `import_settings.repair_quality_source` |
| 2 | 02 | REV `aging_effect_pct=100%` default (reeds slice 35; regressie bevestigd) |
| 3 | 03 | `rcm_core.cm_overlay.materialize_cm_overlay_project` — run aligned met `ef_cm_overlay` |
| 4 | 04 | Horizon-playbook in modelinstellingen-tooltip + dit document |
| 5 | 05 | `rcm_core.input_parity_audit` — MTTF parity groen; InitialAge-mismatches gedocumenteerd (B3) |
| 6 | 06 | `rcm_core.rev_interval_audit` — overlay-only REV gedocumenteerd (D1/D2) |
| 7 | 07 | Regressietests + parity-gate bewaking (geen REV-explosies; fail_count ≤ 128) |

## Analist playbook (stap 0+)

1. **Herimport** AW Excel (`RCMCostdata export_*.xlsx`) — niet het validatie-xlsx.
2. **Modelinstellingen:** `aw_mc_lifecycle_horizon` aan als # falen vs AW TotalW leidend is (A2).
3. **Run** met CM-overlay (automatisch geseed uit `aw_disabled_pm_ids` bij import).
4. **Validatie-export** — controleer oorzaakcodes; B1 zou afnemen na slice 67-import.
5. **Overlay reset** naar import-seed als C4 (handmatige overlay) dominant is.

## Reproduceerbare checks

```bash
pytest tests/test_slice67_issue01_repair_quality.py tests/test_slice67_parity_rekenbugs.py -q
pytest tests/test_gaarkeuken_parity_gate.py -q
```

```python
from pathlib import Path
from rcm_core.persistence import load_project
from rcm_core.engine import run_analytical
from rcm_core.cm_overlay import materialize_cm_overlay_project
from rcm_core.rcm_cost_benchmark import build_parity_report

p = load_project(Path("tests/fixtures/RCMCostdata export_Gaarkeuken.rcm.json"))
fm, _ = run_analytical(materialize_cm_overlay_project(p), parallel=False)
print(build_parity_report(p, fm).summary)
```

## Post-fix status (2026-06-05)

- `repair_quality`: **0.0** op alle Gaarkeuken-FM's (`missing_default_0`)
- CM-overlay run: median `|Δ scenario| = 0` (135/135 FM's)
- `ef_actual ≈ ef_rq_0` na repair_quality-fix
- Cost-parity **128/135** blijft — resterende gap = A1/A2/A4 residu (geen rekenbug)
- Geen `expected_failures_rcm > 10⁴` (slice 66 regressie)

## Fixes A2 + B3 (2026-06-10)

### A2 — LifeTime-semantiek

`aw_mc_lifecycle_horizon` default omgezet van `False` naar `True` in `rcm_core/config.py`.
RCM2 hanteert nu altijd de volledige LCC-methode: `lifecycle_years` jaar **vooruit** ongeacht
initiële leeftijd. Beide Gaarkeuken-fixtures bijgewerkt; drie test-assertions omgekeerd
(`test_aw_mc_lifecycle_horizon_default_is_true` in slice66/67 handoff-tests).

### B3 — InitialAge mismatch (import)

`InitialAge=0` (= "onbekend" in AW-export) wordt nu overgeslagen bij opbouw van `ia_by_pbs`
in `isograph_import_service.py`. Gevolg: 19 van 26 PBS-conflicts in het PM-scenario zijn
opgelost. De 7 echte multi-leeftijd-conflicts (bv. `{13yr, 44yr}`) blijven als conflict
geregistreerd — bouwjaar niet gezet.

Bugfix: `int(modeljaar - age_yr)` → `round(modeljaar - age_yr)` voor nauwkeurigere afronding.
Nieuwe test: `test_initial_age_zero_does_not_conflict_with_real_age`.

## PM-scenario controle (2026-06-09)

Aanvullende controle op het PM-scenario (`RCMCostdata export_PM.xlsx`):

- **Inputbestand:** `tests/fixtures/RCMCostdata export_Gaarkeuken_PM.rcm.rcm.json`
- **Controlebestand:** `tests/fixtures/Modellering door Delta Pi_validatie_falenPM.xlsx`
- **Resultaat:** 12 OK / 123 FAIL — **geen software-actieverpunten**
- **Dominante oorzaken:** A2 (LifeTime-semantiek, 57 FM's), A1 (50 FM's), A4 (15 FM's)
- **Conclusie:** Alle afwijkingen zijn modelkeuzes; geen rekenbugs gevonden

Wijziging: `export_validation_workbook` / `export_validation_excel` accepteren nu
`input_file`-parameter — het inputbestand wordt in de Excel-metadata vastgelegd.

Details: `VALIDATIE_RAPPORTAGE_FALENPM.md` in deze map.

## Referenties

- `.scratch/rcm-desktop-slice67-parity-rekenbugs/PRD.md`
- `.scratch/rcm-desktop-slice67-parity-rekenbugs/VALIDATIE_RAPPORTAGE_FALEN5.md`
- `.scratch/rcm-desktop-slice67-parity-rekenbugs/VALIDATIE_RAPPORTAGE_FALENPM.md`
- `docs/adr/ADR-0008-rcm-cost-parity.md`
- `.scratch/rcm-desktop-slice66-rev-segment-survival-fix/KANBAN_HANDOFF.md`
