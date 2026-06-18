# Kanban-handoff — slice 104 FM single-run presentatie

**Datum:** 2026-06-16  
**Status:** ready-for-human (re-HILT104) — editor-blockers AFK afgerond  
**Bron:** AFK-batch editor-blockers 2026-06-17

## Queue

| # | Issue | Type | Triage | Blocked by |
|---|-------|------|--------|------------|
| 01 | Adapter: compact FM-tabel + metric-sync | AFK | **done** | — |
| 02 | UI: tabel/diagram-toggle single-run FM | AFK | **done** | 01 |
| 03 | FM-editor: effecten + preventief direct bewerkbaar | AFK | **done** | — |
| 04 | Top 10 verwijderen + default modus FM | AFK | **done** | 01, 02 |
| 05 | HILT104 handcheck | HITL | ready-for-human | — |
| 06 | FM-editor dubbelklik in scenariovergelijking | AFK | **done** | — |

## AFK-batch voortgang (editor-blockers)

| Issue | Fix | Tests |
|-------|-----|-------|
| 03 | Effecten/Preventief tabs in `QScrollArea`; tabel-stretch + scroll-buttons | `test_slice104_fm_editor_tabs.py` — 5 passed |
| 06 | Dubbelklik compare-kolommen → `_open_fm_editor` | `test_slice104_fm_compare_editor.py` — 2 passed |

## Volgende stap

```text
/hilt 104
```

Re-check pad C (editor tabs + compare-dubbelklik). Checklist: `HILT104_HANDCHECK.md`

## Relatie slice 103

- **Issue 06** (FM compare geen verschil) blijft `needs-triage` — HILT103 B4 blocker
- HILT103 checks A3/B2 (Top 10) overslaan; vervangen door HILT104

## Definition of done

Issues 01–04 merged + HILT104 GO + regressie groen
