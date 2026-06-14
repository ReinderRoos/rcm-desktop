# HILT98 — Handcheck Monte Carlo engine v1

**Issue:** slice 98 issue 12  
**Datum:** 2026-06-14  
**Status:** open — wacht op analist

## Doel

Visuele QA van MC Run-modus vóór merge: voortgang, seed, annuleren, FM-onzekerheidsbanden, analytische Top 10/LCC ongewijzigd.

## Voorbereiding

1. Start resultatenwerkruimte (`python -m rcm_desktop.main`).
2. Open demo-project (Haarlem of Gaarkeuken PM).
3. **Modelinstellingen:** `monte_carlo_n` = 1000, `monte_carlo_seed` = vast getal (bijv. 42).

## Stappen

1. Run-modus **Monte Carlo** in validatiestrip.
2. **Start analyse** — controleer:
   - [ ] Voortgangspercentage zichtbaar in statusstrip
   - [ ] Seed zichtbaar tijdens run
3. Na voltooiing — **FM-resultaten**:
   - [ ] P10/P50/P90 zichtbaar voor kosten, downtime, faalgebeurtenissen (P50 kolom + tooltip of band-layout)
4. **Annuleren:** start opnieuw, klik **Annuleren** halverwege:
   - [ ] Status geannuleerd; geen banden in FM-resultaten
5. **Reproduceerbaarheid:**zelfde seed, opnieuw run:
   - [ ] Banden stabiel (zelfde P50 binnen afronding)
6. Schakel Run-modus terug naar **Analytisch** (zonder herbereken):
   - [ ] FM-resultaten tonen puntwaarden (geen MC-banden)
   - [ ] Top 10 en LCC tonen analytische cijfers

## Akkoord

| Analist | Datum | GO / NO-GO | Opmerkingen |
|---------|-------|------------|-------------|
| | | | |
