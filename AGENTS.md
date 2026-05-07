# Agent instructions (rcm-desktop)

Project-specifieke notities voor AI-agents in deze RCM2 desktop-repo.

## Achtergrond

Dit is een fresh copy-and-adapt van de RCM1-kern (`../rcm/`), met een nieuwe
PySide6 desktop-UI. Beslissingen, MoSCoW-mapping en scrub-list staan in
`../rcm/.scratch/rcm2-restart-reference/RCM2_REFERENTIE.md` (bron van waarheid
voor strategische keuzes).

## Vocabulaire

Zie `CONTEXT.md`. Belangrijke termen: **Domain model**, **Editing schema
registry**, **schema-backed FK** vs **project-backed FK**, **Tabulaire
editing-pipeline**, **Globale digest**, **FM-invoerhash**, **Adapter CLI**,
**Adapter Qt**.

## Issue-tracker

Lokale markdown onder `.scratch/<feature>/` met PRD.md + issues/NN.md
(mattpocock-conventie). Triage-labels: `needs-triage`, `needs-info`,
`ready-for-agent`, `ready-for-human`, `wontfix`.

## Architectuurprincipes

- **UI/kern-decoupling als MUST**: `rcm_desktop/views/` mag de kern alleen
  benaderen via `rcm_desktop/adapter/`. Geen directe imports van `rcm_core.*`
  in views, behalve typing-only.
- **TDD op adapterlaag**: alles in `rcm_desktop/adapter/` is test-first met
  `pytest-qt`. Pure UI in `views/` wordt niet test-gestuurd ontwikkeld.
- **Kern blijft puur**: `rcm_core/` heeft geen Qt-imports en geen kennis van UI.
- **Scrub-list is hard contract**: zaken op de scrub-list (zie `CONTEXT.md` en
  RCM2_REFERENTIE) komen niet terug zonder expliciet besluit + ADR.

## Test-seam

Voor de geporteerde kern (CLI/Runflow-equivalenten) blijft de seam: **patch op
`rcm_core.incremental_run as ir`** voor incrementele/cache-gedrag. Adapter-
specifieke mocks blijven binnen `rcm_desktop.adapter.*`.

## Nieuwe code

- Python 3.11+. PySide6 6.6+.
- Bij wijziging van `rcm_core/models.py` of `rcm_core/editing/schemas.py`:
  parity-tests in `tests/test_editing_schemas_parity.py` moeten blijven slagen
  (anders is het een drift en geen werkende wijziging).
- Bij motorwijziging zonder JSON-vormwijziging: verhoog `CACHE_INPUTS_VERSION`
  in `rcm_core/cache.py`.
