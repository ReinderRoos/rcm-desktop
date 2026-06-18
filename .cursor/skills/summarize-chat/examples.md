# Example — slice 35 sessie (2026-05-21)

Chat covered: KANBAN read → issue 02 PM spike → `Enabled` semantics fix.

## User-facing summary (good)

> Issue 02 is done. PM effect links now resolve on `(Cause, SubIndex)` regardless of AW `Enabled`; CM fixture goes from 12→54 links, 57→15 warnings. Spike doc and tests updated. Still open: map AW `Enabled=False` to planning overlay on import.

## Issue row (good)

| 02 | PM-semantiek-spike | **done** | `PM_SEMANTICS_SPIKE.md`; CM: 54 PM-links / 15 waarschuwingen; `Enabled` = scenario, niet koppeling |

## Sessie-fix entry (good)

### Enabled filter on PM effect links

- **Symptoom:** 46 PM-waarschuwingen terwijl AW assignments wél PEnable hadden
- **Oorzaak:** `resolve_pm_task_id` skipte `Enabled=False` tasks
- **Fix:** `rcm_core/isograph_pm_import_rules.py` — structurele koppeling los van scenario
- **Test:** `test_cm_fixture_pm_effect_links_resolved`, `test_pm_link_resolves_when_scheduled_task_disabled`

## What to omit

- Full openpyxl install debugging unless it blocks future sessions
- Every intermediate spike draft revision
- Verbatim chat quotes longer than one line
