# Slice 43 — Testrapport: parallel taakgroep-PM-deduplicatie

**Datum:** 2026-05-23  
**Scope:** `rcm_core` motor + regressietests (geen UI-wijziging)  
**Status:** geïmplementeerd; gerelateerde pytest-set groen in ontwikkelsessie

---

## 1. Samenvatting

| Item | Conclusie |
|------|-----------|
| **Probleem** | Bij parallelle FM-berekening werden **gedeelde taakgroep-PM-kosten** per faalwijze opnieuw geteld. |
| **Impact** | Vooral **scenario-runs** (`parallel=True`); Start analyse bleef sequentieel en was minder getroffen. |
| **Fix** | Post-pass `deduplicate_parallel_fm_pm_costs` na de worker-pool, met dezelfde deduplicatie als sequentieel. |
| **Zekerheid** | K1-contract: parallel ≡ sequentieel per FM op `total_cost_eur`, `pm_cost_eur`, `expected_pm_downtime_hr`. |
| **Cache** | `CACHE_INPUTS_VERSION` 103 → **104** (oude parallel-cache ongeldig). |

---

## 2. Wat was er fout?

### 2.1 Domeinregel (correct gedrag)

Een **TaskGroup** (bijv. maandelijkse inspectieronde `TG-IN-MECH`) hoort **één keer per project/lifecycle** te tellen, ook als meerdere faalwijzen een PM-taak in diezelfde groep hebben.

Dat regelt `compute_pm_totals` via een gedeelde set `counted_group_ids` in `rcm_core/engine.py`: bij de eerste FM die een `task_group_id` tegenkomt worden groepskosten en -downtime toegevoegd; de groep-ID gaat in de set; latere FM’s met dezelfde groep tellen die kosten niet opnieuw.

### 2.2 Bug: parallel pad zonder gedeelde set

- **Sequentieel:** één `counted_groups`-set over alle FM’s in vaste volgorde → correct.
- **Parallel (vóór fix):** elke `ProcessPoolExecutor`-worker roept `compute_fm_result` aan met een **eigen lege** set → elke FM telt de volledige taakgroepkosten opnieuw in `pm_cost_eur` en daarmee in `total_cost_eur`.

`compute_pbs_results` **sommeert** alleen FM-resultaten; het dedupliceert taakgroepen niet (de oude docstring suggereerde ten onrechte het tegendeel).

### 2.3 Waar zag je het in de product?

| Pad | `parallel` | Getroffen? |
|-----|------------|------------|
| **Start analyse** | `False` (`DEFAULT_RUN_POLICY`) | Nee (bewust sequentieel) |
| **Scenario CM vs PM** | `True` (`SCENARIO_RUN_POLICY`) | **Ja** |
| **CLI** met `--parallel` | `True` (bij ≥8 FM’s) | **Ja** |

Parallel start pas bij **≥8 faalwijzen**; kleinere projecten vallen terug op sequentieel (geen bug, wel relevant voor testfixtures).

---

## 3. Hoe is dit ontdekt?

### 3.1 Prioritering na slice 42

Grill-me / kanban koos **correctness (C′)** na slice 42 (LCC-CM-vorm). De parallel taakgroep-bug stond al als bekend risico (slice 24 scenario-parallel).

### 3.2 Bestaande regressietest (documenteerde het defect)

`test_parallel_fm_pass_inflates_task_group_costs` in `tests/test_run_metrics_baseline.py` **verwachtte** dat parallel **>50% hoger** was dan sequentieel op Haarlem — vastgelegd defect, geen gewenst gedrag. Vervangen door K1-parity in `tests/test_parallel_task_group_dedup.py`.

### 3.3 TDD mini-fixture (RED vóór fix)

Synthetisch project: 8 FM’s (parallel pool actief), FM-1 en FM-2 delen `TG-SHARED` (€10.000 / 2 jaar, lifecycle 10 jaar → **€50.000** groepskosten één keer).

**Vóór de fix (pytest-failure):**

| FM | Veld | Sequentieel (correct) | Parallel (fout) |
|----|------|----------------------|-----------------|
| FM-2 | `total_cost_eur` | ~€20 (alleen CM) | **€50.020** (CM + dubbele groep) |

### 3.4 Haarlem-demo

- 121 faalwijzen → parallel pool altijd actief.
- Gedeelde groepen `TG-IN-MECH` / `TG-IN-ELEK` (veel PM-taken met `task_group_id`).
- Oude test: projecttotaal parallel **>1,5×** sequentieel.

---

## 4. Wat is er veranderd?

### 4.1 `deduplicate_parallel_fm_pm_costs` (`rcm_core/engine.py`)

Na de parallel workers:

1. Zelfde **FM-volgorde** als sequentieel (`target_ids`).
2. Eén gedeelde `counted_groups` over alle FM’s.
3. Per FM opnieuw `compute_pm_totals` (SSOT).
4. Bijwerken: `pm_cost_eur`, `expected_pm_downtime_hr`, `effect_bijdragen`, `total_cost_eur`.
5. **Niet** wijzigen: CM, faalmomenten, `horizon_profile`, `risk_contribution`.

`compute_all_fm_results` roept deze post-pass alleen aan na een echte parallel pool (`parallel=True` en ≥8 FM’s).

### 4.2 Cache

`CACHE_INPUTS_VERSION`: **103 → 104** in `rcm_core/cache.py`.

### 4.3 Tests

| Bestand | Rol |
|---------|-----|
| `tests/test_parallel_task_group_dedup.py` | K1-parity mini + Haarlem |
| `tests/test_run_metrics_baseline.py` | Inflatie-test verwijderd; sequentiële baseline ongewijzigd |

### 4.4 Bewust niet gewijzigd

- Desktop Start analyse parallel (slice S2 apart).
- LCC-CM-algoritme (slice 42).
- Domain model / editing schemas.

---

## 5. Hoe weet je dat resultaten nu kloppen?

### 5.1 Hoofdbewijs: K1-parity

Voor **elke** faalwijze: `run_analytical(parallel=True)` ≡ `parallel=False` op:

- `total_cost_eur`
- `pm_cost_eur`
- `expected_pm_downtime_hr`

Tolerantie: `rel=1e-6`, `abs=1e-4` EUR (`tests/test_parallel_task_group_dedup.py`).

Sequentieel was het referentiepad; parallel is nu hetzelfde resultaat (workers + post-pass).

### 5.2 Sequentieel Haarlem-baseline ongewijzigd

`test_haarlem_run_metrics_match_post_aging_ssot_baseline` (`parallel=False`):

- `total_cost_eur` ≈ **€29.536.895,66**
- `unavailability_pct` ≈ **78,49%**

### 5.3 Overige regressie

- Slice 42: `test_haarlem_lcc_cm_characterization_h3`
- Slice 24: `tests/test_desktop_scenario_run_service_slice24.py`

---

## 6. Testuitvoering (reproduceerbaar)

```powershell
cd c:\Users\rroos\claude-workspace\rcm-desktop

python -m pytest tests/test_parallel_task_group_dedup.py -v
python -m pytest tests/test_run_metrics_baseline.py -v
python -m pytest tests/test_lcc_cm_shape.py tests/test_haarlem_fixture_aging_flip.py -q
python -m pytest tests/test_desktop_scenario_run_service_slice24.py -q
```

### 6.1 Resultatenmatrix (ontwikkelsessie)

| Suite | Tests | Resultaat |
|-------|-------|-----------|
| `test_parallel_task_group_dedup.py` | 2 | PASS |
| `test_run_metrics_baseline.py` + slice 42 LCC | 15 | PASS |
| `test_desktop_scenario_run_service_slice24.py` | 5 | PASS |
| **Totaal gerelateerd** | **22** | **PASS** |

### 6.2 Testcases

| ID | Test | Bewijs |
|----|------|--------|
| **S43-01** | `test_parallel_matches_sequential_on_shared_task_group_mini` | Dubbeltelling 2 FM + 1 groep; parallel pool (8 FM) |
| **S43-02** | `test_parallel_matches_sequential_on_haarlem` | Parity 121 FM, echte taakgroepen |
| **REG-01** | `test_haarlem_run_metrics_match_post_aging_ssot_baseline` | Sequentieel referentietotaal stabiel |
| **REG-02** | `test_haarlem_lcc_cm_characterization_h3` | LCC-CM slice 42 intact |
| **REG-03** | slice 24 scenario tests | Adapter parallel-scenario consistent |

### 6.3 Vóór/na (conceptueel)

| Meting | Vóór fix (parallel) | Na fix (parallel) | Referentie |
|--------|---------------------|-------------------|------------|
| Mini FM-2 `total_cost_eur` | ~€50.020 | ~€20 | = sequentieel |
| Haarlem projecttotaal | >1,5× sequentieel | = sequentieel | K1 per FM |
| Haarlem sequentieel totaal | ~€29,54M | ~€29,54M | baseline-test |

---

## 7. Actie in de UI

1. **Herbereken** na upgrade (cache 104), vooral scenario’s.
2. **Verwacht:** lagere scenario-totalen waar parallel-cache te hoog was — correctie, geen dataverlies.
3. **Start analyse:** nog sequentieel; verschil vooral bij **scenario CM/PM**.

Optionele handcheck: zelfde project sequentieel via CLI vs scenario in desktop na Herbereken.

---

## 8. Grenzen van deze zekerheid

| Wel afgedekt | Niet in slice 43 |
|--------------|------------------|
| Taakgroep-PM parallel vs seq | LCC CM-vorm (slice 42) |
| Per-FM K1-kostenvelden | Import `failure_type` audit (D3) |
| Cache 104 | Desktop Start analyse parallel (S2) |
| Sequentieel pad | PM in `horizon_profile` per jaar |

---

## 9. Gerelateerde documenten

| Document | Pad |
|----------|-----|
| PRD | `.scratch/rcm-desktop-slice43-parallel-task-group-dedup/PRD.md` |
| Issues | `.scratch/rcm-desktop-slice43-parallel-task-group-dedup/issues/` |
| Handoff | `.scratch/rcm-desktop-slice43-parallel-task-group-dedup/KANBAN_HANDOFF.md` |
| Parity-tests | `tests/test_parallel_task_group_dedup.py` |
| Motor | `rcm_core/engine.py` |

---

**Conclusie:** Fout in parallelle FM-berekening zonder project-brede taakgroepdeduplicatie. Zekerheid via K1-parity (mini + Haarlem), ongewijzigde sequentiële baseline, cache-bump 104, en regressie slice 42/24.
