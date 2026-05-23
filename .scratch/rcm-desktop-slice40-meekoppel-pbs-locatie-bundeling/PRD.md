# Slice 40 — Meekoppelkansen PBS-locatie bundeling (Planning-2b fix)

**Triage:** ready-for-agent  
**Type:** AFK (adapter + werkruimte-UI; geen motorwijziging)  
**Parent:** slice 39 (meekoppelkansen); ADR-0005 (amendement); slice 28–30 (overlay-shift); slice 38 (LCC render-cache)  
**Versie:** 1.0  
**Datum:** 2026-05-23  
**Referentie-fixture:** `tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json`  
**Supersedes:** geplande slice 40 “PBS-bundeling op `element_naam`” — merged in deze slice

## Problem Statement

Slice 39 leverde meekoppelkansen in de resultatenwerkruimte (LCC + what-if), maar de discovery groepeerde op **`element_naam`** (tekstveld op `PBSItem`). Bij Isograph-import krijgen veel PBS-knooppunten dezelfde `Description` als `element_naam`, terwijl het **verschillende locaties** in de boom zijn (`pbs_id`).

Gevolg voor analisten (getest op AWZI Haarlem):

- Slechts **enkele megagroepen** (bijv. twee rijen) terwijl het project veel REV-locaties heeft.
- **Toepassen** verschuift onbedoeld REV-taken over **het hele project** die toevallig dezelfde type-naam delen — niet “op dit element onder dit subsysteem”.
- De oude paar-weergave (PM A/B) was evenmin intuïtief; de tussenliggende elementgroep op `element_naam` loste het scope-probleem niet op.

Analisten willen **per fysieke PBS-locatie** in de navigatieboom zien welke REV-momenten binnen het tijdsvenster liggen, en **alle REV’s op die locatie** in één actie kunnen bundelen naar het **vroegste of laatste** due-jaar — realistisch default **laatste** (uitstellen naar gemeenschappelijk moment).

## Solution

Vervang discovery en presentatie door **PBS-locatiebundeling**:

1. **Discovery (adapter, Qt-vrij):** groepeer REV-taken op **`pbs_id`** (PBS-knoop van de gekoppelde faalwijze). Toon groep als ≥ 2 REV op die knoop **en** max(due) − min(due) ≤ N (default 2). Due-jaar = `int(round(interval_jaar))` (bestaand contract).
2. **Locatielabel:** boompad via `parent_pbs_id`-keten; label per niveau = `bouwdeel_naam` (fallback `pbs_id`) — consistent met navigatieboom.
3. **Tabel (compact):** boompad, PBS-id, # REV, due-bereik (min–max), span Δ. Geen lange PM-lijst in de hoofdtabel.
4. **Preview:** volledige PM-lijst met verschuivingen per taak; anker **vroegste** of **laatste** due-jaar (toggle). Default **laatste**.
5. **Toepassen:** alle REV’s in de groep naar gekozen anker via bestaande overlay-shift (`apply_overlay_shift` / `apply_bundle_shift`); geen motor-run; geen `.rcm.json`-mutatie. Apply zonder preview gebruikt default **laatste** anker.
6. **ADR-0005 amenderen:** discovery op `pbs_id`; default anker laatste; `element_naam`-collisie als historische RCM1-parity-noot.
7. **Legacy opruimen:** paar-gebaseerde API (`MeekoppelSuggestion`, `discover_meekoppelkansen` voor UI) verwijderen; één datamodel `MeekoppelLocationGroup`.

Architectuurregels ongewijzigd: **UI → adapter → kern**; views geen `rcm_core` (typing-only).

## User Stories

### Discovery — per PBS-locatie

1. Als **onderhoudsingenieur** wil ik meekoppelkansen **per PBS-locatie** zien, zodat bundelen alleen REV’s op **deze knoop** raakt.
2. Als **analist** wil ik groeperen op **`pbs_id`**, niet op `element_naam`, zodat identieke type-namen op verschillende locaties niet samensmelten.
3. Als **analist** wil ik alleen **REV-taken** in groepen, zodat het gedrag voorspelbaar blijft.
4. Als **analist** wil ik een groep alleen als **≥ 2 REV** op dezelfde `pbs_id` hangen, zodat enkelvoudige locaties geen ruis geven.
5. Als **analist** wil ik dat **max(due) − min(due) ≤ N** (default 2) voor de hele groep, zodat alleen nabije momenten gebundeld worden.
6. Als **analist** wil ik **N instelbaar** (1–5), zodat ik het venster kan aanscherpen of verbreden.
7. Als **analist** wil ik due-jaar = **`round(interval_jaar)`** plus overlay-offset in preview/apply, zodat what-if-shift consistent blijft met LCC.
8. Als **analist** wil ik **geen groep** voor interval ≤ 0 of ontbrekende FM/PBS, zodat incomplete data wordt overgeslagen.
9. Als **maintainer** wil ik discovery **pure adapter-logica** (geen Qt), zodat gedrag pytestbaar is.
10. Als **analist** wil ik bij **project wisselen** geen stale groepen, zodat sessie-state schoon reset.

### Locatielabel — boompad

11. Als **analist** wil ik een **boompad** (root → … → knoop) zien, zodat ik de locatie herken in de linker navigatieboom.
12. Als **analist** wil ik padlabels via **`bouwdeel_naam`** per ancestor, zodat de sidebar en meekoppeltabel hetzelfde vocabulaire gebruiken.
13. Als **analist** wil ik een aparte **`pbs_id`-kolom**, zodat ik traceerbaar blijf naar Isograph/import.
14. Als **analist** wil ik fallback naar **`pbs_id`** als een padsegment leeg is, zodat het pad nooit blank is.
15. Als **trainer** wil ik in help-tekst dat due-jaren **levensduur-jaren** zijn (niet kalenderjaar uit de grafiek), zodat verwarring met LCC-as wordt voorkomen.

### Presentatie — compacte tabel

16. Als **analist** wil ik kolommen **boompad, PBS-id, # REV, due-bereik, span**, zodat ik snel scan welke locaties bundelbaar zijn.
17. Als **analist** wil ik **geen lange PM-lijst** in de hoofdtabel, zodat rijen overzichtelijk blijven.
18. Als **analist** wil ik een **empty-state** als geen groepen binnen N, zodat ik weet dat discovery liep.
19. Als **analist** wil ik meekoppelkansen **alleen in LCC + what-if**, zodat apply altijd overlay is (slice 39-contract).
20. Als **analist** wil ik **buiten what-if** een hint, zodat apply niet per ongeluk beschikbaar lijkt.

### Preview — volledig beeld vóór actie

21. Als **onderhoudsingenieur** wil ik in **Preview** alle PM’s met **van → naar** due-jaar zien, zodat ik begrijp wat verschuift.
22. Als **onderhoudsingenieur** wil ik **standaard bundelen naar het laatste** due-jaar, zodat het realistische uitstel-gedrag default is.
23. Als **onderhoudsingenieur** wil ik in preview kunnen **omschakelen naar vroegste** anker, zodat ik naar voren bundelen kan kiezen.
24. Als **onderhoudsingenieur** wil ik **blokkades** (SVO/WET) in preview, zodat apply niet stilletjes faalt.
25. Als **analist** wil ik preview **geen overlay muteren**, zodat verkennen veilig is.

### Apply — bundel op locatie

26. Als **onderhoudsingenieur** wil ik **Toepassen zonder preview** met default **laatste** anker, zodat ik snel kan werken na vertrouwd gedrag.
27. Als **onderhoudsingenieur** wil ik na preview **Toepassen** met het gekozen anker, zodat preview en actie consistent zijn.
28. Als **onderhoudsingenieur** wil ik dat **alle REV’s in de groep** meeschuiven naar het anker, zodat één actie de locatie bundelt.
29. Als **analist** wil ik **all-or-nothing** bij blokkade (SVO/WET), zodat overlay half-besmet raakt.
30. Als **analist** wil ik **geen motor-run** na apply, zodat CM pas na expliciet Herbereken komt (slice 28–29).
31. Als **analist** wil ik na apply **LCC-curve/jaardetail** vernieuwd zien via overlay `change_count`.
32. Als **analist** wil ik **Reset naar baseline** en iteratieve applies, zodat experimenten terugdraaibaar zijn.
33. Als **analist** wil ik **geen ltap_light-korting** bij expliciet meekoppelen (ADR-0005).

### Governance en kwaliteit

34. Als **productowner** wil ik **ADR-0005 geamendeerd**, zodat agents niet terugvallen op `element_naam`.
35. Als **maintainer** wil ik **legacy paar-API verwijderd**, zodat één discovery-pad onderhoudbaar blijft.
36. Als **tester** wil ik **unit tests** op pbs_id-groepering, pad-labels, venster, apply multi-PM.
37. Als **tester** wil ik **pytest-qt smoke** op werkruimte-paneel met nieuwe kolommen.
38. Als **maintainer** wil ik een **Haarlem-handchecklist** in handoff, zodat slice 39-gate opnieuw objectief is na fix.
39. Als **productowner** wil ik **Planning-2c** (functioneel meekoppelen) **expliciet out of scope**, zodat scope beheersbaar blijft.

## Implementation Decisions

### Modules (diep vs ondiep)

- **PBS-pad label service (nieuw, diep, Qt-vrij):**
  - Input: `RCMProject`, `pbs_id`.
  - Output: padstring (segmenten gescheiden, bijv. ` › `) via `parent_pbs_id`-loop naar root.
  - Label per segment: `bouwdeel_naam` if non-empty else `pbs_id`.
  - Deterministisch; geen Qt.

- **Meekoppelkansen discovery service (wijzig, diep):**
  - Vervang `MeekoppelElementGroup` / paar-model door **`MeekoppelLocationGroup`**: `pbs_id`, `path_label`, `tasks: tuple[MeekoppelRevTask, …]`, `min_due_jaar`, `max_due_jaar`, `span_jaar`.
  - Collect REV via `faalwijze.pbs_id`; groepeer op `pbs_id`; filter ≥ 2 taken en span ≤ N.
  - Verwijder `discover_meekoppelkansen` / `MeekoppelSuggestion` uit publieke API.

- **Meekoppel apply bridge (wijzig, diep):**
  - `preview_meekoppel_location` / `apply_meekoppel_location` op `MeekoppelLocationGroup`.
  - Default anchor: **`later`** (laatste effectief due-jaar in groep).
  - Preview: lijst `MeekoppelShiftMove` per PM die verschuift; blocked als enige taak SVO/WET.
  - Apply: bereken volledige `anchor_years`-map in één stap (all-or-nothing validatie); delegeer niet per PM los zonder rollback-gedrag.

- **Meekoppeltabelmodel (wijzig, ondiep):** kolommen compact; rij-type `MeekoppelLocationGroup`.

- **Resultatenwerkruimte (wijzig, ondiep):** sync discovery op locatiegroepen; preview-body met PM-lijst; `_meekoppel_last_anchor` default `"later"`; dialog default **laatste** aangevinkt; help-tekst bijwerken.

- **ADR-0005 (documentatie):** discovery `pbs_id`; default anker laatste; RCM1 `element_naam`-parity vervangen door RCM2-locatiesemantiek.

### Apply-semantiek (locatiegroep)

```
effective_due(pm) = round(interval_jaar) + round(overlay.anchor_years[pm])
target = min(effective_due) if anchor == "earlier" else max(effective_due)
for each pm in group.tasks where effective_due(pm) != target:
    shift_years = target - effective_due(pm)
    overlay.anchor_years[pm] += shift_years
```

### Contracten

- Meekoppelen = presentatie-overlay only; `last_run` / motor-cache ongewijzigd tot Herbereken.
- Geen wijziging `CACHE_INPUTS_VERSION` of domain model.
- Navigatieboom-builder ongewijzigd; pad-service mag dezelfde labelregel hergebruiken (geen duplicatie van boomstructuur-logica indien extractie zinvol).

## Testing Decisions

- **Goede tests** meten **extern gedrag**: aantal groepen, `pbs_id`-scheiding bij gelijke `element_naam`, padlabels, preview-moves, overlay na apply, fout bij SVO/WET — niet interne loopvolgorde.
- **Unit tests (geen Qt):**
  - Twee PBS metzelfde `element_naam`, verschillende REV → **twee groepen**, niet één.
  - Eén `pbs_id` met 3 REV, span ≤ N → één groep met 3 taken.
  - Span > N → geen groep.
  - Pad: parent chain levert verwacht segmenten.
  - Preview default **later**; toggle **earlier** keert shifts om.
  - Apply verschuift **alle** niet-anker PM’s; `change_count` stijgt.
  - SVO/WET → apply geblokkeerd, overlay ongewijzigd.
- **pytest-qt smoke:** LCC + what-if → tabel met boompad/PBS-id; apply → overlay update.
- **Prior art:** `test_meekoppelkansen_discovery_service.py`, `test_meekoppel_apply_service.py`, `test_desktop_meekoppel_workspace.py` (herschrijven, niet parallel legacy pad).
- **Handmatig:** Haarlem-checklist — verwacht **meer rijen** dan 2 megagroepen; elke rij **kleine lokale** REV-set; geen regressie LCC-snelheid (slice 36–38).

## Out of Scope

- **Planning-2c** functioneel meekoppelen (functie/taakgroep-dimension) — spike + go/no-go apart.
- **`ltap_light`-kortingsmodel** en impliciete samenval-korting.
- **Motor-run / passief-materialisatie** bij apply.
- **ValidateWindow / LTAP-pariteit** voor meekoppelkansen.
- **Subclusters** (connected components binnen één `pbs_id` bij wijd gespreide due-jaren) — bewust niet; volledige groep moet span ≤ N hebben.
- **Twee modi** (locatie vs `element_naam`) naast elkaar.
- **CSV/export** van suggesties.
- **Bulk apply** over meerdere groepen in één klik.

## Further Notes

- **Issue-volgorde (tracer-bullet):**

| # | Titel | Fase |
|---|--------|------|
| 01 | ADR-amendement + PBS-pad-service + locatie-discovery | A |
| 02 | Apply/preview locatiegroep + element-groep legacy weg | B |
| 03 | Compacte werkruimte-tabel + messages/help | B |
| 04 | Tests + Haarlem handoff | C |

- **Legacy-opruiming (issue 01 vs 02):** issue 01 verwijdert paar-only API (`MeekoppelSuggestion`, `discover_meekoppelkansen`); issue 02 verwijdert element-groep API en levert locatie-apply — UI blijft tussendoor werkend op element-groep tot issue 03 wired.

- **Relatie slice 39:** UI-paneel en what-if-gate blijven; alleen discovery/semantiek/presentatie wijzigen. Slice 39-handoff kan verwijzen naar slice 40 als correctie.
- **Grill-me besluiten (2026-05-23):** pbs_id, volledige groep span ≤ N, default anker laatste, boompad + PBS-id kolom, compacte tabel, apply zonder preview OK, slice 40 merged met geplande 2b.
- **Restrisico:** padlabels kunnen repetitief zijn als import dezelfde Description op alle niveaus zet — acceptabel; uniekheid via `pbs_id`.
