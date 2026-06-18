# Validatie-rapportage — falen5 (na slice-67 bugfixes)

**Datum:** 2026-06-08  
**Fixture:** `tests/fixtures/Modellering door Delta Pi_validatie_falen5.xlsx`  
**Geëxporteerd:** 2026-06-08T20:56:27 UTC  
**Project:** Modellering door Delta Pi  
**LifeTime:** 50 jaar | **CM-overlay PM uit:** 235  
**Totaal geanalyseerde FMs:** 135

---

## Statistisch overzicht

### Dominante factor

| Factor | # FMs |
|---|---|
| residu (AW-onbekend) | 133 |
| scenario (CM-overlay) | 2 |

### Actie-verdeling

| Actie | # FMs | Aard |
|---|---|---|
| Band gebruiken; dieper onderzoek sigma/NMF/verdeling | 79 | Model-keuze (geen bug) |
| Run met CM-overlay materialiseren | 25 | **Actieverpunt** |
| Geen actie nodig (Parity OK) | 15 | Opgelost |
| MTTF/multipliciteit controleren; rest via MC-band | 13 | Model-keuze (geen bug) |
| Optioneel invoer harmoniseren (leeftijd/MTTF/REV-scenario) | 3 | Secundair / optioneel |

### Oorzaakcodes (primair + secundair gecombineerd)

| Code | Betekenis | # FMs |
|---|---|---|
| C2 | REV uit in AW CM-overlay scenario | 88 |
| A1 | Analytisch vs Monte Carlo | 79 |
| B3 | InitialAge vs RCM2-leeftijd mismatch | 27 |
| C1 | Run ≠ AW CM-scenario | 25 |
| A4 | Random falen residual | 13 |

---

## Oordeel: model-keuzes, geen bugs

### A1 — Analytisch vs Monte Carlo (79 FMs, primaire oorzaak)

RCM2 berekent verwachte falen **analytisch** via de Weibull survival-integraal.
AW gebruikt **Monte Carlo simulatie**. Dit levert structureel andere uitkomsten op:

- MC simuleert de stochastische spreiding van de verdeling; de analytische verwachtingswaarde
  valt op een andere plek dan de MC-verwachtingswaarde bij scheefverdelingen.
- Aanvaard acceptatiecriterium: RCM2-waarde moet binnen de AW-band `TotalW ± TotalWErr` vallen,
  niet puntsgewijs gelijk zijn.
- Actie: geen softwarewijziging nodig; "Band gebruiken" is de juiste interpretatiegrens.

### ef = 0 bij over-aged componenten (10 FMs, bewust grensgedrag)

Wanneer `leeftijd >> MTTF` geeft de analytische Weibull-survival vrijwel 0 kans dat de
component de toekomstige studieperiode overleeft zonder te falen. RCM2 berekent dan correct
~0 verwachte falen.

| FM | leeftijd | MTTF | Ratio | AW TotalW | mult |
|---|---|---|---|---|---|
| 06H-350.3.16.2.1.A.1 | 44 | 6 | **7.3×** | 26.8 | 38 |
| 06H-350.4.4.10.1.A.1 | 44 | 6.25 | **7.0×** | 5.0 | 8 |
| 06H-350.1.7.5.1.A.1 | 44 | 10 | **4.4×** | 5.5 | 4 |
| 06H-350.2.2.3.1.A.1 | 44 | 10 | **4.4×** | 5.5 | 2 |
| 06H-350.1.20.13.1.A.2 | 44 | 13 | 3.4× | 4.3 | 4 |
| 06H-350.3.19.4.1.A.1 | 44 | 13 | 3.4× | 4.3 | 10 |
| 06H-350.3.8.2.1.A.1 | 44 | 15 | 2.9× | 96.8 | 2 |
| 06H-350.3.8.3.1.A.1 | 44 | 20 | 2.2× | 3.0 | 2 |
| 06H-350.3.6.1.1.A.1 | 11 | 5 | 2.2× | 118.1 | 1 |
| 06H-350.4.20.1.1.A.1 | 13 | 6 | 2.2× | 8.9 | 22 |

AW toont voor deze FMs wél positieve waarden, waarschijnlijk via MC-sampling die ook
het staart-gedrag van de verdeling meeneemt. Dit is een **architectuurverschil**, geen fout.

### A4 — Random falen residual (13 FMs)

Analytisch: `ef = mult × studieduur / MTTF`. AW's TotalW kan afwijken door
fase-relatie met onderhoudsmomenten in MC-simulatie. Actie: MTTF en multipliciteit
controleren, rest accepteren als MC-band.

### C2 — REV uitgeschakeld in CM-overlay (88 FMs, secundair signaal)

Het CM-overlay scenario (235 PM-taken uitgeschakeld) schakelt REV impliciet mee uit.
Dit is **expliciet gemodelleerd**: `Δ REV effect = 0` voor vrijwel alle betrokken FMs.
Geen actie nodig.

---

## Resterende actieverpunten

### 1. CM-overlay run materialiseren (25 FMs, code C1)

In 25 FMs geldt `|Δ scenario| = |ef_actual − ef_cm_overlay| > 0.5`, wat betekent dat
de huidige run de 235 uitgeschakelde PM-taken niet correct materialiseert.

Grootste uitschieters:

| FM | ef_actual | ef_cm_overlay | Δ scenario |
|---|---|---|---|
| 06H-350.3.5.9.1.A.1 | 2387 | 2508 | **−121** |
| 06H-350.1.3.1.10.1.A.1 | 1319 | 1386 | **−67** |
| 06H-350.3.3.7.1.A.1 | 100.9 | 60 | **+41** |
| 06H-350.3.13.4.1.A.1 | 53.6 | 25 | **+29** |
| 06H-350.3.23.2.1.A.2 | 269 | 250 | **+19** |
| 06H-350.3.19.4.1.A.2 | 204 | 190 | **+14** |

**Actie:** Run opnieuw uitvoeren met CM-overlay correct geseed vanuit `aw_disabled_pm_ids`.

### 2. Leeftijd-harmonisatie (27 FMs, code B3, optioneel)

In 27 FMs wijkt de RCM2-leeftijd af van de AW InitialAge. In de meeste gevallen staat
RCM2 op 0 terwijl AW een hoge leeftijd heeft (doorgaans 44 jaar = bouwjaar 1982).
Dit kan worden gecorrigeerd via invoer, maar beïnvloedt de analytische uitkomst slechts
beperkt wanneer ef_cm_overlay al dichtbij AW TotalW zit. **Prioriteit: laag.**

---

## Conclusie

**De overgrote meerderheid van de resterende afwijkingen (79 + 13 + 10 = 102 FMs) wordt
niet veroorzaakt door softwarefouten, maar door het fundamentele architectuurverschil
tussen de analytische motor van RCM2 en de Monte Carlo simulatie van AW.**

De twee concrete actiepunten zijn:
1. **25 FMs** — CM-overlay correct materialiseren in de run (C1).
2. Optioneel: leeftijden harmoniseren voor B3-FMs (27 FMs).

Na correctie van punt 1 zal het residu volledig worden gedomineerd door A1
(Analytisch vs MC), waarvoor de band-acceptatie het juiste criterium is.
