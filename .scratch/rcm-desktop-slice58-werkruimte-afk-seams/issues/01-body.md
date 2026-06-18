## Parent

https://github.com/ReinderRoos/rcm-desktop/issues/17

## What to build

Tracer voor slice 58 (stap 1): één Qt-vrije entry voor rapport-gating in de werkruimte. `assess_report_workspace` levert `ReportWorkspaceAssessment` met `eligible`, `reason` (bestaande message constants), en `ReportRunBundle | None`. Bundle-samenstelling blijft delegeert aan `report_run_source_service` (ongewijzigde SSOT); verwijder de shallow alias `resolve_bundle_for_preview`.

Resultatenwerkruimte-toolbar en rapport-generatiedialoog gebruiken alleen deze entry (inclusief preview page counts). Geen duplicate eligibility in de view. Compare A-only, A+B en single-run prioriteit gelijk aan slice 57; live `PlanningOverlayState` alleen bij single-run bundle-resolutie (ADR-0007: bevroren slot-overlays in compare).

Unit-tests dekken assessment-gedrag; bestaande slice-57-rapporttests (materialisatie, docx) blijven groen. Geen wijziging aan rapportinhoud, PDF of drempels.

## Acceptance criteria

- [ ] `assess_report_workspace` bestaat met frozen `ReportWorkspaceAssessment` (`eligible`, `reason`, `bundle`)
- [ ] Toolbar en rapport-dialoog gebruiken alleen deze entry; `resolve_bundle_for_preview` verwijderd of intern
- [ ] Bij geen bundle: duidelijke `reason`; knop enabled/disabled consistent met dialoog-preview
- [ ] Compare A-only, A+B en single-run gedrag gelijk aan slice 57; ADR-0007 overlay-regels intact
- [ ] Unit-tests: assessment voor single-run, compare varianten, geen run / geen bundle
- [ ] `python -m pytest tests/test_report_*.py tests/test_slice57_*.py -q` groen na merge

## Blocked by

None - can start immediately.
