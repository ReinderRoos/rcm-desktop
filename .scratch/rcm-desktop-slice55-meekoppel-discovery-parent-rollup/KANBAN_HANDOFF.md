# KANBAN handoff — slice 55 (meekoppel discovery parent-rollup)

**Status:** done (issues 01–03 af; issue 04 HITL handcheck open)  
**PRD:** `PRD.md`  
**Slice-map:** `SLICE_MAP.md`

## Doel

Discovery groepeert REV op **parent** van FM-knoop (één trede hoger); scope-filter gebruikt **leaf-dekking**. Unblock slice 54 issues 03+.

## Issues (volgorde)

| # | Issue | Type | Status |
|---|-------|------|--------|
| 01 | `bundling_pbs_id` + discovery rollup | AFK | **done** |
| 02 | Scope-filter leaf-dekking | AFK | **done** |
| 03 | ADR-0005 amendement | AFK | **done** |
| 04 | Haarlem-handcheck + GO | HITL | ⬜ |

## Haarlem-handcheck (template — invullen bij issue 04)

**Fixture:** `tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json`  
**Datum:** _  
**Uitvoerder:** _

### Stappen

1. Open project in resultatenwerkruimte, modus **Tijdsplot (LCC)**.
2. Zet **what-if planning** aan; open paneel **Meekoppelkansen**.
3. Selecteer in PBS-boom een **realistische subselectie** (meerdere children onder gemeenschappelijke parent — geen root-only).
4. Noteer **selectiesamenvatting** (aantal REV) en aantal **locatierijen** bij tijdsvenster **2**.
5. Verhoog venster naar **5**; noteer verschil.
6. Kies één locatierij → **Preview** → controleer dat alle REV van de parent-groep in de lijst staan (leaf-traceerbaar).
7. Optioneel: **Toepassen** op één rij; controleer LCC/overlay-effect.

### Verwachting (post-rollup)

- [ ] Meer locatierijen dan pre-rollup bij dezelfde PBS-selectie en venster 2, **of** expliciete verklaring (bijv. span > venster op alle parents).
- [ ] Geen mismatch: samenvatting toont REV’s maar tabel permanent leeg terwijl sibling-leaves onder parent binnen venster zitten.

### Edge cases / notities

- Orphan `parent_pbs_id`: _
- Zeer brede parent (veel REV in één rij): _
- Overig: _

### Uitkomst

- [ ] **GO** — slice 54 issues 03+ mogen starten  
- [ ] **NO-GO** — reden: _

## Sessienotities

- Issues 01–02 waren al geïmplementeerd; deze sessie: ADR-amendement, gate tests (`test_slice55_discovery_rollup_gate.py`), panel multi-select tests.
- Slice 54 issue 05 gestart: live doeljaar op checkbox-selectie (`recompute_task_rows_for_selection`).

## Testcommando

```powershell
python -m pytest tests/test_slice55_discovery_rollup_gate.py tests/test_meekoppelkansen_discovery_service.py tests/test_meekoppel_panel_service.py tests/test_meekoppel_preview_selection_service.py -q
```
