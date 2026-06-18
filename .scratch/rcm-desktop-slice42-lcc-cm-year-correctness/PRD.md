# PRD — RCM2 desktop slice 42 (LCC correctief jaarprofiel: vormtests + Haarlem-fixture)

**Status:** ready-for-agent  
**Versie:** 1.0  
**Triage-labels:** ready-for-agent  
**Type:** AFK (test + fixture; geen motor- of UI-featurewijziging)  
**Parent:** grill-me roadmap 2026-05-23 (north star C — motor/correctheid); slice 22/24 aging-SSOT + DS-4  
**Referentie-fixture:** `tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json` (AWZI Haarlem Waarderpolder demo)

## Problem Statement

In de **LCC-tijdsplot** (Resultatenwerkruimte, modus Tijdsplot) ziet de analist een **grote, vlakke basis** voor correctieve kosten (~€197k per jaar) met slechts kleine fluctuaties, terwijl hij **piekende verouderingskosten** rond MTTF verwacht. Dat roept twijfel op: is dit een **foute berekening in de tool**, of **verwacht gedrag gegeven de invoer**?

Readonly-analyse op het Haarlem-demo-project toont:

- De UI-waarde voor 2026 (correctief €197.465,55) komt **exact** overeen met de motor+adapter-keten.
- Alle faalwijzen hebben **`horizon_profile`** — geen legacy proportionele fallback in `build_cor_eur_per_bucket`.
- **Random-failure** faalwijzen (58 stuks) dragen ~**93%** van de CM-kosten bij met **CV = 0** (perfect vlak hazard-model).
- **Aging-failure** faalwijzen (63 stuks) dragen ~**7%** bij met wel piekend profiel (CV ≈ 0,73), maar te klein om het portfolio zichtbaar te maken.

Bestaande tests (`test_lcc_profile.py`) controleren vooral **reconciliatie** (som jaarlijkse CM ≡ lifecycle-totaal, DS-4b), niet **vorm** (vlak vs piekend) noch **decompositie** random vs aging. De analist heeft daarom **geen geautomatiseerde zekerheid** dat de tool per faalmodeltype correct rekent én dat het demo-project een bruikbare LCC-vorm toont voor oefening en regressie.

## Solution

Formaliseer **zekerheid over het LCC-CM-jaarprofiel** in vier complementaire lagen (D4, start bij D1):

1. **D1 — Synthetische vormtests:** minimal fixtures waar random **moet vlak** zijn en aging **moet pieken**; dezelfde keten als de UI (`run_analytical` → `build_cm_eur_per_bucket` / `horizon_profile.cor_eur`); reconcile DS-4b.
2. **F1+G2+G3 — Haarlem-fixture in-place:** alle 58 `random` faalwijzen omzetten naar `aging` met expliciete `sigma_jaar = 0,15 × mttf_jaar` (1 decimaal) en aging-logische `aanname_faalmodel` / `notes` — zodat het oefenbestand verouderingsgedrag domineert.
3. **Baseline-refresh:** na fixture-flip nieuwe projecttotaal-baselines vastleggen in `test_run_metrics_baseline.py` (en performance-referentie hermeten indien nodig).
4. **D2 — Portfolio-characterisatie (H3):** Haarlem-test die reconcile, aging-dominantie (≥90% CM-share), niet-vlakheid (CV > 0,10, max/mean > 1,3) en afwezigheid legacy-fallback asserteert.

Geen wijziging aan presentatielaag, adapter-cache of `rcm_core`-algoritmes — tenzij tests een bug blootleggen. Handmatige smoke: LCC-tijdsplot toont **piekende** correctieve kosten i.p.v. vlakke basis.

## User Stories

### Zekerheid — synthetische vorm (D1)

1. Als **maintainer** wil ik dat een **enkele random faalwijze** een **vlak** CM-jaarprofiel oplevert (CV < 0,01), zodat het exponentiële faalmodel afdwingbaar is getest.
2. Als **maintainer** wil ik dat een **enkele aging faalwijze** een **piekend** CM-jaarprofiel oplevert (max/mean > 2, piek rond MTTF), zodat de aging-SSOT via de LCC-keten traceerbaar is.
3. Als **maintainer** wil ik dat synthetische tests **DS-4b reconciliëren** (som `cor_eur`-buckets ≡ `expected_cm_cost_eur`), zodat vorm en totaal niet los van elkaar drift kunnen.
4. Als **maintainer** wil ik dat tests bewijzen dat **`horizon_profile.cor_eur`** wordt gebruikt (geen legacy proportionele fallback), zodat regressie naar pre-slice-36 gedrag CI vangt.
5. Als **maintainer** wil ik dat de synthetische fixtures **minimaal** zijn (1 FM, bekende MTTF/sigma/leeftijd), zodat falende asserts snel te diagnosticeren zijn.
6. Als **domain expert** wil ik dat random- en aging-vormtests **dezelfde horizonbucket-semantiek** gebruiken als LTAP/LCC (kalenderjaar-raster), zodat tests het echte productpad representeren.
7. Als **maintainer** wil ik dat aging-vormtests **REV-schema** kunnen uitsluiten (passieve aging), zodat piekvorm niet vervuild wordt door PM-verjonging tenzij expliciet bedoeld.

### Zekerheid — portfolio Haarlem (D2 / H3)

8. Als **analist** wil ik dat het **Haarlem-oefenproject** een **zichtbaar piekend** CM-profiel toont in de tijdsplot, zodat demo en training fysisch intuïtief aanvoelen.
9. Als **maintainer** wil ik dat na de fixture-flip **≥90% van CM-kosten** uit aging-faalwijzen komt, zodat portfolio-vorm niet opnieuw door random wordt gedomineerd.
10. Als **maintainer** wil ik dat het geaggregeerde Haarlem-CM-profiel **niet-vlak** is (CV > 0,10), zodat extreme vlakheid regressie vangt.
11. Als **maintainer** wil ik dat Haarlem **max/mean > 1,3** op jaarlijkse CM asserteert, zodat pieken meetbaar blijven ook bij portfolio-aggregatie.
12. Als **maintainer** wil ik dat Haarlem-characterisatie **DS-4 reconcileert** op projectniveau, zodat vormtests geen stille totalen-drift maskeren.
13. Als **maintainer** wil ik dat Haarlem-runs **`used_legacy=False`** in `build_cor_eur_per_bucket` hebben, zodat ontbrekende `horizon_profile` direct faalt.
14. Als **analist** wil ik dat **projecttotaal kosten en NB** na fixture-flip nog steeds via baseline-test zijn vastgelegd, zodat andere motorregressies (NMF, REV, taakgroepen) detecteerbaar blijven.

### Fixture-mutatie (F1 + G2 + G3)

15. Als **maintainer** wil ik **in-place** mutatie van het Haarlem-demo-JSON (geen fork), zodat alle bestaande tests en perf-referenties één canoniek oefenbestand blijven gebruiken.
16. Als **domain expert** wil ik dat omgezette faalwijzen **`failure_type: aging`** hebben met **`sigma_jaar = round(0,15 × mttf_jaar, 1)`**, zodat JSON traceerbaar is en overeenkomt met DS-1a (`effective_sigma`).
17. Als **domain expert** wil ik dat **`aanname_faalmodel`** en **`notes`** aging-logisch zijn (normaalverdeling, σ=15% MTTF), zodat FM-inspectie en documentatie consistent zijn met bestaande aging-FM's in dezelfde fixture.
18. Als **maintainer** wil ik dat **`repair_quality`** en overige FM-velden ongewijzigd blijven waar niet nodig, zodat alleen faalmodel-semantiek verschuift — geen collateral CM-kostenwijziging door andere velden.
19. Als **maintainer** wil ik dat na flip **121 aging + 0 random** faalwijzen overblijven, zodat de failure-type-mix expliciet asserteerbaar is.
20. Als **trainer** wil ik dat het oefenbestand **meer verouderingsfaalwijzen** bevat dan voorheen, zodat LCC-oefeningen realistischer zijn voor AWZI-achtige assets.

### Baselines en regressie

21. Als **maintainer** wil ik **`test_haarlem_run_metrics_match_post_aging_ssot_baseline`** bijwerken met nieuwe totalen na flip, zodat onbedoelde KPI-inflatie (NMF-TST, Quantity, parallel) nog steeds wordt gevangen.
22. Als **maintainer** wil ik **`test_haarlem_aging_without_rev_matches_pre_ssot_total`** herzien of documenteren als historische referentie, zodat pre-SSOT vergelijking niet misleidend wordt na fixture-wijziging.
23. Als **maintainer** wil ik **`test_haarlem_kpi_run_service_matches_engine`** groen houden, zodat adapter-run en motor parity behouden blijft.
24. Als **maintainer** wil ik **`test_haarlem_fixture_has_no_synthetic_nmf_tst_tasks`** ongewijzigd laten slagen, zodat slice-27 NMF-fixturehygiëne intact blijft.
25. Als **maintainer** wil ik performance-baseline (`tests/perf/baseline.json`) **hermeten** als Haarlem-run-tijden significant verschuiven, zodat slice-36/38 contracten realistisch blijven.

### Keten en architectuur

26. Als **maintainer** wil ik dat vormtests de **kern-adapterketen** gebruiken (`build_cm_eur_per_bucket` op `FMResult` uit `run_analytical`), zodat UI, adapter (`lcc_chart_service`, `lcc_planning_service`) en kern dezelfde bron delen.
27. Als **maintainer** wil ik dat decompositie-tests **`motor_cor_eur_per_bucket`** kunnen gebruiken voor per-FM CM-by-type, zodat aging-share asserties leesbaar zijn.
28. Als **maintainer** wil ik **geen wijziging** aan `rcm_core.models` of editing schemas, zodat parity-tests en scrub-list contracten intact blijven.
29. Als **maintainer** wil ik **geen `CACHE_INPUTS_VERSION` bump** tenzij motorinvoer wijzigt, zodat cache-gedrag niet onnodig invalideert.

### Handmatige verificatie

30. Als **analist** wil ik na implementatie in de **LCC-tijdsplot** op Haarlem een **macroscopisch piekend correctief profiel** zien (niet ~constant €197k/jaar), zodat visuele acceptatie de geautomatiseerde H3-drempels bevestigt.
31. Als **analist** wil ik dat **preventief** en **totaal** in dezelfde plot nog steeds kloppen met slice 28/31-contracten, zodat alleen CM-vorm verandert — geen collateral PM-regressie.

### Developer / agent ergonomie

32. Als **agent** wil ik een **vaste implementatievolgorde** (D1 → fixture → baselines → D2), zodat rode tests eerst de keten bewijzen voordat fixture-wijziging baselines breekt.
33. Als **agent** wil ik **shape-metrics** (CV, max/mean, aging-share) in herbruikbare pure helpers, zodat D1 en D2 niet dupliceren.
34. Als **maintainer** wil ik dat falende shape-tests **actuele bucket- en totalenwaarden** loggen, zodat fixture- of drempel-tuning snel gaat.

## Implementation Decisions

### Scope en north star

- Slice adresseert **C1-symptoom** (LCC correctief jaarprofiel) onder north star **C** (motor/correctheid/performance).
- Diagnose: vlak profiel was **inputmix + faalfysica**, geen presentatiebug; oplossing is **afdekking + betere demo-fixture**, geen LCC-UI-refactor.

### Modules — bestaande keten (ongewijzigd tenzij bug)

| Laag | Module | Rol in slice |
|------|--------|--------------|
| Kern | `build_fm_horizon_profile`, `build_cor_eur_per_bucket` / `build_cm_eur_per_bucket` | Canonical CM per horizonbucket via `FMHorizonProfile.cor_eur`; `used_legacy` flag |
| Kern | `expected_faalmomenten_per_bucket_random`, `expected_aging_lifecycle_faalmomenten_ssot` | Faalfysica achter vorm |
| Kern | `run_analytical` / `compute_fm_result` | Levert `FMResult` + `horizon_profile` |
| Adapter | `motor_cor_eur_per_bucket`, `lcc_chart_service`, `lcc_planning_service` | Consumenten; slice verifieert compatibiliteit via kern-tests |
| Fixture | Haarlem demo JSON | In-place mutatie F1+G2+G3 |

### Nieuwe / gewijzigde artefacten

| Artefact | Besluit |
|----------|---------|
| **Synthetische vormtests (D1)** | Nieuw testbestand; minimal inline `RCMProject.from_dict` fixtures |
| **Shape-metrics helper** | Pure functies: `coefficient_of_variation`, `max_mean_ratio`, `aging_cm_share` — hergebruik in D1/D2; locatie: test helper module of klein `tests/helpers/lcc_cm_shape.py` |
| **Haarlem characterization (D2)** | Nieuw test in bestaande baseline-module of dedicated characterization module |
| **Fixture transform** | Script of eenmalige mutatie: 58 FM's; velden per G2+G3 |

### Fixture-flip (F1 + G2 + G3) — normatief

Voor elke faalwijze met `failure_type == "random"`:

```
failure_type  ← "aging"
sigma_jaar    ← round(0.15 * mttf_jaar, 1)
aanname_faalmodel ← aging-formulering (normaalverdeling, σ=15% MTTF); sluit aan bij bestaande aging-FM's in fixture
notes         ← korte verouderingsbeschrijving / demo-notitie
```

- **`repair_quality`**, `cost_cm_eur`, `mttf_jaar`, PM-koppelingen: **ongewijzigd**.
- Historische vergelijking met pre-flip totalen: **niet vereist** (expliciet besluit F1).

### D2 acceptatiedrempels (H3)

| Assertie | Drempel |
|----------|---------|
| DS-4b reconcile | `sum(build_cm_eur_per_bucket)` ≡ `sum(expected_cm_cost_eur)` binnen bestaande tolerantie |
| Legacy fallback | `build_cor_eur_per_bucket` → `used_legacy is False` |
| Aging CM-share | ≥ **90%** van project-CM uit faalwijzen met `failure_type == aging` |
| Niet-vlak | CV(jaarlijkse CM) **> 0,10** |
| Piek | max(jaarlijkse CM) / mean(jaarlijkse CM) **> 1,3** |

*(Grill-notitie: oorspronkelijk ook max/mean > 2,0 genoemd in H3-variant; **finale keuze H3 = 1,3** na "volg aanbeveling".)*

### D1 drempels (synthetisch)

| Case | Assertie |
|------|----------|
| Random FM | CV < **0,01**; reconcile |
| Aging FM | max/mean > **2,0**; piekjaar in bucket rond MTTF (±1 bucket tolerantie); reconcile |
| Horizon profile pad | `horizon_profile` present; bucket som = `hp.cor_eur` som |

### Baseline-refresh

- **`test_haarlem_run_metrics_match_post_aging_ssot_baseline`:** total_cost_eur, total_downtime_hr, unavailability_pct **opnieuw meten** na flip en vastleggen met korte docstring-update.
- **`test_haarlem_aging_without_rev_matches_pre_ssot_total`:** waarde **hermeten** of test **herlabelen** als historische documentatie — geen misleidende pre-flip constante.
- **`tests/perf/baseline.json`:** alleen bij meetbare wall-clock drift; slice-36/38 **call-count contracts** blijven leidend.

### Deep module — shape characterization helper

Encapsuleer portfolio-statistiek achter een smalle interface:

```python
@dataclass(frozen=True)
class LCCCmYearShape:
    buckets: tuple[float, ...]
    cv: float
    max_mean_ratio: float
    aging_cm_share: float
    used_legacy: bool
    reconciles: bool

def characterize_cm_year_shape(
    project, fm_results, *, build=build_cor_eur_per_bucket
) -> LCCCmYearShape: ...
```

- **Waarom deep:** combineert reconcile, legacy-detectie, type-decompositie en shape-metrics — tests blijven declarative (given project → assert thresholds).
- **Locatie:** test helper (preferred) — geen product-API tenzij later hergebruik in FM-verificatie.

### Implementatievolgorde (tracer bullet)

1. D1 tests + shape helper (rood → groen op huidige fixture waar mogelijk)
2. Fixture flip F1+G2+G3
3. Baseline refresh
4. D2 Haarlem characterization (H3)
5. Handmatige LCC smoke

### Architectuurprincipes (hard contract)

- **Geen** `rcm_core` wijziging behalve indien D1 een echte bug blootlegt.
- **Geen** view/adapter feature work; **Geen** parallel-run fix (apart issue).
- Tests gebruiken **sequentieel** `run_analytical(parallel=False)` — conform desktop run policy en bekende taakgroep-bug.

## Testing Decisions

### Wat een goede test is

- Test **observeerbaar gedrag** aan de motor+LCC-grens: jaarlijkse CM-buckets, reconcile, shape-statistieken, legacy-flag — **niet** private implementatie van Φ-integratie (dat blijft in `test_distributions.py`).
- Synthetische fixtures **minimal** — één FM per scenario; portfolio-tests alleen op Haarlem-fixture.
- Gebruik **bestaande toleranties** voor float-vergelijking (`math.isclose`, `pytest.approx`) consistent met `test_lcc_profile.py`.
- Shape-metrics helpers zijn **pure functies** — unit-testbaar zonder Qt.

### Te testen modules

| Module / artefact | Testtype | Prior art |
|-------------------|----------|-----------|
| `build_cm_eur_per_bucket` / `build_cor_eur_per_bucket` | D1 reconcile + legacy | `tests/test_lcc_profile.py` |
| Aging vs random vorm | D1 shape | `tests/test_distributions.py` (`test_not_uniform_fallback_smear`) |
| `motor_cor_eur_per_bucket` | D2 decompositie | `tests/test_horizon_bucket_series.py` |
| Haarlem fixture + baselines | D2 + baseline | `tests/test_run_metrics_baseline.py` |
| Shape helper | unit | nieuw |

### Niet testen in deze slice

- LCC UI widgets, cache-keys, LTAP call-counts (slice 36–38).
- Import failure_type audit (D3).
- Parallel FM pass taakgroep-deduplicatie.

### CI-gate

- Nieuwe D1 + D2 tests **verplicht groen**.
- Bestaande `test_lcc_profile.py`, `test_run_metrics_baseline.py`, slice-28 LCC smoke blijven groen na baseline-update.

## Out of Scope

- **D3 — Import-audit** van failure_type-classificatie uit Isograph/RCM-Cost export.
- **Parallel-run bugfix** (`test_parallel_fm_pass_inflates_task_group_costs`) en `SCENARIO_RUN_POLICY parallel=True` correctie.
- **LCC UI/UX** wijzigingen (slice 38 lazy detail, slice 30 what-if).
- **Nieuwe KPI's** of modi in Resultatenwerkruimte.
- **Fork** van Haarlem-fixture (F2) — expliciet afgewezen.
- **Selectieve flip** (F3) — expliciet afgewezen ten gunste van volledige random→aging.
- Wijzigingen aan **`rcm_core.models`**, editing schemas, **`CACHE_INPUTS_VERSION`**.
- **Monte Carlo** of scenario CM/PM vergelijkingsslice.
- **Documentatie/ADR** behalve korte test-docstrings en eventueel KANBAN-handoff.

## Further Notes

- Deze slice operationaliseert de **grill-me sessie** (2026-05-23) na slice 41: north star C, symptoom C1, besluiten D4→D1, F1, G2+G3, H3.
- **Risico — portfolio-aggregatie:** zelfs met 100% aging-FM's kan som van veel verspreide MTTF's relatief **gematigd** CV geven; H3-drempels (CV > 0,10, max/mean > 1,3) vangen extreme vlakheid; D1 bewijst per-FM-fysica onafhankelijk.
- **Risico — baseline-shift:** fixture-flip wijzigt lifecycle-totalen door aging-SSOT i.p.v. random hazard; dat is **verwacht** — geen bug tenzij D1 faalt.
- **Risico — perf:** aging zwaarder per FM kan run-tijd iets beïnvloeden; hermeten indien CI perf-regressie ziet.
- **Agents:** start met **TDD op D1** vóór fixture-mutatie; commit fixture + baselines in dezelfde changeset als D2.
- **Handoff:** na merge handmatig LCC-tijdsplot Haarlem verifiëren; screenshot optioneel in `.scratch/.../KANBAN_HANDOFF.md`.
