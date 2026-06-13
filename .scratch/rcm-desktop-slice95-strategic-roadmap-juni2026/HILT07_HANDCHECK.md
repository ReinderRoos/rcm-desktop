# HILT07 — Handcheck vergelijkingswerkruimte

**Issue:** slice 95 issue 07  
**Datum:** 2026-06-13  
**Status:** handchecked door analist (2026-06-13)

## Doel

Visuele QA van dual-project vergelijking vóór merge: twee echte klantprojecten,
balanced split per faalwijze (invoer- én resultaatdiffs).

## Stappen

1. Start resultatenwerkruimte (`python -m rcm_desktop.main`).
2. Menu **Analyse → Vergelijk modellen…** (Ctrl+Shift+L).
3. Kies **project A** en **project B** (`.rcm.json`).
4. Klik **Vergelijk**.
5. Controleer FM-lijst:
   - [x] Regels met status **beide**, **alleen A**, **alleen B** kloppen.
   - [x] Kolommen Invoer Δ / Resultaat Δ tonen verwachte aantallen.
6. Selecteer een gepaarde FM (beide):
   - [x] Detail toont velddiffs (MTTF, faaltype, …) indien van toepassing.
   - [x] Detail toont resultaatdiffs indien beide modellen een run/cache hebben.
7. Herhaal met **Haarlem Waarderpolder demo** + tweede klantproject:
   - Pad A: `tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.cache.json` → bij voorkeur echte `.rcm.json` export
   - Pad B: tweede `.rcm.json` uit klantomgeving
8. Sluit vergelijkingswerkruimte; dagelijkse werkruimte blijft ongewijzigd.

## Notities

| Project A | Project B | Bevindingen |
|-----------|-----------|-------------|
| Klantproject (analist) | Tweede klantproject | Analist bevestigde 2026-06-13: vergelijk-FM-lijst, detailpaneel veld/resultaatdiffs en MC run-modus stub zichtbaar; akkoord voor issue 07. |

## Akkoord

- [x] Analist akkoord — issue 07 kan op `done`
