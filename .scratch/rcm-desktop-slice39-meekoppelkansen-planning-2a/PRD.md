# Slice 39 — Meekoppelkansen (Planning-2a)

**Triage:** ready-for-agent  
**Type:** AFK (adapter + werkruimte-UI; geen motorwijziging)  
**Parent:** slice 28–30 (LCC what-if, overlay-shift); slice 38 (LCC render-cache); fase 0 ADR-0005 (meekoppelen onderhoud)  
**Versie:** 1.0  
**Datum:** 2026-05-21  
**Referentie-fixture:** `tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json`

## Problem Statement

In RCM1 kon de analist **meekoppelkansen** zien: paren van REV-taken op hetzelfde PBS-element waarvan de eerste due-jaren dicht bij elkaar liggen (standaard binnen 2 jaar). Dat hielp om onderhoud te **bundelen in de tijd** zonder alles handmatig te zoeken.

In RCM2 is handmatig verschuiven al mogelijk (LCC-modus, what-if aan, selectie in jaardetail, `apply_overlay_shift`), maar er is **geen discovery-laag**: de gebruiker moet zelf REV-paren op hetzelfde element vinden en jaren vergelijken. Meekoppelkansen stonden bewust op de scrub-list (`CONTEXT.md`: *meekoppelkansen buiten scope tracer-bullet*).

Na fase 0 (ADR-0005) is **Planning-2a** de eerste implementatiestap: **suggesties tonen** en optioneel **auto-apply** als overlay-shift — zonder motor-run, zonder LTAP-light-korting, zonder ValidateWindow-pariteit. PBS-bundeling (2b) en functioneel meekoppelen (2c) volgen pas na go/no-go.

## Solution

Voeg in de **resultatenwerkruimte** (alleen **LCC + What-if planning actief**) een **meekoppelkansen-paneel** toe:

1. **Discovery (adapter):** pure service die uit `RCMProject` suggestierijen bouwt met **RCM1-parity** (REV-only, zelfde PBS-`element_naam`, `|jaar_a − jaar_b| ≤ N`, default N=2). Geen port van scrub-list-module `meekoppelkansen_v1.py`; geen pandas.
2. **Presentatie:** sorteerbare tabel met element, PM-id’s, due-jaren, delta, korte reden. Instelbaar tijdsvenster N (default 2).
3. **Voorstel-first + auto-apply:** per suggestie **Preview** (huidige jaren → doeljaren na shift) en optioneel **Toepassen** (expliciete opt-in). Apply = alleen **overlay-shift** via bestaande bundel-engine; LCC-curve/plot vernieuwt; **geen** stille herberekening; project-JSON ongewijzigd.
4. **Apply-semantiek (2a, paar):** default anker = **eerdere** due-jaar; verschuif de **latere** taak naar het eerdere jaar. Preview toont beide PM’s, shift-bedrag en geblokkeerde taken (SVO/WET). Gebruiker kan in preview het anker omdraaien (naar later jaar) vóór apply.
5. **Kosten:** geen ltap_light-korting bij expliciet meekoppelen; LCC toont som van individuele taakkosten (bestaand contract).

Architectuurregels: **UI → adapter → kern**; suggestie-logica en apply-bridge **test-first** in adapter; views geen `rcm_core` (typing-only).

## User Stories

### Discovery — meekoppelkansen vinden

1. Als **onderhoudsingenieur** wil ik een **lijst van meekoppelkansen** zien, zodat ik REV-taken op hetzelfde element met nabije due-jaren snel vind.
2. Als **analist** wil ik dat alleen **REV-taken** in suggesties voorkomen, zodat het gedrag overeenkomt met RCM1.
3. Als **analist** wil ik suggesties alleen voor taken op het **zelfde PBS-element** (`element_naam`), zodat koppeling fysiek plausibel blijft.
4. Als **analist** wil ik dat due-jaren **binnen een tijdsvenster N** liggen (default **2 jaar**), zodat ik focus houd op realistische bundelkansen.
5. Als **analist** wil ik **N instelbaar** maken (bijv. 1–5), zodat ik strenger of ruimer kan zoeken zonder code te wijzigen.
6. Als **analist** wil ik per suggestie **PM-id A/B, PBS-id’s, jaar A/B, delta en reden** zien, zodat ik kan verifiëren vóór actie.
7. Als **analist** wil ik **geen suggesties** voor taken met interval ≤ 0 of ontbrekende FM/PBS-koppeling, zodat incomplete data geen ruis geeft.
8. Als **maintainer** wil ik dat discovery **pure adapter-logica** is (geen Qt), zodat gedrag reproduceerbaar getest wordt.
9. Als **maintainer** wil ik **RCM1-parity** op de heuristiek, zodat Haarlem/legacy-verwachtingen traceerbaar zijn (due-jaar = `round(interval_jaar)` zoals RCM1).
10. Als **analist** wil ik bij **grote projecten** een performante suggestielijst, zodat het paneel niet de LCC-flow blokkeert (lazy build of cache op project-digest acceptabel).

### Context — waar en wanneer

11. Als **analist** wil ik meekoppelkansen **alleen in LCC-modus** zien, zodat planning en suggesties één mentaal model delen.
12. Als **analist** wil ik het paneel **alleen zichtbaar als What-if planning actief** is, zodat apply altijd een overlay-actie is.
13. Als **analist** wil ik **buiten what-if** een korte hint (“Schakel what-if in…”) of verborgen paneel, zodat ik niet denk dat apply beschikbaar is zonder overlay.
14. Als **productowner** wil ik **geen** meekoppelkansen in **ValidateWindow/LTAP**, zodat er één productpad blijft (slice 28-strategie).
15. Als **trainer** wil ik documentatie dat meekoppelen **geen mutatie van het opgeslagen project** is, zodat baseline-run intact blijft tot herberekenen.

### Preview — voorstel-first

16. Als **onderhoudsingenieur** wil ik vóór apply een **preview** zien (huidige due-jaren → doeljaren), zodat ik de impact begrijp.
17. Als **onderhoudsingenieur** wil ik in preview zien **welke PM verschuift** en met **hoeveel jaren**, zodat er geen verrassingen zijn.
18. Als **onderhoudsingenieur** wil ik **standaard** de **latere** taak naar het **eerdere** due-jaar kunnen laten schuiven, zodat bundelen naar het vroegste moment gaat.
19. Als **onderhoudsingenieur** wil ik in preview het **anker kunnen omdraaien** (naar later jaar), zodat ik flexibel kan kiezen per situatie.
20. Als **onderhoudsingenieur** wil ik in preview **blokkades** zien als een taak **niet verschuifbaar** is (SVO/WET), zodat apply niet stilletjes faalt.
21. Als **analist** wil ik preview **geen overlay muteren**, zodat ik veilig kan verkennen.
22. Als **analist** wil ik preview **meerdere suggesties achter elkaar** kunnen openen zonder side-effects, zodat ik kan vergelijken.

### Auto-apply — overlay-shift

23. Als **onderhoudsingenieur** wil ik op **Toepassen** de voorgestelde shift **direct op de overlay** zetten, zodat ik niet handmatig jaren hoef in te voeren.
24. Als **onderhoudsingenieur** wil ik dat apply **bestaande bundelregels** volgt (all-or-nothing, SVO/WET-blokkade), zodat gedrag gelijk is aan handmatige shift.
25. Als **analist** wil ik na apply dat **LCC-curve en jaartabel** vernieuwen, zodat ik het bundeleffect direct zie.
26. Als **analist** wil ik dat apply **geen automatische motor-run** start, zodat correctief/CM-impact pas na expliciet **Herbereken analyse** komt (slice 28–29-contract).
27. Als **analist** wil ik dat **meerdere applies** cumulatief op de overlay werken (change_count stijgt), zodat ik iteratief kan bundelen.
28. Als **analist** wil ik na apply de **suggestielijst** opnieuw kunnen laten evalueren (refresh), zodat vervulde kansen verdwijnen of veranderen.
29. Als **analist** wil ik **Reset naar baseline** nog steeds kunnen gebruiken, zodat experimenten terugdraaibaar zijn.
30. Als **analist** wil ik dat apply **passieve taken** (`disabled_pm_ids`) niet per ongeluk activeert, zodat overlay-semantiek intact blijft.

### Integratie LCC / what-if

31. Als **analist** wil ik na apply **jaardetail** consistent blijven met de overlay (via bestaande LTAP/LCC-keten), zodat plot, tabel en detail één waarheid delen.
32. Als **analist** wil ik **type-filters** en **PBS-scope** intact houden na meekoppel-apply, zodat slice 38-cache en filter-sticky gedrag niet breken.
33. Als **analist** wil ik meekoppel-apply **niet** verwarren met **handmatige shift** in jaardetail, zodat beide paden naast elkaar werken.
34. Als **analist** wil ik dat een PM die al een **anchor_years**-offset heeft, correct wordt meegenomen in preview (effectief due-jaar), zodat iteratieve bundeling klopt.
35. Als **analist** wil ik **geen ltap_light-korting** zien na expliciet meekoppelen, zodat kosten de som van taken blijven (ADR-0005).

### Leeg, fout en randgevallen

36. Als **analist** wil ik bij **geen suggesties** een duidelijke empty-state, zodat ik weet dat discovery liep maar niets vond.
37. Als **analist** wil ik bij **apply-fout** een begrijpelijke melding (zelfde toon als bundel-shift), zodat ik kan corrigeren.
38. Als **analist** wil ik **dubbele paren** niet dubbel in de lijst, zodat de tabel overzichtelijk blijft (geordende paar-key).
39. Als **maintainer** wil ik in ADR/PRD vermeld zien dat **`element_naam`-collisie** zeldzame false positives kan geven, zodat Haarlem-validatie daarop let.
40. Als **analist** wil ik bij **project wisselen** geen suggesties uit het vorige project, zodat sessie-state schoon reset.

### Observability en gates

41. Als **tester** wil ik **unit tests** op discovery-regels (REV-filter, element-match, venster, interval), zodat RCM1-parity CI-borgd is.
42. Als **tester** wil ik **adapter tests** op preview/apply (ok, SVO-blokkade, anker-omdraai), zodat overlay-contract vastligt.
43. Als **tester** wil ik **pytest-qt smoke** (what-if aan → suggestie → preview → apply → LCC update), zodat UI-wiring regressie vangt.
44. Als **maintainer** wil ik een **Haarlem-handchecklist** in handoff, zodat gate 2a→2b (slice 40) objectief is.
45. Als **productowner** wil ik dat slice 39 **klaar** is vóór Planning-2b start, zodat tracer-bullet-discipline geldt.

## Implementation Decisions

### Voorwaarde fase 0

Slice 39 implementatie gaat uit van **ADR-0005** (meekoppelen onderhoud) en **scrub-list-update** in `CONTEXT.md` (meekoppelkansen toegestaan via adapter; `ltap_light` blijft out). Issue 01 mag ADR + CONTEXT meeleveren als die nog ontbreken.

### Diepe modules (Qt-vrij, test-first)

- **Meekoppelkansen discovery service (nieuw, diep):**
  - Input: `RCMProject`, `window_years: int = 2`.
  - Output: immutable rijen (dataclass), velden analoog RCM1: `element_naam`, `pm_a`, `pm_b`, `pbs_a`, `pbs_b`, `jaar_a`, `jaar_b`, `jaar_delta`, `reden`.
  - Regels: alleen `TaskType.REV`; `interval_jaar > 0`; FM/PBS/`element_naam` aanwezig; due-jaar = `int(round(interval_jaar))` (**RCM1-parity**); paar alleen als zelfde `element_naam` en `jaar_delta ≤ window_years`; geen dubbele paren (canonieke ordering op pm_id).
  - Geen import van `meekoppelkansen_v1.py`; geen pandas.
  - Optioneel: memoization op `(project_digest, window_years)` in sessie-scoped cache als performance nodig blijkt.

- **Meekoppel apply bridge (nieuw, diep):**
  - Input: `RCMProject`, `PlanningOverlayState`, suggestie-rij, `anchor: Literal["earlier", "later"]` (default `"earlier"`).
  - Berekent `shift_years` voor de **niet-anker** PM t.o.v. huidige overlay (`anchor_years` meegenomen in effectief jaar voor preview).
  - Output: `MeekoppelPreview` (shifted_pm_id, shift_years, from_years, to_years, blocked_reason | None) en `MeekoppelApplyResult` (overlay | error).
  - Apply delegeert aan **`apply_overlay_shift`** (bestaande bundel-engine); geen parallel shift-pad.
  - All-or-nothing: één niet-verschuifbare taak in het paar → apply geblokkeerd met expliciete reden.

- **Planning overlay state (bestaand):** ongewijzigd contract; `change_count()` blijft cache-invalidering drijven (slice 38).

- **LCC / LTAP presentatie (bestaand):** geen shape-wijziging; apply triggert bestaande werkruimte-rerender voor LCC-modus.

### UI-wijzigingen (minimaal, alleen werkruimte)

- **Meekoppelkansen-paneel** in `ResultsWorkspaceWindow`, zichtbaar iff `modus == LCC` en `overlay.active`.
- Controls: venster N (spinbox, default 2), tabel suggesties, knoppen **Preview** / **Toepassen** per rij (of selectie + actiebalk).
- Preview: modale of inline panel met anker-toggle (vroegste/laatste), shift-samenvatting, blokkade-melding.
- Buiten what-if: paneel verborgen of disabled met copy naar what-if-toggle.
- **Geen** wijzigingen aan ValidateWindow.

### Apply-semantiek prototype (2a paar)

```
# default anchor = earlier due year
if anchor == "earlier":
    target_year = min(jaar_a, jaar_b)
    shifted_pm = pm with later effective due year
else:
    target_year = max(jaar_a, jaar_b)
    shifted_pm = pm with earlier effective due year
shift_years = target_year - effective_due_year(shifted_pm, overlay)
# apply_overlay_shift(project, overlay, pm_ids=[shifted_pm], shift_years=shift_years)
```

Effectief due-jaar = baseline due (`round(interval_jaar)`) + huidige `anchor_years.get(pm_id, 0)`.

### Contracten

- Meekoppelen = **presentatie-only overlay**; `last_run` / motor-cache ongewijzigd tot expliciete herberekening.
- **Geen korting** bij expliciet meekoppelen; impliciete samenval-korting is **niet** in slice 39 (productregel ADR, geen implementatie).
- Discovery is **advies**, geen optimalisatie-engine (caption-gedrag RCM1).

## Testing Decisions

- **Goede tests** meten **extern gedrag** (rijen, preview-jaren, overlay na apply, foutmeldingen), niet interne loopvolgorde.
- **Unit tests (geen Qt) — discovery service:**
  - REV-only; non-REV excluded.
  - Zelfde element vereist; verschillende elementen geen paar.
  - Venster N=2: delta 0–2 wel, delta 3 niet.
  - `interval_jaar <= 0` excluded.
  - Canonieke paar-uniekheid.
  - Fixture: minimaal `one_fm_planning` of kleine synthetic project; Haarlem-parity spot-check handmatig.
- **Unit tests — apply bridge:**
  - Preview default: latere taak → eerdere jaar.
  - Anker `"later"`: omgekeerde shift.
  - SVO/WET in paar → apply geblokkeerd, overlay ongewijzigd.
  - Succesvolle apply verhoogt overlay `change_count`.
  - Overlay al met offset → preview gebruikt effectief jaar.
- **Adapter integratie:**
  - `apply_overlay_shift` spy: exact één call met verwachte `pm_ids`/`shift_years`.
- **pytest-qt smoke (werkruimte):**
  - What-if aan → suggestietabel niet leeg op geschikte fixture (of gemockte adapter) → apply → LCC-status/overlay-indicator update.
  - What-if uit → apply-knop disabled/afwezig.
- **Prior art:** `test_desktop_planning_whatif*.py`, `test_desktop_lcc_*`, LTAP bundel-tests (`apply_bundle_shift`), slice 30 what-if UX tests.
- **Niet in CI:** wall-clock performance op Haarlem; wel handchecklist in handoff.
- **Gate (2a→2b):** handmatige Haarlem-checklist groen vóór slice 40 start.

## Out of Scope

- **Planning-2b** PBS-bundeling (alle REV per element, default laatste anker, toggle vroegste) — slice 40.
- **Planning-2c** functioneel meekoppelen — spike + slice 41 na product-go.
- **`ltap_light`-kortingsmodel** porten of impliciete korting implementeren.
- **Motor-run / passief-materialisatie** als onderdeel van apply; **epic B2** (ankers in motor).
- **ValidateWindow** pariteit of nieuwe LTAP-features.
- **CSV/export** van suggesties.
- **Herontwerp discovery** met functie-/taakgroep-dimension (hoort bij 2c).
- **Bulk auto-apply** van alle suggesties in één klik (alleen per suggestie v1).
- **Wijziging** `CACHE_INPUTS_VERSION` of domain model.

## Further Notes

- **Aanbevolen issue-volgorde (tracer-bullet):**

| # | Titel | Fase |
|---|--------|------|
| 01 | ADR-0005 + CONTEXT scrub-list (indien nog open) + discovery dataclass/API | A |
| 02 | Discovery unit tests + RCM1-parity op fixture | A |
| 03 | Meekoppel preview/apply bridge (overlay-shift) | B |
| 04 | Werkruimte-paneel (LCC + what-if only) + preview UI | B |
| 05 | pytest-qt smoke + Haarlem handoff / gate-checklist | C |

- **Restrisico’s:** `element_naam`-collisie; grote projecten O(n²) paar-loop — mitigatie via cache/paginering indien nodig; due-jaar via `interval_jaar` wijkt af van volledige LTAP-schedule (bewuste RCM1-parity).
- **Relatie slice 38:** apply invalideert LCC via overlay `change_count`; geen extra curve-key wijziging nodig.
- **Go/no-go:** slice 40 (2b) start pas na slice 39 + groene Haarlem-checklist (ADR-0005).
