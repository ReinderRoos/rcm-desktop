# Kanban-handoff — slice 35 + sessie-fixes (2026-05-21)

**Doel:** Vastlegging voor een schone vervolgsessie. Lees dit bestand + `PRD.md` vóór je het kanban-bord oppakt.

**Repo:** `rcm-desktop`  
**Slice-map:** `.scratch/rcm-desktop-slice35-rcm-cost-excel-import/`  
**ADR:** `docs/adr/ADR-0004-isograph-excel-import-import-settings.md`  
**Domein:** `CONTEXT.md` (sectie RCM-Cost import bootstrap)

---

## Kanban-status (issues)

| # | Titel | Triage | Opmerking |
|---|--------|--------|-----------|
| 01 | Import-capability matrix | **done** | `IMPORT_MATRIX.md` + `rcm_core/isograph_export_contract.py` |
| 02 | PM-semantiek-spike | **done** | `PM_SEMANTICS_SPIKE.md`; regels in `isograph_pm_import_rules.py`; CM: 54 PM-links / 15 waarschuwingen; `Enabled` = scenario, niet koppeling |
| 03 | ADR + import_settings | **done** | ADR-0004, `import_settings_contract.py`, CONTEXT |
| 04 | import_settings serialisatie | **done** | round-trip tests |
| 05 | isograph_import_service | **done** | mapper + tests; `propagate_bouwjaar_to_ancestors` toegevoegd (zie bugs) |
| 06 | Import-wizard | **done** | modeljaar + IA-conflicten |
| 07 | Navigatieboom PBS→FM | **done** | `rcm_navigation_tree_*` |
| 08 | Desktop open + opslaan | **done** | `ResultsWorkspaceWindow`, smoke test; handmatig OK op **Gaarkeuken** |
| 09 | AW Enabled → overlay seed | **done** | `aw_disabled_pm_ids` in import_settings; `PlanningOverlayState.from_import_settings`; CM: **235** disabled PM-ids; commit `a939676` |

**Slice 35 tracer-bullet:** functioneel **af** voor bootstrap-import + werkruimte + AW-scenario bij eerste run. **Open productwerk:** subset-export Excel (latere slice); waarschuwingen `validate_aannamen` verminderen (optioneel).

---

## Wat werkt (geverifieerd)

### Desktop-flow

1. Start: `python -m rcm_desktop.main` (venv + `pip install -e .[dev]` — **openpyxl** verplicht).
2. **Open RCM-Cost export…** → wizard (modeljaar, IA-conflicten) → opslaan `.rcm.json`.
3. **Project inladen** / pad in toolbar.
4. **Start analyse** / **Herbereken analyse** — motor + presentatie.
5. **Top 10**, **FM-detail**, **Tijdsplot (LCC)** tonen resultaten op geïmporteerd project.

### Fixtures (tests)

| Bestand | Gebruik |
|---------|---------|
| `tests/fixtures/RCMCostdata export_leeg.xlsx` | Structuur/layout only; import → veel validatiefouten |
| `tests/fixtures/RCMCostdata export_CM.xlsx` | Unit/import tests |
| `tests/fixtures/RCMCostdata export_Gaarkeuken.rcm.json` | E2E LCC; **let op:** 12 PM-links (oude import) — herimport CM geeft 54 |
| `tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json` | Demo zonder Excel |

### Tests (relevante subset)

```powershell
cd rcm-desktop
.\.venv\Scripts\Activate.ps1
python -m pytest tests/test_isograph_export_fixture_contract.py tests/test_isograph_import_service.py `
  tests/test_isograph_pm_import_rules.py tests/test_import_conflict_service.py `
  tests/test_isograph_import_wizard_service.py tests/test_isograph_open_flow_service.py `
  tests/test_desktop_open_rcm_cost_export.py tests/test_rcm_navigation_tree_builder.py `
  tests/test_lcc_gaarkeuken_import.py tests/test_desktop_run_service.py tests/test_import_overlay_seed.py -q
```

**Laatste run slice 35 (2026-05-21):** subset — **39 passed** (16.3s).

**Laatste run post-slice-35 fixes (2026-05-21):** FM inspector + sort — **7 passed** (7.8s):
`test_desktop_fm_results_table_model.py`, `test_fm_table_sorts_by_total_cost_column`, `test_fm_inspector_selection_after_scope_rerender`.

**Repo HEAD:** `15b5d5c` (slice 36 performance); slice 35 + issue 09 in `a939676`. FM inspector/sort + performance fixes in slice 36 commit.

---

## Sessie-bugs opgelost (buiten issue-tekst)

### 1. `openpyxl` ontbrak in venv

- **Symptoom:** app start niet (`ModuleNotFoundError: openpyxl`).
- **Fix:** `pip install -e .` — staat in `pyproject.toml` dependencies.
- **UX:** `main.py` toont NL-fout als openpyxl ontbreekt.

### 2. Import: 65× `PBS_EFFECTIVE_BOUWJAAR_ZERO`

- **Oorzaak:** `InitialAge` alleen op blad-locaties; parent-PBS `bouwjaar=0`.
- **Fix:** `propagate_bouwjaar_to_ancestors()` in `import_conflict_service.py`, aangeroepen na wizard.
- **Test:** `test_cm_fixture_import_valid_after_wizard_choices`, conflict propagation tests.

### 3. Start analyse: interne fout

- **Oorzaak:** `run_service.run()` gaf `scenario_key=` door aan `run_incremental_analysis()` die die parameter niet had → `TypeError` → `RUN_INTERNAL_ERROR`.
- **Fix:** `scenario_key` in `rcm_core/incremental_run.py` + scenario-cachepaden in `rcm_core/cache.py` (`*.rcm.cache.cm.json` / `*.rcm.cache.pm.json`).

### 4. Tijdsplot leeg / vast

- **Oorzaak:** `PMTask` miste `is_wettelijk_verplicht`; LCC-filter crashte met `AttributeError`.
- **Fix:** velden op `PMTask` (`is_wettelijk_verplicht`, `aging_effect_pct`); WET-detectie bij import; fallback `"WET" in taak_omschrijving` in `lcc_type_filter.py` / `ltap_service.py`.
- **Test:** `tests/test_lcc_gaarkeuken_import.py`.

### 5. PM-effectlinks: `Enabled=False` blokkeerde koppeling (issue 02 vervolg)

- **Symptoom:** 57 importwaarschuwingen op CM; 46× task op SubIndex maar `Enabled=False`.
- **Oorzaak:** `resolve_pm_task_id` behandelde AW `Enabled` als structureel i.p.v. scenario.
- **Fix:** `Enabled`-check verwijderd uit `rcm_core/isograph_pm_import_rules.py` — koppeling via `(Cause, SubIndex, P/I-vlaggen)` blijft.
- **Test:** `test_pm_link_resolves_when_scheduled_task_disabled`, `test_cm_fixture_pm_effect_links_resolved` (54 links, 15 waarschuwingen).

### 6. AW `Enabled=False` → baseline-run (issue 09)

- **Symptoom:** Geïmporteerd AW-scenario had disabled taken, maar eerste run telde alle PM-taken mee.
- **Fix:** `aw_disabled_pm_ids` bij import; `PlanningOverlayState.from_import_settings` + seed in werkruimte bij project laden.
- **Test:** `test_synthetic_aw_disabled_pm_ids_in_import_settings`, `test_cm_fixture_aw_disabled_pm_ids_populated`, `test_import_overlay_seed.py`, `test_run_service_materializes_overlay_disabled_pm`.

### 7. FM-inspector reageert niet na re-render (slice 34 regressie)

- **Symptoom:** Inspector werkt kort na openen FM-detail, daarna geen update bij rijselectie (scope/modus-wissel).
- **Oorzaak:** `selectionChanged` één keer gewired met `_fm_inspector_selection_wired`; bij `setModel()` nieuw selection model, vlag blijft `True`.
- **Fix:** Permanente `FMResultsSortProxy` op view; `selectionChanged` bij UI-build; `setSourceModel()` bij refresh; selectie op `fm_id` bewaren.
- **Test:** `test_fm_inspector_selection_after_scope_rerender`.

### 8. FM-tabel: kolomsortering numeriek kapot

- **Symptoom:** Tekstkolommen sorteren; kolommen 4–6 (faalmomenten, downtime, kosten) niet — sorteerpijl wel, volgorde blijft origineel.
- **Oorzaak:** Standaard `QSortFilterProxyModel.lessThan()` sorteert custom `RAW_ROLE` floats niet betrouwbaar; `mapToSource()` in `lessThan` was fout (Qt geeft source-indices).
- **Fix:** `FMResultsSortProxy` in `fm_results_table_model.py` — expliciete float-vergelijking kolommen 4–6; ook ValidateWindow.
- **Test:** `test_sort_proxy_orders_downtime_numerically_not_lexically`, `test_sort_proxy_orders_total_cost_numerically`, `test_fm_table_sorts_by_total_cost_column`.

---

## Architectuur (kort)

```
Excel (.xlsx)
  → isograph_excel_reader
  → isograph_import_service (build_from_workbook)
  → isograph_import_wizard_service (preview + complete_import + IA)
  → isograph_open_flow_service (gate, validate, atomic save)
  → ResultsWorkspaceWindow (Open RCM-Cost export…)

Na laden:
  → import_settings.aw_disabled_pm_ids → PlanningOverlayState (actief indien niet leeg)
  → validate_service / run_service → incremental_run (materialiseert overlay bij actieve disabled set)
  → presentation_cache_service
  → modi: Top10 | LCC (Tijdsplot) | FM-detail
  → rcm_navigation_tree_* (sidebar)
```

**Regels:** UI → alleen via `rcm_desktop/adapter/`; geen `rcm_core` in views (typing ok).

---

## Bekend gedrag / acceptabel voorlopig

- **~718 waarschuwingen** na import (`validate_aannamen`): ontbrekende tekstvelden `aanname_*`, geen blokker.
- **Projecttotaal niet-beschikbaarheid >100%**: optelling over parallelle functies; per component in Top 10 wel logisch.
- **PM-effectlinks:** geïmporteerd wanneer PEnable/IEnable + SubIndex **uniek resolvable** (CM: **54** links, **15** waarschuwingen). **`Enabled` ≠ koppeling** — structureel vs scenario.
- **15 importwaarschuwingen CM:** SubIndex ontbreekt (7) of P-only zonder Planned-task (8) — AW-datakwaliteit.
- **AW `Enabled=False`:** → `import_settings.aw_disabled_pm_ids` (CM: **235**); overlay ge-seed bij laden; **Start analyse** materialiseert passieve taken. What-if-modus kan daarna verder worden aangepast.
- **Gaarkeuken.rcm.json:** opgeslagen met oudere import (12 PM-links); herimport via wizard geeft 54 + actuele `aw_disabled_pm_ids`.
- **FM-inspector jaartabel:** UI klaagt `profile_missing` op echte runs — motor vult `FMResult.horizon_profile` niet (`build_horizon_profile` bestaat maar niet gekoppeld; slice 34 issue 04 bewust zonder motorwijziging).
- **Cache cross-contaminatie:** **nee** — cache per `<project>.rcm.cache.json` + `global_digest`; Gaarkeuken-cache raakt AWZI Haarlem niet. Haarlem-demo heeft geen `import_settings`/overlay-seed; traagheid = cold cache + 60j lifecycle + presentatie-fase (slice 23–26).
- **Performance vs oud:** AWZI Haarlem (~12k regels JSON) trager door werkruimte re-renders, presentatie-cache na motor, LCC dubbel-LTAP — niet door verkeerde fixture-cache.

---

## Aanbevolen volgende kanban-kaarten

1. **Commit FM inspector/sort fixes** — 5 uncommitted files; tests 7/7 groen.
2. **Motor: `horizon_profile` vullen** — slice 27→34 gap; jaartabel/reconcile in inspector dan echt bruikbaar.
3. **Gaarkeuken fixture verversen** — `.rcm.json` herimport (54 PM-links + `aw_disabled_pm_ids`) voor LCC-regressie.
4. **Performance profiel Haarlem** — motor vs presentatie vs LCC-render (optioneel; geen cache-bug).
5. **Import: standaard aanname-teksten** — waarschuwingen terugdringen (lage prioriteit).
6. **Nieuwe slice:** subset-export naar AW-compatibel Excel (PRD out of scope v1).

---

## Belangrijkste bestanden (wijzigingen slice 35 + fixes)

| Pad | Rol |
|-----|-----|
| `rcm_core/isograph_export_contract.py` | Must-v1 sheet/kolom contract |
| `rcm_core/import_settings_contract.py` | `import_settings` merge/normalize |
| `rcm_core/isograph_pm_import_rules.py` | FM/PM-effect regels; **`Enabled` niet bij link-resolutie** |
| `.scratch/.../PM_SEMANTICS_SPIKE.md` | Issue 02 SSOT (PEnable/IEnable/CEnable) |
| `tests/test_isograph_pm_import_rules.py` | Unit tests PM/FM importregels |
| `rcm_desktop/adapter/isograph_import_service.py` | Excel → RCMProject |
| `rcm_desktop/adapter/import_conflict_service.py` | IA + **propagate bouwjaar** |
| `rcm_desktop/adapter/isograph_import_wizard_service.py` | Wizard orchestratie |
| `rcm_desktop/adapter/isograph_open_flow_service.py` | Gate + persist |
| `rcm_desktop/adapter/isograph_import_dialog.py` | Qt wizard |
| `rcm_desktop/views/results_workspace_window.py` | Open export + overlay seed bij project laden |
| `rcm_desktop/adapter/planning_overlay_state.py` | `from_import_settings()` |
| `rcm_desktop/main.py` | Entry → resultatenwerkruimte |
| `rcm_core/incremental_run.py` | `scenario_key` parameter |
| `rcm_core/cache.py` | Scenario cache-paden |
| `rcm_core/models.py` | `PMTask.is_wettelijk_verplicht`, `aging_effect_pct` |
| `rcm_desktop/adapter/fm_results_table_model.py` | `FMResultsSortProxy` + `RAW_ROLE` numerieke sort |
| `rcm_desktop/views/results_workspace_window.py` | Permanente FM-proxy; inspector selectie-wiring |
| `rcm_desktop/views/validate_window.py` | Zelfde `FMResultsSortProxy` |
| `tests/test_desktop_fm_results_table_model.py` | Proxy sort unit tests |
| `tests/test_desktop_results_workspace_window.py` | Inspector + sort regressietests |

---

## Grill-me besluiten (vastgelegd)

- Bootstrap-import AW → RCM2 (ADR-0004); geen gevolgkosten-import.
- PBS → functie → faalwijze in UI; leeftijd op **bouwdeel/PBS**, niet persistent per FM.
- RF → `FMEffectLink.fractie`; FM- en PM-effecten gescheiden; PM-fractie default 1.0.
- AW `ScheduledTask.Enabled` = scenario (niet structurele cause→effect-koppeling).
- `import_settings` voor MC/ruwe AW-metadata; geen Labor/Spares-catalogi in v1.
- Fase 0 gate: matrix + PM-spike vóór grote UI-uitbreiding — **beide afgerond**.

---

*Laatst bijgewerkt: 2026-05-21 — slice 35 af; slice 36 (15b5d5c) bevat FM inspector/sort + performance; horizon_profile motor gekoppeld.*
