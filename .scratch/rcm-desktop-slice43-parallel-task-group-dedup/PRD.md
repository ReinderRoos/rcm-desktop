# PRD — RCM2 desktop slice 43 (parallel run: taakgroep-PM-deduplicatie)

**Status:** ready-for-agent  
**Versie:** 1.0  
**Triage-labels:** ready-for-agent  
**Type:** AFK (motor + tests; geen UI-feature)  
**Parent:** grill-me 2026-05-23 na slice 42; north star **C′** (correctness); slice 24 scenario-parallel  
**Referentie-fixture:** `tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json`

## Problem Statement

De analytische motor kan faalwijzen **parallel** berekenen (`ProcessPoolExecutor`) voor snellere scenario-runs. In dat pad krijgt elke worker een **eigen lege** set `counted_group_ids` voor taakgroep-PM. Gedeelde **taakgroepen** (`TaskGroup`) die aan meerdere faalwijzen hangen, worden daardoor **per FM opnieuw** geteld in `pm_cost_eur`, `expected_pm_downtime_hr` en het PM-deel van `effect_bijdragen`. Het sequentiële pad deelt één `counted_groups`-set over alle FM’s en is **correct**.

Gevolg voor de analist en maintainer:

- **Scenario-runs** (CM/PM-vergelijking) gebruiken `parallel=True` via `SCENARIO_RUN_POLICY` — projecttotalen en FM-totalen kunnen **systematisch te hoog** zijn (op Haarlem >50% inflatie, vastgelegd in `test_parallel_fm_pass_inflates_task_group_costs`).
- Vertrouwen in **correctheid** ondermijnt slice 42 (LCC-vorm) en slice 24 (scenario-cache): de bug zit in de **rekenkern**, niet in invoer of presentatie.
- Desktop **Start analyse** draait bewust sequentieel (`DEFAULT_RUN_POLICY`) — gebruikers van alleen de werkruimte zien het symptoom minder, maar **scenario-pad en CLI `--parallel`** blijven fout.

De bestaande docstring in `compute_all_fm_results` suggereert ten onrechte dat deduplicatie in `compute_pbs_results` plaatsvindt — die functie **sommeert** alleen FM-resultaten en dedupliceert niet.

## Solution

Corrigeer het **parallel-pad** in de rekenkern met een **post-pass** (I1): na de worker-pool een sequentiële pass over alle berekende faalwijzen in **dezelfde volgorde** als het sequentiële pad, met één gedeelde `counted_group_ids`, en herbereken alleen PM-totalen via de bestaande `compute_pm_totals`-semantiek. Werk daarna `FMResult`-velden bij (`pm_cost_eur`, `expected_pm_downtime_hr`, gecombineerde `effect_bijdragen`, `total_cost_eur`). CM, faalmomenten en `horizon_profile` blijven uit de worker.

Leg **zekerheid** vast met **K1-paritytests**: `run_analytical(parallel=True)` ≡ `parallel=False` op een minimale synthetische fixture (2 FM, 1 taakgroep) en op het Haarlem-demo-project (per FM, strikte toleranties). Vervang de inflatie-regressietest door parity.

Invalidateer bestaande FM-cache via **`CACHE_INPUTS_VERSION` bump** (103 → 104), zodat oude parallel-cache geen foute totalen blijft tonen.

**Geen** inschakeling van parallel in desktop Start analyse in deze slice (S2 = aparte kanban-kaart).

## User Stories

### Correctness — analist & domein

1. Als **reliability-analist** wil ik dat **scenario CM vs PM** totalen overeenkomen met een sequentiële herberekening, zodat strategievergelijking niet door dubbele taakgroep-PM wordt vertekend.
2. Als **reliability-analist** wil ik na een tool-upgrade **Herbereken** kunnen doen en **lagere, correcte** scenario-totalen zien waar parallel-cache eerder te hoog was, zodat vertrouwen in de motor herstelt.
3. Als **domain expert** wil ik dat **taakgroepkosten** nog steeds **één keer per lifecycle** worden geteld over het project, zodat de bestaande taakgroep-semantiek uit slice 24 behouden blijft.
4. Als **domain expert** wil ik dat **losse PM-taken** (zonder `task_group_id`) per FM volledig blijven meetellen, zodat alleen gedeelde groepen worden gededupliceerd.
5. Als **reliability-analist** wil ik dat **CM-kosten en horizonprofielen** per FM ongewijzigd blijven ten opzichte van de parallel-worker, zodat LCC-CM-contracten (slice 42) niet collateral breken.

### Correctness — maintainer

6. Als **maintainer** wil ik een **parity-test** parallel ≡ sequentieel op Haarlem, zodat regressie op schaal wordt gevangen.
7. Als **maintainer** wil ik een **minimale synthetische fixture** (2 FM, 1 taakgroep), zodat falende tests direct de deduplicatie-logica tonen.
8. Als **maintainer** wil ik per FM **`total_cost_eur`, `pm_cost_eur` en `expected_pm_downtime_hr`** vergeleken, zodat dubbeltelling niet door aggregatie wordt gemaskeerd.
9. Als **maintainer** wil ik dat **`effect_bijdragen`** na de post-pass consistent is (FM-effecten + herberekende PM-effecten), zodat effectklassen in FM-inspectie niet drift geven.
10. Als **maintainer** wil ik dat de **FM-iteratievolgorde** in de post-pass identiek is aan het sequentiële pad (`target_ids` / `fms_to_calc`), zodat “welke FM de groep telt” deterministisch blijft.
11. Als **maintainer** wil ik dat **parallel onder drempel** (<8 FM’s) nog steeds sequentieel loopt zonder post-pass, zodat bestaand gedrag voor kleine projecten intact blijft.
12. Als **maintainer** wil ik dat **incrementele runs** met `parallel=True` dezelfde totalen geven als sequentieel, zodat cache-seam en scenario-runner correct blijven.

### Cache & upgrade

13. Als **maintainer** wil ik een **`CACHE_INPUTS_VERSION` bump**, zodat oude `.rcm.cache.json` met foute parallel-FM-resultaten niet stilletjes blijven gelden.
14. Als **analist** wil ik na upgrade een duidelijke **cache-miss / Herbereken** ervaren, zodat ik weet dat totalen opnieuw zijn berekend.
15. Als **maintainer** wil ik dat **sequentieel berekende cache** (parallel=False) semantisch hetzelfde blijft na de fix, zodat alleen parallel-output en geïnflateerde scenario-cache veranderen.

### Architectuur & documentatie

16. Als **ontwikkelaar** wil ik een **diepe module** voor post-pass PM-deduplicatie met een smalle interface, zodat `compute_all_fm_results` leesbaar blijft en de pass unit-testbaar is.
17. Als **ontwikkelaar** wil ik dat de **misleidende docstring** over `compute_pbs_results`-deduplicatie wordt gecorrigeerd, zodat toekomstige agents niet op het verkeerde pad zoeken.
18. Als **agent** wil ik een **vaste tracer-bullet-volgorde** (tests → motor → cache/docs), zodat TDD voorspelbaar is.
19. Als **maintainer** wil ik **geen wijziging** aan `RCMProject`-schema of editing parity, zodat `test_editing_schemas_parity` onaangetast blijft.
20. Als **maintainer** wil ik **geen Qt- of adapter-wijzigingen** in deze slice, zodat UI/kern-decoupling intact blijft.

### Scenario & policy (bewust niet in scope)

21. Als **product owner** wil ik dat **scenario-runs** na deze slice **correcte** totalen krijgen zonder policy-wijziging, zodat `SCENARIO_RUN_POLICY` parallel=True veilig blijft op de motorlaag.
22. Als **product owner** wil ik dat **desktop Start analyse** bewust **sequentieel** blijft tot een aparte performance-slice parallel inschakelt, zodat correctheid eerst, snelheid daarna komt.

### Regressie & integratie

23. Als **maintainer** wil ik dat bestaande **slice-24 scenario-tests** (parallel-flag, cache-hergebruik) groen blijven, zodat alleen numerieke scenario-totalen kunnen dalen — geen contractbreuk.
24. Als **maintainer** wil ik dat **slice-42 LCC-characterisatie** (H3) groen blijft, zodat CM-vormtests niet regresseren.
25. Als **maintainer** wil ik dat **`test_haarlem_run_metrics_baseline`** (sequentieel) ongewijzigd blijft, zodat de post-pass het sequentiële pad niet wijzigt.
26. Als **maintainer** wil ik dat **CLI parallel** (`--parallel`) dezelfde parity heeft als `run_analytical`, zodat CLI en desktop-scenario één motor-gedrag delen.

### Handoff

27. Als **maintainer** wil ik een korte **`KANBAN_HANDOFF.md`** met besluiten en testcommando’s, zodat vervolgkaarten (S2 desktop parallel, D3 import-audit) op het bord duidelijk zijn.

## Implementation Decisions

### Scope en north star

- Slice operationaliseert grill-me **C′** na slice 42: **parallel taakgroep-deduplicatie** (F1, I1, S1, K1, T1, V1).
- **Sequentieel pad:** ongewijzigde logica; post-pass wordt **niet** aangeroepen wanneer `parallel=False` of wanneer parallel wordt overgeslagen (<8 FM’s).
- **Parallel pad:** workers leveren FM-resultaten met “ruwe” per-FM PM; direct daarna **één** project-brede deduplicatie-pass.

### Modules — bouwen / wijzigen

| Module (concept) | Rol |
|------------------|-----|
| **`compute_all_fm_results`** | Na parallel pool: aanroep deduplicatie-pass; corrigeer docstring; behoud drempel <8 FM → sequentieel |
| **`deduplicate_parallel_fm_pm_costs`** (nieuw, deep module) | Input: `RCMProject`, `dict[str, FMResult]` (parallel output), optioneel `fm_ids` volgorde. Voor elke FM in vaste volgorde: haal PM-taken + links op, roep `compute_pm_totals` met gedeelde `counted_group_ids`, herbouw `effect_bijdragen` (FM + PM), zet `pm_cost_eur`, `expected_pm_downtime_hr`, `total_cost_eur = expected_cm_cost_eur + pm_cost_eur`. Return bijgewerkte dict. **Geen** Qt, geen I/O. |
| **`compute_pm_totals`** | Ongewijzigde semantiek — hergebruikt als SSOT voor groepsdeduplicatie |
| **`compute_fm_result` / worker** | Ongewijzigd voor parallel workers (CM + horizon uit worker) |
| **`run_analytical`** | Geen gedragswijziging behalve via `compute_all_fm_results` |
| **`CACHE_INPUTS_VERSION`** | Bump 103 → 104 |

### Interface — deduplicatie-pass (beslissingsrijk)

```python
def deduplicate_parallel_fm_pm_costs(
    project: RCMProject,
    fm_results: dict[str, FMResult],
    *,
    fm_ids: list[str] | None = None,
) -> dict[str, FMResult]:
    """Herbereken PM-velden met project-brede taakgroepdeduplicatie.

    fm_ids: expliciete volgorde; default = zelfde als compute_all_fm_results
    (target_ids gefilterd op aanwezige FM's).
    """
```

- **Waarom deep:** bundelt volgorde, gedeelde `counted_group_ids`, PM-effect-herbouw en FMResult-mutatie op één plek — `compute_all_fm_results` blijft orchestratie.
- **Mutatie:** `FMResult` is dataclass; bijwerken via `dataclasses.replace` of equivalent — geen schema-wijziging.

### FM-volgorde (normatief)

- Post-pass iteratie = **zelfde lijst** als sequentiële tak: `target_ids` (of `fm_ids` argument) → `fms_to_calc` volgorde.
- Eerste FM in die volgorde die een taakgroep tegenkomt **telt** de groepskosten; latere FM’s op dezelfde `task_group_id` tellen de groep niet opnieuw (bestaande `compute_pm_totals`-regels).

### Velden die de post-pass wél / niet wijzigt

| Veld | Post-pass |
|------|-----------|
| `expected_cm_cost_eur`, faalmomenten, CM-downtime | **Niet** — uit worker |
| `horizon_profile` | **Niet** — uit worker; geen PM-taakgroep in CM-horizon (slice 42) |
| `pm_cost_eur`, `expected_pm_downtime_hr` | **Ja** — herberekend |
| `effect_bijdragen` | **Ja** — FM-deel behouden, PM-deel opnieuw uit `compute_pm_totals` |
| `total_cost_eur` | **Ja** — `expected_cm_cost_eur + pm_cost_eur` |
| `risk_contribution` | **Niet** |

### Adapter / UI

- **Geen** wijziging aan `RunPolicy`, `run_decision`, `RunRunner`, `scenario_run_service` in deze slice.
- Scenario’s profiteren automatisch zodra motor + cache-bump live zijn.

### Cache

- **`CACHE_INPUTS_VERSION`:** 103 → **104** (AGENTS.md: motorwijziging zonder JSON-vormwijziging).
- Geen wijziging aan `FM_HASH_INPUT_SLICE_VERSION` tenzij hash-inhoud wijzigt (niet verwacht).

### Implementatievolgorde (tracer bullet V1)

1. **Issue 01 — Tests RED:** mini-fixture + Haarlem K1-parity; verwijder/vervang inflatie-test.
2. **Issue 02 — Motor GREEN:** `deduplicate_parallel_fm_pm_costs` + integratie in parallel tak.
3. **Issue 03 — Afsluit:** cache bump, docstring, `KANBAN_HANDOFF.md`.

## Testing Decisions

### Wat een goede test is

- Test **observeerbaar gedrag** van `run_analytical`: parallel vs sequentieel **identieke** FM-PM- en kostenvelden — **niet** interne ProcessPool-details.
- **K1 strikt:** per FM `total_cost_eur`, `pm_cost_eur`, `expected_pm_downtime_hr` met `pytest.approx(rel=1e-6)` of `abs=1e-4` EUR waar passend.
- Mini-fixture **minimaal**: 2 faalwijzen, 1 `TaskGroup`, beide FM’s met PM-taak in dezelfde groep — inflatie zonder fix moet **zichtbaar** zijn vóór GREEN.
- Haarlem-parity alleen als `len(fms) >= 8` parallel pad activeert (121 FM) — anders parallel pad niet getest op schaal; mini-fixture dekt logica.

### Te testen modules

| Module / artefact | Testtype | Prior art |
|-------------------|----------|-----------|
| `run_analytical` parallel ≡ seq | integratie K1 | `tests/test_run_metrics_baseline.py` (`test_parallel_fm_pass_inflates_*` → vervangen) |
| Mini-fixture taakgroep | integratie K1 | nieuw `tests/test_parallel_task_group_dedup.py` (of equivalent) |
| `deduplicate_parallel_fm_pm_costs` | unit (optioneel) | directe aanroep met mock FMResult — alleen als het RED sneller maakt |
| Cache version | unit/smoke | `tests/test_cache.py` / bestaande CACHE constant assert |
| Sequentieel Haarlem baseline | regressie | `test_haarlem_run_metrics_match_*` — moet **ongewijzigd** |

### Niet testen in deze slice

- Desktop `resolve_run_execution` parallel flag (blijft False).
- Perf cold-run Haarlem parallel (S2).
- LCC UI, presentatie-cache, meekoppel.
- Import failure_type audit (D3).
- `horizon_profile` PM-jaarverdeling (buiten post-pass).

### CI-gate

- Nieuwe parity-tests **verplicht groen**.
- `test_parallel_fm_pass_inflates_task_group_costs` **verwijderd of vervangen** — geen test die inflatie **verwacht**.
- Bestaande slice-24 scenario adapter-tests, slice-42 LCC tests, sequentiële Haarlem-baselines groen.

## Out of Scope

- **S2 — Desktop Start analyse parallel inschakelen** (`RunPolicy.allow_parallel=True`, `resolve()` `and False` fix) en perf-contract — aparte kanban-kaart.
- **D3 — Import-audit** `failure_type` uit RCM-Cost/Isograph.
- Wijzigingen **`rcm_core.models`**, **editing schemas**, views, adapter run-policy.
- **Herberekening van `horizon_profile`** in post-pass (niet nodig voor CM/LCC; apart als later PM-jaarlijkse toerekening in horizon komt).
- **Monte Carlo**, nieuwe KPI’s, meekoppel **2c**, Gaarkeuken-fixture, Excel-export.
- **ADR** behalve korte handoff-notitie.

## Further Notes

- Grill-me 2026-05-23: besluiten F1, I1, S1, K1, T1, V1 vastgelegd.
- **Risico — `effect_bijdragen`:** bij implementatie expliciet FM- en PM-bijdragen splitsen of volledig herberekenen; half bijwerken geeft stille drift in FM-inspectie.
- **Risico — scenario-totalen dalen:** analisten met oude parallel-cache zien lagere CM/PM-totalen na Herbereken — **verwacht gedrag**, geen regressie.
- **Risico — post-pass CPU:** kleine extra sequentiële pass na pool; acceptabel vs foutieve totalen; S2 perf-slice meet later winst van echte parallel desktop.
- **Kanban na slice 43:** D3 import-audit → S2 desktop parallel → meekoppel 2c → Gaarkeuken → Excel-export (zie slice 35/36 handoffs).
- **Agents:** TDD issue 01 eerst; geen cache-bump vóór groene parity (issue 03).
