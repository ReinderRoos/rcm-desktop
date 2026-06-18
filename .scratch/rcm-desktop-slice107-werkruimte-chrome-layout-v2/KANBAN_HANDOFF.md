# Kanban handoff — Slice 107: Werkruimte chrome-layout v2

**PRD:** `.scratch/rcm-desktop-slice107-werkruimte-chrome-layout-v2/PRD.md`  
**ADR:** `docs/adr/ADR-0020-werkruimte-chrome-layout-v2.md`  
**Triage:** issues 01–05 **done** (AFK); issue 06 HILT open  
**Volgorde:** 01 → 02 ∥ 03 → 04 → 05 → 06

## Queue

| # | Tranche | Type | Triage |
|---|---------|------|--------|
| 01 | Layout-shell + navigatierail | AFK | **done** |
| 02 | KPI als Output-view | AFK | **done** |
| 03 | Chrome-footer + TopX | AFK | **done** |
| 04 | LCC footer rechterstack | AFK | **done** |
| 05 | Legacy cleanup + regressie | AFK | **done** |
| 06 | HILT107 | HILT | `ready-for-human` |

## Tests

```bash
pytest tests/test_slice107_*.py tests/test_slice79_view_registry.py tests/test_slice105_chrome_toolbar.py tests/test_desktop_results_workspace_window.py -q
# 37+ passed in slice-107 gate; full regressie batch 116 passed
```

## Volgende stap

HILT107 handcheck: `HILT107_HANDCHECK.md`
