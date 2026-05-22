# ADR-0005 — Meekoppelen onderhoud (Planning-2)

## Status

Accepted (2026-05-21).

## Datum

2026-05-21

## Context

RCM1 toonde **meekoppelkansen**: REV-taken op hetzelfde PBS-element met due-jaren binnen een tijdsvenster (standaard 2 jaar), zodat onderhoud in de tijd gebundeld kon worden. RCM2 had handmatige overlay-shift (LCC what-if, slice 28–30) maar geen discovery-laag. Meekoppelkansen stonden op de scrub-list; slice 39 lift dit voor **Planning-2a** via adapter-only implementatie.

## Beslissing

### Gefaseerde scope (Planning-2)

| Fase | Inhoud | Slice |
|------|--------|-------|
| **2a** | Discovery + suggestietabel + preview/apply als overlay-shift (paar, RCM1-parity) | 39 |
| **2b** | PBS-bundeling: alle REV per element, default laatste anker, toggle vroegste | 40 |
| **2c** | Functioneel meekoppelen — spike + go/no-go vóór slice 41 | 41+ |

### UX

- **Voorstel-first:** suggesties zijn advies; geen automatische shift zonder expliciete actie.
- **Auto-apply = opt-in:** knop **Toepassen** na preview; geen stille mutatie.

### Apply-semantiek (2a)

- Alleen **presentatie-overlay** (`anchor_years` / `disabled_pm_ids`); **geen motor-run**, geen mutatie van opgeslagen `.rcm.json` tot herberekenen.
- Apply delegeert aan bestaande `apply_overlay_shift` / `apply_bundle_shift`.
- Preview toont huidige → doeljaren; **muteert overlay niet**.
- Default anker: **eerdere** effectieve due-jaar; latere taak verschuift naar die jaar.
- **Geen ltap_light-korting** bij expliciet meekoppelen; LCC toont som van individuele taakkosten.

### Discovery (2a, RCM1-parity)

- Alleen `TaskType.REV`; `interval_jaar > 0`; FM/PBS/`element_naam` aanwezig.
- Due-jaar = `int(round(interval_jaar))`.
- Paar alleen bij zelfde `element_naam` en `|jaar_a − jaar_b| ≤ N` (default **N = 2**).
- Geen port van scrub-list `meekoppelkansen_v1.py`; geen pandas.

### UI-plaats

- Alleen **resultatenwerkruimte**, modus **LCC**, **what-if planning actief**.
- **Geen** meekoppelkansen in ValidateWindow/LTAP (één productpad).

### Scrub-list

- **Meekoppelkansen:** toegestaan via deze ADR (adapter-only).
- **`ltap_light`:** blijft **out of scope** (geen kortingsmodel in Planning-2).

### Go/no-go

- Slice **40** (2b) start pas na slice 39 + groene Haarlem-handchecklist (zie slice 39 handoff).

### Restrisico

- **`element_naam`-collisie:** verschillende PBS met dezelfde elementnaam worden als één element beschouwd (RCM1-parity).

## Consequenties

- Nieuwe adapter-services: discovery + apply-bridge; tests in `tests/test_desktop_meekoppel*.py`.
- Bestaande overlay- en LCC-presentatie blijven leidend voor cache-invalidatie (`change_count`).
