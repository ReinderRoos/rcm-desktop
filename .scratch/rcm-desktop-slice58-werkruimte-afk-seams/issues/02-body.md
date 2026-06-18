## Parent

https://github.com/ReinderRoos/rcm-desktop/issues/17

## What to build

Tracer voor slice 58 (stap 2): Qt-vrije projectpad-resolutie zodat de resultatenwerkruimte geen pad-beleid dupliceert. `resolve_project_file_path` met prioriteit `session.path` → niet-lege `path_text` → geen pad; frozen `ResolvedProjectPath` met optionele helpers voor cache- en rapport-defaultpaden.

View: verwijder `_project_file_path`; rapportflow gebruikt adapter. Bij geen pad: `ERROR_EMPTY_PATH` via `QMessageBox` (geen stille return). Rapport genereren werkt wanneer alleen het pad-UI-veld gevuld is en `ProjectSession.path` leeg is (permanente fix van productie-bug 2026-06-03). Optioneel smal: minstens één extra caller op hetzelfde resolved object als de diff klein blijft. `AppState._sync_project_session` ongewijzigd.

Tabeltests voor pad-edge cases; pytest-qt smoke: rapport-dialoog opent / flow start met alleen `path_input` gevuld. Geen nieuwe product-UI.

## Acceptance criteria

- [ ] `resolve_project_file_path` en `ResolvedProjectPath` in adapter; prioriteit session → path_text → None
- [ ] Resultatenwerkruimte gebruikt adapter; `_project_file_path` verwijderd
- [ ] Rapport zonder pad toont `ERROR_EMPTY_PATH`; geen stille early exit
- [ ] Rapport werkt met pad alleen in UI-veld (`session.path` None)
- [ ] Unit-tests: session.path / path_text / beide leeg
- [ ] pytest-qt smoke voor path_input-only pad (slice 58)
- [ ] `python -m pytest tests/test_report_*.py tests/test_slice57_*.py tests/test_slice58_*.py -q` groen na merge

## Blocked by

https://github.com/ReinderRoos/rcm-desktop/issues/18
