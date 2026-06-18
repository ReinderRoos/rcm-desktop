# Slice 24 — Motor-correctheid + 5× performance

**Triage:** done  
**Type:** AFK  
**Versie:** 1.1 (domeinreview faalmodel, NMF, jaartoerekening — 2026-05-18)

## Problem Statement

Twee samenhangende problemen verstoren het vertrouwen in de tool én haar bruikbaarheid:

1. **CM- en PM-scenario's leveren bijna identieke resultaten**, terwijl ze fundamenteel
   verschillende onderhoudsstrategieën zouden moeten representeren. Daarnaast dalen de
   **correctieve kosten over de tijd** in aging-plots — dat is fysisch onverwacht na
   een kalender-bucket-bug: vervolg-falingen landen op te vroege horizonjaren. Na CM
   hoort de leeftijd volgens **repair_quality** te verjongen; daarna opnieuw falen met
   periodieke pieken (of vlak profiel bij random), niet asymptotisch dalend.

2. **De desktop-applicatie is traag geworden**: scenario-runs duren onnodig lang, en
   zelfs eenvoudige klikken op de PBS-tree of mode-wissels herberekenen alles van
   scratch.

Aanvullend (domeinreview):

3. **LCC/NB tonen een proxy** — `expected_cm_cost_eur` wordt proportioneel over buckets
   verdeeld, terwijl het domein vraagt: per kalenderjaar **verwachte faalmomenten**,
   dan **kosten, downtime en effecten in dat jaar**.

4. **Niet-merkbaar falen (NMF)** — geen verplichte test-validatie; CM-kosten en
   `interval/2`-detectievertraging in plaats van kalendergebonden ontdekking met
   verborgen niet-beschikbaarheid tot de test.

De **rekenkern** is het epicentrum: kalender-correcte aging-SSOT, gedeelde
verjongingsformule (CM + REV), NMF-jaarpad, scenario-cache en workspace-memoization.

## Domeinspecificatie (normatief)

### DS-1 — Veroudering (aging)

Per horizonjaar **h** (kalenderjaar = `modeljaar + h`):

| Regel | Specificatie |
|-------|----------------|
| DS-1a | Eerste-faling: **normaalverdeling** μ = `mttf_jaar`, σ = `effective_sigma` (default 0,15 × MTTF). |
| DS-1b | Jaarmassa: incrementele Φ-massa per bucket (niet uniform). **AC-50:** cumulatieve eerste-faling-massa met kalenderjaar **> MTTF** = **50% ± 0,5 procentpunt** (universeel; bucket op MTTF-jaar via Φ-split). |
| DS-1c | **Fixture** (niet universeel): MTTF=20, σ=3, start 0 — jaar 18 ≈ 10%, piek ≈ 13% rond jaar 20 (screenshot-referentie). |
| DS-1d | Bij falen in jaar **h**: CM-kosten, reparatiedowntime, effectklassen in **kalenderjaar h**. |
| DS-1e | **Verjonging** (CM en REV, **zelfde formule**): `leeftijd ← leeftijd × (1 − effect)`. CM: `Faalwijze.repair_quality` ∈ [0,1]. REV: `PMTask.aging_effect_pct / 100`. |
| DS-1f | **IN / SVO / TST** verjongen **niet**. TST ontdekt NMF; **daarna CM** → dan `repair_quality`. SVO = randvoorwaardelijk (MTTF-haalbaarheid), geen leeftijdsreset. |
| DS-1g | **1e faalmoment:** belcurve. **2e+ faalmoment:** convolutie/superpositie na verjonging → typisch **uitgesmeerde** tweede golf. Iteratieve SSOT met `clock_time` + kalender-Φ-mapping. |

### DS-2 — Random failure

| Regel | Specificatie |
|-------|----------------|
| DS-2a | Per jaar: verwachte faalmomenten-intensiteit **1/MTTF** (× multipliciteit), geheugenloos. |
| DS-2b | Zelfde jaarlijkse toerekening als DS-1d. |

### DS-3 — Niet merkbaar falen (NMF)

| Regel | Specificatie |
|-------|----------------|
| DS-3a | `is_evident = false` ⇒ minstens één gekoppelde **IN- of TST-taak**; run **blocking** (`FM_NMF_REQUIRES_TEST`). |
| DS-3b | Ontdekking bij **eerstvolgende** geplande test (kalendertijd). |
| DS-3c | Tussen falen en ontdekking: **geen** CM-kosten; **wel** niet-beschikbaarheid over verborgen periode. |
| DS-3d | Bij ontdekking: reparatie-CM + downtime in **ontdekkingsjaar**; inspectiekosten via **PM-pad** (O-3). |
| DS-3e | Geldt voor **random én aging**. |
| DS-3f | **Scenario:** IN/TST voor NMF-FM's **altijd** in motor (override CM-filter) — modelvoorwaarde, geen strategische PM-keuze. |

### DS-4 — Reconciliatie

| Regel | Specificatie |
|-------|----------------|
| DS-4a | Som jaarlijkse verwachte faalmomenten ≡ `FMResult.expected_failures` (× multipliciteit). |
| DS-4b | Som jaarlijkse correctieve EUR ≡ `FMResult.expected_cm_cost_eur`. |
| DS-4c | Som jaarlijkse downtime (NB-proxy) ≡ motor-lifecycle binnen 1e-3. |

### Productbeslissingen (afgerond)

| ID | Besluit |
|----|---------|
| O-1 | `repair_quality` **blijft** voor CM; REV via `aging_effect_pct`; **zelfde verjongingsformule**; niet depreceren. |
| O-2 | Per jaar **verwachte faalmomenten** (continue analytisch; MC: discreet per run, gemiddeld weer continue). |
| O-3 | Inspectiekosten IN/TST via **PM-pad**; geen dubbele CM. |
| O-4 | Effectklassen **jaarlijks** in LCC/NB; **Bijdragen** lifecycle-totaal tot latere slice. |
| O-5 | IN/TST voor NMF **altijd** meenemen (override scenario-filter). |

## Solution

**Eén gecombineerde slice** — motor fysisch correct én ≥ 5× sneller:

- **Aging-lifecycle-engine (M1′):** kalenderjaarbuckets, `clock_time`, gesloten-vorm Φ; eerste-faling + herhaalfalingen met CM/REV-verjonging.
- **Jaarlijkse toerekening (M8):** LCC/NB/effecten uit faalmomenten per jaar, niet alleen herverdeling van lifecycle-totaal.
- **NMF-jaarpad (M7):** ontdekkingsschema, uitgestelde CM, verborgen NB.
- **PM in motor (M3′):** REV-schema op kalendertijd; IN/TST voor detectie; SVO/wettelijk in scenario's.
- **Scenario-definitie (M2):** data-driven `is_wettelijk_verplicht`; NMF-override voor IN/TST.
- **Performance (M4, M5):** per-scenario cache, workspace-render-index, parallel runs.

## User Stories

### Fysica-correctheid

1. Als RCM-analist wil ik dat **CM- en PM-scenario's zichtbaar verschillende LCC-curves** opleveren, zodat ik de impact van een PM-programma kan onderbouwen.
2. Als RCM-analist wil ik dat **correctieve kosten in de tijd** een **vlak profiel** vertonen voor random-faalwijzen, zodat de curve aansluit bij geheugenloze statistiek.
3. Als RCM-analist wil ik dat **correctieve kosten in de tijd** voor aging-faalwijzen **periodieke pieken** vertonen rond herhaalde faalmomenten na CM/REV-verjonging op de **juiste kalenderjaren**.
4. Als RCM-analist wil ik dat bij `repair_quality = 1.0` de aging-curve **periodiek herhaalt** met periode ≈ MTTF vanaf het 1e faalmoment.
5. Als RCM-analist wil ik dat bij `repair_quality = 0.0` de aging-curve een **constant verhoogde hazard** toont na het 1e faalmoment.
6. Als domein-expert wil ik dat het **lifecycle-totaal** aan verwachte faalmomenten ongewijzigd blijft en reconcilieert met `FMResult`.
7. Als RCM-analist wil ik dat **REV-taken** periodiek de effectieve leeftijd verlagen via `aging_effect_pct`, zodat PM-investering in LCC/NB zichtbaar is.
8. Als domein-expert wil ik dat **niet-merkbaar falen zonder IN/TST** de run **blokkeert**, zodat geen stille onderinschatting ontstaat.
9. Als RCM-analist wil ik dat **CM-kosten bij NMF pas in het ontdekkingsjaar** vallen en **verborgen niet-beschikbaarheid** tot de test meetelt.
10. Als RCM-analist wil ik dat **IN/TST voor NMF** in elk scenario in de motor zitten, zodat het faalmodel altijd compleet is.
11. Als RCM-analist wil ik dat **SVO-taken** in elk scenario als verplicht gelden (randvoorwaardelijk onderhoud).
12. Als RCM-analist wil ik dat **wettelijk verplichte PM-taken** via `is_wettelijk_verplicht` in elk scenario lopen.
13. Als RCM-analist wil ik dat het **CM-scenario** SVO + wettelijk + NMF-IN/TST bevat, zodat vergelijking eerlijk is.
14. Als RCM-analist wil ik dat het **PM-scenario** alle PM-taken uitvoert inclusief REV-aging-effecten.
15. Als domein-expert wil ik **`aging_effect_pct` op REV-taken** (0–100%), met dezelfde verjongingssemantiek als `repair_quality` op CM.
16. Als domein-expert wil ik dat **CM na falen** `repair_quality` toepast, dat **IN/SVO/TST zonder CM** de leeftijd niet resetten, en dat **TST na ontdekking van falen** leidt tot CM met `repair_quality`.
17. Als domein-expert wil ik dat de **eerste-faling-massa** een normale verdeling volgt (σ = 15% × MTTF) met **50% massa ná MTTF-jaar** (AC-50).
18. Als RCM-analist wil ik **correctieve kosten in het jaar van falen** op de LCC-staaf, niet alleen herverdeeld lifecycle-totaal.
19. Als RCM-analist wil ik **periodieke pieken** na REV op **juiste kalenderjaren**, niet door raster-bug naar jaar 0.
20. Als domein-expert wil ik dat **CM (`repair_quality`) en REV (`aging_effect_pct`) dezelfde verjongingsformule** gebruiken.
21. Als RCM-analist wil ik een **vlak** random-profiel (1/MTTF) zodat random en aging visueel te onderscheiden zijn.
22. Als domein-expert wil ik dat de **tweede-faling-golf** breder/uitgesmeerder kan zijn dan de eerste (convolutie), zonder dat de 50%-norm voor **eerste falen** wordt verbroken.

### Performance

23. Als RCM-analist wil ik dat **CM + PM-run** samen **≥ 5× sneller** is dan vandaag (demo-fixture).
24. Als RCM-analist wil ik dat een **herhaalde run** vrijwel instantaan is (cache).
25. Als RCM-analist wil ik dat **PBS-tree-klik** alleen presentatie triggert.
26. Als RCM-analist wil ik dat **mode-wissel** ≤ 200 ms is.
27. Als RCM-analist wil ik **parallelle** scenario-runs.
28. Als RCM-analist wil ik **gescheiden CM/PM-cache** bestanden.
29. Als RCM-analist wil ik dat een tweede CM-run na PM alleen gewijzigde FM's herberekent.

### Schema + migratie

30. Als domein-expert wil ik `is_wettelijk_verplicht` en `aging_effect_pct` op `PMTask`.
31. Als ontwikkelaar wil ik **automatische defaults** bij laden (REV → `aging_effect_pct=100` indien ontbreekt).
32. Als ontwikkelaar wil ik dat oude fixtures blijven werken via `from_dict`-defaults.
33. Als domein-expert wil ik de nieuwe kolommen in de **editing schema registry**.

### Cache-gedrag

34. Als ontwikkelaar wil ik een **slankere FM-hash** met globale PBS/task_group-digest.
35. Als ontwikkelaar wil ik **per-scenario cache** met `CACHE_INPUTS_VERSION`.

### Workspace-rendering

36. Als RCM-analist wil ik dat **niet-actieve modi** niet worden gerenderd tot zichtbaar.
37. Als RCM-analist wil ik **memoized** presentatie per slot/scope/modus.
38. Als RCM-analist wil ik **snelle** CM/PM-slot-wissel in KPI-tabel.

### Verificatie

39. Als RCM-analist wil ik **scenario-fixtures** met zichtbaar CM≠PM-verschil.
40. Als RCM-analist wil ik **regressie op periodiek patroon** bij `repair_quality=1`.
41. Als RCM-analist wil ik **Monte Carlo-vergelijking** (seed=42, ~5%) voor aging-buckets.
42. Als domein-expert wil ik **AC-50** en fixture `mttf20_sigma3` in tests, niet vaste 10% voor alle MTTF's.
43. Als ontwikkelaar wil ik **TDD** op adapter en kern-modules.
44. Als ontwikkelaar wil ik **geen Qt in rcm_core** en geen directe kern-imports in views.
45. Als ontwikkelaar wil ik **`CACHE_INPUTS_VERSION`** verhogen bij motorwijziging.
46. Als RCM-analist wil ik **gescheiden disclaimers** voor aging-SSOT vs NMF-proxy in NB-tooltips.
47. Als ontwikkelaar wil ik **geen scrub-list**-features introduceren.

## Implementation Decisions

### Deep modules

**M1′. Aging-lifecycle-engine** — SSOT voor `expected_failures` en `faalmomenten_per_calendar_bucket`. Kalender-mapping via `clock_time`; geen `study_start_age` als vast raster over iteraties. Eerste-faling uit Φ; vervolg na CM (`repair_quality`) en geplande REV (`aging_effect_pct/100`). Gesloten-vorm helpers (M6).

**M2. Scenario-definitie** — `pm_tasks_for_scenario(project, scenario_key) -> set[pm_id]`. CM = SVO ∨ `is_wettelijk_verplicht`. PM = alle taken. **Override:** alle IN/TST gekoppeld aan niet-evidente FM altijd meenemen. `build_project_for_scenario` blijft dunne wrapper.

**M3′. Onderhoudseffect op aging** — Zelfde verjonging `age *= (1 - effect)`:
- Na **CM** (elke faal+reparatie): `effect = repair_quality`.
- Op **REV-momenten** (kalender, interval): `effect = aging_effect_pct/100`.
- **IN, SVO, TST:** geen verjonging; **TST → ontdekking → CM** past `repair_quality` toe.
Random falen: geheugenloos; REV geen invloed op random type.

**M4. Per-scenario cache-index** — `<project>.rcm.cache.<scenario>.json`; slankere FM-hash.

**M5. Workspace-render-index** — memo per `(slot, scope_id, modus)`; lazy modi.

**M6. Snelle-normaal-helpers** — `normal_cdf`, truncated mean, vectorized Φ-segmenten.

**M7. NMF-jaarpad** — pure module `nmf_schedule`: faalmomenten per jaar → verborgen NB, CM/downtime in ontdekkingsjaar; integreert in `compute_fm_result`; vervangt `interval/2` voor presentatie.

**M8. Jaarlijkse toerekening** — per FM per bucket: `cm_eur[h] = fmomenten[h] × cost_cm_eur` (+ NMF-verschuiving); downtime en effectklassen parallel; reconciliatie DS-4.

### Interface-snapshot (M1′ + verjonging)

```python
def rejuvenate_age(age: float, effect_fraction: float) -> float:
    """Gedeeld voor CM (repair_quality) en REV (aging_effect_pct/100)."""
    return age * (1.0 - effect_fraction)

def expected_aging_lifecycle_calendar_buckets(
    *,
    current_age: float,
    lifecycle_years: float,
    mttf: float,
    sigma: float,
    repair_quality: float,
    rev_schedule: tuple[tuple[float, float], ...] = (),  # (interval_jaar, effect_pct)
    num_buckets: int,
    max_iterations: int = 100,
) -> tuple[float, list[float]]:
    """Iteratie: Φ-massa op kalenderbuckets; clock_time op; CM-verjonging;
    REV-momenten tussendoor; 2e+ golf uitgesmeerd t.o.v. 1e bel."""
```

### Ondiepe wijzigingen

- `PMTask`: `is_wettelijk_verplicht`, `aging_effect_pct` (REV-default 100 bij laden).
- `validators`: `FM_NMF_REQUIRES_TEST`.
- `lcc_profile` / adapters: consumeren M8/M7 buckets; geen tweede reconciliatie-logica in Qt.
- `CACHE_INPUTS_VERSION` +1 bij M1′/M7/M8.
- Messages: tooltips DS-1/2/3; NMF-disclaimer; verjonging CM vs REV.

## Testing Decisions

**Goede tests:** extern gedrag, geen mock van `quad`; property-tests op bekende input.

**Modules met tests:**

| Module | Tests |
|--------|--------|
| M1′ / M6 | AC-50 (eerste-faling alle MTTF); fixture `mttf20_sigma3`; vlak random; periodiciteit rq=1; rq=0 hazard; calendar-bug regressie; REV verschuift pieken; MC ~5% |
| M2 | CM/PM filter; NMF-override IN/TST |
| M3′ | CM repair_quality; REV aging_effect_pct; zelfde formule; IN/SVO geen reset; TST→CM reset |
| M7 | block zonder test; CM verschoven; hidden NB |
| M8 | `sum(cm_eur[h]) == expected_cm_cost_eur` |
| M4–M5 | cache/scenario/perf (bestaande slice 24) |

**AC-50 (normatief):** `sum(h: calendar_year(h) > mttf) m_first[h] / sum(m_first) ∈ [0.495, 0.505]`. MTTF-bucket met overlap: Φ-split.

**Fixture mttf20_sigma3 (optioneel):** index 17 ∈ [0.095, 0.105]; max(f[18:21]) ∈ [0.12, 0.14]; argmax ∈ {18,19,20}.

**Volledige SSOT (vorm):** 2e golf niet puntmassa op één jaar; geen uniforme aging-smearing.

**Prior art:** `tests/test_distributions.py`, `tests/test_lcc_profile.py`, `tests/test_engine.py`, `tests/test_cache.py`.

## Out of Scope

- Monte Carlo als **productiepad** (wel verificatie).
- Killer/olifant (ADR-0003), Excel-IO, LTAP-light.
- UI-redesign buiten tooltips/disclaimers.
- Geoptimaliseerd scenario (slice 25).
- Bijdragen-modus **jaarlijks** (lifecycle-totaal blijft tot latere slice).
- Gesloten-vorm **convolutie** 2e golf als harde eis (iteratieve SSOT volstaat).
- GPU/JIT, LTAP-bundeling-refactor.

## Further Notes

- **Volgorde:** M6 → M1′ → M8 → M3′ ∥ M7 (na M1′) → adapters → M4/M5 performance.
- **Slice 22:** historisch geleverd; gedrag hertest onder M1′.
- **Vocabulaire:** **faalmomenten** (niet "falingen"); analytisch continue verwachtingswaarden.
- **Communicatie:** LCC-tooltip: jaarkansen normaal faalmodel; NMF: CM bij ontdekking.
- **Issues 02–07:** zie issue-splitting in tracker; label `ready-for-agent`.
