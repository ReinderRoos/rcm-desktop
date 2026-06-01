# Meekoppel UX v2 — designbesluiten (grill-me fase 0–3)

**Status:** Accepted (2026-06-01).  
**Scope:** Meekoppelkansen-paneel, resultatenwerkruimte LCC + what-if (ADR-0005, slice 40+).

## Fase 0 — North star

| # | Besluit |
|---|---------|
| 1 | Succescriteria: begrip ~30 s **en** foutloze bundel-flow met verwacht LCC-effect (Haarlem). |
| 2 | Happy path: **Preview → Toepassen**; geen apply zonder geziene verschuivingen. |
| 3 | Anker: **vroegste / laatste** in paneel; default **laatste**; geen dialoog bij preview. |
| 4 | Bundel v1: alle REV's op één PBS-locatie naar hetzelfde doel-due-jaar. |
| 5 | Boom ↔ tabel: tabel **gefilterd** op geselecteerde PBS-subboom (`scope_id`). |
| 6 | Rij: boompad + korte REV-samenvatting + due-bereik; `pbs_id` secundair. |
| 7 | Taal: **due-jaren primair**; kalenderjaar in preview/tooltip via `modeljaar + due`. |
| 8 | Apply: enabled **na preview** voor huidige rij+anker; tot rijwissel, ankerwissel of reset what-if. |

## Fase 1 — Taal & mentaal model

| # | Besluit |
|---|---------|
| 1.1 | Kolom due-bereik → **Eerste uitvoering (jaren)**. |
| 1.2 | Preview-regels: **`taak_omschrijving`**, fallback `pm_id`. |
| 1.3 | Kalenderjaar **in preview-body** per regel (`≈ kalender A → B`). |
| 1.4 | Span-kolom → **Verschil (jaren)**. |

## Fase 2 — Tabel & selectie

| # | Besluit |
|---|---------|
| 2.1 | REV-overzicht via **tooltip** op boompad (omschrijving + jaar). |
| 2.2 | **Geen PBS-id-kolom**; id in tooltip + preview-footnote. |
| 2.3 | Filter: locaties **onder** `scope_id` (subtree, zelfde als `result_filter_service`). |
| 2.4 | Lege filter: **"Geen meekoppelkansen in de geselecteerde boomtak."** |

## Fase 3 — Bundel-flow

| # | Besluit |
|---|---------|
| 3.1 | Anker: **radio's in toolbar** (vóór Preview/Toepassen). |
| 3.2 | Preview: **QMessageBox** met verschuivingslijst (geen anker-dialoog). |
| 3.3 | Anker wisselen opzelfde rij → Apply uit tot nieuwe preview. |
| 3.4 | Geen extra apply-bevestiging. |

## Implementatie-slices

- **A:** `meekoppel_display_service`, `messages`, preview-formattering
- **B:** tabelmodel, scope-filter in `meekoppel_panel_service`
- **C:** toolbar radio's, apply-gating, view wiring, tests

## Testplan

```powershell
python -m pytest tests/test_meekoppel_panel_service.py tests/test_meekoppelkansen_discovery_service.py tests/test_meekoppel_apply_service.py tests/test_desktop_meekoppel_workspace.py -q
```

+ Haarlem handcheck (slice 40 checklist, 6 punten).
