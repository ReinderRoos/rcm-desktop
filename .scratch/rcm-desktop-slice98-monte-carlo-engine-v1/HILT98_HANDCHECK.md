# HILT98 — Handcheck Monte Carlo engine v1

**Issue:** slice 98 issue 12  
**Datum:** 2026-06-16 (hervalidatie na slice 100 unified Start analyse)  
**Status:** GO — completed

## Doel

Visuele QA van MC Run-modus vóór merge: voortgang, seed, annuleren, FM-onzekerheidsbanden, analytische Top 10/LCC ongewijzigd.

## Voorbereiding

1. Start resultatenwerkruimte (`python -m rcm_desktop.main`).
2. Open demo-project (Haarlem of Gaarkeuken PM).
3. **Modelinstellingen:** `monte_carlo_n` = 1000, `monte_carlo_seed` = vast getal (bijv. 42).

## Stappen

1. Run-modus **Monte Carlo** in validatiestrip → **Start analyse**.
   - [x] Voortgang en seed zichtbaar in statusstrip (unified Start analyse, slice 100)
2. Na voltooiing — **FM-resultaten**:
   - [x] P50 in kolom; tooltip toont P10 en P90 (geen P50 in tooltip)
3. **Annuleren:** start opnieuw, klik **Annuleren** halverwege:
   - [x] Status geannuleerd; geen banden in FM-resultaten
4. **Reproduceerbaarheid:** zelfde seed, opnieuw run:
   - [x] Banden stabiel (zelfde P50 binnen afronding)
5. Run-modus **Analytisch** → **Start analyse**:
   - [x] Puntwaarden in FM-resultaten (geen MC-banden)
6. **Top 10 + LCC** analytisch; moduswissel MC → Analytisch zonder run:
   - [x] Analytische cijfers in Top 10/LCC; na moduswissel zonder run blijven analytische waarden zichtbaar

## Notities

- Eerdere sessie (2026-06-13): GO met kanttekening — puntwaarden na analytische run en moduswissel nog niet getest; beide nu OK.
- Dispatch via unified **Start analyse** (slice 100); Run A/B niet meer vereist voor MC.

## Akkoord

| Analist | Datum | GO / NO-GO | Opmerkingen |
|---------|-------|------------|-------------|
| ReinderRoos | 2026-06-13 | GO met kanttekening | MC via Run A/B; tooltip P10/P90 OK; leeg analytisch zonder prior run |
| ReinderRoos | 2026-06-16 | GO | Hervalidatie: Start analyse dispatch, alle checks 1–6 OK incl. analytische puntwaarden + Top10/LCC |
