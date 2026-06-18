# Kosten-diagnose — slice 71 issue 00

**Datum:** 2026-06-05  
**Fixture:** `tests/fixtures/RCMCostdata export_Gaarkeuken.rcm.json`

## Bevinding

| Scenario | `total_cost_eur` | Opmerking |
|----------|------------------|-----------|
| Raw project (403 PM-taken) | **172,3 M** | Zonder `materialize_cm_overlay_project` |
| CM-overlay (168 PM-taken) | **154,4 M** | 235 `aw_disabled_pm_ids` uit AW-import |
| `run_service.run()` default | **154,4 M** | Overlay actief (slice 68 alignment) |

CM-overlay **werkt** in het run-pad: disabled PM's worden gematerialiseerd vóór analyse.

## Verklaring analist-observatie (~60 M → ~160 M)

- **~160 M** komt overeen met overlay-run (~154 M) of raw-run (~172 M) — CM-kosten domineren (~152 M CM vs ~2,6 M PM na overlay).
- **~60 M** past **niet** bij Gaarkeuken engine-totalen op projectniveau. Mogelijke bronnen: ander project (bijv. Haarlem ~23 M), PBS-subscope, of UI vóór slice-68 fix (run zonder overlay-materialisatie).
- Overlay bespaart hier vooral **PM-kosten** (~18 M delta); CM blijft ~152 M.

## Actie slice 71

- UX-wijzigingen (issues 01–08) mogen doorgaan; geen aparte rekenbug in run_service.
- Bij analist-bevestiging dat 60 M op **ander** project/scope slaat: aparte band-test toevoegen.

## Tests

- `tests/test_slice71_cm_overlay_kosten.py`
- `tests/test_slice68_parity_run_alignment.py` (C1-regressie)
