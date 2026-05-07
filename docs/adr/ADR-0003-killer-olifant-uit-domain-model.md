# ADR-0003 — Killer/olifant-classificatie verwijderd uit Domain model

## Status
Accepted (supersedes RCM1 `docs/adr/ADR-0001-killer-olifant-taxonomie-ui.md`)

## Datum
2026-05-07

## Context
RCM1 heeft op `PBSResult` twee booleans: `is_unavailability_killer` en
`is_cost_elephant`, gevuld door `engine.classify_results` met drempels uit
`config.py`. RCM1's eigen ADR-0001 plus issues 09 en 10 hebben de UI-labels al
geneutraliseerd (`legacy`/`neutral` mode), maar lieten de classificatie zelf
in het model staan.

Bij de RCM2-start (mei 2026) is besloten dat de classificatie als geheel
**irrelevant is voor interpretatie**: gebruikers leiden de rangordening van
PBS-bijdragen zelf af uit numerieke kolommen (`total_cost_eur`,
`total_downtime_hr`, `unavailability_pct`). Top-X-views in de UI doen dit
sorteer-/filterwerk; een impliciete classificatie aan de domeinkant is
overbodig en risicovol (drempelkeuze leidt tot interpretatiefouten).

## Beslissing
- `is_unavailability_killer` en `is_cost_elephant` worden verwijderd uit
  `rcm_core/models.py::PBSResult` en uit `to_dict()`.
- `unavailability_killer_threshold_pct` en `cost_elephant_threshold_eur`
  vervallen uit `rcm_core/config.py::RCMConfig`.
- `engine.classify_results` vervalt; `run_analytical` retourneert PBS-resultaten
  zonder classificatie.
- `rcm_core.cli` toont geen `[KILLER]`/`[OLIFANT]` flags meer in `_print_summary`.
- Demo-fixtures worden eenmalig gescrubd: drempelwaarden uit `config`-blok
  verwijderd.

## Consequenties
- **Cache-correctheidscontract**: de canonieke serialisatie verandert van vorm,
  dus oude RCM1-cachebestanden mogen niet als geldig worden vertrouwd.
  Implementatie: `CACHE_INPUTS_VERSION = 100` (RCM2 fresh start) in
  `rcm_core/cache.py`.
- UI/Top-X verschuift naar pure numerieke rangordening; presentatieklasse
  beslist zelf welke drempels (indien gewenst) zichtbaar zijn — niet meer in
  het domeinmodel verankerd.
- Tests in RCM1 die `classify_results` valideren zijn niet geporteerd.
- Externe rapportages die op kolomnamen `is_unavailability_killer` /
  `is_cost_elephant` rekenen zullen breken — er is geen externe afnemer
  bekend voor RCM2 en RCM1 blijft afzonderlijk bestaan.

## Verworpen alternatieven
- **A. Labels behouden**: continueert RCM1's eigen ADR-0001 zonder voortgang;
  de productbeslissing was juist te sterk verankerd in het model.
- **B. Alleen UI-labels verwijderen**: laat domeinmodel-fields staan, alleen
  geen tonen. Dat is wat RCM1's `legacy`/`neutral` mode al doet; lost de
  semantische wens niet op.
- **C. Drempels in UI alleen**: kantelen drempels naar UI-config. Mogelijk
  later interessant, niet nodig voor v1 omdat Top-X met sortering dezelfde
  inzichtsfunctie levert.

## Gerelateerd
- Vervangt: RCM1 `docs/adr/ADR-0001-killer-olifant-taxonomie-ui.md`.
- RCM1 issues `09`, `10`, `11` (taxonomie + UI-uitfasering + bugfix).
- Scrub-list in `../rcm/.scratch/rcm2-restart-reference/RCM2_REFERENTIE.md`.
