# ADR-0004 — Isograph RCM-Cost Excel-import en import_settings

## Status

Accepted (2026-05-19). Haalt **Excel-import (bootstrap)** van de scrub-list; **subset-export** naar AW blijft latere slice.

## Datum

2026-05-19

## Context

RCM2 startte met scrub-list **geen Excel-IO** (`CONTEXT.md`, tracer-bullet). Organisaties migreren van **Isograph Availability Workbench / RCM-Cost** via `RCMCostdata export_*.xlsx` (25 tabbladen). Handmatig overtypen is onhoudbaar.

Grill-me en slice-35 PRD:

- **Bootstrap** AW → `.rcm.json` (geen bidirectionele sync in v1).
- **Slank model**: geen Labor/Spares-catalogi, geen gevolgkosten per effect in RCM2.
- **Isograph-ID’s** behouden (`pbs_id`, `functie_id`, `fm_id`).
- **Fase-0 gate**: import-matrix + PM-spike vóór mapper; `pm_effect_links` niet raden.

## Beslissing

### Excel-import (in scope)

- Toegestaan: **eenmalige import** van RCM-Cost export naar `RCMProject` + opslaan als `.rcm.json`.
- Implementatie: Qt-vrije mapper in adapterlaag; UI alleen via `rcm_desktop.adapter`.
- Layout-contract: `rcm_core/isograph_export_contract.py` + `IMPORT_MATRIX.md`.

### Excel-export (out of scope deze ADR)

- Subset-export terug naar AVSIM-importeerbaar Excel = **eigen slice**; asymmetrisch t.o.v. import.

### Top-level `import_settings` op `.rcm.json`

Optioneel veld naast `config`, `pbs_items`, …:

```json
{
  "config": { "...": "..." },
  "import_settings": {
    "import_settings_schema_version": 1,
    "isograph_project": { "AvsimNoSimulationsRequested": 0 },
    "isograph_causes": { "FM-001": { "TotalCostErrPc": 5.0 } },
    "isograph_assignments": { "...": "PEnable/IEnable raw" }
  }
}
```

**Contract** (geïmplementeerd in `rcm_core/import_settings_contract.py`):

| Regel | Gedrag |
|-------|--------|
| `import_settings_schema_version` | Verplicht na normalisatie; huidige waarde **1** |
| Onbekende keys | **Pass-through** bij round-trip (toekomst Monte Carlo / export) |
| Leeg ontbrekend | Normaliseer naar `{ "import_settings_schema_version": 1 }` |

**Serialisatie** op `RCMProject` volgt in issue 04 (fase 1); deze ADR legt alleen het contract vast.

### Domeinregels import v1

- **Geen** `cost_gevolg_eur` / `CostPerOccurrence` uit AW.
- **RF** → `FMEffectLink.fractie`.
- **PM-effectlinks** alleen na afgeronde PM-spike (issue 02); anders leeg + waarschuwing.
- **Leeftijd** op PBS (`bouwjaar`), niet per FM; `modeljaar` via wizard.

### Monte Carlo

- `RcmNoSimulations` / `RcmRandomNoSeed` → `RCMConfig` waar aanwezig.
- Overige MC/onzekerheidskolommen → `import_settings` (motor/UI MC blijft buiten deze slice).

## Consequenties

- `CONTEXT.md` vermeldt RCM-Cost import-pad; scrub-list Excel-IO is **superseded voor bootstrap-import**.
- Tests: `tests/test_import_settings_contract.py`, `tests/test_isograph_export_fixture_contract.py`.
- `openpyxl` als **dev**-dependency voor layout-tests; productie-import voegt runtime-dep toe in fase 1.
- Geen wijziging `CACHE_INPUTS_VERSION` — import_settings niet in FM-hash tot expliciet besloten.

## Verworpen alternatieven

- **Volledige 25-tab pariteit** — te zwaar; catalogi en Avsim blijven buiten v1.
- **PEnable direct → PMEffectLink** — risico op verkeerde beschikbaarheid zonder spike.
- **Gevolgkosten importeren** — productfocus beschikbaarheid/degradatie, geen kosten per effect.

## Gerelateerd

- PRD: `.scratch/rcm-desktop-slice35-rcm-cost-excel-import/PRD.md`
- Matrix: `IMPORT_MATRIX.md`
- PM-spike: `PM_SEMANTICS_SPIKE.md`
