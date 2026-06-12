## Parent

https://github.com/ReinderRoos/rcm-desktop/issues/9

## What to build

Eerste tracer voor werkruimte-rapportage: een Qt-vrije content-pipeline levert een immutable rapportmodel (voorblad + KPI-pagina) uit project en één geldige motorrun, schrijft een bewerkbaar Word-document, en is bereikbaar vanuit de resultatenwerkruimte.

Introduceer rapporttypes (`ReportDocument`, `ReportOptions`), eligibility (kan genereren zonder `done`-run?), materialisatie single-run (hergebruik bestaande KPI-builder, vaste projectbrede scope, geen UI-filters), en docx-writer (`python-docx`, dev-setup documenteren). Toolbar-knop **Rapport genereren…** is disabled zonder geldige run; compacte dialoog met alleen outputpad (default `{projectmap}/rapporten/{naam}_{datum}.docx`). Synchrone generatie is acceptabel in deze slice. Na succes opent het OS het `.docx`.

Voorblad: projectnaam/modelleur indien beschikbaar (slice 52), anders bestandsnaam-fallback, datum, scenario-context single-run. KPI-pagina: vier bestaande KPI-rijen + LCC-periode/modeljaar als context.

## Acceptance criteria

- [ ] `ReportEligibilityService` levert `can_generate` + reden; zonder `done`-run geen generatie
- [ ] `ReportMaterializationService` single-run: cover + KPI-secties in `ReportDocument`
- [ ] `ReportDocxWriter` schrijft parseerbaar `.docx` met koppen en KPI-tabel
- [ ] Toolbar **Rapport genereren…** in resultatenwerkruimte; knop disabled zonder eligible run
- [ ] Minimale dialoog: alleen padkeuze met verstandig default
- [ ] Na succes wordt Word geopend via OS
- [ ] Unit-tests: eligibility, materialisatie-sectievolgorde/golden op `ReportDocument`, docx-smoke
- [ ] `python-docx` dependency en korte dev-setup-notitie

## Blocked by

None - can start immediately.
