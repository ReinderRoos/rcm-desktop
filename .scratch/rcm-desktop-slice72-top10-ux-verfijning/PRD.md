# PRD — Slice 72: Top 10 UX-verfijning

**Status:** **goedgekeurd** — GitHub publicatie pending  
**Voorganger:** slice 71 (NB-effectfilter & metric 3-way)  
**Datum:** 2026-06-05

## Probleem

Na slice 71 blijven vijf UX-fricties in de Bijdragen-modus (Top 10):

1. **NB-effectfilter** staat in de toolbar maar klapt niet uit bij klik op het veld.
2. **Component-bron** is overbodig — faalwijze is leidend; inzoomen op component via PBS-boom.
3. **Tabel naast staafdiagram** is redundant.
4. **Staaflabels** tonen altijd aandeel-%, niet de gekozen uren/%-weergave voor NB.
5. **Effectfilter** moet end-to-end de bijdragen-ranking en -waarden beïnvloeden (verificatie).

## Oplossing

Zes tracer-bullet issues (00–05): popup-fix, faalwijze-default, chart-only, display-seam, staaflabels, regressie NB-filter.

## Niet in scope

- Tijdsplot-wijzigingen (slice 71 dekt dit).
- Nieuwe metrics of bronnen.
- Kostendiagnose (slice 71-00).

## Architectuur (improve-codebase-architecture)

- **Display-seam** (`contribution_display_service`): Qt-vrije formattering voor bijdragen-waarden; één plek voor chart-labels en eventuele toekomstige export.
- **Bron-toggle verwijderen**: minder workspace-state en orchestrator-complexiteit.
- **NbEffectFilterCombo**: read-only editable combo + `showPopup` op klik; later eventueel menu-based widget.

## Issues

Zie [issues/INDEX.md](issues/INDEX.md).
