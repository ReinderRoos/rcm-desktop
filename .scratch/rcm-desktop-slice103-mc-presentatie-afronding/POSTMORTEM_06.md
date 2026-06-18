# POSTMORTEM — Issue 06: FM compare exact gelijk na MC scenario-2 wijziging

**Datum:** 2026-06-18  
**Branch:** `feat/workspace-rapportage-slice58`  
**HILT:** HILT103 B4 (NO-GO)  
**Fix commit:** zie git log  

---

## Root cause

`_faalmomenten_scalar` (in `contribution_horizon_value_service.py`) berekende voor
`horizon="per_year"` + `year_choice="average"` de per-jaar waarde als:

```python
return float(sum(faalmomenten_per_bucket(project, fmr))) / len(buckets)
```

`faalmomenten_per_bucket(project, fmr)` rebuildt de bucket-verdeling via het
**analytische model van het live project** — inclusief de PM/REV-planning die op het
moment van de aanroep actief is in de sessie.

In de FM compare-flow gebruiken **beide slots hetzelfde live project** (het huidige
sessieproject). Scenario 1 en scenario 2 zijn bevroren als `CompareSlotSnapshot`
(met slot-specifieke `mc_run`), maar `build_fm_detail_view_for_compare_slot` geeft
`session.loaded.core()` als `project`-argument mee — dit is het *live* project, niet
het project waarmee de MC-run was berekend.

Gevolg:
- `faalmomenten_per_bucket(live_project, fmr_slot_A)` = analytisch totaal
- `faalmomenten_per_bucket(live_project, fmr_slot_B)` = **exact hetzelfde** analytisch totaal

Beide panels toonden daardoor dezelfde `failures_band.p50`, zelfs wanneer de twee MC-runs
sterk verschillende `failures.p50` hadden.

LCC compare toonde wél verschil omdat het `slot.run_result` gebruikt (bevroren op het
moment van de run, met het project-van-dat-moment).

### Waarom speelde dit alleen bij `per_year + average`?

Voor `horizon="lifecycle"` retourneerde `_faalmomenten_scalar` rechtstreeks
`float(fmr.expected_failures)`, wat de slot-specifieke MC P50 is — dus voor die
presentatie waren de waarden wél correct.

---

## Fix

**Bestand:** `rcm_desktop/adapter/contribution_horizon_value_service.py`  
**Functie:** `_faalmomenten_scalar`

Schaal de analytische bucket-distributie naar `fmr.expected_failures` (de slot-specifieke
MC P50 voor MC-runs, de analytische lifecycle-totaal voor analytische FMResult objecten):

```python
bucket_total = float(sum(buckets))
expected = float(fmr.expected_failures)
scale = expected / bucket_total if bucket_total > 0.0 else 1.0

if presentation.year_choice == "average":
    return expected / len(buckets)          # = sum(scaled_buckets) / n
# per specifiek jaar:
return float(buckets[idx]) * scale          # shape uit analytisch model, totaal = MC P50
```

**Analytische FMResult:** `expected_failures ≈ sum(buckets)` → `scale ≈ 1.0` → geen zichtbaar effect.  
**MC FMResult in compare:** `expected_failures` = slot-specifiek MC P50 ≠ analytisch totaal → elk
slot krijgt een eigen display-waarde die het MC-resultaat weerspiegelt.

---

## Test delta

| Bestand | Wijziging |
|---------|-----------|
| `tests/test_slice103_fm_compare_mc_scenario.py` | Nieuw — regressietest |
| `rcm_desktop/adapter/contribution_horizon_value_service.py` | Fix in `_faalmomenten_scalar` |

**Test:** `test_fm_compare_panels_mc_slots_reflect_slot_specific_p50`  
- Maakt twee `MCRunResult` objecten met `failures.p50 = 2.0` resp. `10.0` (factor 5 verschil)  
- Stopt ze in compare slots A en B via `CompareSlotSnapshot.from_mc_run`  
- Roept `build_fm_compare_panels` aan met de sample project en `_DEFAULT_SNAPSHOT`
  (`ContributionPresentation(horizon="per_year", year_choice="average")`)  
- Asserteert dat `panels[0].fm.mc_rows[0].failures_band.p50 != panels[1].fm.mc_rows[0].failures_band.p50`

**Voor de fix:** beide panels toonden `0.3007` (analytisch jaargemiddelde).  
**Na de fix:** `p50_a ≈ 0.0250` (= 2.0 / 80 buckets), `p50_b ≈ 0.1250` (= 10.0 / 80 buckets).

---

## Model-keuzerationale

De per-jaar display wordt gecomputed via de analytische bucket-distributie als *vorm*
(welk jaar heeft relatief meer falen) en `fmr.expected_failures` als *schaal*
(het totaal). Dit principe geldt al voor de `lifecycle`-presentatie
(`return float(fmr.expected_failures)`). De fix breidt dit uit naar de `per_year`-presentatie.

Voor analytische runs is `fmr.expected_failures ≈ sum(buckets)` (zelfde bron), dus
de verandering heeft geen zichtbaar effect op het analytische pad.

Voor specifieke jaarkeuze (`year_choice = 2030` etc.) geldt dezelfde schaling:
`buckets[idx] * scale` geeft de bucket-waarde voor dat jaar, herschaald naar het
MC P50-totaal. Dit is consistent met de `average`-aanpak en zorgt ervoor dat ook
jaar-specifieke weergaven slot-specifiek zijn.

---

## Preventie

1. **Testpatroon:** MC compare-tests moeten altijd `mc_results` in het `MCRunResult`
   object opnemen met FM IDs die overeenkomen met het project. Tests met lege `fm_results`
   (zoals in `test_slice100_compare_mixed_fm.py`) testen de MC-scaling-code niet.

2. **Risicozone:** Elke functie die `faalmomenten_per_bucket(project, fmr)` aanroept voor
   een `FMResult` die afkomstig is van `fm_results_from_mc_p50` heeft potentieel dit probleem
   als `project` niet hetzelfde project is als waarmee de MC-run werd berekend.

3. **Naam-scouting:** `kosten_scalar_for_fm` heeft een soortgelijk patroon voor
   `per_year + average`: het gebruikt `faal_buckets` (analytisch) voor de verdeling van
   PM-kosten over buckets. Dit is bewust niet gewijzigd (zie HILT101: "Keep cor_eur on the
   analytical bucket spine"), maar is een kandidaat voor een follow-up analyse als KOSTEN
   compare ook afwijkingen toont.
