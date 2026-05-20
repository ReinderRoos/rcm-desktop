# Slice 34 — FM-verificatie in de resultatenwerkruimte

**Triage:** done  
**Type:** AFK (adapter + werkruimte-UI; geen `rcm_core`-schema-wijziging)  
**Parent:** slice 23 (resultatenwerkruimte), grill-me slice 8 / FM-spot-check (2026-05-19)  
**Relatie slice 8:** layout-close-out ValidateWindow blijft **uitgesteld**; zie deferred notities in slice-8 PRD  
**Versie:** 1.0  
**Datum:** 2026-05-19

## Problem Statement

Reliability-analisten willen **één faalwijze (FM) precies kunnen controleren**: kloppen de getallen in de UI met wat ze handmatig of in een spreadsheet verwachten, inclusief **lifecycle-totalen** en — waar beschikbaar — **verdeling over horizonjaren** (`horizon_profile`)?

De **resultatenwerkruimte** (standaard venster) biedt modus **FM-detail** met een sorteerbare tabel van **alle** FM’s in PBS-scope, maar alleen **lifecycle-kolommen** per rij. Er is geen paneel dat:

- de **motor-output van één geselecteerde FM** ontleedt (faalmomenten, downtime-componenten, kosten, effectbijdragen);
- **jaar/bucket-reeksen** uit `FMHorizonProfile` toont en **reconcilieert** met lifecycle-totalen;
- de **FM-invoerhash** toont zodat invoerwijzigingen traceerbaar zijn.

Het legacy **ValidateWindow** (`--legacy-validate`) is een **projectcockpit** (bewerken, run, LTAP/PM what-if), geen FM-laboratorium. Analisten die daar nog naar zoeken, missen een expliciet pad in documentatie en product.

**Slice 8** (ValidateWindow-layout) lost dit niet op; die slice is na grill-me **uitgesteld** ten gunste van deze FM-verificatie-epic en documentatie in `CONTEXT.md`.

## Solution

1. **Documentatie (eerste deliverable):** Vastleggen in `CONTEXT.md` welke **drie lagen** FM-verificatie ondersteunen: (1) pytest/CLI reproduceerbaar, (2) interactief via resultatenwerkruimte, (3) legacy ValidateWindow alleen voor bewerken/LTAP — met disclaimer dat jaar-voor-jaar FM-inspectie in UI **deze slice** levert.

2. **FM-inspector in modus FM-detail:** Na selectie van **één rij** in de FM-resultatentabel een **inspectorpaneel** onder (of naast) de tabel met:
   - **Identiteit:** `fm_id`, faalwijze-omschrijving, PBS-id, bouwdeel;
   - **Lifecycle-samenvatting:** `expected_failures`, downtime (raw, detection, PM, totaal), CM/PM/totaal kosten, `effect_bijdragen` (compact);
   - **Jaartabel:** per kalenderjaar (mapping uit project `modeljaar` + `lifecycle_years`, zelfde als LCC) de bucket-waarden uit `horizon_profile` — faalmomenten-proxy, correctief EUR, downtime uur, verborgen NB uur;
   - **Reconcile-regels:** expliciete status of som buckets ≈ lifecycle (toleranties zoals bestaande NB/LCC-proxy-tests); waarschuwing als `horizon_profile` ontbreekt (cache-migratie/legacy).

3. **FM-invoerhash:** Toon `compute_fm_hash`-resultaat voor de geselecteerde FM (via bestaande cache-helper / adapter), zodat de analist ziet of een bewerking deze FM opnieuw laat rekenen.

4. **Geen motorwijziging:** Alle waarden komen uit `RunResult` / `FMResult` na bestaande run; geen nieuwe berekeningen in `rcm_core`.

## User Stories

### Documentatie en mentaal model

1. Als analist wil ik in `CONTEXT.md` lezen **waar** ik één FM controleer, zodat ik niet in ValidateWindow-layout zoek.
2. Als analist wil ik weten dat **pytest + fixtures** de strengste verificatie zijn, zodat ik regressies vastleg voordat ik in de UI kijk.
3. Als analist wil ik weten dat **FM-detail in de werkruimte** de interactieve plek is na slice 34, zodat ik het standaard venster gebruik.
4. Als trainer wil ik legacy ValidateWindow **niet** aanbevelen voor FM-spot-check, zodat cursisten niet verkeerd trainen.

### Selectie en scope

5. Als analist wil ik in modus **FM-detail** een FM **aan klikken** in de bestaande tabel, zodat de inspector die FM toont.
6. Als analist wil ik dat de inspector **alleen FM’s in actieve PBS-scope** kan tonen (zelfde filter als de tabel), zodat scope consistent blijft.
7. Als analist wil ik bij **geen selectie** een korte lege staat (“selecteer een faalwijze”), zodat het paneel niet rommelig is.
8. Als analist wil ik bij **wissel van PBS-scope** de selectie resetten of valideren, zodat ik geen FM buiten scope inspecteer.

### Lifecycle-samenvatting

9. Als analist wil ik **lifecycle-totalen** van de geselecteerde FM in één blok zien, zodat ik die kan afzetten tegen mijn verwachting.
10. Als analist wil ik **downtime-componenten** (raw, detection delay, PM) gescheiden zien, zodat ik begrijp waar het totaal vandaan komt.
11. Als analist wil ik **effectbijdragen per effectklasse** zien, zodat ik effectverdeling kan controleren.
12. Als analist wil ik **geen Risico-aggregaat** als primaire KPI in de inspector, zodat de UI consistent blijft met slice 33.

### Jaarreeks en reconcile

13. Als analist wil ik per **kalenderjaar** de bucket-waarden uit `horizon_profile` zien, zodat ik jaarlijkse verwachtingen kan checken.
14. Als analist wil ik een **reconcile-indicator** (OK / waarschuwing) zien of de som van buckets overeenkomt met lifecycle-totalen, zodat ik proxy-fouten spot.
15. Als analist wil ik bij **ontbrekend `horizon_profile`** een duidelijke melding, zodat ik weet dat alleen lifecycle-totalen betrouwbaar zijn.
16. Als analist wil ik dezelfde **kalenderjaar-mapping** als LCC/Tijdsplot, zodat jaar K in de inspector hetzelfde jaar is als in de grafiek.
17. Als analist wil ik **faalmomenten per bucket** zien via dezelfde proxy als Top 10/LCC (niet een tweede berekening in de view), zodat cijfers niet divergeren.

### Traceerbaarheid invoer

18. Als analist wil ik de **FM-invoerhash** zien voor de geselecteerde FM, zodat ik weet of mijn laatste bewerking deze FM invalideert.
19. Als ontwikkelaar wil ik de hash via de **bestaande cache-API** halen, zodat er geen tweede hash-definitie ontstaat.

### UX in FM-detail

20. Als analist wil ik de **FM-tabel** en inspector **tegelijk** kunnen zien (split verticaal), zodat ik niet hoef te wisselen tussen lijst en detail.
21. Als analist wil ik de inspector **alleen in modus FM-detail**, niet in Top 10 of Tijdsplot, zodat andere modi rustig blijven.
22. Als analist met klein venster wil ik dat de jaartabel **scrollbaar** is, zodat alle kolommen bereikbaar blijven.

### Architectuur en kwaliteit

23. Als ontwikkelaar wil ik een **Qt-vrije** `fm_verification_service`, zodat reconcile en jaar-mapping pytestbaar zijn zonder QApplication.
24. Als ontwikkelaar wil ik **views** alleen via `rcm_desktop.adapter` laten praten met run-data, zodat ADR UI/kern-decoupling geldt.
25. Als tester wil ik **adapter unit-tests** met fixture-`FMResult` (met en zonder `horizon_profile`), zodat reconcile-gedrag vastligt.
26. Als tester wil ik **pytest-qt smoke**: selectie in FM-tabel → inspector zichtbaar met verwachte `fm_id`.

### Niet-functioneel

27. Als productowner wil ik **geen `CACHE_INPUTS_VERSION`-bump**, zodat motor-output ongewijzigd blijft.
28. Als analist wil ik dat de inspector **read-only** is, zodat ik per ongeluk geen motorinvoer wijzig.

## Implementation Decisions

### Modules

| Module | Rol |
|--------|-----|
| **`fm_verification_service`** (nieuw, Qt-vrij) | Bouwt `FMVerificationView` uit `RCMProject`, `FMResult`, optioneel hash-string; jaar-mapping via bestaande kalenderjaar-helper; faalmomenten per bucket via zelfde pad als `contribution_horizon_value_service` / `lcc_profile`-proxy; reconcile-lifecycle vs som buckets. |
| **`fm_verification_year_table_model`** (nieuw, Qt) | Read-only tabel: kalenderjaar + kolommen faalmomenten, correctief EUR, downtime uur, verborgen NB uur (labels via `messages`). |
| **`results_workspace_window`** | FM-detail-pagina: split of stacked layout; `currentChanged` / selectie op FM-tabel → laad inspector; lege staat zonder selectie. |
| **`CONTEXT.md`** | Sectie *FM-verificatie & spot-check* (drie lagen B9a). |
| **Slice-8 PRD** | *Deferred* sectie bijwerken (geen implementatie nu). |

### `FMVerificationView` (conceptueel contract)

```python
@dataclass(frozen=True)
class FMVerificationLifecycle:
    expected_failures: float
    expected_raw_downtime_hr: float
    expected_detection_delay_hr: float
    expected_pm_downtime_hr: float
    expected_total_downtime_hr: float
    expected_cm_cost_eur: float
    pm_cost_eur: float
    total_cost_eur: float
    effect_bijdragen: tuple[tuple[str, float], ...]  # (klasse_id, waarde)

@dataclass(frozen=True)
class FMVerificationYearRow:
    calendar_year: int
    faalmomenten: float
    cor_eur: float
    cor_downtime_hr: float
    hidden_nb_hr: float

@dataclass(frozen=True)
class FMVerificationView:
    fm_id: str
    faalwijze_omschrijving: str
    pbs_id: str
    bouwdeel_naam: str
    fm_input_hash: str | None
    lifecycle: FMVerificationLifecycle
    year_rows: tuple[FMVerificationYearRow, ...]
    profile_missing: bool
    reconcile_ok: bool
    reconcile_notes: tuple[str, ...]  # korte NL-regels voor UI
```

- **Reconcile:** `sum(year_rows.faalmomenten) ≈ lifecycle.expected_failures` (1e-3); downtime/cost waar profile compleet — zelfde toleranties als `test_desktop_contribution_horizon_value_service` / NB-proxy; bij `profile_missing` → `reconcile_ok=False` met vaste note, geen stille OK.
- **Hash:** `compute_fm_hash(project, fm_id)` of equivalent uit cache-module; `None` als project/FM niet resolveerbaar.

### Werkruimte-gedrag

- Selectie: eerste geselecteerde rij in `FMResultsTableModel` (single-selection mode op FM-tabel in FM-detail).
- Inspector-data bron: actief scenario-slot `RunResult` (zelfde als FM-tabel vandaag); geen aparte run.
- Bij modus ≠ FM-detail: inspector verborgen of leeg; geen state leak naar andere modi.

### Deep module-afbakening

- **Niet** in de view: bucket-math, kalenderjaar-index, reconcile — alles in `fm_verification_service`.
- **Wel** in de view: layout, selectie-events, formatting via bestaande `format_*` helpers of table model `DisplayRole`.

## Testing Decisions

**Goede tests** asserten op **waarden en zichtbare labels**, niet op widget-diepte:

- Gegeven `FMResult` met bekend `horizon_profile`: `build_fm_verification_view` levert N jaarrijen, reconcile OK, lifecycle matcht motorvelden.
- Gegeven FM zonder profile: `profile_missing=True`, geen jaarrijen of lege rijen + note.
- pytest-qt: run + open werkruimte → FM-detail → selecteer rij → inspector toont `fm_id` en minstens één lifecycle-label.

**Modules met tests (verplicht):**

| Module | Type |
|--------|------|
| **fm_verification_service** | Unit — reconcile, mapping, missing profile, hash aanwezig |
| **fm_verification_year_table_model** | Unit — kolommen, formatting |
| **results_workspace_window** | pytest-qt smoke — selectie → inspector |

**Prior art:** `tests/test_desktop_contribution_horizon_value_service.py`, `tests/test_desktop_result_filter_service.py`, `tests/test_desktop_results_workspace_window.py` (FM-detail modus).

## Out of Scope

- **ValidateWindow-layout** (slice 8 close-out: idle_banner, PBS-tabelmodel opruimen) — apart uitgesteld.
- **Bewerken** van faalwijzen of motorinvoer vanuit de inspector (blijft ValidateWindow / toekomstige edit-flow).
- **LTAP / PM what-if** per FM (planning blijft elders).
- **Monte Carlo**, Excel-export, vergelijking van twee scenario’s op FM-niveau in één inspector.
- **Nieuwe motorvelden** of wijziging `FMHorizonProfile`-schema.
- **Volledige verwijdering** van legacy ValidateWindow.
- **Automatische “expected value” invoer** door de gebruiker (geen spreadsheet-import in deze slice).

## Further Notes

### Relatie andere slices

| Slice | Relatie |
|-------|---------|
| 23 | Werkruimte-host; FM-detail-modus bestaat |
| 33 | Geen Risico-metric in UI; inspector volgt |
| 27 | `horizon_profile` SSOT; geen herschaling naar lifecycle |
| 22 | Bucket-faalmomenten-proxy; hergebruik patronen |
| 8 | Layout deferred; issue 20 done in code, 21 ready-for-human |

### Risico’s

- **Proxy vs motor:** jaar-faalmomenten in inspector zijn presentatie-proxy; disclaimer in UI/tooltip.
- **Hash zonder geladen project:** toon placeholder als validate/project ontbreekt.
- **Selectie vs multi-select:** enforce single-row voor inspector-clarity.

### Issues (gepubliceerd)

| # | Titel | Triage |
|---|--------|--------|
| 01 | FM-verificatie documenteren in CONTEXT.md | done |
| 02 | fm_verification_service: lifecycle, jaren, reconcile, hash | done |
| 03 | FM-inspector: selectie + lifecycle in FM-detail | done |
| 04 | FM-inspector: jaartabel + reconcile | done |

Afhankelijkheden: 01 ∥ 02; 02 → 03 → 04.
