# Effect-semantiek-spike — OHS cause–effect import (slice 69)

**Datum:** 2026-06-05  
**Brondata:** `tests/fixtures/RCMCostdata export_CM.xlsx`  
**Implementatie:** `rcm_core/isograph_pm_import_rules.py` + `isograph_import_service._build_effect_links`  
**Status:** **Leidend** — herziet slice-35 PM-spike waar nodig (§6.3 RF op PM).

---

## 1. Bron van waarheid

| Bron | Rol |
|------|-----|
| **RcmCauseEffectAssignments** | Primaire bron voor `FMEffectLink` en `PMEffectLink` |
| **RcmEffects** | Effect-id / omschrijving |
| **RcmScheduledTasks** | PM-taak-resolutie via `Cause` + `SubIndex` + `Type` |
| **RcmCauses.EffectIds** | Audit/cross-check alleen — **geen** link-creatie |

---

## 2. Afwijking t.o.v. slice-35 PM_SEMANTICS_SPIKE

| Onderwerp | Slice 35 | Slice 69 (besluit) |
|-----------|----------|-------------------|
| RF op PM | Nee — `fractie=1.0` default | **Ja** — `PMEffectLink.fractie = RedundancyFactor` (zelfde als CM) |
| PEnable + IEnable | Eén gecombineerde resolutie | **Aparte scopes** — Planned en Inspection elk eigen link(s) |
| SubIndex mismatch | Geen link + waarschuwing | **Fallback** naar unieke taak in scope + `SubIndex-fallback` waarschuwing |
| Enabled=False | Wel structurele link | Ongewijzigd |

**Motor:** `compute_pm_totals` gebruikt `duration × fractie × executions`; geen engine-wijziging.

---

## 3. Importregels

```
for assignment (cause, effect, sub, RF, C/P/I flags):
  if CEnable:  FMEffectLink(fractie=RF)
  if PEnable:  for each resolved Planned task:  PMEffectLink(pm_id=task.pm_id, fractie=RF)
  if IEnable:  for each resolved Inspection task: PMEffectLink(pm_id=task.pm_id, fractie=RF)
```

### 3.1 PM-resolutie per scope

1. Zoek ScheduledTask: `Cause` + `SubIndex` + `Type` in scope.
2. **Exact één** match → link met **task-SubIndex** in `pm_id` (`{cause}|{task_id}|{task_sub}`).
3. **Geen** match, **exact één** taak in scope op cause → SubIndex-fallback + waarschuwing.
4. **Meerdere** kandidaten → geen link + ambiguous/unresolved waarschuwing.

### 3.2 RF op PM

`pm_effect_fractie(row) = parse_redundancy_factor(RedundancyFactor)` — default 1.0 indien leeg.

---

## 4. Voorbeeld-cause walkthrough

**Cause:** `06H-350.1.1.1.1.1.A.1`

| Effect | RF (CM) | P/I | Assignment SubIndex | Scheduled REV SubIndex |
|--------|---------|-----|-------------------|------------------------|
| VGM - Effect 3 | 0.1 | P+I | 0 | 0 |
| VGM - Effect 2 | 0.9 | P+I | 0 | 0 |
| Schutten 0-20% | 1.0 | P+I | **2** | 0 (fallback) |
| Schutten 81-100% | 0.5 | P+I | 0 | 0 |

Na slice 69: 4 FM-links (ongewijzigd) + PM-links op `…|REV|0` met fracties 0.1/0.9/1.0/0.5 waar P/I enabled.

---

## 5. ADR-0004 aanvulling

Zie `docs/adr/ADR-0004-isograph-excel-import-import-settings.md` — sectie **PM-effect fractie (slice 69)**.
