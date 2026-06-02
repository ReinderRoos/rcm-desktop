# KANBAN handoff — slice 55 (meekoppel discovery parent-rollup)

**Status:** niet gestart  
**PRD:** `PRD.md`  
**Slice-map:** `SLICE_MAP.md`

## Doel

Discovery groepeert REV op **parent** van FM-knoop (één trede hoger); scope-filter gebruikt **leaf-dekking**. Unblock slice 54 issues 03+.

## Issues (volgorde)

| # | Issue | Type | Status |
|---|-------|------|--------|
| 01 | `bundling_pbs_id` + discovery rollup | AFK | ⬜ |
| 02 | Scope-filter leaf-dekking | AFK | ⬜ |
| 03 | ADR-0005 amendement | AFK | ⬜ |
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

_(agent/human vult aan tijdens implementatie)_
