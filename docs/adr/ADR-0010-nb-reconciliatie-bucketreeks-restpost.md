# ADR-0010: NB-reconciliatie — bucketreeks-spine + verborgen-NB-restpost

**Status:** accepted
**Date:** 2026-06-11
**Parent:** grill-with-docs-sessie 2026-06-11; slice **73** (NB-scalar reconciliatie); volgt slice 70/71

## Context

De niet-beschikbaarheid (NB) werd op drie plekken verschillend gereduceerd:
Top 10-scalar bij lege filter (`contribution_value_for_fm`), Top 10-scalar bij
gevulde filter (`nb_scalar_for_fm` → `_filtered_nb_scalar`) en de Tijdsplot-curve
(`nb_yearly_series`). Hierdoor kon een **subselectie** van NB-effectklassen een
**hogere** waarde tonen dan de **totale** NB (geobserveerd ~60×: gefilterd gaf het
levensduur-totaal, ongefilterd het jaargemiddelde). Daarnaast sluiten de
effect-specifieke NB-delen per definitie niet aan op het totaal: het totaal bevat
**verborgen NB** (detectievertraging) en PM-uren die niet aan een fysieke
effectklasse toe te rekenen zijn, en RF-fracties kunnen samen >1 zijn.

## Decision

1. **Eén bron-van-waarheid: de NB-bucketreeks (per FM).** Eén interne spine bouwt
   per FM én per `EffectNbFilterSet` de gepresenteerde NB per horizonbucket. Zowel
   `nb_scalar_for_fm` (reductie: levensduur-som / jaargemiddelde / kalenderjaar) als
   `nb_yearly_series` (de reeks zelf) reduceren/presenteren eruit. Top 10 en Tijdsplot
   kunnen daardoor niet meer driften; de scalar is per constructie een reductie van de
   curve.

2. **Verborgen NB als selecteerbare restpost.** De NB-effectfilter krijgt naast de
   echte availability-effectklassen een selecteerbare **Detectie-/verborgen-NB-restpost**.
   De selecteerbare verzameling vormt zo een **echte partitie** van de totale NB:
   leeg = totaal, alles aangevinkt = totaal, elke deelselectie ≤ totaal. De echte
   effectklassen behouden hun definitie (`RF × downtime × failures` + PM-uren); de
   restpost absorbeert detectievertraging (+ niet-toegewezen PM).

3. **RF niet hernormaliseren.** Motor-RF blijft eerlijk; de "geheel ≥ delen"-invariant
   wordt geborgd door de partitie + een veiligheids-clamp (getoonde filterwaarde
   ≤ totaal) voor zeldzame RF-overlap (Σ RF > 1).

4. **PM in het availability-pad telt in uren** (gedegradeerde uren), niet als
   telling. *Implementatie-noot (2026-06-11):* uit `engine.py` blijkt dat
   `pm_effect_bijdragen` al in uren is (`duration.to_hours() × RF × executions`);
   de oorspronkelijke code (`pm_val = pm_raw`) was dus al eenheids-correct. De in
   slice 73 verwachte "PM-eenheidsfix" bleek een misdiagnose en is niet nodig —
   alleen de CM-telling vereist `× downtime` (per FM, zie decision over
   `aggregate`). Het contract "PM in uren" blijft staan; er was geen codewijziging
   voor nodig.

## Considered Options

- **Pro-rata verdeling van verborgen NB over de availability-klassen** (Σdelen = totaal
  exact, alles-aangevinkt = totaal). Verworpen: de per-effect getallen wijken dan af
  van hun fysieke definitie in `CONTEXT.md`; de restpost-aanpak houdt de delen eerlijk
  én levert dezelfde optel-garantie.
- **Verborgen NB als niet-selecteerbare restpost.** Verworpen: dan blijft "alle
  effectklassen aangevinkt" kleiner dan het totaal, wat de analist verwart.
- **RF stilletjes normaliseren naar som 1 per FM.** Verworpen: verbergt een echt
  modelleerprobleem in de invoer.

## Consequences

- `EffectNbFilterSet` / de effectfilter-UI kennen een speciale restpost-post naast de
  effectklasse-IDs; consumenten (Top 10, Tijdsplot) behandelen die als onderdeel van
  de partitie.
- Een afwijking van dit contract (bv. opnieuw pro-rata willen) vereist heroverweging
  van deze ADR.
- Domeintermen vastgelegd in `CONTEXT.md`: **NB-bucketreeks (per FM)**,
  **Detectie-/verborgen-NB-restpost**.

## References

- `rcm_core/effect_impact_service.py` (`nb_scalar_for_fm`, `nb_yearly_series`, spine)
- `rcm_desktop/adapter/contribution_chart_service.py` (`_effect_presentation`)
- `rcm_desktop/adapter/contribution_horizon_value_service.py`
- `rcm_desktop/adapter/tijdsplot_curve_service.py`
- `.scratch/rcm-desktop-slice73-nb-scalar-reconciliatie/PRD.md`
