# ADR-0016: Vergelijkingsbeleid (twee projectbestanden, balanced split)

**Status:** accepted  
**Date:** 2026-06-13  
**Parent:** slice 95 PRD — strategische roadmap juni 2026

## Context

Reliability-analisten moeten twee willekeurige `.rcm.json`-bestanden (baseline A,
scenario B) ad hoc kunnen vergelijken zonder portfolio-merge. ADR-0007 regelt
A/B op **één project** (runs/scenario's); fase B extend naar **twee projecten**.
Uniformeren en automatische merge op lage drempel zijn expliciet uitgesteld.

## Decision

- **Entry:** twee ad hoc projectpaden (A en B); geen portfolio vereist.
- **Canoniek pad:** `LoadModel(A) + LoadModel(B) → AlignFailureModes →
  DifferenceSet → ComparePresentation` (Qt-vrij in adapter use-cases).
- **Balanced split per FM:** invoerparameters én resultaten even zichtbaar per
  gekoppeld FM-paar — geen aparte "alleen params"-modus als default.
- **Geen auto-uniformeren in v1:** detecteren en visualiseren only; uniformeren
  volgt fase C (`NormalizationProposal → UserReview → Patch → AuditTrail`).
- **Vergelijkingswerkruimte** is een aparte workflow boven hetzelfde
  faalwijze-/projectmodel; de dagelijkse enkel-model werkruimte blijft het hart.

## Consequences

- Compare-logica blijft Qt-vrij en unit-testbaar op adapter-niveau.
- ADR-0006/0007 blijven geldig; workspace dual-project is aanvulling, geen
  vervanging van legacy ValidateWindow compare.
- UI voor vergelijkingswerkruimte vereist HILT vóór merge (twee klantprojecten).
