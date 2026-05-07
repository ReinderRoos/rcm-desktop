# ADR-0002 — PySide6 als UI-framework voor RCM2; PBS-tree React-component uitgefaseerd

## Status
Accepted

## Datum
2026-05-07

## Context
Na ADR-0001 (Python-only UI) is de keuze tussen Python-web (NiceGUI/Reflex/FastUI)
en native desktop (PySide6/Flet/Toga) afgewogen.

## Beslissing
RCM2 v1 wordt gebouwd met **PySide6** (Qt6, LGPL).

## Overwegingen
- Past bij de solitaire/lokale scope uit `RCM_V1_SCOPE_EN_SUCCESCRITERIA.md`.
- Volwassen grid-/tree-widgets (`QTableView`, `QTreeView`,
  `QAbstractItemModel`) sluiten direct aan op de **tabulaire editing-pipeline**.
- Bestaand PyInstaller-pad in RCM1 (`rcm.spec`) is uitbreidbaar naar UI-packaging.
- LGPL-licentie geeft commerciële vrijheid (in tegenstelling tot PyQt6 GPL).

## Consequenties
- Geen herbruik van de React PBS-tree-component (RCM1 issues 12-14): die wordt
  uitgefaseerd. PBS-boom in RCM2 wordt opnieuw gebouwd met `QTreeView` +
  custom `QAbstractItemModel`.
- TDD-discipline op de adapterlaag (Qt-models, run-thread, signal-bridges)
  met `pytest-qt`. Pure UI-rendering wordt niet test-gestuurd ontwikkeld.
- Leerpad ~3-4 weken focus zonder bestaande Qt-ervaring; daarom is de eerste
  milestone afgebakend als tracer-bullet (zie tracer-bullet PRD).

## Verworpen alternatieven
- **NiceGUI / Reflex**: web-stijl Python-UI; werkt loopback maar voelt nog
  steeds als webapp. Reflex compileert naar React/Next.js — half B-keuze.
- **Flet (Flutter)**: krachtige cross-platform desktop, maar minder volwassen
  voor zware tabel-/tree-flows.
- **Toga / BeeWare**: kleiner ecosysteem.

## Gerelateerd
- ADR-0001 (Python-only UI).
- `../rcm/.scratch/rcm2-restart-reference/RCM2_REFERENTIE.md` (keuze 4).
