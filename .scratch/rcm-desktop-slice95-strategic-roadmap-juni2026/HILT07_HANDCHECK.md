# HILT07 — Handcheck vergelijkingswerkruimte

**Issue:** slice 95 issue 07  
**Datum:** 2026-06-13  
**Status:** te verifiëren door analist

## Doel

Visuele QA van dual-project vergelijking vóór merge: twee echte klantprojecten,
balanced split per faalwijze (invoer- én resultaatdiffs).

## Stappen

1. Start resultatenwerkruimte (`python -m rcm_desktop.main`).
2. Menu **Analyse → Vergelijk modellen…** (Ctrl+Shift+L).
3. Kies **project A** en **project B** (`.rcm.json`).
4. Klik **Vergelijk**.
5. Controleer FM-lijst:
   - [ ] Regels met status **beide**, **alleen A**, **alleen B** kloppen.
   - [ ] Kolommen Invoer Δ / Resultaat Δ tonen verwachte aantallen.
6. Selecteer een gepaarde FM (beide):
   - [ ] Detail toont velddiffs (MTTF, faaltype, …) indien van toepassing.
   - [ ] Detail toont resultaatdiffs indien beide modellen een run/cache hebben.
7. Herhaal met **Haarlem Waarderpolder demo** + tweede klantproject:
   - Pad A: `tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.cache.json` → bij voorkeur echte `.rcm.json` export
   - Pad B: tweede `.rcm.json` uit klantomgeving
8. Sluit vergelijkingswerkruimte; dagelijkse werkruimte blijft ongewijzigd.

## Notities

| Project A | Project B | Bevindingen |
|-----------|-----------|-------------|
| | | |

## Akkoord

- [ ] Analist akkoord — issue 07 kan op `done`
