# HILT98 — Handcheck Monte Carlo engine v1

**Issue:** slice 98 issue 12  
**Datum:** 2026-06-14 (hervat 2026-06-13)  
**Status:** GO met kanttekening

## Doel

Visuele QA van MC Run-modus vóór merge: voortgang, seed, annuleren, FM-onzekerheidsbanden, analytische Top 10/LCC ongewijzigd.

## Voorbereiding

1. Start resultatenwerkruimte (`python -m rcm_desktop.main`).
2. Open demo-project (Haarlem of Gaarkeuken PM).
3. **Modelinstellingen:** `monte_carlo_n` = 1000, `monte_carlo_seed` = vast getal (bijv. 42).

## Stappen

1. Run-modus **Monte Carlo** in validatiestrip.
   - [x] Start analyse verborgen; Run A/B beschikbaar (MC-dispatch)
2. **Run → A** (MC-modus) — controleer:
   - [x] Voortgangspercentage zichtbaar in statusstrip
   - [x] Seed zichtbaar tijdens run
3. Na voltooiing — **FM-resultaten**:
   - [x] P50 in kolom; tooltip toont P10 en P90 (geen P50 in tooltip)
4. **Annuleren:** start opnieuw, klik **Annuleren** halverwege:
   - [x] Status geannuleerd; geen banden in FM-resultaten
5. **Reproduceerbaarheid:**zelfde seed, opnieuw run:
   - [x] Banden stabiel (zelfde P50 binnen afronding)
6. Schakel Run-modus terug naar **Analytisch** (zonder herbereken):
   - [x] FM-resultaten leeg wanneer geen prior analytische run (verwacht)
   - [ ] Niet getest: puntwaarden na eerdere analytische run (geen prior run in sessie)

## Kanttekening

- Zonder eerdere analytische run zijn FM/Top10/LCC leeg na omschakeling naar Analytisch — verwacht gedrag, geen bug. Herbereken analyse vult views (niet opnieuw getest in deze sessie).

## Akkoord

| Analist | Datum | GO / NO-GO | Opmerkingen |
|---------|-------|------------|-------------|
| ReinderRoos | 2026-06-13 | GO met kanttekening | MC via Run A/B; tooltip P10/P90 OK; leeg analytisch zonder prior run |
