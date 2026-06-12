## Parent

https://github.com/ReinderRoos/rcm-desktop/issues/17

## What to build

Tracer voor slice 58 (stap 3, optioneel in PRD): consolideer compare split-layout zonder UX-wijziging. Split-constanten en `compute_compare_split_layout` op één plek; productie blijft `compare_split_layout_service`. Legacy `workspace_split_layout` is geen no-op orchestrator meer in productiepaden — stub gedeprecieerd of alleen test-compat.

Geen wijziging aan A/B-semantiek (ADR-0006/0007). Alleen uitvoeren als stappen 1–2 gemerged en geen open conflict met slice-53 venster-split werk.

## Acceptance criteria

- [ ] Split-constanten gecentraliseerd; productie importeert niet dubbel uit legacy stub
- [ ] `compute_compare_split_layout` blijft enkel SSOT voor layout in werkruimte
- [ ] Geen zichtbare UX-wijziging in compare-modi
- [ ] `tests/test_compare_split_layout_service.py` en slice-53 issue-07 guard (`workspace_split_layout` niet in view) groen
- [ ] Optioneel: `tests/test_slice29_scenario_ui_deprecation.py` groen

## Blocked by

https://github.com/ReinderRoos/rcm-desktop/issues/18
https://github.com/ReinderRoos/rcm-desktop/issues/19
