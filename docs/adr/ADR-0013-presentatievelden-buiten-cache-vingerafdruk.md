# ADR-0013: Presentatievelden buiten de cache-vingerafdruk

**Status:** accepted  
**Datum:** 2026-06-11  
**Slice:** 86 (PBS-volgorde)

## Context

Sommige velden op het domain model beïnvloeden alleen **presentatie** (volgorde in de UI,
rapportage, boom) en niet de analytische motor. Als zulke velden in de globale digest of
de FM-invoerhash zitten, levert elke herordening een volledige cache-invalidatie en
her-run — terwijl rekenkundig niets verandert.

## Besluit

**Presentatievelden** worden wel opgeslagen in `to_dict()` / `.rcm.json`, maar expliciet
**uitgesloten** van:

- `compute_global_digest`
- `fm_analytical_inputs_dict` / `compute_fm_hash`

### Criterium: wanneer is een veld “presentatie”?

Een veld is presentatie als wijziging ervan **geen** rekenresultaat (FM-resultaten,
aggregaten, cache-output) mag veranderen. Typisch: sorteer-/weergavevolgorde, UI-metadata,
rapportage-labels.

Rekenvelden (MTTF, downtime, koppelingen, multipliciteit, …) blijven altijd in de
vingerafdruk.

### Testpatroon: vingerafdruk-stabiliteit

Voor elk nieuw presentatieveld is een test verplicht:

1. Alleen dat veld wijzigen → globale digest **en** FM-hash **ongewijzigd**.
2. Een bekend rekenveld wijzigen → digest **wel** gewijzigd (controle dat uitsluiting niet
   te breed is).

Zie `tests/test_slice86_pbs_volgorde.py`.

## Eerste toepassing: `PBSItem.volgorde`

Sibling-volgorde in de PBS-boom (`volgorde: int`, default `0`). Migratie: ontbrekend veld
bij inlezen → volgorde = lees-/importpositie binnen het niveau.

## Gevolgen

- Herordenen markeert het project **dirty** (opslaan nodig) maar triggert **geen** her-run.
- Parity-tests (`models.py` + `editing/schemas.py`) blijven leidend voor schema-drift.
- Geen `CACHE_INPUTS_VERSION`-bump (geen wijziging aan reken-JSON-vorm in de motor).

## Alternatieven overwogen

- Volgorde impliciet houden (dict-volgorde): niet stabiel genoeg over round-trips.
- Volgorde in digest opnemen: bestraft elke UI-herordening met volledige recomputatie.
