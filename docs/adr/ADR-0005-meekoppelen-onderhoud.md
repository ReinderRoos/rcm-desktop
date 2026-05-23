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
| **2b** | PBS-locatiebundeling: alle REV per `pbs_id`, boompad, default laatste anker | 40 |
| **2c** | Functioneel meekoppelen — spike + go/no-go vóór slice 41 | 41+ |

### UX

- **Voorstel-first:** suggesties zijn advies; geen automatische shift zonder expliciete actie.
- **Auto-apply = opt-in:** knop **Toepassen** na preview; geen stille mutatie.

### Apply-semantiek (2a)

- Alleen **presentatie-overlay** (`anchor_years` / `disabled_pm_ids`); **geen motor-run**, geen mutatie van opgeslagen `.rcm.json` tot herberekenen.
- Apply delegeert aan bestaande `apply_overlay_shift` / `apply_bundle_shift`.
- Preview toont huidige → doeljaren; **muteert overlay niet**.
- Default anker: **laatste** effectieve due-jaar (2b); **eerdere** was default in 2a.
- **Geen ltap_light-korting** bij expliciet meekoppelen; LCC toont som van individuele taakkosten.

### Discovery (2b, RCM2-locatiesemantiek)

- Alleen `TaskType.REV`; `interval_jaar > 0`; FM/PBS aanwezig.
- Due-jaar = `int(round(interval_jaar))`.
- Groep per **`pbs_id`** (faalwijze-PBS-knoop): ≥ 2 REV op dezelfde locatie en `max(due) − min(due) ≤ N` (default **N = 2**).
- Locatielabel: boompad via `parent_pbs_id`; segment = `bouwdeel_naam` of fallback `pbs_id`.
- **Geen** groepering op globale `element_naam` (RCM1-parity verlaten vanwege import-collisies).

### Discovery (2a, historisch)

- Paar/groep op zelfde `element_naam` — vervangen door 2b in slice 40.

### UI-plaats

- Alleen **resultatenwerkruimte**, modus **LCC**, **what-if planning actief**.
- **Geen** meekoppelkansen in ValidateWindow/LTAP (één productpad).

### Scrub-list

- **Meekoppelkansen:** toegestaan via deze ADR (adapter-only).
- **`ltap_light`:** blijft **out of scope** (geen kortingsmodel in Planning-2).

### Go/no-go

- Slice **40** (2b) start pas na slice 39 + groene Haarlem-handchecklist (zie slice 39 handoff).

### Restrisico

- **`element_naam`-collisie (2a):** verschillende PBS met dezelfde elementnaam werden als één element beschouwd — opgelost in 2b via `pbs_id`.

## Consequenties

- Nieuwe adapter-services: discovery + apply-bridge; tests in `tests/test_desktop_meekoppel*.py`.
- Bestaande overlay- en LCC-presentatie blijven leidend voor cache-invalidatie (`change_count`).
