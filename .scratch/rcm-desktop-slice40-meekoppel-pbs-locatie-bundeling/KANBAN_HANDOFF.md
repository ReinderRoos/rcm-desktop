# Kanban-handoff — slice 40 meekoppel PBS-locatie bundeling

**Status:** tracer-bullet af (issues 01–04 geïmplementeerd)  
**Repo:** `rcm-desktop`  
**Slice-map:** `.scratch/rcm-desktop-slice40-meekoppel-pbs-locatie-bundeling/`  
**ADR:** `docs/adr/ADR-0005-meekoppelen-onderhoud.md` (geamendeerd)  
**Parent:** slice 39 correctie; grill-me 2026-05-23  
**Fixture:** `tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json`

## Probleem (kort)

Slice 39 groepeerde op `element_naam` → megagroepen op Haarlem. Slice 40 groepeert op **`pbs_id`** met boompad + compacte tabel; default anker **laatste**.

## Issues

| # | Titel | Status |
|---|--------|--------|
| 01 | ADR + pad-service + locatie-discovery | done |
| 02 | Preview/apply locatiegroep + legacy weg | done |
| 03 | Werkruimte-tabel + copy | done |
| 04 | Tests + handoff | done |

## Wijzigingen (samenvatting)

- **`pbs_path_label_service.py`:** boompad via `parent_pbs_id`, segment = `bouwdeel_naam` of `pbs_id`.
- **`discover_meekoppel_locations`:** groepering op `pbs_id`; `MeekoppelLocationGroup`.
- **`preview_meekoppel_location` / `apply_meekoppel_location`:** default anker `later`; legacy paar/element-API verwijderd.
- **Werkruimte-tabel:** kolommen Boompad, PBS-id, # REV, Due-bereik, Span Δ.
- **Preview-dialog:** default laatste anker; body met locatie + PBS-id + PM-lijst.

## Tests

```bash
python -m pytest tests/test_pbs_path_label_service.py tests/test_meekoppelkansen_discovery_service.py tests/test_meekoppel_apply_service.py tests/test_desktop_meekoppel_workspace.py -v
```

Regressie (slice 36–38, handmatig na Haarlem):

```bash
python -m pytest tests/test_desktop_results_workspace_window.py tests/test_lcc_presentatie_cache.py -q
```

## Haarlem-checklist (handmatig)

1. Run → LCC → what-if → **meerdere** locatierijen (niet 2 megagroepen op type-naam).
2. Boompad herkenbaar t.o.v. navigatieboom; PBS-id klopt bij selectie in boom.
3. Preview default **laatste**; PM-lijst compleet in dialog.
4. Toepassen → overlay-teller ↑; LCC vernieuwt; alleen REV's op **die** `pbs_id` verschoven.
5. Reset overlay → baseline.
6. Geen regressie LCC-snelheid / handmatige shift (slice 36–38).

---

*Laatste update: 2026-05-23 — TDD implementatie issues 01–04.*
