# Kanban-handoff — slice 103 MC-presentatie afronding

**Datum:** 2026-06-16  
**Status:** NO-GO HILT103 — FM compare blocker (B4); issue 06 triage nodig  
**Grill:** `/grill-with-docs` slice 103 — afgerond

## Queue

| # | Issue | Type | Triage | Blocked by |
|---|-------|------|--------|------------|
| 01 | ADR-0018 v1.3 + CONTEXT glossary | AFK | done | — |
| 02 | HILT103 gecombineerde handcheck | HITL | ready-for-human | — |
| 03 | MC LCC/NB-jaarcurves (single-run + scenario compare) | AFK | needs-triage | 02 (pad A/B) |
| 04 | Mixed compare LCC-slot zonder analytical session | AFK | needs-triage | 02 (pad C) |
| 05 | RF-kolom align (conditional) | AFK | needs-triage | 02 (D1) |
| 06 | FM compare geen verschil na scenario-2 wijziging | AFK | needs-triage | 02 (B4) |

## Start nu

```text
/hilt 103
```

## Grill-besluiten (samenvatting)

- HILT103 gecombineerd (HILT100 + HILT101)
- Fixes alleen voor bevestigde blockers; adapter-only
- Lifecycle MC ≠ analytisch punt: documenteren + accepteren
- RF-kolom: conditional
- Out of scope: MC fase 2, ValidateWindow, core motor

## Definition of done

HILT103 GO + bevestigde blocker-fixes (issues 03–05) + docs-poort (issue 01)

## Batch-voortgang (AFK-batch)

**Gestart:** 2026-06-16  
**Laatste update:** 2026-06-16

### Afgerond (HILT103 tussentijdse feedback)
| Issue | Outcome | Tests |
|-------|---------|-------|
| — | FM-detail: horizon/jaar-knoppen zichtbaar (`workspace_toolbar_sync`) | `test_slice103_fm_detail_ui` |
| — | FM-detail: dubbelklik elke kolom opent editor | `test_slice103_fm_detail_ui` |

### Afgerond
| Issue | Outcome | Tests |
|-------|---------|-------|
| 01 | ADR-0018 v1.3 + CONTEXT glossary | — |

### Bezig
- —

### Nog in queue
- Geen `ready-for-agent` items in repo (actieve slices 98–103)

### Blockers
- Issue 02 (HILT103) blokkeert issues 03–05 (`needs-triage` + `Blocked by` 02)
- Issues 03–04: regressietests al groen (10 passed slice100/101 MC-presentatie) — visuele HILT103 bevestiging vereist vóór triage naar `ready-for-agent` of `wontfix`

### Follow-up (slice 104)
Analist-wensen uit HILT103 (tabel/diagram single-run, Top 10 weg, FM-editor tabs)
→ `.scratch/rcm-desktop-slice104-fm-single-run-presentatie/`
- HILT103 checks **A3** en **B2** (Top 10) overslaan; vervangen door HILT104
