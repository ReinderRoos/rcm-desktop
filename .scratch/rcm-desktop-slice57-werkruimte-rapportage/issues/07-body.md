## Parent

https://github.com/ReinderRoos/rcm-desktop/issues/9

## What to build

Sluit slice 57 af met regressie-gates: werkruimte-UX zonder rapport ongewijzigd; smoke voor rapportknop enabled/disabled, dialoog-preview bij compare; geen rapportknop in ValidateWindow. Documenteer PDF-prerequisite (LibreOffice) voor ontwikkelaars/gebruikers.

## Acceptance criteria

- [ ] Single-run en compare workspace-UX ongewijzigd wanneer geen rapport wordt gegenereerd
- [ ] Smoke: knop disabled zonder run; enabled met done-run; preview in dialoog
- [ ] Geen ValidateWindow-rapportentrypoint in v1
- [ ] README/dev-setup vermeldt PDF-converter prerequisite
- [ ] Dedicated slice-57 smoke of uitbreiding bestaand workspace-smoke patroon

## Blocked by

https://github.com/ReinderRoos/rcm-desktop/issues/15
