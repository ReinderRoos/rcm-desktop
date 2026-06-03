# RCM2 desktop

RCM2 als native desktop-app (PySide6/Qt6) op een geporteerde RCM1-kern.

Status: **scaffolding** — tracer-bullet wordt nu opgepakt; zie
`.scratch/rcm-desktop-tracer-bullet/` voor werkpakket en issues.

Achtergrond, scope, beslissingen en MoSCoW-mapping staan in
`../rcm/.scratch/rcm2-restart-reference/RCM2_REFERENTIE.md`.

## Quickstart

```powershell
# vanuit rcm-desktop/
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]

# rookproef op de geporteerde kern (zonder Qt):
python -m rcm_core.cli validate tests\fixtures\awzi_haarlem_waarderpolder_demo.rcm.json
python -m rcm_core.cli run     tests\fixtures\awzi_haarlem_waarderpolder_demo.rcm.json --full

# tests:
python -m pytest

# optioneel: PDF-export uit werkruimte-rapport vereist LibreOffice (soffice op PATH,
# standaard Windows-installatie onder Program Files, of env LIBREOFFICE_PROGRAM)

# Qt-desktop:
python -m rcm_desktop.main
```

Na starten: projectbestand kiezen en **Project inladen** gebruiken (bestand inlezen en domain model valideren).

## Layout

```
rcm-desktop/
  rcm_core/        gepoorte analytische kern + editing-pipeline (scrub-list toegepast)
    cli.py         rookproef-CLI (validate / impact / run / fit / bibliotheek-*)
    editing/       tabulaire editing-pipeline
  rcm_desktop/     PySide6 GUI
    adapter/       Qt-models, run-thread, signal-bridges (TDD verplicht)
    views/         Qt-views (manueel getest)
    main.py
  tests/           gepoorte pytest-suite + nieuwe Qt-adapter-tests
    fixtures/awzi_haarlem_waarderpolder_demo.rcm.json
  docs/adr/        architectuurbeslissingen
  .scratch/        feature-PRD's en issues (mattpocock-conventie)
  CONTEXT.md       domeinvocabulaire
  AGENTS.md        agent-conventies voor deze repo
  pyproject.toml
```

## LTAP tijdgrafiek (PM)

De validate-window bevat een LTAP-paneel voor PM-planning met what-if bundeling:

- **Tijdas als staafdiagram** per lifecycle-jaar met twee reeksen: `baseline` en `what-if`.
- **Klik op een jaar** filtert de detailtabel op dat jaar.
- Detailtabel toont de geplande werkzaamheden (what-if), inclusief uitvoeringen, kosten en downtime.
- Boven de detailtabel staat een compacte jaarsamenvatting: `baseline | what-if | Δ`.
- **Toon alle jaren** heft het jaarfilter op en zet de tabel terug naar totaaloverzicht.
- Zonder `QtCharts` blijft LTAP bruikbaar via de lijstselectie + detailtabel (fallback).

## Wat is bewust niet meegeporteerd

Zie scrub-list in `RCM2_REFERENTIE.md`. Hoofdpunten:

- **Killer/olifant-classificatie** (`is_unavailability_killer`, `is_cost_elephant`,
  `classify_results`, drempelwaarden in config) — gebruiker leidt rangordening
  zelf af uit numerieke bijdragen.
- **Streamlit-shell**, runflow-contract en alle Streamlit-UI.
- **Excel import/export**, Monte Carlo (`simulation`), LTAP-light, meekoppelkansen —
  buiten scope tracer-bullet; later eventueel terug.
