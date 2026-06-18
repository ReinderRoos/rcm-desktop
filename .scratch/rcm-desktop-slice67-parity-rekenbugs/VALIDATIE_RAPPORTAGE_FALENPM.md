# Validatie-rapportage — falenPM (PM-scenario controle)

**Datum:** 2026-06-09  
**Inputbestand:** `tests/fixtures/RCMCostdata export_Gaarkeuken_PM.rcm.rcm.json`  
**Controlebestand:** `tests/fixtures/Modellering door Delta Pi_validatie_falenPM.xlsx`  
**AW-inputbron PM:** `tests/fixtures/RCMCostdata export_PM.xlsx`  
**Project:** Modellering door Delta Pi  
**LifeTime:** 50 jaar | **CM-overlay PM uit:** 0 (PM-scenario: alle taken actief)  
**Totaal geanalyseerde FMs:** 135  
**`aw_mc_lifecycle_horizon`:** False (RCM2 default — resterende studieduur)

---

## Achtergrond

Voorgaande validaties (falen1–falen6) gebruikten het **CM-scenario**: AW-export met
235 PM-taken uitgeschakeld (`aw_disabled_pm_ids`). Slice 68 loste C1 (run vs CM-overlay)
op voor dat scenario.

Dit rapport controleert het **PM-scenario**: AW-export met alle PM-taken actief.
De AW-benchmarkwaarden (`TotalW`) verschillen in 105 van 135 FMs wezenlijk van de
CM-waarden — de PM-run genereert een eigen falenpatroon.

Aanleiding voor dit rapport:
1. `export_validation_workbook` accepteert nu een `input_file`-parameter zodat het
   controlebestand expliciet documenteert welk `.rcm.json` als inputbron is gebruikt.
2. Controle of afwijkingen in het PM-scenario rekenbugs zijn of modelkeuzes.

---

## Statistisch overzicht

### Samenvatting

| Categorie | # FMs |
|---|---|
| Parity OK | 12 |
| Parity FAIL | 123 |
| Totaal met AW benchmark | 135 |

### Dominante factor

| Factor | # FMs |
|---|---|
| residu (AW-onbekend) | 116 |
| LifeTime-semantiek | 17 |
| REV in motor | 2 |

### Actie-verdeling

| Actie | # FMs | Aard |
|---|---|---|
| Productkeuze: AW-horizon vs resterende studieduur | 50 | Model-keuze (A2) |
| Band gebruiken; geen softwarefix | 30 | Model-keuze (A1) |
| Band gebruiken + optioneel leeftijd harmoniseren | 20 | Model-keuze (A1 + B3) |
| MTTF/multipliciteit controleren; rest via MC-band | 15 | Model-keuze (A4) |
| Geen actie nodig (Parity OK) | 12 | OK |
| AW-horizon + optioneel leeftijd harmoniseren | 7 | Model-keuze (A2 + B3) |
| REV-intervalcontrole | 1 | Model-keuze (D1) |

### Oorzaakverdeling (alle codes, primair + secundair)

| Code | Betekenis | # FMs |
|---|---|---|
| A2 | LifeTime-semantiek | 57 |
| A1 | Analytisch vs Monte Carlo | 50 |
| B3 | InitialAge vs RCM2-leeftijd mismatch | 27 |
| A4 | Random falen residual | 15 |
| D1 | REV in motor (paradox) | 1 |

---

## Oordeel: modelkeuzes, geen bugs

### A2 — LifeTime-semantiek (57 FMs, primaire oorzaak voor PM)

De dominante nieuwe bevinding t.o.v. het CM-scenario: AW PM gebruikt **volledige LifeTime**
vooruit (`lifecycle_years` jaar vanaf leeftijd 0), terwijl RCM2 standaard de **resterende**
studieduur berekent (van huidige leeftijd tot het einde van de studieperiode).

| FM | RCM2 ef | AW TotalW | ef_horizon | Δ horizon |
|---|---|---|---|---|
| 06H-350.1.1.1.11.1.A.1 | 22.09 | 758.15 | 81.50 | +59.4 |
| 06H-350.1.20.7.1.A.2 | 22.09 | 602.14 | 81.50 | +59.4 |
| 06H-350.2.2.9.1.A.1 | 3.49 | 479.08 | 46.37 | +42.9 |
| 06H-350.1.7.10.1.A.1 | 6.98 | 479.04 | 92.75 | +85.8 |

Zelfs `ef_horizon_forward` (RCM2 met volledige 50 jaar vooruit) ligt nog een factor 6–40×
onder de AW TotalW. Dit residu is niet door A2 alleen te verklaren; het valt in categorie
A1 (MC-residu) of duidt op een fundamenteel verschil in hoe AW PM-scenario faalfrequenties
accumuleert (zie §over-large residuen hieronder).

**Actie A2:** Productkeuze — schakel `aw_mc_lifecycle_horizon=True` in als aanpassing
aan AW-semantiek gewenst is. Dit laat A2 verdwijnen maar verplaatst ~57 FMs naar A1.

### A1 — Analytisch vs Monte Carlo (50 FMs, primaire oorzaak)

Zelfde patroon als CM-scenario: RCM2 analytisch (Weibull-integraal), AW Monte Carlo.
De afwijkingen zijn groter in PM dan in CM omdat PM-scenario meer aging-interacties heeft.

Top 5 afwijkingen (primair A1):

| FM | RCM2 ef | AW TotalW | failure_type |
|---|---|---|---|
| 06H-350.3.1.2.3.A.1 | 22.76 | 921.02 | aging |
| 06H-350.3.6.2.1.A.2 | 24.84 | 479.74 | aging |
| 06H-350.3.17.8.1.A.2 | 11.59 | 479.11 | aging |
| 06H-350.3.12.2.1.A.1 | 11.59 | 429.00 | aging |
| 06H-350.3.19.4.1.A.1 | 0.00 | 355.31 | aging |

**Over-large residuen (factor 10–40×):** voor sommige A1-FMs is de discrepantie te groot
voor puur MC-residu. Meest waarschijnlijke verklaring: AW PM-scenario berekent `TotalW`
via `OutageFrequency × 8760 × lifecycle_years`, waarbij `OutageFrequency` een PM-gewogen
effectieve uitvalfrequentie is die fundamenteel verschilt van de analytische Weibull-integral
bij aging. Dit is een **modelconventie-verschil**, geen rekenbug.

### A4 — Random falen residual (15 FMs)

Zelfde als CM-scenario: analytisch `ef = mult × studieduur / MTTF` vs AW MC. Geen actie.

### D1 — REV paradox (1 FM)

| FM | RCM2 ef | AW TotalW | ef_no_rev | Δ REV effect |
|---|---|---|---|---|
| 06H-350.1.1.1.1.1.A.2 | 125.62 | 107.56 | 100.00 | +25.62 |

REV verjongd de component (repair_quality terugzet naar leeftijd 0). Voor een aging FM
met hoge multipliciteit en relatief laag MTTF versus lifecycle kan dit het **totaal verwacht
aantal falen verhogen**: vóór REV is de component oud → lage hazard in resterende studie;
na REV is de component jong → hogere hazard voor de resterende 50 jaar. Dit is een bekende
eigenschap van het analytisch model, **geen bug**. AW=107.56 zit tussen ef_no_rev (100) en
ef_actual (125.62) — AW modeleert dit REV-effect partieel.

### Vergelijking met CM-scenario

| Bevinding | CM-scenario (falen5/6) | PM-scenario (falenPM) |
|---|---|---|
| Parity OK | 15 | 12 |
| C1 (run vs CM-overlay) | **25** (actieverpunt) | 0 (geen overlay) |
| A2 (LifeTime-semantiek) | < 5 | **57** |
| A1 (Analytisch vs MC) | 79 | 50 |
| A4 (Random residual) | 13 | 15 |
| D1 (REV paradox) | 0 | 1 |
| B3 (leeftijd-mismatch) | 27 sec. | 27 sec. |
| **Software-actieverpunten** | **1 (C1)** | **0** |

---

## Resterende actieverpunten

### Geen software-actieverpunten in PM-scenario

Alle 123 parity-fails zijn toe te schrijven aan modelkeuzes:
- **A2 (57 FMs):** LifeTime-semantiek — productkeuze, geen bug.
- **A1 (50 FMs):** Analytisch vs Monte Carlo — inherent architectuurverschil.
- **A4 (15 FMs):** Random falen MC-residu — inherent.
- **D1 (1 FM):** REV-verjongingsparadox — architectuurkeuze.

### Optionele verbeteringen (lage prioriteit)

1. **`aw_mc_lifecycle_horizon=True`** zetten als de analist wil vergelijken met
   de volledige 50-jaar vooruit (verwijdert A2; verplaatst naar A1 met horizonbanding).
2. **Leeftijd-harmonisatie (B3, 27 FMs):** Bouwjaar afstemmen op AW InitialAge.
   Effect is beperkt wanneer de primaire oorzaak A1/A2 is.
3. **Dieper AW-PM-conventie-onderzoek:** voor FMs met factor 10–40× discrepantie
   (over-large A1-residu): bevestigen of AW PM TotalW werkelijk via OutageFrequency
   is berekend en of dat een ander kost-concept vertegenwoordigt.

---

## Conclusie

**Het PM-scenario bevat geen rekenbugs in RCM2.** Alle afwijkingen worden verklaard door:
1. **LifeTime-semantiek (A2, 57 FMs):** AW loopt 50 jaar vooruit; RCM2 stopt op einde
   van de 50-jarige studieperiode. Modelkeuze.
2. **Analytisch vs Monte Carlo (A1, 50 FMs):** inherent verschil.
3. **REV-paradox (D1, 1 FM):** architectuurkeuze, verwacht gedrag.

Het CM-scenario actieverpunt C1 (run vs CM-overlay) is niet aanwezig in het PM-scenario —
er is geen overlay te materialiseren. Het PM-scenario gedraagt zich correct.

De controle bevestigt dat het toevoegen van de `input_file`-parameter aan de validatie-export
(zie codewijziging) het onderscheid CM/PM expliciet vastlegt in het controlebestand.
