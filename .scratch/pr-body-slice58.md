## Summary

- **Slice 57 — rapportage:** knop *Genereer rapport* opent een dialoog en levert een gestandaardiseerd Word-rapport (optioneel PDF via LibreOffice) met KPI's, top-10, PBS-bijdragen en tijdsplots per functie, voor single-run en A/B-vergelijking.
- **Slice 58 — AFK-seams:** `assess_report_workspace`, `resolve_project_file_path` en geconsolideerde `SPLIT_*`-constanten als Qt-vrije adapters; fix voor het geval dat alleen `path_input` is ingevuld (geen `session.path`).
- **Slice 56 — A/B-vergelijking:** compare-slots, planning runs en werkruimte-UI (ADR-0007) als basis voor rapportbronkeuze.

De branch bevat ook eerdere werkruimte/meekoppel-commits waar deze features op voortbouwen.

## Test plan

- [ ] Project openen, run afronden, **Genereer rapport** → dialoog, DOCX export
- [ ] Zelfde met projectpad alleen in padveld (zonder opgeslagen session.path)
- [ ] A/B-slots vullen → rapport met vergelijking
- [ ] PDF export (LibreOffice/`soffice` geïnstalleerd — zie README)
- [ ] `python -m pytest tests/test_report_*.py tests/test_slice57_workspace_report_smoke.py tests/test_slice58_*.py tests/test_project_path_resolution_service.py tests/test_architecture_deepening.py -q`
