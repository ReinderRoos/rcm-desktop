# PM-semantiek-spike — PEnable / IEnable / CEnable (issue 02)

**Datum:** 2026-05-21  
**Brondata:** `tests/fixtures/RCMCostdata export_CM.xlsx` (intern gevuld; 228 assignments, 403 scheduled tasks)  
**Implementatie:** `rcm_core/isograph_pm_import_rules.py` + `isograph_import_service._build_effect_links`  
**Status:** **Afgerond** — importregels vastgelegd en gevalideerd op CM-fixture.

---

## 1. AW-semantiek (RcmCauseEffectAssignments)

Elke rij koppelt één **Cause** (faalwijze) aan één **Effect** (effectklasse) met drie onafhankelijke enable-vlaggen en een **SubIndex**:

| Kolom | Betekenis in AW | RCM2-doel |
|-------|-----------------|-----------|
| **CEnable** | Effect actief bij **correctief falen** (CM) | `FMEffectLink` wanneer `True` |
| **PEnable** | Effect actief tijdens **gepland onderhoud** (Planned/REV/WET/…) | `PMEffectLink` → ScheduledTask met `Type` ∈ planned-scope |
| **IEnable** | Effect actief tijdens **inspectie** | `PMEffectLink` → ScheduledTask met `Type` ∈ inspection-scope |
| **RedundancyFactor** | P(gevolg \| falen) — **alleen CM-conditional** | `FMEffectLink.fractie` |
| **SubIndex** | Join-sleutel naar rij in `RcmScheduledTasks` (zelfde `Cause` + `SubIndex`) | Bepaalt welke PM-taak |

**Observatie CM-fixture** — vlagcombinaties (228 rijen):

| CEnable | PEnable | IEnable | Aantal |
|---------|---------|---------|--------|
| True | False | False | 159 |
| True | True | True | 42 |
| True | True | False | 23 |
| False | True | False | 3 |
| False | True | True | 1 |

Geen rijen met alleen `IEnable=True` (zonder PEnable) in dit bestand.

---

## 2. RCM2-model (FM vs PM gescheiden)

- **FMEffectLink:** degradatie/beschikbaarheid **bij falen** → `duration × RF × expected_failures`.
- **PMEffectLink:** degradatie **tijdens PM-uitvoering** → `task.duration × fractie × executions` (zie `engine.compute_pm_totals`).

Daarom:

- **RF hoort niet op PM-links.** PM-fractie = welk deel van de **taakduur** het systeemgevolg meeneemt (default **1.0** = volledige taakduur).
- FM- en PM-effecten blijven **aparte dictionaries** (`fm_effect_links` / `pm_effect_links`), conform grill-me.

---

## 3. Importregels (besluit)

Geïmplementeerd in `isograph_pm_import_rules.py`.

### 3.1 FM-effectlink

```
CEnable truthy  →  FMEffectLink(fm_id=Cause, klasse_id=Effect, fractie=RedundancyFactor)
```

Default RF = 1.0 als leeg.

### 3.2 PM-effectlink (structureel; `Enabled` ≠ koppeling)

```
(PEnable OR IEnable) truthy
AND exactly one ScheduledTask where:
  Cause = assignment.Cause
  SubIndex = assignment.SubIndex
  AND (
    (PEnable AND Type ∈ {Planned, PM, REV, WET, SVO, TST})
    OR (IEnable AND Type ∈ {Inspection, IN, Inspectie})
  )
→  PMEffectLink(pm_id="{Cause}|{TaskId}|{SubIndex}", klasse_id=Effect, fractie=1.0)
```

**`Enabled` op ScheduledTask:** scenario-vlag (taak draait wel/niet in dit AW-scenario), **niet** gebruikt bij link-resolutie. Koppeling cause→taak→effect is structureel. Uitvoering in RCM2: planning-overlay (`disabled_pm_ids`) — apart besluit; AW `Enabled` wordt bij import nog niet automatisch gemapt.

**Bewuste keuzes:**

| Situatie | Gedrag |
|----------|--------|
| Geen PEnable/IEnable | Geen PM-link; geen waarschuwing |
| Meerdere matching tasks (zelfde Cause+SubIndex, verschillende task_id) | **Geen** PM-link + waarschuwing (ambiguous) |
| SubIndex ontbreekt in ScheduledTasks | **Geen** PM-link + waarschuwing |
| Task op SubIndex, `Enabled=False` | **Wel** PM-link (structureel) |
| PEnable én IEnable beide True | Beide scopes doorzoeken; link alleen bij **uniek** task_id |
| RF op assignment | **Niet** mappen naar PM-fractie |

### 3.3 Audit / unresolved

Rijen met PEnable/IEnable zonder resolvable task → ruwe vlaggen in `import_settings.isograph_assignments` + importwaarschuwing (`pm_import_warning_unresolved`).

---

## 4. Validatie CM-fixture

Import: `build_from_workbook(CM, modeljaar=2026)`

| Metriek | Waarde |
|---------|--------|
| FM effect links | 224 |
| PM effect links | **54** |
| PM tasks | 403 |
| PM-waarschuwingen (unresolved) | 15 |

**Assignments met PEnable/IEnable:** 69 → **54 resolved**, **15 unresolved**.

| Reden unresolved | Aantal |
|------------------|--------|
| Geen ScheduledTask op SubIndex | 7 |
| PEnable-only, geen Planned-task op SubIndex | 8 |

**Vlagpatroon resolved vs unresolved (na fix Enabled):**

| PEnable | IEnable | Resolved | Unresolved |
|---------|---------|----------|------------|
| True | True | 43 | 0 |
| True | False | 11 | 26 |

**Let op:** `Gaarkeuken.rcm.json` is met oudere import (12 links) opgeslagen; herimport geeft 54 links.

---

## 5. Voorbeelden

### Resolved (Inspection, beide vlaggen True)

```
Cause: 06H-350.2.2.1.1.A.1  SubIndex: 1  P+I: True/True
→ Task IN-WET (Inspection, Enabled) → PMEffectLink → Schutten 81-100% functieverlies
```

### Resolved (disabled task — structurele koppeling blijft)

```
Cause: 06H-350.1.1.1.5.1.A.1  SubIndex: 0  P+I: True/True
→ ScheduledTask REV (Planned, Enabled=False) → PMEffectLink (koppeling OK; uitvoering = overlay)
```

### Unresolved (SubIndex ontbreekt)

```
Cause: 06H-350.1.1.1.9.1.A.1  SubIndex: 1  P-only
→ geen ScheduledTask op SubIndex 1 → waarschuwing
```

### FM-only (CM)

```
CEnable=True, PEnable=False, IEnable=False, RF=0.49
→ FMEffectLink fractie=0.49, geen PM-link
```

---

## 6. Open punten (niet blokkerend v1)

1. **P-only zonder Planned-task op SubIndex** — assignment wijst naar inspectie-slot of ontbrekende rij; 26 unresolved in CM (datakwaliteit in AW).
2. **AW `Enabled` → RCM2 overlay** — nog niet automatisch bij import; baseline-run neemt disabled AW-taken nog wél mee in kosten (aparte slice/ADR).
3. **PM-fractie ≠ 1.0** — AW heeft geen direct equivalent; later alleen via expliciet veld, niet via RF.
4. **I-only assignments** — regels ondersteunen het; geen voorbeelden in CM-fixture.

---

## 7. Besluit issue 02

| Vraag | Antwoord |
|-------|----------|
| Wanneer `PMEffectLink` importeren? | §3.2 — uniek resolvable ScheduledTask via SubIndex; **`Enabled` irrelevant** |
| RF → PM? | **Nee** |
| Spike gate fase 0? | **Ja, afgerond** op CM-fixture |
| Triage | **done** |

Geen apart follow-up issue voor importregels — regels staan in `isograph_pm_import_rules.py` en worden getest via `tests/test_isograph_pm_import_rules.py` + CM-importtest.
