# ADR-0015 — Ernst-dualiteit invoerbevindingen: kruis-entiteit-regels zijn waarschuwingen in het grid, fouten bij run

## Status

Accepted (2026-06-12).

## Datum

2026-06-12

## Context

Invoerbevindingen (zie `CONTEXT.md`) brengen drie validatiebronnen samen in het
entiteiten-grid: de tabulaire editing-pipeline, projectvalidatie
(`validate_project`/`validate_aannamen`) en consistentie-bevindingen (slice 49).
De projectvalidatieregels vallen uiteen in twee groepen:

- **Enkel-rij-regels** — toetsbaar binnen één rij (bijv. `FM_RANDOM_SIGMA_NONZERO`,
  negatieve kosten).
- **Kruis-entiteit-regels** — lezen meerdere entiteiten (bijv. `FM_NMF_REQUIRES_TEST`:
  een NMF-faalwijze vereist een gekoppelde testtaak).

Tijdens het bewerken is een tijdelijk inconsistente tussenstand bij
kruis-entiteit-regels normaal: de analist past eerst de faalwijze aan en daarna
pas de REV-taak. Hard blokkeren in het grid zou die werkvolgorde onmogelijk maken.

## Beslissing

Dezelfde regelcode krijgt bewust **twee ernstniveaus, afhankelijk van waar je
kijkt**:

| Regelgroep | In het entiteiten-grid | Bij run / Validate-knop |
|------------|------------------------|--------------------------|
| Enkel-rij (`validate_project`) | **Fout** — rood, blokkeert opslaan/run | Fout |
| Kruis-entiteit (`validate_project`) | **Waarschuwing** — geel, niet-blokkerend | **Fout** (ongewijzigd hard) |
| `validate_aannamen` | Waarschuwing | Waarschuwing |

Het grid is daarmee een *werkruimte-weergave* van de modelkwaliteit, geen
poortwachter: geel betekent "dit moet nog kloppen vóór een run, maar je mag
verder werken". De run-/Validate-semantiek van `validate_project` verandert
niet.

## Gevolgen

- Een toekomstige lezer ziet dezelfde regelcode met twee severities; dat is
  bedoeld gedrag, geen bug.
- Kruis-entiteit-waarschuwingen in het grid later alsnog blokkerend maken is
  een merkbare gedragsbreuk (gebruikers bouwen gewoontes op rond "geel mag
  blijven staan tijdens het werk") en vereist herziening van dit ADR.
- `CellErrorView` krijgt een `severity`-attribuut (`"error"`/`"warning"`).

## Overwogen alternatieven

| Optie | Waarom niet |
|-------|-------------|
| Alle `validate_project`-regels hard blokkeren in het grid | Maakt normale tussentijdse bewerkstappen (eerst FM, dan REV-taak) onmogelijk |
| Alle `validate_project`-regels als waarschuwing in het grid | Enkel-rij-fouten (negatieve kosten, sigma bij random) zijn binnen de rij direct oplosbaar; uitstellen voegt niets toe |
| Kruis-entiteit-regels ook bij run verzachten tot waarschuwing | Verzwakt het bestaande contract van `validate_project`; een run op een aantoonbaar inconsistent model is onverdedigbaar |
