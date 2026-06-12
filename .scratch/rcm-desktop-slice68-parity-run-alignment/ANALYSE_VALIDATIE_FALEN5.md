# Analyse validatie-export falen5 (Gaarkeuken)

**Datum:** 2026-06-05  
**Bron:** `tests/fixtures/Modellering door Delta Pi_validatie_falen5.xlsx`  
**Context:** Na slice 66 (REV-survival) en slice 67 (repair_quality, CM-overlay helper, audits)  
**Sheet:** Validatie — 140 data-rijen, 135 FM's met benchmark

## Samenvatting

| Actie | # FM's | Aard |
|-------|--------|------|
| Band gebruiken; dieper onderzoek sigma/NMF/verdeling | 79 | Model-keuze (A1 — geen bug) |
| Run met CM-overlay materialiseren | 25 | **Actieverpunt (C1 — software)** |
| Geen actie nodig (Parity OK) | 15 | Opgelost |
| MTTF/multipliciteit controleren; rest via MC-band | 13 | Model-keuze (A4 — geen bug) |
| Optioneel invoer harmoniseren | 3 | Secundair (B3) |

**Conclusie:** De overgrote meerderheid van resterende afwijkingen is **geen rekenbug** maar analytisch (RCM2) vs Monte Carlo (AW). Enige concrete software-actie: **CM-overlay correct materialiseren in de run** (25 FM's, C1).

## 1. A1 — Analytisch vs Monte Carlo (79 FM's)

RCM2 berekent verwachte falen analytisch (Weibull survival-integraal). AW gebruikt Monte Carlo-simulatie. Dit levert structureel andere uitkomsten, vooral bij aging-FM's:

- MC simuleert stochastische spreiding; analytische verwachtingswaarde valt op een andere plek dan MC-mediaan.
- Bij hoge leeftijd/MTTF-ratio's daalt analytische oplossing sneller naar 0.
- **Aanbeveling:** AW-band (TotalW ± TotalWErr) als acceptatiecriterium, geen puntvergelijking.

## 2. ef_actual = 0 bij over-aged componenten (10 FM's)

| FM | leeftijd | MTTF | Ratio | AW TotalW |
|----|----------|------|-------|-----------|
| 06H-350.3.16.2.1.A.1 | 44 | 6 | 7.3× | 26.8 |
| 06H-350.4.4.10.1.A.1 | 44 | 6.25 | 7.0× | 5.0 |
| 06H-350.1.7.5.1.A.1 | 44 | 10 | 4.4× | 5.5 |
| (overige 7) | | | 2.2–4.4× | |

Component 2–7× MTTF overleefd → Weibull-hazard → survival ≈ 0 → RCM2 berekent **0** verwachte falen in studieduur. AW hanteert andere MC-conventie. **Architectuurkeuze, geen fout.**

## 3. A4 — Random falen (13 FM's)

Analytisch: ef = mult × T / MTTF. AW TotalW wijkt door MC + fase-relatie onderhoud. **Aanbeveling:** MTTF/multipliciteit controleren, rest accepteren binnen MC-band.

## 4. C2 — REV uit in CM-overlay (88 FM's secundair)

In 88 FM's staat REV uit in AW CM-scenario (REV actief=0). CM-overlay onderdrukt PM → REV impliciet uit. Δ REV effect ≈ 0 voor vrijwel alle rijen. **Expliciet gemodelleerd.**

## 5. C1 — Run ≠ CM-overlay (25 FM's) — ENIGE SOFTWARE-ACTIE

`ef_actual ≠ ef_cm_overlay` met significante Δ scenario. Huidige run materialiseert 235 uitgeschakelde PM-taken niet consistent met counterfactual.

**Uitschieters:**

| FM | Δ scenario | Notitie |
|----|------------|---------|
| 06H-350.3.5.9.1.A.1 | −120.8 | mastenveroudering, mult=114 |
| 06H-350.3.3.7.1.A.1 | +40.9 | SCADA, leeftijd=12, MTTF=7 |
| 06H-350.3.13.4.1.A.1 | +28.6 | niveaumeetsysteem |

**Opvolging:** slice 68 issue 01 — run-pad default CM-overlay materialisatie.

## 6. B3 — Leeftijd-harmonisatie (27 FM's secundair, 3 optioneel)

RCM2-leeftijd wijkt af van AW InitialAge (vaak RCM2=0, AW=44 jr). Niet per se fout; optioneel corrigeren via invoer. **Lage prioriteit** — slice 68 issue 05.

## Relatie eerdere slices

| Slice | Status | Effect op falen5 |
|-------|--------|------------------|
| 66 REV-survival | done | Geen explosieve expected_failures |
| 67 repair_quality | done | B1 opgelost; ef_actual ≈ ef_rq_0 in tests |
| 67 CM-overlay helper | done in tests | C1 blijft in analist-export → run-keten gap |
| 68 run alignment | **planned** | C1 → 0 verwacht |

## Reproduceerbare check (na slice 68)

```bash
pytest tests/test_slice68_parity_run_alignment.py -q
```

Verwachting na fix: validatie-export opnieuw genereren → **0×** "Run met CM-overlay materialiseren", **~79×** band-accepteren (A1), **~15×** Parity OK.
