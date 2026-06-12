# ADR-0008: RCM-Cost resultaat-parity (modelcontrole)

**Status:** accepted  
**Date:** 2026-06-05  
**Parent:** epic parity/portfolio/MC; grill-sessie 2026-06-05; slice **65** (rcm-cost-parity)

## Context

Analisten importeren RCM-Cost/AW-exporten naar RCM2. De Excel-export bevat per
faalwijze **benchmark-resultaten** (`TotalCost`, `TotalTdt`, …) plus
onzekerheidsbanden (`TotalCostErrPc`, `TotalTdtErr`, …). RCM2 berekent eigen
FM-resultaten via de analytische motor.

Doel: **modelcontrole** — per FM (en projecttotaal) rapporteren of RCM2 binnen
de AW-onzekerheidsband valt, zonder stille afwijkingen.

Grill-besluit 1: AW-band is voldoende; geen extra portfolio-€-drempel in v1.

## Decision

### Import (benchmark-metadata)

- Per FM in `import_settings.isograph_causes[fm_id]` bewaren:
  - **Benchmark:** `TotalCost`, `TotalTdt`, `OperationalCost`, `EffectCost`, …
  - **Onzekerheid:** bestaande err-kolommen + `TotalTdtErr`
- Geen wijziging aan domain model; pass-through compat (ADR-0004-stijl).
- Bestaande `.rcm.json` zonder `TotalCost` → parity UI toont “geen benchmark”.

### Pass-criteria (v1)

| Metriek RCM2 | AW-kolom | Gate |
|--------------|----------|------|
| `total_cost_eur` | `TotalCost` | **Ja** — \|Δ\| ≤ max(`TotalCostErrAbs`, `TotalCostErrPc`/100 × AW) |
| `expected_total_downtime_hr + expected_pm_downtime_hr` | `TotalTdt` | **Ja** als `TotalTdtErr` aanwezig; anders informatief |
| Overige kolommen | waar err-kolom bestaat | Zelfde patroon (later uitbreidbaar) |

### Diagnostiek (v1.1 — geen gate)

Per FM extra **rekendiagnostiek** om parity-afwijkingen te verklaren (informative only):

| RCM2 | AW | Doel |
|------|-----|------|
| `expected_failures` | `TotalW` (fallback: `OutageFrequency` × 8760 × lifecycle) | Aantal keer falen |
| REV-momenten actief / structureel | — (afgeleid uit geïmporteerde `RcmScheduledTasks`) | REV-telling + scenario (CM: uitgeschakeld) |
| REV-kalenderjaren | — | Jaartallen REV-taken in lifecycle |
| `expected_total_downtime_hr` | `CTdt` | CM-downtime |
| `expected_pm_downtime_hr` | `PTdt` | PM-downtime |
| — | `ITdt` | Inspectie-downtime (AW-only) |
| `expected_cm_cost_eur` / `pm_cost_eur` | — | Kosten-splitsing RCM2 |
| `p_failure_lifecycle` | — | Kans op ≥1 falen |
| leeftijd / MTTF | `InitialAge` / `FmMttf` | Invoerparity |
| PM-taken per type | — | IN/SVO/TST/REV-telling |

Import uitbreiding: `TotalW`, `TotalWErr`, `OutageFrequency`, `ITdt`, `CTdt`, `PTdt`, `InitialAge`, `FmMttf` in `isograph_causes`.

- Geen err-kolom bij benchmark → **informatief**, geen fail.
- FM-verdict: fail als één gated metriek faalt; pass als alle gated pass; anders informatief/missing.

### Architectuur

- **Deep module:** `rcm_core/rcm_cost_benchmark.py` (Qt-vrij, pytestbaar).
- **Adapter:** `rcm_desktop/adapter/rcm_cost_parity_service.py` — bouwt view-DTO uit `FMResult` + project.
- **View:** `rcm_cost_parity_dialog.py` — read-only tabel; geen motor in views.

### UI

- Toolbar-knop **Modelcontrole AW** in resultatenwerkruimte.
- Actief na run wanneer `import_settings` AW-benchmarks bevat.
- Toont samenvatting (pass/fail/missing) + sorteerbare FM-tabel.

### Effect-metrics parity (slice 70)

Grill-besluiten: categorie-specifieke presentatie; AW-pariteit **informatief**, geen gate v1.

| Effectcategorie | RCM2 (via `EffectImpactService`) | AW-benchmark | Gate v1 |
|-----------------|----------------------------------|--------------|---------|
| beschikbaarheid | NB per effect (RF × downtime × failures + PM-uren) | downtime/Tdt-proxies waar aanwezig | **Nee** |
| veiligheid | incidenten-equivalent (`failures × RF`) | incident-proxies | **Nee** |
| alle (kosten) | — | `EffectCost` per cause | **Nee** (informatief) |

- FM-level gates (`TotalCost`, `TotalTdt`) blijven ongewijzigd (slice 65).
- Effect-niveau: verdict **informative** / **missing**; nooit **fail** in v1.
- Validatie-export effecttab: cause codes **E1** import, **E2** metrics/eenheid, **E3** missing benchmark.
- Spike: `.scratch/rcm-desktop-slice70-effectcategorie-resultaten/EFFECT_METRICS_SEMANTICS_SPIKE.md`

## Consequences

- Parity is **diagnostisch**; fail betekent geen blokkerende validatie.
- CM/PM-scenarioverschil: vergelijk met de run die de analist net uitvoerde; overlay/planning volgt bestaande run-pad.
- Portfolio-merge: FM-verdicts per submodel; geen extra project-€-gate (grill 1).
- Spike-item “Roggebot-kolommen” blijft optionele uitbreiding; v1 implementeert alleen kolommen in import + core.

## References

- ADR-0004 — `import_settings`-contract
- `.scratch/rcm-desktop-epic-parity-portfolio-mc/GRILL_DECISIONS.md` — grill 1
- Slice 66 — `aw_mc_lifecycle_horizon` activeert meerdere REV-cycli en maakte een stale survival-noemer in `_conditional_failures_with_rev_segments` zichtbaar (128/135 Gaarkeuken-fails vóór fix; `.scratch/rcm-desktop-slice66-rev-segment-survival-fix/`)
